# Success Criteria

**Purpose:** Define the success criteria for Operation Plugin Foundation

---

## Primary Success Question

At completion, we should be able to answer YES to:

> If tomorrow we add:
> - Object Detection
> - OCR
> - Captioning
> - PDF Extraction
> - Audio Transcription
>
> do we know:
> - where observations belong?
> - how provenance works?
> - how versions work?
> - how reprocessing works?
> - how multiple engines coexist?

---

## Success Criteria

### 1. Plugin Identity ✅

| Criterion | Evidence |
|-----------|----------|
| Every observation has `plugin_name` | Column exists in database |
| Every observation has `engine_name` | Column exists in database |
| Every observation has `plugin_version` | Column exists in database |
| Plugin registry tracks identity | `PLUGIN_DEFINITIONS` updated |
| Workers set identity | `BaseWorker.get_provenance()` implemented |

**Verification:**
```python
# Get observation
obs = backend.get_photo_metadata(document_id)

# Verify identity
assert obs.plugin_name == 'metadata.exif.pillow'
assert obs.engine_name == 'pillow-exif'
assert obs.plugin_version == '1.0.0'
```

---

### 2. Provenance Tracking ✅

| Criterion | Evidence |
|-----------|----------|
| Observations include provenance | `processed_at` timestamp |
| Source artifact tracked | `artifact_hash` stored |
| Workers include provenance | `BaseWorker.get_provenance()` implemented |
| Provenance queryable | Indexes created |

**Verification:**
```python
# Get provenance
prov = backend.get_provenance(document_id, 'photo_metadata')

# Verify provenance
assert prov.processed_at is not None
assert prov.artifact_hash is not None
assert prov.plugin_name is not None
```

---

### 3. Namespacing ✅

| Criterion | Evidence |
|-----------|----------|
| Namespace convention defined | Documented in `namespacing-strategy.md` |
| Examples provided | `metadata.exif.pillow`, `vision.object-detection.yolo` |
| Current plugins mapped | Migration mapping documented |
| Validation logic | `validate_namespace()` implemented |

**Verification:**
```python
# Validate namespace
assert validate_namespace('metadata.exif.pillow')  # Valid
assert validate_namespace('vision.object-detection.yolo')  # Valid
assert not validate_namespace('yolo')  # Invalid
```

---

### 4. Reprocessing Boundaries ✅

| Criterion | Evidence |
|-----------|----------|
| Per-plugin job types | `extract_exif`, `detect_objects` |
| Plugin owns its table | EXIF owns `photo_metadata` |
| Reprocessing isolated | Reprocess EXIF doesn't touch OCR |
| API for reprocessing | `/api/v1/plugins/{name}/reprocess` |

**Verification:**
```python
# Reprocess EXIF only
backend.reprocess_plugin('metadata.exif.pillow')

# Verify only EXIF table affected
exif_affected = backend.get_affected_count('photo_metadata')
ocr_affected = backend.get_affected_count('ocr_text')

assert exif_affected > 0
assert ocr_affected == 0  # OCR not affected
```

---

### 5. Multi-Engine Readiness ✅

| Criterion | Evidence |
|-----------|----------|
| UNIQUE allows multiple engines | `(document_id, plugin_name, engine_name)` |
| Future engines can coexist | Schema ready for YOLO, DINO, OWL-ViT |
| Engine queryable | `WHERE engine_name = 'yolo_v8'` works |
| Engine comparable | Cross-engine queries supported |

**Verification:**
```sql
-- Query multiple engines
SELECT engine_name, objects
FROM object_detections
WHERE document_id = 123;

-- All engines returned
-- yolo_v8: [{...}]
-- grounding_dino: [{...}]
-- owl_vit: [{...}]
```

---

## Test Scenarios

### Scenario 1: Add Object Detection

> Tomorrow, we add Object Detection with YOLO and Grounding DINO.

**Questions to Answer:**

1. **Where do observations belong?**
   - Answer: `object_detections` table with `plugin_name='vision.object-detection.yolo'`

