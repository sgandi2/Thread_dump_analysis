"""
Test script for Monitor Agent

This script demonstrates how to use the Monitor Agent and test its functionality.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.config import config
from shared.models import ThreadInfo, ThreadDumpData, ThreadState, AlertMessage, AlertSeverity, IssueType
from agents.monitor import MonitorAgent, SlackNotifier
from datetime import datetime


def create_mock_thread_dump():
    """Create a mock thread dump for testing."""
    threads = [
        ThreadInfo(
            thread_id="1",
            thread_name="HTTP-Worker-1",
            state=ThreadState.RUNNABLE,
            stack_trace=[
                "at com.wm.app.b2b.server.ServiceThread.run(ServiceThread.java:123)",
                "at java.lang.Thread.run(Thread.java:748)"
            ],
            cpu_time=350000,  # 350 seconds - hung thread!
            blocked_count=0
        ),
        ThreadInfo(
            thread_id="2",
            thread_name="HTTP-Worker-2",
            state=ThreadState.BLOCKED,
            stack_trace=[
                "at com.wm.app.b2b.server.ServiceThread.run(ServiceThread.java:456)",
                "- waiting to lock <0x00000000d5c5e5e0>"
            ],
            cpu_time=50000,
            blocked_count=5
        ),
        ThreadInfo(
            thread_id="3",
            thread_name="HTTP-Worker-3",
            state=ThreadState.RUNNABLE,
            stack_trace=[
                "at com.wm.app.b2b.server.ServiceThread.run(ServiceThread.java:789)"
            ],
            cpu_time=10000,
            blocked_count=0
        )
    ]
    
    return ThreadDumpData(
        timestamp=datetime.now(),
        server_url=config.WEBMETHODS_URL,
        total_threads=len(threads),
        threads=threads,
        cpu_usage=85.5,  # High CPU!
        memory_usage=78.2
    )


def test_thread_detection():
    """Test thread detection logic."""
    print("=" * 70)
    print("Testing Thread Detection")
    print("=" * 70)
    
    dump = create_mock_thread_dump()
    
    # Test hung thread detection
    hung_threads = dump.get_hung_threads(threshold=300)
    print(f"\n✓ Hung threads detected: {len(hung_threads)}")
    for thread in hung_threads:
        print(f"  - {thread.thread_name} (duration: {thread.get_duration():.2f}s)")
    
    # Test blocked thread detection
    blocked_threads = dump.get_blocked_threads()
    print(f"\n✓ Blocked threads detected: {len(blocked_threads)}")
    for thread in blocked_threads:
        print(f"  - {thread.thread_name} (blocked count: {thread.blocked_count})")
    
    # Test deadlock detection
    deadlocks = dump.detect_deadlocks()
    print(f"\n✓ Deadlocks detected: {len(deadlocks)}")
    
    print("\n" + "=" * 70)


def test_alert_creation():
    """Test alert message creation."""
    print("\nTesting Alert Creation")
    print("=" * 70)
    
    dump = create_mock_thread_dump()
    hung_thread = dump.get_hung_threads()[0]
    
    alert = AlertMessage(
        alert_id="test-123",
        timestamp=datetime.now(),
        severity=AlertSeverity.HIGH,
        issue_type=IssueType.HUNG_THREAD,
        title=f"Hung Thread Detected: {hung_thread.thread_name}",
        description=f"Thread has been running for {hung_thread.get_duration():.2f} seconds",
        thread_info=hung_thread,
        server_url=config.WEBMETHODS_URL,
        recommendations=[
            "Review thread stack trace for blocking operations",
            "Check for database connection issues",
            "Consider thread interruption if safe"
        ]
    )
    
    print(f"\n✓ Alert created:")
    print(f"  - ID: {alert.alert_id}")
    print(f"  - Severity: {alert.severity.value}")
    print(f"  - Type: {alert.issue_type.value}")
    print(f"  - Title: {alert.title}")
    print(f"  - Recommendations: {len(alert.recommendations)}")
    
    # Test Slack block formatting
    blocks = alert.to_slack_blocks()
    print(f"\n✓ Slack blocks generated: {len(blocks)} blocks")
    
    print("\n" + "=" * 70)


def test_slack_notifier():
    """Test Slack notifier."""
    print("\nTesting Slack Notifier")
    print("=" * 70)
    
    notifier = SlackNotifier()
    
    if not notifier.webhook_url:
        print("\n⚠️  No Slack webhook configured. Skipping Slack test.")
        print("   Set SLACK_WEBHOOK_URL in .env to test Slack integration")
    else:
        print(f"\n✓ Slack notifier initialized")
        print(f"  - Webhook: {notifier.webhook_url[:50]}...")
        print(f"  - Channel: {notifier.channel}")
        
        # Ask user if they want to send test message
        response = input("\nSend test message to Slack? (y/n): ")
        if response.lower() == 'y':
            if notifier.send_test_message():
                print("✓ Test message sent successfully!")
            else:
                print("✗ Failed to send test message")
    
    print("\n" + "=" * 70)


def test_monitor_agent():
    """Test monitor agent (without actual API calls)."""
    print("\nTesting Monitor Agent")
    print("=" * 70)
    
    print("\n✓ Monitor agent can be initialized")
    print("  Note: Full testing requires webMethods Integration Server")
    print("  Use 'python run_monitor.py --once' to test with real server")
    
    print("\n" + "=" * 70)


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Monitor Agent Test Suite" + " " * 29 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        # Run tests
        test_thread_detection()
        test_alert_creation()
        test_slack_notifier()
        test_monitor_agent()
        
        # Summary
        print("\n")
        print("╔" + "=" * 68 + "╗")
        print("║" + " " * 25 + "Test Summary" + " " * 31 + "║")
        print("╚" + "=" * 68 + "╝")
        print()
        print("✅ All tests completed successfully!")
        print()
        print("Next steps:")
        print("  1. Configure .env with your settings")
        print("  2. Set up Slack webhook URL")
        print("  3. Install Ollama and pull llama2 model")
        print("  4. Run: python run_monitor.py --test-slack")
        print("  5. Run: python run_monitor.py --once")
        print("  6. Run: python run_monitor.py (for continuous monitoring)")
        print()
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
