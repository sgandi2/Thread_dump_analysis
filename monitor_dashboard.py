#!/usr/bin/env python3
"""
Real-time Monitoring Dashboard
Shows live status of the complete workflow: Collection → Analysis → Remediation
"""
import json
import sys
import io
import time
from pathlib import Path
from datetime import datetime, timedelta
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def format_time_ago(timestamp_str):
    """Format timestamp as 'X minutes ago'"""
    try:
        dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        now = datetime.now()
        diff = now - dt
        
        if diff.total_seconds() < 60:
            return f"{int(diff.total_seconds())}s ago"
        elif diff.total_seconds() < 3600:
            return f"{int(diff.total_seconds() / 60)}m ago"
        else:
            return f"{int(diff.total_seconds() / 3600)}h ago"
    except:
        return timestamp_str


def get_severity_icon(severity):
    """Get icon for severity level"""
    icons = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🔵',
        'info': '🟢'
    }
    return icons.get(severity.lower(), '⚪')


def main():
    """Main dashboard loop"""
    
    while True:
        clear_screen()
        
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 15 + "🔍 LIVE MONITORING DASHBOARD" + " " * 24 + "║")
        print("╚" + "═" * 68 + "╝")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⏰ Current Time: {now}")
        print("─" * 70)
        
        # 1. COLLECTION STATUS
        print("\n📊 STEP 1: THREAD DUMP COLLECTION")
        print("─" * 70)
        
        dump_dir = Path("data/thread_dumps")
        json_dumps = sorted(dump_dir.glob("jstack_dump_*.json"), reverse=True)
        
        print(f"Total Dumps Collected: {len(json_dumps)}")
        
        if json_dumps:
            latest_dump = json_dumps[0]
            timestamp = latest_dump.stem.replace("jstack_dump_", "")
            time_ago = format_time_ago(timestamp)
            
            with open(latest_dump, 'r') as f:
                data = json.load(f)
            
            print(f"\n✅ Latest Collection:")
            print(f"   Time: {timestamp} ({time_ago})")
            print(f"   Threads: {data.get('thread_count', 0)}")
            print(f"   File: {latest_dump.name}")
            
            # Calculate next collection
            try:
                last_time = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
                next_time = last_time + timedelta(seconds=300)
                now_dt = datetime.now()
                
                if next_time > now_dt:
                    time_until = next_time - now_dt
                    minutes = int(time_until.total_seconds() / 60)
                    seconds = int(time_until.total_seconds() % 60)
                    print(f"\n⏳ Next Collection: in {minutes}m {seconds}s")
                else:
                    print(f"\n⏳ Next Collection: should be happening now...")
            except:
                pass
        else:
            print("\n⚠️  No dumps collected yet")
        
        # 2. ANALYSIS STATUS
        print("\n\n🤖 STEP 2: AI ANALYSIS (LangGraph Analyzer)")
        print("─" * 70)
        
        analysis_dir = Path("data/analysis_results")
        analysis_files = sorted(analysis_dir.glob("analysis_*.json"), reverse=True)
        
        print(f"Total Analyses Completed: {len(analysis_files)}")
        
        if analysis_files:
            latest_analysis = analysis_files[0]
            timestamp = latest_analysis.stem.replace("analysis_", "")
            time_ago = format_time_ago(timestamp)
            
            with open(latest_analysis, 'r') as f:
                data = json.load(f)
            
            severity = data.get('severity', 'unknown')
            icon = get_severity_icon(severity)
            
            print(f"\n✅ Latest Analysis:")
            print(f"   Time: {timestamp} ({time_ago})")
            print(f"   Severity: {icon} {severity.upper()}")
            print(f"   Hung Threads: {data.get('hung_threads', 0)}")
            print(f"   Blocked Threads: {data.get('blocked_threads', 0)}")
            print(f"   Deadlocks: {data.get('deadlock_count', 0)}")
            
            if data.get('recommendations'):
                print(f"\n   💡 Recommendations:")
                for rec in data['recommendations'][:3]:  # Show first 3
                    print(f"      • {rec}")
        else:
            print("\n⚠️  No analyses completed yet")
        
        # 3. ALERTS STATUS
        print("\n\n🚨 STEP 3: ALERTS & NOTIFICATIONS")
        print("─" * 70)
        
        alerts_dir = Path("data/alerts")
        alert_files = sorted(alerts_dir.glob("alert_*.json"), reverse=True)
        
        print(f"Total Alerts Generated: {len(alert_files)}")
        
        if alert_files:
            print(f"\n📋 Recent Alerts:")
            for alert_file in alert_files[:3]:  # Show last 3
                try:
                    with open(alert_file, 'r') as f:
                        alert = json.load(f)
                    
                    severity = alert.get('severity', 'unknown')
                    icon = get_severity_icon(severity)
                    title = alert.get('title', 'No title')
                    timestamp = alert.get('timestamp', '')
                    
                    print(f"   {icon} [{severity.upper()}] {title}")
                    if timestamp:
                        print(f"      Time: {timestamp}")
                except:
                    pass
        else:
            print("\n✅ No alerts - System is healthy!")
        
        # 4. REMEDIATION STATUS
        print("\n\n🔧 STEP 4: REMEDIATION ACTIONS")
        print("─" * 70)
        
        # Check if any remediation actions were taken
        remediation_dir = Path("data/remediation")
        if remediation_dir.exists():
            remediation_files = sorted(remediation_dir.glob("remediation_*.json"), reverse=True)
            print(f"Total Remediation Actions: {len(remediation_files)}")
            
            if remediation_files:
                print(f"\n📋 Recent Actions:")
                for rem_file in remediation_files[:3]:
                    try:
                        with open(rem_file, 'r') as f:
                            rem = json.load(f)
                        
                        action = rem.get('action_type', 'unknown')
                        status = rem.get('status', 'unknown')
                        timestamp = rem.get('timestamp', '')
                        
                        status_icon = "✅" if status == "success" else "❌"
                        print(f"   {status_icon} {action.upper()}")
                        if timestamp:
                            print(f"      Time: {timestamp}")
                    except:
                        pass
            else:
                print("\n✅ No remediation actions needed")
        else:
            print("✅ No remediation actions needed - System is healthy!")
        
        # SYSTEM STATISTICS
        print("\n\n📈 SYSTEM STATISTICS")
        print("─" * 70)
        print(f"   Monitoring Interval: 5 minutes (300 seconds)")
        print(f"   Collection Method: jstack (direct JVM access)")
        print(f"   Analysis Engine: LangGraph Analyzer Agent")
        print(f"   Alert System: Slack notifications")
        print(f"   Remediation: LangGraph Remediation Agent")
        
        # WORKFLOW STATUS
        print("\n\n🔄 COMPLETE WORKFLOW STATUS")
        print("─" * 70)
        
        collection_ok = len(json_dumps) > 0
        analysis_ok = len(analysis_files) > 0
        
        print(f"   {'✅' if collection_ok else '⏳'} Collection → {'✅' if analysis_ok else '⏳'} Analysis → {'✅' if len(alert_files) == 0 else '🚨'} Alerts → {'✅' if not remediation_dir.exists() or len(list(remediation_dir.glob('*.json'))) == 0 else '🔧'} Remediation")
        
        print("\n" + "═" * 70)
        print("💡 Press Ctrl+C to exit | Refreshing every 10 seconds...")
        print("═" * 70)
        
        # Wait 10 seconds before refresh
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring dashboard stopped.")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring dashboard stopped.")

# Made with Bob