2. **How is provenance tracked?**
   - Answer: `processed_at`, `artifact_hash`, `plugin_version`

3. **How do versions work?**
   - Answer: Each observation tracks `plugin_version`

4. **How is reprocessing isolated?**
   - Answer: Reprocessing Object Detection doesn't touch EXIF, OCR, etc.

5. **Can multiple engines coexist?**
   - Answer: Yes, `(document_id, plugin_name, engine_name)` allows YOLO and DINO

---

### Scenario 2: Add OCR

> Tomorrow, we add OCR with Tesseract.

**Questions to Answer:**

1. **Where do observations belong?**
   - Answer: `ocr_text` table with `plugin_name='vision.ocr.tesseract'`

2. **How is provenance tracked?**
   - Answer: Standard provenance columns

3. **How do versions work?**
   - Answer: `plugin_version` tracked per observation

4. **How is reprocessing isolated?**
   - Answer: Reprocessing OCR only affects `ocr_text`

5. **Can multiple OCR engines coexist?**
   - Answer: Yes, Tesseract and Cloud Vision can both store results

---

## Verification Checklist

### Database

- [ ] All provenance columns added
- [ ] All rows backfilled
- [ ] UNIQUE constraint updated
- [ ] Indexes created
- [ ] Comments added

### Code

- [ ] `PLUGIN_DEFINITIONS` updated
- [ ] `Plugin` class updated
- [ ] `BaseWorker.get_provenance()` implemented
- [ ] `PhotoMetadataExtractor` updated
- [ ] `save_*_with_provenance()` implemented

### Tests

- [ ] Existing tests pass
- [ ] Provenance tests pass
- [ ] Migration tests pass
- [ ] API tests pass

### Documentation

- [ ] `plugin-identity.md` complete
- [ ] `provenance-model.md` complete
- [ ] `namespacing-strategy.md` complete
- [ ] `reprocessing-boundaries.md` complete
- [ ] `multi-engine-readiness.md` complete
- [ ] `migration-plan.md` complete
- [ ] `success-criteria.md` complete

---

## Non-Goals (Not Required for Success)

The following are NOT required for Operation Plugin Foundation success:

- ❌ Object Detection implementation
- ❌ OCR implementation
- ❌ Captioning implementation
- ❌ Plugin marketplace
- ❌ Hot loading
- ❌ Dynamic plugins
- ❌ Remote plugins
- ❌ Plugin RPC
- ❌ Distributed execution
- ❌ Sandboxing

These are future operations.

---

## Success Sign-off

### Developer Sign-off

```
Operation Plugin Foundation

- [ ] Plugin identity implemented
- [ ] Provenance tracking implemented
- [ ] Namespacing defined
- [ ] Reprocessing boundaries established
- [ ] Multi-engine readiness verified
- [ ] All tests pass
- [ ] Documentation complete

Verified by: _________________
Date: _________________
```

### QA Sign-off

```
Operation Plugin Foundation - QA Verification

- [ ] Database migration validated
- [ ] Functional tests pass
- [ ] Regression tests pass
- [ ] API backward compatible
- [ ] Performance acceptable

Verified by: _________________
Date: _________________
```

---

## Summary

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Plugin Identity | ✅ Ready | Columns + registry |
| Provenance | ✅ Ready | Columns + timestamp |
| Namespacing | ✅ Ready | Convention + validation |
| Reprocessing | ✅ Ready | Per-plugin isolation |
| Multi-Engine | ✅ Ready | UNIQUE constraint |

**Overall Status:** Ready for future plugin operations.

---

## Next Operations

With Operation Plugin Foundation complete, the following operations can begin:

1. **Operation Object Detection** - Implement YOLO, Grounding DINO, OWL-ViT
2. **Operation OCR** - Implement Tesseract, Cloud Vision
3. **Operation Captioning** - Implement BLIP, GPT-4V
4. **Operation Transcription** - Implement Whisper

Each new plugin will:
- Use the established identity model
- Include provenance
- Follow namespace conventions
- Maintain reprocessing boundaries
- Support multi-engine coexistence
