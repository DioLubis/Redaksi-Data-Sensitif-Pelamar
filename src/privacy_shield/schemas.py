from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Literal

Source = Literal["visual", "ocr_regex", "opencv_face_fallback"]


@dataclass(frozen=True)
class Box:
    x1: int
    y1: int
    x2: int
    y2: int

    def area(self) -> int:
        return max(0, self.x2 - self.x1) * max(0, self.y2 - self.y1)

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class Detection:
    page_number: int
    category: str
    source: Source
    confidence: float
    box: Box
    severity: Literal["high", "critical"] = "high"
    evidence_hash: str | None = None
    redaction_method: str = "black_box"

    def to_dict(self) -> dict:
        return {
            "page_number": self.page_number,
            "category": self.category,
            "source": self.source,
            "confidence": round(self.confidence, 4),
            "severity": self.severity,
            "box": self.box.to_dict(),
            "evidence_hash": self.evidence_hash,
            "redaction_method": self.redaction_method,
        }


@dataclass(frozen=True)
class OCRToken:
    text: str
    box: Box
    confidence: float
    line_id: tuple[int, int, int]

    def evidence_hash(self) -> str:
        return sha256(self.text.encode("utf-8")).hexdigest()[:16]

    def safe_dict(self, redact_text: bool = True) -> dict:
        return {
            "text": "[REDACTED_TOKEN]" if redact_text else self.text,
            "text_hash": self.evidence_hash(),
            "box": self.box.to_dict(),
            "confidence": round(self.confidence, 4),
            "line_id": list(self.line_id),
        }


@dataclass
class PageOCR:
    page_number: int
    tokens: list[OCRToken] = field(default_factory=list)

    def safe_dict(self) -> dict:
        return {"page_number": self.page_number, "tokens": [token.safe_dict() for token in self.tokens]}
