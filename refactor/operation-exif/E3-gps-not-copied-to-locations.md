# E3: GPS Not Copied to locations Table

**Status:** Open  
**Severity:** High  
**Classification:** Open

## Problem Statement

GPS coordinates extracted from image EXIF data are stored in `photo_metadata` table but are **never copied to the `locations` table**. This causes:

1. Timeline API can query GPS-tagged photos (reads from photo_metadata)
2. Map API can show markers (reads from photo_metadata)
3. **BUT:** Location-based queries cannot find GPS coordinates
4. **BUT:** Reverse geocoding cannot be applied to GPS locations
5. **BUT:** Location deduplication doesn't include GPS coordinates

## Impact

- **User Impact:** GPS coordinates not searchable via location queries
- **Developer Impact:** Two different code paths for location data
- **Data Impact:** GPS locations not benefiting from location deduplication

## Affected Files

| File | Issue |
|------|-------|
| `workers/photo_metadata_extractor.py` | Extracts GPS but doesn't save to locations |
| `workers/location_extractor.py` | Only processes text, not photo_metadata |
| `storage/postgres_backend.py` | No method to link photo_metadata GPS to locations |
| `extractors/location_extractor.py` | Doesn't read photo_metadata |

## Current Flow

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

## Required Changes

### Option A: Add Job to Extract GPS Locations

Create a new job type `extract_gps_locations` that runs after `extract_photo_metadata`:

```python
# workers/gps_location_extractor.py
def process(self, job):
    photo_metadata = backend.get_photo_metadata(job['document_id'])
    if photo_metadata.get('gps_latitude') and photo_metadata.get('gps_longitude'):
        location_id = backend.save_location(
            name=f"GPS: {lat}, {lon}",
            coordinates=(lat, lon)
        )
        backend.add_location_to_document(job['document_id'], location_id)
```

### Option B: Modify PhotoMetadataExtractor

Add location saving to existing `PhotoMetadataExtractor`:

```python
# In PhotoMetadataExtractor.process()
if metadata.get('gps_latitude') and metadata.get('gps_longitude'):
    location_id = self.backend.save_location(
        name=f"GPS: {metadata['gps_latitude']}, {metadata['gps_longitude']}",
        coordinates=(metadata['gps_latitude'], metadata['gps_longitude'])
    )
    self.backend.add_location_to_document(document_id, location_id)
```

### Option C: Create LocationSync Worker

New worker that syncs GPS data between tables:

```python
# workers/location_sync_worker.py
def sync_photo_locations():
    photos = backend.get_all_photos_with_gps()
    for photo in photos:
        location_id = backend.save_location(
            name=f"GPS: {photo['gps_latitude']}, {photo['gps_longitude']}",
            coordinates=(photo['gps_latitude'], photo['gps_longitude'])
        )
        backend.add_location_to_document(photo['document_id'], location_id)
```

## Recommended Approach

**Option B - Modify PhotoMetadataExtractor**

1. Simpler than adding new jobs
2. Keeps GPS and location together
3. Single point of failure for debugging

## Definition of Done

- [ ] GPS coordinates stored in locations table
- [ ] Document linked to GPS location via document_locations
- [ ] Existing GPS-tagged photos backfilled
- [ ] Map and location queries both work with GPS data

## Dependencies

- **Hard:** E2 (structured_data handling)
- **Soft:** E1 (mime_type - can parallelize)

## Risk Assessment

- **Low Risk:** Simple database inserts
- **Impact:** Enables GPS-based location features
- **Testing:** Test with existing GPS-tagged images

## Effort Estimate

- **Time:** 2-4 hours
- **Complexity:** Low
- **Testing:** Medium (need backfill logic)

## Existing GPS Data

Current database state:
- `photo_metadata`: 0 rows (but jobs queued)
- `locations`: 2 rows (text-extracted, no GPS)

After fix, expected:
- `locations`: ~500+ rows (GPS-based)
- `document_locations`: Matching count
