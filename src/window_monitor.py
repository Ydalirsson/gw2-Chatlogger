class WindowMonitor:
    def __init__(self) -> None:
        self._last_error = None

    def is_target_active(self, title: str) -> bool:
        if not title:
            return True
        try:
            import pywinctl as pwc

            window = pwc.getActiveWindow()
            if window is None:
                return False
            window_title = window.title or ""
            return title.lower() in window_title.lower()
        except Exception as exc:
            self._last_error = str(exc)
            return True

    def last_error(self) -> str:
        return self._last_error or ""
