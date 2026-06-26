# Redaction Engine and Privacy Pipeline

## Supported Visual Model Scope

The current trained-data scope is `face_photo`, `signature`, `qr_code`, `barcode`, and `id_card`. The pipeline does not claim visual YOLO detection for stamp, address, document-number, or generic sensitive regions because no ground truth exists for those classes.

## Redaction Rules

| Category | Source | Method | Action |
| --- | --- | --- | --- |
| face/photo | YOLO | blur | Always redact |
| signature | YOLO | black box | Always redact |
| QR code | YOLO | pixelate | Always redact |
| barcode | YOLO | pixelate | Always redact |
| ID card | YOLO | black box | Always redact |
| email, phone, address, document number | OCR plus regex | black box | Always redact |
| skills, experience, education, certification | OCR/profile builder | keep | Eligible for sanitized profile |

## Run Locally

Install dependencies and the Tesseract executable, then run only with a trained five-class weight file:

```powershell
pip install -r requirements-privacy.txt
python scripts/run_privacy_pipeline.py `
  --input path\to\document.pdf `
  --output artifacts\scan-001 `
  --model yolo26 `
  --weights experiments\runs\yolo26\yolo26n_seed42\weights\best.pt
```

For YOLOv5, clone the official repository from the training guide and add `--yolov5-repo external\yolov5`.

## Output Contracts

`detection_result.json` stores page number, class/category, source, confidence, redaction method, bounding box, and optional non-reversible evidence hash. It does not store OCR text.

```json
{
  "schema_version": "1.0",
  "model_scope": "five_class_visual_detector",
  "pages": [{"page_number": 1, "detections": [{"category": "email", "source": "ocr_regex", "box": {"x1": 10, "y1": 20, "x2": 200, "y2": 40}}]}]
}
```

`ocr_result.json` contains redacted tokens, token hashes, coordinates, and OCR confidence. Raw OCR text is held only in process memory while the profile is built.

`sanitized_candidate_profile.json` contains only skills, experience, education, certifications, and privacy status flags. The Gemini boundary must call `assert_gemini_safe` before sending this object.

`privacy_risk_report.json` contains counts, risk level, processing duration, redaction application rate, and Gemini-safe payload status. Redaction Success Rate, Sensitive Data Leakage Rate, Over-redaction Rate, and OCR PII Detection Accuracy require manually reviewed ground truth for a valid research metric; unavailable metrics are emitted as `null`.

The redacted PDF is image-based and rebuilt from redacted pages, so the original PDF text layer is not retained.

## Tests

```powershell
pytest -q
```

The integration test uses a generated dummy PNG and in-memory dummy OCR/model classes. It never invokes Gemini or uses a real CV.
