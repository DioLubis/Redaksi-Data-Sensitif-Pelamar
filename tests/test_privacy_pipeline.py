from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from privacy_shield.box_merger import merge_boxes
from privacy_shield.file_validator import validate_file
from privacy_shield.pdf_to_image import document_to_images
from privacy_shield.pii_text_detector import detect_pii
from privacy_shield.pipeline import assert_gemini_safe, run_privacy_pipeline
from privacy_shield.privacy_report_generator import build_privacy_report
from privacy_shield.redaction_engine import apply_redactions
from privacy_shield.sanitized_profile_builder import build_sanitized_profile
from privacy_shield.schemas import Box, Detection, OCRToken, PageOCR
from privacy_shield.yolo_detector import YOLODetector


def token(text: str, x: int, y: int, line: int) -> OCRToken:
    return OCRToken(text, Box(x, y, x + 50, y + 20), 0.99, (1, 1, line))


def test_file_validation_rejects_unsupported_file(tmp_path: Path) -> None:
    path = tmp_path / "input.txt"
    path.write_text("dummy", encoding="utf-8")
    with pytest.raises(ValueError):
        validate_file(path)


def test_image_validation_and_preprocessing(tmp_path: Path) -> None:
    source = tmp_path / "input.png"
    Image.new("RGB", (20, 20), "white").save(source)
    assert validate_file(source).media_type == "image"
    pages = document_to_images(source, tmp_path / "pages")
    assert len(pages) == 1 and pages[0].is_file()


def test_pii_detection_never_exposes_value() -> None:
    ocr = PageOCR(1, [token("contact@example.test", 10, 10, 1), token("Skills", 10, 40, 2)])
    detections = detect_pii(ocr)
    assert detections[0].category == "email"
    assert detections[0].evidence_hash
    assert "example" not in json.dumps(detections[0].to_dict())


def test_box_merger_applies_margin_and_merges_overlap() -> None:
    left = Detection(1, "signature", "visual", 0.9, Box(10, 10, 50, 50))
    right = Detection(1, "email", "ocr_regex", 0.99, Box(35, 10, 70, 50))
    merged = merge_boxes([left, right], (100, 100))
    assert len(merged) == 1
    assert merged[0].box.x1 < 10
    assert merged[0].box.x2 > 70


def test_redaction_black_box(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    target = tmp_path / "redacted.png"
    Image.new("RGB", (100, 100), "white").save(source)
    apply_redactions(source, [Detection(1, "signature", "visual", 1.0, Box(10, 10, 40, 40))], target)
    assert Image.open(target).getpixel((20, 20)) == (0, 0, 0)


def test_gemini_guard_rejects_pii() -> None:
    with pytest.raises(ValueError):
        assert_gemini_safe({"skills": ["user@example.test"], "privacy_status": {"raw_document_included": False}})


def test_profile_builder_and_report_exclude_pii_values() -> None:
    ocr = PageOCR(1, [token("Skills", 0, 0, 1), token("Python", 0, 20, 2), token("user@example.test", 0, 40, 3)])
    pii = detect_pii(ocr)
    profile = build_sanitized_profile([ocr], pii)
    report = build_privacy_report(pii, 0, profile)
    assert profile["skills"] == ["Python"]
    assert report["detections_by_category"]["email"] == 1
    assert "example" not in json.dumps(report)


def test_yolo_detector_requires_real_weight(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        YOLODetector("yolo26", tmp_path / "missing.pt")


class DummyDetector:
    def detect(self, image_path: str | Path, page_number: int) -> list[Detection]:
        return [Detection(page_number, "signature", "visual", 0.95, Box(150, 20, 230, 50))]


class DummyOCR:
    def extract(self, image_path: str | Path, page_number: int) -> PageOCR:
        return PageOCR(page_number, [token("Skills", 10, 10, 1), token("Python", 10, 35, 2), token("contact@example.test", 10, 70, 3)])


def test_end_to_end_pipeline_outputs_only_sanitized_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "dummy.png"
    Image.new("RGB", (300, 120), "white").save(source)
    result = run_privacy_pipeline(source, tmp_path / "output", DummyDetector(), DummyOCR())
    assert Path(result["redacted_pdf"]).is_file()
    assert len(result["redacted_pages"]) == 1
    assert result["profile"]["skills"] == ["Python"]
    assert "example" not in json.dumps(result["ocr"])
    assert result["report"]["gemini_safe_payload_pass"] is True
    assert not (tmp_path / "output" / "work_pages").exists()
