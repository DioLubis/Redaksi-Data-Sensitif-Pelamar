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
BACKENDS = ("yolov5", "yolo26")


def artifact_zip(directory: Path) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in directory.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(directory))
    return buffer.getvalue()


def latest_best_weight(backend: str) -> Path | None:
    candidates = sorted((ROOT / "experiments" / "runs" / backend).glob("**/weights/best.pt"), key=lambda path: path.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]
    fallback = sorted((ROOT / "artifacts").glob(f"trained_{backend}*/best.pt"), key=lambda path: path.stat().st_mtime, reverse=True)
    return fallback[0] if fallback else None


def discover_weights() -> dict[str, Path | None]:
    return {backend: latest_best_weight(backend) for backend in BACKENDS}


@st.cache_resource(show_spinner=False)
def load_detector(model_name: str, weights_path: str, yolov5_repo: str) -> YOLODetector:
    return YOLODetector(model_name, weights_path, yolov5_repo)


def show_evaluation() -> None:
    reports = ROOT / "experiments" / "reports"
    comparison = reports / "comparison.csv"
    st.subheader("Evaluasi Model")
    if comparison.is_file():
        frame = pd.read_csv(comparison)
        st.dataframe(frame, width="stretch", hide_index=True)
        chart = reports / "comparison_metrics.png"
        if chart.is_file():
            st.image(str(chart), caption="Perbandingan precision, recall, F1, mAP@50, dan mAP@50:95")
    else:
        quick_reports = sorted((ROOT / "artifacts").glob("trained_*/quick_evaluation.json"))
        if quick_reports:
            report = json.loads(quick_reports[-1].read_text(encoding="utf-8"))
            st.dataframe(pd.DataFrame([report]), width="stretch", hide_index=True)
        else:
            st.info("Hasil evaluasi belum tersedia. Jalankan training, evaluasi, benchmark, lalu generate_comparison_report.py.")


def show_result(result: dict, output_dir: Path, key_prefix: str) -> None:
    report = result["report"]
    profile = result["profile"]
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
        st.download_button("Unduh redacted PDF", data=Path(result["redacted_pdf"]).read_bytes(), file_name=f"{key_prefix}_redacted_document.pdf", mime="application/pdf", key=f"{key_prefix}_pdf")
        for name in ["detection_result.json", "ocr_result.json", "sanitized_candidate_profile.json", "privacy_risk_report.json"]:
            path = output_dir / name
            st.download_button(f"Unduh {name}", data=path.read_bytes(), file_name=f"{key_prefix}_{name}", mime="application/json", key=f"{key_prefix}_{name}")
        st.download_button("Unduh semua output", data=artifact_zip(output_dir), file_name=f"{key_prefix}_privacy_shield_output.zip", mime="application/zip", key=f"{key_prefix}_zip")


