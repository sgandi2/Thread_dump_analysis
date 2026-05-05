# Thread Dump Remediation Agent

**Team Member:** Sai  
**Technology:** LangGraph  
**Purpose:** Automated remediation for thread issues - kill threads, cancel operations, or restart Integration Server

## Overview

The Thread Dump Remediation Agent is a LangGraph-based intelligent agent that provides automated remediation for thread-related issues in webMethods Integration Server. It can kill hung threads, cancel operations, restart the server, or perform other corrective actions based on severity analysis.

## Features

- ✅ **LangGraph Workflow**: 7-node state machine with approval gates
- ✅ **Multiple Remediation Types**: Kill thread, cancel operation, restart server, force GC, clear cache
- ✅ **Severity-Based Actions**: Automatic action selection based on issue severity
- ✅ **Approval System**: Configurable approval for critical actions
- ✅ **Risk Assessment**: Detailed risk analysis for each action
- ✅ **Verification**: Post-action verification of server health
- ✅ **Safe Actions**: Auto-approval for low-risk actions
- ✅ **Comprehensive Logging**: Detailed execution tracking

## Architecture

### Workflow Steps

```
1. Analyze Issue → 2. Recommend Actions → 3. Select Action
                                              ↓
6. Verify Result ← 5. Execute Action ← 4. Request Approval
```

### Remediation Types

| Type | Description | Risk Level | Auto-Approve |
|------|-------------|------------|--------------|
| `KILL_THREAD` | Terminate hung thread | High | No |
| `CANCEL_OPERATION` | Cancel running operation | Medium | No |
| `RESTART_SERVER` | Restart Integration Server | Critical | No |
| `INCREASE_THREAD_POOL` | Increase thread pool size | Medium | No |
| `CLEAR_CACHE` | Clear server cache | Low | Yes |
| `FORCE_GC` | Force garbage collection | Low | Yes |
| `NO_ACTION` | No action needed | None | Yes |

### State Machine

```python
RemediationState = {
    "server_url": str,
    "auth_credentials": Dict,
    "thread_info": Optional[ThreadInfo],
    "analysis_result": Dict,
    "recommended_actions": List[RemediationAction],
    "selected_action": Optional[RemediationType],
    "execution_result": Dict,
    "approval_required": bool,
    "approved": bool,
    "error": Optional[str],
    "timestamp": datetime,
    "metadata": Dict
}
```

## Installation

### 1. Install Dependencies

```bash
cd agents/remediation
pip install -r requirements.txt
```

### 2. Configure Environment

Update `.env` file:

```env
# webMethods Integration Server
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USER=Administrator
WEBMETHODS_PASSWORD=manage

# Thresholds
HUNG_THREAD_THRESHOLD=300
CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
```

## Usage

### Basic Usage

```python
from agents.remediation.remediation_agent import RemediationAgent
from shared.models import ThreadInfo

# Create hung thread example
thread = ThreadInfo(
    thread_id="0x1000",
    name="HTTP Handler",
    state="RUNNABLE",
    cpu_time=650.0  # 10+ minutes
)

# Create agent
agent = RemediationAgent(auto_approve=True)

# Run remediation
result = agent.run(
    thread_info=thread,
    analysis_result={"cpu_usage": 85.0}
)

# Check result
if not result.get("error"):
    print(f"✅ Remediation successful")
    print(f"Action: {result['execution_result']['action']}")
```

### With Manual Approval

```python
# Require manual approval for all actions
agent = RemediationAgent(auto_approve=False)

result = agent.run(thread_info=thread)

# Approval will be requested during workflow
```

### Integration with Collector

```python
from agents.collector.collector_agent import ThreadDumpCollectorAgent
from agents.remediation.remediation_agent import RemediationAgent

# Collect thread dump
collector = ThreadDumpCollectorAgent()
dump_result = collector.run()

# Find hung threads
hung_threads = [t for t in dump_result["parsed_threads"] if t.is_hung()]

# Remediate each hung thread
agent = RemediationAgent()
for thread in hung_threads:
    result = agent.run(thread_info=thread)
```

