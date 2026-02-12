from collections import deque


def _normalize(line: str) -> str:
    return " ".join(line.split()).lower()


class RecentDeduper:
    def __init__(self, max_recent: int = 500) -> None:
        self._max_recent = max(1, max_recent)
        self._deque = deque()
        self._set = set()

    def filter_new(self, lines):
        new_lines = []
        for line in lines:
            if not line:
                continue
            clean = line.strip()
            if not clean:
                continue
            key = _normalize(clean)
            if key in self._set:
                continue
            self._deque.append(key)
            self._set.add(key)
            if len(self._deque) > self._max_recent:
                old = self._deque.popleft()
                self._set.discard(old)
            new_lines.append(clean)
        return new_lines
