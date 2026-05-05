#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to send a sample long-running thread alert to Slack
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
    print("LONG-RUNNING THREAD ALERT TEST")
    print("=" * 80)
    print()
    
    # Initialize Slack notifier
    notifier = SlackNotifier()
    
    # Create sample long-running thread alert
    alert = AlertMessage(
        alert_id="test-long-running-001",
        timestamp=datetime.now(),
        severity=AlertSeverity.MEDIUM,
        issue_type=IssueType.PERFORMANCE,
        title="WARNING: 3 Long-Running Thread(s) Detected",
        description="""**Long-Running Threads (>60s):** 3
  • HTTP Handler-1 (CPU: 125.50s)
  • Database-Connection-Pool-Worker (CPU: 89.30s)
  • JMS-Listener-Thread (CPU: 72.15s)

**Analysis:** These threads have been running for more than 60 seconds. While not yet marked as hung, they may indicate:
- Large data processing operations
- Complex calculations in progress
- Potential infinite loops
- External service delays

**Recommendations:**
1. Monitor these threads for completion
2. Check if operations are expected
3. Review for optimization opportunities
4. Set timeout if operation is stuck
5. Consider breaking into smaller tasks""",
        server_url=config.WEBMETHODS_URL,
        recommendations=[
            "Monitor thread CPU time trends",
            "Check database query performance",
            "Review external service response times",
            "Consider implementing timeouts",
            "Break large operations into smaller chunks"
        ],
        metadata={
            'cycle': 42,
            'total_threads': 75,
            'hung_threads': 0,
            'long_running_threads': 3,
            'blocked_threads': 0,
            'test': True
        }
    )
    
    print("Sending long-running thread alert to Slack...")
    print()
    print(f"Title: {alert.title}")
    print(f"Severity: {alert.severity.value}")
    print(f"Long-Running Threads: 3")
    print()
    
    # Send alert
    success = notifier.send_alert(alert)
    
    if success:
        print("[SUCCESS] Alert sent to Slack!")
        print()
        print("Check your Slack channel for the notification.")
        print("The alert should show:")
        print("  - 🟡 WARNING severity")
        print("  - 3 long-running threads with CPU times")
        print("  - Analysis and recommendations")
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
