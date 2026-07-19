import html

from PySide6 import QtCore, QtGui, QtWidgets

from .paths import find_wine_prefix_logs
from .settings import Settings, ALL_CHANNELS
from .log_reader import ChatLogReader


CHANNEL_COLORS = {
    "Party": "#4aa3ff",
    "Squad": "#3fbf6f",
    "Unknown": "#999999",
}
TIME_COLOR = "#888888"
BROADCAST_COLOR = "#f0a030"


def _time_hm(recv_time: str) -> str:
    # recv_time is "YYYY-MM-DDTHH:MM:SS"; show HH:MM.
    if len(recv_time) >= 16 and recv_time[10] == "T":
        return recv_time[11:16]
    return recv_time


class LiveTab(QtWidgets.QWidget):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._entries = []  # keep everything so filter toggles can re-render
        self._visible = set(settings.visible_channels())

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
        layout.addLayout(filter_row)
        layout.addWidget(self.view, 1)

    # -- entries -----------------------------------------------------------

    def add_entry(self, entry: dict) -> None:
        self._entries.append(entry)
        if self._passes_filter(entry):
            self.view.append(self._format_html(entry))
            self._scroll_to_end_if_wanted()

    def _passes_filter(self, entry: dict) -> bool:
        channel = entry.get("channel", "Unknown")
        if channel not in CHANNEL_COLORS:
            channel = "Unknown"
        return channel in self._visible

    def _format_html(self, entry: dict) -> str:
        channel = entry.get("channel", "Unknown")
        color = CHANNEL_COLORS.get(channel, CHANNEL_COLORS["Unknown"])
        time_str = _time_hm(str(entry.get("recv_time", "")))
        character = entry.get("character") or entry.get("account") or "?"
        text = entry.get("text") or ""

        tag = channel
        subgroup = entry.get("subgroup")
        if channel == "Squad" and subgroup is not None:
            tag = f"Squad·{subgroup}"

        esc = html.escape
        parts = [
            f'<span style="color:{TIME_COLOR}">[{esc(time_str)}]</span> ',
        ]
        if entry.get("broadcast"):
            parts.append(f'<span style="color:{BROADCAST_COLOR}">★</span> ')
        parts.append(
            f'<span style="color:{color};font-weight:bold">[{esc(tag)}] {esc(str(character))}:</span> '
        )
        parts.append(f'<span>{esc(str(text))}</span>')
        return "".join(parts)

    def _scroll_to_end_if_wanted(self) -> None:
        if self.autoscroll.isChecked():
            bar = self.view.verticalScrollBar()
            bar.setValue(bar.maximum())

    # -- filters / clear ---------------------------------------------------

    def _on_filter_changed(self) -> None:
        self._visible = {ch for ch, box in self._channel_boxes.items() if box.isChecked()}
        self._settings.set_visible_channels(sorted(self._visible))
        self._rerender()

    def _rerender(self) -> None:
        self.view.clear()
        for entry in self._entries:
            if self._passes_filter(entry):
                self.view.append(self._format_html(entry))
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
            "Point it at 'gw2chatlogger.jsonl' next to arcdps in your GW2 bin64 folder.\n"
            "Coverage is party/squad chat only (unofficial_extras limitation)."
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
                "Use Browse to select it manually (it sits next to arcdps in bin64).",
            )


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GW2 Chat Logger")

        self.settings = Settings()
        self.reader = ChatLogReader(self.settings.log_path())

        self.live_tab = LiveTab(self.settings)
        self.options_tab = OptionsTab(self.settings)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.live_tab, "Live")
        tabs.addTab(self.options_tab, "Options")
        self.setCentralWidget(tabs)

        self.status = self.statusBar()
        self._update_status()

        self.reader.entry_received.connect(self.live_tab.add_entry)
        self.reader.error.connect(self._on_reader_error)
        self.options_tab.path_changed.connect(self._on_path_changed)

        self.reader.start(from_beginning=True)

    def _on_path_changed(self, path: str) -> None:
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
        self.reader.stop()
        super().closeEvent(event)
