# Phase 2: Monitor Agent Implementation

## Overview

This document describes the implementation of the Monitor Agent with Slack notifications using LangGraph for Phase 2 of the Thread Dump Analysis AI Agent project.

## Components Implemented

### 1. Shared Infrastructure

#### `shared/config.py`
- Central configuration management
- Environment variable handling
- **Ollama integration** for local AI recommendations
- Threshold configurations for monitoring
- Support for webMethods Integration Server settings

#### `shared/models.py`
- Data models for thread information (`ThreadInfo`)
- Thread dump data structure (`ThreadDumpData`)
- Alert message format (`AlertMessage`)
- Analysis results (`AnalysisResult`)
- Remediation actions (`RemediationAction`)
- Enums for thread states, alert severity, and issue types

#### `shared/utils.py`
- API client for webMethods Integration Server
- Thread dump parser
- Slack message formatter
- Metrics calculator
- **Ollama API integration** for AI recommendations
- Logging setup utilities

### 2. Monitor Agent (`agents/monitor/`)

#### `monitor_agent.py` - Core Monitoring Logic with LangGraph

**LangGraph Workflow:**
```
fetch_server_stats → detect_hung_threads → detect_blocked_threads → 
check_deadlocks → check_resource_usage → generate_alerts
```

**Key Features:**
- Polls webMethods Integration Server for thread statistics
- Detects hung threads (threads exceeding threshold duration)
- Identifies blocked threads and potential deadlocks
- Monitors CPU and memory usage
- Generates structured alerts with recommendations
- Alert deduplication to prevent spam

**Workflow Nodes:**
1. **fetch_server_stats**: Retrieves current thread and resource data
2. **detect_hung_threads**: Identifies threads running longer than threshold
3. **detect_blocked_threads**: Finds threads in BLOCKED state
4. **check_deadlocks**: Detects potential deadlock situations
5. **check_resource_usage**: Monitors CPU and memory thresholds
6. **generate_alerts**: Creates AlertMessage objects for issues

#### `slack_notifier.py` - Slack Integration

**Features:**
- Sends formatted alerts to Slack using webhook
- Rich message formatting with Slack blocks
- Action buttons for "Analyze" and "Remediate"
- Alert deduplication
- Test message functionality
- Monitoring summaries

**Message Format:**
- Header with severity emoji
- Issue details (type, time, server)
- Thread information (ID, name, state, duration)
- Stack trace preview
- AI-powered recommendations
- Action buttons

#### `scheduler.py` - Periodic Monitoring

**Features:**
- APScheduler-based periodic monitoring
- Configurable polling interval (default: 30 seconds)
- Graceful startup and shutdown
- Status tracking (run count, alert count)
- Interval adjustment on-the-fly
- Periodic summary reports

**Commands:**
- `start_monitoring()`: Begin periodic checks
- `stop_monitoring()`: Stop monitoring
- `adjust_interval(seconds)`: Change polling frequency
- `run_once()`: Execute single monitoring cycle
- `get_status()`: Get current status

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# webMethods Integration Server
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USER=Administrator
WEBMETHODS_PASSWORD=manage

# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#alerts

# Ollama Configuration (Local AI)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Monitoring Thresholds
HUNG_THREAD_THRESHOLD=300  # seconds
CPU_THRESHOLD=80           # percentage
MEMORY_THRESHOLD=85        # percentage
DEADLOCK_CHECK_ENABLED=true

# Monitoring Settings
POLL_INTERVAL=30           # seconds
ALERT_COOLDOWN=300         # seconds (5 minutes)

