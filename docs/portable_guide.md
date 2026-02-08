# Portable App & Installer Guide (Archived)

**Status**: Verified Working (Feb 2026)
**Goal**: Create a standalone `.exe` that works on any drive (`C:\`, `D:\`, etc.) without requiring Python.

## 1. Prerequisites
- **Python 3.12+**
- **PyInstaller**: `pip install pyinstaller`
- **Inno Setup**: Download from [jrsoftware.org](https://jrsoftware.org/isdl.php).

## 2. Path Handling Logic (Critical)
To make the app portable, the code must detect if it's running as a script or Frozen EXE.

**Code Pattern (`src/bootstrap.py` & `src/ingest_transcribe.py`):**
```python
import sys
import os

if getattr(sys, 'frozen', False):
    # If frozen, the executable is in a folder (e.g., dist/AI Video Engine)
    # We want valid paths relative to that folder
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # If running as script, go up from src/
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define portable assets
MODELS_DIR = os.path.join(BASE_DIR, "models")
TEMP_DIR = os.path.join(BASE_DIR, "temp")
```

## 3. PyInstaller Build (`build.spec`)
Run: `pyinstaller build.spec`

**Key Spec Config:**
- `datas`: Include `src`, `assets`, `launch_hidden.vbs`.
- `hiddenimports`: `flet`, `faster_whisper`, `engineio.async_drivers.threading`.

## 4. Inno Setup script (`setup_script.iss`)
- **DefaultDirName**: `{autopf}\AI Video Engine` (Program Files) or `{userdocs}`.
- **Flags**: `ignoreversion`, `recursesubdirs`.
- **Icons**: Can set distinct uninstall and app icons.

## 5. Deployment
1. Build the EXE: `python -m PyInstaller build.spec`
2. Compile ISS: Open `setup_script.iss` -> Compile.
3. Result: `AI_Video_Engine_Setup.exe`.
