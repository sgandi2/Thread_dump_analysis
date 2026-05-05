@echo off
REM Remove Dashboard Auto-Start from Windows

echo ========================================
echo Remove Auto-Start for Dashboard
echo ========================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires administrator privileges
    echo Please run as Administrator
    pause
    exit /b 1
)

echo Removing scheduled task...
echo.

REM Delete scheduled task
schtasks /delete /tn "ThreadDumpDashboard" /f

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: Auto-start removed!
    echo ========================================
    echo.
    echo The dashboard will no longer start automatically.
    echo You can still start it manually using start_dashboard_service.bat
    echo.
) else (
    echo.
    echo Note: Task may not exist or already removed
    echo.
)

echo ========================================
pause

@REM Made with Bob
