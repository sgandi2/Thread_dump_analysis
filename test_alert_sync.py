"""
Test Alert Synchronization between Slack and Dashboard
This script tests the complete flow:
1. Monitor detects an issue
2. Alert is sent to Slack
3. Alert is saved to data/alerts/
4. Dashboard can load and display the alert
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from agents.monitor.slack_notifier import SlackNotifier
from dashboard.utils.data_loader import DataLoader
from shared.models import AlertMessage, IssueType, AlertSeverity

def create_test_alert():
    """Create a test alert to verify the sync flow"""
    print("=" * 80)
    print("TESTING ALERT SYNCHRONIZATION")
    print("=" * 80)
    
    # Initialize components
    notifier = SlackNotifier()
    data_loader = DataLoader()
    
    # Create test alert using AlertMessage model
    test_alert = AlertMessage(
        severity=AlertSeverity.HIGH,
        issue_type=IssueType.HUNG_THREAD,
        title='Test Alert - Hung Thread Detected',
        description='This is a test alert to verify Slack-Dashboard synchronization',
        timestamp=datetime.now(),
        server_url='http://localhost:5555',
        recommendations=[
            'Review thread stack trace',
            'Check for deadlocks',
            'Consider restarting the service'
        ],
        metadata={
            'pid': '12345',
            'cpu_usage': 85.5,
            'memory_usage': 72.3,
            'hung_threads': 2,
            'long_running_threads': 3,
            'pattern': 'WAITING_ON_LOCK',
            'thread_logs': [
                {
                    'thread_id': 'Thread-1',
                    'name': 'pool-1-thread-1',
                    'state': 'WAITING',
                    'cpu_time': 350.5,
                    'stack_trace': [
                        'java.lang.Object.wait(Native Method)',
                        'com.example.Service.processRequest(Service.java:123)'
                    ]
                }
            ],
            'root_cause': 'Thread waiting on lock for extended period',
            'detailed_analysis': 'Multiple threads are blocked waiting for the same resource lock'
        }
    )
    
    print("\n1. Sending test alert to Slack...")
    try:
        result = notifier.send_alert(test_alert)
        if result:
            print("   [OK] Alert sent to Slack successfully")
        else:
            print("   [WARN] Alert sending failed (check Slack webhook)")
    except Exception as e:
        print(f"   [ERROR] Error sending alert: {e}")
    
    # Wait a moment for file to be written
    time.sleep(1)
    
    print("\n2. Checking if alert was saved to data/alerts/...")
    alerts_dir = Path("data/alerts")
    alert_files = list(alerts_dir.glob("alert_*.json"))
    
    if alert_files:
        print(f"   [OK] Found {len(alert_files)} alert file(s)")
        latest_alert = max(alert_files, key=lambda p: p.stat().st_mtime)
        print(f"   [FILE] Latest: {latest_alert.name}")
        
        # Read and display the alert
        with open(latest_alert, 'r') as f:
            saved_alert = json.load(f)
        
        print("\n3. Alert content:")
        print(f"   - Alert ID: {saved_alert.get('alert_id')}")
        print(f"   - Timestamp: {saved_alert.get('timestamp')}")
        print(f"   - Severity: {saved_alert.get('severity')}")
        print(f"   - Title: {saved_alert.get('title')}")
        print(f"   - Status: {saved_alert.get('status')}")
    else:
        print("   [ERROR] No alert files found in data/alerts/")
        return False
    
    print("\n4. Testing dashboard data loader...")
    try:
        active_alerts = data_loader.load_active_alerts()
        print(f"   [OK] Dashboard can load {len(active_alerts)} active alert(s)")
        
        if active_alerts:
            alert = active_alerts[0]
            print(f"\n5. First alert details:")
            print(f"   - Title: {alert.get('title')}")
            print(f"   - Severity: {alert.get('severity')}")
            print(f"   - Status: {alert.get('status')}")
            print(f"   - Recommendations: {len(alert.get('recommendations', []))}")
            
            if alert.get('metadata'):
                meta = alert['metadata']
                print(f"   - CPU Usage: {meta.get('cpu_usage')}%")
                print(f"   - Memory Usage: {meta.get('memory_usage')}%")
                print(f"   - Hung Threads: {meta.get('hung_threads')}")
    except Exception as e:
        print(f"   [ERROR] Error loading alerts: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("[SUCCESS] ALERT SYNCHRONIZATION TEST COMPLETED")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Start the dashboard: python -m streamlit run dashboard/app_enhanced.py --server.port 8502")
    print("2. Open browser: http://localhost:8502")
    print("3. Check the '🔔 Recent Slack Alerts' section")
    print("4. The test alert should appear in the dashboard")
    
    return True

if __name__ == "__main__":
    create_test_alert()

# Made with Bob
