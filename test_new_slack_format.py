#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to send Slack alert with new format
"""

import sys
import os
from datetime import datetime

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.monitor.slack_notifier import SlackNotifier
from shared.models import AlertMessage, AlertSeverity, IssueType
from shared.config import config

def main():
    print("=" * 80)
    print("NEW SLACK FORMAT TEST")
    print("=" * 80)
    print()
    
    # Initialize Slack notifier
    notifier = SlackNotifier()
    
    # Create sample alert with new format
    thread_log = """Hung Threads: 1
  • HTTP Handler-1
    State: RUNNABLE
    CPU Time: 325.50s
    Blocked Count: 0
    Stack: at com.wm.app.b2b.server.ServiceThread.run(ServiceThread.java:245)

Long-Running Threads (>60s): 2
  • Database-Connection-Pool-Worker
    State: RUNNABLE
    CPU Time: 125.30s
    Stack: at java.sql.Statement.executeQuery(Statement.java:156)

  • JMS-Listener-Thread
    State: WAITING
    CPU Time: 89.15s
    Stack: at java.lang.Object.wait(Native Method)"""

    root_cause = """Hung threads detected - threads have been running for over 5 minutes.
Possible causes:
  • Infinite loop in application code
  • Database query timeout or deadlock
  • External service not responding
  • Resource contention or lock waiting"""

    detailed_analysis = """Total Threads: 75
Runnable: 35
Waiting: 22
Blocked: 0
Hung: 1
Long-Running: 2

Analysis Severity: CRITICAL
Patterns Detected: 2
  • hung_threads: 1 occurrence(s)
  • long_running_threads: 2 occurrence(s)"""

    alert = AlertMessage(
        alert_id="test-new-format-001",
        timestamp=datetime.now(),
        severity=AlertSeverity.CRITICAL,
        issue_type=IssueType.HUNG_THREAD,
        title="CRITICAL Alert: HUNG THREAD",
        description=thread_log,
        server_url=config.WEBMETHODS_URL,
        recommendations=[
            "Review thread stack trace for blocking calls",
            "Check database connection pool status",
            "Verify external service availability",
            "Consider killing thread if unresponsive",
            "Increase timeout values if needed"
        ],
        metadata={
            'cycle': 42,
            'total_threads': 75,
            'hung_threads': 1,
            'long_running_threads': 2,
            'blocked_threads': 0,
            'pid': 1860,
            'cpu_usage': 193.7,
            'memory_usage': 3.7,
            'root_cause': root_cause,
            'detailed_analysis': detailed_analysis
        }
    )
    
    print("Sending alert with new format to Slack...")
    print()
    print("Expected Format:")
    print("  CRITICAL Alert: HUNG THREAD")
    print("  Process ID: 1860")
    print("  CPU Usage: 193.7%")
    print("  Memory Usage: 3.7%")
    print("  Detected: 2026-05-05 19:28:30")
    print("  Pattern: HUNG THREAD")
    print("  Long Running thread log from server")
    print("  Root cause analysis")
    print("  Detailed Analysis")
    print("  AI Remediations recommendation steps")
    print()
    
    # Send alert
    success = notifier.send_alert(alert)
    
    if success:
        print("[SUCCESS] Alert sent to Slack with new format!")
        print()
        print("Check your Slack channel for the notification.")
    else:
        print("[FAILED] Could not send alert to Slack")
        print()
        print("Please check:")
        print("  1. SLACK_WEBHOOK_URL is configured in .env")
        print("  2. Webhook URL is valid")
        print("  3. Network connectivity")
    
    print()
    print("=" * 80)

if __name__ == '__main__':
    main()

# Made with Bob
