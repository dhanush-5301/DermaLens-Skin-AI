@echo off
title DermaLens AI Backend Server
color 0A
echo.
echo ============================================
echo   DermaLens AI - Starting Backend Server
echo ============================================
echo.

cd /d "%~dp0backend"

echo Checking Python and dependencies...
python --version
if errorlevel 1 (
    echo.
    echo ERROR: Python not found! Please install Python 3.8+
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo Installing/checking required packages...
pip install uvicorn fastapi torch torchvision pillow python-dotenv anthropic numpy -q

echo.
echo ============================================
echo   Server starting on http://127.0.0.1:8000
echo   Open this URL in your browser!
echo   Press CTRL+C to stop the server
echo ============================================
echo.

uvicorn main:app --host 127.0.0.1 --port 8000 --reload

echo.
echo Server stopped. Press any key to close.
pause
