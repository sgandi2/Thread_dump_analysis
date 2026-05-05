#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Thread Dump Collection using jcmd

This script collects thread dumps from webMethods Integration Server using jcmd,
a modern JDK diagnostic tool that comes with Java 7+.

jcmd is more versatile than jstack and provides better error messages.
It's the recommended tool for modern Java environments.

Usage:
    python collect_with_jcmd.py --pid 9584
    python collect_with_jcmd.py --pid 9584 --output custom_dump.txt
    python collect_with_jcmd.py --list  # List all Java processes
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

def find_jcmd():
    """
    Find jcmd executable in system PATH or JAVA_HOME.
    
    Returns:
        str: Path to jcmd executable or None if not found
    """
    # Try to find jcmd in PATH
    try:
        result = subprocess.run(
            ['where', 'jcmd'] if sys.platform == 'win32' else ['which', 'jcmd'],
            capture_output=True,
            text=True,
            check=True
        )
        jcmd_path = result.stdout.strip().split('\n')[0]
        if os.path.exists(jcmd_path):
            return jcmd_path
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Try JAVA_HOME
    java_home = os.environ.get('JAVA_HOME')
    if java_home:
        jcmd_path = os.path.join(java_home, 'bin', 'jcmd.exe' if sys.platform == 'win32' else 'jcmd')
        if os.path.exists(jcmd_path):
            return jcmd_path
    
    return None

def list_java_processes(jcmd_path):
    """
    List all running Java processes.
    
    Args:
        jcmd_path: Path to jcmd executable
    """
    print("\n[*] Listing all Java processes...\n")
    try:
        result = subprocess.run(
            [jcmd_path],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error listing processes: {e}")
        print(f"Error output: {e.stderr}")
        return False

def collect_thread_dump(pid, jcmd_path, output_file=None):
    """
    Collect thread dump using jcmd.
    
    Args:
        pid: Process ID of the Java process
        jcmd_path: Path to jcmd executable
        output_file: Optional output file path
        
    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\n[*] Collecting thread dump from PID {pid} using jcmd...\n")
    
    try:
        # Run jcmd Thread.print
        result = subprocess.run(
            [jcmd_path, str(pid), 'Thread.print'],
            capture_output=True,
            text=True,
            check=True
        )
        
        thread_dump = result.stdout
        
        # Generate output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = Path('data/thread_dumps')
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f'jcmd_dump_{timestamp}.txt'
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(thread_dump)
        
        print(f"[SUCCESS] Thread dump collected successfully!")
        print(f"[FILE] Saved to: {output_file}")
        print(f"[SIZE] {len(thread_dump)} bytes")
        
        # Count threads
        thread_count = thread_dump.count('"') // 2  # Approximate thread count
        print(f"[THREADS] Approximate thread count: {thread_count}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error collecting thread dump: {e}")
        print(f"Error output: {e.stderr}")
        
        # Provide helpful error messages
        if "Access is denied" in e.stderr or "Unable to open socket file" in e.stderr:
            print("\n[WARNING] Permission Error Detected!")
            print("\nPossible solutions:")
            print("1. Run this script as Administrator (Windows) or with sudo (Linux)")
            print("2. Ensure the target process is running as the same user")
            print("3. Use file-based monitoring instead (recommended for production):")
            print("   python start_monitoring_from_files.py -d 'path/to/diagnostics'")
            print("\nSee THREAD_COLLECTION_METHODS.md for more details.")
        
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Collect thread dumps using jcmd (Java 7+ diagnostic tool)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all Java processes
  python collect_with_jcmd.py --list
  
  # Collect thread dump from specific PID
  python collect_with_jcmd.py --pid 9584
  
  # Collect with custom output file
  python collect_with_jcmd.py --pid 9584 --output my_dump.txt

For more information, see THREAD_COLLECTION_METHODS.md
        """
    )
    
    parser.add_argument(
        '--pid',
        type=int,
        help='Process ID of the Java process'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='Output file path (default: data/thread_dumps/jcmd_dump_TIMESTAMP.txt)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all running Java processes'
    )
    
    args = parser.parse_args()
    
    # Find jcmd
    print("[*] Looking for jcmd...")
    jcmd_path = find_jcmd()
    
    if not jcmd_path:
        print("[ERROR] jcmd not found!")
        print("\nPlease ensure:")
        print("1. Java Development Kit (JDK) is installed")
        print("2. JAVA_HOME environment variable is set")
        print("3. JDK bin directory is in your PATH")
        print("\nOn Windows:")
        print('  set PATH=%PATH%;C:\\Program Files\\Java\\jdk-11\\bin')
        print("\nOn Linux/Mac:")
        print('  export PATH=$PATH:/usr/lib/jvm/java-11-openjdk/bin')
        print("\nAlternatively, use file-based monitoring:")
        print("  python start_monitoring_from_files.py -d 'path/to/diagnostics'")
        sys.exit(1)
    
    print(f"[SUCCESS] Found jcmd at: {jcmd_path}")
    
    # List processes if requested
    if args.list:
        list_java_processes(jcmd_path)
        sys.exit(0)
    
    # Collect thread dump
    if not args.pid:
        print("[ERROR] --pid is required (or use --list to see available processes)")
        parser.print_help()
        sys.exit(1)
    
    success = collect_thread_dump(args.pid, jcmd_path, args.output)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

# Made with Bob
