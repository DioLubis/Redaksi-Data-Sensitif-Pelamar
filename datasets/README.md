# Dataset Workspace

Folder ini menyimpan dataset untuk Applicant Privacy Shield.

## Struktur

```text
datasets/
  raw/                     # dataset sumber hasil download, tidak langsung dipakai training
  interim/                 # hasil konversi sementara
  manifests/               # manifest sumber, split, dan audit dataset
  privacy_shield/
    data.yaml              # konfigurasi YOLOv5/YOLO26
    images/
      train/
      val/
      test/
    labels/
      train/
      val/
      test/
```

## Aturan

1. Dataset final untuk training berada di `datasets/privacy_shield`.
2. Format label final adalah YOLO detection format.
3. Satu image harus memiliki satu file label dengan nama stem yang sama.
4. File original dari dataset sumber tetap berada di `datasets/raw`.
5. Jangan masukkan CV pribadi, KTP asli, atau dokumen pribadi nyata yang tidak berasal dari dataset open source berlisensi jelas.

