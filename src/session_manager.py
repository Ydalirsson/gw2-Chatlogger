from datetime import datetime
from pathlib import Path
import threading
from typing import Iterable, List

from PIL import Image


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp")


class SessionManager:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = Path(base_dir)
        self._current_dir = None
        self._lock = threading.Lock()
        self._counter = 0

    def set_base_dir(self, base_dir: Path) -> None:
        self._base_dir = Path(base_dir)

    def current_session_dir(self) -> Path:
        return self._current_dir

    def start_new_session(self) -> Path:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self._current_dir = self._base_dir / f"session_{timestamp}"
        self._current_dir.mkdir(parents=True, exist_ok=True)
        self._counter = 0
        return self._current_dir

    def save_image(self, image) -> Path:
        if self._current_dir is None:
            self.start_new_session()
        with self._lock:
            self._counter += 1
            index = self._counter
        filename = f"chat_{index:05d}.png"
        path = self._current_dir / filename
        Image.fromarray(image).save(path)
        return path

    def list_images(self, session_dir: Path) -> List[Path]:
        folder = Path(session_dir)
        if not folder.exists():
            return []
        images = [
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ]
        images.sort(key=lambda item: item.name)
        return images

    def output_path(self, session_dir: Path) -> Path:
        return Path(session_dir) / "chatlog.txt"
