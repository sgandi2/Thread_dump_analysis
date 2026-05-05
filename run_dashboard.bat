@echo off
REM webMethods Thread Dump Analysis Dashboard Launcher
REM Quick start script for Windows

echo ========================================
echo webMethods Thread Dump Analysis Dashboard
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo Python found!
echo.

REM Check if streamlit is installed
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
    echo Streamlit not found. Installing dependencies...
    pip install streamlit plotly pandas
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Starting dashboard...
echo.
echo Dashboard will open in your browser at http://localhost:8501
echo Press Ctrl+C to stop the dashboard
echo.

REM Start the dashboard
streamlit run dashboard/app.py

pause

@REM Made with Bob
