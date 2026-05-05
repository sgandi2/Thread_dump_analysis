"""Utility functions for Thread Dump Analysis AI Agent."""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from requests.auth import HTTPBasicAuth

from .config import config
from .models import ThreadInfo, ThreadDumpData, ThreadState

logger = logging.getLogger(__name__)


def call_webmethods_api(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Optional[Dict[str, Any]]:
    """
    Call webMethods Integration Server API.
    
    Args:
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        data: Request data for POST/PUT
        timeout: Request timeout in seconds
        
    Returns:
        Response data as dictionary or None on error
    """
    url = f"{config.WEBMETHODS_URL}/{endpoint.lstrip('/')}"
    auth = HTTPBasicAuth(*config.get_webmethods_auth())
    
    try:
        response = requests.request(
            method=method,
            url=url,
            auth=auth,
            json=data,
            timeout=timeout,
            verify=False  # For self-signed certs in dev
        )
        response.raise_for_status()
        return response.json() if response.content else {}
    except requests.exceptions.RequestException as e:
        logger.error(f"API call failed: {url} - {str(e)}")
        return None


def parse_thread_dump(raw_dump: str) -> List[ThreadInfo]:
    """
    Parse thread dump text into ThreadInfo objects.
    
    Args:
        raw_dump: Raw thread dump text (JStack format)
        
    Returns:
        List of ThreadInfo objects
    """
    threads = []
    current_thread = None
    stack_trace = []
    
    for line in raw_dump.split('\n'):
        line = line.strip()
        
        # Thread header line
        if line.startswith('"') and 'tid=' in line:
            # Save previous thread if exists
            if current_thread:
                current_thread.stack_trace = stack_trace
                threads.append(current_thread)
                stack_trace = []
            
            # Parse thread header
            thread_name = line.split('"')[1] if '"' in line else "unknown"
            thread_id = line.split('tid=')[1].split()[0] if 'tid=' in line else "unknown"
            
            # Parse state
            state = ThreadState.RUNNABLE
            if 'BLOCKED' in line:
                state = ThreadState.BLOCKED
            elif 'WAITING' in line:
                state = ThreadState.WAITING
            elif 'TIMED_WAITING' in line:
                state = ThreadState.TIMED_WAITING
            
            current_thread = ThreadInfo(
                thread_id=thread_id,
                thread_name=thread_name,
                state=state,
                stack_trace=[]
            )
            
        # Stack trace line
        elif line.startswith('at ') or line.startswith('- '):
            stack_trace.append(line)
            
        # Lock information
        elif 'waiting on' in line.lower() or 'locked' in line.lower():
            if current_thread:
                if 'waiting on' in line.lower():
                    current_thread.lock_name = line.split('<')[1].split('>')[0] if '<' in line else None
                stack_trace.append(line)
    
    # Save last thread
    if current_thread:
        current_thread.stack_trace = stack_trace
        threads.append(current_thread)
    
    return threads


def format_slack_message(
    title: str,
    description: str,
    fields: Optional[Dict[str, str]] = None,
    color: str = "danger"
) -> Dict[str, Any]:
    """
    Format a Slack message with attachments.
    
    Args:
        title: Message title
        description: Message description
        fields: Additional fields to display
        color: Message color (good, warning, danger)
        
    Returns:
        Formatted Slack message dictionary
    """
    attachment = {
        "color": color,
        "title": title,
        "text": description,
        "ts": int(datetime.now().timestamp())
    }
    
    if fields:
        attachment["fields"] = [
            {"title": k, "value": v, "short": True}
            for k, v in fields.items()
        ]
    
    return {
        "attachments": [attachment]
    }


def calculate_thread_metrics(threads: List[ThreadInfo]) -> Dict[str, Any]:
    """
    Calculate metrics from thread list.
    
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
            "blocked_percentage": 0.0,
            "avg_blocked_count": 0.0
        }
    
    state_counts = {
        ThreadState.RUNNABLE: 0,
        ThreadState.BLOCKED: 0,
        ThreadState.WAITING: 0,
        ThreadState.TIMED_WAITING: 0
    }
    
    total_blocked_count = 0
    
    for thread in threads:
        if thread.state in state_counts:
            state_counts[thread.state] += 1
        total_blocked_count += thread.blocked_count
    
    return {
        "total_threads": total,
        "runnable": state_counts[ThreadState.RUNNABLE],
        "blocked": state_counts[ThreadState.BLOCKED],
        "waiting": state_counts[ThreadState.WAITING],
        "timed_waiting": state_counts[ThreadState.TIMED_WAITING],
        "blocked_percentage": (state_counts[ThreadState.BLOCKED] / total) * 100,
        "avg_blocked_count": total_blocked_count / total if total > 0 else 0
    }


def get_ollama_recommendation(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.7
) -> Optional[str]:
    """
    Get AI recommendation from Ollama.
    
    Args:
        prompt: The prompt to send to Ollama
        model: Model name (defaults to config)
        temperature: Temperature for generation
        
    Returns:
        Generated text or None on error
    """
    model = model or config.OLLAMA_MODEL
    url = f"{config.OLLAMA_BASE_URL}/api/generate"
    
    try:
        response = requests.post(
            url,
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        return result.get("response", "")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama API call failed: {str(e)}")
        return None


def save_thread_dump(dump_data: ThreadDumpData, filename: Optional[str] = None) -> str:
    """
    Save thread dump data to file.
    
    Args:
        dump_data: ThreadDumpData object
        filename: Optional filename (auto-generated if not provided)
        
    Returns:
        Path to saved file
    """
    import os
    
    if not filename:
        timestamp = dump_data.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"thread_dump_{timestamp}.json"
    
    filepath = os.path.join(config.THREAD_DUMPS_DIR, filename)
    os.makedirs(config.THREAD_DUMPS_DIR, exist_ok=True)
    
    # Convert to dict for JSON serialization
    data = {
        "timestamp": dump_data.timestamp.isoformat(),
        "server_url": dump_data.server_url,
        "total_threads": dump_data.total_threads,
        "cpu_usage": dump_data.cpu_usage,
        "memory_usage": dump_data.memory_usage,
        "threads": [
            {
                "thread_id": t.thread_id,
                "thread_name": t.thread_name,
                "state": t.state.value,
                "stack_trace": t.stack_trace,
                "cpu_time": t.cpu_time,
                "blocked_count": t.blocked_count
            }
            for t in dump_data.threads
        ]
    }
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Thread dump saved to {filepath}")
    return filepath


def setup_logging(name: str, level: str = None) -> logging.Logger:
    """
    Setup logging for a module.
    
    Args:
        name: Logger name
        level: Log level (defaults to config)
        
    Returns:
        Configured logger
    """
    import os
    
    level = level or config.LOG_LEVEL
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler
    os.makedirs(config.LOG_DIR, exist_ok=True)
    file_handler = logging.FileHandler(
        os.path.join(config.LOG_DIR, f"{name}.log")
    )
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger

# Made with Bob
