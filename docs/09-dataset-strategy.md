# Dataset Strategy and Preparation

## 1. Tujuan Dataset

Dataset digunakan untuk melatih YOLOv5 dan YOLO26 mendeteksi area visual sensitif pada CV, dokumen lamaran, sertifikat, formulir, dokumen identitas, dan dokumen pendukung lain sebelum data masuk ke AI Screening.

Dataset final harus memakai format yang sama untuk YOLOv5 dan YOLO26:

```text
datasets/privacy_shield/images/train
datasets/privacy_shield/images/val
datasets/privacy_shield/images/test
datasets/privacy_shield/labels/train
datasets/privacy_shield/labels/val
datasets/privacy_shield/labels/test
datasets/privacy_shield/data.yaml
```

## 2. Kelas Final YOLO

| ID | Class |
|---:|---|
| 0 | `face_photo` |
| 1 | `signature` |
| 2 | `qr_code` |
| 3 | `barcode` |
| 4 | `id_card` |

File konfigurasi final: [data.yaml](../datasets/privacy_shield/data.yaml).

## 3. Strategi Gabungan Dataset

Tidak satu dataset open source yang langsung memenuhi semua kelas visual sensitif CV. Karena itu digunakan strategi gabungan:

1. Gunakan dataset khusus untuk kelas spesifik seperti wajah dan dokumen identitas.
2. Gunakan dataset layout dokumen untuk area blok teks dan konteks dokumen.
3. Gunakan dataset formulir scan untuk variasi OCR, noise, dan form layout.
4. Gunakan dataset resume/CV open source untuk bentuk dokumen yang dekat dengan kasus Karierly.
5. Lakukan remapping class dan anotasi tambahan jika dataset sumber belum punya kelas sensitif yang sama.

## 4. Mapping Dataset ke Kelas

| Dataset | Kelas yang Dipakai | Cara Pakai |
|---|---|---|
| WIDER FACE | `face_photo` | Konversi bbox wajah ke class `face_photo`. Untuk konteks CV, wajah diperlakukan sebagai foto pribadi yang harus diredaksi. |
| MIDV-500 | `id_card` | Bbox dokumen resmi dikonversi menjadi class `id_card`. |
| Signature dataset open source | `signature` | Area tinta pada crop signature diberi bbox otomatis dan dibagi berdasarkan writer. |
| QR dataset open source | `qr_code` | Label YOLO sumber dipetakan ke class `qr_code`. |
| Barcode dataset open source | `barcode` | Label COCO sumber dipetakan ke class `barcode`. |
| Resume/CV open source | OCR candidate regions saja | Dipertahankan untuk OCR/regex dan audit, bukan label YOLO final. |
| Signature dataset open source | `signature` | Dipakai untuk memperkaya variasi tanda tangan. |
| QR/barcode dataset open source | `qr_code`, `barcode` | Dipakai untuk memperkaya pola QR dan barcode pada dokumen. |

## 5. Aturan Konversi ke Format YOLO

Format YOLO setiap baris:

```text
class_id x_center y_center width height
```

Semua nilai koordinat dinormalisasi ke rentang `0.0` sampai `1.0`.

Konversi dari bbox pixel `x_min, y_min, x_max, y_max`:

```text
x_center = ((x_min + x_max) / 2) / image_width
y_center = ((y_min + y_max) / 2) / image_height
width = (x_max - x_min) / image_width
height = (y_max - y_min) / image_height
```

Konversi dari COCO `x, y, width, height`:

```text
x_min = x
y_min = y
x_max = x + width
y_max = y + height
```

Konversi dari VOC:

```text
x_min = xmin
y_min = ymin
x_max = xmax
y_max = ymax
```

Script:

```powershell
python scripts/dataset/convert_annotations_to_yolo.py `
  --format coco `
  --annotations datasets/raw/source/annotations.json `
  --images datasets/raw/source/images `
  --out-images datasets/privacy_shield/images/train `
  --out-labels datasets/privacy_shield/labels/train `
  --class-map configs/class_map_generic_privacy.json
```

## 6. Pedoman Labeling Per Kelas

### `face_photo`

Beri label jika area memuat wajah manusia atau foto profil pribadi di CV, kartu identitas, sertifikat, formulir, atau dokumen pendukung.

Label mencakup:

1. Foto wajah formal di CV.
2. Foto wajah pada ID card.
3. Pas foto yang ditempel pada formulir.
4. Wajah pada dokumen pendukung yang bisa mengidentifikasi pelamar.

Jangan label:

1. Ikon avatar generik.
2. Ilustrasi wajah yang bukan identitas nyata.
3. Logo perusahaan yang menyerupai wajah.

### `signature`

Beri label pada tanda tangan basah, tanda tangan digital berupa image, paraf, atau scribble yang jelas dimaksudkan sebagai tanda tangan.

Label mencakup:

1. Tanda tangan pelamar.
2. Tanda tangan pejabat pada sertifikat.
3. Tanda tangan pada formulir.

