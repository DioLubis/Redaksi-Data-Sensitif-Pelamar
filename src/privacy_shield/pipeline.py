from __future__ import annotations

import json
import re
import tempfile
from hashlib import sha256
from pathlib import Path
from time import perf_counter
from typing import Protocol

from PIL import Image

from privacy_shield.box_merger import merge_boxes
from privacy_shield.file_validator import validate_file
from privacy_shield.pdf_to_image import document_to_images
from privacy_shield.pii_text_detector import EMAIL, GITHUB, ID_NUMBER, PHONE, detect_pii
from privacy_shield.privacy_report_generator import build_privacy_report
from privacy_shield.redaction_engine import apply_redactions, images_to_pdf
from privacy_shield.sanitized_profile_builder import build_sanitized_profile
from privacy_shield.schemas import Box, Detection, OCRToken, PageOCR


class VisualDetector(Protocol):
    def detect(self, image_path: str | Path, page_number: int) -> list[Detection]: ...


class OCRExtractor(Protocol):
    def extract(self, image_path: str | Path, page_number: int) -> PageOCR: ...


def _safe_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def assert_gemini_safe(profile: dict) -> None:
    serialized = json.dumps(profile, ensure_ascii=False)
    if EMAIL.search(serialized) or PHONE.search(serialized) or ID_NUMBER.search(serialized) or GITHUB.search(serialized):
        raise ValueError("Sanitized profile failed PII leakage guard.")
    if profile.get("privacy_status", {}).get("raw_document_included"):
        raise ValueError("Raw document flag is forbidden in Gemini payload.")


def _overlap_area(left: Box, right: Box) -> int:
    return Box(max(left.x1, right.x1), max(left.y1, right.y1), min(left.x2, right.x2), min(left.y2, right.y2)).area()


def _tokens_inside_box(tokens: list[OCRToken], box: Box) -> tuple[int, int]:
    count = 0
    area = 0
    for token in tokens:
        overlap = _overlap_area(token.box, box)
        if overlap:
            count += 1
            area += overlap
    return count, area


def filter_visual_false_positives(detections: list[Detection], ocr: PageOCR) -> list[Detection]:
    filtered: list[Detection] = []
    for detection in detections:
        if detection.source != "opencv_face_fallback":
            filtered.append(detection)
            continue
        token_count, token_area = _tokens_inside_box(ocr.tokens, detection.box)
        box_area = max(1, detection.box.area())
        if token_count >= 3 or token_area / box_area > 0.03:
            continue
        filtered.append(detection)
    return filtered


def run_privacy_pipeline(input_path: str | Path, output_dir: str | Path, detector: VisualDetector, ocr_extractor: OCRExtractor) -> dict:
    started = perf_counter()
    validation = validate_file(input_path)
    output = Path(output_dir)
    pages_dir = output / "redacted_pages"
    all_detections: list[Detection] = []
    ocr_pages: list[PageOCR] = []
    redacted_pages: list[Path] = []
    page_results = []
    with tempfile.TemporaryDirectory(prefix="privacy_pages_") as workspace:
        source_pages = document_to_images(validation.path, workspace)
        for page_number, page_path in enumerate(source_pages, start=1):
            visual = detector.detect(page_path, page_number)
            page_ocr = ocr_extractor.extract(page_path, page_number)
            visual = filter_visual_false_positives(visual, page_ocr)
            textual = detect_pii(page_ocr)
            with Image.open(page_path) as image:
                merged = merge_boxes([*visual, *textual], image.size)
            redacted_path = pages_dir / f"page_{page_number:03d}.png"
            apply_redactions(page_path, merged, redacted_path)
            all_detections.extend(merged)
            ocr_pages.append(page_ocr)
            redacted_pages.append(redacted_path)
            page_results.append({"page_number": page_number, "detections": [item.to_dict() for item in merged]})
    profile = build_sanitized_profile(ocr_pages, [item for item in all_detections if item.source == "ocr_regex"])
    assert_gemini_safe(profile)
    report = build_privacy_report(all_detections, started, profile)
    output.mkdir(parents=True, exist_ok=True)
    detection_json = {"schema_version": "1.0", "document_sha256": sha256(validation.path.read_bytes()).hexdigest(), "model_scope": "five_class_visual_detector", "pages": page_results}
    ocr_json = {"schema_version": "1.0", "contains_raw_text": False, "pages": [page.safe_dict() for page in ocr_pages]}
    _safe_json(output / "detection_result.json", detection_json)
    _safe_json(output / "ocr_result.json", ocr_json)
    _safe_json(output / "sanitized_candidate_profile.json", profile)
    _safe_json(output / "privacy_risk_report.json", report)
    redacted_pdf = images_to_pdf(redacted_pages, output / "redacted_document.pdf")
    return {"redacted_pdf": str(redacted_pdf), "redacted_pages": [str(path) for path in redacted_pages], "detections": detection_json, "ocr": ocr_json, "profile": profile, "report": report}
