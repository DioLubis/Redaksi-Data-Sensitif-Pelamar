# Dataset Inventory and Remaining Gaps

Updated status after importing the local manual datasets. Raw sources and final YOLO artifacts remain excluded from Git by `.gitignore`.

## Ready for YOLO Training

| Target class | Source | Labeling method | Current status |
| --- | --- | --- | --- |
| `face_photo` | WIDER FACE | Official bounding boxes converted to YOLO | Available in train, validation, and test. |
| `signature` | Signature image corpus | Automatic ink-region bounding box with 8% margin; split by writer ID | Available in train, validation, and test. These are signature crops, not signatures embedded in documents. |
| `qr_code` | QR Code YOLO corpus | Original YOLO boxes remapped to class ID 2 | Available in train, validation, and test. |
| `id_card` | Curated MIDV-500 subset | Official quadrilateral converted to YOLO boxes; split by document template | Available in train, validation, and test. |
| `barcode` | Barcode COCO corpus from `datasets/instalasi_manual/barcode_dataset` | Official COCO boxes converted to YOLO | Available in train, validation, and test. |

## Retained for OCR-Assisted Labeling

`datasets/instalasi_manual/archive (2)/data` contains 2,484 resume PDFs. It is retained as an open-source document corpus for the next stage:

1. Sample a controlled subset of PDFs.
2. Convert PDF pages to images.
3. Run local OCR only.
4. Produce candidate boxes for email, phone number, address, dates, and document-number patterns using OCR coordinates plus regex.
5. Manually audit all candidate labels before using them as ground truth.

The PDF corpus must not be sent to Gemini or committed to Git.

## Not Included in the Current YOLO Model

| Target class | Required data | Why the current corpus is insufficient |
| --- | --- | --- |
| `stamp_or_seal` | Scanned documents with stamp/seal boxes | The downloaded stamp repository contained code only, not a dataset. |
| `document_number_area` | ID/certificate/document images with field-area boxes | MIDV only gives whole-card quadrilaterals. |
| `contact_block_visual` | Resume/document pages with reviewed email/phone/link block boxes | Resume PDFs are currently unannotated. |
| `address_block_visual` | Resume/document pages with reviewed address block boxes | Resume PDFs are currently unannotated. |
| `sensitive_visual_region` | Reviewed document regions that do not fit a more specific class | No ground-truth source is currently present. |

## Before Fair YOLOv5 vs YOLO26 Evaluation

1. Every one of the five reported classes has positive samples in train, validation, and test.
2. Split by source template, writer, or document identity, never by near-duplicate image frame.
3. Add document-context signature examples; standalone signature crops alone are not representative of CV pages.
4. Audit OCR-generated labels. Regex and OCR are candidate-label generators, not automatically trusted ground truth.
5. Freeze the final dataset manifest and compute class counts before training both models with identical splits.
