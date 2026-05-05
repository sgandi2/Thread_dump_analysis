#!/usr/bin/env python3
"""
Main entry point for running the Thread Dump Monitor Agent.

This script starts the monitoring system with scheduling and Slack notifications.
"""

import sys
import os
import signal
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.config import config
from shared.utils import setup_logging
from agents.monitor.scheduler import MonitorScheduler

logger = setup_logging("main")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Thread Dump Monitor Agent for webMethods Integration Server"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=config.POLL_INTERVAL,
        help=f"Monitoring interval in seconds (default: {config.POLL_INTERVAL})"
    )
    
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run monitoring once and exit (no scheduling)"
    )
    
    parser.add_argument(
        "--test-slack",
        action="store_true",
        help="Send a test message to Slack and exit"
    )
    
    parser.add_argument(
        "--server-url",
        type=str,
        default=config.WEBMETHODS_URL,
        help=f"webMethods server URL (default: {config.WEBMETHODS_URL})"
    )
    
    return parser.parse_args()


def test_slack_integration():
    """Test Slack integration."""
    from agents.monitor.slack_notifier import SlackNotifier
    
    logger.info("Testing Slack integration...")
    notifier = SlackNotifier()
    
    if notifier.send_test_message():
        logger.info("✅ Slack integration test successful!")
        return True
    else:
        logger.error("❌ Slack integration test failed!")
        return False


def run_once(server_url: str):
    """Run monitoring once without scheduling."""
    from agents.monitor.monitor_agent import MonitorAgent
    from agents.monitor.slack_notifier import SlackNotifier
    
    logger.info("Running one-time monitoring check...")
    
    agent = MonitorAgent()
    notifier = SlackNotifier()
    
    alerts = agent.monitor(server_url)
    
    if alerts:
        logger.info(f"Generated {len(alerts)} alerts")
        sent = notifier.send_alerts(alerts)
        logger.info(f"Sent {sent} alerts to Slack")
    else:
        logger.info("No alerts generated")


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Print banner
    print("=" * 70)
    print("  Thread Dump Analysis AI Agent - Monitor")
    print("  Powered by LangGraph & Ollama")
    print("=" * 70)
    print()
    
    # Validate configuration
    if not config.validate():
        logger.warning("Configuration validation failed. Some features may not work.")
    
    # Test Slack integration if requested
    if args.test_slack:
        success = test_slack_integration()
        sys.exit(0 if success else 1)
    
    # Run once if requested
    if args.once:
        run_once(args.server_url)
        sys.exit(0)
    
    # Start scheduled monitoring
    logger.info(f"Starting monitor with {args.interval}s interval")
    logger.info(f"Monitoring server: {args.server_url}")
    logger.info(f"Slack channel: {config.SLACK_CHANNEL}")
    logger.info(f"Hung thread threshold: {config.HUNG_THREAD_THRESHOLD}s")
    print()
    
    scheduler = MonitorScheduler(interval=args.interval)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("\nReceived shutdown signal. Stopping monitor...")
        scheduler.stop_monitoring()
        logger.info("Monitor stopped. Goodbye!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    try:
        scheduler.start_monitoring()
        
        print("✅ Monitor is running!")
        print(f"📊 Checking every {args.interval} seconds")
        print(f"🔔 Alerts will be sent to {config.SLACK_CHANNEL}")
        print("\nPress Ctrl+C to stop\n")
        
        # Keep the main thread alive
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\nKeyboard interrupt received")
        scheduler.stop_monitoring()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        scheduler.stop_monitoring()
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