# Logging
LOG_LEVEL=INFO
LOG_DIR=logs
```

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Ollama (for AI recommendations)

**Linux/Mac:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download from https://ollama.com/download

**Start Ollama and pull model:**
```bash
ollama serve
ollama pull llama2
```

### 3. Configure Slack Webhook

1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Create a webhook for your channel
5. Copy webhook URL to `.env` file

### 4. Setup Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Running the Monitor Agent

#### Option 1: With Scheduler (Recommended)

```bash
python -m agents.monitor.scheduler
```

This will:
- Start periodic monitoring every 30 seconds (configurable)
- Send alerts to Slack when issues detected
- Run continuously until stopped (Ctrl+C)

#### Option 2: Single Run

```bash
python -m agents.monitor.monitor_agent
```

This will:
- Run one monitoring cycle
- Generate alerts if issues found
- Exit after completion

#### Option 3: Test Slack Integration

```bash
python -m agents.monitor.slack_notifier
```

This will:
- Send a test message to Slack
- Verify webhook configuration
- Exit after sending

### Programmatic Usage

```python
from agents.monitor.monitor_agent import MonitorAgent
from agents.monitor.slack_notifier import SlackNotifier
from agents.monitor.scheduler import MonitorScheduler

# One-time monitoring
agent = MonitorAgent()
alerts = agent.monitor()

# Send alerts to Slack
notifier = SlackNotifier()
notifier.send_alerts(alerts)

# Scheduled monitoring
scheduler = MonitorScheduler(interval=30)
scheduler.start_monitoring()

# Keep running...
# scheduler.stop_monitoring()  # When done
```

## Alert Types

### 1. Hung Thread Alert
- **Severity**: HIGH
- **Trigger**: Thread running > threshold (default: 300s)
- **Recommendations**:
  - Review thread stack trace for blocking operations
  - Check for database connection issues
  - Consider thread interruption if safe

### 2. Deadlock Alert
- **Severity**: CRITICAL
- **Trigger**: Multiple threads in circular wait
- **Recommendations**:
  - Analyze thread dump for circular dependencies
  - Consider restarting affected services
  - Review locking mechanisms in code

### 3. High CPU Alert
- **Severity**: HIGH
- **Trigger**: CPU usage > threshold (default: 80%)
- **Recommendations**:
  - Identify CPU-intensive threads
  - Review recent deployments
  - Consider scaling resources

### 4. High Memory Alert
- **Severity**: HIGH
- **Trigger**: Memory usage > threshold (default: 85%)
- **Recommendations**:
  - Check for memory leaks
  - Review GC logs
  - Consider increasing heap size

### 5. Blocked Threads Alert
- **Severity**: MEDIUM
- **Trigger**: Threads in BLOCKED state
- **Recommendations**:
  - Identify lock contention
  - Review synchronization code
  - Check database connection pool

## LangGraph Workflow Details

The Monitor Agent uses LangGraph to create a stateful workflow:

```python
class MonitorState(TypedDict):
    server_url: str
    timestamp: datetime
    threads: List[Dict[str, Any]]
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    hung_threads: List[Dict[str, Any]]
    blocked_threads: List[Dict[str, Any]]
    deadlocks: List[List[Dict[str, Any]]]
    alerts: List[AlertMessage]
    metrics: Dict[str, Any]
    error: Optional[str]
```

**State Flow:**
1. Initial state created with server URL
2. Each node processes and updates state
3. State passed to next node in sequence
4. Final state contains all alerts and metrics

## Integration with Other Agents

The Monitor Agent is designed to trigger other agents:

```python
# When hung thread detected
if hung_threads:
    # Trigger Collector Agent (Ranadeep)
    collector_agent.collect_thread_dump(server_url)
    
    # Trigger Analyzer Agent (Ranadeep)
    analyzer_agent.analyze(thread_dump)
    
    # Trigger Specialist Agents (Vinay)
    gc_specialist.analyze_gc_logs()
    cpu_specialist.analyze_cpu_usage()
    
    # Trigger Remediation Agent (Sai)
    remediation_agent.suggest_actions(analysis_result)
```

## Testing

### Test Scenarios

1. **Normal Operation**
   ```bash
   # Should show "No alerts generated"
   python -m agents.monitor.monitor_agent
   ```

2. **Slack Integration**
   ```bash
   # Should send test message to Slack
   python -m agents.monitor.slack_notifier
   ```

3. **Scheduled Monitoring**
   ```bash
   # Should run continuously
   python -m agents.monitor.scheduler
   ```

### Mock Testing

For testing without actual webMethods server:

```python
# Mock the API call
from unittest.mock import patch

