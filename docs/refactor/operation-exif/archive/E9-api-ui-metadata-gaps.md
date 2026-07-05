# E9: API/UI Metadata Gaps

**Status:** Partial  
**Severity:** Medium  
**Classification:** Partial Implementation
**Last Updated:** 2026-07-02 (Post-Implementation Audit)

## Implementation Status

### What Was Done

1. ✅ `mime_type` is now populated for new documents (E1 partial)
2. ✅ DocumentDetail model includes `thumbnail_path` (E5)
3. ✅ Timeline API exposes photo metadata (existing)
4. ⚠️ Explorer API includes `mime_type` field in DocumentDetail

### What Remains

1. ❌ **No mime_type filter in Explorer API** - Can't filter by media type
2. ❌ **No camera/make filter** - Not exposed as query parameters
3. ❌ **No GPS location name** - No reverse geocoding
4. ❌ **Dashboard filters incomplete** - Frontend not updated
5. ❌ **No metadata counts API** - Operations API missing stats

### API Gap Analysis

| Metadata | Explorer API | Timeline API | Status |
|----------|-------------|-------------|--------|
| mime_type | ✅ Partial | - | Need filter params |
| Dimensions | ✅ Via photo_metadata | - | Need better exposure |
| Camera make/model | ✅ Via photo_metadata | ✅ | Need filter params |
| GPS coordinates | ✅ Via photo_metadata | ✅ | Need aggregation |
| File size | ✅ | - | Working |
| Timestamps | ✅ | ✅ | Working |

## Problem Statement

The API and UI have metadata that is partially exposed or not exposed at all:

### API Gaps

| Metadata | Explorer API | Timeline API | Status |
|----------|-------------|-------------|--------|
| mime_type | ✓ | - | Partial (E1) |
| Dimensions | - | ✓ (via photo_metadata) | Partial |
| Camera make/model | - | ✓ | Working |
| GPS coordinates | - | ✓ | Partial (E3) |
| File size | ✓ | - | Working |
| Timestamps | ✓ | ✓ | Working |

### UI Gaps

| Feature | Current | Needed |
|---------|---------|--------|
| MIME type filter | ✗ | ✓ |
| Photo dimensions | ✗ | ✓ |
| Camera filter | ✗ | ✓ |
| GPS location name | ✗ | ✓ |

## Impact

- **User Impact:** Cannot filter by common metadata
- **Developer Impact:** Inconsistent API exposure
- **Data Impact:** Available data not surfaced

## Affected Files

| File | Issue |
|------|-------|
| `api/routes/explorer.py` | Missing metadata filters |
| `api/routes/timeline.py` | Partial exposure |
| `api/routes/operations.py` | Missing metadata counts |
| `dashboard/src/` | Missing filters/display |

## Required Changes

### 1. Explorer API Enhancement

```python
# api/routes/explorer.py
class DocumentResponse(BaseModel):
    # Existing fields...
    mime_type: Optional[str]
    dimensions: Optional[Dimensions]  # Add
    camera: Optional[Camera]  # Add (from photo_metadata join)
    gps_location: Optional[GPSLocation]  # Add
```

### 2. Metadata Counts API

```python
# api/routes/operations.py
class MetadataStats(BaseModel):
    mime_types: dict  # Count by mime_type
    cameras: dict  # Count by camera
    dimensions: dict  # Distribution of dimensions
```

### 3. Filter Enhancements

```python
# GET /api/explorer/documents
filters = {
    'mime_type': 'image/jpeg',
    'camera_make': 'Canon',
    'has_gps': True,
    'min_width': 1920,
    'min_height': 1080
}
```

## Definition of Done

- [ ] Explorer API exposes all document metadata
- [ ] Timeline API exposes location names
- [ ] Operations API provides metadata counts
- [ ] Dashboard filters work

## Dependencies

- E1 (mime_type)
- E3 (GPS to locations)
- E7 (embeddings)

## Risk Assessment

- **Low Risk:** API additions only
- **Impact:** Better UX
- **Testing:** Test API responses

## Effort Estimate

- **Time:** 4-6 hours
- **Complexity:** Low
- **Testing:** Test API and dashboard
