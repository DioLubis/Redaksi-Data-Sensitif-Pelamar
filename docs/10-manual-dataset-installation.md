# Manual Dataset Installation

Dokumen ini menjelaskan cara memasang dataset sumber untuk Applicant Privacy Shield tanpa membuat dataset ikut ter-upload ke GitHub.

## 1. Prinsip Penting

Dataset besar dan data mentah tidak boleh masuk GitHub.

File berikut sudah di-ignore oleh `.gitignore`:

```gitignore
datasets/raw/
datasets/interim/
datasets/privacy_shield/images/**
datasets/privacy_shield/labels/**
reports/
runs/
weights/
*.pt
*.onnx
```

Yang boleh masuk GitHub:

1. Dokumentasi.
2. Script konversi.
3. Config class map.
4. `datasets/privacy_shield/data.yaml`.
5. `.gitkeep` untuk mempertahankan struktur folder.

Sebelum commit, cek:

```powershell
git status --short --ignored
git ls-files datasets/raw datasets/interim datasets/privacy_shield/images datasets/privacy_shield/labels reports
```

Output `git ls-files` harus kosong untuk folder dataset payload.

## 2. Struktur Folder Target

Dataset sumber ditempatkan di `datasets/raw`.

Dataset final YOLO ditempatkan di `datasets/privacy_shield`.

```text
datasets/
  raw/
    wider_face/
    funsd/
    doclaynet/
    midv500/
    resumes/
  interim/
    resume_pages/
  privacy_shield/
    data.yaml
    images/
      train/
      val/
      test/
    labels/
      train/
      val/
      test/
```

## 3. Install Dependency

Jalankan dari root proyek:

```powershell
cd "D:\TugasUnud\Semester 6\VISKOM\redaksi-data-sensitif-pelamar"
pip install -r requirements-dataset.txt
```

Jika sebelumnya sudah pernah meng-install `datasets` versi baru dan muncul error `Dataset scripts are no longer supported`, paksa versi yang kompatibel:

```powershell
python -m pip install --upgrade "datasets>=2.19.0,<4.0.0" huggingface_hub
```

Dependency penting:

1. `pillow` untuk membaca/menulis image.
2. `pymupdf` untuk convert PDF ke image.
3. `datasets` untuk akses Hugging Face dataset.
4. `pyyaml` untuk file konfigurasi YAML.

## 4. FUNSD

FUNSD digunakan untuk formulir scan, OCR, dan layout dokumen.

Sumber resmi:

```text
https://guillaumejaume.github.io/FUNSD/
```

Dataset ini bisa diunduh otomatis dengan script:

```powershell
python scripts/dataset/download_datasets.py --dataset funsd
```

Hasil yang diharapkan:

```text
datasets/raw/funsd/
  dataset/
    training_data/
      images/
      annotations/
    testing_data/
      images/
      annotations/
  funsd.zip
  .download_complete
```

Cek jumlah file:

```powershell
(Get-ChildItem -File datasets\raw\funsd\dataset\training_data\images | Measure-Object).Count
(Get-ChildItem -File datasets\raw\funsd\dataset\testing_data\images | Measure-Object).Count
```

Catatan:

FUNSD tidak langsung menjadi label YOLO privacy final. Anotasinya berisi struktur form, sehingga perlu review atau mapping tambahan untuk class seperti `contact_block_visual`, `address_block_visual`, dan `sensitive_visual_region`.

## 5. WIDER FACE

WIDER FACE digunakan untuk class `face_photo`.

Sumber resmi:

```text
https://shuoyang1213.me/WIDERFACE/
```

Download manual file berikut dari halaman resmi:

1. `WIDER_train.zip`
2. `WIDER_val.zip`
3. `wider_face_split.zip`

Extract ke struktur berikut:

```text
datasets/raw/wider_face/
  WIDER_train/
    images/
  WIDER_val/
    images/
  wider_face_split/
    wider_face_train_bbx_gt.txt
    wider_face_val_bbx_gt.txt
```

Konversi train split ke format YOLO:

