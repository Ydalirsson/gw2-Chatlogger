from pathlib import Path

from PySide6 import QtCore

from .text_dedupe import RecentDeduper


class WorkerSignals(QtCore.QObject):
    result = QtCore.Signal(object)
    error = QtCore.Signal(str)
    finished = QtCore.Signal()


class OcrWorker(QtCore.QRunnable):
    def __init__(self, engine, image):
        super().__init__()
        self.engine = engine
        self.image = image
        self.signals = WorkerSignals()

    def run(self):
        try:
            lines = self.engine.read_lines(self.image)
            self.signals.result.emit(lines)
        except Exception as exc:
            self.signals.error.emit(str(exc))
        finally:
            self.signals.finished.emit()


class BatchWorker(QtCore.QThread):
    file_result = QtCore.Signal(str, str)
    error = QtCore.Signal(str)
    finished = QtCore.Signal()

    def __init__(self, engine, files):
        super().__init__()
        self.engine = engine
        self.files = list(files)

    def run(self):
        try:
            for path in self.files:
                try:
                    lines = self.engine.read_lines_from_path(path)
                    text = "\n".join(lines)
                    self.file_result.emit(path, text)
                except Exception as exc:
                    self.error.emit(f"{path}: {exc}")
        finally:
            self.finished.emit()


class SessionOcrWorker(QtCore.QThread):
    line_result = QtCore.Signal(str)
    status = QtCore.Signal(str)
    error = QtCore.Signal(str)
    finished = QtCore.Signal(str)

    def __init__(self, engine, files, output_path=None, max_recent=500):
        super().__init__()
        self.engine = engine
        self.files = list(files)
        self.output_path = Path(output_path) if output_path else None
        self.max_recent = max_recent

    def run(self):
        deduper = RecentDeduper(max_recent=self.max_recent)
        total = len(self.files)
        handle = None
        if self.output_path is not None:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            handle = self.output_path.open("w", encoding="utf-8")
        try:
            for index, path in enumerate(self.files, start=1):
                try:
                    lines = self.engine.read_lines_from_path(path)
                except Exception as exc:
                    self.error.emit(f"{path}: {exc}")
                    continue

                new_lines = deduper.filter_new(lines)
                if new_lines:
                    for line in new_lines:
                        self.line_result.emit(line)
                        if handle is not None:
                            handle.write(line + "\n")
                self.status.emit(f"Processed {index}/{total}")
        finally:
            if handle is not None:
                handle.close()
            self.finished.emit(str(self.output_path) if self.output_path else "")


class OcrInitWorker(QtCore.QThread):
    log = QtCore.Signal(str)
    error = QtCore.Signal(str)
    finished = QtCore.Signal(bool)

    def __init__(self, engine) -> None:
        super().__init__()
        self.engine = engine

    def run(self):
        try:
            self.log.emit("Starting OCR initialization...")
            self.engine.ensure_initialized(log_cb=self.log.emit)
            self.log.emit("OCR initialization complete.")
            self.finished.emit(True)
        except Exception as exc:
            self.error.emit(str(exc))
            self.finished.emit(False)
