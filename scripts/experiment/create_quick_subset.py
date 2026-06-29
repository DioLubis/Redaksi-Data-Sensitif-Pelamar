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


def build_split(source: Path, target: Path, split: str, per_class: int, max_total: int) -> dict[str, int]:
    source_images = source / "images" / split
    source_labels = source / "labels" / split
    output_images = target / "images" / split
    output_labels = target / "labels" / split
    output_images.mkdir(parents=True, exist_ok=True)
    output_labels.mkdir(parents=True, exist_ok=True)
    selected: list[Path] = []
    selected_set: set[Path] = set()
    labels = sorted(source_labels.glob("*.txt"))
    candidates_by_class: dict[int, list[Path]] = {}
    for class_id, class_name in enumerate(CLASS_NAMES):
        candidates = [path for path in labels if class_id in label_classes(path) and image_for_label(source_images, path)]
        candidates_by_class[class_id] = candidates
        if len(candidates) < per_class:
            raise ValueError(f"Not enough {class_name} images in {split}: {len(candidates)} < {per_class}")
        for label in candidates[:per_class]:
            if label not in selected_set:
                selected.append(label)
                selected_set.add(label)
    cursor = {class_id: per_class for class_id in range(len(CLASS_NAMES))}
    while len(selected) < max_total:
        added = False
        for class_id in range(len(CLASS_NAMES)):
            candidates = candidates_by_class[class_id]
            while cursor[class_id] < len(candidates) and candidates[cursor[class_id]] in selected_set:
                cursor[class_id] += 1
            if cursor[class_id] >= len(candidates):
                continue
            label = candidates[cursor[class_id]]
            selected.append(label)
            selected_set.add(label)
            cursor[class_id] += 1
            added = True
            if len(selected) >= max_total:
                break
        if not added:
            break
    counts = {class_name: 0 for class_name in CLASS_NAMES}
    for label in selected:
        image = image_for_label(source_images, label)
        assert image is not None
        shutil.copy2(image, output_images / image.name)
        shutil.copy2(label, output_labels / label.name)
        for class_id in label_classes(label):
            if 0 <= class_id < len(CLASS_NAMES):
                counts[CLASS_NAMES[class_id]] += 1
    return {"total_images": len(selected), **counts}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a deterministic medium subset for YOLO training.")
    parser.add_argument("--source", default="datasets/privacy_shield", type=Path)
    parser.add_argument("--output", default="artifacts/quick_training_dataset", type=Path)
    parser.add_argument("--train-per-class", default=100, type=int)
    parser.add_argument("--val-per-class", default=20, type=int)
    parser.add_argument("--test-per-class", default=20, type=int)
    parser.add_argument("--train-max-total", default=800, type=int)
    parser.add_argument("--val-max-total", default=150, type=int)
    parser.add_argument("--test-max-total", default=150, type=int)
    args = parser.parse_args()
    if args.output.exists():
        shutil.rmtree(args.output)
    summaries = {
        "train": build_split(args.source, args.output, "train", args.train_per_class, args.train_max_total),
        "val": build_split(args.source, args.output, "val", args.val_per_class, args.val_max_total),
        "test": build_split(args.source, args.output, "test", args.test_per_class, args.test_max_total),
    }
    data = {"path": str(args.output.resolve()), "train": "images/train", "val": "images/val", "test": "images/test", "nc": len(CLASS_NAMES), "names": {index: name for index, name in enumerate(CLASS_NAMES)}}
    (args.output / "data.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print({"output": str(args.output), "per_class": summaries})


if __name__ == "__main__":
    main()
