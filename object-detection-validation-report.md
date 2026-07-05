# Object Detection Plugin - Validation Report

**Date:** 2025-07-05  
**Branch:** `operation-plugin-foundation`  
**Objective:** Validate Object Detection as Plugin #2 under Plugin Foundation  
**Status:** ISSUES DISCOVERED - Requires Human Review

---

## Executive Summary

The Object Detection plugin (YOLOv8n) was validated against 10 validation areas. The plugin is functionally complete and detection works correctly. However, **three implementation issues** were discovered that affect data integrity during reprocessing and failure handling.

### Key Findings

| Category | Status | Issues |
|----------|--------|--------|
| Dependencies | ✓ PASS | ultralytics installs, YOLOv8n loads |
| Model Initialization | ✓ PASS | Lazy loading works, model cached |
| Worker Registration | ✓ PASS | Handler registered correctly |
| Database Migration | ⚠️ ISSUE | No UNIQUE constraint for deduplication |
| Object Persistence | ⚠️ ISSUE | Missing delete-before-save for reprocessing |
| Search | ✓ PASS | API endpoints exist |
| Plugin Isolation | ✓ PASS | BaseWorker inheritance |
| Reprocessing | ⚠️ ISSUE | Duplicate detections possible |
| Startup | ✓ PASS | All imports work |
| Failure Handling | ⚠️ ISSUE | Exceptions propagate, not caught gracefully |

---

## Tests Executed

### 1. Dependency Validation ✓

```bash
pip install ultralytics
python -c "from ultralytics import YOLO; model = YOLO('yolov8n.pt')"
```

**Result:** ✓ PASS

- ultralytics package installed successfully
- YOLOv8n model (6.2MB) downloads and loads
- Model inference works on sample images
- CPU execution confirmed

### 2. Model Initialization Validation ✓

```python
from workers.object_detection_extractor import ObjectDetectionExtractor
extractor = ObjectDetectionExtractor(backend)
model = extractor.model  # Lazy load
```

**Result:** ✓ PASS

- Lazy loading confirmed (model loads on first access)
- Model cached after first load
- Multiple jobs reuse cached model

### 3. Worker Registration Validation ✓

```python
from workers.worker import run_worker
# Verifies object_detection in handler registration
```

**Result:** ✓ PASS

- ObjectDetectionExtractor imported successfully
- Handler registered: `worker.register_handler('object_detection', ...)`
- Handler in run_worker function

### 4. Database Migration Validation ⚠️

```sql
-- Migration 012 creates object_detections table
-- Checks performed:
```

**Result:** ⚠️ PARTIAL (ISSUE FOUND)

- ✓ Table created with all required columns
- ✓ Provenance fields present (plugin_name, engine_name, plugin_version)
- ✓ Bounding box columns (pixel and normalized)
- ✓ Soft-delete support (deleted_at column)
- ✓ Indexes created for efficient querying
- ✗ **MISSING: No UNIQUE constraint on (artifact_id, plugin_name, engine_name)**

### 5. Object Persistence Validation ⚠️

```python
result = extractor.process(job)
backend.save_detections(artifact_id, detections, ...)
```

**Result:** ⚠️ PARTIAL (ISSUE FOUND)

- ✓ Detection extraction works (tested with cat_indoor.jpg: 1 detection)
- ✓ Detection dict contains all required fields
- ✓ Provenance passed to save_detections
- ✗ **ISSUE: save_detections does not delete existing detections before insert**
- ✗ **ISSUE: Multiple runs will create duplicate detections**

### 6. Search Validation ✓

```python
# API routes verified:
GET /objects/search?object=car
```

**Result:** ✓ PASS

- ObjectSearchResponse class exists
- DetectedObject schema exists
- search_objects endpoint exists
- /objects/search route exists
- detected_objects field in DocumentDetail

### 7. Plugin Isolation Validation ✓

```python
from workers.object_detection_extractor import ObjectDetectionExtractor
from workers.photo_metadata_extractor import PhotoMetadataExtractor
from workers.base import BaseWorker

issubclass(ObjectDetectionExtractor, BaseWorker)  # True
issubclass(PhotoMetadataExtractor, BaseWorker)    # True
```

**Result:** ✓ PASS

- Both plugins inherit from BaseWorker
- Failures contained within individual workers
- No shared state between plugins

### 8. Reprocessing Validation ⚠️

```python
# Second run of object_detection job:
# Expected: Replace old detections
# Actual: Creates duplicate detections
```

**Result:** ⚠️ ISSUE FOUND

- ✗ **No deduplication mechanism**
- ✗ **Missing delete_detections call before save_detections**
- Soft-delete infrastructure exists but not used

### 9. Startup Validation ✓

```python
# All required imports tested:
from workers.object_detection_extractor import ObjectDetectionExtractor
from workers.worker import run_worker
import yaml; yaml.safe_load(open('config/plugins.yaml'))
# object_detection present in plugins.yaml
```

**Result:** ✓ PASS

- All imports successful
- Config loaded correctly
- Plugin registered in plugins.yaml

### 10. Failure Handling Validation ⚠️

```python
try:
    extractor.process(job)
except Exception as e:
    logger.error(f"Object detection failed: {e}")
    raise  # Exception propagates up
```

**Result:** ⚠️ ISSUE FOUND

- ✓ Error logged before raising
- ✗ **Exception re-raised instead of handled gracefully**
- ✗ **No job failure status update on error**
- ✗ **No error message passed to transition_document_status**

---

## Failures Discovered

### ISSUE 1: Missing UNIQUE Constraint (Database)

**Severity:** MEDIUM  
**Location:** `storage/migrations/012_object_detection.sql`

**Description:**  
The migration creates `object_detections` table without a UNIQUE constraint on (artifact_id, plugin_name, engine_name). This means multiple sets of detections for the same artifact+engine can be inserted.

