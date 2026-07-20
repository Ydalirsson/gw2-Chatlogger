from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from .paths import find_wine_prefix_logs
from .settings import Settings, ALL_CHANNELS
from .log_reader import ChatLogReader
from .session import SessionRecorder
from .formatting import format_html, CHANNEL_COLORS


class LiveTab(QtWidgets.QWidget):
    """Live monitor of incoming chat, plus the session-recording controls.

    The view always shows what arrives (the "control" window). Recording is a
    separate, user-driven action: it writes new messages to a chosen .txt while
    active and does not touch the live display.
    """

    def __init__(self, settings: Settings, recorder: SessionRecorder, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._recorder = recorder
        self._entries = []  # keep everything so filter toggles can re-render
        self._visible = set(settings.visible_channels())

        # -- session controls --------------------------------------------
        self.record_button = QtWidgets.QPushButton()
        self.record_button.clicked.connect(self._toggle_record)
        self.session_status = QtWidgets.QLabel()
        self.session_status.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        session_row = QtWidgets.QHBoxLayout()
        session_row.addWidget(self.record_button)
        session_row.addWidget(self.session_status, 1)

        # -- live view ----------------------------------------------------
        self.view = QtWidgets.QTextEdit()
        self.view.setReadOnly(True)
        self.view.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)

        self._channel_boxes = {}
        filter_row = QtWidgets.QHBoxLayout()
        filter_row.addWidget(QtWidgets.QLabel("Show:"))
        for channel in ALL_CHANNELS:
            box = QtWidgets.QCheckBox(channel)
            box.setChecked(channel in self._visible)
            box.stateChanged.connect(self._on_filter_changed)
            self._channel_boxes[channel] = box
            filter_row.addWidget(box)
        filter_row.addStretch(1)

        self.autoscroll = QtWidgets.QCheckBox("Autoscroll")
        self.autoscroll.setChecked(settings.autoscroll())
        self.autoscroll.stateChanged.connect(
            lambda: self._settings.set_autoscroll(self.autoscroll.isChecked())
        )
        clear_button = QtWidgets.QPushButton("Clear")
        clear_button.clicked.connect(self._clear)
        filter_row.addWidget(self.autoscroll)
        filter_row.addWidget(clear_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(session_row)
        layout.addLayout(filter_row)
        layout.addWidget(self.view, 1)

        self._recorder.changed.connect(self._update_session_status)
        self._update_session_status()

    # -- entries -----------------------------------------------------------

    def add_entry(self, entry: dict) -> None:
        self._entries.append(entry)
        if self._passes_filter(entry):
            self.view.append(format_html(entry))
            self._scroll_to_end_if_wanted()

    def _passes_filter(self, entry: dict) -> bool:
        channel = entry.get("channel", "Unknown")
        if channel not in CHANNEL_COLORS:
            channel = "Unknown"
        return channel in self._visible

    def _scroll_to_end_if_wanted(self) -> None:
        if self.autoscroll.isChecked():
            bar = self.view.verticalScrollBar()
            bar.setValue(bar.maximum())

    # -- session recording -------------------------------------------------

    def _toggle_record(self) -> None:
        if self._recorder.is_recording():
            self._stop_record()
        else:
            self._start_record()

    def _start_record(self) -> None:
        default_name = f"gw2chat_session_{datetime.now():%Y%m%d_%H%M%S}.txt"
        start = str(Path(self._settings.session_dir()) / default_name)
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Session speichern unter", start, "Textdatei (*.txt);;Alle Dateien (*)"
        )
        if not path:
            return
        if not Path(path).suffix:
            path += ".txt"
        if self._recorder.start(path):
            self._settings.set_session_dir(str(Path(path).parent))

    def _stop_record(self) -> None:
        count = self._recorder.count()
        path = self._recorder.path()
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle("Aufnahme beenden")
        box.setIcon(QtWidgets.QMessageBox.Question)
        box.setText("Aufnahme beenden?")
        box.setInformativeText(f"{count} Nachrichten aufgezeichnet\n{path}")
        keep = box.addButton("Behalten", QtWidgets.QMessageBox.AcceptRole)
        discard = box.addButton("Verwerfen", QtWidgets.QMessageBox.DestructiveRole)
        box.addButton("Abbrechen", QtWidgets.QMessageBox.RejectRole)
        box.setDefaultButton(keep)
        box.exec()
        clicked = box.clickedButton()
        if clicked not in (keep, discard):
            return  # cancelled — keep recording
        self._recorder.stop(discard=(clicked is discard))

    def _update_session_status(self) -> None:
        if self._recorder.is_recording():
            self.record_button.setText("■  Aufnahme beenden")
            self.record_button.setStyleSheet("font-weight: bold;")
            path = self._recorder.path()
            started = self._recorder.started_at()
            since = started.strftime("%H:%M") if started else "?"
            name = path.name if path else "?"
            self.session_status.setText(
                f'<span style="color:#e05555">●</span> Aufnahme → <b>{name}</b>'
                f" · {self._recorder.count()} Nachrichten · seit {since}"
            )
        else:
            self.record_button.setText("●  Aufnahme starten")
            self.record_button.setStyleSheet("")
            self.session_status.setText(
                '<span style="color:#888">Keine Aufnahme aktiv</span>'
            )

    # -- filters / clear ---------------------------------------------------

    def _on_filter_changed(self) -> None:
        self._visible = {ch for ch, box in self._channel_boxes.items() if box.isChecked()}
        self._settings.set_visible_channels(sorted(self._visible))
        self._rerender()

    def _rerender(self) -> None:
        self.view.clear()
        for entry in self._entries:
            if self._passes_filter(entry):
                self.view.append(format_html(entry))
        self._scroll_to_end_if_wanted()

    def _clear(self) -> None:
        self._entries = []
        self.view.clear()


