"""Collect thread dumps using jstack command."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import subprocess
import re
from datetime import datetime
from typing import Optional, List
import json

from shared.models import ThreadInfo, ThreadState
from shared.utils import setup_logging
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent
from agents.monitor.slack_notifier import SlackNotifier

logger = setup_logging("jstack_collector")


def find_java_process(process_name: str = "IntegrationServer") -> Optional[int]:
    """
    Find Java process ID by name.
    
    Args:
        process_name: Process name to search for
        
    Returns:
        Process ID or None
    """
    try:
        # Try jps first (Java Process Status)
        result = subprocess.run(
            ["jps", "-l"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if process_name.lower() in line.lower():
                    pid = line.split()[0]
                    logger.info(f"Found Java process: {line.strip()}")
                    return int(pid)
        
        # Fallback to tasklist on Windows
        if sys.platform == 'win32':
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq java.exe", "/FO", "CSV"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines[1:]:  # Skip header
                    if 'java.exe' in line.lower():
                        parts = line.split(',')
                        if len(parts) >= 2:
                            pid = parts[1].strip('"')
                            logger.info(f"Found Java process (PID: {pid})")
                            return int(pid)
        
        return None
        
    except Exception as e:
        logger.error(f"Error finding Java process: {str(e)}")
        return None


def collect_thread_dump_jstack(pid: int) -> Optional[str]:
    """
    Collect thread dump using jstack.
    
    Args:
        pid: Java process ID
        
    Returns:
        Thread dump as string or None
    """
    try:
        logger.info(f"Collecting thread dump from PID {pid}...")
        
        result = subprocess.run(
            ["jstack", str(pid)],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Thread dump collected ({len(result.stdout)} bytes)")
            return result.stdout
        else:
            logger.error(f"jstack failed: {result.stderr}")
            return None
            
    except FileNotFoundError:
        logger.error("jstack command not found. Ensure JDK is installed and in PATH")
        return None
    except subprocess.TimeoutExpired:
        logger.error("jstack command timed out")
        return None
    except Exception as e:
        logger.error(f"Error running jstack: {str(e)}")
        return None


def parse_jstack_output(dump: str) -> List[ThreadInfo]:
    """
    Parse jstack output into ThreadInfo objects.
    
    Args:
        dump: Raw jstack output
        
    Returns:
        List of ThreadInfo objects
    """
    threads = []
    current_thread = None
    stack_trace = []
    
    for line in dump.split('\n'):
        line = line.strip()
        
        # Thread header: "Thread-1" #12 prio=5 os_prio=0 tid=0x00007f8a2c001000 nid=0x1234 runnable
        if line.startswith('"') and ' tid=' in line:
            # Save previous thread
            if current_thread:
                current_thread['stack_trace'] = stack_trace
                threads.append(ThreadInfo(**current_thread))
            
            # Parse new thread
            match = re.match(r'"([^"]+)".*tid=(0x[0-9a-f]+).*nid=(0x[0-9a-f]+)\s+(\w+)', line)
            if match:
                name, tid, nid, state = match.groups()
                current_thread = {
                    'thread_id': tid,
                    'name': name,
                    'state': state.upper(),
                    'cpu_time': 0.0,
                    'stack_trace': []
                }
                stack_trace = []
        
        # Stack trace line
        elif line.startswith('at ') and current_thread:
            stack_trace.append(line)
        
        # Locked/waiting info
        elif ('- locked' in line or '- waiting' in line) and current_thread:
            if '- locked' in line:
                match = re.search(r'<(0x[0-9a-f]+)>', line)
                if match and not current_thread.get('locked_monitors'):
                    current_thread['locked_monitors'] = [match.group(1)]
            elif '- waiting on' in line:
                match = re.search(r'<(0x[0-9a-f]+)>', line)
                if match:
                    current_thread['lock_name'] = match.group(1)
                    current_thread['state'] = 'WAITING'
    
    # Save last thread
    if current_thread:
        current_thread['stack_trace'] = stack_trace
        threads.append(ThreadInfo(**current_thread))
    
    return threads


def save_thread_dump(dump: str, threads: List[ThreadInfo]) -> str:
    """Save thread dump to file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw dump as .txt only
    raw_path = f"data/thread_dumps/jstack_dump_{timestamp}.txt"
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)
    
    with open(raw_path, 'w', encoding='utf-8') as f:
        f.write(dump)
    
    logger.info(f"Saved thread dump to {raw_path}")
    logger.info(f"Thread count: {len(threads)}")
    
    return raw_path


