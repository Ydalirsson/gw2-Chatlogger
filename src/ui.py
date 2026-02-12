from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from .capture import capture_region
from .ocr_engine import OcrEngine
from .paths import app_data_dir
from .settings import Settings
from .session_manager import SessionManager
from .window_monitor import WindowMonitor
from .workers import OcrWorker, SessionOcrWorker, OcrInitWorker


class SelectAreaLabel(QtWidgets.QLabel):
    def __init__(self, pixmap: QtGui.QPixmap, parent=None) -> None:
        super().__init__(parent)
        self.setPixmap(pixmap)
        self.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self._origin = None
        self._rubber = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle, self)
        self._selection = None

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() != QtCore.Qt.LeftButton:
            return
        self._origin = event.pos()
        self._rubber.setGeometry(QtCore.QRect(self._origin, QtCore.QSize()))
        self._rubber.show()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._origin is None:
            return
        rect = QtCore.QRect(self._origin, event.pos()).normalized()
        self._rubber.setGeometry(rect)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() != QtCore.Qt.LeftButton:
            return
        if self._origin is None:
            return
        self._selection = self._rubber.geometry()
        self._origin = None

    def selection(self):
        return self._selection


class SelectAreaDialog(QtWidgets.QDialog):
    def __init__(self, pixmap: QtGui.QPixmap, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Chat Box Area")
        self.setModal(True)

        info = QtWidgets.QLabel(
            "Drag to select the chat box. Press Enter/Space to confirm, C to cancel."
        )
        info.setWordWrap(True)

        self._label = SelectAreaLabel(pixmap)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(info)
        layout.addWidget(self._label, 1)

        self.resize(pixmap.width(), pixmap.height())

    def selected_rect(self):
        rect = self._label.selection()
        if rect is None:
            return None
        pixmap = self._label.pixmap()
        if pixmap is None:
            return None
        dpr = pixmap.devicePixelRatio() or 1.0
        return QtCore.QRect(
            int(rect.x() * dpr),
            int(rect.y() * dpr),
            int(rect.width() * dpr),
            int(rect.height() * dpr),
        )

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Space):
            if self.selected_rect() is not None:
                self.accept()
            return
        if event.key() in (QtCore.Qt.Key_C, QtCore.Qt.Key_Escape):
            self.reject()
            return
        super().keyPressEvent(event)


class ControlTab(QtWidgets.QWidget):
    record_clicked = QtCore.Signal()
    stop_clicked = QtCore.Signal()
    try_clicked = QtCore.Signal()
    set_area_clicked = QtCore.Signal()
    new_session_clicked = QtCore.Signal()
    init_clicked = QtCore.Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.record_button = QtWidgets.QPushButton("Record")
        self.stop_button = QtWidgets.QPushButton("Stop")
        self.try_button = QtWidgets.QPushButton("Try")
        self.set_area_button = QtWidgets.QPushButton("Set Chat Box Area")
        self.new_session_button = QtWidgets.QPushButton("New Session Folder")
        self.init_button = QtWidgets.QPushButton("Initialize OCR")
        self.init_progress = QtWidgets.QProgressBar()
        self.init_progress.setRange(0, 1)
        self.init_progress.setValue(0)
        self.init_progress.setVisible(False)

        self.status_label = QtWidgets.QLabel("Status: idle")
        self.log_path_label = QtWidgets.QLabel("Session folder: not set")

        self.stop_button.setEnabled(False)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(self.record_button)
        button_row.addWidget(self.stop_button)
        button_row.addWidget(self.try_button)

        second_row = QtWidgets.QHBoxLayout()
        second_row.addWidget(self.set_area_button)
        second_row.addWidget(self.new_session_button)

        init_row = QtWidgets.QHBoxLayout()
        init_row.addWidget(self.init_button)
        init_row.addWidget(self.init_progress, 1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(button_row)
        layout.addLayout(second_row)
        layout.addLayout(init_row)
        layout.addSpacing(8)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_path_label)
        layout.addStretch(1)

        self.record_button.clicked.connect(self.record_clicked.emit)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        self.try_button.clicked.connect(self.try_clicked.emit)
        self.set_area_button.clicked.connect(self.set_area_clicked.emit)
        self.new_session_button.clicked.connect(self.new_session_clicked.emit)
        self.init_button.clicked.connect(self.init_clicked.emit)

    def set_recording(self, recording: bool) -> None:
        self.record_button.setEnabled(not recording)
        self.stop_button.setEnabled(recording)

    def set_init_running(self, running: bool) -> None:
        self.init_button.setEnabled(not running)
        if running:
            self.init_progress.setVisible(True)
            self.init_progress.setRange(0, 0)
        else:
            self.init_progress.setRange(0, 1)
            self.init_progress.setValue(1)
            self.init_progress.setVisible(False)

    def update_status(self, text: str) -> None:
        self.status_label.setText(f"Status: {text}")

    def set_session_path(self, path: Path) -> None:
        if path is None:
            self.log_path_label.setText("Session folder: not set")
        else:
            self.log_path_label.setText(f"Session folder: {path}")