```powershell
python scripts/dataset/convert_widerface_to_yolo.py `
  --annotations datasets/raw/wider_face/wider_face_split/wider_face_train_bbx_gt.txt `
  --images datasets/raw/wider_face/WIDER_train/images `
  --out-images datasets/privacy_shield/images/train `
  --out-labels datasets/privacy_shield/labels/train
```

Konversi val split:

```powershell
python scripts/dataset/convert_widerface_to_yolo.py `
  --annotations datasets/raw/wider_face/wider_face_split/wider_face_val_bbx_gt.txt `
  --images datasets/raw/wider_face/WIDER_val/images `
  --out-images datasets/privacy_shield/images/val `
  --out-labels datasets/privacy_shield/labels/val
```

Catatan:

WIDER FACE adalah dataset wajah umum, bukan CV. Untuk penelitian ini, hasilnya digunakan untuk memperkuat deteksi wajah/foto pribadi. Jika ingin konteks CV lebih kuat, tambahkan anotasi `face_photo` dari dataset resume/CV.

## 6. DocLayNet

DocLayNet digunakan untuk layout dokumen dan kandidat region seperti `contact_block_visual`, `address_block_visual`, dan `sensitive_visual_region`.

Sumber:

```text
https://github.com/DS4SD/DocLayNet
https://huggingface.co/datasets/docling-project/DocLayNet
```

Untuk prototype, jangan download seluruh dataset jika tidak perlu. Ambil subset terlebih dahulu:

```powershell
python scripts/dataset/download_datasets.py `
  --dataset doclaynet `
  --split train `
  --limit 200
```

Hasil subset:

```text
datasets/raw/doclaynet/
  doclaynet_train_000000.png
  doclaynet_train_000001.png
  ...
```

Catatan penting:

1. Script downloader subset saat ini menyimpan image saja.
2. Untuk training YOLO privacy, tetap perlu annotation COCO dari DocLayNet atau anotasi manual.
3. Mapping otomatis DocLayNet ke class privacy tidak boleh dianggap ground truth final.
4. Gunakan DocLayNet terutama untuk variasi layout dan baseline region.

Jika memiliki annotation COCO DocLayNet, konversi:

```powershell
python scripts/dataset/convert_annotations_to_yolo.py `
  --format coco `
  --annotations datasets/raw/doclaynet/annotations.json `
  --images datasets/raw/doclaynet/images `
  --out-images datasets/privacy_shield/images/train `
  --out-labels datasets/privacy_shield/labels/train `
  --class-map configs/class_map_doclaynet_privacy.json
```

## 7. MIDV-500

MIDV-500 digunakan untuk class `id_card`, `document_number_area`, dan `sensitive_visual_region`.

Sumber/tooling:

```text
https://github.com/fcakyon/midv500
```

Opsi 1, install tooling:

```powershell
pip install midv500
```

Opsi 2, download manual dari sumber yang disebutkan di dokumentasi/paper MIDV-500 atau mirror Kaggle jika tersedia, lalu extract ke:

```text
datasets/raw/midv500/
```

Target struktur umum:

```text
datasets/raw/midv500/
  images/
  annotations.json
```

Jika annotation sudah dalam COCO:

```powershell
python scripts/dataset/convert_annotations_to_yolo.py `
  --format coco `
  --annotations datasets/raw/midv500/annotations.json `
  --images datasets/raw/midv500/images `
  --out-images datasets/privacy_shield/images/train `
  --out-labels datasets/privacy_shield/labels/train `
  --class-map configs/class_map_generic_privacy.json
