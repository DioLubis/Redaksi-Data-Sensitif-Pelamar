# Product Requirement Document

## 1. Latar Belakang

Karierly memiliki alur Applicant Tracking System yang memungkinkan kandidat mengunggah CV, recruiter mengelola pipeline kandidat, dan AI Screening menganalisis kecocokan kandidat terhadap lowongan. Karena CV dapat mengandung data pribadi yang tidak relevan untuk screening pekerjaan, dibutuhkan lapisan perlindungan sebelum data dikirim ke Gemini API.

Applicant Privacy Shield menjadi gateway yang memastikan hanya informasi relevan seperti skill, pengalaman, pendidikan, sertifikasi, proyek, dan ringkasan profesional yang diteruskan ke AI Screening.

## 2. Sasaran Pengguna

1. Recruiter yang membutuhkan hasil AI Screening tanpa melihat data sensitif yang tidak diperlukan.
2. Admin yang membutuhkan audit dan laporan redaksi.
3. Peneliti/mahasiswa yang membutuhkan prototype reproducible untuk membandingkan YOLOv5 dan YOLO26.

## 3. Nilai Produk

1. Mengurangi risiko pemrosesan data pribadi oleh AI eksternal.
2. Menyediakan bukti audit bahwa sistem melakukan redaksi.
3. Menyediakan eksperimen perbandingan model deteksi visual.
4. Menjaga utilitas screening pekerjaan dengan tetap mempertahankan informasi relevan.

## 4. Fitur MVP

| ID | Fitur | Prioritas |
|---|---|---|
| F-01 | Upload CV/dokumen pendukung | Wajib |
| F-02 | Validasi file | Wajib |
| F-03 | PDF to image preprocessing | Wajib |
| F-04 | Deteksi visual YOLOv5 | Wajib |
| F-05 | Deteksi visual YOLO26 | Wajib, jika package tersedia |
| F-06 | OCR | Wajib |
| F-07 | Regex/NER PII detection | Wajib |
| F-08 | Detection merger | Wajib |
| F-09 | Redaction engine | Wajib |
| F-10 | Sanitized candidate profile | Wajib |
| F-11 | Gemini safe prompt | Wajib |
| F-12 | Privacy Risk Report | Wajib |
| F-13 | Audit trail | Wajib |
| F-14 | Dashboard status scan | Wajib |
| F-15 | Model comparison report | Wajib |

## 5. Fitur Opsional

| ID | Fitur | Alasan Opsional |
|---|---|---|
| O-01 | Blind screening nama kandidat | Tidak selalu diperlukan untuk semua skenario |
| O-02 | Manual review queue | Menambah kompleksitas UI dan workflow |
| O-03 | Role-based report detail | Relevan untuk production, tidak wajib untuk prototype |
| O-04 | Active learning | Membutuhkan siklus anotasi tambahan |
| O-05 | MinIO/S3 storage | Filesystem lokal cukup untuk prototype |

## 6. User Story

1. Sebagai kandidat, saya ingin mengunggah CV agar dapat melamar pekerjaan.
2. Sebagai recruiter, saya ingin melihat hasil AI Screening tanpa data sensitif yang tidak perlu.
3. Sebagai admin, saya ingin melihat laporan redaksi agar dapat memastikan dokumen diproses dengan aman.
4. Sebagai peneliti, saya ingin membandingkan YOLOv5 dan YOLO26 dengan metrik yang sama.
5. Sebagai sistem AI Screening, saya hanya ingin menerima sanitized profile agar tidak memproses file mentah.

## 7. Success Metrics

| Area | Metrik |
|---|---|
| Deteksi visual | mAP@0.5, mAP@0.5:0.95, precision, recall, F1 |
| Kecepatan | latency per page, FPS, total processing time |
| Redaksi | redaction coverage, false negative PII rate, over-redaction rate |
| OCR/PII | precision, recall, F1 untuk entitas PII |
| Integrasi | raw_document_sent_to_gemini = false |
| Audit | semua job memiliki audit log minimum upload, scan, redact, profile, safe screening |

## 8. Out of Scope MVP

1. Production-grade access control lengkap.
2. Integrasi payment, tenant, atau career page penuh.
3. Training NER besar dari nol.
4. Penyimpanan cloud production.
5. Legal compliance formal seperti sertifikasi ISO atau DPIA penuh.

