# Dashboard Service Setup Guide

## Running Dashboard as Background Service

The dashboard can run as a background service (non-interactive mode) that starts automatically with Windows.

---

## Quick Start

### Option 1: Start Dashboard Service Now
```bash
start_dashboard_service.bat
```
This starts the dashboard in headless mode (no console window).

### Option 2: Setup Auto-Start with Windows
```bash
# Run as Administrator
setup_auto_start.bat
```
This creates a Windows scheduled task that starts the dashboard automatically when Windows boots.

---

## Service Scripts

### 1. `start_dashboard_service.bat`
**Purpose**: Start dashboard as background service

**Features**:
- Runs in headless mode (no browser auto-open)
- No console window (uses `pythonw`)
- Accessible from network
- Runs on port 8502

**Usage**:
```bash
start_dashboard_service.bat
```

**Access**:
- Local: http://localhost:8502
- Network: http://YOUR_COMPUTER_NAME:8502

---

### 2. `stop_dashboard_service.bat`
**Purpose**: Stop the dashboard service

**Usage**:
```bash
stop_dashboard_service.bat
```

This kills all `pythonw.exe` processes running the dashboard.

---

### 3. `setup_auto_start.bat`
**Purpose**: Configure dashboard to start automatically with Windows

**Requirements**:
- Must run as Administrator
- Creates Windows scheduled task

**Usage**:
```bash
# Right-click and select "Run as Administrator"
setup_auto_start.bat
```

**What it does**:
- Creates scheduled task named "ThreadDumpDashboard"
- Triggers at system startup
- Runs with SYSTEM privileges
- Starts dashboard automatically

**Verify**:
```bash
# Check if task exists
schtasks /query /tn "ThreadDumpDashboard"
```

---

### 4. `remove_auto_start.bat`
**Purpose**: Remove auto-start configuration

**Requirements**:
- Must run as Administrator

**Usage**:
```bash
# Right-click and select "Run as Administrator"
remove_auto_start.bat
```

---

## Configuration Options

### Headless Mode
The dashboard runs with these Streamlit options:
```bash
--server.headless true
--server.address 0.0.0.0
--server.port 8502
```

**Benefits**:
- No browser auto-opens
- Accessible from network
- Runs in background
- No console window

### Network Access
By default, the dashboard is accessible from:
- **Localhost**: http://localhost:8502
- **Network**: http://YOUR_IP:8502

To restrict to localhost only, modify `start_dashboard_service.bat`:
```bash
# Change this line:
--server.address 0.0.0.0

# To:
--server.address localhost
```

---

## Monitoring Service Status

### Check if Dashboard is Running
```bash
# Windows
tasklist | findstr pythonw

# Or check the port
netstat -ano | findstr :8502
```

### View Dashboard Logs
Streamlit logs are stored in:
```
%USERPROFILE%\.streamlit\logs\
```

---

## Troubleshooting

### Dashboard Not Starting

**Problem**: Service fails to start

**Solutions**:
1. Check Python installation:
   ```bash
   python --version
   ```

2. Check Streamlit installation:
   ```bash
   python -c "import streamlit"
   ```

3. Install missing dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Check port availability:
   ```bash
   netstat -ano | findstr :8502
   ```

### Port Already in Use

**Problem**: Port 8502 is already in use

**Solutions**:
1. Stop existing service:
   ```bash
   stop_dashboard_service.bat
   ```

2. Or change port in `start_dashboard_service.bat`:
   ```bash
   --server.port 8503
   ```

### Auto-Start Not Working

**Problem**: Dashboard doesn't start with Windows

**Solutions**:
1. Verify scheduled task exists:
   ```bash
   schtasks /query /tn "ThreadDumpDashboard"
   ```

2. Check task status:
   ```bash
   schtasks /query /tn "ThreadDumpDashboard" /v /fo list
   ```

3. Run task manually:
   ```bash
   schtasks /run /tn "ThreadDumpDashboard"
   ```

4. Check task history in Task Scheduler:
   - Open Task Scheduler (taskschd.msc)
   - Find "ThreadDumpDashboard"
   - Check "History" tab

