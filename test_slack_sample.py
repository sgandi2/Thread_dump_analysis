"""Test Slack notification with a sample message."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from datetime import datetime
from agents.monitor.slack_notifier import SlackNotifier
from shared.models import AlertMessage, AlertSeverity, IssueType

def main():
    """Send a sample alert to Slack."""
    print("="*70)
    print("SLACK NOTIFICATION TEST - Sample Message")
    print("="*70)
    
    # Create Slack notifier
    notifier = SlackNotifier()
    
    # Check if webhook is configured
    if not notifier.webhook_url:
        print("\n[!] No Slack webhook URL configured!")
        print("\nTo configure Slack:")
        print("1. Create a Slack webhook at: https://api.slack.com/messaging/webhooks")
        print("2. Set SLACK_WEBHOOK_URL in your .env file")
        print("3. Optionally set SLACK_CHANNEL (default: #alerts)")
        print("\nExample .env:")
        print("SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL")
        print("SLACK_CHANNEL=#thread-dump-alerts")
        return False
    
    print(f"\n[+] Slack webhook configured")
    print(f"    URL: {notifier.webhook_url[:50]}...")
    print(f"    Channel: {notifier.channel}")
    
    # Send test message first
    print("\n[+] Sending test message...")
    if notifier.send_test_message():
        print("    [SUCCESS] Test message sent!")
    else:
        print("    [FAILED] Could not send test message")
        return False
    
    # Create sample alert - Hung Thread
    print("\n[+] Creating sample hung thread alert...")
    hung_alert = AlertMessage(
        alert_id="sample-001",
        timestamp=datetime.now(),
        severity=AlertSeverity.HIGH,
        issue_type=IssueType.HUNG_THREAD,
        title="Hung Thread Detected: HTTP-Worker-5",
        description=(
            "Thread 'HTTP-Worker-5' has been running for 425.3 seconds, "
            "exceeding the threshold of 300 seconds. The thread appears to be "
            "stuck in a database query operation."
        ),
        server_url="http://localhost:5555",
        recommendations=[
            "Review thread stack trace for blocking database operations",
            "Check database connection pool status",
            "Verify database server responsiveness",
            "Consider killing the thread if it's safe to do so"
        ],
        metadata={
            "thread_id": "0x7f8a2c001000",
            "thread_name": "HTTP-Worker-5",
            "duration": 425.3,
            "state": "RUNNABLE",
            "stack_trace_preview": "java.net.SocketInputStream.read() -> com.wm.app.b2b.server.ServiceThread.run()"
        }
    )
    
    print(f"    Alert ID: {hung_alert.alert_id}")
    print(f"    Severity: {hung_alert.severity.value}")
    print(f"    Type: {hung_alert.issue_type.value}")
    
    print("\n[+] Sending hung thread alert to Slack...")
    if notifier.send_alert(hung_alert):
        print("    [SUCCESS] Hung thread alert sent!")
    else:
        print("    [FAILED] Could not send hung thread alert")
    
    # Create sample alert - High CPU
    print("\n[+] Creating sample high CPU alert...")
    cpu_alert = AlertMessage(
        alert_id="sample-002",
        timestamp=datetime.now(),
        severity=AlertSeverity.CRITICAL,
        issue_type=IssueType.HIGH_CPU,
        title="Critical: High CPU Usage Detected",
        description=(
            "CPU usage has reached 94.5%, significantly exceeding the "
            "threshold of 80%. Multiple threads are consuming excessive CPU resources."
        ),
        server_url="http://localhost:5555",
        recommendations=[
            "Identify CPU-intensive threads using thread dump analysis",
            "Review recent code deployments for performance issues",
            "Check for infinite loops or inefficient algorithms",
            "Consider scaling resources or load balancing"
        ],
        metadata={
            "cpu_usage": 94.5,
            "threshold": 80.0,
            "top_threads": [
                {"name": "HTTP-Worker-3", "cpu": 35.2},
                {"name": "HTTP-Worker-7", "cpu": 28.1},
                {"name": "GC-Thread", "cpu": 15.8}
            ]
        }
    )
    
    print(f"    Alert ID: {cpu_alert.alert_id}")
    print(f"    Severity: {cpu_alert.severity.value}")
    print(f"    Type: {cpu_alert.issue_type.value}")
    
    print("\n[+] Sending high CPU alert to Slack...")
    if notifier.send_alert(cpu_alert):
        print("    [SUCCESS] High CPU alert sent!")
    else:
        print("    [FAILED] Could not send high CPU alert")
    
    # Create sample alert - Deadlock
    print("\n[+] Creating sample deadlock alert...")
    deadlock_alert = AlertMessage(
        alert_id="sample-003",
        timestamp=datetime.now(),
        severity=AlertSeverity.CRITICAL,
        issue_type=IssueType.DEADLOCK,
        title="CRITICAL: Deadlock Detected",
        description=(
            "A deadlock has been detected involving 3 threads. "
            "Threads are waiting on each other in a circular dependency, "
            "causing a complete standstill. Immediate action required."
        ),
        server_url="http://localhost:5555",
        recommendations=[
            "Analyze thread dump to identify circular lock dependencies",
            "Review locking mechanisms in the affected code paths",
            "Consider restarting affected services to break the deadlock",
            "Implement timeout mechanisms for lock acquisition",
            "Review and refactor code to prevent future deadlocks"
        ],
        metadata={
            "affected_threads": 3,
            "thread_ids": ["0x7f8a2c001000", "0x7f8a2c002000", "0x7f8a2c003000"],
            "locks_involved": ["Lock-A", "Lock-B", "Lock-C"]
        }
    )
    
    print(f"    Alert ID: {deadlock_alert.alert_id}")
    print(f"    Severity: {deadlock_alert.severity.value}")
    print(f"    Type: {deadlock_alert.issue_type.value}")
    
    print("\n[+] Sending deadlock alert to Slack...")
    if notifier.send_alert(deadlock_alert):
        print("    [SUCCESS] Deadlock alert sent!")
    else:
        print("    [FAILED] Could not send deadlock alert")
    
    # Send summary
    print("\n[+] Sending monitoring summary...")
    if notifier.send_summary(
        total_threads=150,
        hung_count=2,
        blocked_count=5
    ):
        print("    [SUCCESS] Summary sent!")
    else:
        print("    [FAILED] Could not send summary")
    
    print("\n" + "="*70)
    print("[SUCCESS] All sample messages sent to Slack!")
    print("="*70)
    print("\nCheck your Slack channel for the alerts:")
    print(f"  Channel: {notifier.channel}")
    print("\nYou should see:")
    print("  1. Test message (startup notification)")
    print("  2. Hung thread alert (HIGH severity)")
    print("  3. High CPU alert (CRITICAL severity)")
    print("  4. Deadlock alert (CRITICAL severity)")
    print("  5. Monitoring summary")
    print("="*70)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

# Made with Bob
