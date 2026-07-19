"""Tails the addon's JSON Lines chat log and emits one dict per new entry.

The addon appends one JSON object per line to a file next to its DLL. On Linux
that file lives inside the Wine/Proton prefix and is written by a Wine process, so
QFileSystemWatcher notifications are unreliable -- a periodic poll is the primary
mechanism and the watcher is only an accelerator.
"""
import json
from pathlib import Path

from PySide6 import QtCore


class ChatLogReader(QtCore.QObject):
    entry_received = QtCore.Signal(dict)
    error = QtCore.Signal(str)

    def __init__(self, path=None, poll_ms: int = 500, parent=None) -> None:
        super().__init__(parent)
        self._path = Path(path) if path else None
        self._offset = 0
        self._buffer = b""

        self._watcher = QtCore.QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._watcher.directoryChanged.connect(self._on_dir_changed)

        self._timer = QtCore.QTimer(self)
        self._timer.setInterval(poll_ms)
        self._timer.timeout.connect(self._poll)

    # -- configuration -----------------------------------------------------

    def path(self):
        return self._path

    def set_path(self, path) -> None:
        was_running = self._timer.isActive()
        self.stop()
        self._path = Path(path) if path else None
        self.reset()
        if was_running:
            self.start()

    def reset(self) -> None:
        self._offset = 0
        self._buffer = b""

    # -- lifecycle ---------------------------------------------------------

    def start(self, from_beginning: bool = True) -> None:
        if self._path is None:
            return
        if not from_beginning and self._path.exists():
            try:
                self._offset = self._path.stat().st_size
            except OSError:
                self._offset = 0
        self._install_watch()
        self._timer.start()
        self._poll()  # pick up whatever already exists

    def stop(self) -> None:
        self._timer.stop()
        for group in (self._watcher.files(), self._watcher.directories()):
            if group:
                self._watcher.removePaths(group)

    # -- watching ----------------------------------------------------------

    def _install_watch(self) -> None:
        if self._path is None:
            return
        # Watch the file when present; always watch the parent dir so we notice the
        # file being (re)created, which also drops the file watch.
        if self._path.exists() and str(self._path) not in self._watcher.files():
            self._watcher.addPath(str(self._path))
        parent = self._path.parent
        if parent.exists() and str(parent) not in self._watcher.directories():
            self._watcher.addPath(str(parent))

    def _on_file_changed(self, _path: str) -> None:
        self._poll()
        self._install_watch()  # re-arm if an editor/rotation replaced the file

    def _on_dir_changed(self, _path: str) -> None:
        self._install_watch()
        self._poll()

    # -- reading -----------------------------------------------------------

    def _poll(self) -> None:
        if self._path is None or not self._path.exists():
            return
        try:
            size = self._path.stat().st_size
            if size < self._offset:  # truncated or rotated
                self._offset = 0
                self._buffer = b""
            if size == self._offset:
                return
            with self._path.open("rb") as handle:
                handle.seek(self._offset)
                data = handle.read()
                self._offset = handle.tell()
        except OSError as exc:
            self.error.emit(str(exc))
            return
        self._buffer += data
        self._emit_complete_lines()

    def _emit_complete_lines(self) -> None:
        while b"\n" in self._buffer:
            raw, self._buffer = self._buffer.split(b"\n", 1)
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as exc:
                self.error.emit(f"parse error: {exc}")
                continue
            if isinstance(entry, dict):
                self.entry_received.emit(entry)
