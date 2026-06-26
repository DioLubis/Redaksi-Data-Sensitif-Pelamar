# Streamlit Application

## Purpose

`streamlit_app.py` is the local demo interface for Applicant Privacy Shield. It accepts a PDF, JPG, or PNG, runs the selected local model and local OCR, and shows only sanitized artifacts. It does not call Gemini or upload the raw document to an external service.

## Prerequisites

1. A trained five-class `best.pt` weight file for YOLOv5 or YOLO26.
2. Python dependencies:

```powershell
pip install -r requirements-privacy.txt
```

3. Tesseract binary installed and available on `PATH`. On Windows, install Tesseract, reopen PowerShell, then verify:

```powershell
tesseract --version
```

4. For YOLOv5, clone the official repository at `external/yolov5` as described in `docs/12-training-yolov5-yolo26.md`.

## Run

```powershell
streamlit run streamlit_app.py
```

The app normally opens at `http://localhost:8501`.

## Using the App

1. Select `yolo26` or `yolov5`.
2. Enter the absolute or project-relative `best.pt` path.
3. Upload a PDF, JPG, or PNG no larger than the configured pipeline limit.
4. Select **Jalankan Redaksi**.
5. Review redacted pages, sanitized profile, privacy report, and JSON artifacts.
6. Download the redacted PDF or ZIP output when the report shows `Gemini safe payload: PASS`.

## Outputs

| Output | Meaning | Sensitive text included? |
| --- | --- | --- |
| `redacted_document.pdf` | Rebuilt image-based PDF with redacted regions | No |
| `redacted_pages/*.png` | Redacted page images | No, for detected regions |
| `detection_result.json` | Bounding boxes, class/category, source, confidence, hashes | No |
| `ocr_result.json` | OCR coordinates, confidence, token hashes | No |
| `sanitized_candidate_profile.json` | Skills, experience, education, certifications | No PII values allowed |
| `privacy_risk_report.json` | Risk summary and safety checks | No |

All scan output is written to `artifacts/<scan-id>/`, which is excluded from Git. The temporary uploaded original and temporary page conversion files are deleted after the run.

## Evaluation Panel

The **Evaluasi Sistem** tab reads `experiments/reports/comparison.csv` and `comparison_metrics.png` after model training. Generate these files with:

```powershell
python scripts/experiment/generate_comparison_report.py
```

The app presents model metrics but does not invent values when training or evaluation has not been completed.
