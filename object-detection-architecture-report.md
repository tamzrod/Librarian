# Object Detection Plugin Architecture Report

**Date**: 2026-07-05  
**Operation**: Object Detection Plugin Discovery  
**Objective**: Determine Object Detection implementation status

---

## Executive Summary

**Status**: **Partially Implemented** (Database Foundation + Code, Not Registered)

Object Detection is NOT visible in Settings because the plugin discovery mechanism (`_discover_installed_plugins()`) does not recognize it as installed, even though all components exist.

---

## Component Analysis

### 1. Database Support ✅ COMPLETE

| Component | Status | Details |
|-----------|--------|---------|
| Migration 012 | ✅ Applied | `012_object_detection.sql` |
| Table `object_detections` | ✅ Created | Stores detections with FK to `documents` |
| Indexes | ✅ Created | 7 indexes for efficient querying |
| Job Type | ✅ Defined | `JobType.OBJECT_DETECTION = 'object_detection'` |

### 2. Plugin Registration ⚠️ INCOMPLETE

| Component | Status | Details |
|-----------|--------|---------|
| PLUGIN_DEFINITIONS | ✅ Present | Defined in `plugin_registry.py` lines 73-82 |
| plugins.yaml config | ✅ Present | `object_detection: {enabled: true}` |
| `_discover_installed_plugins()` | ❌ MISSING | Does NOT recognize `object_detection` as installed |

**Root Cause**: The `_discover_installed_plugins()` function only recognizes handlers that are registered in the `registered_job_types` set:

```python
registered_job_types = {
    'extract_photo_metadata',  # ✅ photo_metadata_extractor.py
    'generate_thumbnail',       # ✅ thumbnail_generator.py
    # ❌ object_detection NOT listed
}
```

### 3. Worker Implementation ✅ COMPLETE

| Component | Status | Details |
|-----------|--------|---------|
| `object_detection_extractor.py` | ✅ Exists | Full `ObjectDetectionExtractor` class |
| Handler Registration | ✅ Present | `worker.py` lines 331, 343 |
| YOLOv8n Integration | ✅ Implemented | CPU capable, GPU accelerated |
| Base Class | ✅ Extends | `BaseWorker` |

**Handler Registration** (`workers/worker.py`):
```python
from .object_detection_extractor import ObjectDetectionExtractor
...
worker.register_handler('object_detection', ObjectDetectionExtractor(backend).process)
```

### 4. UI Support ✅ COMPLETE

| Component | Status | Details |
|-----------|--------|---------|
| Settings Route | ✅ Implemented | `GET /api/v1/settings/plugins` |
| Plugin Model | ✅ Complete | Includes identity fields |
| Object Detection Search | ✅ Implemented | `GET /explorer/objects` endpoint |

---

## Why Object Detection Is Hidden

The plugin is NOT visible because:

1. **Plugin Registry Filters by Installation**: `get_installed_plugins()` only returns plugins in `INSTALLED_PLUGINS`

2. **Discovery Doesn't Include Object Detection**:
   ```python
   registered_job_types = {
       'extract_photo_metadata',  # recognized
       'generate_thumbnail',       # recognized
       # object_detection NOT recognized
   }
   ```

3. **Configuration Alone Is Not Sufficient**: Even though `plugins.yaml` has `object_detection: {enabled: true}`, the registry ignores it because discovery doesn't mark it as installed.

---

## What Would Make Object Detection Visible

To make Object Detection appear in Settings, the `_discover_installed_plugins()` function needs to recognize it. This requires adding the handler to the `registered_job_types` set.

**Current**:
```python
registered_job_types = {
    'extract_photo_metadata',
    'generate_thumbnail',
}
```

**Needed**:
```python
registered_job_types = {
    'extract_photo_metadata',
    'generate_thumbnail',
    'object_detection',  # Add this
}
```

---

## Architectural Layers Summary

```
┌─────────────────────────────────────────────────────────────┐
│                      SETTINGS UI                            │
│              (GET /api/v1/settings/plugins)                │
└──────────────────────────┬──────────────────────────────────┘
                           │ filters by INSTALLED_PLUGINS
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    PluginRegistry                           │
│              get_installed_plugins()                        │
│              ↓                                              │
│        INSTALLED_PLUGINS (from _discover_installed_plugins)│
└──────────────────────────┬──────────────────────────────────┘
                           │ reads configuration
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                 plugins.yaml                                │
│    object_detection: {enabled: true}  ← exists but ignored│
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Handler Registration (workers/worker.py)       │
│         worker.register_handler('object_detection', ...)     │
└──────────────────────────┬──────────────────────────────────┘
                           │ registers
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         object_detection_extractor.py                       │
│              ObjectDetectionExtractor                       │
└──────────────────────────┬──────────────────────────────────┘
                           │ writes to
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Migration 012: object_detections table        │
└─────────────────────────────────────────────────────────────┘
```

---

## Recommendations

### Option 1: Enable in Discovery (Minimal Change)
Add `'object_detection'` to the `registered_job_types` set in `_discover_installed_plugins()`.

### Option 2: Leave as-is (Current State)
Object Detection works but is hidden from Settings UI. Jobs are still created and processed for images.

### Option 3: Implement as Optional Feature
Document that Object Detection requires additional setup (YOLOv8 model) and add conditional registration.

---

## Conclusion

| Aspect | Status |
|--------|--------|
| Database Schema | ✅ Complete |
| Worker Implementation | ✅ Complete |
| Job Scheduling | ✅ Complete |
| Plugin Configuration | ✅ Complete |
| UI Visibility | ❌ Hidden (discovery gap) |
| End-to-End Pipeline | ✅ Functional |

**Object Detection is a fully functional but hidden feature.** The database, worker, and job scheduling all work correctly. The only issue is that Settings UI doesn't show it because the plugin discovery mechanism doesn't recognize it as "installed."

---

*Report generated: 2026-07-05*
