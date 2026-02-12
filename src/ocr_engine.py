import threading
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageOps


class OcrEngine:
    def __init__(
        self, languages: List[str], model_dir: Path, use_gpu: bool = False, quality: str = "balanced"
    ) -> None:
        self._languages = list(languages)
        self._model_dir = Path(model_dir)
        self._lock = threading.Lock()
        self._reader = None
        self._reader_langs = None
        self._reader_gpu = None
        self._ready = False
        self._use_gpu = bool(use_gpu)
        self._quality = str(quality).lower()
        self._readtext_kwargs = {
            "detail": 1,
            "paragraph": True,
            "decoder": "beamsearch",
            "beamWidth": 5,
            "text_threshold": 0.5,
            "low_text": 0.25,
            "link_threshold": 0.4,
            "contrast_ths": 0.3,
            "adjust_contrast": 0.7,
            "min_size": 10,
        }

    def set_languages(self, languages: List[str]) -> None:
        self._languages = list(languages)
        self._reader = None
        self._reader_langs = None
        self._reader_gpu = None
        self._ready = False

    def set_use_gpu(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._use_gpu:
            return
        self._use_gpu = enabled
        self._reader = None
        self._reader_langs = None
        self._reader_gpu = None
        self._ready = False

    def set_quality(self, value: str) -> None:
        value = str(value).lower()
        if value not in {"fast", "balanced", "accurate"}:
            value = "balanced"
        if value == self._quality:
            return
        self._quality = value

    def is_ready(self) -> bool:
        return bool(self._ready and self._reader is not None)

    def ensure_initialized(self, log_cb=None) -> None:
        with self._lock:
            langs = self._normalized_languages()
            if (
                self._reader is None
                or tuple(langs) != self._reader_langs
                or self._use_gpu != self._reader_gpu
            ):
                if log_cb:
                    log_cb("Preparing EasyOCR models.")
                self._init_reader(log_cb=log_cb)
            self._ready = True

    def _init_reader(self, log_cb=None) -> None:
        import easyocr

        self._model_dir.mkdir(parents=True, exist_ok=True)
        langs = self._normalized_languages()
        if log_cb:
            device = "GPU" if self._use_gpu else "CPU"
            log_cb(f"Initializing EasyOCR ({device}). This can take a while on first run.")
        try:
            self._reader = easyocr.Reader(
                langs,
                gpu=self._use_gpu,
                model_storage_directory=str(self._model_dir),
                download_enabled=True,
            )
        except Exception as exc:
            raise RuntimeError(
                "EasyOCR init failed. Ensure models can be downloaded or placed "
                f"in {self._model_dir}. Original error: {exc}"
            ) from exc
        self._reader_langs = tuple(langs)
        self._reader_gpu = self._use_gpu

    def read_lines(self, image: np.ndarray) -> List[str]:
        prepared, meta = self._prepare_image(image)
        langs = self._normalized_languages()
        read_kwargs = self._readtext_kwargs_for(meta, langs)
        with self._lock:
            if (
                self._reader is None
                or tuple(langs) != self._reader_langs
                or self._use_gpu != self._reader_gpu
            ):
                self._init_reader()
            raw = self._reader.readtext(prepared, **read_kwargs)
        return self._extract_text_lines(raw)

    def read_lines_from_path(self, path: str) -> List[str]:
        image = Image.open(str(path)).convert("RGB")
        return self.read_lines(np.array(image))

    def _extract_text_lines(self, raw) -> List[str]:
        lines = []
        if not raw:
            return lines
        for item in raw:
            if isinstance(item, str):
                text = item
            elif isinstance(item, (list, tuple)):
                text = ""
                if len(item) >= 2 and isinstance(item[1], str):
                    text = item[1]
                elif len(item) >= 1 and isinstance(item[0], str):
                    text = item[0]
                else:
                    continue
            else:
                continue
            clean = text.strip()
            if clean:
                lines.append(clean)
        return lines

    def _prepare_image(self, image: np.ndarray):
        pil = Image.fromarray(image).convert("L")
        mean, contrast = self._analyze_image(pil)

        pil = ImageOps.autocontrast(pil, cutoff=2)
        pil = self._apply_gamma(pil, mean)
        if contrast < 55:
            pil = self._flatten_background(pil)
            pil = pil.filter(ImageFilter.MedianFilter(size=3))
        pil = pil.filter(ImageFilter.UnsharpMask(radius=1, percent=160, threshold=3))

        scale = self._compute_scale(pil.height)
        if scale > 1.0:
            new_size = (int(pil.width * scale), int(pil.height * scale))
            pil = pil.resize(new_size, Image.BICUBIC)

        meta = {"mean": mean, "contrast": contrast, "scale": scale}
        return np.array(pil.convert("RGB")), meta

    def _analyze_image(self, pil: Image.Image) -> tuple:
        small = pil.resize((max(1, pil.width // 4), max(1, pil.height // 4)))
        arr = np.array(small)
        mean = float(arr.mean())
        p5, p95 = np.percentile(arr, [5, 95])
        contrast = float(p95 - p5)
        return mean, contrast

    def _apply_gamma(self, pil: Image.Image, mean: float) -> Image.Image:
        if mean < 80:
            gamma = 0.75
        elif mean > 160:
            gamma = 1.1
        else:
            gamma = 1.0
        if gamma == 1.0:
            return pil
        lut = [min(255, int((i / 255.0) ** gamma * 255)) for i in range(256)]
        return pil.point(lut)

    def _flatten_background(self, pil: Image.Image) -> Image.Image:
        blur = pil.filter(ImageFilter.GaussianBlur(radius=6))
        flattened = ImageChops.subtract(pil, blur)
        return ImageOps.autocontrast(flattened)

    def _compute_scale(self, height: int) -> float:
        target_height = 360.0
        scale = target_height / float(height)
        if scale < 1.0:
            return 1.0
        return min(scale, 2.5)

    def _readtext_kwargs_for(self, meta: dict, langs: List[str]) -> dict:
        mean = meta["mean"]
        contrast = meta["contrast"]
        scale = meta["scale"]
        kwargs = dict(self._readtext_kwargs)

        if mean < 80:
            kwargs.update(
                {
                    "text_threshold": 0.4,
                    "low_text": 0.2,
                    "contrast_ths": 0.4,
                    "adjust_contrast": 0.8,
                }
            )
        if contrast < 50:
            kwargs.update(
                {
                    "text_threshold": 0.35,
                    "low_text": 0.18,
                    "adjust_contrast": 0.9,
                }
            )

        kwargs["min_size"] = max(8, int(10 * scale))
        if len(langs) > 1:
            kwargs["decoder"] = "beamsearch"
            kwargs["beamWidth"] = 5
        else:
            kwargs["decoder"] = "greedy"
            kwargs["beamWidth"] = 1
        self._apply_quality_profile(kwargs)
        return kwargs

    def _normalized_languages(self) -> List[str]:
        mapping = {
            "de": "de",
            "ger": "de",
            "german": "de",
            "deu": "de",
            "en": "en",
            "eng": "en",
            "english": "en",
        }
        normalized = []
        seen = set()
        for lang in self._languages:
            key = mapping.get(str(lang).lower(), str(lang).lower())
            if key in seen:
                continue
            seen.add(key)
            normalized.append(key)
        if not normalized:
            normalized = ["en"]
        return normalized

    def _apply_quality_profile(self, kwargs: dict) -> None:
        if self._quality == "fast":
            kwargs["decoder"] = "greedy"
            kwargs["beamWidth"] = 1
            kwargs["text_threshold"] = min(0.7, max(kwargs["text_threshold"], 0.55))
            kwargs["low_text"] = max(kwargs["low_text"], 0.3)
            kwargs["contrast_ths"] = min(kwargs["contrast_ths"], 0.25)
            kwargs["adjust_contrast"] = min(kwargs["adjust_contrast"], 0.6)
        elif self._quality == "accurate":
            kwargs["decoder"] = "beamsearch"
            kwargs["beamWidth"] = max(kwargs["beamWidth"], 7)
            kwargs["text_threshold"] = max(0.35, kwargs["text_threshold"] - 0.1)
            kwargs["low_text"] = max(0.15, kwargs["low_text"] - 0.05)
            kwargs["contrast_ths"] = max(0.35, kwargs["contrast_ths"])
            kwargs["adjust_contrast"] = max(0.8, kwargs["adjust_contrast"])
