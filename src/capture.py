import numpy as np
import mss


def capture_region(x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    if x2 <= x1 or y2 <= y1:
        raise ValueError("Invalid capture region")

    region = {
        "left": int(x1),
        "top": int(y1),
        "width": int(x2 - x1),
        "height": int(y2 - y1),
    }
    with mss.mss() as sct:
        image = np.array(sct.grab(region))

    if image.ndim != 3 or image.shape[2] < 3:
        raise ValueError("Unexpected capture data")

    rgb = image[:, :, :3][:, :, ::-1]
    return rgb
