from pathlib import Path
from typing import List

from PySide6 import QtCore

from .paths import default_log_path


ALL_CHANNELS = ["Party", "Squad", "Unknown"]


def _to_bool(value, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)


class Settings:
    def __init__(self) -> None:
        self._settings = QtCore.QSettings()

    def log_path(self) -> Path:
        value = self._settings.value("log/path")
        if value:
            return Path(value)
        return default_log_path()

    def set_log_path(self, path: str) -> None:
        self._settings.setValue("log/path", str(path))

    def autoscroll(self) -> bool:
        return _to_bool(self._settings.value("view/autoscroll", True), True)

    def set_autoscroll(self, enabled: bool) -> None:
        self._settings.setValue("view/autoscroll", bool(enabled))

    def visible_channels(self) -> List[str]:
        value = self._settings.value("view/channels")
        if value is None:
            return list(ALL_CHANNELS)
        if isinstance(value, str):
            channels = [item for item in value.split(",") if item]
        else:
            channels = list(value)
        return channels or list(ALL_CHANNELS)

    def set_visible_channels(self, channels: List[str]) -> None:
        self._settings.setValue("view/channels", list(channels))
