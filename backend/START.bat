@echo off
REM Currency Intelligence Platform - Start Backend
REM This is the ONE script you need to run the backend

echo ========================================
echo Currency Intelligence Platform
echo Backend Server Startup
echo ========================================
echo.

REM Activate conda environment
call conda activate currency-intelligence

REM Copy Slack configuration if .env doesn't exist
if not exist .env (
    echo Setting up Slack webhook...
    copy slack_config.env .env
    echo ✅ Slack configured!
    echo.
)

REM Start the server
echo Starting backend server...
echo This will fetch 25 years of historical data (first run takes 60-90 seconds)
echo.
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload

pause


