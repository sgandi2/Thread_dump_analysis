# 🎯 Dashboard Access & System URLs

## 📊 Web Dashboard (Streamlit)

### Access URL
```
http://localhost:8501
```

**Status**: ✅ Running (Started successfully)

### Features
- **Real-time Thread Monitoring**: View all 75 threads from Integration Server
- **Thread Analysis**: See hung threads, blocked threads, deadlocks
- **AI Recommendations**: Get AI-powered suggestions for issues
- **Performance Metrics**: CPU, Memory, GC statistics
- **Remediation Actions**: Apply fixes directly from the dashboard
- **Historical Data**: View trends and patterns over time

### How to Access
1. Open your web browser
2. Navigate to: `http://localhost:8501`
3. The dashboard will show live data from your Integration Server

---

## 🔄 Complete Monitoring System Status

### 1. Thread Dump Collection (Running)
- **Method**: jstack (direct JVM access)
- **Interval**: Every 5 minutes (300 seconds)
- **Status**: ✅ Active
- **Data Location**: `data/thread_dumps/`
- **Latest Collection**: Check dashboard for real-time status

### 2. AI Analysis Engine (Running)
- **Agent**: LangGraph Analyzer Agent
- **Workflow**: 7-step analysis pipeline
- **Status**: ✅ Active
- **Results Location**: `data/analysis_results/`

### 3. Slack Notifications (Configured)
- **Status**: ✅ Ready
- **Webhook**: Configured in `.env`
- **Alert Types**: Hung threads, deadlocks, high CPU/memory
- **Cooldown**: 5 minutes between duplicate alerts

### 4. Remediation System (Ready)
- **Agent**: LangGraph Remediation Agent
- **Actions Available**:
  - Kill hung threads
  - Restart server
  - Force garbage collection
  - Clear caches
  - Increase thread pool
  - Cancel operations
- **Approval**: Manual approval required for critical actions

---

## 🖥️ System Components

### Running Services

| Service | Status | Port/Location | Purpose |
|---------|--------|---------------|---------|
| Streamlit Dashboard | ✅ Running | http://localhost:8501 | Web UI for monitoring |
| Thread Collector | ✅ Running | Background | Collects dumps every 5 min |
| Analyzer Agent | ✅ Running | Background | AI analysis of threads |
| Monitor Agent | ✅ Running | Background | Detects issues & alerts |
| MCP Server | ⏸️ Available | Port 3000 | API for agent integration |

### Data Directories

```
data/
├── thread_dumps/          # Raw & parsed thread dumps
│   ├── jstack_dump_*.txt  # Raw jstack output
│   └── jstack_dump_*.json # Parsed thread data
├── analysis_results/      # AI analysis results
│   └── analysis_*.json    # Analysis with recommendations
├── alerts/                # Alert history
│   └── alert_*.json       # Slack alerts sent
└── remediation/           # Remediation actions (if any)
    └── remediation_*.json # Actions taken
```

---

## 🎮 Quick Actions

### View Dashboard
```bash
# Dashboard is already running at:
http://localhost:8501
```

### Check System Status
```bash
python check_monitoring_status.py
```

### Analyze Latest Thread Dump
```bash
python analyze_collected_dump.py
```

### View Live Monitoring Dashboard (Console)
```bash
python monitor_dashboard.py
```

### Stop Monitoring
```bash
# Find and terminate the Python process running start_monitoring.py
# Or press Ctrl+C in the terminal where it's running
```

---

## 📋 Dashboard Features Guide

### Main Dashboard Sections

1. **Overview Panel**
   - Server health status
   - Active thread count
   - Hung thread count
   - CPU & Memory usage

2. **Thread List**
   - All 75 threads from Integration Server
   - Status indicators (Normal/Hung/Blocked/Waiting)
   - CPU time and blocked time
   - Click to view stack trace

3. **Analysis Results**
   - AI-powered severity assessment
   - Pattern detection
   - Deadlock detection
   - Recommendations

4. **Alerts & Notifications**
   - Recent alerts
   - Severity levels
   - Timestamps
   - Alert history

5. **Remediation Actions**
   - Available actions for each issue
   - Risk assessment
   - Approval workflow
   - Action history

6. **Performance Charts**
   - CPU usage over time
   - Memory usage trends
   - Thread count history
   - GC activity

---

## 🔧 Remediation Workflow

### From Dashboard

1. **Identify Issue**
   - Dashboard shows problematic threads
   - AI provides severity and recommendations

2. **Select Action**
   - Choose appropriate remediation action
   - Review risk assessment
   - See expected impact

3. **Approve & Execute**
   - Manual approval for critical actions
   - Automatic execution for low-risk actions
   - Real-time status updates

4. **Verify Results**
   - Post-action verification
   - Success/failure notification
   - Updated thread status

### Available Actions

| Action | Risk Level | Use Case |
|--------|-----------|----------|
| Kill Thread | Medium | Hung thread blocking resources |
| Cancel Operation | Low | Long-running operation |
| Force GC | Low | Memory pressure |
| Clear Cache | Low | Memory optimization |
| Increase Thread Pool | Low | Thread exhaustion |
| Restart Server | High | Critical issues only |

---

## 📊 Current System Statistics

### Integration Server
- **Process ID**: 9644
- **Total Threads**: 75
- **Status**: Healthy (INFO severity)
- **Hung Threads**: 0
- **Blocked Threads**: 0
- **Deadlocks**: 0

### Monitoring
- **Collections**: 2+ (and counting)
- **Analyses**: 2+ (and counting)
- **Alerts**: 0 (system healthy)
- **Remediations**: 0 (none needed)

---

## 🚀 Next Steps

1. **Access Dashboard**: Open http://localhost:8501 in your browser
2. **Monitor Threads**: Watch real-time thread status
3. **Review Analysis**: Check AI recommendations
4. **Set Alerts**: Configure Slack notifications
5. **Test Remediation**: Try actions on test issues

---

## 📞 Support & Documentation

### Key Files
- `README.md` - Project overview
- `QUICKSTART_MCP.md` - MCP integration guide
- `IMPLEMENTATION_PLAN.md` - Technical details
- `TEAM_ASSIGNMENTS.md` - Team responsibilities

### Scripts
- `start_monitoring.py` - Start monitoring system
- `check_monitoring_status.py` - Check system status
- `analyze_collected_dump.py` - Analyze thread dumps
- `monitor_dashboard.py` - Console dashboard

### Agents
- `agents/collector/` - Thread dump collection
- `agents/analyzer/` - AI analysis
- `agents/monitor/` - Monitoring & alerts
- `agents/remediation/` - Remediation actions

---

## ✅ System Health Check

Run this command to verify everything is working:

```bash
python check_monitoring_status.py
```

Expected output:
- ✅ Thread dumps being collected every 5 minutes
- ✅ Analysis results available
- ✅ No critical alerts (healthy system)
- ✅ Dashboard accessible at http://localhost:8501

---

**🎉 Your Thread Dump Analysis System is Fully Operational!**

Access the dashboard now: **http://localhost:8501**