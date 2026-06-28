from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import ensure_project_python, load_config, python_executable, read_last_metrics_csv, resolve, run, runtime_data_config, select_device


def save_report(path: Path, report: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")


def evaluate_yolov5(config: dict, weights: Path, device: str) -> dict:
    repo = resolve(config["models"]["yolov5"]["repo"])
    data_config = runtime_data_config(config["experiment"]["data"])
    name = f"yolov5_{weights.stem}_test"
    project = resolve(config["paths"]["runs"]) / "evaluation"
    run([
        python_executable(), str(repo / "val.py"), "--weights", str(weights), "--data", str(data_config),
        "--img", str(config["experiment"]["image_size"]), "--batch-size", str(config["experiment"]["batch_size"]),
        "--task", "test", "--device", device, "--project", str(project), "--name", name, "--exist-ok", "--plots",
    ])
    run_dir = project / name
    metrics = read_last_metrics_csv(run_dir / "results.csv")
    return {"backend": "yolov5", "weights": str(weights), "split": "test", **metrics, "run_dir": str(run_dir)}


def evaluate_yolo26(config: dict, weights: Path, device: str) -> dict:
    from ultralytics import YOLO

    data_config = runtime_data_config(config["experiment"]["data"])
    name = f"yolo26_{weights.stem}_test"
    project = resolve(config["paths"]["runs"]) / "evaluation"
    results = YOLO(str(weights)).val(
        data=str(data_config), split="test", imgsz=config["experiment"]["image_size"],
        batch=config["experiment"]["batch_size"], device=device, project=str(project), name=name, exist_ok=True, plots=True,
    )
    precision = float(results.box.mp)
    recall = float(results.box.mr)
    return {
        "backend": "yolo26", "weights": str(weights), "split": "test", "precision": precision, "recall": recall,
        "f1": 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall),
        "map50": float(results.box.map50), "map50_95": float(results.box.map), "run_dir": str(project / name),
    }


def main() -> None:
    ensure_project_python()
    parser = argparse.ArgumentParser(description="Evaluate a YOLOv5 or YOLO26 weight file on the identical test split.")
    parser.add_argument("--backend", choices=["yolov5", "yolo26"], required=True)
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--config", default="configs/training/privacy_shield.yaml")
    parser.add_argument("--device")
    args = parser.parse_args()
    config = load_config(args.config)
    device = select_device(config["experiment"]["device"], args.device)
    report = evaluate_yolov5(config, args.weights, device) if args.backend == "yolov5" else evaluate_yolo26(config, args.weights, device)
    report_path = resolve(config["paths"]["reports"]) / f"{args.backend}_{args.weights.stem}_test.json"
    save_report(report_path, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
