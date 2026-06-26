from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

from common import CLASS_TO_ID, ImageSize, ensure_dir, write_yolo_label, xyxy_to_yolo


def bbox_from_quad(quad: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [point[0] for point in quad]
    ys = [point[1] for point in quad]
    return min(xs), min(ys), max(xs), max(ys)


def find_image_for_ground_truth(data_root: Path, json_path: Path) -> Path | None:
    view_name = json_path.parent.name
    stem = json_path.stem
    document_root = json_path.parents[2]
    candidates = [
        document_root / "images" / view_name / f"{stem}.tif",
        document_root / "images" / view_name / f"{stem}.jpg",
        document_root / "images" / view_name / f"{stem}.png",
        data_root / f"{stem}.tif",
        data_root / f"{stem}.jpg",
        data_root / f"{stem}.png",
        data_root.parent / f"{stem}.tif",
        data_root.parent / f"{stem}.jpg",
        data_root.parent / f"{stem}.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = list(data_root.rglob(f"{stem}.*")) + list(data_root.parent.glob(f"{stem}.*"))
    for match in matches:
        if match.suffix.lower() in {".tif", ".tiff", ".jpg", ".jpeg", ".png"}:
            return match
    return None


def convert_image_to_jpg(source_path: Path, output_path: Path) -> ImageSize:
    ensure_dir(output_path.parent)
    with Image.open(source_path) as image:
        rgb = image.convert("RGB")
        rgb.save(output_path, quality=95)
        return ImageSize(width=rgb.width, height=rgb.height)


def convert_midv_quad(
    data_root: Path,
    output_image_dir: Path,
    output_label_dir: Path,
    split_prefix: str,
    margin_ratio: float,
) -> tuple[int, int]:
    ensure_dir(output_image_dir)
    ensure_dir(output_label_dir)
    class_id = CLASS_TO_ID["id_card"]
    converted = 0
    skipped = 0

    for json_path in sorted(data_root.rglob("ground_truth/**/*.json")):
        data = json.loads(json_path.read_text(encoding="utf-8"))
        quad = data.get("quad")
        if not quad:
            skipped += 1
            continue

        source_image = find_image_for_ground_truth(data_root, json_path)
        if source_image is None:
            skipped += 1
            continue

        document_id = json_path.parents[2].name
        view_name = json_path.parent.name
        output_stem = f"{split_prefix}_midv_{document_id}_{view_name}_{json_path.stem}"
        output_image_path = output_image_dir / f"{output_stem}.jpg"
        output_label_path = output_label_dir / f"{output_stem}.txt"

        image_size = convert_image_to_jpg(source_image, output_image_path)
        x_min, y_min, x_max, y_max = bbox_from_quad(quad)
        box = xyxy_to_yolo(
            class_id,
            x_min,
            y_min,
            x_max,
            y_max,
            image_size,
            margin_ratio=margin_ratio,
        )
        write_yolo_label(output_label_path, [box] if box is not None else [])
        converted += 1

    return converted, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert MIDV quad ground truth to YOLO id_card labels.")
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--out-images", required=True, type=Path)
    parser.add_argument("--out-labels", required=True, type=Path)
    parser.add_argument("--split-prefix", default="train")
    parser.add_argument("--margin-ratio", default=0.02, type=float)
    args = parser.parse_args()

    converted, skipped = convert_midv_quad(
        args.data_root,
        args.out_images,
        args.out_labels,
        args.split_prefix,
        args.margin_ratio,
    )
    print(f"Converted {converted} MIDV image(s). Skipped {skipped}.")


if __name__ == "__main__":
    main()

