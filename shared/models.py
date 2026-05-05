"""Data models for Thread Dump Analysis AI Agent."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class ThreadState(Enum):
    """Thread states."""
    RUNNABLE = "RUNNABLE"
    BLOCKED = "BLOCKED"
    WAITING = "WAITING"
    TIMED_WAITING = "TIMED_WAITING"
    NEW = "NEW"
    TERMINATED = "TERMINATED"


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(Enum):
    """Types of issues detected."""
    HUNG_THREAD = "hung_thread"
    DEADLOCK = "deadlock"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    BLOCKED_THREADS = "blocked_threads"
    RESOURCE_CONTENTION = "resource_contention"


@dataclass
class ThreadInfo:
    """Information about a single thread."""
    thread_id: str
    thread_name: str
    state: ThreadState
    stack_trace: List[str]
    cpu_time: Optional[float] = None
    user_time: Optional[float] = None
    blocked_time: Optional[float] = None
    blocked_count: int = 0
    waited_count: int = 0
    lock_name: Optional[str] = None
    lock_owner_id: Optional[str] = None
    lock_owner_name: Optional[str] = None
    in_native: bool = False
    suspended: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    
    def get_duration(self) -> float:
        """Get thread duration in seconds."""
        if self.cpu_time:
            return self.cpu_time / 1000.0  # Convert ms to seconds
        return 0.0
    
    def is_hung(self, threshold: int = 300) -> bool:
        """Check if thread is hung based on threshold."""
        return self.get_duration() > threshold and self.state in [
            ThreadState.RUNNABLE, 
            ThreadState.BLOCKED, 
            ThreadState.WAITING
        ]


@dataclass
class ThreadDumpData:
    """Complete thread dump data."""
    timestamp: datetime
    server_url: str
    total_threads: int
    threads: List[ThreadInfo]
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    heap_used: Optional[int] = None
    heap_max: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_hung_threads(self, threshold: int = 300) -> List[ThreadInfo]:
        """Get list of hung threads."""
        return [t for t in self.threads if t.is_hung(threshold)]
    
    def get_blocked_threads(self) -> List[ThreadInfo]:
        """Get list of blocked threads."""
        return [t for t in self.threads if t.state == ThreadState.BLOCKED]
    
    def detect_deadlocks(self) -> List[List[ThreadInfo]]:
        """Detect potential deadlocks."""
        deadlocks = []
        blocked = self.get_blocked_threads()
        
        # Build lock ownership graph
        lock_graph: Dict[str, ThreadInfo] = {}
        for thread in blocked:
            if thread.lock_owner_id:
                lock_graph[thread.thread_id] = thread
        
        # Find cycles (simple deadlock detection)
        visited = set()
        for thread in blocked:
            if thread.thread_id in visited:
                continue
            
            cycle = []
            current = thread
            path = set()
            
            while current and current.thread_id not in visited:
                if current.thread_id in path:
                    # Found a cycle
                    cycle_start = list(path).index(current.thread_id)
                    deadlocks.append(list(path)[cycle_start:])
                    break
                
                path.add(current.thread_id)
                visited.add(current.thread_id)
                
                # Move to lock owner
                if current.lock_owner_id and current.lock_owner_id in lock_graph:
                    current = lock_graph[current.lock_owner_id]
                else:
                    break
        
        return deadlocks


@dataclass
class AlertMessage:
    """Alert message structure."""
    alert_id: str
    timestamp: datetime
    severity: AlertSeverity
    issue_type: IssueType
    title: str
    description: str
    thread_info: Optional[ThreadInfo] = None
    affected_threads: List[ThreadInfo] = field(default_factory=list)
    server_url: str = ""
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_slack_blocks(self) -> List[Dict[str, Any]]:
        """Convert alert to Slack block format."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 {self.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{self.severity.value.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Issue Type:*\n{self.issue_type.value.replace('_', ' ').title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Server:*\n{self.server_url}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{self.description}"
                }
            }
        ]
        
        # Add thread info if available
        if self.thread_info:
            thread_text = (
                f"*Thread Details:*\n"
                f"• ID: `{self.thread_info.thread_id}`\n"
                f"• Name: `{self.thread_info.thread_name}`\n"
                f"• State: `{self.thread_info.state.value}`\n"
                f"• Duration: `{self.thread_info.get_duration():.2f}s`"
            )
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": thread_text
                }
            })
            
            # Add stack trace preview (first 5 lines)
            if self.thread_info.stack_trace:
                stack_preview = "\n".join(self.thread_info.stack_trace[:5])
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Stack Trace (preview):*\n```{stack_preview}```"
                    }
                })
        
        # Add recommendations
        if self.recommendations:
            rec_text = "\n".join([f"• {rec}" for rec in self.recommendations])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommendations:*\n{rec_text}"
                }
            })
        
        # Add action buttons
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Analyze",
                        "emoji": True
                    },
                    "value": f"analyze_{self.alert_id}",
                    "action_id": "analyze_button"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Remediate",
                        "emoji": True
                    },
                    "value": f"remediate_{self.alert_id}",
                    "action_id": "remediate_button",
                    "style": "danger"
                }
            ]
        })
        
        return blocks


@dataclass
class AnalysisResult:
    """Analysis result from AI agents."""
    analysis_id: str
    timestamp: datetime
    thread_dump_data: ThreadDumpData
    issues_detected: List[IssueType]
    root_causes: List[str]
    recommendations: List[str]
    specialist_insights: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RemediationAction:
    """Remediation action details."""
    action_id: str
    timestamp: datetime
    action_type: str
    target: str  # thread_id, service_name, etc.
    parameters: Dict[str, Any]
    status: str  # pending, executing, completed, failed, rolled_back
    result: Optional[str] = None
    error: Optional[str] = None
    rollback_available: bool = True
    executed_by: str = "system"

# Made with Bob
