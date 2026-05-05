#!/usr/bin/env python3
"""
Detect running service with infinite loop by collecting two dumps 30 seconds apart
and comparing RUNNABLE threads with identical stack traces.
"""

import json
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def collect_thread_dump():
    """Collect a fresh thread dump using jstack"""
    print(f"Collecting thread dump at {datetime.now().strftime('%H:%M:%S')}...")
    
    try:
        result = subprocess.run(
            ['python', 'collect_with_jstack.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Find the most recent dump file
            dump_files = sorted(Path('thread_dumps').glob('jstack_dump_*.json'))
            if dump_files:
                latest = dump_files[-1]
                print(f"✓ Collected: {latest.name}")
                return latest
        else:
            print(f"✗ Collection failed: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"✗ Error collecting dump: {e}")
        return None

def load_dump(filepath):
    """Load thread dump from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"✗ Error loading {filepath}: {e}")
        return None

def get_stack_signature(thread):
    """Get a signature for the thread's stack trace"""
    if 'stack_trace' not in thread:
        return None
    
    # Use first 5 stack frames as signature (ignore line numbers)
    frames = []
    for frame in thread['stack_trace'][:5]:
        # Remove line numbers and file info for comparison
        method = frame.split('(')[0].strip() if '(' in frame else frame.strip()
        frames.append(method)
    
    return '|'.join(frames)

def compare_dumps(dump1_path, dump2_path):
    """Compare two dumps to find threads with identical stack traces"""
    dump1 = load_dump(dump1_path)
    dump2 = load_dump(dump2_path)
    
    if not dump1 or not dump2:
        return []
    
    threads1 = dump1.get('threads', [])
    threads2 = dump2.get('threads', [])
    
    # Build signature map for dump1 RUNNABLE threads
    sig_map1 = {}
    for t in threads1:
        if t.get('state') == 'RUNNABLE':
            sig = get_stack_signature(t)
            if sig:
                sig_map1[t['name']] = sig
    
    # Find matching RUNNABLE threads in dump2
    infinite_loops = []
    for t in threads2:
        if t.get('state') == 'RUNNABLE':
            name = t['name']
            sig2 = get_stack_signature(t)
            
            if name in sig_map1 and sig2 and sig_map1[name] == sig2:
                # Same thread, same stack trace = likely infinite loop
                infinite_loops.append({
                    'name': name,
                    'cpu_time': t.get('cpu_time', 0),
                    'stack_trace': t.get('stack_trace', [])[:10]  # First 10 frames
                })
    
    return infinite_loops

def main():
    print("=" * 80)
    print("INFINITE LOOP DETECTION - Collecting two dumps 30 seconds apart")
    print("=" * 80)
    print()
    
    # Collect first dump
    print("Step 1: Collecting first thread dump...")
    dump1 = collect_thread_dump()
    if not dump1:
        print("Failed to collect first dump. Exiting.")
        return 1
    
    print()
    print("Step 2: Waiting 30 seconds...")
    for i in range(30, 0, -1):
        print(f"\rCountdown: {i:2d} seconds remaining...", end='', flush=True)
        time.sleep(1)
    print("\r" + " " * 50 + "\r", end='')  # Clear countdown line
    
    print()
    print("Step 3: Collecting second thread dump...")
    dump2 = collect_thread_dump()
    if not dump2:
        print("Failed to collect second dump. Exiting.")
        return 1
    
    print()
    print("Step 4: Comparing dumps for infinite loops...")
    print()
    
    infinite_loops = compare_dumps(dump1, dump2)
    
    if not infinite_loops:
        print("✓ No infinite loops detected!")
        print()
        print("This means:")
        print("  • No RUNNABLE threads had identical stack traces in both dumps")
        print("  • The service may have completed between dumps")
        print("  • Or the service is not CPU-intensive enough to show as RUNNABLE")
        return 0
    
    print(f"⚠ Found {len(infinite_loops)} potential infinite loop(s):")
    print()
    
    for i, loop in enumerate(infinite_loops, 1):
        print(f"{i}. Thread: {loop['name']}")
        print(f"   CPU Time: {loop['cpu_time']:.2f}s")
        print(f"   Stack Trace (top 10 frames):")
        for frame in loop['stack_trace']:
            print(f"      {frame}")
        print()
    
    # Send Slack alert if configured
    try:
        from shared.utils import send_slack_notification
        from shared.config import SLACK_WEBHOOK_URL
        
        if SLACK_WEBHOOK_URL:
            message = f"🔴 *Infinite Loop Detected*\n\n"
            message += f"Found {len(infinite_loops)} thread(s) with identical stack traces:\n"
            for loop in infinite_loops:
                message += f"• `{loop['name']}` (CPU: {loop['cpu_time']:.2f}s)\n"
            
            send_slack_notification(message)
            print("✓ Slack notification sent")
    except Exception as e:
        print(f"Note: Could not send Slack notification: {e}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
