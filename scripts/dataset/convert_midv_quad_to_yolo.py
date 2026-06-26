from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

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


def convert_image_to_jpg(
    source_path: Path,
    output_path: Path,
    jpeg_quality: int,
    max_long_side: int | None,
) -> ImageSize:
    ensure_dir(output_path.parent)
    with Image.open(source_path) as image:
        rgb = image.convert("RGB")
        if max_long_side and max(rgb.size) > max_long_side:
            scale = max_long_side / max(rgb.size)
            rgb = rgb.resize(
                (round(rgb.width * scale), round(rgb.height * scale)),
                Image.Resampling.LANCZOS,
            )
        rgb.save(output_path, quality=jpeg_quality, optimize=True)
        return ImageSize(width=rgb.width, height=rgb.height)


def evenly_spaced(items: list[Path], limit: int | None) -> Iterable[Path]:
    if limit is None or len(items) <= limit:
        return items
    indices = [round(index * (len(items) - 1) / (limit - 1)) for index in range(limit)]
    return [items[index] for index in indices]


def convert_midv_quad(
    data_root: Path,
    output_image_dir: Path,
    output_label_dir: Path,
    split_prefix: str,
    margin_ratio: float,
    document_ids: set[str] | None,
    max_images_per_document: int | None,
    jpeg_quality: int,
    max_long_side: int | None,
) -> tuple[int, int]:
    ensure_dir(output_image_dir)
    ensure_dir(output_label_dir)
    class_id = CLASS_TO_ID["id_card"]
    converted = 0
    skipped = 0

    documents: dict[str, list[Path]] = {}
    for json_path in sorted(data_root.rglob("ground_truth/**/*.json")):
        document_id = json_path.parents[2].name
        if document_ids and document_id not in document_ids:
            continue
        documents.setdefault(document_id, []).append(json_path)

    for document_id, json_paths in documents.items():
        for json_path in evenly_spaced(json_paths, max_images_per_document):
            data = json.loads(json_path.read_text(encoding="utf-8"))
            quad = data.get("quad")
            if not quad:
                skipped += 1
                continue

            source_image = find_image_for_ground_truth(data_root, json_path)
            if source_image is None:
                skipped += 1
                continue

            view_name = json_path.parent.name
            output_stem = f"{split_prefix}_midv_{document_id}_{view_name}_{json_path.stem}"
            output_image_path = output_image_dir / f"{output_stem}.jpg"
            output_label_path = output_label_dir / f"{output_stem}.txt"

            if output_image_path.exists() and output_label_path.exists():
                continue

            image_size = convert_image_to_jpg(
                source_image,
                output_image_path,
                jpeg_quality,
                max_long_side,
            )
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
    parser.add_argument(
        "--documents",
        nargs="+",
        help="MIDV document folder names to include. Omit to include every completed document.",
    )
    parser.add_argument(
        "--max-images-per-document",
        type=int,
        help="Deterministically retain this many frames from each document template.",
    )
    parser.add_argument("--jpeg-quality", default=85, type=int)
    parser.add_argument(
        "--max-long-side",
        default=1600,
        type=int,
        help="Resize larger images before saving. Set 0 to preserve original size.",
    )
    args = parser.parse_args()

    converted, skipped = convert_midv_quad(
        args.data_root,
        args.out_images,
        args.out_labels,
        args.split_prefix,
        args.margin_ratio,
        set(args.documents) if args.documents else None,
        args.max_images_per_document,
        args.jpeg_quality,
        args.max_long_side or None,
    )
    print(f"Converted {converted} MIDV image(s). Skipped {skipped}.")


if __name__ == "__main__":
    main()
