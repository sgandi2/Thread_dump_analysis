#!/usr/bin/env python3
"""
Integration Bridge for Existing Thread Dump Agent

This script integrates your existing threaddump_agent.py with ThreadHeap Guardian.
It collects thread dumps using your agent and feeds them into our analysis system.

Usage:
    python integrate_existing_agent.py --pid 30864 --cpu 95.5 --memory 45.2
    python integrate_existing_agent.py --json-file alert.json
"""

import sys
import os
import argparse
import json
import subprocess
from pathlib import Path
from datetime import datetime
import shutil

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def run_existing_agent(pid, cpu, memory, jvm_heap=None, json_file=None):
    """
    Run the existing threaddump_agent.py to collect thread dumps.
    
    Args:
        pid: Process ID
        cpu: CPU percentage
        memory: Memory percentage
        jvm_heap: JVM heap percentage (optional)
        json_file: JSON file with metrics (optional)
        
    Returns:
        dict: Result from the agent
    """
    print_header("Step 1: Collecting Thread Dumps with Existing Agent")
    
    # Check if threaddump_agent.py exists
    agent_script = Path('threaddump_agent.py')
    if not agent_script.exists():
        print("[ERROR] threaddump_agent.py not found in current directory")
        print("Please ensure the script is in the same directory as this integration script")
        return None
    
    # Build command
    cmd = [sys.executable, str(agent_script)]
    
    if json_file:
        cmd.extend(['--json-file', json_file])
    else:
        cmd.extend([
            '--pid', str(pid),
            '--cpu', str(cpu),
            '--memory', str(memory)
        ])
        if jvm_heap:
            cmd.extend(['--jvm-heap', str(jvm_heap)])
    
    print(f"Running: {' '.join(cmd)}\n")
    
    try:
        # Run the existing agent
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0:
            print(f"\n[WARNING] Agent returned non-zero exit code: {result.returncode}")
            if result.stderr:
                print(f"Error output: {result.stderr}")
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to run existing agent: {e}")
        return None

def copy_thread_dumps_to_project(source_dir='thread_dumps', dest_dir='data/thread_dumps'):
    """
    Copy thread dumps from existing agent's directory to ThreadHeap Guardian's directory.
    
    Args:
        source_dir: Source directory (existing agent's output)
        dest_dir: Destination directory (ThreadHeap Guardian's data folder)
        
    Returns:
        list: Paths of copied files
    """
    print_header("Step 2: Copying Thread Dumps to ThreadHeap Guardian")
    
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    if not source_path.exists():
        print(f"[ERROR] Source directory not found: {source_dir}")
        return []
    
    # Create destination directory
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # Find thread dump files (txt files, excluding analysis reports)
    thread_dumps = []
    for pattern in ['threaddump_*.txt', 'javacore_*.txt', 'dump_*.txt']:
        thread_dumps.extend(source_path.glob(pattern))
    
    # Exclude analysis reports
    thread_dumps = [f for f in thread_dumps if 'analysis_report' not in f.name]
    
    if not thread_dumps:
        print(f"[WARNING] No thread dump files found in {source_dir}")
        return []
    
    # Sort by modification time (newest first)
    thread_dumps.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"Found {len(thread_dumps)} thread dump file(s):")
    
    copied_files = []
    for dump_file in thread_dumps:
        dest_file = dest_path / dump_file.name
        
        try:
            shutil.copy2(dump_file, dest_file)
            size = dump_file.stat().st_size
            print(f"  [COPIED] {dump_file.name} ({size:,} bytes)")
            copied_files.append(dest_file)
        except Exception as e:
            print(f"  [ERROR] Failed to copy {dump_file.name}: {e}")
    
    print(f"\n[SUCCESS] Copied {len(copied_files)} file(s) to {dest_dir}")
    return copied_files

