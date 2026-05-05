@echo off
REM Quick Demo - Analyze Thread Dump
REM Usage: demo_analyze.bat YOUR_THREAD_DUMP.txt

echo ============================================================
echo  ThreadHeap Guardian - Demo Analysis
echo ============================================================
echo.

REM Check if file was provided
if "%~1"=="" (
    echo ERROR: Please provide a thread dump file
    echo.
    echo Usage: demo_analyze.bat YOUR_THREAD_DUMP.txt
    echo.
    echo Example: demo_analyze.bat C:\dumps\threaddump.txt
    echo.
    pause
    exit /b 1
)

set SOURCE_FILE=%~1
set DEST_DIR=data\thread_dumps
set DEST_FILE=%DEST_DIR%\%~nx1

REM Check if source file exists
if not exist "%SOURCE_FILE%" (
    echo ERROR: File not found: %SOURCE_FILE%
    echo.
    pause
    exit /b 1
)

REM Create destination directory
if not exist "%DEST_DIR%" mkdir "%DEST_DIR%"

REM Copy file
echo [1/3] Copying thread dump to project...
copy "%SOURCE_FILE%" "%DEST_FILE%"
if errorlevel 1 (
    echo ERROR: Failed to copy file
    pause
    exit /b 1
)
echo       Done: %DEST_FILE%
echo.

REM Analyze
echo [2/3] Analyzing thread dump...
python analyze_collected_dump.py --file "%DEST_FILE%"
if errorlevel 1 (
    echo ERROR: Analysis failed
    pause
    exit /b 1
)
echo.

REM Start dashboard
echo [3/3] Starting dashboard...
echo.
echo Dashboard will open at: http://localhost:8502
echo Press Ctrl+C to stop the dashboard
echo.
python -m streamlit run dashboard\app_enhanced.py --server.port 8502

pause

@REM Made with Bob
