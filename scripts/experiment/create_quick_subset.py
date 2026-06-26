from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml

CLASS_NAMES = ["face_photo", "signature", "qr_code", "barcode", "id_card"]


def label_classes(label_path: Path) -> set[int]:
    return {int(line.split()[0]) for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()}


def image_for_label(images: Path, label: Path) -> Path | None:
    for suffix in (".jpg", ".jpeg", ".png"):
        candidate = images / f"{label.stem}{suffix}"
        if candidate.exists():
            return candidate
    return None


def build_split(source: Path, target: Path, split: str, per_class: int) -> dict[str, int]:
    source_images = source / "images" / split
    source_labels = source / "labels" / split
    output_images = target / "images" / split
    output_labels = target / "labels" / split
    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)
    selected: set[Path] = set()
    counts: dict[str, int] = {}
    labels = sorted(source_labels.glob("*.txt"))
    for class_id, class_name in enumerate(CLASS_NAMES):
        candidates = [path for path in labels if class_id in label_classes(path) and image_for_label(source_images, path)]
        if len(candidates) < per_class:
            raise ValueError(f"Not enough {class_name} images in {split}: {len(candidates)} < {per_class}")
        chosen = candidates[:per_class]
        selected.update(chosen)
        counts[class_name] = len(chosen)
    for label in selected:
        image = image_for_label(source_images, label)
        assert image is not None
        shutil.copy2(image, output_images / image.name)
        shutil.copy2(label, output_labels / label.name)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic balanced subset for CPU smoke training.")
    parser.add_argument("--source", default="datasets/privacy_shield", type=Path)
    parser.add_argument("--output", default="artifacts/quick_training_dataset", type=Path)
    parser.add_argument("--train-per-class", default=40, type=int)
    parser.add_argument("--val-per-class", default=10, type=int)
    parser.add_argument("--test-per-class", default=10, type=int)
    args = parser.parse_args()
    if args.output.exists():
        shutil.rmtree(args.output)
    summaries = {
        "train": build_split(args.source, args.output, "train", args.train_per_class),
        "val": build_split(args.source, args.output, "val", args.val_per_class),
        "test": build_split(args.source, args.output, "test", args.test_per_class),
    }
    data = {"path": str(args.output.resolve()), "train": "images/train", "val": "images/val", "test": "images/test", "nc": len(CLASS_NAMES), "names": {index: name for index, name in enumerate(CLASS_NAMES)}}
    (args.output / "data.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print({"output": str(args.output), "per_class": summaries})


if __name__ == "__main__":
    main()
