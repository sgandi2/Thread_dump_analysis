# Phase 2: Monitor Agent - Quick Start Guide

## 🎯 Overview

Phase 2 implements the **Monitor Agent** that continuously monitors webMethods Integration Server for issues and sends Slack notifications using **LangGraph** for workflow orchestration and **Ollama** for AI-powered recommendations.

## ✅ What's Implemented

### Core Components

1. **Monitor Agent** ([`agents/monitor/monitor_agent.py`](agents/monitor/monitor_agent.py))
   - LangGraph workflow for monitoring
   - Detects hung threads (> 300s threshold)
   - Identifies blocked threads
   - Checks for deadlocks
   - Monitors CPU and memory usage
   - Alert deduplication

2. **Slack Notifier** ([`agents/monitor/slack_notifier.py`](agents/monitor/slack_notifier.py))
   - Rich Slack message formatting with blocks
   - Action buttons (Analyze, Remediate)
   - Alert deduplication
   - Test message functionality
   - Periodic summaries

3. **Scheduler** ([`agents/monitor/scheduler.py`](agents/monitor/scheduler.py))
   - APScheduler for periodic monitoring
   - Configurable polling interval (default: 30s)
   - Graceful shutdown handling
   - Status tracking

4. **Shared Utilities** ([`shared/`](shared/))
   - Configuration management with Ollama support
   - Data models (ThreadInfo, AlertMessage, etc.)
   - Utility functions for API calls and parsing

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Ollama (for AI recommendations)

```bash
# Install Ollama (if not already installed)
# Visit: https://ollama.ai

# Pull the model
ollama pull llama2

# Verify it's running
curl http://localhost:11434/api/tags
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Required Configuration:**

```bash
# webMethods Integration Server
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USER=Administrator
WEBMETHODS_PASSWORD=manage

# Slack (REQUIRED for notifications)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_CHANNEL=#alerts

# Ollama (for AI recommendations)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Thresholds
HUNG_THREAD_THRESHOLD=300
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85

# Monitoring
POLL_INTERVAL=30
```

### 4. Get Slack Webhook URL

1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to your workspace
5. Copy the webhook URL to `.env`

### 5. Run the Monitor

```bash
# Run with default settings (30s interval)
python run_monitor.py

# Run with custom interval
python run_monitor.py --interval 60

# Run once (no scheduling)
python run_monitor.py --once

# Test Slack integration
python run_monitor.py --test-slack
```

## 📊 LangGraph Workflow

The Monitor Agent uses LangGraph to orchestrate the monitoring workflow:

```
fetch_server_stats
    ↓
detect_hung_threads
    ↓
detect_blocked_threads
    ↓
check_deadlocks
    ↓
check_resource_usage
    ↓
generate_alerts
    ↓
[Alerts sent to Slack]
```

## 🔔 Alert Types

The monitor detects and alerts on:

1. **Hung Threads** (HIGH severity)
   - Threads running > threshold time
   - Includes stack trace preview
   - Recommendations provided

2. **Deadlocks** (CRITICAL severity)
   - Circular thread dependencies
   - Multiple threads involved
   - Immediate action required

3. **High CPU Usage** (HIGH severity)
   - CPU > 80% threshold
   - Identifies CPU-intensive threads

4. **High Memory Usage** (HIGH severity)
   - Memory > 85% threshold
   - GC analysis recommendations

5. **Blocked Threads** (MEDIUM severity)
   - Threads in BLOCKED state
   - Lock contention analysis

## 📝 Slack Message Format

Alerts include:
- **Header**: Issue title with severity emoji
- **Details**: Severity, type, timestamp, server
- **Description**: Issue explanation
- **Thread Info**: ID, name, state, duration
- **Stack Trace**: Preview (first 5 lines)
- **Recommendations**: AI-powered suggestions
- **Action Buttons**: Analyze, Remediate

## 🧪 Testing

### Test Slack Integration

```bash
python run_monitor.py --test-slack
```

### Run Single Check

```bash
python run_monitor.py --once
```

### Test Individual Components

```bash
# Test monitor agent
python -m agents.monitor.monitor_agent

# Test Slack notifier
python -m agents.monitor.slack_notifier