```

Catatan:

1. Frame dari dokumen identitas yang sama tidak boleh masuk train dan test sekaligus.
2. Untuk class `document_number_area`, biasanya perlu anotasi tambahan karena annotation bawaan mungkin hanya menandai dokumen/kartu, bukan nomor spesifik.
3. Prioritaskan dokumen publik/dummy sesuai lisensi dataset.

### Resume Download MIDV-500 Tanpa Duplikat

### Mode Hemat Penyimpanan (Direkomendasikan)

Unduh penuh 50 template MIDV-500 tidak diperlukan untuk kelas `id_card` pada prototype ini. Gunakan maksimal 20 template yang sudah lengkap dan konversi hanya 80 frame representatif tiap template. Konfigurasi split yang tidak mencampur template antar train, validation, dan test ada pada `configs/midv500_curated_split.json`.

Konverter `convert_midv_quad_to_yolo.py` menyimpan hasil sebagai JPEG kualitas 85 dengan sisi terpanjang maksimum 1600 piksel. Hasilnya langsung memiliki label YOLO kelas `id_card` dan jauh lebih kecil dari TIFF mentah.

Jalankan konversi per split dengan daftar template dari `configs/midv500_curated_split.json`. Setelah `validate_yolo_labels.py` menyatakan valid, raw MIDV TIFF boleh dihapus karena `datasets/privacy_shield/images` dan `datasets/privacy_shield/labels` adalah artefak kerja untuk training. Jangan hapus `data.yaml`, konfigurasi split, atau label YOLO.

### Dataset QR Code dan Signature

Jika dataset QR Code sudah memiliki folder `images/<split>` dan `labels/<split>` berformat YOLO, gunakan `import_yolo_class.py` untuk memetakan class sumber menjadi `qr_code` tanpa mengubah koordinat bounding box. Validasi setiap split karena image tanpa file label harus dilewati.

Dataset signature berupa crop dapat diberi label otomatis dengan `prepare_signature_crops.py`. Script mendeteksi area tinta non-putih, menambah margin 8%, dan membagi writer agar identitas writer tidak muncul pada lebih dari satu split. Label ini cocok sebagai data awal kelas `signature`; data tanda tangan yang benar-benar berada di halaman dokumen tetap diperlukan pada tahap pengayaan berikutnya.

Package `midv500.download_dataset()` dapat terlihat mulai dari awal lagi karena script bawaannya selalu mengiterasi semua URL. Untuk menghindari duplikasi, gunakan script resume proyek ini:

```powershell
python scripts/dataset/resume_midv500_download.py `
  --output datasets/raw/midv500_full `
  --dry-run
```

Command `--dry-run` hanya menampilkan folder yang sudah lengkap dan folder yang masih perlu diunduh. Jika hasilnya benar, lanjutkan:

```powershell
python scripts/dataset/resume_midv500_download.py `
  --output datasets/raw/midv500_full
```

Script ini:

1. Mengecek folder `datasets/raw/midv500_full/midv500`.
2. Men-skip dokumen yang sudah punya folder `images` dan `ground_truth`.
3. Mengunduh hanya dokumen yang belum lengkap.
4. Menyimpan file sementara sebagai `.zip.part` agar download gagal tidak dianggap final.
5. Menghapus zip setelah extract berhasil, kecuali memakai opsi `--keep-zip`.

Jika sebelumnya berhenti di folder `19_esp_drvlic`, script ini seharusnya melanjutkan dari `20_esp_id_new` selama folder `01` sampai `19` sudah lengkap.

## 8. Dataset Resume/CV

Dataset resume/CV digunakan untuk konteks dokumen yang paling dekat dengan sistem Karierly.

Contoh sumber:

```text
https://huggingface.co/datasets/opensporks/resumes
https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset
```

Langkah manual:

1. Cek lisensi dataset.
2. Download dataset dari Hugging Face atau Kaggle.
3. Extract ke:

```text
datasets/raw/resumes/
```

Jika file berupa PDF, konversi ke image:

```powershell
python scripts/dataset/convert_pdf_to_images.py `
  --input datasets/raw/resumes `
  --output datasets/interim/resume_pages `
  --dpi 200
