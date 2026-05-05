"""Slack notification handler for Monitor Agent."""

import json
import requests
from typing import List, Optional
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.config import config
from shared.models import AlertMessage
from shared.utils import setup_logging

logger = setup_logging("slack_notifier")


class SlackNotifier:
    """Handle Slack notifications for alerts."""
    
    def __init__(self, webhook_url: Optional[str] = None, channel: Optional[str] = None):
        """
        Initialize Slack notifier.
        
        Args:
            webhook_url: Slack webhook URL (defaults to config)
            channel: Slack channel (defaults to config)
        """
        self.webhook_url = webhook_url or config.SLACK_WEBHOOK_URL
        self.channel = channel or config.SLACK_CHANNEL
        self.sent_alerts = set()  # Track sent alerts for deduplication
        
        if not self.webhook_url:
            logger.warning("No Slack webhook URL configured. Notifications disabled.")
    
    def send_alert(self, alert: AlertMessage) -> bool:
        """
        Send an alert to Slack.
        
        Args:
            alert: AlertMessage to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.warning("Cannot send alert: No webhook URL configured")
            return False
        
        # Check for duplicate
        if self._is_duplicate(alert):
            logger.info(f"Skipping duplicate alert: {alert.alert_id}")
            return False
        
        try:
            # Format message using blocks
            payload = self._format_alert_message(alert)
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Alert sent successfully: {alert.title}")
                self._mark_sent(alert)
                return True
            else:
                logger.error(
                    f"Failed to send alert: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error sending Slack alert: {str(e)}")
            return False
    
    def send_alerts(self, alerts: List[AlertMessage]) -> int:
        """
        Send multiple alerts to Slack.
        
        Args:
            alerts: List of AlertMessage objects
            
        Returns:
            Number of alerts sent successfully
        """
        sent_count = 0
        
        for alert in alerts:
            if self.send_alert(alert):
                sent_count += 1
        
        logger.info(f"Sent {sent_count}/{len(alerts)} alerts to Slack")
        return sent_count
    
    def _format_alert_message(self, alert: AlertMessage) -> dict:
        """
        Format alert as Slack message with blocks.
        
        Args:
            alert: AlertMessage to format
            
        Returns:
            Slack message payload
        """
        # Get severity emoji
        severity_emoji = {
            "critical": "🔴",
            "high": "🟠",
            "medium": "🟡",
            "low": "🟢",
            "info": "ℹ️"
        }
        emoji = severity_emoji.get(alert.severity.value, "⚠️")
        
        # Build blocks
        blocks = alert.to_slack_blocks()
        
        # Add header with emoji
        blocks[0]["text"]["text"] = f"{emoji} {alert.title}"
        
        # Create payload
        payload = {
            "channel": self.channel,
            "blocks": blocks,
            "text": f"{alert.title}"  # Fallback text
        }
        
        return payload
    
    def _is_duplicate(self, alert: AlertMessage) -> bool:
        """
        Check if alert is a duplicate.
        
        Args:
            alert: AlertMessage to check
            
        Returns:
            True if duplicate, False otherwise
        """
        # Create a unique key for the alert
        alert_key = f"{alert.issue_type.value}_{alert.title}"
        return alert_key in self.sent_alerts
    
    def _mark_sent(self, alert: AlertMessage):
        """
        Mark alert as sent.
        
        Args:
            alert: AlertMessage that was sent
        """
        alert_key = f"{alert.issue_type.value}_{alert.title}"
        self.sent_alerts.add(alert_key)
    
    def send_test_message(self) -> bool:
        """
        Send a test message to verify Slack integration.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.error("Cannot send test message: No webhook URL configured")
            return False
        
        payload = {
            "channel": self.channel,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Thread Dump Monitor - Test Message",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            "*Monitor Agent is now active!*\n\n"
                            "The Thread Dump Analysis AI Agent is monitoring your "
                            "webMethods Integration Server for:\n"
                            "• Hung threads\n"
                            "• Deadlocks\n"
                            "• High CPU usage\n"
                            "• High memory usage\n"
                            "• Blocked threads"
                        )
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Server:*\n{config.WEBMETHODS_URL}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Poll Interval:*\n{config.POLL_INTERVAL}s"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Hung Thread Threshold:*\n{config.HUNG_THREAD_THRESHOLD}s"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "🤖 Powered by LangGraph & Ollama"
                        }
                    ]
                }
            ],
            "text": "Thread Dump Monitor - Test Message"
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Test message sent successfully")
                return True
            else:
                logger.error(f"Failed to send test message: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending test message: {str(e)}")
            return False
    
    def send_summary(self, total_threads: int, hung_count: int, blocked_count: int) -> bool:
        """
        Send a monitoring summary to Slack.
        
        Args:
            total_threads: Total number of threads
            hung_count: Number of hung threads
            blocked_count: Number of blocked threads
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            return False
        
        # Determine status
        if hung_count > 0 or blocked_count > 0:
            status_emoji = "⚠️"
            status_text = "Issues Detected"
            color = "warning"
        else:
            status_emoji = "✅"
            status_text = "All Clear"
            color = "good"
        
        payload = {
            "channel": self.channel,
            "attachments": [
                {
                    "color": color,
                    "title": f"{status_emoji} Monitoring Summary",
                    "text": status_text,
                    "fields": [
                        {
                            "title": "Total Threads",
                            "value": str(total_threads),
                            "short": True
                        },
                        {
                            "title": "Hung Threads",
                            "value": str(hung_count),
                            "short": True
                        },
                        {
                            "title": "Blocked Threads",
                            "value": str(blocked_count),
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ],
                    "footer": "Thread Dump Monitor",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending summary: {str(e)}")
            return False


def main():
    """Test Slack notifier."""
    logger.info("Testing Slack Notifier")
    
    notifier = SlackNotifier()
    
    # Send test message
    if notifier.send_test_message():
        logger.info("✅ Slack integration working!")
    else:
        logger.error("❌ Slack integration failed")


if __name__ == "__main__":
    main()

# Made with Bob
