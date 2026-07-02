from __future__ import annotations

import hashlib
import json
import logging
import shutil
import sys
import tempfile
import time
import uuid
import zipfile
import base64
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from privacy_shield.ocr_extractor import TesseractOCRExtractor
from privacy_shield.pipeline import run_privacy_pipeline
from privacy_shield.pdf_to_image import document_to_images
from privacy_shield.yolo_detector import YOLODetector

ARTIFACTS_ROOT = ROOT / "artifacts"
LOGS_ROOT = ARTIFACTS_ROOT / "logs"
BACKENDS = ("yolov5", "yolo26")


def get_logger() -> logging.Logger:
    LOGS_ROOT.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("privacy_shield_streamlit")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(LOGS_ROOT / "streamlit_scans.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger


def artifact_zip(directory: Path) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in directory.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(directory))
    return buffer.getvalue()


def image_data_uri(path: str | Path) -> str:
    image_path = Path(path)
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def before_after_document_slider(before_pages: list[str | Path], after_pages: list[str | Path], key: str, height: int | None = None) -> None:
    component_id = f"compare_{hashlib.sha256(key.encode('utf-8')).hexdigest()[:12]}"
    page_count = min(len(before_pages), len(after_pages))
    page_blocks = []
    for index, (before_path, after_path) in enumerate(zip(before_pages, after_pages), start=1):
        before = image_data_uri(before_path)
        after = image_data_uri(after_path)
        page_blocks.append(f"""
          <section class="page-compare">
            <div class="page-label">Halaman {index}</div>
            <div class="compare-frame">
              <img class="before-img" src="{before}" alt="Dokumen asli halaman {index}">
              <div class="redacted-layer">
                <img class="after-img" src="{after}" alt="Dokumen tersensor halaman {index}">
              </div>
              <div class="label after-label">Sesudah blok</div>
              <div class="label before-label">Sebelum</div>
            </div>
          </section>
        """)
    component_height = height or min(2400, max(860, 820 * page_count))
    html = f"""
    <style>
      #{component_id} {{
        width: 100%;
        max-width: 980px;
        margin: 0 auto;
      }}
      #{component_id} .slider-bar {{
        position: sticky;
        top: 0;
        z-index: 20;
        padding: 10px 12px 12px;
        border: 1px solid #d0d5dd;
        background: rgba(255, 255, 255, 0.96);
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
      }}
      #{component_id} .slider-row {{
        display: flex;
        align-items: center;
        gap: 10px;
        font: 13px Arial, sans-serif;
        color: #111827;
      }}
      #{component_id} input[type="range"] {{
        flex: 1;
      }}
      #{component_id} .page-compare {{
        margin: 18px auto 26px;
      }}
      #{component_id} .page-label {{
        margin: 0 0 8px;
        color: #344054;
        font: 600 13px Arial, sans-serif;
      }}
      #{component_id} .compare-frame {{
        position: relative;
        width: 100%;
        border: 1px solid #d0d5dd;
        background: #111827;
        overflow: hidden;
      }}
      #{component_id} .compare-frame img {{
        display: block;
        width: 100%;
        height: auto;
        user-select: none;
        pointer-events: none;
      }}
      #{component_id} .redacted-layer {{
        position: absolute;
        inset: 0 auto 0 0;
        width: 50%;
        overflow: hidden;
        border-right: 2px solid #ffffff;
      }}
      #{component_id} .redacted-layer img {{
        width: var(--image-width, 100%);
        max-width: none;
      }}
      #{component_id} .label {{
        position: absolute;
        top: 10px;
        padding: 4px 8px;
        background: rgba(17, 24, 39, 0.78);
        color: #fff;
        font: 12px Arial, sans-serif;
        border-radius: 4px;
      }}
      #{component_id} .before-label {{ right: 10px; }}
      #{component_id} .after-label {{ left: 10px; }}
    </style>
    <div id="{component_id}">
      <div class="slider-bar">
        <div class="slider-row">
          <span>Sesudah blok</span>
          <input id="{component_id}_range" type="range" min="0" max="100" value="50" aria-label="Geser perbandingan sebelum dan sesudah">
          <span>Sebelum</span>
        </div>
      </div>
      {''.join(page_blocks)}
    </div>
    <script>
      const box = document.getElementById("{component_id}");
      const slider = document.getElementById("{component_id}_range");
      function syncWidth() {{
        box.querySelectorAll(".compare-frame").forEach((frame) => {{
          frame.querySelector(".after-img").style.setProperty("--image-width", frame.clientWidth + "px");
        }});
      }}
      function update() {{
        box.querySelectorAll(".redacted-layer").forEach((layer) => {{
          layer.style.width = slider.value + "%";
        }});
        syncWidth();
      }}
      slider.addEventListener("input", update);
      window.addEventListener("resize", update);
      update();
    </script>
    """
    components.html(html, height=component_height, scrolling=True)


