from pathlib import Path
import sys
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


def default_log_dir() -> Path:
    docs = QtCore.QStandardPaths.writableLocation(QtCore.QStandardPaths.DocumentsLocation)
    if docs:
        return Path(docs) / "Guild Wars 2"
    return Path.home() / "Guild Wars 2"
