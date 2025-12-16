@echo off
REM ===================================================================
REM Face Attendance System - Quick Start Script
REM Run this to start both backend and frontend
REM ===================================================================

cd /d "%~dp0"

echo.
echo ===================================================================
echo  Face Attendance System - Starting
echo ===================================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\pip install -r backend\requirements.txt
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Start backend in new window
echo Starting backend server...
start "FaceAttend Backend" cmd /k "cd backend && python app.py"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
echo Starting frontend dev server...
start "FaceAttend Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================================
echo  ✓ System Starting!
echo ===================================================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Logs:
echo  - Backend: Check "FaceAttend Backend" window
echo  - Frontend: Check "FaceAttend Frontend" window
echo.
echo To stop:
echo  1. Close both terminal windows, OR
echo  2. Run: taskkill /FI "WINDOWTITLE eq FaceAttend*" /F
echo.
echo ===================================================================
echo.

pause
