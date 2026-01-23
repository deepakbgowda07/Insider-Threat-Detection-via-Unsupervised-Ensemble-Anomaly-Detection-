@echo off
REM Insider Threat Detection Dashboard - Startup Script
REM Run this to launch the dashboard locally

echo.
echo =============================================================
echo  INSIDER THREAT DETECTION DASHBOARD - STARTUP
echo =============================================================
echo.

cd /d "%~dp0"

echo Checking Python environment...
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Installing/verifying dependencies...
pip install -q streamlit pandas numpy matplotlib seaborn scikit-learn

echo.
echo =============================================================
echo Launching dashboard at http://localhost:8501
echo =============================================================
echo.
echo Press Ctrl+C to stop the server
echo.

streamlit run app.py --client.showErrorDetails=false

pause
