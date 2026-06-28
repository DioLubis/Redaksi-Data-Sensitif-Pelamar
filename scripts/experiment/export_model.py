from __future__ import annotations

import argparse
from pathlib import Path

from common import ensure_project_python, load_config, python_executable, resolve, run


def main() -> None:
    ensure_project_python()
    parser = argparse.ArgumentParser(description="Export a YOLOv5 or YOLO26 weight file to ONNX.")
    parser.add_argument("--backend", choices=["yolov5", "yolo26"], required=True)
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--config", default="configs/training/privacy_shield.yaml")
    parser.add_argument("--image-size", type=int)
    args = parser.parse_args()
    config = load_config(args.config)
    image_size = args.image_size or config["experiment"]["image_size"]
    if args.backend == "yolov5":
        repo = resolve(config["models"]["yolov5"]["repo"])
        run([python_executable(), str(repo / "export.py"), "--weights", str(args.weights), "--imgsz", str(image_size), "--include", "onnx"])
    else:
        from ultralytics import YOLO

        print(YOLO(str(args.weights)).export(format="onnx", imgsz=image_size))


if __name__ == "__main__":
    main()