def show_comparison(results: dict[str, tuple[dict, Path]]) -> None:
    st.success("Redaksi selesai. Kedua backend diproses pada file yang sama.")
    rows = []
    for backend, (result, output_dir) in results.items():
        report = result["report"]
        visual_count = sum(
            1
            for page in result["detections"]["pages"]
            for detection in page["detections"]
            if detection["source"] in {"visual", "opencv_face_fallback"}
        )
        face_count = sum(
            1
            for page in result["detections"]["pages"]
            for detection in page["detections"]
            if detection["category"] == "face_photo"
        )
        rows.append({
            "backend": backend.upper(),
            "detections": report["detection_count"],
            "visual_detections": visual_count,
            "face_photo": face_count,
            "risk_level": report["risk_level"],
            "processing_s": round(report["processing_time_ms"] / 1000, 2),
            "output": str(output_dir),
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    tabs = st.tabs([backend.upper() for backend in results])
    for tab, (backend, (result, output_dir)) in zip(tabs, results.items()):
        with tab:
            show_result(result, output_dir, backend)


def main() -> None:
    st.set_page_config(page_title="Applicant Privacy Shield", page_icon="PS", layout="wide")
    st.title("Applicant Privacy Shield")
    st.caption("Redaksi lokal dokumen pelamar sebelum AI Screening. Dokumen mentah tidak dikirim ke Gemini.")
    with st.sidebar:
        st.header("Konfigurasi Scan")
        weights = discover_weights()
        yolov5_repo = str(ROOT / "external" / "yolov5")
        for backend, path in weights.items():
            st.text_input(f"Weights {backend.upper()}", value=str(path) if path else "Belum ditemukan", disabled=True)
        ocr_language = st.text_input("Bahasa OCR", value="eng")
        st.divider()
        st.caption("Scan menjalankan YOLOv5 dan YOLO26 otomatis untuk perbandingan.")
        st.caption("Kelas visual dataset: face/photo, signature, QR code, barcode, dan ID card.")
        st.caption("Email, telepon, alamat, dan nomor dokumen ditangani OCR + regex.")

    upload_tab, evaluation_tab, explanation_tab = st.tabs(["Scan Dokumen", "Evaluasi Sistem", "Penjelasan Output"])
    with upload_tab:
        uploaded = st.file_uploader("Unggah PDF, JPG, atau PNG", type=["pdf", "jpg", "jpeg", "png"])
        if uploaded is not None:
            st.write(f"File diterima: tipe {uploaded.type or 'unknown'}, ukuran {uploaded.size / 1024 / 1024:.2f} MB")
        if st.button("Jalankan Redaksi", type="primary", disabled=uploaded is None):
            missing = [backend.upper() for backend, path in weights.items() if path is None or not path.is_file()]
            if missing:
                st.error(f"Weights belum lengkap untuk: {', '.join(missing)}. Selesaikan training kedua model terlebih dahulu.")
            else:
                scan_id = uuid.uuid4().hex
                scan_results: dict[str, tuple[dict, Path]] = {}
                with st.spinner("Memproses dokumen dengan YOLOv5 dan YOLO26 secara lokal..."):
                    try:
                        with tempfile.TemporaryDirectory(prefix="privacy_upload_") as temporary:
                            input_path = Path(temporary) / f"upload{Path(uploaded.name).suffix.lower()}"
                            input_path.write_bytes(uploaded.getbuffer())
                            for backend in BACKENDS:
                                output_dir = ARTIFACTS_ROOT / scan_id / backend
                                detector = load_detector(backend, str(weights[backend]), yolov5_repo)
                                result = run_privacy_pipeline(input_path, output_dir, detector, TesseractOCRExtractor(ocr_language))
                                scan_results[backend] = (result, output_dir)
                        st.session_state["latest_results"] = scan_results
                    except Exception as exc:
                        shutil.rmtree(ARTIFACTS_ROOT / scan_id, ignore_errors=True)
                        st.error(f"Scan tidak dapat dijalankan: {exc}")
        if "latest_results" in st.session_state:
            show_comparison(st.session_state["latest_results"])
    with evaluation_tab:
        show_evaluation()
    with explanation_tab:
        st.subheader("Arti Output")
        st.markdown("- **Redacted PDF dan halaman**: dokumen baru yang area sensitifnya telah disamarkan permanen.\n- **Detection JSON**: kategori, lokasi, sumber deteksi, confidence, dan metode redaksi tanpa isi PII.\n- **OCR JSON**: koordinat dan hash token OCR, dengan text token disamarkan.\n- **Sanitized profile**: hanya informasi relevan seperti skill, pengalaman, pendidikan, dan sertifikasi. Ini satu-satunya payload yang boleh diberikan ke Gemini.\n- **Privacy report**: jumlah deteksi, risk level, durasi, dan status guard payload Gemini.")
        st.subheader("Batasan Evaluasi")
        st.markdown("Metrik leakage, over-redaction, dan akurasi OCR memerlukan ground truth yang telah diaudit. Nilai tersebut tidak boleh diinterpretasikan jika belum ada audit manual.")


if __name__ == "__main__":
    main()
