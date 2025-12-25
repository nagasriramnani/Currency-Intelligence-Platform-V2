@echo off
REM ============================================================================
REM Sapphire Intelligence Platform - Startup Script for Windows
REM Version: 2.1.0
REM 
REM This script starts both backend (FastAPI) and frontend (Next.js) services
REM ============================================================================

echo.
echo ============================================================================
echo    SAPPHIRE INTELLIGENCE PLATFORM
echo    Currency Analytics + EIS Investment Scanner
echo ============================================================================
echo.

REM Initialize Conda (try multiple locations)
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
    echo [ERROR] Python is not installed. Please install Python 3.9 or higher.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed. Please install Node.js 18 or higher.
    pause
    exit /b 1
)

echo [OK] Python and Node.js found
echo.

REM ============================================================================
REM BACKEND SETUP
REM ============================================================================
echo [1/4] Setting up backend...
cd backend

REM Activate conda environment
echo       Activating conda environment: currency-intelligence
call conda activate currency-intelligence 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Conda environment not found!
    echo           Run: conda env create -f environment.yml
    pause
    exit /b 1
)

REM Check for .env file
if not exist ".env" (
    echo [WARNING] No .env file found in backend/
    echo           Please create backend/.env with your API keys
    echo.
    echo           Required keys:
    echo           - COMPANIES_HOUSE_API_KEY
    echo           - TAVILY_API_KEY
    echo           - HF_API_KEY
    echo           - GMAIL_ADDRESS
    echo           - GMAIL_APP_PASSWORD
    echo.
    pause
)

echo [OK] Backend ready
echo.

REM ============================================================================
REM FRONTEND SETUP
REM ============================================================================
echo [2/4] Setting up frontend...
cd ..\frontend

if not exist "node_modules" (
    echo       Installing frontend dependencies (first run)...
    call npm install --silent
)

echo [OK] Frontend ready
echo.

REM ============================================================================
REM START SERVICES
REM ============================================================================
echo [3/4] Starting backend API...
cd ..\backend
echo       URL: http://localhost:8000
echo       Docs: http://localhost:8000/docs
echo       (First run: Loading data takes 60-90 seconds)
start "Sapphire API" cmd /k "call conda activate currency-intelligence && python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to initialize
timeout /t 5 /nobreak >nul

echo [4/4] Starting frontend dashboard...
cd ..\frontend
echo       URL: http://localhost:3000
echo       EIS Scanner: http://localhost:3000/eis
start "Sapphire Dashboard" cmd /k npm run dev

echo.
echo ============================================================================
echo    SAPPHIRE INTELLIGENCE PLATFORM IS RUNNING!
echo ============================================================================
echo.
echo    Dashboard:    http://localhost:3000
echo    EIS Scanner:  http://localhost:3000/eis
echo    API:          http://localhost:8000
echo    API Docs:     http://localhost:8000/docs
echo.
echo    To stop services, close the terminal windows.
echo.
echo ============================================================================
echo.

pause
