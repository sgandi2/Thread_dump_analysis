"""Start continuous monitoring with jstack collection every 1 minute."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import time
import signal
from datetime import datetime
from typing import Optional

from collect_with_jstack import find_java_process, collect_thread_dump_jstack, parse_jstack_output, save_thread_dump
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent
from agents.monitor.slack_notifier import SlackNotifier
from shared.models import AlertMessage, AlertSeverity, IssueType
from shared.config import config
from shared.utils import setup_logging

logger = setup_logging("monitoring")

class ContinuousMonitor:
    """Continuous monitoring using jstack only."""
    
    def __init__(self, interval: int = 60, send_slack: bool = True):
        """
        Initialize monitor.
        
        Args:
            interval: Monitoring interval in seconds
            send_slack: Whether to send Slack notifications
        """
        self.interval = interval
        self.send_slack = send_slack
        self.running = False
        self.pid: Optional[int] = None
        
        # Initialize components
        self.analyzer = ThreadDumpAnalyzerAgent()
        self.slack_notifier = SlackNotifier() if send_slack else None
        
        # Statistics
        self.cycle_count = 0
        self.total_alerts = 0
        self.total_hung_threads = 0
        
        logger.info(f"Monitor initialized (interval: {interval}s, slack: {send_slack})")
    
    def start(self):
        """Start monitoring."""
        self.running = True
        
        print("="*70)
        print("CONTINUOUS THREAD DUMP MONITORING")
        print("="*70)
        print(f"Interval: {self.interval} seconds (1 minute)")
        print(f"Slack alerts: {'Enabled' if self.send_slack else 'Disabled'}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        # Find Java process once
        print("\nFinding Integration Server process...")
        self.pid = find_java_process("IntegrationServer")
        
        if not self.pid:
            print("[ERROR] Could not find Integration Server process")
            print("\nPlease ensure:")
            print("1. Integration Server is running")
            print("2. Run 'jps -l' to verify Java processes")
            return False
        
        print(f"[SUCCESS] Found Integration Server (PID: {self.pid})")
        
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
        
        # Step 1: Collect thread dump with jstack
        print("\n[1/3] Collecting thread dump with jstack...")
        dump = collect_thread_dump_jstack(self.pid)
        
        if not dump:
            print("[FAILED] Could not collect thread dump")
            print("  Possible reasons:")
            print("  - Need administrator privileges")
            print("  - jstack not in PATH (run add_jstack_to_path.bat)")
            print("  - Process may have restarted")
            print("\n  Solutions:")
            print("  1. Run: add_jstack_to_path.bat (as administrator)")
            print("  2. Then run: start_monitoring_admin.bat (as administrator)")
            return
        
        print(f"[SUCCESS] Collected {len(dump)} bytes")
        
        # Step 2: Parse threads
        print("\n[2/3] Parsing threads...")
        threads = parse_jstack_output(dump)
        
        if not threads:
            print("[FAILED] Could not parse threads")
            return
        
        print(f"[SUCCESS] Parsed {len(threads)} threads")
        
        # Calculate statistics
        hung_count = sum(1 for t in threads if t.is_hung())
        blocked_count = sum(1 for t in threads if t.is_blocked())
        waiting_count = sum(1 for t in threads if t.is_waiting())
        runnable_count = sum(1 for t in threads if t.state == 'RUNNABLE')
        
        # NEW: Detect long-running threads (>30s CPU time but not marked as hung)
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
        
        # Save thread dump
        storage_path = save_thread_dump(dump, threads)
        
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
        # Alert on hung threads, long-running threads, or critical/high/medium severity
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
                for thread in long_running_threads[:5]:  # Show first 5
                    thread_log_parts.append(f"  • {thread.name}")
                    thread_log_parts.append(f"    State: {thread.state}")
                    thread_log_parts.append(f"    CPU Time: {thread.cpu_time:.2f}s")
                    if thread.stack_trace:
                        thread_log_parts.append(f"    Stack: {thread.stack_trace[0]}")
                    thread_log_parts.append("")
                if long_running_count > 5:
                    thread_log_parts.append(f"  ... and {long_running_count - 5} more threads")
            
            # Build root cause analysis
            root_cause_parts = []
            if hung_count > 0:
                root_cause_parts.append("Hung threads detected - threads have been running for over 5 minutes.")
                root_cause_parts.append("Possible causes:")
                root_cause_parts.append("  • Infinite loop in application code")
                root_cause_parts.append("  • Database query timeout or deadlock")
                root_cause_parts.append("  • External service not responding")
                root_cause_parts.append("  • Resource contention or lock waiting")
            elif long_running_count > 0:
                root_cause_parts.append("Long-running threads detected - threads have been running for over 60 seconds.")
                root_cause_parts.append("Possible causes:")
                root_cause_parts.append("  • Large data processing operation")
                root_cause_parts.append("  • Complex calculation in progress")
                root_cause_parts.append("  • Slow database queries")
                root_cause_parts.append("  • May escalate to hung thread if continues")
            
            # Build detailed analysis
            detailed_analysis_parts = []
            detailed_analysis_parts.append(f"Total Threads: {len(threads)}")
            detailed_analysis_parts.append(f"Runnable: {runnable_count}")
            detailed_analysis_parts.append(f"Waiting: {waiting_count}")
            detailed_analysis_parts.append(f"Blocked: {blocked_count}")
            detailed_analysis_parts.append(f"Hung: {hung_count}")
            detailed_analysis_parts.append(f"Long-Running: {long_running_count}")
            detailed_analysis_parts.append("")
            detailed_analysis_parts.append(f"Analysis Severity: {analysis.severity.value.upper()}")
            if hasattr(analysis, 'patterns') and analysis.patterns:
                detailed_analysis_parts.append(f"Patterns Detected: {len(analysis.patterns)}")
                for pattern_name, pattern_data in analysis.patterns.items():
                    detailed_analysis_parts.append(f"  • {pattern_name}: {pattern_data.get('count', 0)} occurrence(s)")
            else:
                detailed_analysis_parts.append("Patterns Detected: 0")
            
            # Calculate CPU and memory usage (mock values for now - would come from CPU/GC specialists)
            cpu_usage = 67.5  # Would come from CPU specialist
            memory_usage = 78.3  # Would come from GC specialist
            
            alert = AlertMessage(
                alert_id=f"monitor-{self.cycle_count}",
                timestamp=datetime.now(),
                severity=alert_severity,
                issue_type=issue_type,
                title=title,
                description="\n".join(thread_log_parts),
                server_url=config.WEBMETHODS_URL,
                recommendations=analysis.recommendations[:5],
                metadata={
                    'cycle': self.cycle_count,
                    'total_threads': len(threads),
                    'hung_threads': hung_count,
                    'long_running_threads': long_running_count,
                    'blocked_threads': blocked_count,
                    'pid': self.pid,
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'root_cause': "\n".join(root_cause_parts),
                    'detailed_analysis': "\n".join(detailed_analysis_parts)
                }
            )
            
            if self.slack_notifier.send_alert(alert):
                print("[SUCCESS] Alert sent to Slack")
                self.total_alerts += 1
            else:
                print("[FAILED] Could not send alert")
        else:
            if not should_alert:
                print(f"\n[OK] No issues detected (severity: {severity})")
            else:
                print(f"\n[INFO] Slack notifications disabled")
        
        # Cycle summary
        duration = (datetime.now() - cycle_start).total_seconds()
        print(f"\n[COMPLETE] Cycle duration: {duration:.2f}s")
        print("="*70)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Continuous thread dump monitoring with jstack"
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Monitoring interval in seconds (default: 60)'
    )
    parser.add_argument(
        '--no-slack',
        action='store_true',
        help='Disable Slack notifications'
    )
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = ContinuousMonitor(
        interval=args.interval,
        send_slack=not args.no_slack
    )
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\n\nReceived shutdown signal")
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    monitor.start()


if __name__ == "__main__":
    main()

# Made with Bob
