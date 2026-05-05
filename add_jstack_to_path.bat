@echo off
REM Add jstack to PATH for current session and permanently
REM This script must be run as Administrator

echo ============================================================
echo Add jstack to PATH
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

REM Find Java installation
echo [1/4] Finding Java installation...
for /f "tokens=*" %%i in ('where java 2^>nul') do set JAVA_PATH=%%i

if not defined JAVA_PATH (
    echo [ERROR] Java not found in PATH
    echo Please install JDK and ensure java is in PATH
    pause
    exit /b 1
)

echo [OK] Found Java: %JAVA_PATH%

REM Get JDK bin directory
for %%i in ("%JAVA_PATH%") do set JAVA_BIN=%%~dpi
echo [OK] Java bin directory: %JAVA_BIN%

REM Check if jstack exists
if exist "%JAVA_BIN%jstack.exe" (
    echo [OK] Found jstack.exe in Java bin directory
) else (
    echo [ERROR] jstack.exe not found in %JAVA_BIN%
    echo.
    echo This might be a JRE installation. You need JDK for jstack.
    echo Please install JDK from: https://www.oracle.com/java/technologies/downloads/
    pause
    exit /b 1
)

REM Add to PATH for current session
echo.
echo [2/4] Adding to PATH for current session...
set PATH=%JAVA_BIN%;%PATH%
echo [OK] Added to current session PATH

REM Add to system PATH permanently
echo.
echo [3/4] Adding to system PATH permanently...
setx /M PATH "%JAVA_BIN%;%PATH%" >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Added to system PATH permanently
) else (
    echo [WARNING] Could not add to system PATH permanently
    echo You may need to add it manually
)

REM Verify jstack is accessible
echo.
echo [4/4] Verifying jstack is accessible...
jstack -version >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] jstack is now accessible!
    echo.
    jstack -version
) else (
    echo [WARNING] jstack verification failed
    echo You may need to restart your terminal
)

echo.
echo ============================================================
echo SETUP COMPLETE
echo ============================================================
echo.
echo Next steps:
echo 1. Close this window
echo 2. Open a NEW terminal (to load updated PATH)
echo 3. Run: jstack -version
echo 4. If successful, run: start_monitoring_admin.bat
echo.
echo Note: You may need to restart your computer for the PATH
echo       changes to take effect system-wide.
echo ============================================================
echo.
pause

@REM Made with Bob
