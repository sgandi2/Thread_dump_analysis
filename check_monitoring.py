"""
Quick script to check monitoring status and restart if needed
"""
import os
import sys
from pathlib import Path
from datetime import datetime

def check_latest_dump():
    """Check the latest thread dump timestamp"""
    dump_dir = Path("data/thread_dumps")
    
    if not dump_dir.exists():
        print("❌ Thread dumps directory not found!")
        return None
    
    # Get all .txt files (thread dumps)
    txt_files = list(dump_dir.glob("jstack_dump_*.txt"))
    
    if not txt_files:
        print("❌ No thread dumps found!")
        return None
    
    # Sort by modification time
    txt_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest = txt_files[0]
    
    # Get timestamp from filename
    filename = latest.stem  # jstack_dump_20260505_210433
    timestamp_str = filename.split('_')[-2] + filename.split('_')[-1]  # 20260505210433
    
    # Parse timestamp
    dump_time = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
    current_time = datetime.now()
    
    time_diff = (current_time - dump_time).total_seconds()
    
    print(f"\n📊 Monitoring Status Check")
    print(f"{'='*60}")
    print(f"Latest dump: {latest.name}")
    print(f"Dump time: {dump_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Time since last dump: {int(time_diff)} seconds ({int(time_diff/60)} minutes)")
    print(f"{'='*60}\n")
    
    if time_diff > 120:  # More than 2 minutes
        print("⚠️  WARNING: No new dumps in over 2 minutes!")
        print("   The monitoring process may have stopped.")
        print("\n💡 To restart monitoring:")
        print("   1. Close any running start_monitoring_admin.bat windows")
        print("   2. Right-click start_monitoring_admin.bat")
        print("   3. Select 'Run as administrator'")
    else:
        print("✅ Monitoring appears to be active (recent dump found)")
    
    return dump_time

if __name__ == "__main__":
    check_latest_dump()

# Made with Bob
