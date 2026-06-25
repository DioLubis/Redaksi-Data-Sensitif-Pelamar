# Dataset Plan

## Prinsip Dataset

Dataset harus:

1. Open source atau tersedia publik.
2. Gratis untuk diakses.
3. Mudah diunduh untuk penelitian.
4. Memiliki lisensi yang diperiksa sebelum digunakan.
5. Tidak dikirim ke Gemini dalam bentuk mentah.
6. Digunakan hanya untuk eksperimen lokal.

## Kebutuhan Dataset

Sistem membutuhkan beberapa jenis data:

1. CV/resume PDF atau image.
2. Dokumen form/scanned document untuk OCR dan layout.
3. Gambar atau dokumen yang mengandung signature, QR code, barcode, foto, stamp, dan area identitas.
4. Anotasi bounding box untuk kelas visual sensitif.
5. Data teks untuk evaluasi regex/NER PII.

## Kandidat Dataset Open Source

| Dataset | Kegunaan | Catatan |
|---|---|---|
| Hugging Face `opensporks/resumes` | Resume PDF dan teks | Cocok untuk pipeline CV; lisensi perlu dicek sebelum final |
| Kaggle Resume Dataset | Resume PDF/string | Banyak variasi resume; perlu akun Kaggle dan cek lisensi |
| FUNSD | OCR, form understanding, layout | Dataset kecil tapi anotasi dokumen jelas |
| RVL-CDIP | Variasi dokumen image skala besar | Cocok untuk robust document preprocessing |
| Signature dataset open source | Deteksi tanda tangan | Pilih yang lisensinya jelas |
| QR/barcode dataset open source | Deteksi QR/barcode | Bisa dipakai untuk kelas visual spesifik |
| Face dataset open source | Deteksi foto wajah | Harus hati-hati lisensi dan etika |

## Strategi Penggunaan Dataset

Karena dataset CV dengan anotasi area sensitif lengkap sulit ditemukan, strategi prototype:

1. Gunakan dataset resume open source sebagai dokumen dasar.
2. Gunakan dataset dokumen seperti FUNSD/RVL-CDIP untuk variasi layout dan OCR.
3. Gunakan dataset objek khusus untuk signature, QR, barcode, stamp, dan face jika lisensinya memungkinkan.
4. Buat anotasi bounding box pada subset dokumen open source yang dipilih.
5. Jangan membuat data pribadi asli baru.
6. Jangan memakai CV pribadi teman/keluarga/dosen.

## Anotasi

Format anotasi yang disarankan:

1. YOLO format untuk training:

```text
class_id x_center y_center width height
```

2. JSON manifest untuk audit:

```json
{
  "image_id": "doc001_page001",
  "source_dataset": "funsd",
  "split": "train",
  "annotations": [
    {
      "class_name": "signature",
      "bbox": [120, 440, 310, 500]
    }
  ]
}
```

## Label Mapping

```json
{
  "0": "face_photo",
  "1": "personal_photo",
  "2": "signature",
  "3": "qr_code",
  "4": "barcode",
  "5": "id_card",
  "6": "stamp_or_seal",
  "7": "document_number_area",
  "8": "sensitive_visual_region",
  "9": "contact_block_visual",
  "10": "address_block_visual"
}
```

## Risiko Dataset

| Risiko | Mitigasi |
|---|---|
| Dataset resume mengandung PII nyata | Jangan upload ke layanan eksternal; gunakan lokal; cek lisensi |
| Lisensi tidak cocok | Ganti dataset atau gunakan hanya dataset dengan lisensi jelas |
| Kelas visual tidak lengkap | Gabungkan beberapa dataset open source |
| Bahasa Indonesia sedikit | Gunakan campuran dataset Inggris dan tambah dataset publik Indonesia jika lisensinya jelas |
| Anotasi manual memakan waktu | Batasi subset MVP dan fokus kelas prioritas |

## Kelas Prioritas MVP

Untuk MVP, kelas paling penting:

1. `face_photo`
2. `signature`
3. `qr_code`
4. `barcode`
5. `id_card`
6. `contact_block_visual`
7. `address_block_visual`

Kelas lain dapat menjadi tahap lanjutan.

## Referensi Awal

1. FUNSD: <https://guillaumejaume.github.io/FUNSD/>
2. RVL-CDIP: <https://adamharley.com/rvl-cdip/>
3. Hugging Face Resume Dataset Example: <https://huggingface.co/datasets/opensporks/resumes>
4. Kaggle Resume Dataset Example: <https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset>