def safe_file_meta(uploaded) -> dict:
    name_hash = hashlib.sha256(uploaded.name.encode("utf-8")).hexdigest()[:16]
    return {
        "file_id": name_hash,
        "extension": Path(uploaded.name).suffix.lower(),
        "size_bytes": uploaded.size,
        "size_mb": round(uploaded.size / 1024 / 1024, 3),
        "mime_type": uploaded.type or "unknown",
    }


def append_scan_log(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(f"{datetime.now(UTC).isoformat()} {message}\n")


def latest_best_weight(backend: str) -> Path | None:
    candidates = sorted((ROOT / "experiments" / "runs" / backend).glob("**/weights/best.pt"), key=lambda path: path.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]
    fallback = sorted((ROOT / "artifacts").glob(f"trained_{backend}*/best.pt"), key=lambda path: path.stat().st_mtime, reverse=True)
    return fallback[0] if fallback else None


def discover_weights() -> dict[str, Path | None]:
    return {backend: latest_best_weight(backend) for backend in BACKENDS}


def detection_summary(result: dict) -> dict:
    detections = [detection for page in result["detections"]["pages"] for detection in page["detections"]]
    model_visual = [item for item in detections if item["source"] == "visual"]
    fallback_visual = [item for item in detections if item["source"] == "opencv_face_fallback"]
    visual = [*model_visual, *fallback_visual]
    ocr = [item for item in detections if item["source"] == "ocr_regex"]
    categories: dict[str, int] = {}
    sources: dict[str, int] = {}
    redaction_methods: dict[str, int] = {}
    for item in detections:
        categories[item["category"]] = categories.get(item["category"], 0) + 1
        sources[item["source"]] = sources.get(item["source"], 0) + 1
        redaction_methods[item["redaction_method"]] = redaction_methods.get(item["redaction_method"], 0) + 1
    return {
        "detection_count": len(detections),
        "visual_detection_count": len(visual),
        "yolo_visual_detection_count": len(model_visual),
        "opencv_face_fallback_count": len(fallback_visual),
        "ocr_regex_detection_count": len(ocr),
        "face_photo_count": categories.get("face_photo", 0),
        "detections_by_category": categories,
        "detections_by_source": sources,
        "redaction_methods": redaction_methods,
        "pages_processed": len(result["detections"]["pages"]),
    }


def build_batch_report(scan_id: str, documents: dict[str, dict], weights: dict[str, Path | None], started: float) -> dict:
    rows = []
    backend_totals: dict[str, dict] = {}
    for document_id, payload in documents.items():
        for backend, (result, output_dir) in payload["results"].items():
            report = result["report"]
            summary = detection_summary(result)
            row = {
                "document_id": document_id,
                "backend": backend,
                "file": payload["file"],
                "original_preview_pages": [str(path) for path in payload["original_pages"]],
                "output_dir": str(output_dir),
                "risk_level": report["risk_level"],
                "processing_time_ms": report["processing_time_ms"],
                "gemini_safe_payload_pass": report["gemini_safe_payload_pass"],
                **summary,
            }
            rows.append(row)
            totals = backend_totals.setdefault(
                backend,
                {"documents": 0, "detections": 0, "visual_detections": 0, "ocr_regex_detections": 0, "face_photo": 0, "processing_time_ms": 0.0},
            )
            totals["documents"] += 1
            totals["detections"] += summary["detection_count"]
            totals["visual_detections"] += summary["visual_detection_count"]
            totals["yolo_visual_detections"] = totals.get("yolo_visual_detections", 0) + summary["yolo_visual_detection_count"]
            totals["opencv_face_fallback"] = totals.get("opencv_face_fallback", 0) + summary["opencv_face_fallback_count"]
            totals["ocr_regex_detections"] += summary["ocr_regex_detection_count"]
            totals["face_photo"] += summary["face_photo_count"]
            totals["processing_time_ms"] += report["processing_time_ms"]
    for totals in backend_totals.values():
        totals["avg_processing_time_ms"] = round(totals["processing_time_ms"] / max(1, totals["documents"]), 2)
    return {
        "schema_version": "1.0",
        "report_type": "batch_system_evaluation_report",
        "scan_id": scan_id,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "document_count": len(documents),
        "backend_count": len(BACKENDS),
        "weights": {backend: str(path) if path else None for backend, path in weights.items()},
        "summary_by_backend": backend_totals,
        "documents": rows,
        "total_processing_time_ms": round((time.perf_counter() - started) * 1000, 2),
        "privacy_notice": "Report stores file hashes, metadata, categories, boxes/counts, and output paths. Original preview pages are saved locally only for before-after comparison and may contain visible PII.",
    }


def save_batch_artifacts(scan_dir: Path, report: dict) -> None:
    scan_dir.mkdir(parents=True, exist_ok=True)
    (scan_dir / "batch_system_evaluation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    flat_rows = []
    for row in report["documents"]:
        flat = {key: value for key, value in row.items() if key not in {"file", "detections_by_category", "detections_by_source", "redaction_methods"}}
        flat.update({
            "file_id": row["file"]["file_id"],
            "file_extension": row["file"]["extension"],
            "file_size_mb": row["file"]["size_mb"],
            "detections_by_category": json.dumps(row["detections_by_category"], sort_keys=True),
            "detections_by_source": json.dumps(row["detections_by_source"], sort_keys=True),
            "redaction_methods": json.dumps(row["redaction_methods"], sort_keys=True),
        })
        flat_rows.append(flat)
    pd.DataFrame(flat_rows).to_csv(scan_dir / "batch_system_evaluation_report.csv", index=False)


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
    st.subheader("Evaluasi Sistem Batch")
    batch_reports = sorted(ARTIFACTS_ROOT.glob("*/batch_system_evaluation_report.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not batch_reports:
        st.info("Report evaluasi sistem batch belum tersedia. Jalankan scan dokumen dari tab Scan Dokumen.")
        return
    selected = st.selectbox("Report batch tersimpan", batch_reports, format_func=lambda path: f"{path.parent.name} - {datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
    report = json.loads(selected.read_text(encoding="utf-8"))
    st.json({
        "scan_id": report["scan_id"],
        "document_count": report["document_count"],
        "summary_by_backend": report["summary_by_backend"],
        "total_processing_time_ms": report["total_processing_time_ms"],
        "privacy_notice": report["privacy_notice"],
    })
    st.dataframe(pd.DataFrame(report["documents"]), width="stretch", hide_index=True)
    csv_path = selected.parent / "batch_system_evaluation_report.csv"
    if csv_path.is_file():
        st.download_button("Unduh CSV report batch", data=csv_path.read_bytes(), file_name="batch_system_evaluation_report.csv", mime="text/csv", key=f"{report['scan_id']}_eval_csv")


def show_result(result: dict, output_dir: Path, key_prefix: str, original_pages: list[Path] | None = None) -> None:
    report = result["report"]
    profile = result["profile"]
    metrics = st.columns(4)
    metrics[0].metric("Deteksi sensitif", report["detection_count"])
    metrics[1].metric("Risk level", report["risk_level"].upper())
    metrics[2].metric("Waktu proses", f"{report['processing_time_ms'] / 1000:.2f} s")
    metrics[3].metric("Gemini safe payload", "PASS" if report["gemini_safe_payload_pass"] else "BLOCKED")

    tabs = st.tabs(["Slider Sebelum/Sesudah", "Halaman Tersensor", "Profile Aman", "Privacy Report", "JSON dan PDF"])
    with tabs[0]:
        if original_pages:
            st.caption("Satu slider sticky mengontrol semua halaman. Geser ke kanan untuk membuka layer dokumen asli.")
            before_after_document_slider(original_pages, result["redacted_pages"], key=f"{key_prefix}_document")
        else:
            st.info("Halaman asli untuk slider tidak tersedia pada hasil scan ini.")
    with tabs[1]:
        for index, page in enumerate(result["redacted_pages"], start=1):
            st.image(page, caption=f"Halaman {index} yang sudah disensor")
    with tabs[2]:
        st.json(profile)
    with tabs[3]:
        st.json(report)
    with tabs[4]:
        st.download_button("Unduh redacted PDF", data=Path(result["redacted_pdf"]).read_bytes(), file_name=f"{key_prefix}_redacted_document.pdf", mime="application/pdf", key=f"{key_prefix}_pdf")
        for name in ["detection_result.json", "ocr_result.json", "sanitized_candidate_profile.json", "privacy_risk_report.json"]:
            path = output_dir / name
            st.download_button(f"Unduh {name}", data=path.read_bytes(), file_name=f"{key_prefix}_{name}", mime="application/json", key=f"{key_prefix}_{name}")
        st.download_button("Unduh semua output", data=artifact_zip(output_dir), file_name=f"{key_prefix}_privacy_shield_output.zip", mime="application/zip", key=f"{key_prefix}_zip")


def show_comparison(results: dict[str, tuple[dict, Path]], title: str = "Perbandingan Backend", key_scope: str = "comparison", original_pages: list[Path] | None = None) -> None:
    st.subheader(title)
    rows = []
    for backend, (result, output_dir) in results.items():
        report = result["report"]
        visual_count = sum(
            1
            for page in result["detections"]["pages"]
            for detection in page["detections"]
            if detection["source"] in {"visual", "opencv_face_fallback"}
        )
        yolo_visual_count = sum(
            1
            for page in result["detections"]["pages"]
            for detection in page["detections"]
            if detection["source"] == "visual"
        )
        fallback_count = sum(
            1
            for page in result["detections"]["pages"]
            for detection in page["detections"]
            if detection["source"] == "opencv_face_fallback"
        )
        ocr_count = sum(
            1
            for page in result["detections"]["pages"]
            for detection in page["detections"]
            if detection["source"] == "ocr_regex"
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
            "yolo_visual": yolo_visual_count,
            "face_fallback": fallback_count,
            "ocr_regex": ocr_count,
            "face_photo": face_count,
            "risk_level": report["risk_level"],
            "processing_s": round(report["processing_time_ms"] / 1000, 2),
            "output": str(output_dir),
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    tabs = st.tabs([backend.upper() for backend in results])
    for tab, (backend, (result, output_dir)) in zip(tabs, results.items()):
        with tab:
            show_result(result, output_dir, f"{key_scope}_{backend}", original_pages)


def show_batch_results(batch: dict) -> None:
    st.success("Redaksi batch selesai. Semua dokumen diproses dengan YOLOv5 dan YOLO26.")
    report = batch["report"]
    scan_dir = batch["scan_dir"]
    st.subheader("Report Evaluasi Sistem")
    backend_rows = []
    for backend, values in report["summary_by_backend"].items():
        backend_rows.append({"backend": backend.upper(), **values})
    st.dataframe(pd.DataFrame(backend_rows), width="stretch", hide_index=True)
    st.download_button(
        "Unduh batch_system_evaluation_report.json",
        data=(scan_dir / "batch_system_evaluation_report.json").read_bytes(),
        file_name="batch_system_evaluation_report.json",
        mime="application/json",
        key=f"{report['scan_id']}_batch_json",
    )
    st.download_button(
        "Unduh batch_system_evaluation_report.csv",
        data=(scan_dir / "batch_system_evaluation_report.csv").read_bytes(),
        file_name="batch_system_evaluation_report.csv",
        mime="text/csv",
        key=f"{report['scan_id']}_batch_csv",
    )
    st.download_button(
        "Unduh seluruh folder scan",
        data=artifact_zip(scan_dir),
        file_name=f"{report['scan_id']}_privacy_shield_batch.zip",
        mime="application/zip",
        key=f"{report['scan_id']}_batch_zip",
    )
    st.caption(f"Log scan tersimpan di `{scan_dir / 'scan.log'}` dan log aplikasi di `{LOGS_ROOT / 'streamlit_scans.log'}`.")
    document_tabs = st.tabs([payload["label"] for payload in batch["documents"].values()])
    for tab, (document_id, payload) in zip(document_tabs, batch["documents"].items()):
        with tab:
            meta = payload["file"]
            st.write(f"File ID: `{meta['file_id']}` | Ekstensi: `{meta['extension']}` | Ukuran: `{meta['size_mb']} MB`")
            show_comparison(payload["results"], title=f"Perbandingan {payload['label']}", key_scope=document_id, original_pages=payload["original_pages"])


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
        st.caption("Email, telepon, alamat, GitHub, dan nomor dokumen ditangani OCR + regex.")

    upload_tab, evaluation_tab, explanation_tab = st.tabs(["Scan Dokumen", "Evaluasi Sistem", "Penjelasan Output"])
    with upload_tab:
        uploaded_files = st.file_uploader("Unggah satu atau lebih PDF, JPG, atau PNG", type=["pdf", "jpg", "jpeg", "png"], accept_multiple_files=True)
        if uploaded_files:
            received = [safe_file_meta(uploaded) for uploaded in uploaded_files]
            st.dataframe(pd.DataFrame(received), width="stretch", hide_index=True)
        if st.button("Jalankan Redaksi", type="primary", disabled=not uploaded_files):
            missing = [backend.upper() for backend, path in weights.items() if path is None or not path.is_file()]
            if missing:
                st.error(f"Weights belum lengkap untuk: {', '.join(missing)}. Selesaikan training kedua model terlebih dahulu.")
            else:
                scan_id = uuid.uuid4().hex
                scan_dir = ARTIFACTS_ROOT / scan_id
                scan_documents: dict[str, dict] = {}
                started = time.perf_counter()
                logger = get_logger()
                scan_log = scan_dir / "scan.log"
                with st.spinner("Memproses batch dokumen dengan YOLOv5 dan YOLO26 secara lokal..."):
                    try:
                        scan_dir.mkdir(parents=True, exist_ok=True)
                        append_scan_log(scan_log, f"INFO scan_started scan_id={scan_id} documents={len(uploaded_files)}")
                        logger.info("scan_started scan_id=%s documents=%s", scan_id, len(uploaded_files))
                        with tempfile.TemporaryDirectory(prefix="privacy_upload_") as temporary:
                            for index, uploaded in enumerate(uploaded_files, start=1):
                                meta = safe_file_meta(uploaded)
                                document_id = f"document_{index:03d}"
                                input_path = Path(temporary) / f"{document_id}{meta['extension']}"
                                input_path.write_bytes(uploaded.getbuffer())
                                original_pages_dir = scan_dir / document_id / "original_pages"
                                original_pages = document_to_images(input_path, original_pages_dir)
                                results: dict[str, tuple[dict, Path]] = {}
                                append_scan_log(scan_log, f"INFO document_started scan_id={scan_id} document_id={document_id} file_id={meta['file_id']} size_mb={meta['size_mb']}")
                                for backend in BACKENDS:
                                    output_dir = scan_dir / document_id / backend
                                    detector = load_detector(backend, str(weights[backend]), yolov5_repo)
                                    result = run_privacy_pipeline(input_path, output_dir, detector, TesseractOCRExtractor(ocr_language))
                                    results[backend] = (result, output_dir)
                                    append_scan_log(scan_log, f"INFO backend_finished scan_id={scan_id} document_id={document_id} backend={backend} detections={result['report']['detection_count']} processing_ms={result['report']['processing_time_ms']}")
                                scan_documents[document_id] = {"label": f"Dokumen {index}", "file": meta, "original_pages": original_pages, "results": results}
                        batch_report = build_batch_report(scan_id, scan_documents, weights, started)
                        save_batch_artifacts(scan_dir, batch_report)
                        append_scan_log(scan_log, f"INFO scan_finished scan_id={scan_id} total_processing_ms={batch_report['total_processing_time_ms']}")
                        logger.info("scan_finished scan_id=%s total_processing_ms=%s", scan_id, batch_report["total_processing_time_ms"])
                        st.session_state["latest_batch"] = {"scan_id": scan_id, "scan_dir": scan_dir, "documents": scan_documents, "report": batch_report}
                    except Exception as exc:
                        logger.exception("scan_failed scan_id=%s", scan_id)
                        st.error(f"Scan tidak dapat dijalankan: {exc}")
        if "latest_batch" in st.session_state:
            show_batch_results(st.session_state["latest_batch"])
    with evaluation_tab:
        show_evaluation()
    with explanation_tab:
        st.subheader("Arti Output")
        st.markdown("- **Redacted PDF dan halaman**: dokumen baru yang area sensitifnya telah disamarkan permanen.\n- **Detection JSON**: kategori, lokasi, sumber deteksi, confidence, dan metode redaksi tanpa isi PII.\n- **OCR JSON**: koordinat dan hash token OCR, dengan text token disamarkan.\n- **Sanitized profile**: hanya informasi relevan seperti skill, pengalaman, pendidikan, dan sertifikasi. Ini satu-satunya payload yang boleh diberikan ke Gemini.\n- **Privacy report**: jumlah deteksi, risk level, durasi, dan status guard payload Gemini.")
        st.subheader("Batasan Evaluasi")
        st.markdown("Metrik leakage, over-redaction, dan akurasi OCR memerlukan ground truth yang telah diaudit. Nilai tersebut tidak boleh diinterpretasikan jika belum ada audit manual.")


if __name__ == "__main__":
    main()
