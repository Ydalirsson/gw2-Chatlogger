# GW2 Chat Logger — arcdps addon

An [arcdps](https://www.deltaconnected.com/arcdps/) addon that subscribes to the
[unofficial_extras](https://github.com/Krappa322/arcdps_unofficial_extras_releases)
chat callback and appends every **party/squad** chat message to
`gw2chatlogger.jsonl` (one JSON object per line) next to the DLL. The PySide6 app in
the repo root tails that file.

> **Coverage:** unofficial_extras only exposes party/squad (+ NPC) chat. Map,
> whisper, guild and say chat are **not** available through this API.

## Build (cross-compile on Linux with mingw-w64)

The addon is always a Windows DLL — on Linux it runs inside the Proton/Wine process.

```bash
# Fedora:
sudo dnf install mingw64-gcc-c++ mingw64-binutils cmake

cd addon
cmake -B build -DCMAKE_TOOLCHAIN_FILE=toolchain-mingw64.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build
# -> build/arcdps_gw2chatlogger.dll
```

Verify the three required exports are present:

```bash
x86_64-w64-mingw32-objdump -p build/arcdps_gw2chatlogger.dll \
  | grep -iE 'get_init_addr|get_release_addr|arcdps_unofficial_extras_subscriber_init'
```

On Windows you can instead open `CMakeLists.txt` with MSVC/CMake and build a
`Release` DLL; no code changes needed.

## Install

Requires **arcdps** and the **unofficial_extras** addon to already be installed.

- Copy `arcdps_gw2chatlogger.dll` into the GW2 `bin64` folder, next to arcdps.
  - **Windows:** `…\Guild Wars 2\bin64\`
  - **Linux/Proton:** the same `bin64` inside your GW2 install (e.g.
    `~/.steam/steam/steamapps/common/Guild Wars 2/bin64/`). arcdps itself is the
    chainloaded `d3d11.dll` there.
- Launch GW2, join a party or squad. `gw2chatlogger.jsonl` appears in `bin64`.
- Point the viewer at that file (its **Find GW2 install** button probes the common
  locations).

## Files

- `include/arcdps.h` — minimal arcdps `arcdps_exports` interface.
- `include/extras_chat_api.h` — minimal, ABI-exact transcription of the
  unofficial_extras chat structs actually used.
- `src/main.cpp` — the addon: registration, chat callback, JSONL writer.
- `tools/fake_writer.py` — writes sample JSONL to test the viewer without the game.
