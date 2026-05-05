"""
Shared data models for thread dump analysis
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ThreadState(Enum):
    """Thread states"""
    RUNNABLE = "RUNNABLE"
    BLOCKED = "BLOCKED"
    WAITING = "WAITING"
    TIMED_WAITING = "TIMED_WAITING"
    NEW = "NEW"
    TERMINATED = "TERMINATED"


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IssueType(Enum):
    """Issue types for alerts"""
    HUNG_THREAD = "hung_thread"
    DEADLOCK = "deadlock"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    BLOCKED_THREAD = "blocked_thread"
    PERFORMANCE = "performance"
    RESOURCE_LEAK = "resource_leak"


@dataclass
class ThreadInfo:
    """Information about a single thread"""
    thread_id: str
    name: str
    state: str
    priority: int = 5
    daemon: bool = False
    cpu_time: float = 0.0
    blocked_time: float = 0.0
    blocked_count: int = 0
    waited_time: float = 0.0
    waited_count: int = 0
    lock_name: Optional[str] = None
    lock_owner_id: Optional[str] = None
    lock_owner_name: Optional[str] = None
    stack_trace: List[str] = field(default_factory=list)
    locked_monitors: List[str] = field(default_factory=list)
    locked_synchronizers: List[str] = field(default_factory=list)
    
    def is_hung(self, threshold: int = 60) -> bool:
        """Check if thread is hung (CPU time > threshold seconds)"""
        return self.cpu_time > threshold
    
    def is_blocked(self) -> bool:
        """Check if thread is blocked"""
        return self.state == ThreadState.BLOCKED.value or self.blocked_count > 0
    
    def is_waiting(self) -> bool:
        """Check if thread is waiting"""
        return self.state in [ThreadState.WAITING.value, ThreadState.TIMED_WAITING.value]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "thread_id": self.thread_id,
            "name": self.name,
            "state": self.state,
            "priority": self.priority,
            "daemon": self.daemon,
            "cpu_time": self.cpu_time,
            "blocked_time": self.blocked_time,
            "blocked_count": self.blocked_count,
            "waited_time": self.waited_time,
            "waited_count": self.waited_count,
            "lock_name": self.lock_name,
            "lock_owner_id": self.lock_owner_id,
            "lock_owner_name": self.lock_owner_name,
            "stack_trace": self.stack_trace,
            "is_hung": self.is_hung(),
            "is_blocked": self.is_blocked(),
            "is_waiting": self.is_waiting()
        }


@dataclass
class ThreadDumpData:
    """Complete thread dump data"""
    server_url: str
    timestamp: datetime
    threads: List[ThreadInfo]
    total_threads: int
    hung_threads: int
    blocked_threads: int
    deadlocks: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "server_url": self.server_url,
            "timestamp": self.timestamp.isoformat(),
            "total_threads": self.total_threads,
            "hung_threads": self.hung_threads,
            "blocked_threads": self.blocked_threads,
            "deadlocks": self.deadlocks,
            "threads": [t.to_dict() for t in self.threads],
            "metadata": self.metadata
        }


@dataclass
class AlertMessage:
    """Alert message for notifications"""
    severity: AlertSeverity
    title: str
    timestamp: datetime
    server_url: str
    message: Optional[str] = None
    description: Optional[str] = None
    alert_id: Optional[str] = None
    issue_type: Optional['IssueType'] = None
    recommendations: List[str] = field(default_factory=list)
    thread_info: Optional[ThreadInfo] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Ensure message or description is set"""
        if not self.message and not self.description:
            self.message = self.title
        elif not self.message:
            self.message = self.description
        elif not self.description:
            self.description = self.message
    
    def to_slack_blocks(self) -> List[Dict[str, Any]]:
        """Convert to Slack blocks format"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": self.title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self.description or self.message
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Server:*\n{self.server_url}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{self.severity.value.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        if self.recommendations:
            rec_text = "\n".join([f"• {rec}" for rec in self.recommendations])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Recommendations:*\n{rec_text}"
                }
            })
        
        blocks.append({"type": "divider"})
        
        return blocks
    
    def to_slack_payload(self) -> Dict[str, Any]:
        """Convert to Slack message payload"""
        color_map = {
            AlertSeverity.CRITICAL: "#FF0000",
            AlertSeverity.HIGH: "#FF6600",
            AlertSeverity.MEDIUM: "#FFCC00",
            AlertSeverity.LOW: "#00CC00",
            AlertSeverity.INFO: "#0099FF"
        }
        
        fields = [
            {
                "title": "Server",
                "value": self.server_url,
                "short": True
            },
            {
                "title": "Severity",
                "value": self.severity.value.upper(),
                "short": True
            },
            {
                "title": "Time",
                "value": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "short": True
            }
        ]
        
        if self.thread_info:
            fields.extend([
                {
                    "title": "Thread",
                    "value": self.thread_info.name,
                    "short": True
                },
                {
                    "title": "State",
                    "value": self.thread_info.state,
                    "short": True
                },
                {
                    "title": "CPU Time",
                    "value": f"{self.thread_info.cpu_time:.2f}s",
                    "short": True
                }
            ])
        
        return {
            "attachments": [
                {
                    "color": color_map[self.severity],
                    "title": self.title,
                    "text": self.message,
                    "fields": fields,
                    "footer": "Thread Dump Analysis Agent",
                    "ts": int(self.timestamp.timestamp())
                }
            ]
        }


@dataclass
class AnalysisResult:
    """Result of thread dump analysis"""
    timestamp: datetime
    server_url: str
    total_threads: int
    hung_threads: int
    blocked_threads: int
    deadlocks: List[Dict[str, Any]]
    recommendations: List[str]
    severity: AlertSeverity
    summary: str
    long_running_threads: int = 0
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "server_url": self.server_url,
            "total_threads": self.total_threads,
            "hung_threads": self.hung_threads,
            "blocked_threads": self.blocked_threads,
            "long_running_threads": self.long_running_threads,
            "deadlocks": self.deadlocks,
            "recommendations": self.recommendations,
            "severity": self.severity.value,
            "summary": self.summary,
            "details": self.details
        }


@dataclass
class GCMetrics:
    """Garbage Collection metrics"""
    timestamp: datetime
    gc_count: int
    gc_time: float
    heap_used: float
    heap_max: float
    heap_utilization: float
    young_gen_size: float
    old_gen_size: float
    gc_pause_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "gc_count": self.gc_count,
            "gc_time": self.gc_time,
            "heap_used": self.heap_used,
            "heap_max": self.heap_max,
            "heap_utilization": self.heap_utilization,
            "young_gen_size": self.young_gen_size,
            "old_gen_size": self.old_gen_size,
            "gc_pause_time": self.gc_pause_time,
            "metadata": self.metadata
        }


@dataclass
class CPUMetrics:
    """CPU metrics"""
    timestamp: datetime
    cpu_usage: float
    system_load: float
    process_cpu: float
    thread_count: int
    peak_thread_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage": self.cpu_usage,
            "system_load": self.system_load,
            "process_cpu": self.process_cpu,
            "thread_count": self.thread_count,
            "peak_thread_count": self.peak_thread_count,
            "metadata": self.metadata
        }


@dataclass
class RemediationAction:
    """Remediation action recommendation"""
    action_type: str
    description: str
    priority: int
    estimated_impact: str
    steps: List[str]
    risks: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "action_type": self.action_type,
            "description": self.description,
            "priority": self.priority,
            "estimated_impact": self.estimated_impact,
            "steps": self.steps,
            "risks": self.risks,
            "metadata": self.metadata
        }

# Made with Bob
