Ringkasan Sistem
Sistem yang akan dibuat adalah privacy gateway untuk Karierly sebelum modul AI Screening berjalan. Sistem ini menerima CV atau dokumen pendukung pelamar, mendeteksi bagian visual dan teks yang berpotensi sensitif, melakukan redaksi otomatis, lalu hanya mengirim data yang sudah disanitasi ke Gemini API.
YOLOv5 dan YOLO26 digunakan hanya untuk deteksi area visual sensitif, bukan untuk membaca isi CV. Untuk isi teks, sistem menggunakan OCR, regex, dan/atau NER. Hasil akhirnya adalah dokumen/redaksi aman, sanitized candidate profile, Privacy Risk Report, Redaction Report, serta metrik evaluasi perbandingan model.
Problem Statement
CV pelamar dapat berisi data pribadi seperti foto wajah, tanda tangan, QR code, alamat, nomor telepon, email pribadi, NIK, tanggal lahir, atau identitas lain. Jika file mentah langsung dikirim ke Gemini API, data tersebut ikut diproses oleh layanan AI eksternal, padahal tidak semuanya relevan untuk penilaian pekerjaan.
Masalah utama sistem ini adalah bagaimana mendeteksi, menyensor, dan memisahkan data sensitif dari informasi yang relevan untuk screening pekerjaan sebelum data masuk ke Gemini.
Tujuan Sistem
Mendeteksi area visual sensitif pada CV dan dokumen pendukung.
Membandingkan performa YOLOv5 dan YOLO26 secara adil.
Melakukan redaksi otomatis pada area visual dan teks sensitif.
Menghasilkan sanitized candidate profile untuk AI Screening.
Mencegah data pribadi tidak relevan dikirim ke Gemini.
Menyediakan laporan risiko privasi dan laporan redaksi.
Menyediakan metrik evaluasi deteksi, redaksi, dan perlindungan data.
Menjaga eksperimen tetap reproducible dengan dataset sintetis/dummy.
Daftar Modul
Document Ingestion Module
Menerima file CV/dokumen pendukung, misalnya PDF, JPG, PNG, atau hasil konversi halaman dokumen.

Document Preprocessing Module
Mengubah PDF menjadi image per halaman, melakukan normalisasi ukuran, resolusi, orientasi, dan metadata dokumen.

Visual Sensitive Object Detection Module
Menjalankan YOLOv5 dan YOLO26 melalui adapter yang seragam untuk mendeteksi objek visual sensitif seperti foto wajah, tanda tangan, QR code, barcode, ID card, stempel, dan elemen identitas visual lain.

OCR Module
Mengekstrak teks dari dokumen hasil preprocessing untuk dianalisis lebih lanjut.

Text Sensitive Data Detection Module
Menggunakan regex dan/atau NER untuk mendeteksi email pribadi, nomor telepon, NIK, alamat lengkap, tanggal lahir, nama keluarga, URL personal, nomor rekening, dan data sensitif lain.

Redaction Engine
Melakukan masking, blurring, black-box redaction, atau removal terhadap area sensitif visual dan teks.

Sanitized Candidate Profile Builder
Menghasilkan data kandidat yang hanya berisi informasi relevan seperti pengalaman kerja, pendidikan, skill, sertifikasi, proyek, bahasa, dan ringkasan profesional.

Safe Prompt Builder for Gemini
Menyusun prompt Gemini hanya dari sanitized profile, bukan dari file mentah.

Privacy Risk Report Module
Menampilkan jenis data sensitif yang ditemukan, tingkat risiko, lokasi halaman, confidence, dan status redaksi.

Redaction Report Module
   Mencatat area mana yang disensor, metode redaksi, model yang mendeteksi, confidence score, dan status akhir.

Model Evaluation Module
   Mengukur performa YOLOv5 vs YOLO26 menggunakan mAP, precision, recall, F1-score, latency, model size, inference speed, dan false negative rate pada data sensitif.

Audit & Reproducibility Module
   Menyimpan konfigurasi eksperimen, seed, versi model, dataset manifest, parameter training, dan hasil evaluasi.

Aktor Sistem
Pelamar
Mengunggah CV atau dokumen lamaran melalui career page.

Recruiter
Melihat kandidat, hasil AI Screening, laporan redaksi, dan laporan risiko privasi.

Admin
Mengelola konfigurasi sistem, kebijakan redaksi, dataset evaluasi, dan akses laporan.

AI Screening Service
Modul Karierly yang menerima sanitized candidate profile untuk dianalisis oleh Gemini.

Privacy Gateway Service
Sistem baru yang berada di antara upload dokumen dan AI Screening.

Gemini API
Layanan eksternal yang hanya menerima data hasil sanitasi, bukan file CV mentah.

Data Sensitif yang Harus Dilindungi
Foto wajah pelamar.
Tanda tangan.
QR code.
Barcode.
KTP, SIM, paspor, kartu mahasiswa, atau ID card lain.
NIK atau nomor identitas nasional.
Alamat lengkap.
Nomor telepon pribadi.
Email pribadi jika tidak diperlukan untuk scoring.
Tanggal lahir.
Tempat lahir.
Status pernikahan.
Agama.
Jenis kelamin jika tidak relevan dengan pekerjaan.
Nomor rekening.
NPWP.
Link personal yang tidak relevan.
Foto dokumen sertifikat yang memuat nomor identitas.
Metadata file yang dapat mengandung nama asli, lokasi, atau informasi perangkat.
Informasi keluarga atau kontak darurat.
Arsitektur Sistem
High-level architecture:
Career Page / Upload CV
        |
        v
