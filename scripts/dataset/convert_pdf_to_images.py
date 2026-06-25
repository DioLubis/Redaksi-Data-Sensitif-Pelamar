from __future__ import annotations

import argparse
from pathlib import Path


def convert_pdf_to_images(pdf_path: Path, output_dir: Path, dpi: int) -> list[Path]:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise SystemExit(
            "PyMuPDF is required. Install with: pip install pymupdf"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    scale = dpi / 72.0
    matrix = fitz.Matrix(scale, scale)

    with fitz.open(pdf_path) as doc:
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            output_path = output_dir / f"{pdf_path.stem}_page_{page_index + 1:04d}.png"
            pix.save(output_path)
            written.append(output_path)

    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert PDF files to page images.")
    parser.add_argument("--input", required=True, type=Path, help="PDF file or folder.")
    parser.add_argument("--output", required=True, type=Path, help="Output image folder.")
    parser.add_argument("--dpi", default=200, type=int, help="Render DPI.")
    args = parser.parse_args()

    pdf_paths = [args.input] if args.input.is_file() else sorted(args.input.rglob("*.pdf"))
    if not pdf_paths:
        raise SystemExit("No PDF files found.")

    total = 0
    for pdf_path in pdf_paths:
        target_dir = args.output / pdf_path.stem if args.input.is_dir() else args.output
        written = convert_pdf_to_images(pdf_path, target_dir, args.dpi)
        total += len(written)
        print(f"{pdf_path}: {len(written)} page images")

    print(f"Done. Wrote {total} image(s).")


if __name__ == "__main__":
    main()

