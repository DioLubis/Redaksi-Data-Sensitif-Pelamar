# Risk Mitigation

## Risiko Teknis

| Risiko | Dampak | Mitigasi |
|---|---|---|
| YOLO gagal mendeteksi data sensitif visual | PII visual lolos | Gunakan threshold konservatif, prioritaskan recall, gabungkan dengan OCR/regex |
| OCR salah membaca teks | PII tekstual lolos | Gunakan regex multi-format, NER, dan final PII guard |
| PDF masih menyimpan text layer asli | Redaksi tidak permanen | Flatten sanitized PDF menjadi image-based PDF |
| YOLO26 tidak tersedia lokal | Perbandingan tidak lengkap | Buat adapter dan dokumentasikan unavailable secara jujur |
| Dataset tidak punya anotasi lengkap | Evaluasi lemah | Anotasi subset dengan label schema tetap |
| Multi-page PDF lambat | UX buruk | Jalankan sebagai background job |
| Log menyimpan PII | Kebocoran privasi | Terapkan logging policy tanpa raw PII |

## Risiko Privasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| File mentah terkirim ke Gemini | Pelanggaran prinsip sistem | Backend hanya mengizinkan sanitized profile untuk safe screening |
| Prompt masih mengandung email/telepon/alamat | PII leakage | Final PII guard sebelum request |
| Recruiter melihat data sensitif yang tidak diperlukan | Bias atau privasi terganggu | Tampilkan sanitized profile dan redaction summary |
| Dataset open source mengandung PII nyata | Risiko etis | Gunakan lokal, cek lisensi, jangan kirim ke API eksternal |

## Risiko Penelitian

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Klaim YOLO26 tidak valid | Penelitian tidak kredibel | Pakai dokumentasi resmi dan catat versi package |
| Perbandingan model tidak adil | Hasil bias | Split, label, hardware, dan metrik harus sama |
| Dataset terlalu kecil | Generalisasi rendah | Jelaskan keterbatasan dan gunakan beberapa dataset |
| Overclaim terhadap Karierly | Analisis tidak akademik | Posisikan sebagai prototype privacy gateway, bukan fitur production final |

## Privacy Guardrail

Sebelum Gemini dipanggil, sistem wajib memeriksa:

1. Tidak ada raw document path di payload.
2. Tidak ada base64 file.
3. Tidak ada email.
4. Tidak ada nomor telepon.
5. Tidak ada NIK/NPWP.
6. Tidak ada alamat lengkap.
7. Tidak ada tanggal lahir.
8. Tidak ada data keluarga.
9. Tidak ada field `original_text`.
10. Tidak ada OCR raw text penuh tanpa sanitasi.

Jika guard gagal, request diblokir dan audit log dibuat.

