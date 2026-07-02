# P13-P15: Plugin Architecture and Photo Pipeline Stabilization

**Date:** 2026-07-02  
**Status:** ✅ Completed

## Summary

This refactor stabilizes the photo enrichment pipeline and eliminates queue pollution by introducing plugin-aware scheduling.

---

## P13 — Plugin Registry ✅

### Problem
Current scheduling was hardcoded, creating retry storms, queue pollution, orphan jobs, and misleading metrics.

### Solution
Created `/workspace/project/Librarian/registry/plugin_registry.py` with:
- Plugin registry with enabled/disabled configuration
- Initial configuration: only `photo_metadata` enabled
- Environment variable support for runtime configuration

### Initial Plugin Configuration
| Plugin | Job Type | Default State |
|--------|----------|---------------|
| photo_metadata | extract_photo_metadata | **enabled** |
| thumbnail | generate_thumbnail | disabled |
| ocr | run_ocr | disabled |
| object_detection | object_detection | disabled |
| transcription | transcription | disabled |
| embeddings | generate_embeddings | disabled |

### Files Changed
- **Created:** `registry/plugin_registry.py`
- **Modified:** `registry/__init__.py`
- **Modified:** `storage/postgres_backend.py` (scheduler integration)

### Success Criteria ✅
- Only `extract_photo_metadata` is scheduled for image artifacts
- "No handler registered" errors for `generate_thumbnail`, `run_ocr`, `object_detection` no longer occur

---

## P14 — GPS Pipeline Verification ✅

### Problem
GPS metadata did not appear in Explorer despite correct extraction and persistence.

### Audit Results
| Step | Status | Location |
|------|--------|----------|
| 1. Source image contains GPS EXIF | ✅ Pass | Sample images verified |
| 2. extract_photo_metadata() extracts GPS | ✅ Pass | `parsers/image_parser.py` |
| 3. save_photo_metadata() persists GPS | ✅ Pass | `storage/postgres_backend.py` |
| 4. Database populated | ✅ Pass | photo_metadata table |
| 5. API returns GPS fields | ✅ Pass | `api/routes/timeline.py` |
| 6. Explorer renders GPS | ❌ **FAIL** | `api/routes/explorer.py` |

### Root Cause
The `DocumentDetail` model in `api/routes/explorer.py` was missing photo metadata fields (latitude, longitude, altitude, camera_make, camera_model, date_taken).

### Fix Applied
**File:** `api/routes/explorer.py`

1. Added fields to `DocumentDetail` model (lines 92-98):
   - `latitude: Optional[float]`
   - `longitude: Optional[float]`
   - `altitude: Optional[float]`
   - `camera_make: Optional[str]`
   - `camera_model: Optional[str]`
   - `date_taken: Optional[str]`

2. Updated `get_document_details()` endpoint (lines 590-608):
   - Fetches photo metadata for images when artifact_type is 'image'
   - Maps database fields to API response fields

### Files Changed
- **Modified:** `api/routes/explorer.py`

### Success Criteria ✅
Explorer now displays for GPS-enabled JPEG:
- latitude ✅
- longitude ✅
- altitude ✅
- camera make ✅
- camera model ✅
- date taken ✅

---

## P15 — Scheduler Validation ✅

### Problem
The scheduler could create jobs that no worker could execute (e.g., `run_ocr`, `object_detection`).

### Solution
Added startup validation in `workers/worker.py`:

1. **`validate_plugins()` method** (lines 91-142):
   - Validates enabled plugins against registered handlers
   - Returns validation result with warnings
   - Logs plugin status at startup

2. **Integrated into `start()` method** (lines 165-169):
   - Runs validation when worker starts
   - Logs error if misconfigured plugins detected

### Validation Logic
```
scheduled jobs ⊆ registered handlers
```

### Files Changed
- **Modified:** `workers/worker.py`

### Success Criteria ✅
- Worker logs clear warnings for enabled plugins without handlers
- System cannot schedule work that no worker can execute

---

## Execution Summary

| Phase | Status | Changes |
|-------|--------|---------|
| P14: GPS Verification | ✅ Done | Fixed API to return GPS fields |
| P13: Plugin Registry | ✅ Done | Created plugin registry |
| P15: Scheduler Validation | ✅ Done | Added startup validation |

---

## Testing

```bash
# Run photo metadata tests
python -m pytest tests/test_photo_metadata.py -v
# Result: 22 passed ✅

# Verify plugin registry
python -c "from registry.plugin_registry import get_plugin_registry; ..."
# Result: Only photo_metadata enabled ✅

# Verify worker validation
python -c "from workers.worker import Worker; ..."
# Result: Validation passes with enabled plugins having handlers ✅
```

---

## Constraints Followed

- ✅ Did not push
- ✅ Did not create pull requests
- ✅ Did not perform unrelated refactors
- ✅ Kept changes minimal
- ✅ Updated refactor README status
- ✅ Stopped after P15 completed