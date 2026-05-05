"""Test Monitor Agent with Slack Notifications."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import json

from agents.monitor.monitor_agent import MonitorAgent
from agents.monitor.slack_notifier import SlackNotifier
from agents.monitor.scheduler import MonitorScheduler
from shared.models import AlertMessage, AlertSeverity, IssueType


def test_slack_notifier():
    """Test Slack notifier functionality."""
    print("\n" + "="*60)
    print("TEST 1: Slack Notifier")
    print("="*60)
    
    # Create notifier with mock webhook
    notifier = SlackNotifier(
        webhook_url="https://hooks.slack.com/services/TEST/WEBHOOK/URL",
        channel="#thread-dump-alerts"
    )
    
    # Create test alert
    alert = AlertMessage(
        alert_id="test-001",
        timestamp=datetime.now(),
        severity=AlertSeverity.HIGH,
        issue_type=IssueType.HUNG_THREAD,
        title="Test Hung Thread Alert",
        description="This is a test alert for hung thread detection",
        server_url="http://localhost:5555",
        recommendations=[
            "Review thread stack trace",
            "Check for blocking operations",
            "Consider thread interruption"
        ],
        metadata={"thread_id": "0x1234", "duration": 350.5}
    )
    
    print(f"\n+ Created test alert:")
    print(f"  - Alert ID: {alert.alert_id}")
    print(f"  - Severity: {alert.severity.value}")
    print(f"  - Type: {alert.issue_type.value}")
    print(f"  - Title: {alert.title}")
    
    # Mock the requests.post call
    with patch('requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Send alert
        success = notifier.send_alert(alert)
        
        print(f"\n+ Slack notification sent: {success}")
        print(f"  - Webhook called: {mock_post.called}")
        print(f"  - Call count: {mock_post.call_count}")
        
        if mock_post.called:
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            print(f"\n+ Slack payload structure:")
            print(f"  - Channel: {payload.get('channel')}")
            print(f"  - Blocks count: {len(payload.get('blocks', []))}")
            print(f"  - Fallback text: {payload.get('text')}")
            
            # Print first block (header)
            if payload.get('blocks'):
                header = payload['blocks'][0]
                print(f"\n+ Alert header:")
                print(f"  - Type: {header.get('type')}")
                print(f"  - Text: {header.get('text', {}).get('text')}")
    
    print("\n✅ Slack notifier test completed")
    return success


def test_monitor_agent_with_mock_data():
    """Test monitor agent with mock server data."""
    print("\n" + "="*60)
    print("TEST 2: Monitor Agent with Mock Data")
    print("="*60)
    
    agent = MonitorAgent()
    
    # Mock server response with hung threads
    mock_thread_data = {
        "threads": [
            {
                "id": "0x1001",
                "name": "HTTP-Worker-1",
                "state": "RUNNABLE",
                "cpuTime": 350000,  # 350 seconds (hung)
                "userTime": 350000,
                "blockedCount": 0,
                "waitedCount": 5,
                "stackTrace": [
                    "java.net.SocketInputStream.read()",
                    "com.wm.app.b2b.server.ServiceThread.run()"
                ]
            },
            {
                "id": "0x1002",
                "name": "HTTP-Worker-2",
                "state": "BLOCKED",
                "cpuTime": 50000,
                "userTime": 50000,
                "blockedCount": 10,
                "waitedCount": 20,
                "stackTrace": [
                    "java.lang.Object.wait()",
                    "com.wm.app.b2b.server.ServiceThread.run()"
                ]
            },
            {
                "id": "0x1003",
                "name": "HTTP-Worker-3",
                "state": "RUNNABLE",
                "cpuTime": 100000,
                "userTime": 100000,
                "blockedCount": 0,
                "waitedCount": 2,
                "stackTrace": []
            }
        ]
    }
    
    mock_stats = {
        "cpuUsage": 85.5,
        "memoryUsage": 78.2
    }
    
    print(f"\n+ Mock data created:")
    print(f"  - Total threads: {len(mock_thread_data['threads'])}")
    print(f"  - Hung threads: 1 (HTTP-Worker-1, 350s)")
    print(f"  - Blocked threads: 1 (HTTP-Worker-2)")
    print(f"  - CPU usage: {mock_stats['cpuUsage']}%")
    print(f"  - Memory usage: {mock_stats['memoryUsage']}%")
    
    # Mock API calls
    with patch('shared.utils.call_webmethods_api') as mock_api:
        def api_side_effect(endpoint):
            if "threads" in endpoint:
                return mock_thread_data
            elif "stats" in endpoint:
                return mock_stats
            return None
        
        mock_api.side_effect = api_side_effect
        
        # Run monitoring
        print("\n+ Running monitor agent...")
        alerts = agent.monitor("http://localhost:5555")
        
        print(f"\n+ Monitoring results:")
        print(f"  - Alerts generated: {len(alerts)}")
        
        for i, alert in enumerate(alerts, 1):
            print(f"\n  Alert #{i}:")
            print(f"    - Severity: {alert.severity.value}")
            print(f"    - Type: {alert.issue_type.value}")
            print(f"    - Title: {alert.title}")
            print(f"    - Description: {alert.description[:80]}...")
            print(f"    - Recommendations: {len(alert.recommendations)}")
    
    print("\n[+] Monitor agent test completed")
    return alerts


def test_slack_integration_end_to_end():
    """Test complete monitoring with Slack notifications."""
    print("\n" + "="*60)
    print("TEST 3: End-to-End Monitor + Slack Integration")
    print("="*60)
    
    # Create monitor agent
    agent = MonitorAgent()
    
    # Create Slack notifier with mock webhook
    notifier = SlackNotifier(
        webhook_url="https://hooks.slack.com/services/TEST/WEBHOOK/URL",
        channel="#thread-dump-alerts"
    )
    
    # Mock server data with multiple issues
    mock_thread_data = {
        "threads": [
            {
                "id": "0x2001",
                "name": "Hung-Thread-1",
                "state": "RUNNABLE",
                "cpuTime": 400000,  # 400 seconds
                "userTime": 400000,
                "blockedCount": 0,
                "waitedCount": 0,
                "stackTrace": ["java.net.SocketInputStream.read()"]
            },
            {
                "id": "0x2002",
                "name": "Blocked-Thread-1",
                "state": "BLOCKED",
                "cpuTime": 50000,
                "userTime": 50000,
                "blockedCount": 15,
                "waitedCount": 30,
                "stackTrace": ["java.lang.Object.wait()"]
            },
            {
                "id": "0x2003",
                "name": "Blocked-Thread-2",
                "state": "BLOCKED",
                "cpuTime": 60000,
                "userTime": 60000,
                "blockedCount": 20,
                "waitedCount": 40,
                "stackTrace": ["java.lang.Object.wait()"]
            }
        ]
    }
    
    mock_stats = {
        "cpuUsage": 92.0,  # High CPU
        "memoryUsage": 88.5  # High memory
    }
    
    print(f"\n+ Test scenario:")
    print(f"  - 1 hung thread (400s)")
    print(f"  - 2 blocked threads")
    print(f"  - High CPU: {mock_stats['cpuUsage']}%")
    print(f"  - High memory: {mock_stats['memoryUsage']}%")
    
    # Mock API and Slack calls
    with patch('shared.utils.call_webmethods_api') as mock_api, \
         patch('requests.post') as mock_post:
        
        # Setup API mock
        def api_side_effect(endpoint):
            if "threads" in endpoint:
                return mock_thread_data
            elif "stats" in endpoint:
                return mock_stats
            return None
        
        mock_api.side_effect = api_side_effect
        
        # Setup Slack mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Run monitoring
        print("\n+ Running monitoring cycle...")
        alerts = agent.monitor("http://localhost:5555")
        
        print(f"\n+ Generated {len(alerts)} alerts:")
        for i, alert in enumerate(alerts, 1):
            print(f"  {i}. {alert.severity.value.upper()}: {alert.title}")
        
        # Send alerts to Slack
        print("\n+ Sending alerts to Slack...")
        sent_count = notifier.send_alerts(alerts)
        
        print(f"\n+ Slack notifications:")
        print(f"  - Alerts sent: {sent_count}/{len(alerts)}")
        print(f"  - Webhook calls: {mock_post.call_count}")
        
        # Verify Slack payloads
        if mock_post.called:
            print(f"\n+ Slack payload details:")
            for i, call in enumerate(mock_post.call_args_list, 1):
                payload = call[1]['json']
                blocks = payload.get('blocks', [])
                header_text = blocks[0].get('text', {}).get('text', '') if blocks else ''
                print(f"  Call #{i}: {header_text}")
    
    print("\n[+] End-to-end integration test completed")
    return sent_count == len(alerts)


def test_scheduler_with_mock():
    """Test scheduler with mock monitoring."""
    print("\n" + "="*60)
    print("TEST 4: Scheduler with Mock Monitoring")
    print("="*60)
    
    # Create scheduler with short interval for testing
    scheduler = MonitorScheduler(interval=5)
    
    print(f"\n+ Scheduler created:")
    print(f"  - Interval: {scheduler.interval}s")
    print(f"  - Running: {scheduler.is_running}")
    
    # Mock the monitoring job
    with patch.object(scheduler.monitor_agent, 'monitor') as mock_monitor, \
         patch.object(scheduler.slack_notifier, 'send_alerts') as mock_send, \
         patch.object(scheduler.slack_notifier, 'send_test_message') as mock_test:
        
        # Setup mocks
        mock_alert = AlertMessage(
            alert_id="sched-001",
            timestamp=datetime.now(),
            severity=AlertSeverity.HIGH,
            issue_type=IssueType.HUNG_THREAD,
            title="Scheduled Alert Test",
            description="Test alert from scheduler",
            server_url="http://localhost:5555",
            recommendations=["Test recommendation"]
        )
        mock_monitor.return_value = [mock_alert]
        mock_send.return_value = 1
        mock_test.return_value = True
        
        # Start monitoring (will run once immediately)
        print("\n+ Starting scheduler...")
        scheduler.start_monitoring()
        
        print(f"\n+ Scheduler status:")
        print(f"  - Running: {scheduler.is_running}")
        print(f"  - Run count: {scheduler.run_count}")
        print(f"  - Alert count: {scheduler.alert_count}")
        
        # Get status
        status = scheduler.get_status()
        print(f"\n+ Status details:")
        print(f"  - Is running: {status['is_running']}")
        print(f"  - Interval: {status['interval']}s")
        print(f"  - Total runs: {status['run_count']}")
        print(f"  - Total alerts: {status['alert_count']}")
        
        # Stop monitoring
        print("\n+ Stopping scheduler...")
        scheduler.stop_monitoring()
        
        print(f"  - Running: {scheduler.is_running}")
    
    print("\n[+] Scheduler test completed")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MONITOR AGENT + SLACK NOTIFICATION TESTS")
    print("="*70)
    
    results = []
    
    # Test 1: Slack Notifier
    try:
        result1 = test_slack_notifier()
        results.append(("Slack Notifier", result1))
    except Exception as e:
        print(f"\n[X] Test 1 failed: {str(e)}")
        results.append(("Slack Notifier", False))
    
    # Test 2: Monitor Agent
    try:
        result2 = test_monitor_agent_with_mock_data()
        results.append(("Monitor Agent", len(result2) > 0))
    except Exception as e:
        print(f"\n[X] Test 2 failed: {str(e)}")
        results.append(("Monitor Agent", False))
    
    # Test 3: End-to-End Integration
    try:
        result3 = test_slack_integration_end_to_end()
        results.append(("E2E Integration", result3))
    except Exception as e:
        print(f"\n[X] Test 3 failed: {str(e)}")
        results.append(("E2E Integration", False))
    
    # Test 4: Scheduler
    try:
        result4 = test_scheduler_with_mock()
        results.append(("Scheduler", result4))
    except Exception as e:
        print(f"\n[X] Test 4 failed: {str(e)}")
        results.append(("Scheduler", False))
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED")
    else:
        print("[FAILURE] SOME TESTS FAILED")
    print("="*70)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

# Made with Bob
