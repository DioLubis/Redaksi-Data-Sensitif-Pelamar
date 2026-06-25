# API Contract

Base path: `/api`

Format error standar:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "File type is not supported.",
    "details": {
      "allowed_types": ["application/pdf", "image/jpeg", "image/png"]
    }
  }
}
```

## 1. Upload Applicant Document

`POST /api/applicants/:id/documents/upload`

Content-Type: `multipart/form-data`

Request:

```json
{
  "file": "cv.pdf",
  "document_type": "cv"
}
```

Response `201`:

```json
{
  "document_id": "b7b1d3a1-53f2-4c42-bcd5-0af2e8ac1b95",
  "applicant_id": "1679df45-6e3c-4a42-88f1-2c57f9aa31ec",
  "status": "uploaded",
  "file": {
    "original_filename": "cv.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 820000,
    "page_count": 3,
    "sha256_hash": "hash-value"
  }
}
```

Possible errors:

1. `UNSUPPORTED_FILE_TYPE`
2. `FILE_TOO_LARGE`
3. `PAGE_LIMIT_EXCEEDED`
4. `MALFORMED_DOCUMENT`

## 2. Create Privacy Scan

`POST /api/privacy-scans`

Request:

```json
{
  "applicant_document_id": "b7b1d3a1-53f2-4c42-bcd5-0af2e8ac1b95",
  "models": ["yolov5", "yolo26"],
  "redaction_policy": "privacy_first",
  "blind_screening": false
}
```

Response `202`:

```json
{
  "scan_id": "b8b2b963-45fa-41ef-af59-7cf2e0f3117f",
  "status": "queued",
  "models": ["yolov5", "yolo26"],
  "redaction_policy": "privacy_first"
}
```

## 3. Get Privacy Scan Status

`GET /api/privacy-scans/:id`

Response `200`:

```json
{
  "scan_id": "b8b2b963-45fa-41ef-af59-7cf2e0f3117f",
  "status": "completed",
  "progress": 100,
  "summary": {
    "pages_processed": 3,
    "visual_detections": 8,
    "textual_detections": 12,
    "redactions_applied": 20,
    "risk_level": "medium"
  },
  "timestamps": {
    "created_at": "2026-06-26T02:00:00Z",
    "started_at": "2026-06-26T02:00:10Z",
    "finished_at": "2026-06-26T02:01:20Z"
  }
}
```

## 4. Get Privacy Scan Report

`GET /api/privacy-scans/:id/report`

Response `200`:

```json
{
  "scan_id": "b8b2b963-45fa-41ef-af59-7cf2e0f3117f",
  "privacy_risk_report": {
    "risk_level": "medium",
    "detected_categories": ["face_photo", "email", "phone_number", "full_address"],
    "high_risk_items": 2,
    "redaction_coverage": 1.0
  },
  "redaction_report": {
    "total_redactions": 20,
    "by_detector": {
      "yolov5": 5,
      "yolo26": 6,
      "ocr_regex": 9
    },
    "by_class": {
      "face_photo": 1,
      "signature": 1,
      "email": 2,
      "phone_number": 2,
      "full_address": 1
    }
  },
  "model_comparison": {
    "yolov5": {
      "detections": 5,
      "avg_confidence": 0.82,
      "latency_ms": 430
    },
    "yolo26": {
      "detections": 6,
      "avg_confidence": 0.86,
      "latency_ms": 390
    }
  }
}
```

## 5. Safe AI Screening

`POST /api/ai-screening/safe`

Request:

```json
{
  "applicant_id": "1679df45-6e3c-4a42-88f1-2c57f9aa31ec",
  "sanitized_candidate_profile_id": "3a1f7a80-4041-4e08-a2cb-4baea2d78b76",
  "job_id": "8c58afc1-7eab-42f9-910c-77e9c506a3dd"
}
```

Response `200`:

```json
{
  "ai_screening_request_id": "8572c3dc-6c6c-4b07-8717-d95ff14ce797",
  "status": "completed",
  "result": {
    "score": 84,
    "matched_skills": ["React", "PostgreSQL", "REST API"],
    "missing_skills": ["Docker"],
    "experience_relevance": "high",
    "summary": "Candidate has relevant frontend and backend experience.",
    "suggested_questions": [
      "Explain your experience building REST APIs.",
      "Describe a project using React."
    ]
  },
  "privacy_status": {
    "raw_document_sent_to_gemini": false,
    "sanitized_profile_only": true,
    "final_pii_guard_passed": true
  }
}
```

## 6. Get Sanitized Profile

`GET /api/applicants/:id/sanitized-profile`

Response `200`:

```json
{
  "applicant_id": "1679df45-6e3c-4a42-88f1-2c57f9aa31ec",
  "sanitized_candidate_profile_id": "3a1f7a80-4041-4e08-a2cb-4baea2d78b76",
  "profile": {
    "skills": ["React", "Go", "PostgreSQL"],
    "education": [
      {
        "degree": "Bachelor",
        "field": "Computer Science"
      }
    ],
    "experiences": [
      {
        "role": "Frontend Developer",
        "duration": "1 year",
        "description": "Built dashboard and recruitment features."
      }
    ],
    "certifications": [],
    "projects": []
  },
  "removed_fields": ["email", "phone_number", "full_address", "face_photo"],
  "risk_level": "medium"
}
```

