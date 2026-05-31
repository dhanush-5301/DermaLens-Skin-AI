"""
DermaLens AI - Quick Diagnostic
Run: python diagnose.py
This prints exactly what's missing and why the server won't start.
"""
import sys
import subprocess
import importlib
from pathlib import Path

ROOT = Path(__file__).parent
BACKEND = ROOT / "backend"

print("=" * 60)
print("  DermaLens AI — DIAGNOSTIC REPORT")
print("=" * 60)
print()

# Python version
print(f"Python version  : {sys.version}")
print(f"Python path     : {sys.executable}")
print()

# Required packages
packages = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "multipart": "python-multipart",
    "PIL": "pillow",
    "dotenv": "python-dotenv",
    "numpy": "numpy",
    "torch": "torch",
    "torchvision": "torchvision",
    "anthropic": "anthropic",
}

print("Package Status:")
missing = []
for imp, pip_name in packages.items():
    try:
        mod = importlib.import_module(imp)
        version = getattr(mod, "__version__", "installed")
        print(f"  ✓  {pip_name:<20} {version}")
    except ImportError:
        print(f"  ✗  {pip_name:<20} MISSING")
        missing.append(pip_name)

print()

# .env file
env_path = ROOT / ".env"
print("Environment:")
print(f"  .env file       : {'EXISTS' if env_path.exists() else 'MISSING'}")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "ANTHROPIC_API_KEY" in line and "sk-ant-xxx" not in line and "=" in line:
            key_val = line.split("=", 1)[1].strip()
            if key_val and not key_val.startswith("#"):
                print(f"  Anthropic key   : SET (starts with {key_val[:10]}...)")
            else:
                print(f"  Anthropic key   : NOT SET (blank)")
        elif "ANTHROPIC_API_KEY" in line:
            print(f"  Anthropic key   : PLACEHOLDER (sk-ant-xxx...)")

# Backend
print()
print("Backend:")
print(f"  backend/main.py : {'EXISTS' if (BACKEND/'main.py').exists() else 'MISSING'}")
print(f"  uploads dir     : {'EXISTS' if (ROOT/'uploads').exists() else 'will be created'}")
print(f"  models dir      : {'EXISTS' if (ROOT/'models').exists() else 'MISSING (will use ImageNet init)'}")

# Port check
print()
print("Network:")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', 8000))
sock.close()
if result == 0:
    print("  Port 8000       : ALREADY IN USE (server may already be running!)")
    print("  Try opening     : http://127.0.0.1:8000")
else:
    print("  Port 8000       : FREE (server not running yet)")

print()

# Summary
if missing:
    print("=" * 60)
    print("  ⚠  MISSING PACKAGES — Run this to fix:")
    print()
    torch_pkgs = [p for p in missing if p in ("torch", "torchvision")]
    other_pkgs = [p for p in missing if p not in ("torch", "torchvision")]
    if other_pkgs:
        print(f"  pip install {' '.join(other_pkgs)}")
    if torch_pkgs:
        print(f"  pip install {' '.join(torch_pkgs)} --index-url https://download.pytorch.org/whl/cpu")
    print("=" * 60)
else:
    print("=" * 60)
    print("  ✓  All packages installed. Start server with:")
    print()
    print("  cd backend")
    print("  python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload")
    print()
    print("  OR run:  python launch.py")
    print("=" * 60)

print()
input("Press Enter to exit...")
