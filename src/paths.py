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


def _gw2_install_roots() -> List[Path]:
    """Common Guild Wars 2 install roots whose bin64/ holds arcdps and our addon.

    Under Steam/Proton the game lives in steamapps/common/, which is directly
    readable from the Linux side (the addon writes the log there, not deep inside
    the Wine prefix).
    """
    home = Path.home()
    return [
        home / ".steam/steam/steamapps/common/Guild Wars 2",
        home / ".local/share/Steam/steamapps/common/Guild Wars 2",
        home / ".var/app/com.valvesoftware.Steam/data/Steam/steamapps/common/Guild Wars 2",
        home / "Games/guild-wars-2/drive_c/Program Files/Guild Wars 2",
        home / ".wine/drive_c/Program Files/Guild Wars 2",
        Path("C:/Program Files/Guild Wars 2"),  # native Windows
    ]


def candidate_log_paths() -> List[Path]:
    """All plausible locations of the addon log file (existing or not)."""
    return [root / "bin64" / LOG_FILENAME for root in _gw2_install_roots()]


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
