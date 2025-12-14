# InsightFace Installation Instructions for Windows

## Problem
InsightFace requires compilation which fails on Windows without Visual Studio C++ build tools.

## Solution Options

### Option 1: Install Pre-built Wheel (Recommended)
Download pre-built wheel from: https://github.com/deepinsight/insightface/releases

Or use this pip command:
```bash
venv\Scripts\python.exe -m pip install insightface-0.7.3-cp311-cp311-win_amd64.whl
```

### Option 2: Install Build Tools
1. Install Visual Studio 2022 Build Tools
2. Select "Desktop development with C++"
3. Then: `venv\Scripts\pip install insightface`

### Option 3: Use Docker (Production)
```dockerfile
FROM python:3.11-slim
RUN pip install insightface
```

### Option 4: Test Without InsightFace
The backend will run in "test mode" without face recognition.
You can test all other endpoints (registration, enrollment, etc.)

## Current Status
Backend is fully implemented but face recognition endpoint will return mock data until InsightFace is installed.

## Next Steps
1. Try Option 1 (pre-built wheel)
2. If that fails, use Option 4 (test mode) for now
3. Recognition will work once InsightFace is successfully installed
