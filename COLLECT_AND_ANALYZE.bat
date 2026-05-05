@echo off
REM Collect and Analyze Thread Dumps from webMethods
REM This script copies thread dumps from Integration Server and analyzes them

echo ============================================================
echo  Thread Dump Collection and Analysis
echo ============================================================
echo.

REM Default Integration Server diagnostics path
set DEFAULT_PATH=C:\SoftwareAG\IntegrationServer\instances\default\logs\diagnostics

REM Check if path was provided as argument
if "%~1"=="" (
    echo No path provided. Using default path:
    echo %DEFAULT_PATH%
    echo.
    echo To use a different path, run:
    echo   COLLECT_AND_ANALYZE.bat "C:\your\path\to\diagnostics"
    echo.
    set DIAG_PATH=%DEFAULT_PATH%
) else (
    set DIAG_PATH=%~1
)

REM Run the collection and analysis script
python collect_and_analyze.py --source "%DIAG_PATH%"

echo.
echo ============================================================
echo  Done!
echo ============================================================
echo.
pause

@REM Made with Bob
