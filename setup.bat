@echo off
echo ========================================
echo FaceAttend Pro - Complete Setup
echo ========================================
echo.

REM Check if venv exists
if not exist venv\ (
    echo Creating Python virtual environment...
    python -m venv venv
)

echo.
echo [1/4] Activating virtual environment...
call venv\Scripts\activate

echo.
echo [2/4] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo [3/4] Installing Node.js dependencies...
cd ..\frontend
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install Node dependencies
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Start backend:  cd backend ^&^& python app.py
echo   2. Start frontend: cd frontend ^&^& npm run dev
echo.
echo Then open http://localhost:5173 in your browser
echo.
pause
