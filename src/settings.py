from pathlib import Path
from PySide6 import QtCore
from .paths import default_log_dir


class Settings:
    def __init__(self) -> None:
        self._settings = QtCore.QSettings()

    def chat_area(self) -> dict:
        return {
            "x1": int(self._settings.value("chat_area/x1", 0)),
            "y1": int(self._settings.value("chat_area/y1", 0)),
            "x2": int(self._settings.value("chat_area/x2", 0)),
            "y2": int(self._settings.value("chat_area/y2", 0)),
        }

    def set_chat_area(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self._settings.setValue("chat_area/x1", int(x1))
        self._settings.setValue("chat_area/y1", int(y1))
        self._settings.setValue("chat_area/x2", int(x2))
        self._settings.setValue("chat_area/y2", int(y2))

    def screenshots_per_minute(self) -> int:
        return int(self._settings.value("recording/spm", 30))

    def set_screenshots_per_minute(self, spm: int) -> None:
        self._settings.setValue("recording/spm", int(spm))

    def languages(self) -> list:
        value = self._settings.value("ocr/languages")
        if value is None:
            return ["de", "en"]
        if isinstance(value, str):
            return [item for item in value.split(",") if item]
        return list(value)

    def set_languages(self, languages: list) -> None:
        self._settings.setValue("ocr/languages", list(languages))

    def log_dir(self) -> Path:
        value = self._settings.value("logging/dir")
        if value:
            return Path(value)
        return default_log_dir()

    def set_log_dir(self, path: str) -> None:
        self._settings.setValue("logging/dir", path)

    def active_window_title(self) -> str:
        return str(self._settings.value("window/title", "Guild Wars 2"))

    def set_active_window_title(self, title: str) -> None:
        self._settings.setValue("window/title", title)

    def only_when_active(self) -> bool:
        value = self._settings.value("window/only_when_active", True)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def set_only_when_active(self, enabled: bool) -> None:
        self._settings.setValue("window/only_when_active", bool(enabled))

    def use_gpu(self) -> bool:
        value = self._settings.value("ocr/use_gpu", False)
        if isinstance(value, str):
            return value.lower() in ("1", "true", "yes", "on")
        return bool(value)

    def set_use_gpu(self, enabled: bool) -> None:
        self._settings.setValue("ocr/use_gpu", bool(enabled))

    def ocr_quality(self) -> str:
        value = self._settings.value("ocr/quality", "balanced")
        return str(value).lower()

    def set_ocr_quality(self, value: str) -> None:
        self._settings.setValue("ocr/quality", str(value).lower())
