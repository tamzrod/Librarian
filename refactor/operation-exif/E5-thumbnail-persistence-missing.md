# E5: Thumbnail Persistence Missing

**Status:** Open  
**Severity:** Medium  
**Classification:** Open

## Problem Statement

Thumbnail generation is queued as a job type (`generate_thumbnail`) but:

1. **No worker handles it:** `PhotoMetadataExtractor` doesn't generate thumbnails
2. **No storage table:** No `thumbnails` table exists
3. **No API endpoint:** Dashboard must generate thumbnails on-demand or proxy

## Impact

- **User Impact:** Thumbnails must be generated on-demand (slow)
- **Developer Impact:** Can't cache thumbnails
- **Data Impact:** Repeated thumbnail generation

## Affected Files

| File | Issue |
|------|-------|
| `workers/photo_metadata_extractor.py` | Could generate thumbnails |
| `storage/postgres_backend.py` | No thumbnail storage methods |
| `storage/migrations/` | No thumbnails table |
| `api/routes/` | No thumbnail serving endpoint |
| `dashboard/` | Must proxy or generate |

## Current Flow

```
Image File
    ↓
Job Queued: generate_thumbnail
    ↓
NO WORKER HANDLES THIS JOB
    ↓
Job sits in QUEUED forever
    ↓
Dashboard must handle thumbnails differently
```

## Required Changes

### Option A: Add Thumbnails Table

```sql
CREATE TABLE thumbnails (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    width INTEGER,
    height INTEGER,
    format VARCHAR(10),
    data BYTEA,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Option B: Store as Files

Store thumbnails on filesystem:
- `/library/.thumbnails/{doc_id}.jpg`

### Option C: External Storage

Store in object storage (S3, GCS, etc.)

## Thumbnail Generator Implementation

```python
# workers/thumbnail_generator.py
class ThumbnailGenerator:
    def process(self, job):
        doc = backend.get_document(job['document_id'])
        image = Image.open(doc['path'])
        thumbnail = image.thumbnail((200, 200))
        
        # Option A: Store in DB
        backend.save_thumbnail(doc['document_id'], thumbnail)
        
        # Option B: Store on filesystem
        save_thumbnail_to_filesystem(doc['document_id'], thumbnail)
```

## Definition of Done

- [ ] `generate_thumbnail` job has handler
- [ ] Thumbnails stored persistently
- [ ] API can serve thumbnails
- [ ] Dashboard uses stored thumbnails

## Dependencies

- None (can be implemented independently)

## Risk Assessment

- **Low Risk:** New table/file storage
- **Impact:** Performance improvement
- **Testing:** Test thumbnail generation and serving

## Effort Estimate

- **Time:** 4-6 hours
- **Complexity:** Medium
- **Testing:** Test generation and serving
