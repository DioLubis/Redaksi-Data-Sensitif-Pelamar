from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image

from common import CLASS_TO_ID, ensure_dir


def save_jpeg(source: Path, destination: Path, quality: int, max_long_side: int) -> None:
    ensure_dir(destination.parent)
    with Image.open(source) as image:
        rgb = image.convert("RGB")
        if max(rgb.size) > max_long_side:
            scale = max_long_side / max(rgb.size)
            rgb = rgb.resize(
                (round(rgb.width * scale), round(rgb.height * scale)),
                Image.Resampling.LANCZOS,
            )
        rgb.save(destination, quality=quality, optimize=True)


def remap_label(source: Path, destination: Path, target_class_id: int) -> bool:
    lines: list[str] = []
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        parts = raw_line.split()
        if len(parts) != 5:
            return False
        try:
            coordinates = [float(value) for value in parts[1:]]
        except ValueError:
            return False
        if not all(0.0 <= value <= 1.0 for value in coordinates):
            return False
        lines.append(f"{target_class_id} " + " ".join(f"{value:.6f}" for value in coordinates))
    if not lines:
        return False
    ensure_dir(destination.parent)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def import_split(
    source_images: Path,
    source_labels: Path,
    out_images: Path,
    out_labels: Path,
    output_prefix: str,
    target_class_id: int,
    quality: int,
    max_long_side: int,
    start_index: int,
    limit: int | None,
) -> tuple[int, int]:
    imported = 0
    skipped = 0
    pairs = [
        image_path
        for image_path in sorted(path for path in source_images.iterdir() if path.is_file())
        if (source_labels / f"{image_path.stem}.txt").exists()
    ]
    selected_pairs = pairs[start_index : start_index + limit if limit else None]
    skipped += len(pairs) - len(selected_pairs)
    for image_path in selected_pairs:
        source_label = source_labels / f"{image_path.stem}.txt"
        if not source_label.exists():
            skipped += 1
            continue
        stem = f"{output_prefix}_{image_path.stem}"
        destination_image = out_images / f"{stem}.jpg"
        destination_label = out_labels / f"{stem}.txt"
        if destination_image.exists() and destination_label.exists():
            continue
        if not remap_label(source_label, destination_label, target_class_id):
            destination_label.unlink(missing_ok=True)
            skipped += 1
            continue
        save_jpeg(image_path, destination_image, quality, max_long_side)
        imported += 1
    return imported, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a single-class YOLO source into Privacy Shield labels.")
    parser.add_argument("--source-images", required=True, type=Path)
    parser.add_argument("--source-labels", required=True, type=Path)
    parser.add_argument("--out-images", required=True, type=Path)
    parser.add_argument("--out-labels", required=True, type=Path)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--target-class", required=True, choices=CLASS_TO_ID)
    parser.add_argument("--jpeg-quality", default=85, type=int)
    parser.add_argument("--max-long-side", default=1600, type=int)
    parser.add_argument("--start-index", default=0, type=int)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    imported, skipped = import_split(
        args.source_images,
        args.source_labels,
        args.out_images,
        args.out_labels,
        args.prefix,
        CLASS_TO_ID[args.target_class],
        args.jpeg_quality,
        args.max_long_side,
        args.start_index,
        args.limit,
    )
    print(f"Imported {imported} image(s). Skipped {skipped} image(s).")


if __name__ == "__main__":
    main()
