# Local Thread Dump Collection & Analysis Guide

This guide will help you collect thread dumps from your Integration Server and analyze them locally using ThreadHeap Guardian.

---

## 🎯 Quick Start - 3 Steps

### Step 1: Collect Thread Dump

**Option A: Using File-Based Collection (Recommended)**
```bash
# Point to your Integration Server's diagnostics directory
python start_monitoring_from_files.py --directory "C:\SoftwareAG\IntegrationServer\instances\default\logs\diagnostics"
```

**Option B: Using jcmd (if you have access)**
```bash
# First, find your Integration Server PID
python collect_with_jcmd.py --list

# Then collect thread dump
python collect_with_jcmd.py --pid <YOUR_PID>
```

**Option C: Manual Collection**
```bash
# If you already have a thread dump file, just copy it to:
# data/thread_dumps/your_dump.txt
```

### Step 2: Analyze the Thread Dump

```bash
# Analyze the most recent dump
python analyze_collected_dump.py

# Or analyze a specific file
python analyze_collected_dump.py --file data/thread_dumps/your_dump.txt
```

### Step 3: View Results

```bash
# Start the dashboard to see visual analysis
python -m streamlit run dashboard/app_enhanced.py --server.port 8502

# Open browser to: http://localhost:8502
```

---

## 📋 Detailed Instructions

### Method 1: File-Based Collection (Production Ready)

**Best for:** Production environments, service accounts, no permission issues

**Setup:**

1. **Locate Integration Server diagnostics directory:**
   ```
   Windows: C:\SoftwareAG\IntegrationServer\instances\<instanceName>\logs\diagnostics
   Linux: /opt/softwareag/IntegrationServer/instances/<instanceName>/logs/diagnostics
   ```

2. **Start monitoring:**
   ```bash
   python start_monitoring_from_files.py --directory "YOUR_DIAGNOSTICS_PATH"
   ```

3. **Trigger thread dump in Integration Server:**
   - Open Integration Server Administrator
   - Go to: Settings → Diagnostics → Generate Thread Dump
   - Or wait for automatic generation (if configured)

4. **Monitor will automatically:**
   - Detect new thread dump files
   - Parse and analyze them
   - Send alerts to Slack (if configured)
   - Save analysis results to `data/analysis_results/`

**Advantages:**
- ✅ No special permissions needed
- ✅ Works with service accounts
- ✅ Production-ready
- ✅ Continuous monitoring

---

### Method 2: Direct Collection with jcmd

**Best for:** Development, testing, when you have access

**Prerequisites:**
- Java Development Kit (JDK) installed
- jcmd in PATH or JAVA_HOME set
- Same user context as Integration Server (or admin rights)

**Steps:**

1. **Verify jcmd is available:**
   ```bash
   # Windows
   where jcmd
   
   # Linux/Mac
   which jcmd
   ```

2. **List Java processes:**
   ```bash
   python collect_with_jcmd.py --list
   ```
   
   Output will show:
   ```
   9584 com.wm.server.Server
   12345 org.eclipse.equinox.launcher.Main
   ```

3. **Collect thread dump:**
   ```bash
   python collect_with_jcmd.py --pid 9584
   ```
   
   This saves to: `data/thread_dumps/jcmd_dump_YYYYMMDD_HHMMSS.txt`

**Troubleshooting:**
- If "Access Denied": Use file-based collection instead
- If "jcmd not found": Add JDK bin to PATH or use file-based collection

---

### Method 3: Manual Collection

**Best for:** One-time analysis, existing thread dumps

**Steps:**

1. **Get thread dump file** (from any source):
   - Integration Server Administrator → Generate Thread Dump
   - Existing diagnostic files
   - Support team provided dumps
   - jstack/jcmd output

2. **Copy to project:**
   ```bash
   # Copy your thread dump file
   copy "C:\path\to\your\threaddump.txt" "data\thread_dumps\"
   ```

3. **Analyze:**
   ```bash
   python analyze_collected_dump.py --file data/thread_dumps/threaddump.txt
   ```

---

## 🔍 Analysis Options

### Quick Analysis (Command Line)

```bash
# Analyze most recent dump
python analyze_collected_dump.py

# Analyze specific file
python analyze_collected_dump.py --file data/thread_dumps/dump.txt

# Get detailed output
python analyze_collected_dump.py --verbose
```

**Output includes:**
- Thread count and states
- Hung threads (>60s CPU time)
- Long-running threads (30-60s)
- Blocked threads
- Deadlocks
- AI-generated recommendations

### Visual Analysis (Dashboard)

```bash
# Start dashboard
python -m streamlit run dashboard/app_enhanced.py --server.port 8502
```

**Dashboard shows:**
- System overview with metrics
- Thread state distribution
- Hung and long-running threads
- Detailed thread information
- AI recommendations
- Alert history

---

## 📊 Understanding the Analysis

### Thread States

**RUNNABLE** - Thread is executing
- Normal if CPU time is reasonable
- Concerning if CPU time > 60s (hung)
- Warning if CPU time 30-60s (long-running)

**BLOCKED** - Waiting for monitor lock
- Check what lock it's waiting for
- Look for potential deadlocks

**WAITING** - Waiting for notification
- Normal for idle threads
- Check wait time if excessive

