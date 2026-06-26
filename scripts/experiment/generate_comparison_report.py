from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from common import load_config, resolve


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a CSV, Markdown table, and metric plot from evaluation reports.")
    parser.add_argument("--config", default="configs/training/privacy_shield.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    reports_dir = resolve(config["paths"]["reports"])
    evaluations = [load_json(path) for path in reports_dir.glob("*_test.json")]
    benchmarks = {item["backend"]: item for path in reports_dir.glob("*_benchmark.json") for item in [load_json(path)]}
    if not evaluations:
        raise FileNotFoundError(f"No evaluation reports found in {reports_dir}")
    rows = []
    for evaluation in evaluations:
        benchmark = benchmarks.get(evaluation["backend"], {})
        rows.append({
            "model": evaluation["backend"], "precision": evaluation.get("precision"), "recall": evaluation.get("recall"),
            "f1": evaluation.get("f1"), "map50": evaluation.get("map50"), "map50_95": evaluation.get("map50_95"),
            "inference_ms_per_image": benchmark.get("inference_ms_per_image"), "fps": benchmark.get("fps"),
            "model_size_mb": benchmark.get("model_size_mb"),
        })
    frame = pd.DataFrame(rows).sort_values("model")
    frame.to_csv(reports_dir / "comparison.csv", index=False)
    (reports_dir / "comparison.md").write_text(frame.to_markdown(index=False) + "\n", encoding="utf-8")
    frame.set_index("model")[["precision", "recall", "f1", "map50", "map50_95"]].plot.bar(figsize=(10, 5), ylim=(0, 1), rot=0)
    plt.ylabel("score")
    plt.tight_layout()
    plt.savefig(reports_dir / "comparison_metrics.png", dpi=160)
    print(frame.to_markdown(index=False))


if __name__ == "__main__":
    main()
