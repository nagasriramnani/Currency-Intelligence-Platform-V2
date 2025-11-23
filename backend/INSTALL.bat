@echo off
REM One-time installation script for Currency Intelligence Platform

echo ========================================
echo Currency Intelligence Platform
echo Installation Script
echo ========================================
echo.

echo Step 1: Creating conda environment...
call conda env create -f environment.yml

echo.
echo Step 2: Activating environment...
call conda activate currency-intelligence

echo.
echo Step 3: Installing Prophet from conda-forge (recommended)...
call conda install -c conda-forge prophet -y

echo.
echo Step 4: Fixing dependencies...
pip install numpy==1.24.3 --force-reinstall
pip install scikit-learn==1.3.2 --force-reinstall --no-build-isolation

echo.
echo Step 5: Setting up Slack webhook...
copy slack_config.env .env

echo.
echo ========================================
echo ✅ Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run: START.bat
echo 2. Wait 60-90 seconds for data to load
echo 3. Open: http://localhost:8000
echo.
pause


