# Monitoring System Restart Guide

## Current Issue
The monitoring stopped at 21:04:33. The `start_monitoring_admin.bat` may be running but not collecting new dumps due to:
1. **Access Denied Error**: jstack needs administrator privileges
2. **Process Stopped**: The monitoring loop may have exited

## Solution: Restart Monitoring with Admin Rights

### Step 1: Stop Any Running Monitoring
1. Close any open `start_monitoring_admin.bat` windows
2. Or press `Ctrl+C` in the terminal running the monitoring

### Step 2: Restart with Administrator Privileges
1. **Right-click** on `start_monitoring_admin.bat`
2. Select **"Run as administrator"**
3. Click **"Yes"** when prompted by UAC

### Step 3: Verify Monitoring is Active
You should see output like:
```
======================================================================
CONTINUOUS THREAD DUMP MONITORING
======================================================================
Interval: 60 seconds (1 minute)
Slack alerts: Enabled
Time: 2026-05-05 21:25:00
======================================================================

Finding Integration Server process...
[SUCCESS] Found Integration Server (PID: 9584)

======================================================================
MONITORING STARTED - Press Ctrl+C to stop
======================================================================

[CYCLE 1] 2026-05-05 21:25:32
Collecting thread dump from PID 9584...
✅ Thread dump saved: jstack_dump_20260505_212532.txt
✅ Parsed 156 threads -> jstack_dump_20260505_212532.json
```

### Step 4: Check New Thread Dumps
New dumps should appear in `data/thread_dumps/` every 60 seconds:
```
data/thread_dumps/
  jstack_dump_20260505_212532.txt
  jstack_dump_20260505_212532.json
  jstack_dump_20260505_212632.txt
  jstack_dump_20260505_212632.json
  ...
```

## What the Monitoring System Does

### 1. **Collect** (Every 60 seconds)
- Uses jstack to capture thread dump from Integration Server
- Saves raw dump as `.txt` file
- Parses and saves structured data as `.json` file

### 2. **Analyze** (Immediately after collection)
- Detects hung threads (CPU time > 60s)
- Detects long-running threads (30-60s)
- Detects blocked/waiting threads
- Runs AI analysis using LangGraph analyzer

### 3. **Alert** (If issues found)
- Creates alert file in `data/alerts/` for dashboard
- Sends formatted alert to Slack
- Includes recommendations and thread details

### 4. **Dashboard Sync** (Automatic)
- Dashboard reads alerts from `data/alerts/`
- Displays in Thread Monitor section
- Shows real-time status

## Monitoring Configuration

Edit `.env` file to configure:

```env
# Integration Server
WEBMETHODS_URL=http://localhost:5555
INTEGRATION_SERVER_PID=9584

# Slack Notifications
SLACK_WEBHOOK_URL=your_webhook_url_here

# Monitoring Settings
MONITOR_INTERVAL=60
HUNG_THREAD_THRESHOLD=60
```

## Troubleshooting

### Problem: "Access is denied" error
**Solution**: Must run as Administrator
- Right-click `start_monitoring_admin.bat`
- Select "Run as administrator"

### Problem: "Could not find Integration Server process"
**Solution**: Verify Integration Server is running
```bash
jps -l | findstr IntegrationServer
```

### Problem: No Slack alerts
**Solution**: Check Slack webhook URL in `.env`
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Problem: Dashboard not showing alerts
**Solution**: 
1. Check `data/alerts/` directory has JSON files
2. Refresh dashboard at http://localhost:8502
3. Check "Thread Monitor" section

## Manual Analysis

To analyze existing dumps without waiting:

```bash
# Analyze the latest dump
python analyze_collected_dump.py

# Analyze a specific dump
python analyze_collected_dump.py --dump-file data/thread_dumps/jstack_dump_20260505_210433.txt
```

## Quick Commands

```bash
# Start monitoring (requires admin)
start_monitoring_admin.bat

# Check monitoring status
python check_monitoring.py

# View latest dumps
dir data\thread_dumps\*.txt /O-D

# View alerts
dir data\alerts\*.json /O-D

# Open dashboard
# Already running at http://localhost:8502
```

## Expected Output

### Healthy System (No Issues)
```
[CYCLE 5] 2026-05-05 21:30:00
Collecting thread dump from PID 9584...
✅ Thread dump saved: jstack_dump_20260505_213000.txt
✅ Parsed 156 threads -> jstack_dump_20260505_213000.json
✅ No issues detected - system healthy

[WAITING] Next check in 60 seconds...
```

### System with Issues
```
[CYCLE 6] 2026-05-05 21:31:00
Collecting thread dump from PID 9584...
✅ Thread dump saved: jstack_dump_20260505_213100.txt
✅ Parsed 158 threads -> jstack_dump_20260505_213100.json

⚠️  ISSUES DETECTED:
   - Hung threads: 2
   - Long-running threads: 3
   - Blocked threads: 5

🔍 Running AI analysis...
✅ Analysis complete
📢 Sending alert to Slack...
✅ Alert sent successfully
💾 Alert saved: data/alerts/alert_20260505_213100_hung_thread.json

[WAITING] Next check in 60 seconds...
```

## Dashboard Access

The dashboard is already running at:
**http://localhost:8502**

Navigate to the **"Thread Monitor"** section to see:
- Active alerts
- Thread statistics
- Analysis results
- Recommendations

---

**Note**: Keep the monitoring terminal open and running. Do not close it or the monitoring will stop.