class LoggerTab(QtWidgets.QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.text_edit = QtWidgets.QPlainTextEdit()
        self.text_edit.setReadOnly(True)

        clear_button = QtWidgets.QPushButton("Clear")
        clear_button.clicked.connect(self.text_edit.clear)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        layout.addWidget(clear_button)

    def append_lines(self, lines) -> None:
        for line in lines:
            self.text_edit.appendPlainText(line)

    def append_text(self, text: str) -> None:
        if text:
            self.text_edit.appendPlainText(text)


class OptionsTab(QtWidgets.QWidget):
    settings_updated = QtCore.Signal()

    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings

        area = settings.chat_area()

        self.x1 = QtWidgets.QSpinBox()
        self.y1 = QtWidgets.QSpinBox()
        self.x2 = QtWidgets.QSpinBox()
        self.y2 = QtWidgets.QSpinBox()
        for spin in (self.x1, self.y1, self.x2, self.y2):
            spin.setRange(0, 20000)

        self.x1.setValue(area["x1"])
        self.y1.setValue(area["y1"])
        self.x2.setValue(area["x2"])
        self.y2.setValue(area["y2"])

        self.spm = QtWidgets.QSpinBox()
        self.spm.setRange(1, 600)
        self.spm.setValue(settings.screenshots_per_minute())

        self.lang_de = QtWidgets.QCheckBox("German")
        self.lang_en = QtWidgets.QCheckBox("English")
        langs = settings.languages()
        self.lang_de.setChecked("de" in langs)
        self.lang_en.setChecked("en" in langs)

        self.log_dir_edit = QtWidgets.QLineEdit(str(settings.log_dir()))
        browse_button = QtWidgets.QPushButton("Browse")
        browse_button.clicked.connect(self._browse_log_dir)

        self.use_gpu = QtWidgets.QCheckBox("Use GPU (if available)")
        self.use_gpu.setChecked(settings.use_gpu())

        self.quality_combo = QtWidgets.QComboBox()
        self.quality_combo.addItems(["Fast", "Balanced", "Accurate"])
        current_quality = settings.ocr_quality()
        if current_quality == "fast":
            self.quality_combo.setCurrentText("Fast")
        elif current_quality == "accurate":
            self.quality_combo.setCurrentText("Accurate")
        else:
            self.quality_combo.setCurrentText("Balanced")

        self.active_title_edit = QtWidgets.QLineEdit(settings.active_window_title())
        self.only_when_active = QtWidgets.QCheckBox("Only when active window matches")
        self.only_when_active.setChecked(settings.only_when_active())

        form = QtWidgets.QFormLayout()
        area_layout = QtWidgets.QHBoxLayout()
        area_layout.addWidget(QtWidgets.QLabel("X1"))
        area_layout.addWidget(self.x1)
        area_layout.addWidget(QtWidgets.QLabel("Y1"))
        area_layout.addWidget(self.y1)
        area_layout.addWidget(QtWidgets.QLabel("X2"))
        area_layout.addWidget(self.x2)
        area_layout.addWidget(QtWidgets.QLabel("Y2"))
        area_layout.addWidget(self.y2)

        form.addRow("Chat area", area_layout)
        form.addRow("Screenshots per minute", self.spm)

        lang_layout = QtWidgets.QHBoxLayout()
        lang_layout.addWidget(self.lang_de)
        lang_layout.addWidget(self.lang_en)
        form.addRow("Languages", lang_layout)

        log_layout = QtWidgets.QHBoxLayout()
        log_layout.addWidget(self.log_dir_edit)
        log_layout.addWidget(browse_button)
        form.addRow("Session base folder", log_layout)
        form.addRow("OCR", self.use_gpu)
        form.addRow("OCR quality", self.quality_combo)

        form.addRow("Active window title", self.active_title_edit)
        form.addRow("", self.only_when_active)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(form)
        layout.addStretch(1)

        for widget in (self.x1, self.y1, self.x2, self.y2, self.spm):
            widget.valueChanged.connect(self._save_settings)
        self.lang_de.stateChanged.connect(self._save_settings)
        self.lang_en.stateChanged.connect(self._save_settings)
        self.log_dir_edit.editingFinished.connect(self._save_settings)
        self.use_gpu.stateChanged.connect(self._save_settings)
        self.quality_combo.currentIndexChanged.connect(self._save_settings)
        self.active_title_edit.editingFinished.connect(self._save_settings)
        self.only_when_active.stateChanged.connect(self._save_settings)

    def _browse_log_dir(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Log Directory")
        if path:
            self.log_dir_edit.setText(path)
            self._save_settings()

    def _save_settings(self) -> None:
        languages = []
        if self.lang_de.isChecked():
            languages.append("de")
        if self.lang_en.isChecked():
            languages.append("en")
        if not languages:
            languages = ["en"]
            self.lang_en.setChecked(True)

        log_dir = self.log_dir_edit.text().strip()
        if not log_dir:
            log_dir = str(self._settings.log_dir())
            self.log_dir_edit.setText(log_dir)

        self._settings.set_chat_area(
            self.x1.value(), self.y1.value(), self.x2.value(), self.y2.value()
        )
        self._settings.set_screenshots_per_minute(self.spm.value())
        self._settings.set_languages(languages)
        self._settings.set_log_dir(log_dir)
        self._settings.set_use_gpu(self.use_gpu.isChecked())
        self._settings.set_ocr_quality(self.quality_combo.currentText())
        self._settings.set_active_window_title(self.active_title_edit.text())
        self._settings.set_only_when_active(self.only_when_active.isChecked())
        self.settings_updated.emit()

    def set_chat_area_values(self, x1: int, y1: int, x2: int, y2: int) -> None:
        self.x1.setValue(x1)
        self.y1.setValue(y1)
        self.x2.setValue(x2)
        self.y2.setValue(y2)
        self._save_settings()


class SessionOcrTab(QtWidgets.QWidget):
    def __init__(self, engine: OcrEngine, session_manager: SessionManager, parent=None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._session_manager = session_manager
        self._worker = None
        self._session_dir = None

        self.select_button = QtWidgets.QPushButton("Select Session Folder")
        self.run_button = QtWidgets.QPushButton("Run OCR for Session")
        self.run_button.setEnabled(False)

        self.session_label = QtWidgets.QLabel("Session: not selected")
        self.status_label = QtWidgets.QLabel("Status: idle")
        self.output_label = QtWidgets.QLabel("Output: chatlog.txt")

        self.image_list = QtWidgets.QListWidget()
        self.output_text = QtWidgets.QPlainTextEdit()
        self.output_text.setReadOnly(True)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addWidget(self.select_button)
        button_row.addWidget(self.run_button)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(button_row)
        layout.addWidget(self.session_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.output_label)
        layout.addWidget(self.image_list)
        layout.addWidget(self.output_text)

        self.select_button.clicked.connect(self._select_session)
        self.run_button.clicked.connect(self._run_session)

    def _select_session(self) -> None:
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Session Folder")
        if not path:
            return
        self._session_dir = Path(path)
        self.session_label.setText(f"Session: {self._session_dir}")
        self._load_images()

    def _load_images(self) -> None:
        self.image_list.clear()
        if self._session_dir is None:
            self.run_button.setEnabled(False)
            return
        images = self._session_manager.list_images(self._session_dir)
        for path in images:
            self.image_list.addItem(str(path))
        self.run_button.setEnabled(bool(images))
        self.status_label.setText(f"Status: {len(images)} images found")
        output_path = self._session_manager.output_path(self._session_dir)
        self.output_label.setText(f"Output: {output_path}")

    def _run_session(self) -> None:
        if self._session_dir is None:
            return
        files = [self.image_list.item(i).text() for i in range(self.image_list.count())]
        if not files:
            return
        if not self._engine.is_ready():
            self.output_text.appendPlainText("OCR is not initialized. Click 'Initialize OCR' first.")
            self.status_label.setText("Status: init required")
            return
        self.output_text.clear()
        self.select_button.setEnabled(False)
        self.run_button.setEnabled(False)

        output_path = self._session_manager.output_path(self._session_dir)
        self._worker = SessionOcrWorker(self._engine, files, output_path=output_path)
        self._worker.line_result.connect(self.output_text.appendPlainText)
        self._worker.status.connect(self._update_status)
        self._worker.error.connect(self._append_error)
        self._worker.finished.connect(self._session_finished)
        self._worker.start()

    def _update_status(self, text: str) -> None:
        self.status_label.setText(f"Status: {text}")

    def _append_error(self, message: str) -> None:
        self.output_text.appendPlainText(f"Error: {message}")

    def _session_finished(self, output_path: str) -> None:
        if output_path:
            self.output_text.appendPlainText("")
            self.output_text.appendPlainText(f"Saved to {output_path}")
        self.status_label.setText("Status: done")
        self.select_button.setEnabled(True)
        self.run_button.setEnabled(True)
        self._worker = None


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GW2 Chat Logger")

        self.settings = Settings()
        self.window_monitor = WindowMonitor()

        data_dir = app_data_dir()
        model_dir = data_dir / "models"
        self.ocr_engine = OcrEngine(
            self.settings.languages(),
            model_dir,
            use_gpu=self.settings.use_gpu(),
            quality=self.settings.ocr_quality(),
        )
        self.session_manager = SessionManager(self.settings.log_dir())

        self.threadpool = QtCore.QThreadPool.globalInstance()
        self._workers = set()
        self._pending_ocr = False
        self._pending_capture = False
        self._window_error_shown = False
        self._capture_count = 0
        self._init_worker = None
        self._init_ready = False

        self.control_tab = ControlTab()
        self.logger_tab = LoggerTab()
        self.options_tab = OptionsTab(self.settings)
        self.session_tab = SessionOcrTab(self.ocr_engine, self.session_manager)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.control_tab, "Control")
        tabs.addTab(self.logger_tab, "Logger View")
        tabs.addTab(self.options_tab, "Options")
        tabs.addTab(self.session_tab, "Session OCR")

        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.addWidget(tabs)
        self.setCentralWidget(container)

        self.record_timer = QtCore.QTimer(self)
        self.record_timer.timeout.connect(self._on_record_tick)

        self.control_tab.record_clicked.connect(self._start_recording)
        self.control_tab.stop_clicked.connect(self._stop_recording)
        self.control_tab.try_clicked.connect(self._try_once)
        self.control_tab.set_area_clicked.connect(self._set_chat_area)
        self.control_tab.new_session_clicked.connect(self._new_log_session)
        self.control_tab.init_clicked.connect(self._start_init)

        self.options_tab.settings_updated.connect(self._on_settings_updated)

        self.control_tab.set_session_path(self.session_manager.current_session_dir())
        self._start_init(auto=True)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.record_timer.stop()
        super().closeEvent(event)

    def _on_settings_updated(self) -> None:
        self.session_manager.set_base_dir(self.settings.log_dir())
        self.ocr_engine.set_languages(self.settings.languages())
        self.ocr_engine.set_use_gpu(self.settings.use_gpu())
        self.ocr_engine.set_quality(self.settings.ocr_quality())
        self._init_ready = False
        if self.record_timer.isActive():
            self._update_timer_interval()
        self._start_init(auto=True)

    def _update_timer_interval(self) -> None:
        spm = max(1, self.settings.screenshots_per_minute())
        interval = max(200, int(60000 / spm))
        self.record_timer.setInterval(interval)

    def _start_recording(self) -> None:
        if self.record_timer.isActive():
            return
        if not self._chat_area_valid():
            QtWidgets.QMessageBox.warning(
                self, "Chat Area", "Set a valid chat box area before recording."
            )
            return
        if self.session_manager.current_session_dir() is None:
            self._new_log_session()
        self._update_timer_interval()
        self.record_timer.start()
        self.control_tab.set_recording(True)
        self.control_tab.update_status("recording (0 images)")

    def _stop_recording(self) -> None:
        if not self.record_timer.isActive():
            return
        self.record_timer.stop()
        self.control_tab.set_recording(False)
        self.control_tab.update_status("stopped")

    def _try_once(self) -> None:
        if not self._ensure_ocr_ready():
            return
        self._capture_and_ocr()

    def _new_log_session(self) -> None:
        try:
            path = self.session_manager.start_new_session()
        except Exception as exc:
            QtWidgets.QMessageBox.warning(
                self, "Session", f"Failed to create session folder: {exc}"
            )
            return
        self._capture_count = 0
        self.control_tab.set_session_path(path)

    def _set_chat_area(self) -> None:
        screen = self._select_screen()
        if screen is None:
            return
        pixmap = screen.grabWindow(0)
        if pixmap.isNull():
            QtWidgets.QMessageBox.warning(
                self, "Screen", "Unable to capture the screen."
            )
            return
        dialog = SelectAreaDialog(pixmap, self)
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        rect = dialog.selected_rect()
        if rect is None or rect.width() <= 0 or rect.height() <= 0:
            return
        geom = screen.geometry()
        dpr = screen.devicePixelRatio() or 1.0
        offset_x = int(geom.x() * dpr)
        offset_y = int(geom.y() * dpr)
        x1 = offset_x + rect.left()
        y1 = offset_y + rect.top()
        x2 = x1 + rect.width()
        y2 = y1 + rect.height()
        self.options_tab.set_chat_area_values(x1, y1, x2, y2)

    def _select_screen(self):
        screens = QtWidgets.QApplication.screens()
        if not screens:
            QtWidgets.QMessageBox.warning(self, "Screen", "No screen found.")
            return None
        if len(screens) == 1:
            return screens[0]

        primary = QtWidgets.QApplication.primaryScreen()
        items = []
        index_map = []
        for scr in screens:
            geom = scr.geometry()
            label = (
                f"{scr.name()} ({geom.width()}x{geom.height()})"
                f"{' [Primary]' if scr == primary else ''}"
            )
            items.append(label)
            index_map.append(scr)

        default_index = screens.index(primary) if primary in screens else 0
        selection, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Select Monitor",
            "Choose the monitor that shows Guild Wars 2:",
            items,
            default_index,
            False,
        )
        if not ok:
            return None
        selected_index = items.index(selection)
        return index_map[selected_index]

    def _chat_area_valid(self) -> bool:
        area = self.settings.chat_area()
        return area["x2"] > area["x1"] and area["y2"] > area["y1"]

    def _on_record_tick(self) -> None:
        self._capture_and_store()

    def _capture_and_store(self) -> None:
        if self._pending_capture:
            return
        if self.settings.only_when_active():
            title = self.settings.active_window_title()
            if not self.window_monitor.is_target_active(title):
                self.control_tab.update_status("paused (window not active)")
                return
            if self.window_monitor.last_error() and not self._window_error_shown:
                self._window_error_shown = True
                self.logger_tab.append_text(
                    f"Window detection warning: {self.window_monitor.last_error()}"
                )

        area = self.settings.chat_area()
        try:
            image = capture_region(area["x1"], area["y1"], area["x2"], area["y2"])
        except Exception as exc:
            self.control_tab.update_status("capture error")
            self.logger_tab.append_text(f"Capture error: {exc}")
            return

        self._pending_capture = True
        try:
            path = self.session_manager.save_image(image)
        except Exception as exc:
            self.control_tab.update_status("save error")
            self.logger_tab.append_text(f"Save error: {exc}")
        else:
            self._capture_count += 1
            self.control_tab.update_status(
                f"recording ({self._capture_count} images)"
            )
            self.logger_tab.append_text(f"Saved: {path}")
        finally:
            self._pending_capture = False

    def _capture_and_ocr(self) -> None:
        if self._pending_ocr:
            return
        if self.settings.only_when_active():
            title = self.settings.active_window_title()
            if not self.window_monitor.is_target_active(title):
                self.control_tab.update_status("paused (window not active)")
                return
            if self.window_monitor.last_error() and not self._window_error_shown:
                self._window_error_shown = True
                self.logger_tab.append_text(
                    f"Window detection warning: {self.window_monitor.last_error()}"
                )

        area = self.settings.chat_area()
        try:
            image = capture_region(area["x1"], area["y1"], area["x2"], area["y2"])
        except Exception as exc:
            self.control_tab.update_status("capture error")
            self.logger_tab.append_text(f"Capture error: {exc}")
            return

        worker = OcrWorker(self.ocr_engine, image)
        self._pending_ocr = True
        self._workers.add(worker)

        worker.signals.result.connect(self._handle_ocr_result)
        worker.signals.error.connect(self._handle_ocr_error)
        worker.signals.finished.connect(lambda: self._on_worker_done(worker))

        self.threadpool.start(worker)

    def _ensure_ocr_ready(self) -> bool:
        if self._init_ready:
            return True
        QtWidgets.QMessageBox.information(
            self,
            "OCR Init",
            "OCR is not initialized yet. Click 'Initialize OCR' and wait until it finishes.",
        )
        return False

    def _start_init(self, auto: bool = False) -> None:
        if self._init_worker is not None and self._init_worker.isRunning():
            return
        if self._init_ready and not auto:
            self.logger_tab.append_text("OCR already initialized.")
            return
        self.control_tab.set_init_running(True)
        self.control_tab.update_status("initializing OCR")
        self.logger_tab.append_text("Initializing OCR. Models may download on first run...")

        self._init_worker = OcrInitWorker(self.ocr_engine)
        self._init_worker.log.connect(self.logger_tab.append_text)
        self._init_worker.error.connect(self._on_init_error)
        self._init_worker.finished.connect(self._on_init_finished)
        self._init_worker.start()

    def _on_init_error(self, message: str) -> None:
        self.control_tab.update_status("ocr init error")
        self.logger_tab.append_text(f"OCR init error: {message}")
        QtWidgets.QMessageBox.warning(self, "OCR Init", message)

    def _on_init_finished(self, success: bool) -> None:
        self.control_tab.set_init_running(False)
        if success:
            self._init_ready = True
            self.control_tab.update_status("ocr ready")
        else:
            self._init_ready = False

    def _handle_ocr_result(self, lines) -> None:
        if lines:
            self.logger_tab.append_lines(lines)
        else:
            self.logger_tab.append_text("(no text detected)")

    def _handle_ocr_error(self, message: str) -> None:
        self.control_tab.update_status("ocr error")
        self.logger_tab.append_text(f"OCR error: {message}")

    def _on_worker_done(self, worker: OcrWorker) -> None:
        self._pending_ocr = False
        self._workers.discard(worker)
