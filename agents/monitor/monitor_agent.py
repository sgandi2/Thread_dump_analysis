"""Monitor Agent - Detects hung threads and issues on webMethods Integration Server using LangGraph."""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from shared.config import config
from shared.models import (
    ThreadInfo, ThreadDumpData, AlertMessage, 
    AlertSeverity, IssueType, ThreadState
)
from shared.utils import (
    call_webmethods_api, 
    calculate_thread_metrics,
    setup_logging
)

logger = setup_logging("monitor_agent")


class MonitorState(TypedDict):
    """State for the monitor agent workflow."""
    server_url: str
    timestamp: datetime
    threads: List[Dict[str, Any]]
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    hung_threads: List[Dict[str, Any]]
    blocked_threads: List[Dict[str, Any]]
    deadlocks: List[List[Dict[str, Any]]]
    alerts: Annotated[List[AlertMessage], operator.add]
    metrics: Dict[str, Any]
    error: Optional[str]


class MonitorAgent:
    """Monitor agent for detecting issues on Integration Server."""
    
    def __init__(self):
        """Initialize the monitor agent."""
        self.alert_history: Dict[str, datetime] = {}  # For deduplication
        self.graph = self._create_graph()
        
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow for monitoring."""
        workflow = StateGraph(MonitorState)
        
        # Add nodes
        workflow.add_node("fetch_server_stats", self._fetch_server_stats)
        workflow.add_node("detect_hung_threads", self._detect_hung_threads)
        workflow.add_node("detect_blocked_threads", self._detect_blocked_threads)
        workflow.add_node("check_deadlocks", self._check_deadlocks)
        workflow.add_node("check_resource_usage", self._check_resource_usage)
        workflow.add_node("generate_alerts", self._generate_alerts)
        
        # Define workflow
        workflow.set_entry_point("fetch_server_stats")
        workflow.add_edge("fetch_server_stats", "detect_hung_threads")
        workflow.add_edge("detect_hung_threads", "detect_blocked_threads")
        workflow.add_edge("detect_blocked_threads", "check_deadlocks")
        workflow.add_edge("check_deadlocks", "check_resource_usage")
        workflow.add_edge("check_resource_usage", "generate_alerts")
        workflow.add_edge("generate_alerts", END)
        
        return workflow.compile()
    
    def _fetch_server_stats(self, state: MonitorState) -> MonitorState:
        """Fetch current server statistics and thread information."""
        logger.info(f"Fetching stats from {state['server_url']}")
        
        try:
            # Fetch thread information
            # Note: Adjust endpoint based on actual webMethods API
            thread_data = call_webmethods_api("admin/threads")
            
            if not thread_data:
                state["error"] = "Failed to fetch thread data"
                return state
            
            # Parse threads
            threads = []
            if isinstance(thread_data, dict) and "threads" in thread_data:
                for t in thread_data["threads"]:
                    threads.append({
                        "thread_id": t.get("id", "unknown"),
                        "thread_name": t.get("name", "unknown"),
                        "state": t.get("state", "RUNNABLE"),
                        "cpu_time": t.get("cpuTime", 0),
                        "user_time": t.get("userTime", 0),
                        "blocked_count": t.get("blockedCount", 0),
                        "waited_count": t.get("waitedCount", 0),
                        "stack_trace": t.get("stackTrace", [])
                    })
            
            state["threads"] = threads
            state["timestamp"] = datetime.now()
            
            # Fetch resource usage
            stats = call_webmethods_api("admin/stats")
            if stats:
                state["cpu_usage"] = stats.get("cpuUsage", 0.0)
                state["memory_usage"] = stats.get("memoryUsage", 0.0)
            
            logger.info(f"Fetched {len(threads)} threads")
            
        except Exception as e:
            logger.error(f"Error fetching server stats: {str(e)}")
            state["error"] = str(e)
        
        return state
    
    def _detect_hung_threads(self, state: MonitorState) -> MonitorState:
        """Detect hung threads based on threshold."""
        logger.info("Detecting hung threads")
        
        hung_threads = []
        threshold = config.HUNG_THREAD_THRESHOLD
        
        for thread in state["threads"]:
            cpu_time = thread.get("cpu_time", 0)
            duration = cpu_time / 1000.0  # Convert to seconds
            
            if duration > threshold:
                thread["duration"] = duration
                hung_threads.append(thread)
                logger.warning(
                    f"Hung thread detected: {thread['thread_name']} "
                    f"(duration: {duration:.2f}s)"
                )
        
        state["hung_threads"] = hung_threads
        return state
    
    def _detect_blocked_threads(self, state: MonitorState) -> MonitorState:
        """Detect blocked threads."""
        logger.info("Detecting blocked threads")
        
        blocked_threads = []
        
        for thread in state["threads"]:
            if thread.get("state") == "BLOCKED" or thread.get("blocked_count", 0) > 0:
                blocked_threads.append(thread)
                logger.warning(f"Blocked thread detected: {thread['thread_name']}")
        
        state["blocked_threads"] = blocked_threads
        return state
    
    def _check_deadlocks(self, state: MonitorState) -> MonitorState:
        """Check for potential deadlocks."""
        if not config.DEADLOCK_CHECK_ENABLED:
            state["deadlocks"] = []
            return state
        
        logger.info("Checking for deadlocks")
        
        # Simple deadlock detection based on blocked threads
        # In production, this would use more sophisticated analysis
        deadlocks = []
        blocked = state["blocked_threads"]
        
        if len(blocked) >= 2:
            # Group threads that might be in deadlock
            # This is a simplified version
            potential_deadlock = []
            for thread in blocked:
                if thread.get("blocked_count", 0) > 5:
                    potential_deadlock.append(thread)
            
            if len(potential_deadlock) >= 2:
                deadlocks.append(potential_deadlock)
                logger.warning(f"Potential deadlock detected with {len(potential_deadlock)} threads")
        
        state["deadlocks"] = deadlocks
        return state
    
    def _check_resource_usage(self, state: MonitorState) -> MonitorState:
        """Check CPU and memory usage."""
        logger.info("Checking resource usage")
        
        cpu_usage = state.get("cpu_usage", 0.0)
        memory_usage = state.get("memory_usage", 0.0)
        
        metrics = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "cpu_threshold_exceeded": cpu_usage > config.CPU_THRESHOLD,
            "memory_threshold_exceeded": memory_usage > config.MEMORY_THRESHOLD
        }
        
        if metrics["cpu_threshold_exceeded"]:
            logger.warning(f"High CPU usage detected: {cpu_usage:.2f}%")
        
        if metrics["memory_threshold_exceeded"]:
            logger.warning(f"High memory usage detected: {memory_usage:.2f}%")
        
        state["metrics"] = metrics
        return state
    
    def _generate_alerts(self, state: MonitorState) -> MonitorState:
        """Generate alerts for detected issues."""
        logger.info("Generating alerts")
        
        alerts = []
        
        # Alert for hung threads
        for thread in state["hung_threads"]:
            if self._should_alert(f"hung_{thread['thread_id']}"):
                alert = AlertMessage(
                    alert_id=str(uuid.uuid4()),
                    timestamp=state["timestamp"],
                    severity=AlertSeverity.HIGH,
                    issue_type=IssueType.HUNG_THREAD,
                    title=f"Hung Thread Detected: {thread['thread_name']}",
                    description=(
                        f"Thread has been running for {thread.get('duration', 0):.2f} seconds, "
                        f"exceeding threshold of {config.HUNG_THREAD_THRESHOLD} seconds."
                    ),
                    server_url=state["server_url"],
                    recommendations=[
                        "Review thread stack trace for blocking operations",
                        "Check for database connection issues",
                        "Consider thread interruption if safe"
                    ],
                    metadata={"thread": thread}
                )
                alerts.append(alert)
                self._mark_alerted(f"hung_{thread['thread_id']}")
        
        # Alert for deadlocks
        for deadlock_group in state["deadlocks"]:
            deadlock_id = "_".join([t["thread_id"] for t in deadlock_group])
            if self._should_alert(f"deadlock_{deadlock_id}"):
                alert = AlertMessage(
                    alert_id=str(uuid.uuid4()),
                    timestamp=state["timestamp"],
                    severity=AlertSeverity.CRITICAL,
                    issue_type=IssueType.DEADLOCK,
                    title="Potential Deadlock Detected",
                    description=(
                        f"Detected {len(deadlock_group)} threads that may be in deadlock. "
                        "Immediate attention required."
                    ),
                    server_url=state["server_url"],
                    recommendations=[
                        "Analyze thread dump for circular dependencies",
                        "Consider restarting affected services",
                        "Review locking mechanisms in code"
                    ],
                    metadata={"threads": deadlock_group}
                )
                alerts.append(alert)
                self._mark_alerted(f"deadlock_{deadlock_id}")
        
        # Alert for high CPU
        if state["metrics"].get("cpu_threshold_exceeded"):
            if self._should_alert("high_cpu"):
                alert = AlertMessage(
                    alert_id=str(uuid.uuid4()),
                    timestamp=state["timestamp"],
                    severity=AlertSeverity.HIGH,
                    issue_type=IssueType.HIGH_CPU,
                    title="High CPU Usage Detected",
                    description=(
                        f"CPU usage is at {state['cpu_usage']:.2f}%, "
                        f"exceeding threshold of {config.CPU_THRESHOLD}%."
                    ),
                    server_url=state["server_url"],
                    recommendations=[
                        "Identify CPU-intensive threads",
                        "Review recent deployments",
                        "Consider scaling resources"
                    ]
                )
                alerts.append(alert)
                self._mark_alerted("high_cpu")
        
        # Alert for high memory
        if state["metrics"].get("memory_threshold_exceeded"):
            if self._should_alert("high_memory"):
                alert = AlertMessage(
                    alert_id=str(uuid.uuid4()),
                    timestamp=state["timestamp"],
                    severity=AlertSeverity.HIGH,
                    issue_type=IssueType.HIGH_MEMORY,
                    title="High Memory Usage Detected",
                    description=(
                        f"Memory usage is at {state['memory_usage']:.2f}%, "
                        f"exceeding threshold of {config.MEMORY_THRESHOLD}%."
                    ),
                    server_url=state["server_url"],
                    recommendations=[
                        "Check for memory leaks",
                        "Review GC logs",
                        "Consider increasing heap size"
                    ]
                )
                alerts.append(alert)
                self._mark_alerted("high_memory")
        
        state["alerts"] = alerts
        logger.info(f"Generated {len(alerts)} alerts")
        
        return state
    
    def _should_alert(self, alert_key: str) -> bool:
        """Check if we should send an alert (deduplication)."""
        if alert_key not in self.alert_history:
            return True
        
        last_alert = self.alert_history[alert_key]
        cooldown = timedelta(seconds=config.ALERT_COOLDOWN)
        
        return datetime.now() - last_alert > cooldown
    
    def _mark_alerted(self, alert_key: str):
        """Mark that an alert was sent."""
        self.alert_history[alert_key] = datetime.now()
    
    def monitor(self, server_url: Optional[str] = None) -> List[AlertMessage]:
        """
        Run monitoring cycle.
        
        Args:
            server_url: Server URL to monitor (defaults to config)
            
        Returns:
            List of generated alerts
        """
        server_url = server_url or config.WEBMETHODS_URL
        
        initial_state: MonitorState = {
            "server_url": server_url,
            "timestamp": datetime.now(),
            "threads": [],
            "cpu_usage": None,
            "memory_usage": None,
            "hung_threads": [],
            "blocked_threads": [],
            "deadlocks": [],
            "alerts": [],
            "metrics": {},
            "error": None
        }
        
        try:
            result = self.graph.invoke(initial_state)
            
            if result.get("error"):
                logger.error(f"Monitoring failed: {result['error']}")
                return []
            
            return result.get("alerts", [])
            
        except Exception as e:
            logger.error(f"Error during monitoring: {str(e)}")
            return []


def main():
    """Main entry point for testing."""
    logger.info("Starting Monitor Agent")
    
    agent = MonitorAgent()
    alerts = agent.monitor()
    
    if alerts:
        logger.info(f"Generated {len(alerts)} alerts:")
        for alert in alerts:
            logger.info(f"  - {alert.title} ({alert.severity.value})")
    else:
        logger.info("No alerts generated")


if __name__ == "__main__":
    main()

# Made with Bob
