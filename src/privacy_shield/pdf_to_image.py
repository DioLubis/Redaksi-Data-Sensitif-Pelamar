from __future__ import annotations

from pathlib import Path

from PIL import Image


def document_to_images(input_path: str | Path, output_dir: str | Path, dpi: int = 200, max_pages: int = 20) -> list[Path]:
    source = Path(input_path)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        page_path = target / "page_001.png"
        with Image.open(source) as image:
            image.convert("RGB").save(page_path)
        return [page_path]
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF processing. Install pymupdf.") from exc
    document = fitz.open(source)
    if document.page_count > max_pages:
        raise ValueError("PDF exceeds the configured page limit.")
    scale = dpi / 72
    pages = []
    for index, page in enumerate(document):
        pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        page_path = target / f"page_{index + 1:03d}.png"
        pixmap.save(page_path)
        pages.append(page_path)
    document.close()
    return pages
