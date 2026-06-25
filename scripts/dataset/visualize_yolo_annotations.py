from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from common import CLASS_NAMES, IMAGE_EXTENSIONS, ensure_dir


def find_images(images_dir: Path) -> list[Path]:
    return sorted(p for p in images_dir.glob("*") if p.suffix.lower() in IMAGE_EXTENSIONS)


def draw_annotation(image_path: Path, label_path: Path, output_path: Path) -> None:
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    width, height = image.size

    if label_path.exists():
        for line in label_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            class_id_text, x_text, y_text, w_text, h_text = line.split()
            class_id = int(class_id_text)
            x_center = float(x_text) * width
            y_center = float(y_text) * height
            box_w = float(w_text) * width
            box_h = float(h_text) * height
            x_min = x_center - box_w / 2.0
            y_min = y_center - box_h / 2.0
            x_max = x_center + box_w / 2.0
            y_max = y_center + box_h / 2.0
            label = CLASS_NAMES[class_id] if 0 <= class_id < len(CLASS_NAMES) else str(class_id)
            draw.rectangle([x_min, y_min, x_max, y_max], outline=(255, 0, 0), width=3)
            draw.rectangle([x_min, max(0, y_min - 18), x_min + 8 * len(label), y_min], fill=(255, 0, 0))
            draw.text((x_min + 2, max(0, y_min - 16)), label, fill=(255, 255, 255))

    ensure_dir(output_path.parent)
    image.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Visualize YOLO labels on sample images.")
    parser.add_argument("--dataset", default="datasets/privacy_shield", type=Path)
    parser.add_argument("--split", default="train", choices=["train", "val", "test"])
    parser.add_argument("--count", default=12, type=int)
    parser.add_argument("--output", default="reports/dataset/visual_samples", type=Path)
    parser.add_argument("--seed", default=42, type=int)
    args = parser.parse_args()

    images_dir = args.dataset / "images" / args.split
    labels_dir = args.dataset / "labels" / args.split
    images = find_images(images_dir)
    if not images:
        raise SystemExit(f"No images found in {images_dir}")

    random.seed(args.seed)
    sample = random.sample(images, min(args.count, len(images)))
    for image_path in sample:
        label_path = labels_dir / f"{image_path.stem}.txt"
        output_path = args.output / args.split / image_path.name
        draw_annotation(image_path, label_path, output_path)
        print(output_path)

    print("Done.")


if __name__ == "__main__":
    main()

