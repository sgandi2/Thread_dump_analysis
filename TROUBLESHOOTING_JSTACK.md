# jstack Access Denied - Troubleshooting Guide

## Problem

When running the monitoring system, you see this error:

```
[1/3] Collecting thread dump with jstack...
2026-05-05 20:12:05 - jstack_collector - ERROR - jstack failed: 9584: Access is denied

[FAILED] Could not collect thread dump
  Possible reasons:
  - Need administrator privileges
  - Process may have restarted
  - jstack not in PATH
```

## Root Cause

**jstack requires administrator/elevated privileges** to attach to Java processes on Windows. This is a security feature to prevent unauthorized access to running processes.

## Solutions

### Solution 1: Run as Administrator (Recommended)

#### Option A: Using the Batch Script

1. **Right-click** on [`start_monitoring_admin.bat`](start_monitoring_admin.bat:1)
2. Select **"Run as administrator"**
3. Click **"Yes"** when prompted by UAC (User Account Control)

The script will:
- Check for administrator privileges
- Activate virtual environment if present
- Start monitoring with proper permissions

#### Option B: Using PowerShell

1. **Right-click** on PowerShell
2. Select **"Run as administrator"**
3. Navigate to project directory:
   ```powershell
   cd C:\Bobathon\Thread_dump_analysis
   ```
4. Run monitoring:
   ```powershell
   python start_monitoring.py
   ```

#### Option C: Using Command Prompt

1. **Right-click** on Command Prompt
2. Select **"Run as administrator"**
3. Navigate to project directory:
   ```cmd
   cd C:\Bobathon\Thread_dump_analysis
   ```
4. Run monitoring:
   ```cmd
   python start_monitoring.py
   ```

### Solution 2: Run Integration Server with Same User

If you don't want to use administrator privileges:

1. **Stop Integration Server**
2. **Start Integration Server** using the same user account that will run the monitoring
3. Run monitoring script normally (no admin needed)

**Note**: This only works if both processes run under the same user account.

### Solution 3: Use Alternative Collection Method

If administrator access is not available, use the REST API method instead:

#### Update Configuration

Edit `.env` file:
```env
# Use REST API instead of jstack
COLLECTION_METHOD=rest_api
SERVER_URL=http://localhost:5555
SERVER_USERNAME=Administrator
SERVER_PASSWORD=manage
```

#### Modify Monitoring Script

The system can fall back to REST API collection if jstack fails. This is already implemented in the collector agent.

## Verification Steps

### 1. Check Administrator Privileges

Run this in your terminal:
```cmd
net session
```

**Expected Output (with admin)**:
```
There are no entries in the list.
```

**Expected Output (without admin)**:
```
System error 5 has occurred.
Access is denied.
```

### 2. Verify jstack is Working

Test jstack manually:
```cmd
jstack 9584
```

Replace `9584` with your Integration Server PID.

**Success**: You'll see thread dump output
**Failure**: "Access is denied" error

### 3. Find Integration Server PID

```cmd
jps -l
```

Look for line containing `IntegrationServer`:
```
9584 com.wm.app.b2b.server.IntegrationServer
```

The number (9584) is the PID.

## Common Issues and Fixes

### Issue 1: "jstack is not recognized"

**Problem**: jstack not in PATH

**Solution**:
1. Find Java installation:
   ```cmd
   where java
   ```
2. Add JDK bin directory to PATH:
   ```cmd
   set PATH=%PATH%;C:\Program Files\Java\jdk-11\bin
   ```
3. Verify:
   ```cmd
   jstack -version
   ```

### Issue 2: "Process may have restarted"

**Problem**: Integration Server PID changed

**Solution**:
1. Stop monitoring (Ctrl+C)
2. Restart monitoring - it will auto-detect new PID
3. Or manually find new PID:
   ```cmd
   jps -l | findstr IntegrationServer
   ```

### Issue 3: UAC Prompt Keeps Appearing

**Problem**: UAC prompts every time

**Solution**:
1. Create scheduled task to run with elevated privileges
2. Or temporarily disable UAC (not recommended for production)

### Issue 4: Still Getting Access Denied with Admin

**Problem**: Even with admin rights, access denied

**Possible Causes**:
1. **Antivirus blocking**: Temporarily disable antivirus
2. **Different user context**: Integration Server running as SYSTEM
3. **Security policy**: Group policy preventing process access

**Solution**:
1. Run Integration Server as current user
2. Or use REST API collection method (Solution 3 above)

## Alternative: REST API Collection

If jstack continues to fail, use the REST API method:

### Advantages
- No administrator privileges required
- Works across network
- More reliable in production
- No process attachment needed

### Disadvantages
- Requires Integration Server credentials
- May have less detailed thread information
- Depends on Integration Server being responsive

### Setup

1. **Update `.env`**:
   ```env
   SERVER_URL=http://localhost:5555
   SERVER_USERNAME=Administrator
   SERVER_PASSWORD=manage
   ```

2. **Test REST API access**:
   ```bash
   python -c "from agents.collector.collector_agent import ThreadDumpCollectorAgent; agent = ThreadDumpCollectorAgent(); result = agent.collect(); print(result)"
   ```

3. **Run monitoring**:
   ```bash
   python start_monitoring.py
   ```

The system will automatically use REST API if jstack fails.

## Best Practices

### For Development/Demo
- ✅ Use administrator privileges with jstack
- ✅ Run [`start_monitoring_admin.bat`](start_monitoring_admin.bat:1)
- ✅ More detailed thread information
- ✅ Better for troubleshooting

### For Production
- ✅ Use REST API collection
- ✅ No elevated privileges needed
- ✅ More secure
- ✅ Works across network
- ✅ Easier to automate

## Quick Reference

### Start Monitoring (Admin Mode)
```cmd
# Right-click and "Run as administrator"
start_monitoring_admin.bat
```

### Start Monitoring (REST API Mode)
```cmd
# No admin needed
python start_monitoring.py
```

### Check Current Privileges
```cmd
net session
```

### Find Integration Server PID
```cmd
jps -l | findstr IntegrationServer
```

### Test jstack Manually
```cmd
jstack <PID>
```

### Test REST API Access
```bash
curl -u Administrator:manage http://localhost:5555/invoke/wm.server/getThreadDumpString
```

## Summary

**The "Access is denied" error occurs because jstack needs administrator privileges to attach to Java processes.**

**Quick Fix**:
1. Right-click [`start_monitoring_admin.bat`](start_monitoring_admin.bat:1)
2. Select "Run as administrator"
3. Click "Yes" on UAC prompt

**Alternative**:
- Use REST API collection method (no admin needed)
- Configure in `.env` file
- Works reliably in production

For the demo, using administrator mode with jstack provides the most detailed thread information and best showcases the system's capabilities.