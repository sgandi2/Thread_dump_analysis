#!/usr/bin/env python3
"""
Collect Thread Dumps from webMethods and Analyze

This script:
1. Copies thread dump files from webMethods Integration Server diagnostics directory
2. Stores them in the project's data/thread_dumps folder
3. Analyzes them automatically
4. Displays results

Usage:
    python collect_and_analyze.py
    python collect_and_analyze.py --source "C:\SoftwareAG\IntegrationServer\instances\default\logs\diagnostics"
    python collect_and_analyze.py --source "path/to/diagnostics" --analyze-all
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from datetime import datetime
import subprocess

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def print_section(text):
    """Print section header."""
    print(f"\n{'='*70}")
    print(f"{text}")
    print(f"{'='*70}\n")

def find_thread_dumps(source_dir):
    """
    Find thread dump files in the source directory.
    
    Args:
        source_dir: Path to webMethods diagnostics directory
        
    Returns:
        List of thread dump file paths
    """
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"[ERROR] Directory not found: {source_dir}")
        return []
    
    # Common thread dump file patterns
    patterns = [
        'threaddump*.txt',
        'thread_dump*.txt',
        'javacore*.txt',
        'dump*.txt'
    ]
    
    thread_dumps = []
    for pattern in patterns:
        thread_dumps.extend(source_path.glob(pattern))
    
    # Sort by modification time (newest first)
    thread_dumps.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return thread_dumps

def copy_thread_dumps(source_files, dest_dir, copy_all=False):
    """
    Copy thread dump files to project directory.
    
    Args:
        source_files: List of source file paths
        dest_dir: Destination directory path
        copy_all: If True, copy all files. If False, copy only new ones.
        
    Returns:
        List of copied file paths
    """
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)
    
    copied_files = []
    skipped_files = []
    
    for source_file in source_files:
        dest_file = dest_path / source_file.name
        
        # Check if file already exists
        if dest_file.exists() and not copy_all:
            # Compare file sizes to see if it's the same file
            if dest_file.stat().st_size == source_file.stat().st_size:
                skipped_files.append(source_file.name)
                continue
        
        try:
            shutil.copy2(source_file, dest_file)
            copied_files.append(dest_file)
            print(f"[COPIED] {source_file.name} ({source_file.stat().st_size:,} bytes)")
        except Exception as e:
            print(f"[ERROR] Failed to copy {source_file.name}: {e}")
    
    if skipped_files:
        print(f"\n[SKIPPED] {len(skipped_files)} file(s) already exist (use --copy-all to override)")
    
    return copied_files

def analyze_thread_dump(dump_file):
    """
    Analyze a thread dump file.
    
    Args:
        dump_file: Path to thread dump file
        
    Returns:
        True if analysis succeeded, False otherwise
    """
    print(f"\n[ANALYZING] {dump_file.name}")
    print("-" * 70)
    
    try:
        result = subprocess.run([
            sys.executable,
            'analyze_collected_dump.py',
            '--file', str(dump_file)
        ], capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.returncode != 0:
            print(f"[ERROR] Analysis failed for {dump_file.name}")
            if result.stderr:
                print(result.stderr)
            return False
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to analyze {dump_file.name}: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Collect thread dumps from webMethods and analyze them',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (will prompt for directory)
  python collect_and_analyze.py
  
  # Specify source directory
  python collect_and_analyze.py --source "C:\\SoftwareAG\\IntegrationServer\\instances\\default\\logs\\diagnostics"
  
  # Copy and analyze all files (including existing ones)
  python collect_and_analyze.py --source "path/to/diagnostics" --copy-all --analyze-all
  
  # Copy only, don't analyze
  python collect_and_analyze.py --source "path/to/diagnostics" --no-analyze
        """
    )
    
    parser.add_argument(
        '--source',
        type=str,
        help='Source directory containing thread dumps (webMethods diagnostics directory)'
    )
    
    parser.add_argument(
        '--destination',
        type=str,
        default='data/thread_dumps',
        help='Destination directory for copied thread dumps (default: data/thread_dumps)'
    )
    
    parser.add_argument(
        '--copy-all',
        action='store_true',
        help='Copy all files, even if they already exist in destination'
    )
    
    parser.add_argument(
        '--analyze-all',
        action='store_true',
        help='Analyze all copied files (default: analyze only newly copied files)'
    )
    
    parser.add_argument(
        '--no-analyze',
        action='store_true',
        help='Copy files but do not analyze them'
    )
    
    parser.add_argument(
        '--latest-only',
        action='store_true',
        help='Copy and analyze only the most recent thread dump'
    )
    
    args = parser.parse_args()
    
    print_header("Thread Dump Collection & Analysis")
    
    # Get source directory
    source_dir = args.source
    if not source_dir:
        print("Please provide the webMethods Integration Server diagnostics directory.")
        print("\nCommon locations:")
        print("  Windows: C:\\SoftwareAG\\IntegrationServer\\instances\\<instanceName>\\logs\\diagnostics")
        print("  Linux:   /opt/softwareag/IntegrationServer/instances/<instanceName>/logs/diagnostics")
        
        default_path = r"C:\SoftwareAG\IntegrationServer\instances\default\logs\diagnostics"
        source_dir = input(f"\nEnter path [{default_path}]: ").strip()
        
        if not source_dir:
            source_dir = default_path
    
    print(f"\n[SOURCE] {source_dir}")
    print(f"[DESTINATION] {args.destination}")
    
    # Find thread dumps
    print_section("Step 1: Finding Thread Dumps")
    
    thread_dumps = find_thread_dumps(source_dir)
    
    if not thread_dumps:
        print("[ERROR] No thread dump files found in source directory.")
        print("\nPlease check:")
        print("1. The directory path is correct")
        print("2. Thread dump files exist in the directory")
        print("3. You have read permissions for the directory")
        return 1
    
    print(f"[FOUND] {len(thread_dumps)} thread dump file(s):")
    for i, dump in enumerate(thread_dumps[:10], 1):
        size = dump.stat().st_size
        mtime = datetime.fromtimestamp(dump.stat().st_mtime)
        print(f"  {i}. {dump.name} ({size:,} bytes, modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    if len(thread_dumps) > 10:
        print(f"  ... and {len(thread_dumps) - 10} more")
    
    # Filter if latest-only
    if args.latest_only:
        thread_dumps = [thread_dumps[0]]
        print(f"\n[INFO] Processing only the latest file: {thread_dumps[0].name}")
    
    # Copy thread dumps
    print_section("Step 2: Copying Thread Dumps")
    
    copied_files = copy_thread_dumps(thread_dumps, args.destination, args.copy_all)
    
    if not copied_files:
        print("\n[INFO] No new files to copy.")
        
        # Check if we should analyze existing files
        if args.analyze_all:
            print("[INFO] Will analyze existing files as requested (--analyze-all)")
            dest_path = Path(args.destination)
            copied_files = list(dest_path.glob('*.txt'))
            copied_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        else:
            print("[INFO] Use --analyze-all to analyze existing files")
            return 0
    else:
        print(f"\n[SUCCESS] Copied {len(copied_files)} file(s) to {args.destination}")
    
    # Analyze thread dumps
    if not args.no_analyze:
        print_section("Step 3: Analyzing Thread Dumps")
        
        files_to_analyze = copied_files
        if args.analyze_all:
            # Analyze all files in destination
            dest_path = Path(args.destination)
            files_to_analyze = list(dest_path.glob('*.txt'))
            files_to_analyze.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        if not files_to_analyze:
            print("[INFO] No files to analyze")
            return 0
        
        print(f"[INFO] Analyzing {len(files_to_analyze)} file(s)...\n")
        
        success_count = 0
        for dump_file in files_to_analyze:
            if analyze_thread_dump(dump_file):
                success_count += 1
        
        print_section("Analysis Complete")
        print(f"[SUCCESS] Analyzed {success_count}/{len(files_to_analyze)} file(s)")
        
        if success_count > 0:
            print("\n[RESULTS] Analysis results saved to: data/analysis_results/")
            print("[ALERTS] Alerts saved to: data/alerts/")
            
            print("\n[NEXT STEPS]")
            print("1. Review analysis results above")
            print("2. Check data/analysis_results/ for detailed JSON reports")
            print("3. Start dashboard for visual analysis:")
            print("   python -m streamlit run dashboard/app_enhanced.py --server.port 8502")
    else:
        print_section("Copy Complete")
        print(f"[SUCCESS] Copied {len(copied_files)} file(s)")
        print("[INFO] Analysis skipped (--no-analyze)")
        print("\nTo analyze later, run:")
        print("  python analyze_collected_dump.py")
    
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