```

Setelah menjadi image, lakukan labeling manual untuk class:

1. `face_photo`
2. `signature`
3. `qr_code`
4. `barcode`
5. `contact_block_visual`
6. `address_block_visual`
7. `document_number_area`
8. `sensitive_visual_region`

Rekomendasi tool labeling:

1. CVAT.
2. Label Studio.
3. Roboflow Annotate.
4. makesense.ai untuk anotasi ringan.

Export hasil labeling ke YOLO format, lalu masukkan ke:

```text
datasets/privacy_shield/images/train
datasets/privacy_shield/images/val
datasets/privacy_shield/images/test
datasets/privacy_shield/labels/train
datasets/privacy_shield/labels/val
datasets/privacy_shield/labels/test
```

## 9. Dataset QR, Barcode, Signature, Stamp Tambahan

Dataset tambahan digunakan jika class tertentu masih kurang.

Letakkan masing-masing dataset di:

```text
datasets/raw/qr_barcode/
datasets/raw/signature/
datasets/raw/stamp/
```

Jika annotation COCO/VOC tersedia, konversi dengan:

```powershell
python scripts/dataset/convert_annotations_to_yolo.py `
  --format coco `
  --annotations datasets/raw/qr_barcode/annotations.json `
  --images datasets/raw/qr_barcode/images `
  --out-images datasets/privacy_shield/images/train `
  --out-labels datasets/privacy_shield/labels/train `
  --class-map configs/class_map_generic_privacy.json
```

Untuk VOC:

```powershell
python scripts/dataset/convert_annotations_to_yolo.py `
  --format voc `
  --annotations datasets/raw/signature/annotations `
  --images datasets/raw/signature/images `
  --out-images datasets/privacy_shield/images/train `
  --out-labels datasets/privacy_shield/labels/train `
  --class-map configs/class_map_generic_privacy.json
```

## 10. Split Dataset Final

Rasio final:

1. Train: 70%
2. Validation: 20%
3. Test: 10%

Aturan:

1. Dokumen dari template yang sama tidak boleh tersebar ke train dan test.
2. Semua halaman dari satu CV masuk split yang sama.
3. Semua frame MIDV-500 dari dokumen identitas yang sama masuk split yang sama.
4. Augmented image dari source yang sama masuk split yang sama.

## 11. Validasi Setelah Instalasi

Jalankan:

```powershell
python scripts/dataset/validate_yolo_labels.py `
  --dataset datasets/privacy_shield `
  --output reports/dataset/validation_summary.json
```

Jika sukses, akan muncul:

```text
Validation passed.
```

Visualisasi sample:

```powershell
python scripts/dataset/visualize_yolo_annotations.py `
  --dataset datasets/privacy_shield `
  --split train `
  --count 20 `
  --output reports/dataset/visual_samples
```

Cek gambar hasil visualisasi di:

```text
reports/dataset/visual_samples/train/
```

## 12. Output Wajib Sebelum Training

Sebelum training YOLOv5 dan YOLO26, pastikan ada:

1. `datasets/privacy_shield/data.yaml`.
2. Image final di `datasets/privacy_shield/images`.
3. Label final di `datasets/privacy_shield/labels`.
4. `reports/dataset/validation_summary.json`.
5. Visualisasi sample anotasi.
6. Catatan sumber dataset dan lisensi.
7. Catatan jumlah image per split.
8. Catatan jumlah bbox per class.
9. Catatan class yang masih kurang data.

## 13. Status Pemrosesan `datasets/instalasi_manual`

Folder `datasets/instalasi_manual` sudah dapat dipakai sebagai sumber lokal, tetapi tidak semuanya otomatis menjadi dataset training final.

Status pemrosesan:

1. WIDER FACE train sudah dikonversi ke `datasets/privacy_shield/images/train` dan `datasets/privacy_shield/labels/train`.
2. WIDER FACE val sudah dikonversi ke `datasets/privacy_shield/images/val` dan `datasets/privacy_shield/labels/val`.
3. WIDER FACE test tidak dipakai karena tidak memiliki ground-truth bbox.
4. MIDV-500 folder lokal yang tersedia adalah repo/tooling dan test data kecil, bukan full dataset. Dari test data lokal, hanya satu image yang cocok dengan ground truth `quad`; sample tersebut sudah dikonversi sebagai class `id_card` di train.
5. Dataset final saat ini siap untuk initial training class `face_photo` dan smoke-test class `id_card`.
6. Dataset belum cukup untuk final comparison semua class privacy karena class `signature`, `qr_code`, `barcode`, `stamp_or_seal`, `document_number_area`, `contact_block_visual`, `address_block_visual`, dan `sensitive_visual_region` masih perlu dataset/anotasi tambahan.

Command yang sudah dipakai untuk WIDER:

```powershell
python scripts/dataset/convert_widerface_to_yolo.py `
  --annotations datasets/instalasi_manual/wider_face_split/wider_face_train_bbx_gt.txt `
  --images datasets/instalasi_manual/WIDER_train/WIDER_train/images `
  --out-images datasets/privacy_shield/images/train `
  --out-labels datasets/privacy_shield/labels/train