with patch('shared.utils.call_webmethods_api') as mock_api:
    mock_api.return_value = {
        "threads": [
            {
                "id": "thread-1",
                "name": "Test Thread",
                "state": "RUNNABLE",
                "cpuTime": 350000  # 350 seconds (hung)
            }
        ]
    }
    
    agent = MonitorAgent()
    alerts = agent.monitor()
    assert len(alerts) > 0
```

## Troubleshooting

### Issue: No Slack notifications

**Solution:**
1. Verify webhook URL in `.env`
2. Test with: `python -m agents.monitor.slack_notifier`
3. Check Slack app permissions
4. Review logs in `logs/slack_notifier.log`

### Issue: Ollama connection failed

**Solution:**
1. Ensure Ollama is running: `ollama serve`
2. Verify URL: `curl http://localhost:11434/api/tags`
3. Pull model: `ollama pull llama2`
4. Check `OLLAMA_BASE_URL` in `.env`

### Issue: Cannot connect to webMethods

**Solution:**
1. Verify server URL and credentials in `.env`
2. Test connection: `curl -u user:pass http://localhost:5555/admin/threads`
3. Check firewall settings
4. Review logs in `logs/monitor_agent.log`

### Issue: Import errors

**Solution:**
```bash
# Install missing dependencies
pip install -r requirements.txt

# Verify installations
python -c "import langgraph; print('LangGraph OK')"
python -c "import slack_sdk; print('Slack SDK OK')"
python -c "import apscheduler; print('APScheduler OK')"
```

## Performance Considerations

- **Polling Interval**: Default 30s, adjust based on load
- **Alert Cooldown**: 5 minutes to prevent spam
- **API Timeout**: 30 seconds for webMethods calls
- **Thread Threshold**: 300 seconds (5 minutes) for hung threads

## Next Steps (Phase 3)

1. **Integration**: Connect with Collector Agent (Ranadeep)
2. **Analysis**: Feed data to Analyzer Agent (Ranadeep)
3. **Specialists**: Invoke GC and CPU specialists (Vinay)
4. **Remediation**: Trigger automated fixes (Sai)
5. **Dashboard**: Display in real-time UI (Bhagwan)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Monitor Agent                         │
│                   (LangGraph Workflow)                   │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │ Fetch Stats  │───▶│ Detect Hung  │                  │
│  └──────────────┘    └──────────────┘                  │
│         │                    │                          │
│         ▼                    ▼                          │
│  ┌──────────────┐    ┌──────────────┐                  │
│  │Check Resource│    │Detect Blocked│                  │
│  └──────────────┘    └──────────────┘                  │
│         │                    │                          │
│         └────────┬───────────┘                          │
│                  ▼                                      │
│         ┌──────────────┐                                │
│         │Check Deadlock│                                │
│         └──────────────┘                                │
│                  │                                      │
│                  ▼                                      │
│         ┌──────────────┐                                │
│         │Generate Alert│                                │
│         └──────────────┘                                │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────────┐
         │   Slack Notifier     │
         │  (Webhook + Blocks)  │
         └──────────────────────┘
                     │
                     ▼
              ┌──────────┐
              │  Slack   │
              │ Channel  │
              └──────────┘
```

## Success Metrics

✅ **Completed:**
- Monitor agent detects hung threads within 30 seconds
- Slack alerts are clear and actionable
- LangGraph workflow handles errors gracefully
- Alert deduplication prevents spam
- Scheduled monitoring runs continuously
- Ollama integration for AI recommendations

## Team Member: Tapaswini

**Responsibilities:**
- ✅ Monitor Agent implementation
- ✅ Slack notification system
- ✅ Scheduling logic with APScheduler
- ✅ LangGraph workflow design
- ✅ Alert deduplication
- ✅ Integration with Ollama

**Time Spent:** Phase 2 (10-25 minutes as per plan)

---

*Phase 2 Complete! Ready for integration with other agents in Phase 3.*