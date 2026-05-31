# Scripts Directory

Helper scripts and utilities for DermaLens AI.

## Windows Batch Scripts

### RUN_DERMALENS.bat
One-click starter for development. Automatically:
- Creates virtual environment (if needed)
- Installs dependencies
- Starts the FastAPI server

**Usage:** Double-click in Windows Explorer

### START_SERVER.bat
Starts the FastAPI development server.

### START_SERVER_ALT.bat
Alternative server startup script.

## Root Level Scripts

See the following in project root:
- `train.py` — Train MobileNetV2 on HAM10000
- `diagnose.py` — Standalone diagnosis utility
- `download_dataset.py` — Download HAM10000 dataset
- `launch.py` — Application launcher

## Future Scripts

- `benchmark.py` — Model performance benchmarking
- `evaluate.py` — Model evaluation on test set
- `optimize.py` — Model quantization & optimization
- `deploy.sh` — Automated deployment script
