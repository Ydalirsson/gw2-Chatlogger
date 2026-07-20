# GW2 Chat Logger

Logs **Guild Wars 2 party/squad chat** as clean, readable text — via the
[arcdps](https://www.deltaconnected.com/arcdps/) **unofficial_extras** API, with no
screenshots and no OCR.

## Overview

The tool has two parts that work together:

- **In-game addon** — `arcdps_gw2chatlogger.dll`, loaded by arcdps. It subscribes to
  **unofficial_extras'** chat callback and appends every party/squad message to a
  `gw2chatlogger.jsonl` buffer next to itself.
- **Desktop viewer** — reads that buffer and shows the chat **live**, colour-coded by
  channel, with per-channel filters. At any point you can **record a session** to a
  clean `.txt` file of your choice (you decide whether the timestamp and channel are
  written). Runs natively on Windows and Linux; grab it from
  **[Releases](../../releases)** — no Python required.

```text
GW2  →  arcdps  →  unofficial_extras  →  arcdps_gw2chatlogger.dll
                                              │  appends
                                              ▼
                                    gw2chatlogger.jsonl   (volatile buffer)
                                              │  tailed by
                                              ▼
                               viewer   →   live view  +  saved .txt session
```

> **Coverage:** unofficial_extras only exposes **party/squad chat (+ the NPC
> channel)**. Map, whisper, guild and say chat are **not** available through this API
> — a hard limit of the data source, not of this tool.

> **`gw2chatlogger.jsonl` is a volatile scratch buffer, not your saved log.** To keep
> a readable transcript, record a session in the viewer (it writes a `.txt` wherever
> you choose).

## Install (for players)

Three pieces need to be in place. The first two come from the GW2 addon community and
are **required**; the third is this tool.

### 1. arcdps + unofficial_extras — required

- **[arcdps](https://www.deltaconnected.com/arcdps/)** — the addon platform.
- **[unofficial_extras](https://github.com/Krappa322/arcdps_unofficial_extras_releases)**
  — the extension that exposes party/squad chat. **Without it, this tool receives
  nothing.**

**Recommended: the [Nexus / Raidcore](https://raidcore.gg/gw2/nexus) addon manager.**
Install Nexus once, then install **arcdps** and **Unofficial Extras** from its
in-game addon library (one click each, with automatic updates). This is by far the
easiest route — especially on **Linux/Proton**, where Nexus also handles the DirectX
proxy chainloading for you.

(You can also install arcdps and unofficial_extras manually from the links above.)

### 2. The chatlogger addon — which folder it goes in

> **Put `arcdps_gw2chatlogger.dll` in your GW2 addon folder, right next to arcdps.**

| Your setup | Folder |
|------------|--------|
| **Nexus / addon manager** | `…\Guild Wars 2\addons\` |
| **Classic arcdps** | `…\Guild Wars 2\bin64\` |
| **Linux / Proton (Steam)** | the same folder inside your install, e.g. `~/.steam/steam/steamapps/common/Guild Wars 2/addons/` |

arcdps automatically loads any `arcdps_*.dll` in that folder. Launch GW2, join a party
or squad, and `gw2chatlogger.jsonl` appears right next to the DLL.

> Don't have the DLL yet? Build it from `addon/` — see **Building (for developers)**.

### 3. The viewer

Download the standalone build from **[Releases](../../releases)** (no Python needed):

| Platform | File |
|----------|------|
| Windows | `gw2chatlogger.exe` |
| Linux (portable) | `gw2chatlogger-x86_64.AppImage` |
| Linux (single binary) | `gw2chatlogger` |

Run it. It auto-detects `gw2chatlogger.jsonl` across your Steam libraries; if it
can't, open **Options** and **Browse** to the file next to the DLL. The **Live** tab
shows chat as it arrives; the record button saves a session to a `.txt` of your
choice.

> **Linux AppImage:** `chmod +x gw2chatlogger-x86_64.AppImage && ./gw2chatlogger-x86_64.AppImage`.
> If you see `libfuse.so.2 not found` (e.g. on Fedora), install FUSE 2 with
> `sudo dnf install fuse`, or run it with `--appimage-extract-and-run`.

## Building (for developers)

### The addon DLL

The addon is **always a Windows DLL** (on Linux it runs inside the Proton/Wine
process). Cross-compile it on Linux with mingw-w64:

```bash
# Fedora
sudo dnf install mingw64-gcc-c++ mingw64-binutils cmake

cd addon
cmake -B build -DCMAKE_TOOLCHAIN_FILE=toolchain-mingw64.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build          # -> build/arcdps_gw2chatlogger.dll
```

On Windows, open `addon/CMakeLists.txt` with MSVC/CMake and build a Release DLL — no
code changes needed. Details: [`addon/README.md`](addon/README.md).

### The viewer from source

Only dependency is PySide6:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src
```

### Try it without the game

```bash
# terminal 1 — the viewer, pointed at a scratch file (Options → Browse)
python -m src

# terminal 2 — fake the addon
python addon/tools/fake_writer.py /tmp/gw2chat.jsonl
```

### Standalone builds

```bash
pip install -r requirements-dev.txt
pyinstaller gw2chatlogger.spec                        # -> dist/gw2chatlogger[.exe]
PYTHON=.venv/bin/python packaging/build-appimage.sh   # -> dist/gw2chatlogger-x86_64.AppImage
```

The Windows `.exe`, the Linux binary and the AppImage are also built automatically by
GitHub Actions (`.github/workflows/build.yml`) — run it from the Actions tab, or push
a `v*` tag to attach all three to a GitHub Release.
```
