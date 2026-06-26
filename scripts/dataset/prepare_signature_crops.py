from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image, ImageChops

from common import CLASS_TO_ID, ImageSize, ensure_dir, write_yolo_label, xyxy_to_yolo

WRITER_PATTERN = re.compile(r"(?:original|forgeries)_(\d+)_")


def split_for_writer(path: Path) -> str:
    match = WRITER_PATTERN.search(path.name)
    if match is None:
        raise ValueError(f"Cannot determine writer id from {path.name}")
    writer_id = int(match.group(1))
    if writer_id <= 40:
        return "train"
    if writer_id <= 48:
        return "val"
    return "test"


def ink_bbox(image: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    rgb = image.convert("RGB")
    background = Image.new("RGB", rgb.size, "white")
    difference = ImageChops.difference(rgb, background).convert("L")
    mask = difference.point(lambda value: 255 if value >= threshold else 0)
    return mask.getbbox()


def process_image(
    source: Path,
    output_image: Path,
    output_label: Path,
    threshold: int,
    margin_ratio: float,
    jpeg_quality: int,
) -> bool:
    with Image.open(source) as image:
        rgb = image.convert("RGB")
        bbox = ink_bbox(rgb, threshold)
        if bbox is None:
            return False
        box = xyxy_to_yolo(
            CLASS_TO_ID["signature"],
            *bbox,
            ImageSize(rgb.width, rgb.height),
            margin_ratio=margin_ratio,
        )
        if box is None:
            return False
        ensure_dir(output_image.parent)
        rgb.save(output_image, quality=jpeg_quality, optimize=True)
        write_yolo_label(output_label, [box])
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare cropped signature images with automatic ink bounding boxes.")
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--threshold", default=25, type=int)
    parser.add_argument("--margin-ratio", default=0.08, type=float)
    parser.add_argument("--jpeg-quality", default=85, type=int)
    args = parser.parse_args()

    prepared = 0
    skipped = 0
    for image_path in sorted(args.source.rglob("*.png")):
        try:
            split = split_for_writer(image_path)
        except ValueError:
            skipped += 1
            continue
        image_dir = args.dataset_root / "images" / split
        label_dir = args.dataset_root / "labels" / split
        stem = f"signature_{image_path.parent.name}_{image_path.stem}"
        output_image = image_dir / f"{stem}.jpg"
        output_label = label_dir / f"{stem}.txt"
        if output_image.exists() and output_label.exists():
            continue
        if process_image(
            image_path,
            output_image,
            output_label,
            args.threshold,
            args.margin_ratio,
            args.jpeg_quality,
        ):
            prepared += 1
        else:
            skipped += 1
    print(f"Prepared {prepared} signature image(s). Skipped {skipped} image(s).")


if __name__ == "__main__":
    main()
