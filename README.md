# GW2 Chat Logger (Python)

## About
This is a Python rewrite of the GW2 Chat Logger. It captures the Guild Wars 2 chat area, stores images per session, and runs offline OCR with EasyOCR when you process a session folder. The UI is built with PySide6.

## Features
- Record, stop, and capture screenshots from a selected chat box area
- Store images per session folder
- Process a session folder with OCR and de-duplication of recent lines
- Options for capture area, speed, languages, and session base folder
- Offline OCR (local models)

## Requirements
- Linux (tested conceptually; Wayland may restrict screen capture)
- Python 3.10 to 3.12 recommended
- System packages for PySide6 and OpenGL if needed by your distro

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If you do not have CPU wheels for PyTorch, follow the official PyTorch install instructions for your distro.

## Run
```bash
python -m src
```

## Dev: Auto-Restart (Hot Reload)
Because this is a PySide GUI app, true hot-reload isn't reliable. The best option is auto-restart on file changes.

### Option A: watchfiles (recommended)
```bash
pip install watchfiles
python -m watchfiles "python -m src" src
```

### Option B: watchdog
```bash
pip install watchdog
watchmedo auto-restart --directory=src --pattern="*.py" --recursive -- python -m src
```

## How to use
### Control tab
- Record: start continuous capture (screenshots only)
- Stop: end capture
- Try: run a single capture and show OCR output
- Set Chat Box Area: draw a rectangle on the primary screen
- New Session Folder: create a new session folder
- Initialize OCR: downloads and prepares EasyOCR models (first run can take a while)

### Logger View tab
- Shows OCR output from Try and capture status messages

### Options tab
- Chat area X1/Y1/X2/Y2
- Screenshots per minute
- Languages (German, English)
- Session base folder
- Use GPU (if available) for OCR
- OCR quality (Fast / Balanced / Accurate)
- Active window title and optional active-window check

### Session OCR tab
- Select a session folder and run OCR on all images
- Outputs `chatlog.txt` inside the session folder

## OCR models and offline mode
EasyOCR downloads model files on first use and stores them locally. To stay offline after that, pre-download the models once while online. The models are stored in the app data directory under `models/`.

## Build with PyInstaller
Install build tools:
```bash
pip install -r requirements-dev.txt
```

Build:
```bash
pyinstaller gw2chatlogger.spec
```

The executable is created in `dist/`. If you want to bundle pre-downloaded EasyOCR models, copy the `models/` folder next to the spec file before running PyInstaller.

## Notes for Linux
- Active window detection relies on `pywinctl`. If it does not work on your desktop environment, disable the active window check in Options.
- Screen capture might require X11 permissions. On Wayland, use an X11 session or disable sandbox restrictions.

## Legacy sources
The original C++/Qt sources are still in `gw2chatlogger/` but are no longer used by the Python version.
