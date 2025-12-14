@echo off
REM Currency Intelligence Platform - Startup Script for Windows
REM This script starts both backend and frontend services

echo.
echo Starting Currency Intelligence Platform...
echo.

REM Initialize Conda (required for conda activate to work in batch scripts)
call "%USERPROFILE%\anaconda3\Scripts\activate.bat" 2>nul
if %errorlevel% neq 0 (
    call "%USERPROFILE%\miniconda3\Scripts\activate.bat" 2>nul
)
if %errorlevel% neq 0 (
    call "%CONDA_PREFIX%\..\Scripts\activate.bat" 2>nul
)

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed. Please install Python 3.9 or higher.
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed. Please install Node.js 18 or higher.
    exit /b 1
)

REM Backend setup
echo Setting up backend...
cd backend

echo Activating conda environment: currency-intelligence
call conda activate currency-intelligence 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Conda environment not found. Run INSTALL.bat first!
    echo    Or use: conda env create -f environment.yml
    pause
    exit /b 1
)

if not exist ".env" (
    echo Setting up Slack webhook...
    copy slack_config.env .env
)

echo Backend ready
echo.

REM Frontend setup
echo Setting up frontend...
cd ..\frontend

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install --silent
)

echo Frontend ready
echo.

REM Start services
echo Starting services...
echo.

REM Start backend
cd ..\backend
echo Starting backend API on http://localhost:8000
echo    (Fetching 25 years of data - first run takes 60-90 seconds)
start "Currency API" cmd /k "call conda activate currency-intelligence && python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend
timeout /t 3 /nobreak >nul

REM Start frontend
cd ..\frontend
echo Starting frontend dashboard on http://localhost:3000
start "Currency Dashboard" cmd /k npm run dev

echo.
echo Currency Intelligence Platform is running!
echo.
echo Dashboard: http://localhost:3000
echo API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo To stop services, close the terminal windows.
echo.

pause
