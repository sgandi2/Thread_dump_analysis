#!/usr/bin/env python3
"""
Quick start script for Thread Dump Monitor Agent.

This script provides an easy way to run the monitor agent with different modes.
"""

import sys
import argparse
from agents.monitor.scheduler import MonitorScheduler
from agents.monitor.monitor_agent import MonitorAgent
from agents.monitor.slack_notifier import SlackNotifier
from shared.config import config
from shared.utils import setup_logging

logger = setup_logging("run_monitor")


def run_scheduled(interval: int = None):
    """Run monitor with scheduler (continuous monitoring)."""
    logger.info("=" * 60)
    logger.info("Thread Dump Monitor - Scheduled Mode")
    logger.info("=" * 60)
    logger.info(f"Server: {config.WEBMETHODS_URL}")
    logger.info(f"Interval: {interval or config.POLL_INTERVAL}s")
    logger.info(f"Slack Channel: {config.SLACK_CHANNEL}")
    logger.info("=" * 60)
    
    scheduler = MonitorScheduler(interval=interval)
    
    try:
        scheduler.start_monitoring()
        logger.info("✅ Monitoring started. Press Ctrl+C to stop.")
        
        # Keep running
        import signal
        import time
        
        def signal_handler(sig, frame):
            logger.info("\n🛑 Shutdown signal received")
            scheduler.stop_monitoring()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Keyboard interrupt")
        scheduler.stop_monitoring()
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        sys.exit(1)


def run_once():
    """Run monitor once and exit."""
    logger.info("=" * 60)
    logger.info("Thread Dump Monitor - Single Run Mode")
    logger.info("=" * 60)
    logger.info(f"Server: {config.WEBMETHODS_URL}")
    logger.info("=" * 60)
    
    try:
        agent = MonitorAgent()
        notifier = SlackNotifier()
        
        logger.info("🔍 Running monitoring check...")
        alerts = agent.monitor()
        
        if alerts:
            logger.info(f"⚠️  Found {len(alerts)} alerts:")
            for alert in alerts:
                logger.info(f"  - {alert.title} ({alert.severity.value})")
            
            logger.info("📤 Sending alerts to Slack...")
            sent = notifier.send_alerts(alerts)
            logger.info(f"✅ Sent {sent}/{len(alerts)} alerts")
        else:
            logger.info("✅ No issues detected")
        
        logger.info("=" * 60)
        logger.info("✅ Monitoring check complete")
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        sys.exit(1)


def test_slack():
    """Test Slack integration."""
    logger.info("=" * 60)
    logger.info("Thread Dump Monitor - Slack Test Mode")
    logger.info("=" * 60)
    logger.info(f"Webhook: {config.SLACK_WEBHOOK_URL[:50]}...")
    logger.info(f"Channel: {config.SLACK_CHANNEL}")
    logger.info("=" * 60)
    
    try:
        notifier = SlackNotifier()
        
        logger.info("📤 Sending test message to Slack...")
        success = notifier.send_test_message()
        
        if success:
            logger.info("✅ Test message sent successfully!")
            logger.info(f"   Check {config.SLACK_CHANNEL} for the message")
        else:
            logger.error("❌ Failed to send test message")
            logger.error("   Check your webhook URL and network connection")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        sys.exit(1)


def check_config():
    """Check configuration and dependencies."""
    logger.info("=" * 60)
    logger.info("Thread Dump Monitor - Configuration Check")
    logger.info("=" * 60)
    
    issues = []
    
    # Check webMethods config
    logger.info("📋 webMethods Integration Server:")
    logger.info(f"   URL: {config.WEBMETHODS_URL}")
    logger.info(f"   User: {config.WEBMETHODS_USER}")
    if not config.WEBMETHODS_URL:
        issues.append("❌ WEBMETHODS_URL not configured")
    else:
        logger.info("   ✅ Configured")
    
    # Check Slack config
    logger.info("\n📋 Slack Configuration:")
    logger.info(f"   Channel: {config.SLACK_CHANNEL}")
    if config.SLACK_WEBHOOK_URL:
        logger.info(f"   Webhook: {config.SLACK_WEBHOOK_URL[:50]}...")
        logger.info("   ✅ Configured")
    else:
        issues.append("❌ SLACK_WEBHOOK_URL not configured")
        logger.info("   ❌ Not configured")
    
    # Check Ollama config
    logger.info("\n📋 Ollama Configuration:")
    logger.info(f"   URL: {config.OLLAMA_BASE_URL}")
    logger.info(f"   Model: {config.OLLAMA_MODEL}")
    try:
        import requests
        response = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            logger.info("   ✅ Ollama is running")
        else:
            issues.append("⚠️  Ollama may not be running properly")
    except Exception:
        issues.append("⚠️  Cannot connect to Ollama (optional)")
        logger.info("   ⚠️  Not running (optional)")
    
    # Check thresholds
    logger.info("\n📋 Monitoring Thresholds:")
    logger.info(f"   Hung Thread: {config.HUNG_THREAD_THRESHOLD}s")
    logger.info(f"   CPU: {config.CPU_THRESHOLD}%")
    logger.info(f"   Memory: {config.MEMORY_THRESHOLD}%")
    logger.info(f"   Poll Interval: {config.POLL_INTERVAL}s")
    logger.info("   ✅ Configured")
    
    # Check dependencies
    logger.info("\n📋 Dependencies:")
    deps = [
        ("langgraph", "LangGraph"),
        ("langchain", "LangChain"),
        ("requests", "Requests"),
        ("apscheduler", "APScheduler"),
        ("slack_sdk", "Slack SDK"),
    ]
    
    for module, name in deps:
        try:
            __import__(module)
            logger.info(f"   ✅ {name}")
        except ImportError:
            issues.append(f"❌ {name} not installed")
            logger.info(f"   ❌ {name}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    if issues:
        logger.warning("⚠️  Configuration Issues Found:")
        for issue in issues:
            logger.warning(f"   {issue}")
        logger.info("\n💡 Fix issues and run again")
        sys.exit(1)
    else:
        logger.info("✅ All checks passed! Ready to monitor.")
        logger.info("\n💡 Run with: python run_monitor.py --scheduled")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Thread Dump Monitor Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run continuous monitoring (recommended)
  python run_monitor.py --scheduled
  
  # Run with custom interval
  python run_monitor.py --scheduled --interval 60
  
  # Run once and exit
  python run_monitor.py --once
  
  # Test Slack integration
  python run_monitor.py --test-slack
  
  # Check configuration
  python run_monitor.py --check-config
        """
    )
    
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Run with scheduler (continuous monitoring)"
    )
    
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit"
    )
    
    parser.add_argument(
        "--test-slack",
        action="store_true",
        help="Test Slack integration"
    )
    
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Check configuration and dependencies"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        help="Polling interval in seconds (for scheduled mode)"
    )
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any([args.scheduled, args.once, args.test_slack, args.check_config]):
        parser.print_help()
        sys.exit(0)
    
    # Execute requested mode
    if args.check_config:
        check_config()
    elif args.test_slack:
        test_slack()
    elif args.once:
        run_once()
    elif args.scheduled:
        run_scheduled(args.interval)


if __name__ == "__main__":
    main()

# Made with Bob
