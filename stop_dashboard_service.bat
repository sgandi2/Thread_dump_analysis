@echo off
REM Stop Streamlit Dashboard Service

echo ========================================
echo Stopping Thread Dump Analysis Dashboard
echo ========================================
echo.

REM Find and kill streamlit processes
echo Looking for Streamlit processes...
tasklist /FI "IMAGENAME eq pythonw.exe" 2>NUL | find /I /N "pythonw.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Found Streamlit processes. Stopping...
    taskkill /F /IM pythonw.exe >nul 2>&1
    echo Dashboard stopped successfully!
) else (
    echo No Streamlit processes found.
)

echo.
echo ========================================
pause

@REM Made with Bob
