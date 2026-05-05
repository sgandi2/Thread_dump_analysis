@echo off
REM Start monitoring with administrator privileges
REM This script must be run as Administrator

echo ============================================================
echo Thread Dump Monitoring - Administrator Mode
echo ============================================================
echo.
echo This script will start the monitoring system with elevated
echo privileges required for jstack to access Java processes.
echo.
echo Press Ctrl+C to stop monitoring at any time.
echo ============================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges
    echo.
) else (
    echo [ERROR] This script must be run as Administrator!
    echo.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Start monitoring
echo [INFO] Starting monitoring system...
echo.
python start_monitoring.py

pause

@REM Made with Bob