python scripts/dataset/convert_widerface_to_yolo.py `
  --annotations datasets/instalasi_manual/wider_face_split/wider_face_val_bbx_gt.txt `
  --images datasets/instalasi_manual/WIDER_val/WIDER_val/images `
  --out-images datasets/privacy_shield/images/val `
  --out-labels datasets/privacy_shield/labels/val
```

Command yang dipakai untuk MIDV test data lokal:

```powershell
python scripts/dataset/convert_midv_quad_to_yolo.py `
  --data-root datasets/instalasi_manual/midv500-master/midv500-master/tests/test_data/data `
  --out-images datasets/privacy_shield/images/train `
  --out-labels datasets/privacy_shield/labels/train `
  --split-prefix train
```

## 14. Troubleshooting

### `ModuleNotFoundError: fitz`

Install PyMuPDF:

```powershell
pip install pymupdf
```

### `ModuleNotFoundError: datasets`

Install Hugging Face datasets:

```powershell
pip install datasets
```

### `RuntimeError: Dataset scripts are no longer supported, but found DocLayNet.py`

DocLayNet di Hugging Face masih memakai dataset loading script. Versi baru package `datasets` tidak lagi mendukung mekanisme itu.

Solusi di virtual environment aktif:

```powershell
python -m pip install --upgrade "datasets>=2.19.0,<4.0.0" huggingface_hub
```

Setelah itu jalankan ulang:

```powershell
python scripts/dataset/download_datasets.py `
  --dataset doclaynet `
  --split train `
  --limit 200
```

Peringatan Windows tentang symlink dari `huggingface_hub` bukan error. Download tetap bisa berjalan, hanya cache dapat memakai ruang disk lebih besar. Jika ingin mematikan warning:

```powershell
$env:HF_HUB_DISABLE_SYMLINKS_WARNING="1"
```

### `pyarrow.lib.ArrowInvalid: Float value ... was truncated converting to int64`

Error ini terjadi pada DocLayNet karena field `objects.area` pada dataset stream dapat berupa float, sedangkan schema loader lama mendefinisikannya sebagai integer.

Script `download_datasets.py` sudah diberi schema override agar `objects.area` dibaca sebagai `float64`. Jika error ini masih muncul, pastikan file script sudah versi terbaru lalu jalankan ulang:

```powershell
python scripts/dataset/download_datasets.py `
  --dataset doclaynet `
  --split train `
  --limit 200
```

Jika masih gagal, bersihkan cache Hugging Face untuk DocLayNet lalu ulangi:

```powershell
Remove-Item -Recurse -Force "$env:USERPROFILE\.cache\huggingface\hub\datasets--docling-project--DocLayNet"
python scripts/dataset/download_datasets.py `
  --dataset doclaynet `
  --split train `
  --limit 200
```

### `No images found`

Cek apakah folder image sudah benar:

```powershell
Get-ChildItem datasets\privacy_shield\images\train
```

### `image has no matching label file`

Setiap image harus punya file `.txt` dengan nama yang sama.

Contoh:

```text
images/train/cv_001.jpg
labels/train/cv_001.txt
```

### `class id out of range`

Pastikan class id hanya `0` sampai `9`, sesuai `data.yaml`.
