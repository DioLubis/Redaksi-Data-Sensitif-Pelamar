from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from common import ensure_project_python, load_config, python_executable, resolve, runtime_data_config, select_device


def sample_source(config: dict) -> Path:
    return resolve(config["experiment"]["data"]).parent / "images" / "test"


def benchmark_yolov5(config: dict, weights: Path, device: str) -> dict:
    import subprocess

    repo = resolve(config["models"]["yolov5"]["repo"])
    data_config = runtime_data_config(config["experiment"]["data"])
    command = [
        python_executable(), str(repo / "val.py"), "--weights", str(weights), "--data", str(data_config),
        "--img", str(config["experiment"]["image_size"]), "--batch-size", str(config["experiment"]["batch_size"]),
        "--task", "speed", "--device", device,
    ]
    completed = subprocess.run(command, check=True, text=True, capture_output=True)
    output = completed.stdout + completed.stderr
    match = re.search(r"Speed:\s*[\d.]+ms pre-process,\s*([\d.]+)ms inference", output)
    if match is None:
        raise RuntimeError("Could not parse YOLOv5 inference speed from val.py output.")
    inference_ms = float(match.group(1))
    return {"backend": "yolov5", "weights": str(weights), "inference_ms_per_image": inference_ms, "fps": 1000 / inference_ms}


def benchmark_yolo26(config: dict, weights: Path, device: str) -> dict:
    from ultralytics import YOLO

    results = list(YOLO(str(weights)).predict(source=str(sample_source(config)), imgsz=config["experiment"]["image_size"], device=device, stream=True, verbose=False))
    inference_times = [result.speed["inference"] for result in results]
    if not inference_times:
        raise RuntimeError("No test images were available for YOLO26 benchmark.")
    inference_ms = sum(inference_times) / len(inference_times)
    return {"backend": "yolo26", "weights": str(weights), "inference_ms_per_image": inference_ms, "fps": 1000 / inference_ms}


def main() -> None:
    ensure_project_python()
    parser = argparse.ArgumentParser(description="Benchmark model-only inference on the Privacy Shield test images.")
    parser.add_argument("--backend", choices=["yolov5", "yolo26"], required=True)
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--config", default="configs/training/privacy_shield.yaml")
    parser.add_argument("--device")
    args = parser.parse_args()
    config = load_config(args.config)
    device = select_device(config["experiment"]["device"], args.device)
    report = benchmark_yolov5(config, args.weights, device) if args.backend == "yolov5" else benchmark_yolo26(config, args.weights, device)
    report["model_size_mb"] = round(args.weights.stat().st_size / 1024**2, 3)
    output = resolve(config["paths"]["reports"]) / f"{args.backend}_{args.weights.stem}_benchmark.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
