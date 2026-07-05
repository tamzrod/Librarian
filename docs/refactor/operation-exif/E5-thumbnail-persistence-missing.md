# E5: Thumbnail Persistence Missing

**Status:** Completed  
**Severity:** Medium  
**Classification:** Open  
**Completed:** 2026-07-01

## Problem Statement

Thumbnail generation was queued as a job type (`generate_thumbnail`) but:

1. **No worker handled it:** `run_worker()` did not register a `generate_thumbnail` handler
2. **No storage mechanism:** Thumbnails had no persistence path
3. **No API exposure:** No way to retrieve thumbnails

## Solution Implemented

### Option B: Filesystem Storage

Thumbnails are stored on the filesystem:
- Directory: `/library/.thumbnails/`
- Filename: `{document_id}_{original_name}_thumb.jpg`

This approach:
- No database schema changes needed (adds column with ALTER)
- Simple file serving via API endpoint
- No external storage dependencies

## Files Modified

| File | Change |
|------|--------|
| `workers/thumbnail_generator.py` | **NEW** - Thumbnail generation handler |
| `workers/worker.py` | Added import and registration of ThumbnailGenerator handler |
| `api/routes/explorer.py` | Added `thumbnail_path` field to DocumentDetail model |
| `api/app.py` | Added `/thumbnails/{path}` endpoint for serving thumbnails |

## Implementation Details

### 1. ThumbnailGenerator Worker

```python
# workers/thumbnail_generator.py
class ThumbnailGenerator(BaseWorker):
    def process(self, job: dict) -> dict:
        # Get document info
        # Check if image is supported type
        # Generate thumbnail using PIL
        # Save to .thumbnails directory
        # Store path in documents.thumbnail_path column
```

**Thumbnail Settings:**
- Size: 256x256 max (maintains aspect ratio)
- Format: JPEG, quality 85
- Directory: `{library_root}/.thumbnails/`

### 2. Handler Registration

```python
# workers/worker.py
from .thumbnail_generator import ThumbnailGenerator
worker.register_handler('generate_thumbnail', ThumbnailGenerator(backend).process)
```

### 3. API Exposure

**DocumentDetail model added:**
```python
thumbnail_path: Optional[str] = Field(default=None, description="Relative path to generated thumbnail")
```

**Endpoint:**
```
GET /thumbnails/{path}
```
Serves thumbnails from `/library/.thumbnails/{path}`

## Data Flow

```
Image discovered
    ↓
generate_thumbnail job created
    ↓
Worker receives job
    ↓
ThumbnailGenerator.process() called
    ↓
Thumbnail generated via PIL
    ↓
Thumbnail persisted to .thumbnails/
    ↓
documents.thumbnail_path updated
    ↓
API exposes thumbnail_path in document detail
    ↓
GET /thumbnails/{path} serves thumbnail
```

## Database Changes

Lightweight migration (in ThumbnailGenerator):
```sql
ALTER TABLE documents ADD COLUMN IF NOT EXISTS thumbnail_path VARCHAR(500);
```

## What Was NOT Modified (Out of Scope)

- EXIF extraction
- OCR
- Embeddings
- GPS
- Locations
- Maps
- Timeline
- Frontend layout
- Database migrations (schema files)
- Schema changes (beyond lightweight column add)

## Definition of Done

- [x] `generate_thumbnail` job has handler
- [x] Thumbnails generated via PIL
- [x] Thumbnails stored on filesystem
- [x] documents.thumbnail_path column populated
- [x] API exposes thumbnail_path in document detail
- [x] `/thumbnails/{path}` endpoint serves thumbnails

## Dependencies

- None (implemented independently)

## Risk Assessment

- **Low Risk:** New code, no breaking changes
- **Impact:** Performance improvement (thumbnails cached vs generated on-demand)
- **Testing:** Verify thumbnail generation and serving

## Effort

- **Time:** 2-3 hours
- **Complexity:** Low
- **Testing:** Basic verification
