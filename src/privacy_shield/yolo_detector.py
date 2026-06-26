from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

from privacy_shield.schemas import Box, Detection

CLASS_NAMES = ["face_photo", "signature", "qr_code", "barcode", "id_card"]
VISUAL_METHOD = {"face_photo": "blur", "signature": "black_box", "qr_code": "pixelate", "barcode": "pixelate", "id_card": "black_box"}


class YOLODetector:
    def __init__(self, model_name: str, weights: str | Path, yolov5_repo: str | Path | None = None, confidence: float = 0.25) -> None:
        if model_name not in {"yolov5", "yolo26"}:
            raise ValueError("model_name must be yolov5 or yolo26")
        self.model_name = model_name
        self.weights = Path(weights)
        self.yolov5_repo = Path(yolov5_repo) if yolov5_repo else None
        self.confidence = confidence
        if not self.weights.is_file():
            raise FileNotFoundError("Model weights are required and were not found.")

    def detect(self, image_path: str | Path, page_number: int) -> list[Detection]:
        return self._detect_yolov5(Path(image_path), page_number) if self.model_name == "yolov5" else self._detect_yolo26(Path(image_path), page_number)

    def _build(self, class_id: int, confidence: float, box: Box, page_number: int) -> Detection:
        if class_id < 0 or class_id >= len(CLASS_NAMES):
            raise ValueError("Model emitted a class outside the frozen five-class dataset.")
        category = CLASS_NAMES[class_id]
        return Detection(page_number, category, "visual", confidence, box, "critical" if category == "id_card" else "high", None, VISUAL_METHOD[category])

    def _detect_yolo26(self, image_path: Path, page_number: int) -> list[Detection]:
        from ultralytics import YOLO

        result = YOLO(str(self.weights)).predict(source=str(image_path), conf=self.confidence, verbose=False)[0]
        detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = (round(value) for value in box.xyxy[0].tolist())
            detections.append(self._build(int(box.cls[0]), float(box.conf[0]), Box(x1, y1, x2, y2), page_number))
        return detections

    def _detect_yolov5(self, image_path: Path, page_number: int) -> list[Detection]:
        if not self.yolov5_repo or not (self.yolov5_repo / "detect.py").is_file():
            raise FileNotFoundError("Official YOLOv5 repository is required for --model yolov5.")
        with tempfile.TemporaryDirectory(prefix="privacy_yolov5_") as temporary:
            root = Path(temporary)
            command = [sys.executable, str(self.yolov5_repo / "detect.py"), "--weights", str(self.weights), "--source", str(image_path), "--conf-thres", str(self.confidence), "--save-txt", "--save-conf", "--nosave", "--project", str(root), "--name", "result", "--exist-ok"]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            label_path = root / "result" / "labels" / f"{image_path.stem}.txt"
            if not label_path.exists():
                return []
            with Image.open(image_path) as image:
                width, height = image.size
            detections = []
            for line in label_path.read_text(encoding="utf-8").splitlines():
                class_id, x_center, y_center, box_width, box_height, confidence = map(float, line.split())
                x1 = round((x_center - box_width / 2) * width)
                y1 = round((y_center - box_height / 2) * height)
                x2 = round((x_center + box_width / 2) * width)
                y2 = round((y_center + box_height / 2) * height)
                detections.append(self._build(int(class_id), confidence, Box(x1, y1, x2, y2), page_number))
            return detections
