# Object Detection Existence Check Report

**Date**: 2026-07-05  
**Operation**: Object Detection Existence Check  
**Objective**: Determine if Object Detection is a functional plugin

---

## Final Classification: **B - Implemented but dependency missing**

Object Detection is **fully implemented** at the code level, but **cannot run** because required dependencies are not installed.

---

## Component Inventory

### 1. Worker Implementation ✅ EXISTS

| File | Status | Lines |
|------|--------|-------|
| `workers/object_detection_extractor.py` | ✅ Complete | 296 |
| `workers/base.py` | ✅ Used | - |

**Class**: `ObjectDetectionExtractor(BaseWorker)`
- Full YOLOv8n integration
- Lazy model loading
- Confidence filtering
- Bounding box extraction
- Normalized coordinates
- Graceful error handling

### 2. Job Handler Registration ✅ EXISTS

**Location**: `workers/worker.py:343`
```python
worker.register_handler('object_detection', ObjectDetectionExtractor(backend).process)
```

### 3. Plugin Definition ✅ EXISTS

**Location**: `registry/plugin_registry.py:73-82`
```python
'object_detection': {
    'job_type': 'object_detection',
    'description': 'Detect objects in images',
    'category': 'vision',
    'namespace': 'vision.object-detection.yolo',
    'type': 'object-detection',
    'engine': 'yolo',
    'version': '1.0.0',
}
```

### 4. Plugin Configuration ✅ EXISTS

**Location**: `config/plugins.yaml:9-12`
```yaml
object_detection:
  enabled: true
  category: vision
  description: Detect objects in images using YOLOv8n
```

### 5. Database Schema ✅ EXISTS

| Component | Status |
|-----------|--------|
| Migration 012 | ✅ Applied |
| `object_detections` table | ✅ Created |
| Indexes (7) | ✅ Created |
| Backend methods | ✅ Implemented |

**Backend Methods** (`storage/postgres_backend.py`):
- `save_detections()` - Lines 3904-3991
- `get_detections()` - Lines 3998-4019
- `get_objects_by_label()` - Lines 4063-4084
- `delete_detections()` - Lines 4127-4165

### 6. API Endpoints ✅ EXISTS

**Location**: `api/routes/explorer.py`
- `GET /explorer/objects` - Line 955 (Object Detection Search)
- `GET /explorer/objects/search` - Line 1003

### 7. Job Scheduling ✅ EXISTS

**Location**: `storage/postgres_backend.py`
- `OBJECT_DETECTION = 'object_detection'` - Line 29
- Job type included in image artifact scheduling - Lines 62, 118

---

## Missing Components

### 1. Dependencies ❌ MISSING

| Package | Status | Required For |
|---------|--------|--------------|
| `ultralytics` | ❌ Not in requirements.txt | YOLOv8n model loading |
| `torch` | ❌ Not in requirements.txt | Deep learning backend |
| `torchvision` | ❌ Not in requirements.txt | Image preprocessing |
| `opencv-python` | ❌ Not in requirements.txt | Image handling |

**Current dependencies** (`requirements.txt`):
```
Pillow>=10.0.0
```
No ML/AI dependencies present.

### 2. Plugin Discovery ❌ INCOMPLETE

**Location**: `registry/plugin_registry.py:152-162`

The `_discover_installed_plugins()` function only recognizes:
```python
registered_job_types = {
    'extract_photo_metadata',  # ✅ recognized
    'generate_thumbnail',       # ✅ recognized
    # object_detection NOT recognized
}
```

This causes the Settings UI to hide the plugin.

---

## Can Object Detection Run?

### Current State: **NO**

**Reason**: `ultralytics` package is not installed.

**If attempted**:
1. Job would be scheduled (backend creates `object_detection` jobs)
2. Worker would pick up job
3. Worker calls `ObjectDetectionExtractor.process()`
4. Process calls `_load_model()` → Line 77: `from ultralytics import YOLO`
5. **ImportError: No module named 'ultralytics'**

### What Would Be Needed to Run:

```bash
pip install ultralytics
# Downloads ~6MB yolov8n.pt model on first run
```

Or add to `requirements.txt`:
```
ultralytics>=8.0.0
```

---

## Why Settings Hides It

The Settings page calls `registry.get_installed_plugins()` which filters by `INSTALLED_PLUGINS`.

`INSTALLED_PLUGINS` is populated by `_discover_installed_plugins()` which checks `registered_job_types`.

Since `object_detection` is not in `registered_job_types`, it's not in `INSTALLED_PLUGINS`.

**Result**: Object Detection is:
- ✅ Configured
- ✅ Defined
- ✅ Scheduled to run
- ✅ Has a worker
- ❌ Not shown in Settings (discovery gap)

---

## Verification Checklist

| Check | Result |
|-------|--------|
| `workers/object_detection_extractor.py` exists | ✅ |
| `ObjectDetectionExtractor` class exists | ✅ |
| Handler registered in `worker.py` | ✅ |
| `object_detection` job_type defined | ✅ |
| Database table exists | ✅ |
| Backend save/get methods exist | ✅ |
| API endpoints exist | ✅ |
| Config in plugins.yaml | ✅ |
| Definition in PLUGIN_DEFINITIONS | ✅ |
| Dependency in requirements.txt | ❌ |
| Discovery includes object_detection | ❌ |
| Shown in Settings UI | ❌ |

---

## Recommendations

### To Enable Fully:

1. **Add dependency** to `requirements.txt`:
   ```
   ultralytics>=8.0.0
   ```

2. **Update discovery** in `registry/plugin_registry.py`:
   ```python
   registered_job_types = {
       'extract_photo_metadata',
       'generate_thumbnail',
       'object_detection',  # Add this
   }
   ```

3. **Install package**:
   ```bash
   pip install ultralytics
   ```

### To Keep Hidden (Current State):

- Object Detection still works for jobs already scheduled
- Backend and worker are ready
- Only UI visibility is affected
- First job would fail with ImportError if scheduled

---

## Conclusion

| Classification | B |
|----------------|---|
| **Description** | Implemented but dependency missing |
| **Code Complete** | ✅ Yes |
| **Runnable** | ❌ No (missing ultralytics) |
| **UI Visible** | ❌ No (discovery gap) |
| **Database Ready** | ✅ Yes |
| **Scheduling Ready** | ✅ Yes |

**Object Detection is production-ready code awaiting dependency installation.**

---

*Report generated: 2026-07-05*
