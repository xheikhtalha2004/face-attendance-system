@echo off
echo Starting FaceAttend Pro...
echo.

REM Start backend in new window
start "FaceAttend Backend" cmd /k "cd backend && venv\Scripts\activate && python app.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
start "FaceAttend Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo Press any key to stop both servers...
pause >nul

REM Kill both windows
taskkill /FI "WINDOWTITLE eq FaceAttend Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq FaceAttend Frontend" /F >nul 2>&1
