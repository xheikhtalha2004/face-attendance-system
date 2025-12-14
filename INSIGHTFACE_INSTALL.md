# InsightFace Installation (Windows, confirmed working)

These steps are the exact recipe used to install `insightface==0.7.3` on Windows 11 (Python 3.11) in the root `venv`.

## 1) Install C++ build tools (required)
Use Winget to add the Visual Studio 2022 Build Tools with the VC++ workload:
```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools -e --source winget ^
  --accept-package-agreements --accept-source-agreements ^
  --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --quiet --norestart"
```

## 2) Activate venv and upgrade pip
```powershell
.\venv\Scripts\activate
python -m pip install --upgrade pip
```

## 3) Install InsightFace with pinned deps
We compiled from source (no prebuilt wheel for cp311 on Windows was available). The following set works together and keeps pandas happy:
```powershell
python -m pip install insightface==0.7.3
python -m pip install --force-reinstall numpy==1.26.4
python -m pip install --force-reinstall scikit-learn==1.3.2 --no-deps
python -m pip install --force-reinstall opencv-python-headless==4.8.1.78 --no-deps
python -m pip install onnx==1.20.0
```

> Shortcut: `pip install -r backend/requirements.txt` now pins these versions.

## 4) Verify
```powershell
python - <<'PY'
import insightface
print("insightface version:", insightface.__version__)
PY
```
Expected: `insightface version: 0.7.3`

## Notes
- This installs models at first run (~500MB) under `~/.insightface/models/`.
- If you see numpy/pandas/opencv conflicts, re-run the pinned commands above.
- For production containers, you can still use: `FROM python:3.11-slim` + `pip install insightface`.
