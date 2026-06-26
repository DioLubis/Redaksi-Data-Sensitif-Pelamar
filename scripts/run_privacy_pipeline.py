from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from privacy_shield.ocr_extractor import TesseractOCRExtractor
from privacy_shield.pipeline import run_privacy_pipeline
from privacy_shield.yolo_detector import YOLODetector


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local Applicant Privacy Shield redaction. No raw document is sent to Gemini.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", choices=["yolov5", "yolo26"], required=True)
    parser.add_argument("--weights", required=True, type=Path)
    parser.add_argument("--yolov5-repo", type=Path, default=ROOT / "external" / "yolov5")
    parser.add_argument("--ocr-language", default="eng")
    args = parser.parse_args()
    detector = YOLODetector(args.model, args.weights, args.yolov5_repo)
    result = run_privacy_pipeline(args.input, args.output, detector, TesseractOCRExtractor(args.ocr_language))
    print(f"Redaction complete. Outputs written to: {args.output}")
    print(f"Redacted pages: {len(result['redacted_pages'])}; detections: {result['report']['detection_count']}")


if __name__ == "__main__":
    main()
