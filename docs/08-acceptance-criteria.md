# Acceptance Criteria

## Upload Protection Layer

MVP diterima jika:

1. File PDF, JPG, PNG diterima.
2. File di luar format tersebut ditolak.
3. File melebihi batas ukuran ditolak.
4. PDF melebihi batas halaman ditolak.
5. Hash file dibuat.
6. Audit log upload dibuat.
7. File asli tidak dapat dipakai oleh endpoint Gemini safe screening.

## PDF/Image Preprocessor

MVP diterima jika:

1. Semua halaman PDF dikonversi menjadi image.
2. Urutan halaman benar.
3. Image hasil konversi memiliki metadata proses.
4. Proses gagal dengan error jelas jika PDF rusak.

## YOLO Sensitive Visual Detector

MVP diterima jika:

1. YOLOv5 dan YOLO26 memakai output schema yang sama.
2. Setiap deteksi memiliki model name, class, bbox, confidence, page number, dan latency.
3. Hasil inference dapat disimpan ke database.
4. Jika YOLO26 tidak tersedia, sistem mengembalikan status unavailable dengan alasan.
5. Evaluasi dapat menghasilkan mAP, precision, recall, F1, dan latency.

## OCR & Textual PII Detector

MVP diterima jika:

1. OCR membaca teks dari image halaman.
2. Regex mendeteksi email, nomor telepon, NIK/NPWP, tanggal lahir, dan rekening.
3. Detector menghasilkan text span atau koordinat redaksi.
4. PII mentah tidak ditulis ke log.
5. Output dapat digabungkan dengan deteksi visual.

## Redaction Engine

MVP diterima jika:

1. Bbox visual sensitif diredaksi.
2. Area teks PII diredaksi.
3. Hasil redaksi permanen pada sanitized document.
4. Redaction report mencatat jumlah, kelas, halaman, dan metode redaksi.
5. Tidak ada selectable sensitive text yang tersisa pada sanitized PDF.

## Sanitized Profile Builder

MVP diterima jika:

1. Profile berisi skill, pengalaman, pendidikan, sertifikasi, proyek, dan ringkasan.
2. Profile tidak berisi email, telepon, alamat lengkap, NIK/NPWP, tanggal lahir, agama, status pernikahan, atau data keluarga.
3. Jika blind screening aktif, nama kandidat dihapus atau diganti candidate code.
4. Removed fields dicatat.

## Gemini Safe Prompt Builder

MVP diterima jika:

1. Prompt dibuat dari sanitized profile saja.
2. Tidak ada file CV mentah, OCR raw text penuh, atau path original document.
3. Final PII guard berjalan sebelum request.
4. Request diblokir jika masih ada PII.
5. Audit log mencatat safe screening requested tanpa menyimpan prompt mentah.

## Privacy Report Generator

MVP diterima jika:

1. Report memuat risk level.
2. Report memuat kategori data sensitif yang ditemukan.
3. Report memuat jumlah redaksi.
4. Report memuat ringkasan YOLOv5 vs YOLO26.
5. Report dapat diakses melalui API.

## Audit Trail Service

MVP diterima jika:

1. Upload, scan, detection, redaction, profile build, dan safe screening tercatat.
2. Log tidak menyimpan PII mentah.
3. Log dapat ditelusuri berdasarkan scan id atau document id.
4. Error job tersimpan dengan pesan aman.

## Backend API

MVP diterima jika:

1. Semua endpoint utama tersedia.
2. Response JSON konsisten.
3. Error format konsisten.
4. Endpoint safe AI screening tidak menerima file mentah.
5. Status job dapat dipantau.

## Frontend Dashboard

MVP diterima jika:

1. User dapat upload dokumen.
2. User dapat melihat status scan.
3. Recruiter dapat melihat sanitized profile.
4. Admin dapat melihat Privacy Risk Report.
5. Admin dapat melihat model comparison summary.

