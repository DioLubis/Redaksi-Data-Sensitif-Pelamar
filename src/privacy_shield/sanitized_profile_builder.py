from __future__ import annotations

from collections import defaultdict

from privacy_shield.schemas import Detection, PageOCR

SAFE_SECTIONS = {"skills": ("skill", "kompetensi", "keahlian"), "experience": ("experience", "pengalaman", "employment"), "education": ("education", "pendidikan"), "certifications": ("certification", "sertification", "sertifikat")}


def _lines(ocr_pages: list[PageOCR]) -> list[str]:
    grouped = defaultdict(list)
    for page in ocr_pages:
        for token in page.tokens:
            grouped[(page.page_number, token.line_id)].append(token.text)
    return [" ".join(tokens).strip() for _, tokens in sorted(grouped.items())]


def build_sanitized_profile(ocr_pages: list[PageOCR], pii_detections: list[Detection]) -> dict:
    blocked_hashes = {item.evidence_hash for item in pii_detections if item.evidence_hash}
    sections = {key: [] for key in SAFE_SECTIONS}
    current_section: str | None = None
    for line in _lines(ocr_pages):
        line_hash = __import__("hashlib").sha256(line.encode("utf-8")).hexdigest()[:16]
        if line_hash in blocked_hashes:
            continue
        lowered = line.lower()
        heading = next((name for name, hints in SAFE_SECTIONS.items() if any(hint in lowered for hint in hints) and len(line) < 80), None)
        if heading:
            current_section = heading
            continue
        if current_section and line and len(line) <= 500:
            sections[current_section].append(line)
    return {
        "schema_version": "1.0",
        "profile_type": "sanitized_candidate_profile",
        "skills": sections["skills"],
        "experience": sections["experience"],
        "education": sections["education"],
        "certifications": sections["certifications"],
        "privacy_status": {"raw_document_included": False, "pii_values_included": False},
    }
