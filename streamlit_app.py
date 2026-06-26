from __future__ import annotations

import json
import shutil
import sys
import tempfile
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from privacy_shield.ocr_extractor import TesseractOCRExtractor
from privacy_shield.pipeline import run_privacy_pipeline
from privacy_shield.yolo_detector import YOLODetector

ARTIFACTS_ROOT = ROOT / "artifacts"
DEFAULT_WEIGHTS = ROOT / "experiments" / "runs" / "yolo26" / "yolo26n_seed42" / "weights" / "best.pt"


def artifact_zip(directory: Path) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in directory.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(directory))
    return buffer.getvalue()


@st.cache_resource(show_spinner=False)
def load_detector(model_name: str, weights_path: str, yolov5_repo: str) -> YOLODetector:
    return YOLODetector(model_name, weights_path, yolov5_repo)


def show_evaluation() -> None:
    reports = ROOT / "experiments" / "reports"
    comparison = reports / "comparison.csv"
    st.subheader("Evaluasi Model")
    if comparison.is_file():
        frame = pd.read_csv(comparison)
        st.dataframe(frame, use_container_width=True, hide_index=True)
        chart = reports / "comparison_metrics.png"
        if chart.is_file():
            st.image(str(chart), caption="Perbandingan precision, recall, F1, mAP@50, dan mAP@50:95")
    else:
        st.info("Hasil evaluasi belum tersedia. Jalankan training, evaluasi, benchmark, lalu generate_comparison_report.py.")


def show_result(result: dict, output_dir: Path) -> None:
    report = result["report"]
    profile = result["profile"]
    st.success("Redaksi selesai. Hanya artefak tersanitasi yang disimpan pada folder output.")
    metrics = st.columns(4)
    metrics[0].metric("Deteksi sensitif", report["detection_count"])
    metrics[1].metric("Risk level", report["risk_level"].upper())
    metrics[2].metric("Waktu proses", f"{report['processing_time_ms'] / 1000:.2f} s")
    metrics[3].metric("Gemini safe payload", "PASS" if report["gemini_safe_payload_pass"] else "BLOCKED")

    tabs = st.tabs(["Halaman Tersensor", "Profile Aman", "Privacy Report", "JSON dan PDF"])
    with tabs[0]:
        for index, page in enumerate(result["redacted_pages"], start=1):
            st.image(page, caption=f"Halaman {index} yang sudah disensor")
    with tabs[1]:
        st.json(profile)
    with tabs[2]:
        st.json(report)
    with tabs[3]:
        st.download_button("Unduh redacted PDF", data=Path(result["redacted_pdf"]).read_bytes(), file_name="redacted_document.pdf", mime="application/pdf")
        for name in ["detection_result.json", "ocr_result.json", "sanitized_candidate_profile.json", "privacy_risk_report.json"]:
            path = output_dir / name
            st.download_button(f"Unduh {name}", data=path.read_bytes(), file_name=name, mime="application/json", key=name)
        st.download_button("Unduh semua output", data=artifact_zip(output_dir), file_name="privacy_shield_output.zip", mime="application/zip")


def main() -> None:
    st.set_page_config(page_title="Applicant Privacy Shield", page_icon="PS", layout="wide")
    st.title("Applicant Privacy Shield")
    st.caption("Redaksi lokal dokumen pelamar sebelum AI Screening. Dokumen mentah tidak dikirim ke Gemini.")
    with st.sidebar:
        st.header("Konfigurasi Scan")
        model_name = st.selectbox("Model visual", ["yolo26", "yolov5"])
        weights = st.text_input("Path weights terbaik", value=str(DEFAULT_WEIGHTS))
        yolov5_repo = st.text_input("Path repository YOLOv5", value=str(ROOT / "external" / "yolov5"), disabled=model_name != "yolov5")
        ocr_language = st.text_input("Bahasa OCR", value="eng")
        st.divider()
        st.caption("Kelas visual dataset: face/photo, signature, QR code, barcode, dan ID card.")
        st.caption("Email, telepon, alamat, dan nomor dokumen ditangani OCR + regex.")

    upload_tab, evaluation_tab, explanation_tab = st.tabs(["Scan Dokumen", "Evaluasi Sistem", "Penjelasan Output"])
    with upload_tab:
        uploaded = st.file_uploader("Unggah PDF, JPG, atau PNG", type=["pdf", "jpg", "jpeg", "png"])
        if uploaded is not None:
            st.write(f"File diterima: tipe {uploaded.type or 'unknown'}, ukuran {uploaded.size / 1024 / 1024:.2f} MB")
        if st.button("Jalankan Redaksi", type="primary", disabled=uploaded is None):
            if not Path(weights).is_file():
                st.error("Weights belum ditemukan. Selesaikan training atau masukkan path best.pt yang benar.")
            else:
                scan_id = uuid.uuid4().hex
                output_dir = ARTIFACTS_ROOT / scan_id
                with st.spinner("Memproses dokumen secara lokal dan membuat output tersanitasi..."):
                    try:
                        with tempfile.TemporaryDirectory(prefix="privacy_upload_") as temporary:
                            input_path = Path(temporary) / f"upload{Path(uploaded.name).suffix.lower()}"
                            input_path.write_bytes(uploaded.getbuffer())
                            detector = load_detector(model_name, weights, yolov5_repo)
                            result = run_privacy_pipeline(input_path, output_dir, detector, TesseractOCRExtractor(ocr_language))
                        st.session_state["latest_result"] = (result, output_dir)
                    except Exception as exc:
                        shutil.rmtree(output_dir, ignore_errors=True)
                        st.error(f"Scan tidak dapat dijalankan: {exc}")
        if "latest_result" in st.session_state:
            result, output_dir = st.session_state["latest_result"]
            show_result(result, output_dir)
    with evaluation_tab:
        show_evaluation()
    with explanation_tab:
        st.subheader("Arti Output")
        st.markdown("- **Redacted PDF dan halaman**: dokumen baru yang area sensitifnya telah disamarkan permanen.\n- **Detection JSON**: kategori, lokasi, sumber deteksi, confidence, dan metode redaksi tanpa isi PII.\n- **OCR JSON**: koordinat dan hash token OCR, dengan text token disamarkan.\n- **Sanitized profile**: hanya informasi relevan seperti skill, pengalaman, pendidikan, dan sertifikasi. Ini satu-satunya payload yang boleh diberikan ke Gemini.\n- **Privacy report**: jumlah deteksi, risk level, durasi, dan status guard payload Gemini.")
        st.subheader("Batasan Evaluasi")
        st.markdown("Metrik leakage, over-redaction, dan akurasi OCR memerlukan ground truth yang telah diaudit. Nilai tersebut tidak boleh diinterpretasikan jika belum ada audit manual.")


if __name__ == "__main__":
    main()
