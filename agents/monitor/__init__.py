"""
Monitor Agent Package

This package contains the monitoring agent that continuously monitors
webMethods Integration Server for performance issues and sends Slack notifications.

Components:
- monitor_agent: Main monitoring logic with LangGraph workflow
- slack_notifier: Slack integration for alert notifications
- scheduler: APScheduler for periodic monitoring

Usage:
    from agents.monitor import MonitorAgent, SlackNotifier, MonitorScheduler
    
    # Create and run monitor
    agent = MonitorAgent()
    alerts = agent.monitor()
    
    # Send alerts to Slack
    notifier = SlackNotifier()
    notifier.send_alerts(alerts)
    
    # Or use scheduler for periodic monitoring
    scheduler = MonitorScheduler(interval=30)
    scheduler.start_monitoring()
"""

from .monitor_agent import MonitorAgent
from .slack_notifier import SlackNotifier
from .scheduler import MonitorScheduler

__all__ = ["MonitorAgent", "SlackNotifier", "MonitorScheduler"]
__version__ = "1.0.0"

# Made with Bob