# Test scheduler
python -m agents.monitor.scheduler
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBMETHODS_URL` | `http://localhost:5555` | Integration Server URL |
| `WEBMETHODS_USER` | `Administrator` | Admin username |
| `WEBMETHODS_PASSWORD` | `manage` | Admin password |
| `SLACK_WEBHOOK_URL` | - | Slack webhook (required) |
| `SLACK_CHANNEL` | `#alerts` | Target Slack channel |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API URL |
| `OLLAMA_MODEL` | `llama2` | Ollama model name |
| `HUNG_THREAD_THRESHOLD` | `300` | Hung thread threshold (seconds) |
| `CPU_THRESHOLD` | `80` | CPU alert threshold (%) |
| `MEMORY_THRESHOLD` | `85` | Memory alert threshold (%) |
| `POLL_INTERVAL` | `30` | Monitoring interval (seconds) |
| `ALERT_COOLDOWN` | `300` | Alert deduplication time (seconds) |

### Command Line Options

```bash
python run_monitor.py --help

Options:
  --interval SECONDS    Monitoring interval (default: 30)
  --once               Run once and exit
  --test-slack         Test Slack integration
  --server-url URL     webMethods server URL
```

## 📁 File Structure

```
agents/monitor/
├── __init__.py
├── monitor_agent.py      # Main monitoring logic with LangGraph
├── slack_notifier.py     # Slack integration
└── scheduler.py          # APScheduler for periodic monitoring

shared/
├── __init__.py
├── config.py            # Configuration with Ollama support
├── models.py            # Data models
└── utils.py             # Utility functions

run_monitor.py           # Main entry point
```

## 🎯 Key Features

### 1. LangGraph Workflow
- State-based workflow orchestration
- Clear separation of monitoring steps
- Easy to extend and modify
- Error handling at each node

### 2. Ollama Integration
- Local AI for recommendations
- No external API costs
- Privacy-friendly
- Fast response times

### 3. Smart Alerting
- Alert deduplication (5-minute cooldown)
- Severity-based prioritization
- Rich Slack formatting
- Action buttons for next steps

### 4. Flexible Scheduling
- Configurable polling interval
- Graceful shutdown
- Status tracking
- Periodic summaries

## 🔍 Monitoring Flow

1. **Fetch Server Stats**
   - Connect to webMethods API
   - Retrieve thread information
   - Get CPU/memory metrics

2. **Detect Issues**
   - Check for hung threads
   - Identify blocked threads
   - Detect deadlocks
   - Monitor resource usage

3. **Generate Alerts**
   - Create alert messages
   - Apply deduplication
   - Format for Slack

4. **Send Notifications**
   - Post to Slack webhook
   - Include action buttons
   - Track sent alerts

## 🐛 Troubleshooting

### Slack Notifications Not Working

```bash
# Test webhook
python run_monitor.py --test-slack

# Check webhook URL in .env
echo $SLACK_WEBHOOK_URL

# Verify Slack app permissions
```

### Ollama Connection Issues

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Test model
ollama run llama2 "Hello"
```

### webMethods Connection Issues

```bash
# Test API endpoint
curl -u Administrator:manage http://localhost:5555/admin/threads

# Check credentials in .env
# Verify server is running
```

## 📈 Next Steps

After Phase 2, you can:

1. **Integrate with Collector Agent** (Phase 2 - Ranadeep)
   - Automatic thread dump collection on alerts
   - Detailed analysis trigger

2. **Add AI Analysis** (Phase 2 - Ranadeep)
   - Use Ollama for root cause analysis
   - Generate detailed recommendations

3. **Implement Remediation** (Phase 2 - Sai)
   - Automated fixes for common issues
   - Safe rollback mechanisms

4. **Build Dashboard** (Phase 2 - Bhagwan)
   - Real-time monitoring view
   - Historical trends
   - Alert management

## 🎉 Success Criteria

✅ Monitor detects issues within 30 seconds
✅ Slack alerts are clear and actionable
✅ No false positives
✅ LangGraph workflow is stable
✅ Ollama integration works
✅ Alert deduplication prevents spam

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Slack API Documentation](https://api.slack.com/)
- [APScheduler Documentation](https://apscheduler.readthedocs.io/)

---

**Phase 2 Status**: ✅ Complete - Monitor Agent with LangGraph & Slack Notifications

**Next**: Phase 2 continues with Collector and Analyzer agents (Ranadeep), Specialist agents (Vinay), Dashboard (Bhagwan), and MCP/Remediation (Sai)