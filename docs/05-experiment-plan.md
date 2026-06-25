# Experiment Plan

## Tujuan Eksperimen

Membandingkan YOLOv5 dan YOLO26 pada tugas deteksi area visual sensitif dalam dokumen pelamar.

## Pertanyaan Penelitian

1. Model mana yang memiliki recall lebih tinggi untuk area sensitif?
2. Model mana yang memiliki mAP lebih baik pada kelas visual sensitif?
3. Model mana yang lebih cepat pada inference per halaman?
4. Apakah YOLO26 memberikan peningkatan yang signifikan dibanding YOLOv5 pada konteks dokumen CV?
5. Apakah peningkatan akurasi sebanding dengan kebutuhan komputasi?

## Hipotesis Awal

1. YOLO26 berpotensi memiliki akurasi dan latency lebih baik karena arsitektur lebih baru.
2. YOLOv5 kemungkinan lebih mudah dijalankan dan lebih stabil untuk prototype karena ekosistem lama dan dokumentasi luas.
3. Untuk redaksi privasi, recall pada kelas sensitif lebih penting daripada precision.

## Kelas Evaluasi

1. `face_photo`
2. `personal_photo`
3. `signature`
4. `qr_code`
5. `barcode`
6. `id_card`
7. `stamp_or_seal`
8. `document_number_area`
9. `sensitive_visual_region`
10. `contact_block_visual`
11. `address_block_visual`

## Dataset Split

Rasio default:

1. Train: 70%
2. Validation: 15%
3. Test: 15%

Syarat:

1. Split sama untuk YOLOv5 dan YOLO26.
2. Seed dicatat.
3. Tidak ada dokumen yang sama muncul di train dan test.
4. Jika dataset berasal dari beberapa sumber, distribusi sumber dicatat.

## Metrik Model Deteksi

| Metrik | Fungsi |
|---|---|
| mAP@0.5 | Akurasi deteksi pada IoU 0.5 |
| mAP@0.5:0.95 | Evaluasi lebih ketat across IoU |
| Precision | Mengukur false positive |
| Recall | Mengukur false negative |
| F1-score | Keseimbangan precision dan recall |
| Per-class recall | Penting untuk kelas sensitif |
| Latency per page | Kecepatan inference |
| FPS | Throughput |
| Model size | Ukuran deployment |
| GPU/CPU memory | Kebutuhan resource |

## Metrik Perlindungan Data

| Metrik | Definisi |
|---|---|
| Redaction coverage | Persentase area sensitif yang berhasil diredaksi |
| PII false negative rate | PII yang lolos tanpa redaksi |
| Over-redaction rate | Area non-sensitif yang ikut diredaksi |
| Gemini leakage rate | PII yang masih muncul di prompt Gemini |
| Raw document leakage | Harus selalu false |

## Konfigurasi Eksperimen

Setiap eksperimen harus mencatat:

1. Dataset version.
2. Dataset source.
3. Label schema version.
4. Train/val/test split.
5. Random seed.
6. Model version.
7. Image size.
8. Batch size.
9. Epoch.
10. Optimizer.
11. Learning rate.
12. Hardware.
13. Dependency version.
14. Start/end timestamp.

## Format Output Eksperimen

`reports/model_comparison.json`:

```json
{
  "experiment_id": "exp-001",
  "dataset_version": "v1",
  "seed": 42,
  "models": {
    "yolov5": {
      "map50": 0.84,
      "map50_95": 0.61,
      "precision": 0.82,
      "recall": 0.88,
      "f1": 0.85,
      "latency_ms_per_page": 45,
      "model_size_mb": 14.2
    },
    "yolo26": {
      "map50": 0.87,
      "map50_95": 0.65,
      "precision": 0.84,
      "recall": 0.91,
      "f1": 0.87,
      "latency_ms_per_page": 39,
      "model_size_mb": 13.8
    }
  }
}
```

## Fairness Rules

1. Dataset harus sama.
2. Split harus sama.
3. Label class harus sama.
4. Resolusi input harus sama jika memungkinkan.
5. Evaluasi harus memakai test set yang sama.
6. Threshold confidence harus dilaporkan.
7. Hardware harus sama.
8. Inference mode harus sama: CPU vs CPU atau GPU vs GPU.

## Keputusan Jika YOLO26 Tidak Tersedia

Jika package/model YOLO26 tidak dapat digunakan di environment lokal:

1. Jangan mengganti dengan model lain lalu menyebutnya YOLO26.
2. Simpan adapter `YOLO26Detector` dengan status `unavailable`.
3. Dokumentasikan alasan teknis.
4. Tetap jalankan YOLOv5 sebagai baseline.
5. Tulis keterbatasan penelitian secara eksplisit.

