#!/usr/bin/env python3
"""
Test Local Thread Dump Collection and Analysis

This script helps you test the thread dump collection and analysis workflow locally.
It will guide you through the process step by step.
"""

import os
import sys
from pathlib import Path
import subprocess

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def print_step(number, text):
    """Print a step number and description."""
    print(f"\n[Step {number}] {text}")
    print("-" * 60)

def check_file_exists(filepath):
    """Check if a file exists."""
    return Path(filepath).exists()

def list_thread_dumps():
    """List available thread dump files."""
    dump_dir = Path('data/thread_dumps')
    if not dump_dir.exists():
        return []
    
    dumps = list(dump_dir.glob('*.txt'))
    return sorted(dumps, key=lambda x: x.stat().st_mtime, reverse=True)

def main():
    """Main test workflow."""
    print_header("ThreadHeap Guardian - Local Collection Test")
    
    print("This script will help you:")
    print("1. Check if you have thread dumps")
    print("2. Collect a new thread dump (if needed)")
    print("3. Analyze the thread dump")
    print("4. View the results")
    
    # Step 1: Check for existing thread dumps
    print_step(1, "Checking for existing thread dumps")
    
    dumps = list_thread_dumps()
    if dumps:
        print(f"Found {len(dumps)} thread dump(s):")
        for i, dump in enumerate(dumps[:5], 1):
            size = dump.stat().st_size
            print(f"  {i}. {dump.name} ({size:,} bytes)")
        
        if len(dumps) > 5:
            print(f"  ... and {len(dumps) - 5} more")
        
        use_existing = input("\nUse existing dump? (y/n): ").strip().lower()
        if use_existing == 'y':
            dump_file = dumps[0]
            print(f"\nUsing: {dump_file}")
            skip_collection = True
        else:
            skip_collection = False
    else:
        print("No existing thread dumps found.")
        skip_collection = False
    
    # Step 2: Collection options
    if not skip_collection:
        print_step(2, "Thread Dump Collection Options")
        
        print("\nChoose collection method:")
        print("1. File-based monitoring (recommended)")
        print("2. Direct collection with jcmd")
        print("3. Manual - I'll provide a file")
        print("4. Skip - Use test data")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            print("\n[File-Based Monitoring]")
            print("This will monitor Integration Server's diagnostics directory.")
            
            default_path = r"C:\SoftwareAG\IntegrationServer\instances\default\logs\diagnostics"
            diag_path = input(f"\nDiagnostics directory [{default_path}]: ").strip()
            if not diag_path:
                diag_path = default_path
            
            if not os.path.exists(diag_path):
                print(f"\n[WARNING] Directory not found: {diag_path}")
                print("Please provide the correct path to your Integration Server diagnostics directory.")
                return
            
            print(f"\nStarting file-based monitoring...")
            print(f"Watching: {diag_path}")
            print("\nPress Ctrl+C to stop monitoring after a thread dump is collected.")
            
            try:
                subprocess.run([
                    sys.executable,
                    'start_monitoring_from_files.py',
                    '--directory', diag_path
                ])
            except KeyboardInterrupt:
                print("\n\nMonitoring stopped.")
            
            # Check for new dumps
            dumps = list_thread_dumps()
            if dumps:
                dump_file = dumps[0]
                print(f"\nFound thread dump: {dump_file}")
            else:
                print("\n[ERROR] No thread dump collected.")
                return
        
        elif choice == '2':
            print("\n[Direct Collection with jcmd]")
            print("Listing Java processes...")
            
            try:
                result = subprocess.run([
                    sys.executable,
                    'collect_with_jcmd.py',
                    '--list'
                ], capture_output=True, text=True)
                
                print(result.stdout)
                
                if result.returncode != 0:
                    print("[ERROR] Failed to list processes.")
                    print("Try file-based monitoring instead.")
                    return
                
                pid = input("\nEnter Integration Server PID: ").strip()
                if not pid.isdigit():
                    print("[ERROR] Invalid PID")
                    return
                
                print(f"\nCollecting thread dump from PID {pid}...")
                result = subprocess.run([
                    sys.executable,
                    'collect_with_jcmd.py',
                    '--pid', pid
                ])
                
                if result.returncode != 0:
                    print("\n[ERROR] Collection failed.")
                    print("Try file-based monitoring instead.")
                    return
                
                dumps = list_thread_dumps()
                if dumps:
                    dump_file = dumps[0]
                else:
                    print("[ERROR] No thread dump found after collection.")
                    return
            
            except Exception as e:
                print(f"[ERROR] {e}")
                return
        
        elif choice == '3':
            print("\n[Manual File Provision]")
            print("Please copy your thread dump file to: data/thread_dumps/")
            input("\nPress Enter when ready...")
            
            dumps = list_thread_dumps()
            if dumps:
                dump_file = dumps[0]
                print(f"\nFound: {dump_file}")
            else:
                print("[ERROR] No thread dump found in data/thread_dumps/")
                return
        
        elif choice == '4':
            print("\n[Using Test Data]")
            print("Skipping collection - will use test data if available")
            dumps = list_thread_dumps()
            if dumps:
                dump_file = dumps[0]
            else:
                print("[ERROR] No test data available.")
                print("Please collect a real thread dump first.")
                return
        
        else:
            print("[ERROR] Invalid choice")
            return
    
    # Step 3: Analyze
    print_step(3, "Analyzing Thread Dump")
    
    print(f"\nAnalyzing: {dump_file}")
    print("This may take a few moments...\n")
    
    try:
        result = subprocess.run([
            sys.executable,
            'analyze_collected_dump.py',
            '--file', str(dump_file)
        ])
        
        if result.returncode != 0:
            print("\n[ERROR] Analysis failed.")
            return
    
    except Exception as e:
        print(f"[ERROR] {e}")
        return
    
    # Step 4: View results
    print_step(4, "Viewing Results")
    
    print("\nAnalysis complete! You can now:")
    print("1. View results in the console output above")
    print("2. Check analysis files in: data/analysis_results/")
    print("3. Start the dashboard for visual analysis")
    
    start_dashboard = input("\nStart dashboard? (y/n): ").strip().lower()
    if start_dashboard == 'y':
        print("\nStarting dashboard...")
        print("Dashboard will open at: http://localhost:8502")
        print("Press Ctrl+C to stop the dashboard.\n")
        
        try:
            subprocess.run([
                sys.executable,
                '-m', 'streamlit', 'run',
                'dashboard/app_enhanced.py',
                '--server.port', '8502'
            ])
        except KeyboardInterrupt:
            print("\n\nDashboard stopped.")
    
    print_header("Test Complete!")
    print("\nNext steps:")
    print("- Review the analysis results")
    print("- Check for hung or long-running threads")
    print("- Follow AI recommendations")
    print("- Set up continuous monitoring if needed")
    print("\nSee LOCAL_COLLECTION_GUIDE.md for more details.")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()

# Made with Bob
