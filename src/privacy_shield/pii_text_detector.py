from __future__ import annotations

import re
from collections import defaultdict

from privacy_shield.schemas import Box, Detection, OCRToken, PageOCR

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE = re.compile(r"(?<!\w)(?:\+?62|0|8)[\d\s().-]{8,}(?!\w)")
ID_NUMBER = re.compile(r"\b\d{12,18}\b")
GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9-]+(?:/[A-Za-z0-9_.-]+)?", re.IGNORECASE)
GITHUB_LABEL = re.compile(r"\bgithub\b\s*[:\-]", re.IGNORECASE)
ADDRESS_HINT = re.compile(r"\b(?:alamat|address|domisili|location|lokasi|jalan|jl\.?|street|avenue|ave\.?|kecamatan|kelurahan|kabupaten|provinsi|province)\b", re.IGNORECASE)
ADDRESS_CONTEXT = re.compile(r"\b(?:no\.?|nomor|rt|rw|kec\.?|kel\.?|kab\.?|kota|provinsi|province|kode\s*pos|indonesia|bali|denpasar|jakarta|bandung|surabaya|yogyakarta|malang)\b", re.IGNORECASE)


def _line_tokens(ocr: PageOCR) -> dict[tuple[int, int, int], list[OCRToken]]:
    grouped: dict[tuple[int, int, int], list] = defaultdict(list)
    for token in ocr.tokens:
        grouped[token.line_id].append(token)
    return grouped


def _union_box(tokens: list[OCRToken]) -> Box:
    return Box(min(t.box.x1 for t in tokens), min(t.box.y1 for t in tokens), max(t.box.x2 for t in tokens), max(t.box.y2 for t in tokens))


def _digit_count(text: str) -> int:
    return sum(character.isdigit() for character in text)


def _evidence_hash(text: str) -> str:
    return __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()[:16]


def _email_tokens(tokens: list[OCRToken]) -> list[OCRToken]:
    selected: list[OCRToken] = []
    for index, token in enumerate(tokens):
        text = token.text
        if "@" in text or EMAIL.search(text):
            selected.append(token)
            if index + 1 < len(tokens) and "." in tokens[index + 1].text:
                selected.append(tokens[index + 1])
    return selected


def _phone_tokens(tokens: list[OCRToken]) -> list[OCRToken]:
    return [token for token in tokens if _digit_count(token.text) or token.text.strip().startswith("+")]


def _id_number_tokens(tokens: list[OCRToken]) -> list[OCRToken]:
    return [token for token in tokens if _digit_count(token.text) >= 6]


def _github_tokens(tokens: list[OCRToken]) -> list[OCRToken]:
    selected: list[OCRToken] = []
    for index, token in enumerate(tokens):
        text = token.text.strip()
        if "github.com" in text.lower():
            selected.append(token)
        elif text.lower().rstrip(":") == "github" and index + 1 < len(tokens) and not tokens[index + 1].text.strip().lower().startswith(("git,", "github,", "gitlab")):
            selected.extend(tokens[index:index + 2])
    return selected


def _address_tokens(tokens: list[OCRToken]) -> list[OCRToken]:
    return [token for token in tokens if ADDRESS_HINT.search(token.text) or ADDRESS_CONTEXT.search(token.text) or _digit_count(token.text)]


def _looks_like_address(text: str) -> bool:
    if not ADDRESS_HINT.search(text):
        return False
    return bool(ADDRESS_CONTEXT.search(text) or _digit_count(text) >= 2)


def detect_pii(ocr: PageOCR) -> list[Detection]:
    detections: list[Detection] = []
    for tokens in _line_tokens(ocr).values():
        text = " ".join(token.text for token in tokens)
        normalized_text = re.sub(r"\s*([@.])\s*", r"\1", text)
        if EMAIL.search(normalized_text):
            selected = _email_tokens(tokens) or tokens
            detections.append(Detection(ocr.page_number, "email", "ocr_regex", 0.99, _union_box(selected), "high", _evidence_hash(text), "black_box"))
            continue
        if GITHUB.search(normalized_text) or GITHUB_LABEL.search(normalized_text):
            selected = _github_tokens(tokens) or tokens
            detections.append(Detection(ocr.page_number, "github_profile", "ocr_regex", 0.99, _union_box(selected), "high", _evidence_hash(text), "black_box"))
            continue
        if PHONE.search(normalized_text):
            selected = _phone_tokens(tokens) or tokens
            detections.append(Detection(ocr.page_number, "phone_number", "ocr_regex", 0.99, _union_box(selected), "high", _evidence_hash(text), "black_box"))
            continue
        if ID_NUMBER.search(normalized_text):
            selected = _id_number_tokens(tokens) or tokens
            detections.append(Detection(ocr.page_number, "document_number", "ocr_regex", 0.99, _union_box(selected), "critical", _evidence_hash(text), "black_box"))
            continue
        if _looks_like_address(normalized_text):
            selected = _address_tokens(tokens) or tokens
            detections.append(Detection(ocr.page_number, "address", "ocr_regex", 0.9, _union_box(selected), "high", _evidence_hash(text), "black_box"))
    return detections
