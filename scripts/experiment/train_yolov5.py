from __future__ import annotations

import argparse
import sys
import time

from common import load_config, resolve, run, select_device, write_metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Train official YOLOv5 on Privacy Shield.")
    parser.add_argument("--config", default="configs/training/privacy_shield.yaml")
    parser.add_argument("--model-size", choices=["n", "s"], default="n")
    parser.add_argument("--device")
    args = parser.parse_args()
    config = load_config(args.config)
    experiment = config["experiment"]
    repo = resolve(config["models"]["yolov5"]["repo"])
    train_script = repo / "train.py"
    if not train_script.exists():
        raise FileNotFoundError(f"YOLOv5 repository is missing: {repo}. Clone it before training.")
    model = config["models"]["yolov5"][args.model_size]
    device = select_device(experiment["device"], args.device)
    name = f"yolov5{args.model_size}_seed{experiment['seed']}"
    project = resolve(config["paths"]["runs"]) / "yolov5"
    output_dir = project / name
    command = [
        sys.executable, str(train_script), "--weights", model, "--data", str(resolve(experiment["data"])),
        "--img", str(experiment["image_size"]), "--epochs", str(experiment["epochs"]),
        "--batch-size", str(experiment["batch_size"]), "--device", device, "--workers", str(experiment["workers"]),
        "--optimizer", experiment["optimizer"], "--hyp", str(resolve(config["models"]["yolov5"]["hyp"])),
        "--seed", str(experiment["seed"]), "--project", str(project), "--name", name, "--exist-ok",
    ]
    write_metadata(output_dir, {"backend": "yolov5", "model": model, "device": device, "config": config})
    started = time.perf_counter()
    run(command)
    write_metadata(
        output_dir,
        {"backend": "yolov5", "model": model, "device": device, "config": config, "training_time_s": time.perf_counter() - started, "peak_gpu_memory_mb": None},
    )


if __name__ == "__main__":
    main()
