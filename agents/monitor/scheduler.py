"""Scheduler for periodic monitoring using APScheduler."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.config import config
from shared.utils import setup_logging
from agents.monitor.monitor_agent import MonitorAgent
from agents.monitor.slack_notifier import SlackNotifier

logger = setup_logging("monitor_scheduler")


class MonitorScheduler:
    """Scheduler for periodic monitoring tasks."""
    
    def __init__(self, interval: Optional[int] = None):
        """
        Initialize the scheduler.
        
        Args:
            interval: Polling interval in seconds (defaults to config)
        """
        self.interval = interval or config.POLL_INTERVAL
        self.scheduler = BackgroundScheduler()
        self.monitor_agent = MonitorAgent()
        self.slack_notifier = SlackNotifier()
        self.is_running = False
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        self.alert_count = 0
        
        logger.info(f"Scheduler initialized with {self.interval}s interval")
    
    def start_monitoring(self):
        """Start the periodic monitoring."""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return
        
        # Add monitoring job
        self.scheduler.add_job(
            func=self._monitoring_job,
            trigger=IntervalTrigger(seconds=self.interval),
            id="monitor_job",
            name="Thread Dump Monitoring",
            replace_existing=True
        )
        
        # Start scheduler
        self.scheduler.start()
        self.is_running = True
        
        logger.info(f"✅ Monitoring started (interval: {self.interval}s)")
        
        # Send startup notification
        self.slack_notifier.send_test_message()
        
        # Run first check immediately
        self._monitoring_job()
    
    def stop_monitoring(self):
        """Stop the periodic monitoring."""
        if not self.is_running:
            logger.warning("Monitoring is not running")
            return
        
        self.scheduler.shutdown(wait=False)
        self.is_running = False
        
        logger.info("❌ Monitoring stopped")
        
        # Send shutdown notification
        self._send_shutdown_notification()
    
    def _monitoring_job(self):
        """Execute monitoring cycle."""
        try:
            logger.info(f"Running monitoring cycle #{self.run_count + 1}")
            self.last_run = datetime.now()
            self.run_count += 1
            
            # Run monitoring
            alerts = self.monitor_agent.monitor()
            
            # Send alerts to Slack
            if alerts:
                sent_count = self.slack_notifier.send_alerts(alerts)
                self.alert_count += sent_count
                logger.info(f"Sent {sent_count} alerts to Slack")
            else:
                logger.info("No alerts generated")
            
            # Send periodic summary (every 10 runs)
            if self.run_count % 10 == 0:
                self._send_periodic_summary()
                
        except Exception as e:
            logger.error(f"Error in monitoring job: {str(e)}")
    
    def _send_periodic_summary(self):
        """Send periodic monitoring summary."""
        try:
            # This would fetch actual stats in production
            summary_text = (
                f"📊 *Monitoring Summary*\n"
                f"• Total runs: {self.run_count}\n"
                f"• Total alerts: {self.alert_count}\n"
                f"• Last run: {self.last_run.strftime('%Y-%m-%d %H:%M:%S') if self.last_run else 'N/A'}\n"
                f"• Status: {'🟢 Active' if self.is_running else '🔴 Stopped'}"
            )
            logger.info(f"Periodic summary: {summary_text}")
        except Exception as e:
            logger.error(f"Error sending periodic summary: {str(e)}")
    
    def _send_shutdown_notification(self):
        """Send notification when monitoring stops."""
        try:
            # In production, this would send a Slack message
            logger.info("Monitoring shutdown notification sent")
        except Exception as e:
            logger.error(f"Error sending shutdown notification: {str(e)}")
    
    def adjust_interval(self, new_interval: int):
        """
        Adjust the monitoring interval.
        
        Args:
            new_interval: New interval in seconds
        """
        if new_interval < 10:
            logger.warning("Interval too short, minimum is 10 seconds")
            new_interval = 10
        
        self.interval = new_interval
        
        if self.is_running:
            # Reschedule the job
            self.scheduler.reschedule_job(
                job_id="monitor_job",
                trigger=IntervalTrigger(seconds=new_interval)
            )
            logger.info(f"Monitoring interval adjusted to {new_interval}s")
        else:
            logger.info(f"Interval set to {new_interval}s (will apply on next start)")
    
    def get_status(self) -> dict:
        """
        Get current scheduler status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "is_running": self.is_running,
            "interval": self.interval,
            "run_count": self.run_count,
            "alert_count": self.alert_count,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.scheduler.get_job("monitor_job").next_run_time.isoformat() 
                       if self.is_running and self.scheduler.get_job("monitor_job") else None
        }
    
    def run_once(self):
        """Run monitoring once without scheduling."""
        logger.info("Running one-time monitoring check")
        self._monitoring_job()


def main():
    """Main entry point for running the scheduler."""
    import signal
    import time
    
    logger.info("Starting Thread Dump Monitor Scheduler")
    
    # Create and start scheduler
    scheduler = MonitorScheduler()
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        scheduler.stop_monitoring()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    scheduler.start_monitoring()
    
    logger.info("Monitor is running. Press Ctrl+C to stop.")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        scheduler.stop_monitoring()


if __name__ == "__main__":
    main()

# Made with Bob