Document Ingestion Service
        |
        v
Document Preprocessing
(PDF to image, page normalization, metadata stripping)
        |
        +-----------------------------+
        |                             |
        v                             v
YOLO Visual Detection             OCR Extraction
(YOLOv5 / YOLO26 Adapter)          |
        |                           v
        |                    Regex / NER Sensitive Text Detection
        |                             |
        +-------------+---------------+
                      |
                      v
              Redaction Engine
                      |
          +-----------+------------+
          |                        |
          v                        v
Sanitized Document          Sanitized Candidate Profile
          |                        |
          v                        v
Redaction Report       Safe Prompt Builder
Privacy Risk Report            |
                               v
                         Gemini API
                               |
                               v
                     Karierly AI Screening Result
                     
Arsitektur ini memisahkan tiga hal penting:
Deteksi visual oleh YOLO.
Deteksi teks sensitif oleh OCR + regex/NER.
Prompt aman ke Gemini tanpa file mentah.
Data Flow
Pelamar mengunggah CV atau dokumen pendukung.
Sistem menyimpan file mentah sementara di area terbatas.
Dokumen diproses menjadi halaman image jika formatnya PDF.
Metadata file dibersihkan atau diabaikan dari pipeline AI.
YOLOv5 mendeteksi area visual sensitif.
YOLO26 mendeteksi area visual sensitif melalui adapter yang sama.
OCR mengekstrak teks dari dokumen.
Regex/NER mendeteksi teks sensitif.
Sistem menggabungkan hasil deteksi visual dan teks.
Redaction Engine menyensor area sensitif.
Sistem membuat sanitized document.
Sistem membuat sanitized candidate profile.
Safe Prompt Builder menyusun prompt Gemini dari data yang sudah disaring.
Gemini menerima hanya data relevan untuk penilaian pekerjaan.
Hasil Gemini dikembalikan ke modul AI Screening Karierly.
Recruiter/admin dapat melihat Redaction Report dan Privacy Risk Report.
Metrik evaluasi model dan perlindungan data disimpan untuk eksperimen.
Risiko dan Mitigasi
YOLO gagal mendeteksi data sensitif visual
Mitigasi: gunakan confidence threshold konservatif, ensemble rule dari YOLO + OCR, dan prioritaskan recall untuk kelas sensitif.

OCR salah membaca teks sensitif
Mitigasi: gunakan kombinasi OCR, regex multi-format, kamus pola Indonesia, dan NER; tambahkan fallback manual review untuk risiko tinggi.

False negative pada data sensitif lebih berbahaya daripada false positive
Mitigasi: gunakan kebijakan privacy-first, yaitu lebih baik menyensor area yang meragukan daripada membiarkan data sensitif lolos.

YOLO26 belum tersedia atau belum jelas package resminya
Mitigasi: jangan mengarang implementasi. Pada tahap implementasi nanti, package/dokumentasi YOLO26 harus diverifikasi. Sistem dibuat dengan model adapter agar YOLOv5 dan YOLO26 memakai interface, dataset, metrik, dan pipeline evaluasi yang sama.

Perbandingan YOLOv5 vs YOLO26 tidak adil
Mitigasi: gunakan dataset yang sama, split yang sama, seed yang sama, kelas yang sama, augmentation yang terdokumentasi, hardware yang dicatat, dan metrik yang konsisten.

Data dummy tidak realistis
Mitigasi: buat dataset sintetis yang menyerupai struktur CV nyata tanpa memakai data pribadi asli.

Sanitized profile kehilangan informasi penting untuk screening
Mitigasi: pisahkan data relevan dan data sensitif dengan policy yang jelas. Skill, pengalaman, pendidikan, proyek, sertifikasi, dan riwayat kerja tetap dipertahankan.

Prompt Gemini masih mengandung data sensitif
Mitigasi: lakukan final prompt inspection menggunakan regex/NER ulang sebelum request dikirim ke Gemini.

Redaksi hanya visual, tetapi teks masih tersimpan di layer PDF
Mitigasi: flatten hasil redaksi menjadi image/PDF baru dan pastikan teks sensitif tidak tersisa sebagai selectable text.

Audit sulit direproduksi
   Mitigasi: simpan manifest dataset, config training, versi dependency, model checkpoint, hash file, seed, dan laporan eksperimen.

Deliverables
Dokumen desain sistem dan arsitektur.
Struktur folder proyek setelah desain disetujui.
Dataset sintetis/dummy untuk CV dan dokumen pendukung.
Skema anotasi data sensitif visual.
Adapter model YOLOv5 dan YOLO26.
Pipeline training dan evaluasi YOLOv5.
Pipeline training dan evaluasi YOLO26, jika package/dokumentasi tersedia.
OCR + regex/NER sensitive text detector.
Redaction Engine untuk visual dan teks.
Safe Prompt Builder untuk Gemini.
Sanitized Candidate Profile schema.
Privacy Risk Report.
Redaction Report.
Model Evaluation Report.
Privacy Protection Metrics Report.
Reproducibility package berisi config, seed, manifest, dan command eksperimen.
Dokumentasi integrasi konseptual dengan Karierly AI Screening.