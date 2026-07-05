# EXIF Plugin Architecture

**Plugin:** EXIF Metadata Extraction  
**Status:** ✅ Implemented

---

## Overview

The EXIF plugin follows the standard plugin architecture pattern with these components:
- Worker handler for job execution
- Parser for actual extraction logic
- Database backend for persistence
- API routes for exposure

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Plugin Architecture                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │   Scanner    │───▶│   Worker     │───▶│   Backend    │        │
│  │              │    │   Handler    │    │              │        │
│  └──────────────┘    └──────────────┘    └──────────────┘        │
│         │                  │                   │                 │
│         │                  ▼                   │                 │
│         │           ┌──────────────┐          │                 │
│         │           │    Parser    │          │                 │
│         │           │              │          │                 │
│         │           └──────────────┘          │                 │
│         │                                     │                 │
│         ▼                                     ▼                 │
│  ┌──────────────┐                      ┌──────────────┐        │
│  │  documents   │                      │photo_metadata│        │
│  │    table     │                      │    table     │        │
│  └──────────────┘                      └──────────────┘        │
│                                                   │              │
│                                                   ▼              │
│                                          ┌──────────────┐       │
│                                          │     API      │       │
│                                          │   Routes     │       │
│                                          └──────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Worker Handler

**File:** `workers/photo_metadata_extractor.py`

**Class:** `PhotoMetadataExtractor`

**Responsibilities:**
- Validate image files
- Call parser for extraction
- Persist results to database
- Update document status
- Handle errors gracefully

**Job Type:** `extract_photo_metadata`

```python
class PhotoMetadataExtractor(BaseWorker):
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif'}
    
    def process(self, job: dict) -> dict:
        # Extract and persist EXIF metadata
        ...
```

### 2. Parser

**File:** `parsers/image_parser.py`

**Function:** `extract_photo_metadata(filepath: Path) -> Optional[dict]`

**Responsibilities:**
- Read image file
- Extract EXIF data using PIL/Pillow
- Parse GPS coordinates (DMS to decimal)
- Parse timestamps (EXIF format to ISO 8601)
- Return structured metadata

### 3. Storage Backend

**File:** `storage/postgres_backend.py`

**Methods:**
- `save_photo_metadata(document_id, metadata)` - Persist extracted metadata
- `get_photo_metadata(document_id)` - Retrieve metadata

### 4. API Routes

**Files:** `api/routes/timeline.py`, `api/routes/explorer.py`

**Endpoints:**
- `GET /timeline/photo/{document_id}` - Get photo metadata
- Document details include photo metadata fields

---

## Data Flow

```
1. User uploads/scans images
         ↓
2. Collection watcher detects new files
         ↓
3. Scanner creates document records
         ↓
4. Scheduler queues extract_photo_metadata jobs
         ↓
5. PhotoMetadataExtractor processes job
         ↓
6. Image parser extracts EXIF data
         ↓
7. Metadata saved to photo_metadata table
         ↓
8. API exposes data to clients
```

---

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| Pillow | >= 9.0 | Image processing and EXIF extraction |
| psycopg2 | >= 2.9 | PostgreSQL database connection |
| Python | >= 3.9 | Runtime |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EXIF_PLUGIN_ENABLED` | true | Enable/disable EXIF extraction |

### Plugin Configuration

```yaml
# config/plugins.yaml
plugins:
  photo_metadata:
    enabled: true
    job_type: extract_photo_metadata
```

---

## Error Handling

| Error | Handling |
|-------|----------|
| Unsupported format | Skip job, log warning |
| Corrupt image | Fail job, log error |
| Missing EXIF | Return empty fields |
| Database error | Retry 3x, then fail |
| File not found | Fail job, log error |

---

## Testing

### Unit Tests
- `tests/test_photo_metadata.py` - Core extraction logic
- `tests/test_parsers.py` - Parser validation

### Integration Tests
- `tests/test_pipeline.py` - End-to-end processing
- `tests/test_pipeline_e2e.py` - Full pipeline validation

---

## Performance Considerations

1. **Parallel Processing**: Workers can run in parallel
2. **Batch Support**: Future enhancement for batch processing
3. **Caching**: Raw EXIF can be cached for re-extraction
4. **Lazy Loading**: Only load needed EXIF tags

---

## Security Considerations

1. **No External Network**: EXIF extraction is local-only
2. **No User Input**: Files are scanned, not user-provided
3. **No Code Execution**: Plugin only reads metadata
4. **Audit Logging**: All extractions are logged

---

## Future Enhancements

1. **Streaming Extraction**: Process large files without loading fully
2. **Selective Tags**: Only extract needed EXIF tags
3. **Thumbnail Quality**: Configurable thumbnail size/quality
4. **Batch Processing**: Process multiple files per job