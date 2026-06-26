from __future__ import annotations

import re
from collections import defaultdict

from privacy_shield.schemas import Box, Detection, PageOCR

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE = re.compile(r"(?<!\w)(?:\+?62|0)[\d\s().-]{8,}(?!\w)")
ID_NUMBER = re.compile(r"\b\d{12,18}\b")
ADDRESS_HINT = re.compile(r"\b(?:jalan|jl\.?|street|st\.?|avenue|ave\.?|kecamatan|kelurahan|kota|kabupaten|province)\b", re.IGNORECASE)


def _line_boxes(ocr: PageOCR) -> dict[tuple[int, int, int], tuple[str, Box]]:
    grouped: dict[tuple[int, int, int], list] = defaultdict(list)
    for token in ocr.tokens:
        grouped[token.line_id].append(token)
    result = {}
    for line_id, tokens in grouped.items():
        text = " ".join(token.text for token in tokens)
        result[line_id] = (text, Box(min(t.box.x1 for t in tokens), min(t.box.y1 for t in tokens), max(t.box.x2 for t in tokens), max(t.box.y2 for t in tokens)))
    return result


def detect_pii(ocr: PageOCR) -> list[Detection]:
    detections: list[Detection] = []
    for text, box in _line_boxes(ocr).values():
        normalized_text = re.sub(r"\s*([@.])\s*", r"\1", text)
        category = None
        severity = "high"
        if EMAIL.search(normalized_text):
            category = "email"
        elif PHONE.search(normalized_text):
            category = "phone_number"
        elif ID_NUMBER.search(normalized_text):
            category, severity = "document_number", "critical"
        elif ADDRESS_HINT.search(normalized_text):
            category = "address"
        if category:
            evidence_hash = __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()[:16]
            detections.append(Detection(ocr.page_number, category, "ocr_regex", 0.99, box, severity, evidence_hash, "black_box"))
    return detections
