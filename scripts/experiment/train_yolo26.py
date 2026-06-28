from __future__ import annotations

import argparse
import time

from common import ensure_project_python, load_config, resolve, runtime_data_config, select_device, write_metadata


def main() -> None:
    ensure_project_python()
    parser = argparse.ArgumentParser(description="Train official Ultralytics YOLO26 on Privacy Shield.")
    parser.add_argument("--config", default="configs/training/privacy_shield.yaml")
    parser.add_argument("--model-size", choices=["n", "s"], default="n")
    parser.add_argument("--device")
    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--workers", type=int)
    args = parser.parse_args()
    from ultralytics import YOLO

    config = load_config(args.config)
    experiment = config["experiment"]
    batch_size = args.batch_size or experiment["batch_size"]
    workers = experiment["workers"] if args.workers is None else args.workers
    model_name = config["models"]["yolo26"][args.model_size]
    device = select_device(experiment["device"], args.device)
    name = f"yolo26{args.model_size}_seed{experiment['seed']}"
    project = resolve(config["paths"]["runs"]) / "yolo26"
    output_dir = project / name
    write_metadata(output_dir, {"backend": "yolo26", "model": model_name, "device": device, "batch_size": batch_size, "workers": workers, "config": config})
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
    except ImportError:
        torch = None
    started = time.perf_counter()
    model = YOLO(model_name)
    data_config = runtime_data_config(experiment["data"])
    model.train(
        data=str(data_config), imgsz=experiment["image_size"], epochs=experiment["epochs"],
        batch=batch_size, device=device, workers=workers, optimizer=experiment["optimizer"],
        lr0=experiment["learning_rate"], lrf=experiment["final_lr_factor"], momentum=experiment["momentum"],
        weight_decay=experiment["weight_decay"], warmup_epochs=experiment["warmup_epochs"], seed=experiment["seed"],
        deterministic=experiment["deterministic"], pretrained=experiment["pretrained"], project=str(project), name=name,
        exist_ok=True, plots=True,
    )
    peak_memory_mb = None
    if "torch" in locals() and torch is not None and torch.cuda.is_available():
        peak_memory_mb = round(torch.cuda.max_memory_allocated() / 1024**2, 3)
    write_metadata(
        output_dir,
        {"backend": "yolo26", "model": model_name, "device": device, "batch_size": batch_size, "workers": workers, "config": config, "training_time_s": time.perf_counter() - started, "peak_gpu_memory_mb": peak_memory_mb},
    )


if __name__ == "__main__":
    main()
