#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify dashboard data loader is working correctly
"""

import sys
import os
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dashboard.utils.data_loader import DataLoader

def main():
    print("=" * 80)
    print("DASHBOARD DATA LOADER TEST")
    print("=" * 80)
    print()
    
    # Initialize data loader
    data_loader = DataLoader()
    
    print(f"Data directory: {data_loader.data_dir}")
    print(f"Thread dumps directory: {data_loader.thread_dumps_dir}")
    print(f"Thread dumps directory exists: {data_loader.thread_dumps_dir.exists()}")
    print()
    
    # Test 1: Load latest analysis
    print("Test 1: Loading latest analysis...")
    analysis = data_loader.load_latest_analysis()
    
    if analysis:
        print("[OK] Analysis loaded successfully!")
        print(f"  Total threads: {analysis.get('total_threads', 'N/A')}")
        print(f"  Hung threads: {analysis.get('hung_threads', 'N/A')}")
        print(f"  Blocked threads: {analysis.get('blocked_threads', 'N/A')}")
        print(f"  Deadlocks: {analysis.get('deadlock_count', 'N/A')}")
        print(f"  Severity: {analysis.get('severity', 'N/A')}")
        print(f"  Timestamp: {analysis.get('timestamp', 'N/A')}")
    else:
        print("✗ Failed to load analysis")
    print()
    
    # Test 2: Get server metrics
    print("Test 2: Getting server metrics...")
    metrics = data_loader.get_server_metrics()
    
    print("[OK] Metrics retrieved:")
    print(f"  Server Health: {metrics['server_health']}")
    print(f"  Active Threads: {metrics['active_threads']}")
    print(f"  Hung Threads: {metrics['hung_threads']}")
    print(f"  Blocked Threads: {metrics['blocked_threads']}")
    print(f"  Deadlocks: {metrics.get('deadlocks', 0)}")
    print(f"  CPU Usage: {metrics['cpu_usage']:.1f}%")
    print(f"  Memory Usage: {metrics['memory_usage']:.1f}%")
    print()
    
    # Test 3: Get thread list
    print("Test 3: Getting thread list...")
    threads = data_loader.get_thread_list()
    
    print(f"[OK] Loaded {len(threads)} threads")
    
    if threads:
        # Count by status
        hung = sum(1 for t in threads if t['status'] == 'Hung')
        blocked = sum(1 for t in threads if t['status'] == 'Blocked')
        waiting = sum(1 for t in threads if t['status'] == 'Waiting')
        normal = sum(1 for t in threads if t['status'] == 'Normal')
        
        print(f"  Hung: {hung}")
        print(f"  Blocked: {blocked}")
        print(f"  Waiting: {waiting}")
        print(f"  Normal: {normal}")
        print()
        
        # Show first 5 threads
        print("  First 5 threads:")
        for i, thread in enumerate(threads[:5], 1):
            print(f"    {i}. {thread['name']} - {thread['state']} - {thread['status']}")
    print()
    
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == '__main__':
    main()

# Made with Bob
