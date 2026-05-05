"""Real-time thread dump collection, monitoring, and analysis."""

import sys
import os
sys.path.append(os.path.dirname(__file__))

import time
import signal
from datetime import datetime
from typing import Optional

from agents.collector.collector_agent import ThreadDumpCollectorAgent
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent
from agents.monitor.slack_notifier import SlackNotifier
from shared.config import config
from shared.utils import setup_logging

logger = setup_logging("realtime_monitor")

class RealtimeMonitor:
    """Real-time thread dump monitoring and analysis."""
    
    def __init__(self, interval: int = 60, send_slack: bool = True):
        """
        Initialize real-time monitor.
        
        Args:
            interval: Monitoring interval in seconds
            send_slack: Whether to send Slack notifications
        """
        self.interval = interval
        self.send_slack = send_slack
        self.running = False
        
        # Initialize agents
        logger.info("Initializing agents...")
        self.collector = ThreadDumpCollectorAgent()
        self.analyzer = ThreadDumpAnalyzerAgent()
        self.slack_notifier = SlackNotifier() if send_slack else None
        
        # Statistics
        self.cycle_count = 0
        self.total_alerts = 0
        self.last_collection_time: Optional[datetime] = None
        
        logger.info(f"Real-time monitor initialized (interval: {interval}s)")
    
    def start(self):
        """Start real-time monitoring."""
        self.running = True
        
        logger.info("="*70)
        logger.info("STARTING REAL-TIME THREAD DUMP MONITORING")
        logger.info("="*70)
        logger.info(f"Server: {config.WEBMETHODS_URL}")
        logger.info(f"Interval: {self.interval} seconds")
        logger.info(f"Slack notifications: {'Enabled' if self.send_slack else 'Disabled'}")
        logger.info("="*70)
        
        # Send startup notification
        if self.slack_notifier:
            self.slack_notifier.send_test_message()
        
        try:
            while self.running:
                self._monitoring_cycle()
                
                if self.running:
                    logger.info(f"\nWaiting {self.interval} seconds until next cycle...")
                    time.sleep(self.interval)
                    
        except KeyboardInterrupt:
            logger.info("\n\nReceived interrupt signal")
            self.stop()
        except Exception as e:
            logger.error(f"Error in monitoring loop: {str(e)}")
            import traceback
            traceback.print_exc()
            self.stop()
    
    def stop(self):
        """Stop monitoring."""
        self.running = False
        logger.info("\n" + "="*70)
        logger.info("STOPPING REAL-TIME MONITORING")
        logger.info("="*70)
        logger.info(f"Total cycles: {self.cycle_count}")
        logger.info(f"Total alerts: {self.total_alerts}")
        logger.info("="*70)
    
    def _monitoring_cycle(self):
        """Execute one monitoring cycle."""
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        logger.info("\n" + "="*70)
        logger.info(f"MONITORING CYCLE #{self.cycle_count}")
        logger.info(f"Time: {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)
        
        # Step 1: Collect thread dump
        logger.info("\n[1/3] Collecting thread dump from Integration Server...")
        try:
            # Run collector agent
            collection_result = self.collector.run()
            
            if collection_result.get("error"):
                logger.error(f"Collection failed: {collection_result.get('error')}")
                return
            
            self.last_collection_time = collection_result.get('timestamp', datetime.now())
            threads = collection_result.get('parsed_threads', [])
            
            logger.info(f"  [SUCCESS] Thread dump collected")
            logger.info(f"  - Timestamp: {self.last_collection_time}")
            logger.info(f"  - Total threads: {len(threads)}")
            logger.info(f"  - Storage: {collection_result.get('metadata', {}).get('storage_path', 'N/A')}")
            
        except Exception as e:
            logger.error(f"  [FAILED] Collection error: {str(e)}")
            return
        
        # Step 2: Analyze thread dump
        logger.info("\n[2/3] Analyzing thread dump...")
        try:
            # Analyze the collected threads
            from shared.models import ThreadInfo
            threads = collection_result.get('parsed_threads', [])
            
            if not threads:
                logger.warning("  [WARNING] No threads to analyze")
                return
            
            analysis_result = self.analyzer.analyze(threads)
            
            logger.info(f"  [SUCCESS] Analysis completed")
            logger.info(f"  - Severity: {analysis_result.severity.value.upper()}")
            logger.info(f"  - Total threads: {analysis_result.total_threads}")
            logger.info(f"  - Hung threads: {analysis_result.hung_threads}")
            logger.info(f"  - Blocked threads: {analysis_result.blocked_threads}")
            logger.info(f"  - Deadlocks: {len(analysis_result.deadlocks)}")
            
            # Display recommendations
            if analysis_result.recommendations:
                logger.info(f"\n  Recommendations:")
                for i, rec in enumerate(analysis_result.recommendations, 1):
                    logger.info(f"    {i}. {rec}")
            
        except Exception as e:
            logger.error(f"  [FAILED] Analysis error: {str(e)}")
            return
        
        # Step 3: Send alerts if needed
        logger.info("\n[3/3] Checking for alerts...")
        
        severity = analysis_result.severity.value
        should_alert = severity in ['critical', 'high', 'medium']
        
        if should_alert and self.slack_notifier:
            logger.info(f"  [ALERT] Severity {severity.upper()} detected - sending Slack notification")
            
            try:
                # Create alert message
                from shared.models import AlertMessage, AlertSeverity, IssueType
                
                severity_map = {
                    'critical': AlertSeverity.CRITICAL,
                    'high': AlertSeverity.HIGH,
                    'medium': AlertSeverity.MEDIUM,
                    'low': AlertSeverity.LOW,
                    'info': AlertSeverity.INFO
                }
                
                alert = AlertMessage(
                    alert_id=f"monitor-{self.cycle_count}",
                    timestamp=datetime.now(),
                    severity=severity_map.get(severity, AlertSeverity.INFO),
                    issue_type=IssueType.PERFORMANCE,
                    title=f"Thread Dump Analysis Alert - Cycle #{self.cycle_count}",
                    description=analysis_result.summary,
                    server_url=config.WEBMETHODS_URL,
                    recommendations=analysis_result.recommendations[:5],  # Limit to 5
                    metadata={
                        'cycle': self.cycle_count,
                        'total_threads': analysis_result.total_threads,
                        'hung_threads': analysis_result.hung_threads,
                        'blocked_threads': analysis_result.blocked_threads,
                        'deadlocks': len(analysis_result.deadlocks)
                    }
                )
                
                if self.slack_notifier.send_alert(alert):
                    logger.info(f"  [SUCCESS] Alert sent to Slack")
                    self.total_alerts += 1
                else:
                    logger.warning(f"  [WARNING] Failed to send alert to Slack")
                    
            except Exception as e:
                logger.error(f"  [ERROR] Failed to create/send alert: {str(e)}")
        else:
            if not should_alert:
                logger.info(f"  [OK] No alerts needed (severity: {severity})")
            else:
                logger.info(f"  [INFO] Slack notifications disabled")
        
        # Cycle summary
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        logger.info(f"\n[CYCLE COMPLETE] Duration: {cycle_duration:.2f}s")
        logger.info("="*70)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Real-time thread dump monitoring and analysis"
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
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (no continuous monitoring)'
    )
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = RealtimeMonitor(
        interval=args.interval,
        send_slack=not args.no_slack
    )
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        logger.info("\nReceived shutdown signal")
        monitor.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    if args.once:
        logger.info("Running single monitoring cycle...")
        monitor._monitoring_cycle()
        logger.info("\nSingle cycle complete")
    else:
        monitor.start()


if __name__ == "__main__":
    main()

# Made with Bob
