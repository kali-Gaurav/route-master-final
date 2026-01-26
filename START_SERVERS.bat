@echo off
REM Startup script for Route Master - Frontend + Backend
REM This script starts both the Flask backend and Vite frontend

setlocal enabledelayedexpansion

cls
echo ================================================================================
echo  ROUTE MASTER - STARTUP SCRIPT
echo ================================================================================
echo.
echo This script will start both servers:
echo   1. Flask Backend  (Python)   - http://localhost:5000
echo   2. Vite Frontend  (Node.js) - http://localhost:5173
echo.
echo.IMPORTANT: A Python window and a Node.js window will open.
echo Keep BOTH windows open for the application to work!
echo.
echo ================================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://www.nodejs.org/
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not installed
    echo npm should come with Node.js
    pause
    exit /b 1
)

echo [OK] Python, Node.js, and npm are installed
echo.

REM Install backend dependencies if needed
if not exist ".venv" (
    echo [NOTICE] Virtual environment not found
    echo Creating Python virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Could not activate virtual environment
    pause
    exit /b 1
)

echo [OK] Python virtual environment activated
echo.

REM Install Python dependencies
echo [STEP 1/3] Installing Python dependencies...
pip install -q -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo WARNING: Could not install Python dependencies
    echo Trying to continue anyway...
) else (
    echo [OK] Python dependencies installed
)

REM Install Node dependencies
echo [STEP 2/3] Installing Node dependencies...
call npm install --silent >nul 2>&1
if errorlevel 1 (
    echo WARNING: Could not install Node dependencies
    echo Trying to continue anyway...
) else (
    echo [OK] Node dependencies installed
)

echo.
echo ================================================================================
echo [STEP 3/3] Starting servers...
echo ================================================================================
echo.

REM Start Flask backend in a new window
echo Starting Flask Backend...
start "Route Master - Flask Backend" python api.py
timeout /t 3 /nobreak

REM Start Vite frontend in a new window
echo Starting Vite Frontend...
start "Route Master - Vite Frontend" cmd /k "npm run dev"

echo.
echo ================================================================================
echo SERVERS STARTING...
echo ================================================================================
echo.
echo Please wait for both windows to fully start.
echo.
echo Frontend URL:  http://localhost:5173
echo Backend URL:   http://localhost:5000/api/health
echo.
echo You can close this window. The servers will continue running.
echo To stop the servers, close the backend and frontend windows.
echo.
pause