class OptionsTab(QtWidgets.QWidget):
    path_changed = QtCore.Signal(str)

    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings

        self.path_edit = QtWidgets.QLineEdit(str(settings.log_path()))
        browse_button = QtWidgets.QPushButton("Browse")
        browse_button.clicked.connect(self._browse)
        find_button = QtWidgets.QPushButton("Find GW2 install")
        find_button.clicked.connect(self._find)

        path_row = QtWidgets.QHBoxLayout()
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_button)
        path_row.addWidget(find_button)

        form = QtWidgets.QFormLayout()
        form.addRow("Chat log file", path_row)

        help_text = QtWidgets.QLabel(
            "This viewer tails the log written by the arcdps 'gw2chatlogger' addon.\n"
            "Point it at 'gw2chatlogger.jsonl' next to arcdps (bin64, or your addon\n"
            "manager's addons folder). Coverage is party/squad chat only "
            "(unofficial_extras limitation)."
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #888;")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(help_text)
        layout.addStretch(1)

        self.path_edit.editingFinished.connect(self._commit_path)

    def _commit_path(self) -> None:
        path = self.path_edit.text().strip()
        if path:
            self.path_changed.emit(path)

    def _browse(self) -> None:
        start_dir = str(self._settings.log_path().parent)
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select chat log file", start_dir, "Chat log (*.jsonl);;All files (*)"
        )
        if path:
            self.path_edit.setText(path)
            self.path_changed.emit(path)

    def _find(self) -> None:
        found = find_wine_prefix_logs()
        if found:
            self.path_edit.setText(str(found[0]))
            self.path_changed.emit(str(found[0]))
            if len(found) > 1:
                others = "\n".join(str(p) for p in found)
                QtWidgets.QMessageBox.information(
                    self, "GW2 install", f"Found several log files:\n\n{others}\n\nUsing the first."
                )
        else:
            QtWidgets.QMessageBox.information(
                self,
                "GW2 install",
                "No 'gw2chatlogger.jsonl' found in the common GW2 install locations.\n"
                "Use Browse to select it manually (it sits next to arcdps).",
            )


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GW2 Chat Logger")

        self.settings = Settings()
        self.reader = ChatLogReader(self.settings.log_path())
        self.recorder = SessionRecorder(self)

        self.live_tab = LiveTab(self.settings, self.recorder)
        self.options_tab = OptionsTab(self.settings)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.live_tab, "Live")
        tabs.addTab(self.options_tab, "Options")
        self.setCentralWidget(tabs)

        self.status = self.statusBar()
        self._update_status()

        # Feed both the live view and (when active) the recorder.
        self.reader.entry_received.connect(self.live_tab.add_entry)
        self.reader.entry_received.connect(self.recorder.on_entry)
        self.reader.error.connect(self._on_reader_error)
        self.recorder.error.connect(self._on_reader_error)
        self.options_tab.path_changed.connect(self._on_path_changed)

        self.reader.start(from_beginning=True)

    def _on_path_changed(self, path: str) -> None:
        if self.recorder.is_recording():
            QtWidgets.QMessageBox.warning(
                self,
                "Aufnahme läuft",
                "Bitte beende erst die laufende Aufnahme, bevor du die Quelldatei "
                "wechselst — sonst würde die komplette neue Datei in die Aufnahme "
                "geschrieben.",
            )
            self.options_tab.path_edit.setText(str(self.reader.path() or ""))
            return
        self.settings.set_log_path(path)
        self.reader.set_path(path)
        self.live_tab._clear()
        self.reader.start(from_beginning=True)
        self._update_status()

    def _on_reader_error(self, message: str) -> None:
        self.status.showMessage(f"Reader error: {message}", 5000)

    def _update_status(self) -> None:
        path = self.reader.path()
        exists = path is not None and path.exists()
        state = "watching" if exists else "waiting for file"
        self.status.showMessage(f"{state}: {path}")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        # Never lose a running session: finalize (keep) it on exit.
        if self.recorder.is_recording():
            self.recorder.stop()
        self.reader.stop()
        super().closeEvent(event)
