from collections import deque
from datetime import datetime
from pathlib import Path
from typing import List


class ChatLogWriter:
    def __init__(self, log_dir: Path) -> None:
        self._log_dir = Path(log_dir)
        self._current_path = None
        self._recent_lines = deque(maxlen=500)

    def set_log_dir(self, log_dir: Path) -> None:
        self._log_dir = Path(log_dir)

    def current_path(self) -> Path:
        return self._current_path

    def start_new_session(self) -> Path:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._current_path = self._log_dir / f"chatlog_{timestamp}.txt"
        self._current_path.touch(exist_ok=True)
        self._recent_lines.clear()
        return self._current_path

    def append_lines(self, lines: List[str]) -> List[str]:
        if self._current_path is None:
            self.start_new_session()

        new_lines = []
        for line in lines:
            clean = line.strip()
            if not clean:
                continue
            if clean in self._recent_lines:
                continue
            self._recent_lines.append(clean)
            new_lines.append(clean)

        if new_lines:
            with self._current_path.open("a", encoding="utf-8") as handle:
                for line in new_lines:
                    handle.write(line + "\n")

        return new_lines
