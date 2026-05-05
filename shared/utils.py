"""
Utility functions for thread dump analysis
"""
import re
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from shared.models import ThreadInfo, ThreadState
import logging
import os


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging for a module
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create console handler if not already added
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger



def call_webmethods_api(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    server_url: Optional[str] = None,
    auth: Optional[Tuple[str, str]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Call webMethods Integration Server API
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        data: Request data for POST/PUT
        server_url: Server URL (uses config if not provided)
        auth: Authentication tuple (username, password)
        timeout: Request timeout in seconds
    
    Returns:
        API response as dictionary
    """
    from shared.config import config
    
    url = f"{server_url or config.WEBMETHODS_URL}{endpoint}"
    auth_creds = auth or config.get_webmethods_auth()
    
    try:
        if method.upper() == "GET":
            response = requests.get(
                url,
                auth=auth_creds,
                timeout=timeout,
                verify=False
            )
        elif method.upper() == "POST":
            response = requests.post(
                url,
                json=data,
                auth=auth_creds,
                timeout=timeout,
                verify=False
            )
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        response.raise_for_status()
        
        # Try to parse JSON response
        try:
            return response.json()
        except json.JSONDecodeError:
            return {"raw_response": response.text}
    
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "failed"}


def parse_thread_dump(dump_text: str) -> List[ThreadInfo]:
    """
    Parse thread dump text into ThreadInfo objects
    
    Args:
        dump_text: Raw thread dump text
    
    Returns:
        List of ThreadInfo objects
    """
    threads = []
    
    # Split by thread entries (looking for thread name pattern)
    # Updated pattern to handle cpu= and elapsed= fields
    thread_pattern = r'"([^"]+)"\s+#(\d+)\s+(?:daemon\s+)?prio=(\d+)'
    
    lines = dump_text.split('\n')
    current_thread = None
    current_stack = []
    
    for line in lines:
        line = line.strip()
        
        # Check for thread header
        match = re.match(thread_pattern, line)
        if match:
            # Save previous thread if exists
            if current_thread:
                current_thread.stack_trace = current_stack
                threads.append(current_thread)
            
            # Create new thread
            name, thread_num, priority = match.groups()
            
            # Extract tid and nid from the line
            tid_match = re.search(r'tid=([^\s]+)', line)
            nid_match = re.search(r'nid=([^\s]+)', line)
            
            tid = tid_match.group(1) if tid_match else f"thread-{thread_num}"
            nid = nid_match.group(1) if nid_match else ""
            
            # Extract CPU time if available
            cpu_time = 0.0
            cpu_match = re.search(r'cpu=([\d.]+)ms', line)
            if cpu_match:
                cpu_time = float(cpu_match.group(1)) / 1000.0  # Convert ms to seconds
            
            current_thread = ThreadInfo(
                thread_id=tid,
                name=name,
                state="RUNNABLE",  # Will be updated from Thread.State line
                priority=int(priority),
                daemon="daemon" in line.lower(),
                cpu_time=cpu_time
            )
            current_stack = []
        
        # Check for state information
        elif line.startswith("java.lang.Thread.State:"):
            if current_thread:
                state_match = re.search(r"State:\s+(\w+)", line)
                if state_match:
                    current_thread.state = state_match.group(1)
        
        # Check for lock information
        elif "waiting on" in line.lower() or "locked" in line.lower():
            if current_thread:
                lock_match = re.search(r"<([^>]+)>", line)
                if lock_match:
                    current_thread.lock_name = lock_match.group(1)
        
        # Check for stack trace
        elif line.startswith("at ") or line.startswith("- "):
            if current_thread:
                current_stack.append(line)
        
        # Check for blocked/waiting info
        elif "waiting to lock" in line.lower():
            if current_thread:
                current_thread.blocked_count += 1
        
        # Empty line might indicate end of thread
        elif not line and current_thread:
            current_thread.stack_trace = current_stack
            threads.append(current_thread)
            current_thread = None
            current_stack = []
    
    # Add last thread if exists
    if current_thread:
        current_thread.stack_trace = current_stack
        threads.append(current_thread)
    
    return threads


def detect_deadlocks(threads: List[ThreadInfo]) -> List[Dict[str, Any]]:
    """
    Detect deadlocks in thread dump
    
    Args:
        threads: List of ThreadInfo objects
    
    Returns:
        List of detected deadlocks with involved threads
    """
    deadlocks = []
    
    # Build lock ownership map
    lock_owners = {}  # lock_name -> thread
    lock_waiters = {}  # lock_name -> [threads]
    
    for thread in threads:
        # Track lock ownership
        if thread.lock_name and thread.state == ThreadState.RUNNABLE.value:
            lock_owners[thread.lock_name] = thread
        
        # Track lock waiters
        if thread.lock_name and thread.is_blocked():
            if thread.lock_name not in lock_waiters:
                lock_waiters[thread.lock_name] = []
            lock_waiters[thread.lock_name].append(thread)
    
    # Detect circular dependencies
    for lock_name, waiting_threads in lock_waiters.items():
        if lock_name in lock_owners:
            owner = lock_owners[lock_name]
            
            # Check if owner is also waiting for a lock
            if owner.lock_name and owner.lock_name in lock_waiters:
                # Potential deadlock
                involved_threads = [owner] + waiting_threads
                deadlocks.append({
                    "lock": lock_name,
                    "owner": {
                        "thread_id": owner.thread_id,
                        "name": owner.name,
                        "waiting_for": owner.lock_name
                    },
                    "waiters": [
                        {
                            "thread_id": t.thread_id,
                            "name": t.name,
                            "state": t.state
                        }
                        for t in waiting_threads
                    ]
                })
    
    return deadlocks


def calculate_thread_metrics(threads: List[ThreadInfo]) -> Dict[str, Any]:
    """
    Calculate metrics from thread list
    
    Args:
        threads: List of ThreadInfo objects
    
    Returns:
        Dictionary of calculated metrics
    """
    total = len(threads)
    
    if total == 0:
        return {
            "total_threads": 0,
            "runnable": 0,
            "blocked": 0,
            "waiting": 0,
            "timed_waiting": 0,
            "hung_threads": 0,
            "daemon_threads": 0,
            "avg_cpu_time": 0.0,
            "max_cpu_time": 0.0
        }
    
    state_counts = {
        "runnable": 0,
        "blocked": 0,
        "waiting": 0,
        "timed_waiting": 0
    }
    
    hung_count = 0
    daemon_count = 0
    total_cpu_time = 0.0
    max_cpu_time = 0.0
    
    for thread in threads:
        # Count states
        state_lower = thread.state.lower()
        if state_lower in state_counts:
            state_counts[state_lower] += 1
        
        # Count hung threads
        if thread.is_hung():
            hung_count += 1
        
        # Count daemon threads
        if thread.daemon:
            daemon_count += 1
        
        # CPU time stats
        total_cpu_time += thread.cpu_time
        max_cpu_time = max(max_cpu_time, thread.cpu_time)
    
    return {
        "total_threads": total,
        "runnable": state_counts["runnable"],
        "blocked": state_counts["blocked"],
        "waiting": state_counts["waiting"],
        "timed_waiting": state_counts["timed_waiting"],
        "hung_threads": hung_count,
        "daemon_threads": daemon_count,
        "avg_cpu_time": total_cpu_time / total if total > 0 else 0.0,
        "max_cpu_time": max_cpu_time
    }


def format_thread_summary(threads: List[ThreadInfo], max_threads: int = 10) -> str:
    """
    Format thread summary for display
    
    Args:
        threads: List of ThreadInfo objects
        max_threads: Maximum number of threads to include in detail
    
    Returns:
        Formatted summary string
    """
    metrics = calculate_thread_metrics(threads)
    
    summary = f"""
Thread Dump Summary
==================
Total Threads: {metrics['total_threads']}
Runnable: {metrics['runnable']}
Blocked: {metrics['blocked']}
Waiting: {metrics['waiting']}
Timed Waiting: {metrics['timed_waiting']}
Hung Threads: {metrics['hung_threads']}
Daemon Threads: {metrics['daemon_threads']}

Average CPU Time: {metrics['avg_cpu_time']:.2f}s
Max CPU Time: {metrics['max_cpu_time']:.2f}s
"""
    
    # Add top threads by CPU time
    if threads:
        sorted_threads = sorted(threads, key=lambda t: t.cpu_time, reverse=True)
        top_threads = sorted_threads[:max_threads]
        
        summary += f"\nTop {len(top_threads)} Threads by CPU Time:\n"
        summary += "-" * 80 + "\n"
        
        for i, thread in enumerate(top_threads, 1):
            summary += f"{i}. {thread.name}\n"
            summary += f"   State: {thread.state}, CPU: {thread.cpu_time:.2f}s\n"
            if thread.lock_name:
                summary += f"   Lock: {thread.lock_name}\n"
            summary += "\n"
    
    return summary


def save_thread_dump(
    threads: List[ThreadInfo],
    filename: Optional[str] = None,
    directory: str = "data/thread_dumps"
) -> str:
    """
    Save thread dump to file
    
    Args:
        threads: List of ThreadInfo objects
        filename: Optional filename (auto-generated if not provided)
        directory: Directory to save file
    
    Returns:
        Path to saved file
    """
    import os
    
    # Create directory if needed
    os.makedirs(directory, exist_ok=True)
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"thread_dump_{timestamp}.json"
    
    filepath = os.path.join(directory, filename)
    
    # Convert threads to dict
    data = {
        "timestamp": datetime.now().isoformat(),
        "thread_count": len(threads),
        "threads": [t.to_dict() for t in threads],
        "metrics": calculate_thread_metrics(threads)
    }
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath

# Made with Bob
