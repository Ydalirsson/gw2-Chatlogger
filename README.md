# GW2 Chat Logger

Logs **Guild Wars 2 party/squad chat** as clean text via the
[arcdps](https://www.deltaconnected.com/arcdps/) **unofficial_extras** API — no
screenshots, no OCR. It has two parts:

1. **An arcdps addon** (`addon/`) that runs inside the game and appends every
   party/squad chat message to `gw2chatlogger.jsonl`.
2. **A PySide6 viewer** (`src/`) that tails that file and shows the chat live,
   colour-coded by channel. Runs natively on Windows and Linux.

> ### Coverage
> unofficial_extras only exposes **party/squad chat (+ the NPC channel)**.
> Map, whisper, guild and say chat are **not** available through this API — that is
> a hard limitation of the data source, not of this tool. If you need those
> channels, this approach cannot provide them.

## How it works

```
GW2 (Windows or Proton) → arcdps → unofficial_extras → addon (chat callback)
   → appends JSONL to  <GW2>/bin64/gw2chatlogger.jsonl
   → PySide6 viewer tails the file → live, colour-coded display
```

Because GW2 is a Windows game, the addon is **always a Windows DLL** (on Linux it
runs inside the Proton/Wine process). The viewer is plain Python and runs natively
on either OS.

## 1. Build & install the addon

Prerequisites in-game: **arcdps** and the **unofficial_extras** addon.

See [`addon/README.md`](addon/README.md) for details. In short, on Fedora:

```bash
sudo dnf install mingw64-gcc-c++ mingw64-binutils cmake
cd addon
cmake -B build -DCMAKE_TOOLCHAIN_FILE=toolchain-mingw64.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build          # -> build/arcdps_gw2chatlogger.dll
```

Copy `arcdps_gw2chatlogger.dll` into the GW2 `bin64` folder next to arcdps
(Windows: `…\Guild Wars 2\bin64\`; Linux/Proton: the same `bin64` inside your GW2
install, e.g. `~/.steam/steam/steamapps/common/Guild Wars 2/bin64/`).

## 2. Run the viewer

Only dependency is PySide6.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m src
```

In **Options**, set the path to `gw2chatlogger.jsonl` — the **Find GW2 install**
button probes the common Steam/Proton/Lutris locations for you. The **Live** tab
then shows chat as it arrives; toggle Party/Squad, autoscroll, or clear.

## Try it without the game

You do not need GW2 running to test the viewer:

```bash
# terminal 1 — the viewer, pointed at a scratch file
python -m src            # Options → Browse → /tmp/gw2chat.jsonl

# terminal 2 — fake the addon
python addon/tools/fake_writer.py /tmp/gw2chat.jsonl
```

Lines should appear live in the Live tab, colour-coded, and honour the channel
filters.

## Build a standalone viewer executable

```bash
pip install -r requirements-dev.txt
pyinstaller gw2chatlogger.spec   # -> dist/gw2chatlogger
```

## Notes for Linux / Proton

- The addon runs inside the Wine process but writes into the GW2 `bin64` folder,
  which lives under `steamapps/common/…` and is directly readable from Linux — the
  viewer reads it there without touching the Wine prefix.
- If **Find GW2 install** does not locate the file, point **Browse** at
  `<your GW2 install>/bin64/gw2chatlogger.jsonl` manually.
