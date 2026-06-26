from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

CLASS_NAMES = [
    "face_photo",
    "signature",
    "qr_code",
    "barcode",
    "id_card",
]

CLASS_TO_ID = {name: idx for idx, name in enumerate(CLASS_NAMES)}


@dataclass(frozen=True)
class ImageSize:
    width: int
    height: int


@dataclass(frozen=True)
class YoloBox:
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float

    def to_line(self) -> str:
        values = [
            self.class_id,
            self.x_center,
            self.y_center,
            self.width,
            self.height,
        ]
        return f"{values[0]} " + " ".join(f"{value:.6f}" for value in values[1:])


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def list_images(path: Path) -> list[Path]:
    return sorted(
        p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def clip(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def xyxy_to_yolo(
    class_id: int,
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
    image_size: ImageSize,
    margin_ratio: float = 0.0,
) -> YoloBox | None:
    width = float(image_size.width)
    height = float(image_size.height)
    if width <= 0 or height <= 0:
        return None

    box_w = max(0.0, x_max - x_min)
    box_h = max(0.0, y_max - y_min)
    margin_x = box_w * margin_ratio
    margin_y = box_h * margin_ratio

    x_min = clip(x_min - margin_x, 0.0, width)
    y_min = clip(y_min - margin_y, 0.0, height)
    x_max = clip(x_max + margin_x, 0.0, width)
    y_max = clip(y_max + margin_y, 0.0, height)

    if x_max <= x_min or y_max <= y_min:
        return None

    x_center = ((x_min + x_max) / 2.0) / width
    y_center = ((y_min + y_max) / 2.0) / height
    yolo_w = (x_max - x_min) / width
    yolo_h = (y_max - y_min) / height

    return YoloBox(
        class_id=class_id,
        x_center=clip(x_center, 0.0, 1.0),
        y_center=clip(y_center, 0.0, 1.0),
        width=clip(yolo_w, 0.0, 1.0),
        height=clip(yolo_h, 0.0, 1.0),
    )


def write_yolo_label(path: Path, boxes: Iterable[YoloBox]) -> None:
    ensure_dir(path.parent)
    lines = [box.to_line() for box in boxes]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
