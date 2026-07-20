import re
from pathlib import Path
import sys
from typing import List

from PySide6 import QtCore


def resource_path(relative_path: str) -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / relative_path
    return Path(__file__).resolve().parent.parent / relative_path


def app_data_dir() -> Path:
    path = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.AppDataLocation)
    if path:
        return Path(path)
    return Path.home() / ".gw2-chatlogger"


# Name of the file the addon writes next to its DLL.
LOG_FILENAME = "gw2chatlogger.jsonl"

# Subfolders, relative to a GW2 install root, where arcdps (and thus our addon)
# may live: an addon manager's "addons" folder (e.g. Nexus/Raidcore), the classic
# "bin64", or directly next to Gw2-64.exe in the install root ("").
_LOG_SUBDIRS = ("addons", "bin64", "")


def _steam_roots() -> List[Path]:
    """Steam base dirs whose steamapps/libraryfolders.vdf we can parse."""
    home = Path.home()
    return [
        home / ".steam/steam",
        home / ".steam/root",
        home / ".local/share/Steam",
        home / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
        home / ".var/app/com.valvesoftware.Steam/data/Steam",
    ]


def _steam_library_paths() -> List[Path]:
    """All Steam library roots, discovered from libraryfolders.vdf.

    Steam records each library (including ones on other drives, e.g. /mnt/...) as a
    `"path"  "..."` entry; a full VDF parser is overkill, so we scan for those.
    """
    libs: List[Path] = []
    seen = set()
    for steam in _steam_roots():
        try:
            text = (steam / "steamapps" / "libraryfolders.vdf").read_text(
                encoding="utf-8", errors="ignore"
            )
        except OSError:
            continue
        for match in re.finditer(r'"path"\s+"([^"]+)"', text):
            # VDF escapes backslashes on Windows; collapse them. No-op on Linux.
            path = Path(match.group(1).replace("\\\\", "\\"))
            if path not in seen:
                seen.add(path)
                libs.append(path)
    return libs


def _gw2_install_roots() -> List[Path]:
    """Guild Wars 2 install roots whose addons/ or bin64/ holds arcdps and our addon.

    Steam libraries are discovered from libraryfolders.vdf (so installs on other
    drives are found); a few common non-Steam locations are appended as a fallback.
    Under Steam/Proton these live in steamapps/common/ and are directly readable
    from the Linux side.
    """
    home = Path.home()
    roots: List[Path] = []
    seen = set()

    def add(path: Path) -> None:
        if path not in seen:
            seen.add(path)
            roots.append(path)

    for lib in _steam_library_paths():
        add(lib / "steamapps" / "common" / "Guild Wars 2")

    for path in (
        home / ".steam/steam/steamapps/common/Guild Wars 2",
        home / ".local/share/Steam/steamapps/common/Guild Wars 2",
        home / ".var/app/com.valvesoftware.Steam/data/Steam/steamapps/common/Guild Wars 2",
        home / "Games/guild-wars-2/drive_c/Program Files/Guild Wars 2",
        home / ".wine/drive_c/Program Files/Guild Wars 2",
        Path("C:/Program Files/Guild Wars 2"),  # native Windows
    ):
        add(path)
    return roots


def candidate_log_paths() -> List[Path]:
    """All plausible locations of the addon log file (existing or not)."""
    paths: List[Path] = []
    seen = set()
    for root in _gw2_install_roots():
        for sub in _LOG_SUBDIRS:
            path = root / sub / LOG_FILENAME
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def find_wine_prefix_logs() -> List[Path]:
    """Existing addon log files across common GW2 install locations."""
    return [path for path in candidate_log_paths() if path.exists()]


def default_log_path() -> Path:
    """Best initial guess for the log path: an existing file if we can find one,
    otherwise a placeholder in the app data dir that the user can correct."""
    found = find_wine_prefix_logs()
    if found:
        return found[0]
    return app_data_dir() / LOG_FILENAME
