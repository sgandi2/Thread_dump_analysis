@echo off
echo ============================================================
echo Thread Dump Monitoring - Starting
echo ============================================================
echo.
echo This script will monitor your Integration Server every 1 minute
echo and alert you if any hung threads are detected.
echo.
echo Press Ctrl+C to stop monitoring
echo.
echo ============================================================
echo.

python start_monitoring.py --interval 60

pause

@REM Made with Bob
