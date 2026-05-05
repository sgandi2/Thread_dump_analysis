"""
Send alerts from existing thread dumps every 1 minute
Alternative solution when jstack cannot collect new dumps
"""

import time
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from analyze_collected_dump import main as analyze_dump

def monitor_and_alert():
    """Monitor existing dumps and send alerts every minute"""
    
    print("=" * 70)
    print("ALERT MONITORING FROM EXISTING DUMPS")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Interval: 60 seconds (1 minute)")
    print("Action: Analyze latest dump and send Slack alert")
    print("=" * 70)
    print()
    
    cycle = 1
    
    while True:
        try:
            print(f"\n{'='*70}")
            print(f"CYCLE #{cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*70}\n")
            
            print("[1/2] Analyzing latest thread dump...")
            
            # Run analysis on latest dump
            result = analyze_dump()
            
            if result == 0:
                print("[SUCCESS] Analysis complete and alert sent to Slack")
            else:
                print("[WARNING] Analysis completed with warnings")
            
            print(f"\n[2/2] Waiting 60 seconds until next cycle...")
            print(f"Next cycle at: {(datetime.now().timestamp() + 60)}")
            
            # Wait 60 seconds
            time.sleep(60)
            cycle += 1
            
        except KeyboardInterrupt:
            print("\n\n" + "="*70)
            print("MONITORING STOPPED BY USER")
            print("="*70)
            print(f"Total cycles completed: {cycle - 1}")
            print(f"Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            break
            
        except Exception as e:
            print(f"\n[ERROR] Cycle #{cycle} failed: {e}")
            print("Continuing to next cycle...")
            time.sleep(60)
            cycle += 1

if __name__ == '__main__':
    monitor_and_alert()

# Made with Bob
