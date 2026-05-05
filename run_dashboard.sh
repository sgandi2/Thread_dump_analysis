#!/bin/bash
# webMethods Thread Dump Analysis Dashboard Launcher
# Quick start script for Linux/Mac

echo "========================================"
echo "webMethods Thread Dump Analysis Dashboard"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "Python found: $(python3 --version)"
echo ""

# Check if streamlit is installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "Streamlit not found. Installing dependencies..."
    pip3 install streamlit plotly pandas
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo "Starting dashboard..."
echo ""
echo "Dashboard will open in your browser at http://localhost:8501"
echo "Press Ctrl+C to stop the dashboard"
echo ""

# Start the dashboard
streamlit run dashboard/app.py

# Made with Bob
