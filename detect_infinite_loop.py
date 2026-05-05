#!/usr/bin/env python3
"""
Detect infinite loop threads by comparing consecutive thread dumps
Looks for RUNNABLE threads that stay in the same stack trace
"""
import json
import sys
import io
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from agents.monitor.slack_notifier import SlackNotifier
from shared.models import AlertMessage, AlertSeverity, IssueType


def load_thread_dumps():
    """Load the two most recent thread dumps"""
    dump_dir = Path("data/thread_dumps")
    json_files = sorted(dump_dir.glob("jstack_dump_*.json"), reverse=True)
    
    if len(json_files) < 2:
        print("❌ Need at least 2 thread dumps to compare")
        print(f"   Found: {len(json_files)}")
        print("   Run collection twice with 30 second gap")
        return None, None
    
    with open(json_files[0], 'r') as f:
        dump1 = json.load(f)
    
    with open(json_files[1], 'r') as f:
        dump2 = json.load(f)
    
    return dump1, dump2


def detect_infinite_loops(dump1, dump2):
    """Detect threads that are stuck in RUNNABLE state with same stack trace"""
    
    print("=" * 70)
    print("🔍 INFINITE LOOP DETECTION")
    print("=" * 70)
    
    print(f"\nComparing:")
    print(f"  Dump 1: {dump1['timestamp']} ({dump1['thread_count']} threads)")
    print(f"  Dump 2: {dump2['timestamp']} ({dump2['thread_count']} threads)")
    
    # Create thread maps by name
    threads1 = {t['name']: t for t in dump1['threads']}
    threads2 = {t['name']: t for t in dump2['threads']}
    
    infinite_loop_threads = []
    
    print(f"\n🔎 Analyzing threads...")
    
    for name, thread1 in threads1.items():
        if name not in threads2:
            continue
        
        thread2 = threads2[name]
        
        # Check if thread is RUNNABLE in both dumps
        if thread1['state'] == 'RUNNABLE' and thread2['state'] == 'RUNNABLE':
            # Compare stack traces (first 3 lines)
            stack1 = thread1.get('stack_trace', [])[:3]
            stack2 = thread2.get('stack_trace', [])[:3]
            
            # If stack trace is identical, likely infinite loop
            if stack1 and stack2 and stack1 == stack2:
                # Check if it's not a normal waiting thread
                if not any(keyword in str(stack1) for keyword in ['wait', 'sleep', 'park', 'Native Method']):
                    infinite_loop_threads.append({
                        'name': name,
                        'thread_id': thread1['thread_id'],
                        'state': thread1['state'],
                        'stack_trace': stack1,
                        'cpu_time': thread1.get('cpu_time', 0),
                        'priority': thread1.get('priority', 5)
                    })
    
    return infinite_loop_threads


def send_alerts(infinite_loop_threads):
    """Send Slack alerts for detected infinite loops"""
    if not infinite_loop_threads:
        return
    
    print(f"\n🚨 Sending Slack alerts...")
    
    notifier = SlackNotifier()
    
    for thread in infinite_loop_threads:
        alert = AlertMessage(
            severity=AlertSeverity.HIGH,
            title=f"🔴 Infinite Loop Detected: {thread['name']}",
            timestamp=datetime.now(),
            server_url="http://localhost:5555",
            description=f"Thread '{thread['name']}' appears to be stuck in an infinite loop",
            issue_type=IssueType.HUNG_THREAD,
            recommendations=[
                "Review the service code for infinite loop conditions",
                "Check for missing loop exit conditions",
                "Verify loop termination logic",
                "Consider killing the thread if unresponsive",
                "Add timeout mechanism to the service"
            ],
            metadata={
                'thread_id': thread['thread_id'],
                'state': thread['state'],
                'stack_trace': thread['stack_trace']
            }
        )
        
        success = notifier.send_alert(alert)
        if success:
            print(f"   ✅ Alert sent for: {thread['name']}")
        else:
            print(f"   ❌ Failed to send alert for: {thread['name']}")


def main():
    """Main detection logic"""
    
    # Load dumps
    dump1, dump2 = load_thread_dumps()
    if not dump1 or not dump2:
        return
    
    # Detect infinite loops
    infinite_loop_threads = detect_infinite_loops(dump1, dump2)
    
    # Display results
    print(f"\n📊 Results:")
    print("=" * 70)
    
    if infinite_loop_threads:
        print(f"\n🔴 Found {len(infinite_loop_threads)} infinite loop thread(s):\n")
        
        for thread in infinite_loop_threads:
            print(f"Thread: {thread['name']}")
            print(f"  ID: {thread['thread_id']}")
            print(f"  State: {thread['state']}")
            print(f"  CPU Time: {thread['cpu_time']}s")
            print(f"  Stack Trace (top 3):")
            for line in thread['stack_trace']:
                print(f"    {line}")
            print()
        
        # Send Slack alerts
        send_alerts(infinite_loop_threads)
        
        print("\n💡 Recommendations:")
        print("  1. Check the dashboard: http://localhost:8502")
        print("  2. Review the service code for loop conditions")
        print("  3. Consider applying remediation from dashboard")
        print("  4. Kill thread if necessary: Use remediation agent")
        
    else:
        print("\n✅ No infinite loop threads detected")
        print("   All RUNNABLE threads appear to be making progress")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

# Made with Bob
