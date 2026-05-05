#!/usr/bin/env python3
"""
Trigger infinite loop service and collect thread dump immediately
"""
import requests
import time
import subprocess
import sys

def trigger_infinite_loop():
    """Trigger the infinite loop service on Integration Server"""
    print("=" * 70)
    print("TRIGGERING INFINITE LOOP SERVICE")
    print("=" * 70)
    
    # URL for the infinite loop service
    url = "http://localhost:5555/invoke/your.package/infiniteLoopService"
    
    print(f"\n[1/3] Triggering service at: {url}")
    
    try:
        # Trigger the service (don't wait for response as it will hang)
        response = requests.post(
            url,
            auth=('Administrator', 'manage'),
            timeout=2  # Short timeout since service will hang
        )
    except requests.exceptions.Timeout:
        print("[SUCCESS] Service triggered (timeout expected for infinite loop)")
    except requests.exceptions.ConnectionError as e:
        print(f"[INFO] Service may be running: {e}")
    except Exception as e:
        print(f"[WARNING] Could not trigger service: {e}")
        print("[INFO] You may need to trigger it manually from Integration Server")
    
    # Wait a moment for thread to start
    print("\n[2/3] Waiting 5 seconds for thread to start...")
    time.sleep(5)
    
    # Collect thread dump
    print("\n[3/3] Collecting thread dump...")
    try:
        result = subprocess.run(
            ['python', 'collect_with_jstack.py'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("[SUCCESS] Thread dump collected!")
            print("\nNow run: python analyze_collected_dump.py")
            print("Or refresh the dashboard at: http://localhost:8502")
        else:
            print(f"[ERROR] Collection failed: {result.stderr}")
            print("\nTry running with admin privileges:")
            print("Right-click PowerShell → Run as Administrator")
            print("Then run: python collect_with_jstack.py")
    except Exception as e:
        print(f"[ERROR] {e}")
        print("\nManual steps:")
        print("1. Run PowerShell as Administrator")
        print("2. Run: python collect_with_jstack.py")
        print("3. Run: python analyze_collected_dump.py")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n⚠️  NOTE: This will trigger an infinite loop service!")
    print("Make sure you have a way to stop it (restart Integration Server)")
    print("\nPress Ctrl+C now to cancel, or wait 3 seconds to continue...")
    
    try:
        time.sleep(3)
        trigger_infinite_loop()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
        sys.exit(0)

# Made with Bob
