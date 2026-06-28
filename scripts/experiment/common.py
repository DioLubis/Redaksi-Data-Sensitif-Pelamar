from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    with config_path.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def resolve(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else PROJECT_ROOT / candidate


def project_python() -> Path:
    scripts_dir = "Scripts" if os.name == "nt" else "bin"
    executable = "python.exe" if os.name == "nt" else "python"
    return PROJECT_ROOT / ".venv" / scripts_dir / executable


def ensure_project_python() -> None:
    expected = project_python()
    if not expected.exists():
        return
    current = Path(sys.executable).resolve()
    if current == expected.resolve():
        return
    os.execv(str(expected), [str(expected), *sys.argv])


def python_executable() -> str:
    expected = project_python()
    return str(expected) if expected.exists() else sys.executable


def runtime_data_config(data_path: str | Path) -> Path:
    source = resolve(data_path)
    with source.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    dataset_root = Path(data.get("path", source.parent))
    if not dataset_root.is_absolute():
        dataset_root = resolve(dataset_root)
    data["path"] = str(dataset_root)
    output = PROJECT_ROOT / "experiments" / "runtime" / f"{source.stem}_absolute.yaml"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, sort_keys=False, allow_unicode=True)
    return output


def select_device(configured_device: str, override: str | None) -> str:
    requested_device = override or configured_device
    if requested_device != "auto":
        validate_device(requested_device)
        return requested_device
    try:
        import torch

        return "0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def validate_device(device: str) -> None:
    normalized = device.strip().lower()
    if normalized in {"", "cpu"}:
        return
    if not _is_cuda_device_request(normalized):
        return
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            f"CUDA device '{device}' was requested, but PyTorch is not installed. "
            "Install the training requirements first."
        ) from exc
    if torch.cuda.is_available() and torch.cuda.device_count() >= _requested_cuda_count(normalized):
        return
    raise RuntimeError(
        f"CUDA device '{device}' was requested, but this Python environment cannot see a usable CUDA GPU.\n"
        f"{_torch_device_summary(torch)}\n"
        "If you have an NVIDIA GPU, install the CUDA build of PyTorch inside this project's .venv, for example:\n"
        "  python -m pip uninstall -y torch torchvision torchaudio\n"
        "  python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128\n"
        "Then verify with:\n"
        "  python -c \"import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())\""
    )


def _is_cuda_device_request(device: str) -> bool:
    if device.startswith("cuda"):
        return True
    return all(part.isdigit() for part in device.split(","))


def _requested_cuda_count(device: str) -> int:
    if device.startswith("cuda"):
        return 1
    return len([part for part in device.split(",") if part])


def _torch_device_summary(torch: Any) -> str:
    version_cuda = getattr(torch.version, "cuda", None)
    return (
        f"torch.__version__={torch.__version__}, "
        f"torch.version.cuda={version_cuda}, "
        f"torch.cuda.is_available()={torch.cuda.is_available()}, "
        f"torch.cuda.device_count()={torch.cuda.device_count()}"
    )


def write_metadata(output_dir: Path, payload: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        **payload,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    print("Running:", " ".join(command))
    return subprocess.run(command, check=True, text=True)


def read_last_metrics_csv(path: Path) -> dict[str, float]:
    import pandas as pd

    frame = pd.read_csv(path)
    row = frame.iloc[-1].to_dict()
    aliases = {
        "precision": ["metrics/precision(B)", "metrics/precision"],
        "recall": ["metrics/recall(B)", "metrics/recall"],
        "map50": ["metrics/mAP50(B)", "metrics/mAP_0.5"],
        "map50_95": ["metrics/mAP50-95(B)", "metrics/mAP_0.5:0.95"],
    }
    metrics: dict[str, float] = {}
    for key, candidates in aliases.items():
        for candidate in candidates:
            if candidate in row:
                metrics[key] = float(row[candidate])
                break
    precision = metrics.get("precision", 0.0)
    recall = metrics.get("recall", 0.0)
    metrics["f1"] = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return metrics