### Command Line

```bash
# Run from project root
python -m agents.remediation.remediation_agent

# Or from remediation directory
cd agents/remediation
python remediation_agent.py
```

## Remediation Actions

### 1. Kill Thread

**When Used**: Thread hung for 10+ minutes  
**Risk**: High - May cause incomplete transactions  
**API**: `/invoke/wm.server/killThread`

```python
# Automatically selected for threads with CPU time > 600s
thread = ThreadInfo(
    thread_id="0x1000",
    name="Hung Thread",
    cpu_time=650.0
)
```

### 2. Cancel Operation

**When Used**: Thread hung for 5-10 minutes  
**Risk**: Medium - Graceful cancellation  
**API**: `/invoke/wm.server/cancelService`

```python
# Selected for threads with CPU time 300-600s
thread = ThreadInfo(
    thread_id="0x1000",
    name="Long Running",
    cpu_time=450.0
)
```

### 3. Restart Server

**When Used**: Deadlock detected  
**Risk**: Critical - Service downtime  
**API**: `/invoke/wm.server/shutdown`

```python
# Selected when deadlocks are present
analysis = {
    "deadlocks": [
        {"lock": "0x2000", "owner": "Thread-1", "waiters": ["Thread-2"]}
    ]
}
```

### 4. Force Garbage Collection

**When Used**: High CPU usage (>90%)  
**Risk**: Low - Brief pause  
**API**: `/invoke/wm.server/forceGC`

```python
# Selected for high CPU
analysis = {"cpu_usage": 92.0}
```

### 5. Clear Cache

**When Used**: High memory usage (>85%)  
**Risk**: Low - Temporary performance impact  
**API**: `/invoke/wm.server/clearCache`

```python
# Selected for high memory
analysis = {"memory_usage": 88.0}
```

### 6. Increase Thread Pool

**When Used**: Thread pool exhausted  
**Risk**: Medium - Increased resource usage  
**API**: `/invoke/wm.server/setThreadPoolSettings`

```python
# Selected when thread pool is full
analysis = {"thread_pool_exhausted": True}
```

## Approval System

### Auto-Approval Rules

Safe actions are auto-approved:
- Force GC
- Clear Cache
- No Action

Critical actions require approval:
- Kill Thread
- Cancel Operation
- Restart Server
- Increase Thread Pool

### Approval Flow

```python
# With auto-approval disabled
agent = RemediationAgent(auto_approve=False)
result = agent.run(thread_info=thread)

# Approval request will be displayed:
# ======================================================================
# REMEDIATION APPROVAL REQUIRED
# ======================================================================
# Action: Kill hung thread 'HTTP Handler'
# Priority: 1
# Impact: High - Will terminate the thread immediately
# 
# Steps:
#   1. Identify thread: 0x1000
#   2. Call killThread API
#   3. Verify thread termination
#   4. Monitor for side effects
# 
# Risks:
#   ⚠ May cause incomplete transactions
#   ⚠ Could affect dependent operations
# ======================================================================
```

### Severity-Based Auto-Approval

```python
# Critical/High severity issues are auto-approved
# even with auto_approve=False
analysis = {
    "severity": "critical",  # Will auto-approve
    "deadlocks": [...]
}
```

## Output Format

### Execution Result

```json
{
  "action": "kill_thread",
  "status": "success",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "details": {
    "status_code": 200,
    "response": "Thread terminated successfully"
  }
}
```

### Complete Result

```json
{
  "server_url": "http://localhost:5555",
  "thread_info": {...},
  "analysis_result": {...},
  "recommended_actions": [...],
  "selected_action": "KILL_THREAD",
  "execution_result": {...},
  "approval_required": false,
  "approved": true,
  "metadata": {
    "severity": "critical",
    "action_count": 3,
    "selected_action": {...},
    "execution_status": "success",
    "verification_status": "complete"
  }
}
```