### Permission Issues

**Problem**: Access denied errors

**Solutions**:
1. Run scripts as Administrator
2. Check file permissions in project directory
3. Ensure Python has necessary permissions

---

## Advanced Configuration

### Running Multiple Dashboards

To run both dashboards (8501 and 8502):

**Dashboard 1 (Original)**:
```bash
start /B pythonw -m streamlit run dashboard/app.py --server.port 8501 --server.headless true
```

**Dashboard 2 (Enhanced)**:
```bash
start /B pythonw -m streamlit run dashboard/app_enhanced.py --server.port 8502 --server.headless true
```

### Custom Startup Script

Create `start_all_services.bat`:
```batch
@echo off
echo Starting all services...

REM Start Dashboard
call start_dashboard_service.bat

REM Start Monitoring
start /B python start_monitoring.py --interval 300

echo All services started!
pause
```

---

## Service Management

### Start All Services
```bash
# Dashboard
start_dashboard_service.bat

# Monitoring
python start_monitoring.py --interval 300
```

### Stop All Services
```bash
# Stop Dashboard
stop_dashboard_service.bat

# Stop Monitoring (Ctrl+C in monitoring window)
```

### Restart Dashboard
```bash
stop_dashboard_service.bat
timeout /t 2
start_dashboard_service.bat
```

---

## Production Deployment

### Recommended Setup

1. **Install as Windows Service**:
   - Use NSSM (Non-Sucking Service Manager)
   - Download: https://nssm.cc/download

2. **Configure NSSM**:
   ```bash
   nssm install ThreadDumpDashboard
   # Path: C:\Python\pythonw.exe
   # Arguments: -m streamlit run dashboard/app_enhanced.py --server.port 8502 --server.headless true
   # Startup directory: C:\Bobathon\Thread_dump_analysis
   ```

3. **Start Service**:
   ```bash
   nssm start ThreadDumpDashboard
   ```

### Security Considerations

1. **Firewall Rules**:
   ```bash
   # Allow port 8502
   netsh advfirewall firewall add rule name="Thread Dump Dashboard" dir=in action=allow protocol=TCP localport=8502
   ```

2. **Authentication**:
   - Consider adding authentication layer
   - Use reverse proxy (nginx/IIS)
   - Implement IP whitelisting

3. **HTTPS**:
   - Configure SSL certificate
   - Use reverse proxy for HTTPS

---

## Monitoring Dashboard Health

### Health Check Script

Create `check_dashboard_health.bat`:
```batch
@echo off
curl -s http://localhost:8502/_stcore/health > nul
if %errorLevel% equ 0 (
    echo Dashboard is healthy
) else (
    echo Dashboard is not responding
    echo Restarting...
    call stop_dashboard_service.bat
    timeout /t 2
    call start_dashboard_service.bat
)
```

### Scheduled Health Checks

Create scheduled task to run health check every 5 minutes:
```bash
schtasks /create /tn "DashboardHealthCheck" /tr "C:\path\to\check_dashboard_health.bat" /sc minute /mo 5
```

---

## Summary

### Quick Commands

| Action | Command |
|--------|---------|
| Start Service | `start_dashboard_service.bat` |
| Stop Service | `stop_dashboard_service.bat` |
| Setup Auto-Start | `setup_auto_start.bat` (as Admin) |
| Remove Auto-Start | `remove_auto_start.bat` (as Admin) |
| Check Status | `tasklist \| findstr pythonw` |
| Access Dashboard | http://localhost:8502 |

### Files Created

- `start_dashboard_service.bat` - Start dashboard service
- `stop_dashboard_service.bat` - Stop dashboard service
- `setup_auto_start.bat` - Configure auto-start
- `remove_auto_start.bat` - Remove auto-start

### Next Steps

1. Run `start_dashboard_service.bat` to start the dashboard
2. Access http://localhost:8502 to verify it's working
3. Run `setup_auto_start.bat` (as Admin) to enable auto-start
4. Reboot to test auto-start functionality

The dashboard will now run in non-interactive mode and start automatically with Windows!