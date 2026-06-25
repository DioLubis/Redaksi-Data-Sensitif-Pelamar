# Project Overview

## Nama Sistem

Applicant Privacy Shield.

## Judul Penelitian

Perbandingan YOLOv5 dan YOLO26 pada Sistem Deteksi dan Redaksi Data Visual Sensitif Pelamar Sebelum Pemrosesan AI Screening pada Applicant Tracking System Karierly.

## Ringkasan

Applicant Privacy Shield adalah privacy gateway untuk dokumen pelamar. Sistem ini ditempatkan sebelum modul AI Screening agar file CV atau dokumen pendukung tidak dikirim mentah ke Gemini API.

Sistem mendeteksi data sensitif visual dengan YOLOv5 dan YOLO26, mendeteksi data sensitif tekstual dengan OCR + regex/NER, melakukan redaksi otomatis, dan menghasilkan sanitized candidate profile untuk AI Screening.

## Problem Statement

CV pelamar sering memuat data pribadi yang tidak diperlukan untuk penilaian pekerjaan, seperti foto wajah, tanda tangan, nomor telepon, email pribadi, alamat lengkap, NIK, tanggal lahir, status pernikahan, agama, dan data keluarga. Jika CV mentah diproses langsung oleh Gemini, data yang tidak relevan dapat ikut terkirim ke layanan eksternal.

Masalah penelitian ini adalah bagaimana membangun pipeline hybrid computer vision dan NLP untuk mendeteksi serta meredaksi data sensitif sebelum AI Screening berjalan, sekaligus membandingkan YOLOv5 dan YOLO26 pada tugas deteksi area visual sensitif.

## Tujuan

1. Membangun prototype privacy gateway untuk dokumen pelamar.
2. Mendeteksi area visual sensitif pada CV/dokumen pendukung.
3. Mendeteksi teks sensitif memakai OCR, regex, dan/atau NER.
4. Membandingkan YOLOv5 dan YOLO26 dengan metrik kuantitatif.
5. Menghasilkan sanitized document dan sanitized candidate profile.
6. Mencegah file mentah dan data sensitif tidak relevan dikirim ke Gemini.
7. Menyediakan Privacy Risk Report, Redaction Report, dan audit trail.

## Aktor

| Aktor | Deskripsi |
|---|---|
| Candidate | Mengunggah CV atau dokumen pendukung |
| Recruiter | Melihat hasil screening dan ringkasan redaksi |
| Admin | Melihat status redaksi, report, dan audit trail |
| Privacy Worker | Menjalankan preprocessing, deteksi, redaksi, dan profile builder |
| AI Screening Service | Memanggil Gemini memakai sanitized candidate profile |
| Gemini API | Memproses data yang sudah disanitasi |

## Batasan

1. YOLO tidak digunakan untuk membaca isi CV.
2. File CV mentah tidak dikirim ke Gemini.
3. Gemini hanya menerima sanitized candidate profile.
4. Dataset harus open source, gratis, mudah diakses, dan diperiksa lisensinya.
5. Prototype difokuskan untuk penelitian lokal, bukan production hardening penuh.
6. Redaksi harus permanen pada sanitized document, bukan overlay visual sementara.

## Asumsi

1. Dokumen input utama berupa PDF, JPG, atau PNG.
2. Prototype dapat dijalankan lokal dengan PostgreSQL dan Redis.
3. Model YOLOv5 dan YOLO26 dibandingkan memakai dataset dan split yang sama.
4. Jika dataset CV open source mengandung PII nyata, data tersebut hanya digunakan sesuai lisensi dan tidak dikirim ke API eksternal.
5. Data yang masuk ke Gemini adalah hasil ekstraksi yang sudah melewati final PII guard.

