#!/usr/bin/env python3
"""
Check the status of the monitoring system
Shows recent thread dumps, analysis results, and alerts
"""
import json
import sys
import io
from pathlib import Path
from datetime import datetime, timedelta

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def format_time_ago(timestamp_str):
    """Format timestamp as 'X minutes ago'"""
    try:
        # Parse timestamp from filename format: YYYYMMDD_HHMMSS
        dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
        now = datetime.now()
        diff = now - dt
        
        if diff.total_seconds() < 60:
            return f"{int(diff.total_seconds())} seconds ago"
        elif diff.total_seconds() < 3600:
            return f"{int(diff.total_seconds() / 60)} minutes ago"
        else:
            return f"{int(diff.total_seconds() / 3600)} hours ago"
    except:
        return timestamp_str


def main():
    print("=" * 70)
    print("🔍 MONITORING SYSTEM STATUS")
    print("=" * 70)
    
    # Check thread dumps
    dump_dir = Path("data/thread_dumps")
    json_dumps = sorted(dump_dir.glob("jstack_dump_*.json"), reverse=True)
    
    print(f"\n📊 Thread Dumps Collected: {len(json_dumps)}")
    if json_dumps:
        print(f"\n   Recent dumps:")
        for dump in json_dumps[:5]:  # Show last 5
            timestamp = dump.stem.replace("jstack_dump_", "")
            time_ago = format_time_ago(timestamp)
            
            # Load and show basic stats
            try:
                with open(dump, 'r') as f:
                    data = json.load(f)
                thread_count = data.get('thread_count', 0)
                print(f"   • {timestamp} ({time_ago}) - {thread_count} threads")
            except:
                print(f"   • {timestamp} ({time_ago})")
    
    # Check analysis results
    analysis_dir = Path("data/analysis_results")
    analysis_files = sorted(analysis_dir.glob("analysis_*.json"), reverse=True)
    
    print(f"\n🤖 Analysis Results: {len(analysis_files)}")
    if analysis_files:
        print(f"\n   Recent analyses:")
        for analysis in analysis_files[:5]:  # Show last 5
            timestamp = analysis.stem.replace("analysis_", "")
            time_ago = format_time_ago(timestamp)
            
            try:
                with open(analysis, 'r') as f:
                    data = json.load(f)
                severity = data.get('severity', 'UNKNOWN')
                hung = data.get('hung_threads', 0)
                blocked = data.get('blocked_threads', 0)
                deadlocks = data.get('deadlock_count', 0)
                
                status = "✅ HEALTHY" if severity == "info" else f"⚠️  {severity.upper()}"
                print(f"   • {timestamp} ({time_ago})")
                print(f"     Status: {status} | Hung: {hung} | Blocked: {blocked} | Deadlocks: {deadlocks}")
            except Exception as e:
                print(f"   • {timestamp} ({time_ago}) - Error reading: {e}")
    
    # Check alerts
    alerts_dir = Path("data/alerts")
    alert_files = sorted(alerts_dir.glob("alert_*.json"), reverse=True)
    
    print(f"\n🚨 Alerts Generated: {len(alert_files)}")
    if alert_files:
        print(f"\n   Recent alerts:")
        for alert in alert_files[:5]:  # Show last 5
            try:
                with open(alert, 'r') as f:
                    data = json.load(f)
                severity = data.get('severity', 'UNKNOWN')
                title = data.get('title', 'No title')
                timestamp = data.get('timestamp', '')
                
                print(f"   • [{severity.upper()}] {title}")
                if timestamp:
                    print(f"     Time: {timestamp}")
            except Exception as e:
                print(f"   • Error reading alert: {e}")
    
    # Show monitoring configuration
    print(f"\n⚙️  Configuration:")
    print(f"   Interval: 5 minutes (300 seconds)")
    print(f"   Collection Method: jstack")
    print(f"   Analysis: LangGraph Analyzer Agent")
    print(f"   Alerts: Slack notifications enabled")
    
    # Show next collection time
    if json_dumps:
        latest = json_dumps[0]
        timestamp = latest.stem.replace("jstack_dump_", "")
        try:
            last_time = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            next_time = last_time + timedelta(seconds=300)
            now = datetime.now()
            
            if next_time > now:
                time_until = next_time - now
                minutes = int(time_until.total_seconds() / 60)
                seconds = int(time_until.total_seconds() % 60)
                print(f"\n⏰ Next Collection: in {minutes}m {seconds}s")
            else:
                print(f"\n⏰ Next Collection: should be happening now...")
        except:
            pass
    
    print("\n" + "=" * 70)
    print("💡 Tip: Run this script again to see updated status")
    print("   To stop monitoring: Find the Python process and terminate it")
    print("=" * 70)


if __name__ == "__main__":
    main()

# Made with Bob
