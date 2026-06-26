from __future__ import annotations

from collections import Counter
from time import perf_counter

from privacy_shield.schemas import Detection


def build_privacy_report(detections: list[Detection], processing_started: float, profile: dict) -> dict:
    counts = Counter(item.category for item in detections)
    critical = sum(item.severity == "critical" for item in detections)
    return {
        "schema_version": "1.0",
        "report_type": "privacy_risk_report",
        "risk_level": "critical" if critical else ("high" if detections else "low"),
        "detection_count": len(detections),
        "detections_by_category": dict(counts),
        "redaction_application_rate": 1.0 if detections else None,
        "redaction_success_rate": None,
        "sensitive_data_leakage_rate": None,
        "over_redaction_rate": None,
        "ocr_pii_detection_accuracy": None,
        "gemini_safe_payload_pass": profile.get("privacy_status", {}).get("raw_document_included") is False and profile.get("privacy_status", {}).get("pii_values_included") is False,
        "processing_time_ms": round((perf_counter() - processing_started) * 1000, 2),
        "privacy_notice": "Report excludes raw OCR text and PII values.",
    }
