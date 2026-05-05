@echo off
echo ========================================
echo Starting Enhanced Thread Dump Dashboard
echo ========================================
echo.
echo Dashboard will be available at:
echo http://localhost:8501
echo.
echo Press Ctrl+C to stop the dashboard
echo ========================================
echo.

streamlit run dashboard/app_enhanced.py --server.port 8501

pause

@REM Made with Bob
