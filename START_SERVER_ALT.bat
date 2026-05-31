@echo off
title DermaLens AI - Server Launcher
color 0A
echo.
echo ================================================
echo    DermaLens AI - Alternative Server Launcher
echo ================================================
echo.

REM ── Step 1: Find Python ──────────────────────────────────────────
echo [1/5] Locating Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found in PATH.
    echo Try: py -3 instead of python
    py -3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo FATAL: No Python found. Install from https://python.org
        pause
        exit /b 1
    )
    set PYTHON=py -3
) else (
    set PYTHON=python
)

%PYTHON% --version
echo Python found OK.
echo.

REM ── Step 2: Upgrade pip silently ─────────────────────────────────
echo [2/5] Upgrading pip (silent)...
%PYTHON% -m pip install --upgrade pip -q --no-warn-script-location
echo.

REM ── Step 3: Install core packages ────────────────────────────────
echo [3/5] Installing core packages (this may take a few mins first time)...
%PYTHON% -m pip install fastapi uvicorn[standard] python-multipart pillow python-dotenv numpy -q
if %errorlevel% neq 0 (
    echo ERROR: Failed installing core packages.
    pause
    exit /b 1
)
echo Core packages OK.
echo.

REM ── Step 4: Install PyTorch (CPU-only, lightweight) ──────────────
echo [4/5] Installing PyTorch (CPU-only)...
%PYTHON% -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu -q
if %errorlevel% neq 0 (
    echo WARNING: PyTorch install had issues. Trying default index...
    %PYTHON% -m pip install torch torchvision -q
)
echo PyTorch OK.
echo.

REM ── Step 5: Start Server ─────────────────────────────────────────
echo [5/5] Starting DermaLens server...
echo.
echo ================================================
echo   URL: http://127.0.0.1:8000
echo   Press CTRL+C to stop
echo ================================================
echo.

cd /d "%~dp0backend"

REM Open browser after 3 seconds
start "" timeout /t 3 /nobreak >nul && start "" "http://127.0.0.1:8000"

%PYTHON% -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload --log-level info

echo.
echo Server stopped.
pause
