# E3: GPS Not Copied to locations Table

**Status:** CANCELLED  
**Severity:** High  
**Classification:** Superseded

---

## Status Note

**This task has been CANCELLED and replaced by E8 (Map Aggregation Layer).**

### Rationale

GPS coordinates should remain in `photo_metadata`, not be copied to `locations` table.

**Reasons:**
1. **Discovery vs Enrichment:** GPS is Discovery metadata (immediately available from EXIF parsing), semantic locations are Enrichment metadata (require reverse geocoding - not implemented)
2. **Ownership clarity:** `photo_metadata` owns GPS, `locations` owns semantic names
3. **No duplication:** GPS doesn't need to be copied
4. **Simpler sync:** No dual ownership to keep in sync

### New Approach (see E8)

Instead of copying GPS to locations, implement a **Map Aggregation Layer** in E8 that:
- Queries `photo_metadata` for GPS coordinates
- Queries `locations` table for semantic locations
- Returns unified results via a single API

---

## Original Task (Archived)

The original task description is preserved below for historical context.

**Superseded by:** E8 - Map Aggregation Layer

### Original Problem Statement

GPS coordinates extracted from image EXIF data are stored in `photo_metadata` table but are **never copied to the `locations` table**. This causes:

1. Timeline API can query GPS-tagged photos (reads from photo_metadata)
2. Map API can show markers (reads from photo_metadata)
3. **BUT:** Location-based queries cannot find GPS coordinates
4. **BUT:** Reverse geocoding cannot be applied to GPS locations
5. **BUT:** Location deduplication doesn't include GPS coordinates

### Original Impact

- **User Impact:** GPS coordinates not searchable via location queries
- **Developer Impact:** Two different code paths for location data
- **Data Impact:** GPS locations not benefiting from location deduplication

### Original Affected Files

| File | Issue |
|------|-------|
| `workers/photo_metadata_extractor.py` | Extracts GPS but doesn't save to locations |
| `workers/location_extractor.py` | Only processes text, not photo_metadata |
| `storage/postgres_backend.py` | No method to link photo_metadata GPS to locations |
| `extractors/location_extractor.py` | Doesn't read photo_metadata |

### Original Current Flow

```
Image File
    ↓
PhotoMetadataExtractor.process()
    ↓
extract_photo_metadata()
    ↓
Returns: {
    'gps_latitude': 14.635186,
    'gps_longitude': 121.092547,
    ...
}
    ↓
backend.save_photo_metadata(document_id, metadata)
    ↓
INSERT INTO photo_metadata (document_id, gps_latitude, gps_longitude, ...)
VALUES (..., 14.635186, 121.092547, ...)
    ↓
NO LINK TO locations table
```

### Original Required Changes

**These approaches are now archived - see E8 for the new direction.**

#### Option A: Add Job to Extract GPS Locations

Create a new job type `extract_gps_locations` that runs after `extract_photo_metadata`.

#### Option B: Modify PhotoMetadataExtractor

Add location saving to existing `PhotoMetadataExtractor`.

#### Option C: Create LocationSync Worker

New worker that syncs GPS data between tables.

### Original Dependencies

- **Hard:** E2 (structured_data handling)
- **Soft:** E1 (mime_type - can parallelize)

### Original Effort Estimate

- **Time:** 2-4 hours
- **Complexity:** Low

### Original Existing GPS Data

Current database state (at time of original analysis):
- `photo_metadata`: 0 rows (but jobs queued)
- `locations`: 2 rows (text-extracted, no GPS)