def main():
    """Main entry point."""
    print("="*70)
    print("THREAD DUMP COLLECTION USING JSTACK")
    print("="*70)
    
    # Step 1: Find Java process
    print("\n[1/4] Finding Integration Server process...")
    pid = find_java_process("IntegrationServer")
    
    if not pid:
        print("[FAILED] Could not find Integration Server process")
        print("\nTroubleshooting:")
        print("1. Verify Integration Server is running")
        print("2. Run 'jps -l' to list Java processes")
        print("3. Specify PID manually: python collect_with_jstack.py <PID>")
        return False
    
    print(f"[SUCCESS] Found process (PID: {pid})")
    
    # Step 2: Collect thread dump
    print(f"\n[2/4] Collecting thread dump with jstack...")
    dump = collect_thread_dump_jstack(pid)
    
    if not dump:
        print("[FAILED] Could not collect thread dump")
        return False
    
    print(f"[SUCCESS] Collected {len(dump)} bytes")
    
    # Step 3: Parse thread dump
    print(f"\n[3/4] Parsing thread dump...")
    threads = parse_jstack_output(dump)
    
    if not threads:
        print("[FAILED] Could not parse threads")
        return False
    
    print(f"[SUCCESS] Parsed {len(threads)} threads")
    
    # Thread statistics
    hung_count = sum(1 for t in threads if t.is_hung())
    blocked_count = sum(1 for t in threads if t.is_blocked())
    waiting_count = sum(1 for t in threads if t.is_waiting())
    
    print(f"\nThread Statistics:")
    print(f"  - Total: {len(threads)}")
    print(f"  - Runnable: {sum(1 for t in threads if t.state == 'RUNNABLE')}")
    print(f"  - Blocked: {blocked_count}")
    print(f"  - Waiting: {waiting_count}")
    print(f"  - Hung: {hung_count}")
    
    # Save
    storage_path = save_thread_dump(dump, threads)
    
    # Step 4: Analyze
    print(f"\n[4/4] Analyzing thread dump...")
    analyzer = ThreadDumpAnalyzerAgent()
    analysis = analyzer.analyze(threads)
    
    print(f"[SUCCESS] Analysis completed")
    print(f"\nAnalysis Results:")
    print(f"  - Severity: {analysis.severity.value.upper()}")
    print(f"  - Hung threads: {analysis.hung_threads}")
    print(f"  - Blocked threads: {analysis.blocked_threads}")
    print(f"  - Deadlocks: {len(analysis.deadlocks)}")
    
    if analysis.recommendations:
        print(f"\nRecommendations:")
        for i, rec in enumerate(analysis.recommendations[:5], 1):
            print(f"  {i}. {rec}")
    
    print(f"\nSummary:")
    print(f"  {analysis.summary}")
    
    print("\n" + "="*70)
    print("[SUCCESS] Thread dump collection and analysis complete!")
    print("="*70)
    print(f"\nFiles saved:")
    print(f"  - Raw dump: data/thread_dumps/jstack_dump_*.txt")
    print(f"  - Parsed JSON: {storage_path}")
    
    return True


if __name__ == "__main__":
    # Check for PID argument
    if len(sys.argv) > 1:
        try:
            pid = int(sys.argv[1])
            print(f"Using specified PID: {pid}")
            dump = collect_thread_dump_jstack(pid)
            if dump:
                threads = parse_jstack_output(dump)
                print(f"Collected {len(threads)} threads")
                save_thread_dump(dump, threads)
        except ValueError:
            print("Invalid PID. Usage: python collect_with_jstack.py <PID>")
            sys.exit(1)
    else:
        try:
            success = main()
            sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n\n[!] Interrupted by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

# Made with Bob
