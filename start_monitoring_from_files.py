"""Start continuous monitoring by reading thread dumps from Integration Server file system."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import time
import signal
from datetime import datetime
from typing import Optional
from pathlib import Path
import glob

from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent
from agents.monitor.slack_notifier import SlackNotifier
from shared.models import AlertMessage, AlertSeverity, IssueType
from shared.config import config
from shared.utils import setup_logging
from collect_with_jstack import parse_jstack_output, save_thread_dump

logger = setup_logging("monitoring_files")

class FileBasedMonitor:
    """Continuous monitoring by reading thread dumps from file system."""
    
    def __init__(self, dump_directory: str, interval: int = 60, send_slack: bool = True):
        """
        Initialize monitor.
        
        Args:
            dump_directory: Directory where Integration Server writes thread dumps
            interval: Monitoring interval in seconds
            send_slack: Whether to send Slack notifications
        """
        self.dump_directory = Path(dump_directory)
        self.interval = interval
        self.send_slack = send_slack
        self.running = False
        self.processed_files = set()  # Track processed files
        
        # Initialize components
        self.analyzer = ThreadDumpAnalyzerAgent()
        self.slack_notifier = SlackNotifier() if send_slack else None
        
        # Statistics
        self.cycle_count = 0
        self.total_alerts = 0
        self.total_hung_threads = 0
        
        logger.info(f"Monitor initialized (directory: {dump_directory}, interval: {interval}s)")
    
    def start(self):
        """Start monitoring."""
        self.running = True
        
        print("="*70)
        print("FILE-BASED THREAD DUMP MONITORING")
        print("="*70)
        print(f"Directory: {self.dump_directory}")
        print(f"Interval: {self.interval} seconds")
        print(f"Slack alerts: {'Enabled' if self.send_slack else 'Disabled'}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Verify directory exists
        if not self.dump_directory.exists():
            print(f"\n[ERROR] Directory not found: {self.dump_directory}")
            print("\nPlease provide the correct path to Integration Server thread dumps")
            print("Example: C:\\SoftwareAG\\IntegrationServer\\instances\\default\\logs\\threaddumps")
            return False
        
        print(f"\n[SUCCESS] Found directory: {self.dump_directory}")
        
        # Send startup notification
        if self.slack_notifier:
            print("\nSending startup notification to Slack...")
            self.slack_notifier.send_test_message()
        
        print("\n" + "="*70)
        print("MONITORING STARTED - Press Ctrl+C to stop")
        print("="*70)
        
        try:
            while self.running:
                self._monitoring_cycle()
                
                if self.running:
                    print(f"\n[WAITING] Next check in {self.interval} seconds...")
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            print("\n\n[STOP] Received interrupt signal")
            self.stop()
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            import traceback
            traceback.print_exc()
            self.stop()
    
    def stop(self):
        """Stop monitoring."""
        self.running = False
        print("\n" + "="*70)
        print("MONITORING STOPPED")
        print("="*70)
        print(f"Total cycles: {self.cycle_count}")
        print(f"Total alerts: {self.total_alerts}")
        print(f"Total hung threads found: {self.total_hung_threads}")
        print("="*70)
    
    def _monitoring_cycle(self):
        """Execute one monitoring cycle."""
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        print(f"\n{'='*70}")
        print(f"CYCLE #{self.cycle_count} - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Step 1: Find new thread dump files
        print("\n[1/3] Looking for new thread dump files...")
        
        # Look for common thread dump file patterns
        patterns = [
            "threaddump*.txt",
            "thread_dump*.txt", 
            "javacore*.txt",
            "*.tdump"
        ]
        
        new_files = []
        for pattern in patterns:
            files = list(self.dump_directory.glob(pattern))
            for file in files:
                if file not in self.processed_files:
                    new_files.append(file)
        
        if not new_files:
            print("[INFO] No new thread dump files found")
            print(f"  Processed files: {len(self.processed_files)}")
            return
        
        # Process the most recent new file
        latest_file = max(new_files, key=lambda f: f.stat().st_mtime)
        print(f"[SUCCESS] Found new file: {latest_file.name}")
        print(f"  Size: {latest_file.stat().st_size} bytes")
        print(f"  Modified: {datetime.fromtimestamp(latest_file.stat().st_mtime)}")
        
        # Step 2: Read and parse thread dump
        print("\n[2/3] Reading and parsing thread dump...")
        
        try:
            with open(latest_file, 'r', encoding='utf-8', errors='ignore') as f:
                dump_content = f.read()
            
            print(f"[SUCCESS] Read {len(dump_content)} bytes")
            
            # Parse threads
            threads = parse_jstack_output(dump_content)
            
            if not threads:
                print("[FAILED] Could not parse threads from file")
                self.processed_files.add(latest_file)
                return
            
            print(f"[SUCCESS] Parsed {len(threads)} threads")
            
            # Mark file as processed
            self.processed_files.add(latest_file)
            
        except Exception as e:
            print(f"[FAILED] Error reading file: {e}")
            return
        
        # Calculate statistics
        hung_count = sum(1 for t in threads if t.is_hung())
        blocked_count = sum(1 for t in threads if t.is_blocked())
        waiting_count = sum(1 for t in threads if t.is_waiting())
        runnable_count = sum(1 for t in threads if t.state == 'RUNNABLE')
        
        # Detect long-running threads (>30s CPU time but not marked as hung)
        long_running_threads = [t for t in threads if t.cpu_time > 30 and not t.is_hung()]
        long_running_count = len(long_running_threads)
        
        print(f"\nThread Statistics:")
        print(f"  Total: {len(threads)}")
        print(f"  Runnable: {runnable_count}")
        print(f"  Blocked: {blocked_count}")
        print(f"  Waiting: {waiting_count}")
        print(f"  Hung: {hung_count}")
        print(f"  Long-Running (>30s): {long_running_count}")
        
        self.total_hung_threads += hung_count
        
        # Save thread dump to our data directory
        storage_path = save_thread_dump(dump_content, threads)
        
        # Step 3: Analyze
        print(f"\n[3/3] Analyzing for issues...")
        analysis = self.analyzer.analyze(threads)
        
        print(f"[SUCCESS] Analysis complete")
        print(f"\nAnalysis Results:")
        print(f"  Severity: {analysis.severity.value.upper()}")
        print(f"  Hung threads: {analysis.hung_threads}")
        print(f"  Blocked threads: {analysis.blocked_threads}")
        print(f"  Deadlocks: {len(analysis.deadlocks)}")
        
        # Display hung threads if any
        if hung_count > 0:
            print(f"\n[WARNING] Found {hung_count} hung thread(s):")
            for thread in threads:
                if thread.is_hung():
                    print(f"  - {thread.name} (CPU: {thread.cpu_time:.2f}s)")
        
        # Display long-running threads if any
        if long_running_count > 0:
            print(f"\n[INFO] Found {long_running_count} long-running thread(s):")
            for thread in long_running_threads:
                print(f"  - {thread.name} (CPU: {thread.cpu_time:.2f}s)")
        
        # Display recommendations
        if analysis.recommendations:
            print(f"\nRecommendations:")
            for i, rec in enumerate(analysis.recommendations[:3], 1):
                print(f"  {i}. {rec}")
        
        # Send alert if needed
        severity = analysis.severity.value
        should_alert = severity in ['critical', 'high', 'medium'] or hung_count > 0 or long_running_count > 0
        
        if should_alert and self.slack_notifier:
            print(f"\n[ALERT] Sending notification to Slack...")
            
            severity_map = {
                'critical': AlertSeverity.CRITICAL,
                'high': AlertSeverity.HIGH,
                'medium': AlertSeverity.MEDIUM,
                'low': AlertSeverity.LOW,
                'info': AlertSeverity.INFO
            }
            
            # Determine alert severity and type
            if hung_count > 0:
                alert_severity = AlertSeverity.CRITICAL
                issue_type = IssueType.HUNG_THREAD
                title = f"🔴 CRITICAL: {hung_count} Hung Thread(s) Detected"
            elif long_running_count > 0:
                alert_severity = AlertSeverity.MEDIUM
                issue_type = IssueType.PERFORMANCE
                title = f"🟡 WARNING: {long_running_count} Long-Running Thread(s) Detected"
            else:
                alert_severity = severity_map.get(severity, AlertSeverity.INFO)
                issue_type = IssueType.PERFORMANCE
                title = f"Thread Monitoring Alert - Cycle #{self.cycle_count}"
            
            # Build thread log details
            thread_log_parts = []
            if hung_count > 0:
                thread_log_parts.append(f"Hung Threads: {hung_count}")
                for thread in threads:
                    if thread.is_hung():
                        thread_log_parts.append(f"  • {thread.name}")
                        thread_log_parts.append(f"    State: {thread.state}")
                        thread_log_parts.append(f"    CPU Time: {thread.cpu_time:.2f}s")
                        thread_log_parts.append(f"    Blocked Count: {thread.blocked_count}")
                        if thread.stack_trace:
                            thread_log_parts.append(f"    Stack: {thread.stack_trace[0]}")
                        thread_log_parts.append("")
            
            if long_running_count > 0:
                thread_log_parts.append(f"Long-Running Threads (>30s): {long_running_count}")
                for thread in long_running_threads[:5]:
                    thread_log_parts.append(f"  • {thread.name}")
                    thread_log_parts.append(f"    State: {thread.state}")
                    thread_log_parts.append(f"    CPU Time: {thread.cpu_time:.2f}s")
                    if thread.stack_trace:
                        thread_log_parts.append(f"    Stack: {thread.stack_trace[0]}")
                    thread_log_parts.append("")
                if long_running_count > 5:
                    thread_log_parts.append(f"  ... and {long_running_count - 5} more threads")
            
            thread_logs = "\n".join(thread_log_parts)
            
            # Create alert
            alert = AlertMessage(
                severity=alert_severity,
                issue_type=issue_type,
                title=title,
                description=f"Detected issues in thread dump from {latest_file.name}",
                timestamp=datetime.now(),
                server_url=config.WEBMETHODS_URL,
                recommendations=analysis.recommendations[:5],
                metadata={
                    'pid': 'N/A (file-based)',
                    'cpu_usage': 0,
                    'memory_usage': 0,
                    'hung_threads': hung_count,
                    'long_running_threads': long_running_count,
                    'pattern': 'FILE_BASED_MONITORING',
                    'thread_logs': thread_logs,
                    'source_file': str(latest_file),
                    'root_cause': f"Analysis from {latest_file.name}",
                    'detailed_analysis': analysis.summary
                }
            )
            
            # Send to Slack
            success = self.slack_notifier.send_alert(alert)
            if success:
                print(f"[SUCCESS] Alert sent to Slack")
                self.total_alerts += 1
            else:
                print(f"[FAILED] Could not send alert to Slack")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor Integration Server thread dumps from file system')
    parser.add_argument('--directory', '-d', 
                       help='Directory containing thread dump files',
                       default=r'C:\SoftwareAG\IntegrationServer\instances\default\logs\threaddumps')
    parser.add_argument('--interval', '-i', type=int, default=60,
                       help='Monitoring interval in seconds (default: 60)')
    parser.add_argument('--no-slack', action='store_true',
                       help='Disable Slack notifications')
    
    args = parser.parse_args()
    
    monitor = FileBasedMonitor(
        dump_directory=args.directory,
        interval=args.interval,
        send_slack=not args.no_slack
    )
    
    monitor.start()


if __name__ == "__main__":
    main()

# Made with Bob