Jangan label:

1. Garis kosong tempat tanda tangan jika belum terisi.
2. Teks nama yang diketik.
3. Ornamen grafis non-tanda tangan.

### `qr_code`

Beri label pada seluruh area QR code, termasuk quiet zone jika terlihat.

Label mencakup:

1. QR code pada sertifikat.
2. QR code verifikasi dokumen.
3. QR code profil/portfolio jika dapat mengarah ke data personal.

Jangan label:

1. Logo kotak biasa.
2. Pattern dekoratif yang bukan QR.

### `barcode`

Beri label pada barcode 1D atau 2D selain QR, misalnya Code128, EAN, PDF417, DataMatrix jika tampak sebagai barcode.

Label mencakup:

1. Barcode pada sertifikat.
2. Barcode pada ID card.
3. Barcode pada dokumen pendukung.

Jangan label:

1. Garis tabel.
2. Pattern dekoratif.

### `id_card`

Beri label pada seluruh kartu identitas atau dokumen identitas yang terlihat sebagai satu objek.

Label mencakup:

1. KTP/SIM/paspor/kartu mahasiswa.
2. Badge identitas.
3. Scan/foto ID card pada dokumen lamaran.

Jangan label:

1. CV biasa tanpa struktur kartu identitas.
2. Sertifikat tanpa fungsi identitas.

### `stamp_or_seal`

Beri label pada stempel, cap, seal, atau official mark yang bisa mengandung identitas institusi, nomor validasi, atau tanda pengesahan.

Label mencakup:

1. Stempel basah.
2. Cap digital.
3. Seal sertifikat.

Jangan label:

1. Logo perusahaan biasa tanpa fungsi stempel.
2. Watermark latar belakang yang tidak mengandung identitas validasi.

### `document_number_area`

Beri label pada area yang memuat nomor dokumen atau nomor identitas visual yang harus disensor.

Label mencakup:

1. NIK.
2. Nomor paspor.
3. Nomor SIM.
4. Nomor sertifikat.
5. Nomor registrasi dokumen.
6. Nomor peserta atau nomor aplikasi.

Jangan label:

1. Tahun pengalaman kerja.
2. Nomor halaman.
3. Nomor urut daftar yang tidak sensitif.

### `contact_block_visual`

Beri label pada blok visual yang berisi kontak personal.

Label mencakup:

1. Blok header CV berisi email dan nomor telepon.
2. Sidebar kontak pada CV.
3. Area "Contact", "Phone", "Email", "LinkedIn" yang bersifat personal.

Jangan label:

1. Kontak perusahaan pada pengalaman kerja.
2. Informasi kontak referensi jika diputuskan tetap diproses manual di luar MVP.

### `address_block_visual`

Beri label pada blok alamat lengkap atau alamat domisili.

Label mencakup:

1. Alamat lengkap di CV.
2. Alamat pada formulir kandidat.
3. Alamat pada ID card.

Jangan label:

1. Kota lokasi kerja saja jika tidak lengkap.
2. Nama negara/kota dalam riwayat pendidikan jika tidak mengidentifikasi alamat pribadi.

### `sensitive_visual_region`

Gunakan sebagai fallback untuk area sensitif yang tidak cocok dengan kelas lain.

Label mencakup:

1. Area keluarga/kontak darurat.
2. Informasi agama/status pernikahan yang tampil sebagai blok visual.
3. Area dokumen pendukung yang mengandung data personal campuran.
4. Foto dokumen pribadi yang tidak termasuk ID card.

Jangan gunakan jika kelas spesifik lain lebih tepat.

## 7. Aturan Bounding Box

1. Box harus menutupi seluruh area sensitif.
2. Tambahkan margin kecil 3-5% jika area rawan bocor, seperti tanda tangan tipis, QR code, barcode, atau nomor dokumen.
3. Jangan membuat box terlalu besar sampai menghapus informasi penting seperti skill, pendidikan, atau pengalaman.
4. Untuk blok kontak/alamat, box harus mencakup label dan value jika keduanya membentuk satu blok.
5. Untuk wajah, box boleh mencakup seluruh pas foto, bukan hanya wajah, jika foto itu akan diredaksi penuh.
6. Untuk ID card, box mencakup seluruh kartu.
7. Untuk dokumen number area, box hanya mencakup nomor dan label terdekat jika perlu.
8. Jika dua objek sensitif saling overlap, boleh dibuat dua bbox berbeda.
9. Jika teks sensitif dideteksi OCR, bbox visual tetap digunakan jika bloknya jelas secara visual.

## 8. Aturan Data Split

Rasio:

1. Train: 70%
2. Validation: 20%
3. Test: 10%

Aturan anti-leakage:

1. Semua halaman dari dokumen yang sama harus masuk split yang sama.
2. Dokumen dari template yang sama tidak boleh tersebar ke train dan test jika hanya beda nama/data.
3. Frame dari video MIDV-500 untuk ID yang sama harus masuk split yang sama.
4. Augmented image dari satu source image harus tetap di split yang sama.
5. Gunakan `document_id`, `template_id`, atau `source_group_id` pada manifest split.

