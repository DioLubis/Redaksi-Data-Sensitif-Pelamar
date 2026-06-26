from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ALLOWED_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png"}


@dataclass(frozen=True)
class FileValidationResult:
    path: Path
    media_type: str
    size_bytes: int


def validate_file(path: str | Path, max_size_mb: int = 15) -> FileValidationResult:
    candidate = Path(path)
    if not candidate.is_file():
        raise FileNotFoundError("Input document does not exist.")
    suffix = candidate.suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise ValueError("Only PDF, JPG, JPEG, and PNG documents are supported.")
    size_bytes = candidate.stat().st_size
    if size_bytes > max_size_mb * 1024 * 1024:
        raise ValueError("Input document exceeds the configured size limit.")
    if suffix == ".pdf":
        if candidate.read_bytes()[:5] != b"%PDF-":
            raise ValueError("Input file does not contain a valid PDF signature.")
    else:
        try:
            from PIL import Image

            with Image.open(candidate) as image:
                image.verify()
        except Exception as exc:
            raise ValueError("Input file is not a valid image.") from exc
    return FileValidationResult(candidate, "pdf" if suffix == ".pdf" else "image", size_bytes)
