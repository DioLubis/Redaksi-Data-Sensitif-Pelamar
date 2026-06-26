from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from PIL import Image

from common import CLASS_TO_ID, ImageSize, ensure_dir, write_yolo_label, xyxy_to_yolo


def parse_wider_annotation(annotation_file: Path) -> list[tuple[str, list[list[float]]]]:
    lines = annotation_file.read_text(encoding="utf-8").splitlines()
    index = 0
    records: list[tuple[str, list[list[float]]]] = []

    while index < len(lines):
        image_rel = lines[index].strip()
        index += 1
        if not image_rel or not image_rel.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        if index >= len(lines):
            break
        face_count_line = lines[index].strip()
        index += 1
        try:
            face_count = int(face_count_line)
        except ValueError:
            continue
        boxes = []
        for _ in range(face_count):
            if index >= len(lines):
                break
            values = [float(v) for v in lines[index].split()]
            index += 1
            x, y, w, h = values[:4]
            if w > 0 and h > 0:
                boxes.append([x, y, x + w, y + h])
        if face_count == 0 and index < len(lines) and not lines[index].strip().lower().endswith((".jpg", ".jpeg", ".png")):
            index += 1
        records.append((image_rel, boxes))

    return records


def convert_widerface(
    annotation_file: Path,
    image_root: Path,
    output_image_dir: Path,
    output_label_dir: Path,
    margin_ratio: float,
    copy_images: bool,
) -> None:
    ensure_dir(output_image_dir)
    ensure_dir(output_label_dir)
    records = parse_wider_annotation(annotation_file)
    class_id = CLASS_TO_ID["face_photo"]

    for image_rel, face_boxes in records:
        source_path = image_root / image_rel
        if not source_path.exists():
            print(f"Missing image: {source_path}")
            continue

        with Image.open(source_path) as image:
            size = ImageSize(width=image.width, height=image.height)

        yolo_boxes = [
            box
            for box in (
                xyxy_to_yolo(
                    class_id,
                    x_min,
                    y_min,
                    x_max,
                    y_max,
                    size,
                    margin_ratio=margin_ratio,
                )
                for x_min, y_min, x_max, y_max in face_boxes
            )
            if box is not None
        ]

        safe_name = image_rel.replace("/", "__").replace("\\", "__")
        output_image_path = output_image_dir / safe_name
        output_label_path = output_label_dir / f"{Path(safe_name).stem}.txt"

        if copy_images:
            shutil.copy2(source_path, output_image_path)
        write_yolo_label(output_label_path, yolo_boxes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert WIDER FACE annotations to YOLO.")
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--images", required=True, type=Path)
    parser.add_argument("--out-images", required=True, type=Path)
    parser.add_argument("--out-labels", required=True, type=Path)
    parser.add_argument("--margin-ratio", default=0.05, type=float)
    parser.add_argument("--no-copy-images", action="store_true")
    args = parser.parse_args()

    convert_widerface(
        args.annotations,
        args.images,
        args.out_images,
        args.out_labels,
        args.margin_ratio,
        not args.no_copy_images,
    )
    print("Done.")


if __name__ == "__main__":
    main()
