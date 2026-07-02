# E6: OCR Output Not Persisted

**Status:** Open  
**Severity:** Medium  
**Classification:** Not Implemented
**Last Updated:** 2026-07-02 (Post-Implementation Audit)

## Implementation Status

### What Exists

1. ✅ `JobType.RUN_OCR = 'run_ocr'` defined in backend
2. ✅ `run_ocr` job queued for image artifacts (see ARTIFACT_TYPE_JOBS)
3. ❌ **NO handler registered** - Worker does not register a handler for `run_ocr`

### Gap Analysis

The job queue expects `run_ocr` jobs but no worker processes them:
```
Worker handlers registered:
- extract_text ✅
- extract_entities ✅
- extract_events ✅
- extract_locations ✅
- generate_embeddings ✅
- extract_photo_metadata ✅
- generate_thumbnail ✅
- run_ocr ❌ NOT REGISTERED
- object_detection ❌ NOT REGISTERED
```

### What's Needed

1. Create `OcrWorker` class to handle `run_ocr` jobs
2. Register handler: `worker.register_handler('run_ocr', OcrWorker(backend).process)`
3. Implement OCR using pytesseract, easyocr, or rapidocr
4. Store OCR text in `document_content` table
5. Add integration tests

## Problem Statement

OCR processing is queued as a job type (`run_ocr`) but:

1. **No worker handles it:** No OCR worker implemented
2. **No storage:** OCR text not stored anywhere
3. **No integration:** OCR text not added to `document_content`

## Impact

- **User Impact:** Scanned documents/images not searchable
- **Developer Impact:** OCR must be re-run on every query
- **Data Impact:** OCR results lost

## Affected Files

| File | Issue |
|------|-------|
| `workers/` | No OCR worker |
| `storage/postgres_backend.py` | No OCR storage methods |
| `workers/content_extractor.py` | Only handles text files |

## Current Flow

```
Image File (or scanned PDF)
    ↓
Job Queued: run_ocr
    ↓
NO WORKER HANDLES THIS JOB
    ↓
Job sits in QUEUED forever
    ↓
Text extraction fails for images
```

## Required Changes

### 1. OCR Worker

```python
# workers/ocr_worker.py
class OcrWorker:
    def process(self, job):
        doc = backend.get_document(job['document_id'])
        ocr_text = self.extract_text_with_ocr(doc['path'])
        
        # Save OCR text
        backend.save_ocr_content(job['document_id'], ocr_text)
        
        # Update document_content or create new entry
        backend.save_content(job['document_id'], ocr_text, 'ocr')
```

### 2. OCR Library Options

| Library | Pros | Cons |
|---------|------|------|
| pytesseract | Open source, good accuracy | Slow, needs language packs |
| easyocr | GPU support, multiple languages | Heavy dependency |
| rapidocr | Fast, accurate | Newer, less tested |

### 3. Storage Options

**Option A:** Add to `document_content` with `extraction_method = 'ocr'`
**Option B:** Create new `ocr_content` table
**Option C:** Append to existing content

## Definition of Done

- [ ] OCR worker implemented
- [ ] OCR text stored persistently
- [ ] OCR text searchable via document_content
- [ ] OCR processed for images without extractable text

## Dependencies

- None (can be implemented independently)

## Risk Assessment

- **Medium Risk:** New dependency, processing time
- **Impact:** Enables search for scanned documents
- **Testing:** Test OCR accuracy and storage

## Effort Estimate

- **Time:** 8-12 hours
- **Complexity:** High
- **Testing:** Test multiple image types
