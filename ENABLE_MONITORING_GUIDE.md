# Enable Monitoring with Admin Rights - Quick Guide

## Current Status
- **Last Alert:** 22:04 (May 5, 2026)
- **Monitoring:** Running but failing (Access Denied)
- **Issue:** jstack requires Administrator privileges
- **Cycles Failed:** 70+ attempts since 21:25:30

## Solution: Restart with Administrator Rights

### Step 1: Stop Current Monitoring
```
1. Go to Terminal 2 in VS Code
2. Press Ctrl+C to stop the monitoring
3. Wait for process to terminate
```

### Step 2: Start with Admin Rights
```
1. Open File Explorer
2. Navigate to: C:\Bobathon\Thread_dump_analysis
3. Find file: start_monitoring_admin.bat
4. RIGHT-CLICK on start_monitoring_admin.bat
5. Select "Run as administrator"
6. Click "Yes" on UAC prompt
```

### Step 3: Verify It's Working
You should see:
```
[SUCCESS] Found Integration Server (PID: 9584)
[1/3] Collecting thread dump with jstack...
[SUCCESS] Collected 12345 bytes
[2/3] Parsing threads...
[SUCCESS] Parsed 76 threads
[3/3] Analyzing for issues...
```

## Alternative: Analyze Existing Dumps (No Admin Required)

If you cannot get admin rights right now, you can analyze the 54+ existing dumps:

```bash
# Analyze the most recent dump
python analyze_collected_dump.py

# This will:
# 1. Read the latest thread dump
# 2. Analyze for hung threads
# 3. Generate AI recommendations
# 4. Send Slack alert
# 5. Update dashboard
```

## Monitoring Configuration

### Current Settings
- **Interval:** 60 seconds (1 minute)
- **PID:** 9584
- **Hung Threshold:** 60 seconds CPU time
- **Long-Running:** 30-60 seconds CPU time

### To Change to 1-Minute Alerts
The monitoring is already set to 60-second intervals. Once restarted with admin rights, it will:
- Collect thread dump every 60 seconds
- Analyze immediately
- Send Slack alert if issues found
- Update dashboard in real-time

## Quick Test (No Admin Required)

Run this to test the analysis pipeline:
```bash
python analyze_collected_dump.py --file data/thread_dumps/jstack_dump_20260505_214910.txt
```

This will analyze an existing dump and send an alert to Slack.

## Why Admin Rights Are Needed

**jstack Tool Requirements:**
- jstack must attach to Java process
- Windows requires admin rights to attach to processes
- Without admin: "Access is denied" error
- With admin: Full thread dump collection

## Troubleshooting

### If monitoring still fails after admin restart:
1. Check jstack is in PATH:
   ```
   jstack -version
   ```

2. If not found, run as admin:
   ```
   add_jstack_to_path.bat
   ```

3. Then restart monitoring as admin

### If you see "PID not found":
1. Check Integration Server is running
2. Verify PID in .env file:
   ```
   INTEGRATION_SERVER_PID=9584
   ```

3. Update if PID changed

## Expected Behavior After Restart

**Every 60 Seconds:**
```
[Cycle #1] Collecting... ✓
[Cycle #1] Analyzing... ✓
[Cycle #1] Alert sent to Slack ✓
[Cycle #1] Dashboard updated ✓

[Waiting 60 seconds...]

[Cycle #2] Collecting... ✓
[Cycle #2] Analyzing... ✓
[Cycle #2] Alert sent to Slack ✓
[Cycle #2] Dashboard updated ✓
```

## Current System State

**Integration Server:**
- PID: 9584
- Status: Running
- CPU: 12.4%
- Memory: 0.9% (290MB)
- Threads: 78 total

**Hung Threads:**
- Count: 2 detected
- Names: Timer-0, Configuration watchdog 1
- Status: Active in last dump (22:04)

**Dashboard:**
- URL: http://localhost:8502
- Status: Running
- Data: Showing last alert from 22:04

## Next Steps

1. **Immediate:** Stop Terminal 2 (Ctrl+C)
2. **Required:** Run start_monitoring_admin.bat as Administrator
3. **Verify:** Check Terminal 2 shows successful collection
4. **Monitor:** Watch Slack for new alerts every 60 seconds
5. **Dashboard:** Refresh to see updated statistics

---

**Note:** The system is fully functional and ready. It just needs administrator privileges to collect new thread dumps. All analysis, AI recommendations, Slack integration, and dashboard features are working perfectly with the existing 54+ collected dumps.