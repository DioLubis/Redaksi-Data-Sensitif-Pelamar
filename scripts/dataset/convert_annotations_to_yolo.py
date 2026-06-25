from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from common import CLASS_TO_ID, ImageSize, ensure_dir, write_yolo_label, xyxy_to_yolo


def load_class_map(path: Path | None) -> dict[str, str]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Class map must be a JSON object: source_class -> target_class")
    return {str(k): str(v) for k, v in data.items()}


def image_size(path: Path) -> ImageSize:
    with Image.open(path) as image:
        return ImageSize(width=image.width, height=image.height)


def convert_coco(
    annotation_path: Path,
    image_root: Path,
    output_image_dir: Path,
    output_label_dir: Path,
    class_map: dict[str, str],
    margin_ratio: float,
    copy_images: bool,
) -> None:
    coco = json.loads(annotation_path.read_text(encoding="utf-8"))
    categories = {item["id"]: item["name"] for item in coco.get("categories", [])}
    images = {item["id"]: item for item in coco.get("images", [])}
    grouped: dict[int, list[dict]] = {}

    for ann in coco.get("annotations", []):
        grouped.setdefault(ann["image_id"], []).append(ann)

    for image_id, image_info in images.items():
        source_path = image_root / image_info["file_name"]
        if not source_path.exists():
            print(f"Missing image: {source_path}")
            continue

        size = ImageSize(width=int(image_info["width"]), height=int(image_info["height"]))
        boxes = []
        for ann in grouped.get(image_id, []):
            source_class = categories.get(ann["category_id"])
            target_class = class_map.get(source_class, source_class)
            if target_class not in CLASS_TO_ID:
                continue

            x, y, w, h = ann["bbox"]
            box = xyxy_to_yolo(
                CLASS_TO_ID[target_class],
                x,
                y,
                x + w,
                y + h,
                size,
                margin_ratio=margin_ratio,
            )
            if box is not None:
                boxes.append(box)

        output_image_path = output_image_dir / source_path.name
        output_label_path = output_label_dir / f"{source_path.stem}.txt"
        if copy_images:
            ensure_dir(output_image_path.parent)
            shutil.copy2(source_path, output_image_path)
        write_yolo_label(output_label_path, boxes)


def convert_voc(
    annotation_root: Path,
    image_root: Path,
    output_image_dir: Path,
    output_label_dir: Path,
    class_map: dict[str, str],
    margin_ratio: float,
    copy_images: bool,
) -> None:
    for xml_path in sorted(annotation_root.rglob("*.xml")):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        filename = root.findtext("filename")
        if not filename:
            print(f"Skipping {xml_path}: missing filename")
            continue

        source_path = image_root / filename
        if not source_path.exists():
            matches = list(image_root.rglob(filename))
            source_path = matches[0] if matches else source_path
        if not source_path.exists():
            print(f"Missing image for {xml_path}: {filename}")
            continue

        size = image_size(source_path)
        boxes = []
        for obj in root.findall("object"):
            source_class = obj.findtext("name")
            target_class = class_map.get(source_class, source_class)
            if target_class not in CLASS_TO_ID:
                continue

            bndbox = obj.find("bndbox")
            if bndbox is None:
                continue
            x_min = float(bndbox.findtext("xmin", "0"))
            y_min = float(bndbox.findtext("ymin", "0"))
            x_max = float(bndbox.findtext("xmax", "0"))
            y_max = float(bndbox.findtext("ymax", "0"))
            box = xyxy_to_yolo(
                CLASS_TO_ID[target_class],
                x_min,
                y_min,
                x_max,
                y_max,
                size,
                margin_ratio=margin_ratio,
            )
            if box is not None:
                boxes.append(box)

        output_image_path = output_image_dir / source_path.name
        output_label_path = output_label_dir / f"{source_path.stem}.txt"
        if copy_images:
            ensure_dir(output_image_path.parent)
            shutil.copy2(source_path, output_image_path)
        write_yolo_label(output_label_path, boxes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert COCO or VOC annotations to YOLO.")
    parser.add_argument("--format", choices=["coco", "voc"], required=True)
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--images", required=True, type=Path)
    parser.add_argument("--out-images", required=True, type=Path)
    parser.add_argument("--out-labels", required=True, type=Path)
    parser.add_argument("--class-map", type=Path)
    parser.add_argument("--margin-ratio", default=0.03, type=float)
    parser.add_argument("--no-copy-images", action="store_true")
    args = parser.parse_args()

    class_map = load_class_map(args.class_map)
    ensure_dir(args.out_images)
    ensure_dir(args.out_labels)

    if args.format == "coco":
        convert_coco(
            args.annotations,
            args.images,
            args.out_images,
            args.out_labels,
            class_map,
            args.margin_ratio,
            not args.no_copy_images,
        )
    else:
        convert_voc(
            args.annotations,
            args.images,
            args.out_images,
            args.out_labels,
            class_map,
            args.margin_ratio,
            not args.no_copy_images,
        )

    print("Done.")


if __name__ == "__main__":
    main()

