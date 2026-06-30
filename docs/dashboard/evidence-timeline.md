# Evidence Timeline

**Status:** Phase 1A Implemented  
**Created:** 2026-06-30  
**Last Updated:** 2026-06-30

This document establishes product direction and tracks implementation phases.

---

## Implementation Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1A | ✅ Complete | Photo metadata extraction from EXIF |
| Phase 1B | ✅ Complete | REST API Exposure |
| Phase 1C | Pending | Timeline visualization UI |
| Phase 2 | Pending | Additional artifact types (PDF, video) |
| Future | Backlog | AI inference, reverse geocoding |

---

## Phase 1B: Completed (REST API Exposure)

**Goal:** Expose photo metadata through versioned REST APIs for dashboard consumption.

### What Was Implemented

1. **API Endpoints**
   - `GET /api/v1/timeline/stats` - Timeline statistics
   - `GET /api/v1/timeline/photos` - List photos with filters
   - `GET /api/v1/timeline/map` - GPS markers for maps
   - `GET /api/v1/timeline/photo/{document_id}` - Full photo metadata

2. **Backend Query Methods**
   - `get_timeline_stats()` - Aggregate statistics
   - `search_photo_metadata()` - Filtered search with pagination
   - `get_photos_with_gps()` - Map marker data
   - `get_photo_metadata()` - Single photo detail

3. **Filtering Support**
   - Camera make/model (partial match)
   - GPS coordinates present
   - Date range (start_date, end_date)
   - Pagination (limit, offset)

### Files Changed

- `api/routes/timeline.py` - New router with 4 endpoints
- `api/app.py` - Registered timeline router
- `storage/postgres_backend.py` - Added query methods
- `docs/api-contract/timeline-v1.md` - API documentation
- `tests/test_timeline_api.py` - 14 tests

### Example API Usage

```javascript
// Get map markers
const { markers } = await fetch('/api/v1/timeline/map');

// Filter by camera
const { data } = await fetch('/api/v1/timeline/photos?camera=iPhone&gps_only=true');

// Get stats
const stats = await fetch('/api/v1/timeline/stats');
```

---

## Phase 1A: Completed

**Goal:** Allow Librarian to extract deterministic metadata from image files and persist it.

### What Was Implemented

1. **Database Schema**
   - `photo_metadata` table stores extracted EXIF data
   - Migration: `storage/migrations/003_photo_metadata.sql`

2. **Metadata Extraction**
   - `extract_photo_metadata()` job type
   - Extracts: timestamp, GPS, camera make/model, lens, dimensions, orientation

3. **Worker Integration**
   - `PhotoMetadataExtractor` class
   - Auto-queues `extract_photo_metadata` job for image files

4. **Supported Fields**

   | Field | Source | Example |
   |-------|--------|---------|
   | timestamp_original | EXIF DateTimeOriginal | 2026-01-01T12:25:10 |
   | gps_latitude | EXIF GPS Latitude | 14.635189 |
   | gps_longitude | EXIF GPS Longitude | 121.092548 |
   | gps_altitude | EXIF GPS Altitude | -57.2 |
   | camera_make | EXIF Make | HONOR |
   | camera_model | EXIF Model | BRP-NX1 |
   | lens_model | EXIF LensModel | (if available) |
   | width | Image dimensions | 3000 |
   | height | Image dimensions | 4000 |
   | orientation | EXIF Orientation | 1 |
   | file_format | PIL format | JPEG |

### Files Changed

- `storage/migrations/003_photo_metadata.sql` - New migration
- `storage/postgres_backend.py` - Added job type, save/get methods
- `parsers/image_parser.py` - Enhanced EXIF extraction
- `workers/photo_metadata_extractor.py` - New worker handler
- `workers/worker.py` - Registered new handler
- `tests/test_photo_metadata.py` - 22 tests

### Design Principles Upheld

- ✅ **Trust metadata before inference** - Only EXIF data used
- ✅ **Deterministic** - Same image = same output
- ✅ **Reproducible** - Raw EXIF stored for audit
- ✅ **No AI** - No OCR, face recognition, object detection

---

## WHAT EVIDENCE TIMELINE IS

Evidence Timeline is a dashboard capability for visualizing artifacts through:

- Time
- Location
- Metadata Tags

The page answers:

- When did this happen?
- Where did this happen?
- What evidence exists for it?
- How did the evidence evolve over time?

The Evidence Timeline is **NOT** a photo application.

Photos are only the first artifact type because they already contain rich metadata.

The long-term goal is artifact agnostic visualization.

---

## CORE MODEL

```
Artifact → Time → Location → Metadata Tags
```

Artifacts participate in the timeline if they provide one or more of these dimensions.

---

## Long-Term Vision

Evidence Timeline eventually becomes a universal temporal and spatial explorer for all evidence artifacts.

```
Photo → Location → Time
PDF → Mentioned Location → Document Date
Email → Sender Location → Sent Timestamp
Sensor Log → Installation Site → Measurement Timestamp
```

The dashboard remains the same. Only the artifact types evolve.

---

## Design Principles

**Trust metadata before inference.**

Phase 1A uses only information already present in the artifact:

- Deterministic behavior
- Reproducible results  
- Explainable outputs
- No hallucinations
- No hidden AI decisions

---

## Excluded Features (Not in Phase 1A)

- Facial recognition / Person identification
- Object / Scene recognition
- OCR
- Identity / Relationship inference
- Semantic tagging / AI generated labels
- Reverse geocoding / Maps visualization

These belong to future phases.

---

## Verification

```bash
# Run tests
python -m pytest tests/test_photo_metadata.py -v

# Test extraction on sample images
python3 -c "
from parsers.image_parser import extract_photo_metadata
metadata = extract_photo_metadata('samples/IMG_20260101_122510.jpg')
print(f'GPS: {metadata[\"gps_latitude\"]}, {metadata[\"gps_longitude\"]}')
print(f'Time: {metadata[\"timestamp_original\"]}')
"
```

Output:
```
GPS: 14.635189, 121.092548
Time: 2026-01-01T12:25:10
```

---

This document preserves architectural intent for future contributors and AI agents.
