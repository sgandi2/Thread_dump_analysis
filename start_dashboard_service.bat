@echo off
REM Start Streamlit Dashboard as Background Service
REM This script runs the dashboard in headless mode

echo ========================================
echo Starting Thread Dump Analysis Dashboard
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Streamlit is not installed
    echo Installing streamlit...
    pip install streamlit
)

echo Starting dashboard on port 8502 in headless mode...
echo.

REM Start dashboard in background using pythonw (no console window)
start /B pythonw -m streamlit run dashboard/app_enhanced.py --server.port 8502 --server.headless true --server.address 0.0.0.0

REM Wait a moment for startup
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo Dashboard started successfully!
echo ========================================
echo.
echo Access the dashboard at:
echo   - Local: http://localhost:8502
echo   - Network: http://%COMPUTERNAME%:8502
echo.
echo The dashboard is running in the background.
echo To stop it, use: taskkill /F /IM pythonw.exe
echo Or use: stop_dashboard_service.bat
echo.
echo ========================================

REM Keep window open briefly
timeout /t 5

@REM Made with Bob