## API Endpoints

| Endpoint | Purpose | Method |
|----------|---------|--------|
| `/invoke/wm.server/killThread` | Kill thread | POST |
| `/invoke/wm.server/cancelService` | Cancel operation | POST |
| `/invoke/wm.server/shutdown` | Restart server | POST |
| `/invoke/wm.server/setThreadPoolSettings` | Adjust thread pool | POST |
| `/invoke/wm.server/clearCache` | Clear cache | POST |
| `/invoke/wm.server/forceGC` | Force GC | POST |
| `/invoke/wm.server/getServerStats` | Verify health | GET |

## Integration Examples

### With Monitor Agent

```python
from agents.monitor.monitor_agent import MonitorAgent
from agents.remediation.remediation_agent import RemediationAgent

# Monitor will automatically trigger remediation
monitor = MonitorAgent()
monitor.set_remediation_agent(RemediationAgent(auto_approve=True))
monitor.start()
```

### With Analyzer Agent

```python
from agents.analyzer.analyzer_agent import ThreadDumpAnalyzerAgent
from agents.remediation.remediation_agent import RemediationAgent

# Analyze then remediate
analyzer = ThreadDumpAnalyzerAgent()
analysis = analyzer.analyze(threads)

if analysis.severity in ["critical", "high"]:
    agent = RemediationAgent()
    result = agent.run(analysis_result=analysis.to_dict())
```

### With Dashboard

```python
# Dashboard can trigger remediation
@app.callback(...)
def remediate_thread(thread_id):
    thread = get_thread_by_id(thread_id)
    agent = RemediationAgent()
    result = agent.run(thread_info=thread)
    return result
```

## Error Handling

The agent handles errors at each step:

- **Analysis Errors**: Invalid input, missing data
- **Recommendation Errors**: No suitable actions
- **Approval Errors**: Timeout, rejection
- **Execution Errors**: API failures, timeouts
- **Verification Errors**: Server unreachable

All errors are captured in the `error` field.

## Safety Features

### 1. Risk Assessment

Every action includes:
- Detailed risk analysis
- Impact estimation
- Step-by-step execution plan

### 2. Approval Gates

Critical actions require approval:
- Manual approval for high-risk actions
- Auto-approval for safe actions
- Severity-based override

### 3. Verification

Post-action verification:
- Server health check
- Stats comparison
- Error detection

### 4. Rollback Support

Future enhancement:
- Action rollback capability
- State snapshots
- Recovery procedures

## Performance

- **Analysis Time**: < 1 second
- **Recommendation Time**: < 1 second
- **Execution Time**: 2-30 seconds (depends on action)
- **Verification Time**: 1-2 seconds
- **Total Time**: 5-35 seconds

## Troubleshooting

### Issue: Action Failed

```
Error: Execution error: [Errno 111] Connection refused
```

**Solution**: Verify server is running and accessible.

### Issue: Approval Timeout

```
⏳ Waiting for manual approval...
```

**Solution**: Use `auto_approve=True` or implement approval system.

### Issue: Verification Failed

```
⚠ Could not verify - Server may be restarting
```

**Solution**: Normal for restart actions, wait for server to come back up.

## Best Practices

1. **Test in Non-Production**: Always test remediation in dev/test first
2. **Monitor Results**: Track remediation success rates
3. **Use Auto-Approval Carefully**: Only for trusted environments
4. **Implement Notifications**: Alert on critical remediations
5. **Log Everything**: Keep detailed logs of all actions

## Future Enhancements

- [ ] Rollback capability for failed actions
- [ ] Multi-server remediation
- [ ] Custom remediation scripts
- [ ] Machine learning for action selection
- [ ] Integration with ticketing systems
- [ ] Scheduled maintenance windows

## Support

For issues or questions:
- Check error messages in result state
- Review logs in `logs/` directory
- Verify server connectivity
- Contact: Sai (Team Member)

## License

Internal use only - webMethods Thread Dump Analysis System