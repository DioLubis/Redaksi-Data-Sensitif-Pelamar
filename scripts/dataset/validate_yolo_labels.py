from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import CLASS_NAMES, IMAGE_EXTENSIONS


def validate_label_file(path: Path, num_classes: int) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 5:
            errors.append(f"{path}:{line_number}: expected 5 values, got {len(parts)}")
            continue
        try:
            class_id = int(parts[0])
            values = [float(value) for value in parts[1:]]
        except ValueError:
            errors.append(f"{path}:{line_number}: non-numeric value")
            continue
        if class_id < 0 or class_id >= num_classes:
            errors.append(f"{path}:{line_number}: class id out of range: {class_id}")
        for value in values:
            if value < 0.0 or value > 1.0:
                errors.append(f"{path}:{line_number}: normalized value out of range: {value}")
        if values[2] <= 0.0 or values[3] <= 0.0:
            errors.append(f"{path}:{line_number}: width/height must be positive")

    return errors


def find_matching_image(images_dir: Path, stem: str) -> Path | None:
    for extension in IMAGE_EXTENSIONS:
        candidate = images_dir / f"{stem}{extension}"
        if candidate.exists():
            return candidate
    matches = [p for p in images_dir.glob(f"{stem}.*") if p.suffix.lower() in IMAGE_EXTENSIONS]
    return matches[0] if matches else None


def validate_split(dataset_dir: Path, split: str) -> tuple[list[str], dict[str, int]]:
    images_dir = dataset_dir / "images" / split
    labels_dir = dataset_dir / "labels" / split
    errors: list[str] = []
    class_counts = {name: 0 for name in CLASS_NAMES}

    label_files = sorted(labels_dir.glob("*.txt"))
    image_files = sorted(p for p in images_dir.glob("*") if p.suffix.lower() in IMAGE_EXTENSIONS)
    image_stems = {p.stem for p in image_files}

    for label_path in label_files:
        errors.extend(validate_label_file(label_path, len(CLASS_NAMES)))
        if find_matching_image(images_dir, label_path.stem) is None:
            errors.append(f"{label_path}: no matching image in {images_dir}")
        for line in label_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            class_id = int(line.split()[0])
            if 0 <= class_id < len(CLASS_NAMES):
                class_counts[CLASS_NAMES[class_id]] += 1

    label_stems = {p.stem for p in label_files}
    for stem in image_stems - label_stems:
        errors.append(f"{images_dir / stem}: image has no matching label file")

    return errors, class_counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate YOLO label files.")
    parser.add_argument("--dataset", default="datasets/privacy_shield", type=Path)
    parser.add_argument("--output", type=Path, help="Optional JSON summary path.")
    args = parser.parse_args()

    all_errors: list[str] = []
    summary = {"splits": {}, "errors": []}
    for split in ["train", "val", "test"]:
        errors, class_counts = validate_split(args.dataset, split)
        all_errors.extend(errors)
        summary["splits"][split] = {"class_counts": class_counts, "error_count": len(errors)}

    summary["errors"] = all_errors
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if all_errors:
        for error in all_errors:
            print(error)
        raise SystemExit(f"Validation failed with {len(all_errors)} error(s).")

    print(json.dumps(summary, indent=2))
    print("Validation passed.")


if __name__ == "__main__":
    main()

