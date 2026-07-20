"""Records incoming chat entries to a user-chosen plain-text transcript.

The recorder is deliberately independent of the game's state: it just writes
every entry it is handed while active. If GW2 crashes or the player switches
squad/party, entries simply pause and later resume — the transcript on disk is
always current because each line is flushed the moment it arrives, so a crash
(of the game or the viewer) can never lose more than nothing.

Format and destination are fixed by the user's choice: a clean .txt transcript,
its path picked per session. include_time / include_channel choose which fields
each line keeps. Ending a session offers keep-or-discard.
"""
import os
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore

from .formatting import format_text


class SessionRecorder(QtCore.QObject):
    changed = QtCore.Signal()  # start/stop/new-line -> refresh the UI
    error = QtCore.Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._path = None
        self._fh = None
        self._count = 0
        self._started_at = None
        self._include_time = True
        self._include_channel = True

    # -- state -------------------------------------------------------------

    def is_recording(self) -> bool:
        return self._fh is not None

    def path(self):
        return self._path

    def count(self) -> int:
        return self._count

    def started_at(self):
        return self._started_at

    # -- lifecycle ---------------------------------------------------------

    def start(self, path, include_time: bool = True, include_channel: bool = True) -> bool:
        """Open `path` for appending and begin recording. include_time/include_channel
        choose which fields the transcript keeps. Returns success."""
        self.stop()  # finalize any previous session first
        p = Path(path)
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            # Append, so pointing at an existing session file continues it rather
            # than silently wiping it.
            self._fh = p.open("a", encoding="utf-8", newline="\n")
        except OSError as exc:
            self._fh = None
            self.error.emit(f"Kann Session-Datei nicht öffnen: {exc}")
            return False

        self._include_time = include_time
        self._include_channel = include_channel
        self._path = p
        self._count = 0
        self._started_at = datetime.now()
        fields = ", ".join(
            label for label, on in (("Zeit", include_time), ("Kanal", include_channel)) if on
        ) or "nur Name + Text"
        self._write_raw(
            f"# GW2 Chat Logger — Session gestartet {self._started_at:%Y-%m-%d %H:%M:%S}"
            f" (Felder: {fields})\n"
        )
        self.changed.emit()
        return True

    def stop(self, discard: bool = False) -> None:
        """End the current session. `discard=True` deletes the file."""
        if self._fh is None:
            return
        if not discard:
            self._write_raw(
                f"# Session beendet {datetime.now():%Y-%m-%d %H:%M:%S}"
                f" — {self._count} Nachrichten\n"
            )
        try:
            self._fh.close()
        except OSError as exc:
            self.error.emit(str(exc))
        self._fh = None

        if discard and self._path is not None:
            try:
                os.remove(self._path)
            except OSError:
                pass
            self._path = None
        self.changed.emit()

    # -- feed --------------------------------------------------------------

    def on_entry(self, entry: dict) -> None:
        """Slot for ChatLogReader.entry_received; writes only while recording."""
        if self._fh is None:
            return
        line = format_text(entry, self._include_time, self._include_channel)
        if self._write_raw(line + "\n"):
            self._count += 1
            self.changed.emit()

    # -- internals ---------------------------------------------------------

    def _write_raw(self, s: str) -> bool:
        try:
            self._fh.write(s)
            self._fh.flush()  # survive a crash of the game or the viewer
            return True
        except OSError as exc:
            self.error.emit(f"Schreibfehler: {exc}")
            return False
