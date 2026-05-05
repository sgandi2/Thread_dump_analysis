@echo off
REM Ollama Setup Script for Windows
REM This script downloads the Llama2 model and starts Ollama service

echo ========================================
echo Ollama AI Setup for Dashboard
echo ========================================
echo.

REM Check if Ollama is installed
ollama --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Ollama is not installed
    echo.
    echo Please install Ollama first:
    echo 1. Download from: https://ollama.ai/download
    echo 2. Run the installer
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
)

echo Ollama found!
echo.

echo Step 1: Pulling Llama2 model (this may take a few minutes, ~4GB download)...
echo.
ollama pull llama2

if errorlevel 1 (
    echo ERROR: Failed to pull Llama2 model
    pause
    exit /b 1
)

echo.
echo ========================================
echo Llama2 model downloaded successfully!
echo ========================================
echo.
echo Starting Ollama service...
echo The service will run in this window.
echo Keep this window open while using the AI chat.
echo.
echo Press Ctrl+C to stop Ollama service
echo.

REM Start Ollama service
ollama serve

@REM Made with Bob
