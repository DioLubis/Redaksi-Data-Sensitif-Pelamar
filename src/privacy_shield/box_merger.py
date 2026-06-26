from __future__ import annotations

from privacy_shield.schemas import Box, Detection


def _iou(left: Box, right: Box) -> float:
    overlap = Box(max(left.x1, right.x1), max(left.y1, right.y1), min(left.x2, right.x2), min(left.y2, right.y2)).area()
    union = left.area() + right.area() - overlap
    return 0 if union == 0 else overlap / union


def add_margin(box: Box, image_size: tuple[int, int], ratio: float = 0.04) -> Box:
    width, height = image_size
    margin_x = round((box.x2 - box.x1) * ratio)
    margin_y = round((box.y2 - box.y1) * ratio)
    return Box(max(0, box.x1 - margin_x), max(0, box.y1 - margin_y), min(width, box.x2 + margin_x), min(height, box.y2 + margin_y))


def merge_boxes(detections: list[Detection], image_size: tuple[int, int], iou_threshold: float = 0.25) -> list[Detection]:
    ordered = sorted(detections, key=lambda item: item.confidence, reverse=True)
    merged: list[Detection] = []
    for candidate in ordered:
        candidate = Detection(**{**candidate.__dict__, "box": add_margin(candidate.box, image_size)})
        same_page_overlap = [item for item in merged if item.page_number == candidate.page_number and _iou(item.box, candidate.box) >= iou_threshold]
        if not same_page_overlap:
            merged.append(candidate)
            continue
        current = same_page_overlap[0]
        union_box = Box(min(current.box.x1, candidate.box.x1), min(current.box.y1, candidate.box.y1), max(current.box.x2, candidate.box.x2), max(current.box.y2, candidate.box.y2))
        merged.remove(current)
        merged.append(Detection(**{**current.__dict__, "box": union_box, "confidence": max(current.confidence, candidate.confidence)}))
    return sorted(merged, key=lambda item: (item.page_number, item.box.y1, item.box.x1))