def analyze_with_threadheap_guardian(dump_files):
    """
    Analyze thread dumps using ThreadHeap Guardian's analyzer.
    
    Args:
        dump_files: List of thread dump file paths
        
    Returns:
        bool: True if analysis succeeded
    """
    print_header("Step 3: Analyzing with ThreadHeap Guardian")
    
    if not dump_files:
        print("[ERROR] No thread dump files to analyze")
        return False
    
    success_count = 0
    
    for dump_file in dump_files:
        print(f"\n[ANALYZING] {dump_file.name}")
        print("-" * 70)
        
        try:
            result = subprocess.run([
                sys.executable,
                'analyze_collected_dump.py',
                '--file', str(dump_file)
            ], capture_output=True, text=True)
            
            if result.stdout:
                print(result.stdout)
            
            if result.returncode == 0:
                success_count += 1
            else:
                print(f"[WARNING] Analysis failed for {dump_file.name}")
                if result.stderr:
                    print(result.stderr)
        
        except Exception as e:
            print(f"[ERROR] Failed to analyze {dump_file.name}: {e}")
    
    print(f"\n[SUMMARY] Successfully analyzed {success_count}/{len(dump_files)} file(s)")
    return success_count > 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Integration bridge for existing thread dump agent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script:
1. Runs your existing threaddump_agent.py to collect thread dumps
2. Copies the dumps to ThreadHeap Guardian's data/thread_dumps folder
3. Analyzes them using ThreadHeap Guardian's analyzer
4. Displays results in the dashboard

Examples:
  # Analyze with CPU and Memory
  python integrate_existing_agent.py --pid 30864 --cpu 95.5 --memory 45.2
  
  # Include JVM heap metrics
  python integrate_existing_agent.py --pid 30864 --cpu 92.0 --memory 88.5 --jvm-heap 91.0
  
  # Read from JSON file
  python integrate_existing_agent.py --json-file alert.json
        """
    )
    
    parser.add_argument('--pid', type=int, help='Process ID to analyze')
    parser.add_argument('--cpu', type=float, help='CPU usage percentage')
    parser.add_argument('--memory', type=float, help='Memory usage percentage')
    parser.add_argument('--jvm-heap', type=float, help='JVM heap usage percentage (optional)')
    parser.add_argument('--json-file', help='Read metrics from JSON file')
    parser.add_argument('--no-dashboard', action='store_true', help='Skip dashboard launch')
    
    args = parser.parse_args()
    
    print_header("ThreadHeap Guardian - Integration Bridge")
    print("Integrating existing thread dump agent with ThreadHeap Guardian")
    
    # Validate arguments
    if args.json_file:
        if not Path(args.json_file).exists():
            print(f"[ERROR] JSON file not found: {args.json_file}")
            return 1
    else:
        if not args.pid or args.cpu is None or args.memory is None:
            parser.print_help()
            print("\n[ERROR] --pid, --cpu, and --memory are required (or use --json-file)")
            return 1
    
    # Step 1: Run existing agent
    result = run_existing_agent(
        args.pid,
        args.cpu,
        args.memory,
        args.jvm_heap,
        args.json_file
    )
    
    if not result:
        print("\n[ERROR] Failed to run existing agent")
        return 1
    
    # Step 2: Copy thread dumps
    copied_files = copy_thread_dumps_to_project()
    
    if not copied_files:
        print("\n[ERROR] No thread dumps were copied")
        return 1
    
    # Step 3: Analyze with ThreadHeap Guardian
    analysis_success = analyze_with_threadheap_guardian(copied_files)
    
    if not analysis_success:
        print("\n[ERROR] Analysis failed")
        return 1
    
    # Step 4: Show results
    print_header("Integration Complete!")
    
    print("✓ Thread dumps collected with existing agent")
    print("✓ Thread dumps copied to ThreadHeap Guardian")
    print("✓ Analysis completed")
    print(f"\n[RESULTS]")
    print(f"  Thread Dumps: data/thread_dumps/")
    print(f"  Analysis Results: data/analysis_results/")
    print(f"  Alerts: data/alerts/")
    
    # Offer to start dashboard
    if not args.no_dashboard:
        print(f"\n[DASHBOARD]")
        response = input("Start ThreadHeap Guardian dashboard? (y/n): ").strip().lower()
        
        if response == 'y':
            print("\nStarting dashboard...")
            print("Dashboard will open at: http://localhost:8502")
            print("Press Ctrl+C to stop.\n")
            
            try:
                subprocess.run([
                    sys.executable,
                    '-m', 'streamlit', 'run',
                    'dashboard/app_enhanced.py',
                    '--server.port', '8502'
                ])
            except KeyboardInterrupt:
                print("\n\nDashboard stopped.")
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
