"""
DermaLens AI - Python Server Launcher
Run this with: python launch.py
This installs missing dependencies and starts the server automatically.
"""
import sys
import subprocess
import os
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"

REQUIRED_PACKAGES = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn[standard]"),
    ("multipart", "python-multipart"),
    ("PIL", "pillow"),
    ("dotenv", "python-dotenv"),
    ("numpy", "numpy"),
    ("torch", "torch --index-url https://download.pytorch.org/whl/cpu"),
    ("torchvision", "torchvision --index-url https://download.pytorch.org/whl/cpu"),
]

def pip_install(package_install_name: str):
    print(f"  Installing: {package_install_name.split()[0]}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", *package_install_name.split(), "-q", "--no-warn-script-location"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  WARNING: {result.stderr[:200]}")
    return result.returncode == 0

def check_import(import_name: str) -> bool:
    try:
        __import__(import_name)
        return True
    except ImportError:
        return False

print("=" * 55)
print("  DermaLens AI — Python Launcher")
print(f"  Python: {sys.version.split()[0]} | {sys.executable}")
print("=" * 55)
print()

# ── Install missing packages ───────────────────────────────────────
print("[1/3] Checking & installing dependencies...")
all_ok = True
for import_name, install_name in REQUIRED_PACKAGES:
    if not check_import(import_name):
        print(f"  Missing: {import_name}")
        ok = pip_install(install_name)
        if not ok:
            print(f"  FAILED to install {install_name}")
            all_ok = False
    else:
        print(f"  OK: {import_name}")

if not all_ok:
    print("\nSome packages failed. The server may not start correctly.")
    input("Press Enter to try anyway...")

print()

# ── Verify backend path ───────────────────────────────────────────
print(f"[2/3] Backend path: {BACKEND}")
if not (BACKEND / "main.py").exists():
    print(f"  ERROR: main.py not found in {BACKEND}")
    input("Press Enter to exit.")
    sys.exit(1)
print("  main.py found OK")
print()

# ── Start server ──────────────────────────────────────────────────
print("[3/3] Starting uvicorn server on http://127.0.0.1:8000 ...")
print("      Press CTRL+C to stop.")
print()

os.chdir(str(BACKEND))

# Open browser after a short delay in background
def open_browser():
    time.sleep(3)
    print("  Opening browser: http://127.0.0.1:8000")
    webbrowser.open("http://127.0.0.1:8000")

import threading
browser_thread = threading.Thread(target=open_browser, daemon=True)
browser_thread.start()

# Start uvicorn
try:
    subprocess.run(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", "127.0.0.1", "--port", "8000",
         "--reload", "--log-level", "info"],
        cwd=str(BACKEND)
    )
except KeyboardInterrupt:
    print("\nServer stopped by user.")
except Exception as e:
    print(f"\nERROR starting server: {e}")
    input("Press Enter to exit.")