## 9. Strategi Augmentasi

Augmentasi bertujuan mensimulasikan kondisi upload dokumen pelamar:

| Augmentasi | Rentang Aman |
|---|---|
| Blur ringan | Gaussian blur kernel 3-5 |
| JPEG compression | Quality 40-90 |
| Brightness/contrast | +/- 20% |
| Rotation kecil | -3 sampai +3 derajat |
| Perspective transform ringan | 0-5% sudut |
| Scan noise | noise tipis, speckle, salt-pepper ringan |
| Shadow | shadow transparan di tepi/area tertentu |
| Low resolution | downscale 50-80%, lalu upscale |

Aturan:

1. Jangan augment sampai label tidak sesuai.
2. Jangan rotasi besar untuk dokumen formal.
3. Jangan crop area sensitif sampai hilang.
4. Simpan parameter augmentasi di manifest jika dipakai untuk eksperimen.

## 10. Script yang Disediakan

| Script | Fungsi |
|---|---|
| `scripts/dataset/download_datasets.py` | Helper download/instruksi dataset sumber |
| `scripts/dataset/convert_pdf_to_images.py` | Konversi PDF menjadi image per halaman |
| `scripts/dataset/convert_annotations_to_yolo.py` | Konversi COCO/VOC ke YOLO |
| `scripts/dataset/convert_widerface_to_yolo.py` | Konversi WIDER FACE ke YOLO class `face_photo` |
| `scripts/dataset/validate_yolo_labels.py` | Validasi file label YOLO |
| `scripts/dataset/visualize_yolo_annotations.py` | Visualisasi sample anotasi |

## 11. Contoh Command

Validasi struktur dan label:

```powershell
python scripts/dataset/validate_yolo_labels.py `
  --dataset datasets/privacy_shield `
  --output reports/dataset/validation_summary.json
```

Visualisasi sample:

```powershell
python scripts/dataset/visualize_yolo_annotations.py `
  --dataset datasets/privacy_shield `
  --split train `
  --count 12 `
  --output reports/dataset/visual_samples
```

Konversi WIDER FACE:

```powershell
python scripts/dataset/convert_widerface_to_yolo.py `
  --annotations datasets/raw/wider_face/wider_face_split/wider_face_train_bbx_gt.txt `
  --images datasets/raw/wider_face/WIDER_train/images `
  --out-images datasets/privacy_shield/images/train `
  --out-labels datasets/privacy_shield/labels/train
```

Konversi PDF ke image:

```powershell
python scripts/dataset/convert_pdf_to_images.py `
  --input datasets/raw/resumes `
  --output datasets/interim/resume_pages `
  --dpi 200
```

## 12. Checklist Kualitas Dataset

Sebelum training, pastikan:

1. `data.yaml` valid dan `nc` sesuai jumlah class.
2. Setiap image memiliki label `.txt` dengan stem yang sama.
3. Setiap nilai YOLO berada pada rentang `0.0` sampai `1.0`.
4. Tidak ada bbox dengan width/height `0`.
5. Tidak ada class id di luar `0-9`.
6. Train/val/test mengikuti rasio 70/20/10 atau alasan deviasinya dicatat.
7. Tidak ada leakage dokumen/template antar split.
8. Setiap class prioritas memiliki contoh cukup.
9. Visualisasi sample sudah dicek manual.
10. Dataset source dan lisensi dicatat di manifest.
11. Tidak ada data pribadi non-open-source.
12. Raw dataset tidak dikirim ke Gemini atau API eksternal.

## 13. Output yang Harus Dilihat Sebelum Training

Sebelum lanjut ke training YOLOv5/YOLO26, siapkan output berikut:

1. `datasets/privacy_shield/data.yaml`.
2. Jumlah image per split.
3. Jumlah bbox per class.
4. `reports/dataset/validation_summary.json`.
5. Folder visualisasi sample: `reports/dataset/visual_samples`.
6. Manifest sumber dataset: `datasets/manifests/dataset_sources.yaml`.
7. Manifest split final, misalnya `datasets/manifests/privacy_shield_split.json`.
8. Minimal 20 sample visual yang sudah dicek manual.
9. Catatan lisensi setiap dataset sumber.
10. Catatan kelas yang masih kurang data.

## 14. Catatan Penting untuk YOLOv5 dan YOLO26

Dataset final tidak boleh spesifik ke salah satu model. YOLOv5 dan YOLO26 harus membaca `data.yaml` dan folder image/label yang sama agar perbandingan adil.

Jika YOLO26 memakai package Ultralytics terbaru, tetap gunakan label YOLO detection standar. Jangan membuat format khusus YOLO26 jika tidak diperlukan.

## 15. Instalasi Dataset Manual

Panduan instalasi manual per dataset tersedia di [Manual Dataset Installation](10-manual-dataset-installation.md).
