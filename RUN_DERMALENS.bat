@echo off
title DermaLens AI — Server
color 0A
echo.
echo ================================================
echo   DermaLens AI — One-Click Server Launcher
echo ================================================
echo.

:: Go to the dermalens folder (where this bat file lives)
cd /d "%~dp0"

:: ── Try venv Python first, then system Python ──
set PYTHON=
if exist "%~dp0..\venv\Scripts\python.exe" (
    set PYTHON=%~dp0..\venv\Scripts\python.exe
    echo [OK] Using venv Python: %PYTHON%
) else if exist "%~dp0venv\Scripts\python.exe" (
    set PYTHON=%~dp0venv\Scripts\python.exe
    echo [OK] Using local venv Python: %PYTHON%
) else (
    set PYTHON=python
    echo [INFO] No venv found, using system Python
)

:: ── Check Python works ──
%PYTHON% --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo.
echo [1/3] Installing required packages (this may take a minute first time)...
%PYTHON% -m pip install --upgrade pip -q
%PYTHON% -m pip install fastapi "uvicorn[standard]" python-multipart pillow python-dotenv numpy torch torchvision --index-url https://download.pytorch.org/whl/cpu -q

echo.
echo [2/3] Verifying backend...
if not exist "%~dp0backend\main.py" (
    echo ERROR: backend\main.py not found!
    pause
    exit /b 1
)
echo [OK] backend\main.py found.

echo.
echo [3/3] Starting server on http://127.0.0.1:8000
echo       The browser will open automatically.
echo       Press CTRL+C to stop the server.
echo.
echo ================================================
echo.

:: Open browser after 3 seconds
start /b cmd /c "timeout /t 4 /nobreak >nul && start http://127.0.0.1:8000"

:: Start server from backend directory
cd /d "%~dp0backend"
%PYTHON% -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

echo.
echo Server stopped. Press any key to close.
pause
