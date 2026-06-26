# Training YOLOv5 and YOLO26

## Scope

The comparison is limited to the five classes that have validated samples in all splits: `face_photo`, `signature`, `qr_code`, `barcode`, and `id_card`.

Contact, address, document-number, stamp, and generic sensitive-region protection remain OCR/regex/manual-review responsibilities. They are not YOLO model outputs and must not be reported as YOLO metrics.

## Fair-Comparison Configuration

Both backends read `configs/training/privacy_shield.yaml` and use the same dataset YAML, image size 640, 50 epochs, seed 42, batch size 8, SGD optimizer, and frozen train/validation/test folders. Compare equivalent scales only, for example `yolov5n` versus `yolo26n`.

Reduce batch size only after an out-of-memory error and record the replacement value in the final report.

## Local Setup

Run from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-training.txt
git clone https://github.com/ultralytics/yolov5.git external/yolov5
pip install -r external/yolov5/requirements.txt
```

Install CUDA-compatible PyTorch before `requirements-training.txt` when a GPU is available. The local preparation environment is CPU-only, so it can run smoke tests but full training is recommended on a CUDA GPU or Google Colab.

## Google Colab Setup

```bash
!git clone https://github.com/<your-account>/redaksi-data-sensitif-pelamar.git
%cd redaksi-data-sensitif-pelamar
!pip install -r requirements-training.txt
!git clone https://github.com/ultralytics/yolov5.git external/yolov5
!pip install -r external/yolov5/requirements.txt
```

Upload or mount the ignored `datasets/privacy_shield/images` and `datasets/privacy_shield/labels` artifacts before training. Never upload raw CV PDFs to a public repository or external AI service.

## Train

```powershell
python scripts/experiment/train_yolov5.py --model-size n --device 0
python scripts/experiment/train_yolo26.py --model-size n --device 0
```

Expected best weights:

```text
experiments/runs/yolov5/yolov5n_seed42/weights/best.pt
experiments/runs/yolo26/yolo26n_seed42/weights/best.pt
```

## Evaluate and Benchmark

```powershell
python scripts/experiment/evaluate_models.py --backend yolov5 --weights experiments/runs/yolov5/yolov5n_seed42/weights/best.pt --device 0
python scripts/experiment/evaluate_models.py --backend yolo26 --weights experiments/runs/yolo26/yolo26n_seed42/weights/best.pt --device 0
python scripts/experiment/benchmark_inference.py --backend yolov5 --weights experiments/runs/yolov5/yolov5n_seed42/weights/best.pt --device 0
python scripts/experiment/benchmark_inference.py --backend yolo26 --weights experiments/runs/yolo26/yolo26n_seed42/weights/best.pt --device 0
```

Evaluation produces confusion matrices and precision-recall curves in backend run folders. Metric and benchmark JSON files are written to `experiments/reports/`.

Generate the aggregate CSV, Markdown table, and metric chart after both evaluations and benchmarks complete:

```powershell
python scripts/experiment/generate_comparison_report.py
```

## Export

```powershell
python scripts/experiment/export_model.py --backend yolo26 --weights experiments/runs/yolo26/yolo26n_seed42/weights/best.pt
```

## Experiment Result Table

| Model | Scale | Seed | Image size | Epochs | Batch | Precision | Recall | F1 | mAP@50 | mAP@50:95 | Inference ms/image | FPS | Weight MB | Training time | Peak GPU MB |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| YOLOv5 | n | 42 | 640 | 50 | 8 | | | | | | | | | | |
| YOLO26 | n | 42 | 640 | 50 | 8 | | | | | | | | | | |

Do not conclude that one model is better from mAP alone. Compare recall for privacy protection, per-class errors, false negatives, latency, model size, and recorded hardware.
