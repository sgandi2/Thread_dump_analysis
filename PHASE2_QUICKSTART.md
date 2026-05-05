# Phase 2 Quick Start Guide

## Monitor Agent with Slack Notifications using LangGraph

This guide will help you quickly set up and run the Monitor Agent for Phase 2.

## Prerequisites

- Python 3.8+
- Ollama (for AI recommendations)
- Slack workspace with webhook access
- webMethods Integration Server (or mock for testing)

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install and Start Ollama

**Linux/Mac:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama2
```

**Windows:**
- Download from https://ollama.com/download
- Install and run Ollama
- Open terminal: `ollama pull llama2`

### 3. Configure Slack Webhook

1. Go to https://api.slack.com/apps
2. Create new app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to your channel
5. Copy webhook URL

### 4. Setup Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
# Required:
#   - SLACK_WEBHOOK_URL
#   - WEBMETHODS_URL (or use default for testing)
```

### 5. Test Configuration

```bash
python run_monitor.py --check-config
```

This will verify:
- ✅ All dependencies installed
- ✅ Slack webhook configured
- ✅ Ollama running
- ✅ Configuration valid

### 6. Test Slack Integration

```bash
python run_monitor.py --test-slack
```

You should see a test message in your Slack channel!

## Running the Monitor

### Option 1: Continuous Monitoring (Recommended)

```bash
python run_monitor.py --scheduled
```

This will:
- Monitor every 30 seconds (configurable)
- Send alerts to Slack when issues detected
- Run until stopped (Ctrl+C)

### Option 2: Custom Interval

```bash
python run_monitor.py --scheduled --interval 60
```

Monitor every 60 seconds instead of default 30.

### Option 3: Single Check

```bash
python run_monitor.py --once
```

Run one monitoring cycle and exit.

## What Gets Monitored?

The Monitor Agent detects:

1. **🔴 Hung Threads** - Threads running > 300 seconds
2. **🔴 Deadlocks** - Circular thread dependencies
3. **🟠 High CPU** - CPU usage > 80%
4. **🟠 High Memory** - Memory usage > 85%
5. **🟡 Blocked Threads** - Threads in BLOCKED state

## Slack Alert Format

Alerts include:
- 🚨 **Header** with severity emoji
- 📊 **Details**: Type, time, server
- 🧵 **Thread Info**: ID, name, state, duration
- 📝 **Stack Trace** preview
- 💡 **AI Recommendations** from Ollama
- 🔘 **Action Buttons**: Analyze, Remediate

## Configuration Options

Edit `.env` to customize:

```bash
# Thresholds
HUNG_THREAD_THRESHOLD=300    # seconds
CPU_THRESHOLD=80             # percentage
MEMORY_THRESHOLD=85          # percentage

# Monitoring
POLL_INTERVAL=30             # seconds
ALERT_COOLDOWN=300           # seconds (prevents spam)

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2          # or llama3, mistral, etc.
```

## Programmatic Usage

```python
from agents.monitor import MonitorAgent, SlackNotifier, MonitorScheduler

# One-time check
agent = MonitorAgent()
alerts = agent.monitor()

# Send to Slack
notifier = SlackNotifier()
notifier.send_alerts(alerts)

# Scheduled monitoring
scheduler = MonitorScheduler(interval=30)
scheduler.start_monitoring()
# ... runs continuously ...
scheduler.stop_monitoring()
```

## Examples

Run interactive examples:

```bash
python examples/test_monitor.py
```

Choose from:
1. Basic Monitoring
2. Slack Notifications
3. Scheduled Monitoring
4. Custom Alert
5. Monitor with Callback

## Troubleshooting

### "No Slack webhook configured"

**Solution:**
```bash
# Add to .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### "Cannot connect to Ollama"

**Solution:**
```bash
# Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```

### "Import langgraph could not be resolved"

**Solution:**
```bash
pip install langgraph langchain langchain-openai
```

### "Cannot connect to webMethods"

**Solution:**
```bash
# For testing without actual server, the monitor will log errors
# but continue running. Update WEBMETHODS_URL in .env when ready.
```

## File Structure

```
agents/monitor/
├── __init__.py           # Package exports
├── monitor_agent.py      # Core monitoring with LangGraph
├── slack_notifier.py     # Slack integration
└── scheduler.py          # APScheduler for periodic checks

shared/
├── config.py            # Configuration management
├── models.py            # Data models
└── utils.py             # Utility functions

run_monitor.py           # Quick start script
examples/test_monitor.py # Example usage
```

## LangGraph Workflow

The Monitor Agent uses LangGraph for stateful workflow:

```
┌─────────────────┐
│ Fetch Stats     │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Detect Hung     │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Detect Blocked  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Check Deadlocks │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Check Resources │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Generate Alerts │
└─────────────────┘
```

## Next Steps

After Phase 2 is working:

1. **Phase 3**: Integrate with Collector Agent (Ranadeep)
2. **Phase 3**: Connect to Analyzer Agent (Ranadeep)
3. **Phase 3**: Add GC Specialist (Vinay)
4. **Phase 3**: Add CPU Specialist (Vinay)
5. **Phase 3**: Connect Remediation Agent (Sai)
6. **Phase 3**: Display in Dashboard (Bhagwan)

## Support

For issues or questions:
1. Check logs in `logs/monitor_agent.log`
2. Run `python run_monitor.py --check-config`
3. Review `PHASE2_MONITOR_AGENT.md` for detailed docs

## Success Criteria ✅

- [x] Monitor detects hung threads within 30 seconds
- [x] Slack alerts are clear and actionable
- [x] LangGraph workflow handles errors gracefully
- [x] Alert deduplication prevents spam
- [x] Scheduled monitoring runs continuously
- [x] Ollama integration for AI recommendations

---

**Phase 2 Complete!** 🎉

Ready for integration with other agents in Phase 3.