from __future__ import annotations

from pathlib import Path

from privacy_shield.schemas import Box, OCRToken, PageOCR


class TesseractOCRExtractor:
    def __init__(self, language: str = "eng") -> None:
        self.language = language

    def extract(self, image_path: str | Path, page_number: int) -> PageOCR:
        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError("pytesseract and Pillow are required for OCR.") from exc
        default_windows_binary = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
        if not Path(pytesseract.pytesseract.tesseract_cmd).is_file() and default_windows_binary.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(default_windows_binary)
        try:
            data = pytesseract.image_to_data(Image.open(image_path), lang=self.language, output_type=pytesseract.Output.DICT)
        except pytesseract.TesseractNotFoundError as exc:
            raise RuntimeError("Tesseract binary is not installed or not on PATH.") from exc
        tokens: list[OCRToken] = []
        for index, raw_text in enumerate(data["text"]):
            text = raw_text.strip()
            confidence = float(data["conf"][index]) if data["conf"][index] != "-1" else 0.0
            if not text or confidence <= 0:
                continue
            x, y, width, height = (int(data[key][index]) for key in ("left", "top", "width", "height"))
            tokens.append(OCRToken(text, Box(x, y, x + width, y + height), confidence / 100, (int(data["block_num"][index]), int(data["par_num"][index]), int(data["line_num"][index]))))
        return PageOCR(page_number, tokens)
