from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, JpegImagePlugin  # noqa: F401

from privacy_shield.schemas import Detection


def apply_redactions(image_path: str | Path, detections: list[Detection], output_path: str | Path, default_method: str = "black_box") -> Path:
    with Image.open(image_path) as source:
        image = source.convert("RGB")
    for detection in detections:
        box = (detection.box.x1, detection.box.y1, detection.box.x2, detection.box.y2)
        method = detection.redaction_method or default_method
        if method == "blur":
            image.paste(image.crop(box).filter(ImageFilter.GaussianBlur(radius=12)), box)
        elif method == "pixelate":
            crop = image.crop(box)
            small = crop.resize((max(1, crop.width // 12), max(1, crop.height // 12)))
            image.paste(small.resize(crop.size), box)
        elif method == "replace_with_label":
            draw = ImageDraw.Draw(image)
            draw.rectangle(box, fill="black")
            draw.text((box[0] + 4, box[1] + 4), "[REDACTED]", fill="white")
        else:
            ImageDraw.Draw(image).rectangle(box, fill="black")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target)
    return target


def images_to_pdf(images: list[Path], output_path: str | Path) -> Path:
    if not images:
        raise ValueError("At least one redacted image is required to create a PDF.")
    converted = [Image.open(path).convert("RGB") for path in images]
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    converted[0].save(target, save_all=True, append_images=converted[1:])
    for image in converted:
        image.close()
    return target
