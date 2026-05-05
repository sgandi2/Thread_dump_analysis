@echo off
REM Setup Dashboard to Auto-Start with Windows
REM This creates a scheduled task that runs at system startup

echo ========================================
echo Setup Auto-Start for Dashboard
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

echo Creating scheduled task for auto-start...
echo.

REM Get current directory
set SCRIPT_DIR=%~dp0
set SCRIPT_PATH=%SCRIPT_DIR%start_dashboard_service.bat

REM Create scheduled task
schtasks /create /tn "ThreadDumpDashboard" /tr "\"%SCRIPT_PATH%\"" /sc onstart /ru SYSTEM /rl HIGHEST /f

if %errorLevel% equ 0 (
    echo.
    echo ========================================
    echo SUCCESS: Auto-start configured!
    echo ========================================
    echo.
    echo The dashboard will now start automatically when Windows boots.
    echo.
    echo Task Name: ThreadDumpDashboard
    echo Trigger: At system startup
    echo Script: %SCRIPT_PATH%
    echo.
    echo To remove auto-start, run: remove_auto_start.bat
    echo.
) else (
    echo.
    echo ERROR: Failed to create scheduled task
    echo Please check the error message above
    echo.
)

echo ========================================
pause

@REM Made with Bob
