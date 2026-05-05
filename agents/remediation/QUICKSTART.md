# Remediation Agent - Quick Start Guide

**Team Member:** Sai  
**Time to Complete:** 5 minutes

## Quick Setup

### Step 1: Install Dependencies

```bash
pip install -r agents/remediation/requirements.txt
```

### Step 2: Configure Environment

Ensure `.env` has these settings:

```env
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USER=Administrator
WEBMETHODS_PASSWORD=manage
HUNG_THREAD_THRESHOLD=300
```

### Step 3: Run Example

```bash
python -m agents.remediation.remediation_agent
```

## Usage Examples

### Example 1: Kill Hung Thread

```python
from agents.remediation.remediation_agent import RemediationAgent
from shared.models import ThreadInfo

# Create hung thread
thread = ThreadInfo(
    thread_id="0x1000",
    name="HTTP Handler",
    state="RUNNABLE",
    cpu_time=650.0  # 10+ minutes - hung
)

# Remediate with auto-approval
agent = RemediationAgent(auto_approve=True)
result = agent.run(thread_info=thread)

print(f"Action: {result['execution_result']['action']}")
print(f"Status: {result['execution_result']['status']}")
```

### Example 2: Handle Deadlock

```python
# Deadlock scenario
analysis = {
    "deadlocks": [
        {
            "lock": "0x2000",
            "owner": {"thread_id": "0x1000", "name": "Thread-1"},
            "waiters": [{"thread_id": "0x2000", "name": "Thread-2"}]
        }
    ]
}

# Will recommend server restart
agent = RemediationAgent(auto_approve=False)
result = agent.run(analysis_result=analysis)
```

### Example 3: High CPU Remediation

```python
# High CPU scenario
analysis = {
    "cpu_usage": 92.0,
    "memory_usage": 75.0
}

# Will force garbage collection
agent = RemediationAgent(auto_approve=True)
result = agent.run(analysis_result=analysis)
```

### Example 4: Integration with Collector

```python
from agents.collector.collector_agent import ThreadDumpCollectorAgent
from agents.remediation.remediation_agent import RemediationAgent

# Collect thread dump
collector = ThreadDumpCollectorAgent()
dump = collector.run()

# Find and remediate hung threads
if not dump.get("error"):
    hung_threads = [t for t in dump["parsed_threads"] if t.is_hung()]
    
    if hung_threads:
        agent = RemediationAgent(auto_approve=True)
        for thread in hung_threads:
            print(f"Remediating: {thread.name}")
            result = agent.run(thread_info=thread)
```

## Expected Output

```
======================================================================
Thread Dump Remediation Workflow - LangGraph Agent
======================================================================
[1/6] Analyzing thread issue...
✓ Analysis complete - Severity: CRITICAL
[2/6] Recommending remediation actions...
✓ Recommended 1 actions
   1. Kill hung thread 'HTTP Handler' (CPU time: 650.00s) (Priority: 1)
[3/6] Selecting remediation action...
✓ Selected: Kill hung thread 'HTTP Handler' (CPU time: 650.00s) (Auto-approved)
[5/6] Executing remediation action...
✓ Thread killed: HTTP Handler
[6/6] Verifying remediation result...
✓ Verification complete - Server responding normally

======================================================================
✅ Remediation Complete
Action: kill_thread
Status: success
======================================================================
```

## Remediation Types

| Action | When Used | Risk | Auto-Approve |
|--------|-----------|------|--------------|
| Kill Thread | CPU > 600s | High | No |
| Cancel Operation | CPU 300-600s | Medium | No |
| Restart Server | Deadlock | Critical | No |
| Force GC | CPU > 90% | Low | Yes |
| Clear Cache | Memory > 85% | Low | Yes |

## Approval Modes

### Auto-Approve Mode

```python
# Automatically approve all actions
agent = RemediationAgent(auto_approve=True)
```

### Manual Approval Mode

```python
# Require approval for critical actions
agent = RemediationAgent(auto_approve=False)

# Approval request will be displayed
# Critical/High severity auto-approved
```

## Integration Patterns

### With Monitor

```python
from agents.monitor.monitor_agent import MonitorAgent
from agents.remediation.remediation_agent import RemediationAgent

monitor = MonitorAgent()
monitor.set_remediation_agent(RemediationAgent(auto_approve=True))
monitor.start()
```

### With Dashboard

```python
# Trigger from dashboard button
def remediate_button_click(thread_id):
    thread = get_thread(thread_id)
    agent = RemediationAgent()
    return agent.run(thread_info=thread)
```

## Troubleshooting

### Connection Error

```
Error: Execution error: Connection refused
```

**Fix**: Check server URL and ensure server is running.

### Permission Error

```
Error: Execution error: 403 Forbidden
```

**Fix**: Verify user has admin privileges.

### Action Failed

```
Status: failed
```

**Fix**: Check server logs and retry with different action.

## Safety Tips

1. ✅ **Test First**: Always test in dev/test environment
2. ✅ **Monitor Results**: Track success rates
3. ✅ **Use Approval**: Require approval in production
4. ✅ **Log Actions**: Keep audit trail
5. ✅ **Verify Health**: Check server after remediation

## Next Steps

1. ✅ Run example to verify setup
2. 📊 Integrate with collector agent
3. 🔍 Add to monitoring workflow
4. 📈 View results in dashboard
5. 🚨 Configure alerts for remediations

## API Reference

```python
class RemediationAgent:
    def __init__(
        self,
        server_url: Optional[str] = None,
        auto_approve: bool = False
    )
    
    def run(
        self,
        thread_info: Optional[ThreadInfo] = None,
        analysis_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]
```

## Support

- **Documentation**: See `agents/remediation/README.md`
- **Tests**: Run `python agents/remediation/test_remediation.py`
- **Contact**: Sai (Team Member)

---

**Ready to remediate!** 🚀