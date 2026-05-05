"""
Example script demonstrating Monitor Agent usage.

This script shows how to use the Monitor Agent programmatically.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.monitor.monitor_agent import MonitorAgent
from agents.monitor.slack_notifier import SlackNotifier
from agents.monitor.scheduler import MonitorScheduler
from shared.models import AlertMessage, AlertSeverity, IssueType, ThreadInfo, ThreadState
from datetime import datetime
import uuid


def example_1_basic_monitoring():
    """Example 1: Basic one-time monitoring."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Monitoring")
    print("=" * 60)
    
    # Create monitor agent
    agent = MonitorAgent()
    
    # Run monitoring
    print("Running monitoring check...")
    alerts = agent.monitor()
    
    # Display results
    if alerts:
        print(f"\n✅ Generated {len(alerts)} alerts:")
        for alert in alerts:
            print(f"  - {alert.title}")
            print(f"    Severity: {alert.severity.value}")
            print(f"    Type: {alert.issue_type.value}")
    else:
        print("\n✅ No issues detected")


def example_2_slack_notification():
    """Example 2: Send alerts to Slack."""
    print("\n" + "=" * 60)
    print("Example 2: Slack Notifications")
    print("=" * 60)
    
    # Create notifier
    notifier = SlackNotifier()
    
    # Create a sample alert
    sample_alert = AlertMessage(
        alert_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        severity=AlertSeverity.HIGH,
        issue_type=IssueType.HUNG_THREAD,
        title="Example Hung Thread Alert",
        description="This is a test alert to demonstrate Slack integration.",
        server_url="http://localhost:5555",
        recommendations=[
            "This is a test alert",
            "No action needed",
            "Check the Slack channel for the message"
        ]
    )
    
    # Send to Slack
    print("Sending test alert to Slack...")
    success = notifier.send_alert(sample_alert)
    
    if success:
        print("✅ Alert sent successfully!")
    else:
        print("❌ Failed to send alert")


def example_3_scheduled_monitoring():
    """Example 3: Scheduled monitoring (runs for 2 minutes)."""
    print("\n" + "=" * 60)
    print("Example 3: Scheduled Monitoring")
    print("=" * 60)
    print("This will run for 2 minutes, then stop automatically.")
    print("Press Ctrl+C to stop earlier.")
    
    # Create scheduler with 30-second interval
    scheduler = MonitorScheduler(interval=30)
    
    # Start monitoring
    scheduler.start_monitoring()
    
    try:
        import time
        # Run for 2 minutes
        for i in range(120):
            time.sleep(1)
            if i % 30 == 0:
                status = scheduler.get_status()
                print(f"\nStatus: Run #{status['run_count']}, Alerts: {status['alert_count']}")
        
        # Stop monitoring
        scheduler.stop_monitoring()
        print("\n✅ Monitoring stopped")
        
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        scheduler.stop_monitoring()


def example_4_custom_alert():
    """Example 4: Create and send custom alert."""
    print("\n" + "=" * 60)
    print("Example 4: Custom Alert")
    print("=" * 60)
    
    # Create a custom thread info
    thread_info = ThreadInfo(
        thread_id="thread-123",
        thread_name="CustomTestThread",
        state=ThreadState.BLOCKED,
        stack_trace=[
            "at com.example.Service.processRequest(Service.java:45)",
            "at com.example.Controller.handleRequest(Controller.java:123)",
            "at java.lang.Thread.run(Thread.java:748)"
        ],
        cpu_time=350000,  # 350 seconds
        blocked_count=5
    )
    
    # Create custom alert
    alert = AlertMessage(
        alert_id=str(uuid.uuid4()),
        timestamp=datetime.now(),
        severity=AlertSeverity.CRITICAL,
        issue_type=IssueType.DEADLOCK,
        title="Custom Deadlock Alert",
        description="Detected a potential deadlock situation with multiple blocked threads.",
        thread_info=thread_info,
        server_url="http://localhost:5555",
        recommendations=[
            "Analyze thread dump for circular dependencies",
            "Review locking mechanisms in Service.java",
            "Consider restarting the affected service"
        ],
        metadata={
            "custom_field": "custom_value",
            "priority": "urgent"
        }
    )
    
    # Display alert details
    print("\nAlert Details:")
    print(f"  ID: {alert.alert_id}")
    print(f"  Title: {alert.title}")
    print(f"  Severity: {alert.severity.value}")
    print(f"  Thread: {alert.thread_info.thread_name}")
    print(f"  Duration: {alert.thread_info.get_duration():.2f}s")
    print(f"  Stack Trace Lines: {len(alert.thread_info.stack_trace)}")
    
    # Send to Slack
    notifier = SlackNotifier()
    print("\nSending to Slack...")
    success = notifier.send_alert(alert)
    
    if success:
        print("✅ Custom alert sent successfully!")
    else:
        print("❌ Failed to send custom alert")


def example_5_monitor_with_callback():
    """Example 5: Monitor with custom callback for alerts."""
    print("\n" + "=" * 60)
    print("Example 5: Monitor with Callback")
    print("=" * 60)
    
    def alert_callback(alert: AlertMessage):
        """Custom callback for handling alerts."""
        print(f"\n🚨 Alert Received: {alert.title}")
        print(f"   Severity: {alert.severity.value}")
        print(f"   Time: {alert.timestamp.strftime('%H:%M:%S')}")
        
        # Custom logic here
        if alert.severity == AlertSeverity.CRITICAL:
            print("   ⚠️  CRITICAL - Immediate action required!")
        
        # Could trigger other actions:
        # - Send email
        # - Create ticket
        # - Trigger remediation
        # - Update dashboard
    
    # Create agent and notifier
    agent = MonitorAgent()
    notifier = SlackNotifier()
    
    # Run monitoring
    print("Running monitoring with callback...")
    alerts = agent.monitor()
    
    # Process alerts with callback
    for alert in alerts:
        alert_callback(alert)
        notifier.send_alert(alert)
    
    if not alerts:
        print("\n✅ No alerts generated")


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print(" Thread Dump Monitor Agent - Examples")
    print("=" * 70)
    
    examples = [
        ("Basic Monitoring", example_1_basic_monitoring),
        ("Slack Notifications", example_2_slack_notification),
        ("Scheduled Monitoring", example_3_scheduled_monitoring),
        ("Custom Alert", example_4_custom_alert),
        ("Monitor with Callback", example_5_monitor_with_callback),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print("  0. Run all examples")
    
    try:
        choice = input("\nSelect example (0-5): ").strip()
        
        if choice == "0":
            for name, func in examples:
                try:
                    func()
                except KeyboardInterrupt:
                    print("\n\n🛑 Skipping to next example...")
                    continue
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            examples[int(choice) - 1][1]()
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("\n" + "=" * 70)
    print("Examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()

# Made with Bob