**TIMED_WAITING** - Waiting with timeout
- Usually normal
- Check if timeout is appropriate

### Severity Levels

**CRITICAL** - Immediate attention required
- Deadlocks detected
- Multiple hung threads (>60s)
- System stability at risk

**HIGH** - Urgent attention needed
- Hung threads detected
- Resource exhaustion
- Performance degradation

**MEDIUM** - Should be addressed
- Long-running threads (30-60s)
- High thread contention
- Potential issues developing

**LOW** - Informational
- Normal operations
- Minor optimizations possible

---

## 🎯 Common Scenarios

### Scenario 1: Hung Thread Detection

**Symptoms:**
- Thread CPU time > 60 seconds
- Thread state: RUNNABLE
- No progress being made

**Analysis Steps:**
1. Collect thread dump
2. Run analysis: `python analyze_collected_dump.py`
3. Look for threads with high CPU time
4. Check stack trace for infinite loops
5. Review AI recommendations

**Example Output:**
```
[CRITICAL] Hung Thread Detected
Thread: HTTP Handler-123
CPU Time: 125.5 seconds
State: RUNNABLE
Stack: com.wm.app.b2b.server.ServiceThread.run()

Recommendation: Thread appears stuck in infinite loop.
Check service logic for exit conditions.
```

### Scenario 2: Deadlock Detection

**Symptoms:**
- Multiple threads blocked
- Circular lock dependency
- System appears frozen

**Analysis Steps:**
1. Collect thread dump
2. Run analysis with deadlock detection
3. Review circular dependencies
4. Identify lock acquisition order

**Example Output:**
```
[CRITICAL] Deadlock Detected
Thread-A waiting for lock held by Thread-B
Thread-B waiting for lock held by Thread-A

Recommendation: Review lock acquisition order.
Implement consistent locking strategy.
```

### Scenario 3: Performance Degradation

**Symptoms:**
- Slow response times
- High thread count
- Many blocked threads

**Analysis Steps:**
1. Collect multiple thread dumps (5-10 seconds apart)
2. Compare thread states
3. Identify bottlenecks
4. Check resource utilization

---

## 📁 Output Files

### Thread Dumps
**Location:** `data/thread_dumps/`
**Format:** `.txt` files
**Naming:** `jcmd_dump_YYYYMMDD_HHMMSS.txt`

### Analysis Results
**Location:** `data/analysis_results/`
**Format:** JSON files
**Naming:** `analysis_YYYYMMDD_HHMMSS.json`

**Contents:**
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_threads": 156,
  "hung_threads": 2,
  "long_running_threads": 5,
  "blocked_threads": 8,
  "severity": "HIGH",
  "issues": [...],
  "recommendations": [...]
}
```

### Alerts
**Location:** `data/alerts/`
**Format:** JSON files
**Naming:** `alert_TIMESTAMP_ID.json`

---

## 🔧 Configuration

### Environment Variables

Create `.env` file:
```bash
# Integration Server
WEBMETHODS_URL=http://localhost:5555
WEBMETHODS_USERNAME=Administrator
WEBMETHODS_PASSWORD=manage

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# AI Model (optional)
OPENAI_API_KEY=your-api-key
# or
ANTHROPIC_API_KEY=your-api-key
```

### Thresholds

Edit `shared/models.py`:
```python
# Hung thread threshold (seconds)
HUNG_THRESHOLD = 60

# Long-running threshold (seconds)
LONG_RUNNING_THRESHOLD = 30
```

---

## 🚀 Automation

### Continuous Monitoring

```bash
# Start file-based monitoring (runs continuously)
python start_monitoring_from_files.py --directory "YOUR_DIAGNOSTICS_PATH"

# Or use scheduled monitoring
python start_monitoring.py --interval 300  # Every 5 minutes
```

### Scheduled Analysis

**Windows Task Scheduler:**
```batch
# Create scheduled task
schtasks /create /tn "ThreadDumpAnalysis" /tr "python C:\path\to\analyze_collected_dump.py" /sc hourly
```

**Linux Cron:**
```bash
# Add to crontab
0 * * * * cd /path/to/project && python analyze_collected_dump.py
```

---

## 📞 Support

**Need Help?**
1. Check [THREAD_COLLECTION_METHODS.md](THREAD_COLLECTION_METHODS.md) for collection methods
2. Review [TROUBLESHOOTING_JSTACK.md](TROUBLESHOOTING_JSTACK.md) for common issues
3. See [README.md](README.md) for project overview

**Common Issues:**
- **Permission denied**: Use file-based collection
- **jcmd not found**: Add JDK bin to PATH or use file-based
- **No thread dumps**: Check Integration Server diagnostics configuration
- **Analysis fails**: Verify thread dump file format

---

## ✅ Checklist

Before starting:
- [ ] Integration Server is running
- [ ] You have access to diagnostics directory OR jcmd
- [ ] Python environment is set up
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` file configured (optional for basic analysis)

For production monitoring:
- [ ] File-based monitoring configured
- [ ] Slack webhook set up (optional)
- [ ] Dashboard accessible
- [ ] Alerts configured
- [ ] Monitoring running as service

---

**Ready to start? Choose your collection method above and begin analyzing!**