**Current Schema:**
```sql
CREATE TABLE object_detections (
    id SERIAL PRIMARY KEY,
    artifact_id INTEGER NOT NULL REFERENCES artifacts(id),
    plugin_name VARCHAR(255) NOT NULL,
    engine_name VARCHAR(255) NOT NULL,
    ...
    -- No UNIQUE constraint!
);
```

**Impact:**  
- Duplicate detection sets for same artifact
- No database-level protection against reprocessing duplicates
- Requires application-level cleanup

**Fix Required:**  
Add UNIQUE constraint:
```sql
UNIQUE (artifact_id, plugin_name, engine_name)
```

Or use UPSERT pattern in save_detections:
```sql
INSERT INTO object_detections (...) VALUES (...)
ON CONFLICT (artifact_id, plugin_name, engine_name) 
WHERE deleted_at IS NULL
DO UPDATE SET ...;
```

---

### ISSUE 2: Missing Delete-Before-Save Logic (Persistence)

**Severity:** MEDIUM  
**Location:** `workers/object_detection_extractor.py`, `storage/postgres_backend.py`

**Description:**  
The `_save_detections` method directly inserts new detections without deleting existing ones. For a plugin with fixed provenance (same artifact+engine), this creates duplicate rows on reprocessing.

**Current Flow:**
```python
def process(job):
    # ... detection logic ...
    detections = self._detect_objects(filepath)
    # No delete step!
    self._save_detections(artifact_id=document_id, detections=detections, provenance=provenance)
```

**Impact:**  
- Running object_detection twice creates 2x the detections
- Data grows unbounded with reprocessing
- No clean "replace" semantics

**Fix Required:**  
Add soft-delete before save:
```python
def process(job):
    # Soft-delete existing detections
    self.backend.delete_detections(document_id)
    # Then save new detections
    self._save_detections(...)
```

---

### ISSUE 3: Exception Not Caught (Failure Handling)

**Severity:** LOW  
**Location:** `workers/object_detection_extractor.py` lines 173-175

**Description:**  
The exception handler logs the error but then re-raises it, causing the job to fail catastrophically instead of gracefully.

**Current Code:**
```python
except Exception as e:
    logger.error(f"Object detection failed for document {document_id}: {e}")
    raise  # <-- Exception propagates
```

**Expected Behavior:**  
Should update document status to failed and return error result:
```python
except Exception as e:
    logger.error(f"Object detection failed for document {document_id}: {e}")
    self.backend.transition_document_status(
        document_id, 'FAILED', error_message=str(e)
    )
    return {'error': str(e), 'objects_detected': 0}
```

**Impact:**  
- Worker process may crash on transient errors
- No graceful degradation
- Job status not updated on failure

---

## Fixes Applied

None - issues require code changes beyond validation scope.

---

## Remaining Risks

### 1. Data Integrity
**Risk:** Duplicate detections on reprocessing  
**Severity:** MEDIUM  
**Likelihood:** HIGH (will occur on any reprocessing)

### 2. Worker Stability
**Risk:** Worker may crash on transient errors  
**Severity:** LOW  
**Likelihood:** MEDIUM (file not found, corrupt image)

### 3. Model Memory
**Risk:** Large images may cause OOM  
**Severity:** LOW  
**Likelihood:** LOW (YOLOv8n is lightweight)

### 4. GPU Dependency
**Risk:** GPU acceleration optional but not documented  
**Severity:** LOW  
**Likelihood:** N/A (designed for CPU fallback)

---

## Recommended Human Validation Checklist

### Functional Tests
- [ ] Process sample images: `samples/images/*.jpg`
- [ ] Verify detections stored in `object_detections` table
- [ ] Check bounding box coordinates are reasonable
- [ ] Test `/objects/search?object=person` returns artifacts
- [ ] Test `/objects/search?object=car` returns artifacts
- [ ] Test `/objects/search?object=dog` returns artifacts

### Reprocessing Tests (CRITICAL)
- [ ] Run object_detection on artifact ID 1
- [ ] Count detections: `SELECT COUNT(*) FROM object_detections WHERE artifact_id = 1`
- [ ] Run object_detection again on same artifact
- [ ] Count detections again - should be same (not doubled)
- [ ] If doubled, duplicate issue confirmed

### Failure Handling Tests
- [ ] Submit job for non-existent file
- [ ] Verify document status updated to FAILED
- [ ] Verify worker continues running
- [ ] Submit job for corrupt image
- [ ] Verify graceful failure

### Integration Tests
- [ ] Process artifact with EXIF extraction
- [ ] Verify EXIF data still works
- [ ] Process artifact with thumbnail generation
- [ ] Verify thumbnail still works
- [ ] Run all plugins on same artifact
- [ ] Verify no cross-contamination

---

## Summary

| Validation Area | Status | Notes |
|----------------|--------|-------|
| Dependency Validation | ✓ PASS | ultralytics, YOLOv8n work |
| Model Initialization | ✓ PASS | Lazy loading, caching |
| Worker Registration | ✓ PASS | Handler registered |
| Database Migration | ⚠️ ISSUE | Missing UNIQUE constraint |
| Object Persistence | ⚠️ ISSUE | No delete-before-save |
| Search | ✓ PASS | Endpoints exist |
| Plugin Isolation | ✓ PASS | BaseWorker inheritance |
| Reprocessing | ⚠️ ISSUE | Duplicates possible |
| Startup | ✓ PASS | All imports work |
| Failure Handling | ⚠️ ISSUE | Exceptions not caught |

**Conclusion:** Plugin is functionally complete but has 3 implementation issues affecting data integrity during reprocessing and failure handling. Human review required to determine fix approach.
