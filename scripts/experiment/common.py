from __future__ import annotations

import json
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


def select_device(configured_device: str, override: str | None) -> str:
    if override:
        return override
    if configured_device != "auto":
        return configured_device
    try:
        import torch

        return "0" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


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
