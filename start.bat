@echo off
REM Startup script for Route Master application (Windows)
REM Starts both backend and frontend servers

echo ========================================
echo Route Master - Startup Script (Windows)
echo ========================================
echo.

REM Check Python
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Python found
) else (
    echo ✗ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Node
echo Checking Node installation...
node --version >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Node found
) else (
    echo ✗ Node not found. Please install Node.js
    pause
    exit /b 1
)

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
npm install

REM Start backend
echo.
echo Starting Backend (Port 5000)...
start "Route Master Backend" python api.py

REM Wait a moment for backend to start
timeout /t 2 /nobreak

REM Start frontend
echo Starting Frontend (Port 5173)...
start "Route Master Frontend" cmd /k npm run dev

echo.
echo ========================================
echo Services Started Successfully!
echo ========================================
echo.
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:5000
echo API Docs: Check SETUP_AND_INTEGRATION.md
echo.
echo Both services are running in separate windows
echo Close the windows to stop the services
echo ========================================

pause
