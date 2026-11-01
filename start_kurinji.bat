@echo off
title KURINJI Launcher
echo ====================================================
echo Starting KURINJI Speech Translation System...
echo ====================================================

:: Navigate to project root
cd /d "%~dp0"

:: Start Backend Uvicorn Server in background
echo Starting Backend API Server (Port 8000)...
start "KURINJI Backend" cmd /k ".\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Start Frontend Vite Dev Server in background
echo Starting Frontend Client (Port 5173)...
start "KURINJI Frontend" cmd /k "cd frontend && npm run dev"

:: Wait 3 seconds and open browser
timeout /t 3 /nobreak >nul
echo Opening KURINJI in browser...
start http://localhost:5173/

echo ====================================================
echo KURINJI is now running!
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo ====================================================
pause
