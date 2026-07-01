# E8: Location/EXIF Disconnect

**Status:** Open  
**Severity:** High  
**Classification:** Open

## Problem Statement

Location extraction and EXIF extraction operate in isolation:

1. **LocationExtractor:** Reads `document_content`, extracts text locations
2. **PhotoMetadataExtractor:** Reads image files, extracts EXIF/GPS
3. **No connection:** GPS coordinates don't flow to location queries
4. **Timeline vs Explorer:** Different data sources for location data

## Impact

- **User Impact:** Cannot search photos by location name
- **Developer Impact:** Two separate location code paths
- **Data Impact:** GPS coordinates only usable in Timeline, not Explorer

## Affected Files

| File | Issue |
|------|-------|
| `workers/location_extractor.py` | Only reads text, not photo_metadata |
| `workers/photo_metadata_extractor.py` | Doesn't save to locations |
| `extractors/location_extractor.py` | Doesn't read photo_metadata |
| `api/routes/explorer.py` | Different query path than timeline |
| `api/routes/timeline.py` | Different query path than explorer |

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ LocationExtractor                                           │
│ - Reads: document_content.text                             │
│ - Extracts: City, State, Country, ZIP                      │
│ - Saves to: locations table                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ separate
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ PhotoMetadataExtractor                                      │
│ - Reads: image files                                       │
│ - Extracts: GPS, EXIF, camera                             │
│ - Saves to: photo_metadata table (NOT locations)           │
└─────────────────────────────────────────────────────────────┘
```

## Required Changes

### 1. Unified Location Data

```
GPS Coordinates (from photo_metadata)
    │
    ├─→ Reverse geocode (future)
    │
    └─→ Save to locations table (E3)
            │
            └─→ link_location_to_document(doc_id, location_id)
                    │
                    └─→ Available in location queries
```

### 2. Cross-Reference Locations

```python
# When photo has GPS coordinates:
# 1. Extract GPS to photo_metadata (done)
# 2. Create location record (E3)
# 3. Link document to location
# 4. Future: reverse geocode for city/state/country

# Then LocationExtractor can:
# - Query photo_metadata for GPS
# - Find nearby text-extracted locations
# - Match or suggest location names
```

### 3. Timeline + Explorer Integration

```python
# Get locations for a document
def get_document_locations(document_id):
    locations = []
    
    # 1. Text-extracted locations
    text_locations = backend.get_locations_for_document(document_id)
    locations.extend(text_locations)
    
    # 2. GPS locations
    photo_meta = backend.get_photo_metadata(document_id)
    if photo_meta and photo_meta.get('gps_latitude'):
        gps_location = {
            'type': 'GPS',
            'latitude': photo_meta['gps_latitude'],
            'longitude': photo_meta['gps_longitude']
        }
        locations.append(gps_location)
    
    return locations
```

## Definition of Done

- [ ] GPS locations queryable via location API
- [ ] Explorer shows GPS locations for photos
- [ ] Timeline shows text locations for photos
- [ ] Location deduplication works across sources

## Dependencies

- E3 (GPS to locations)

## Risk Assessment

- **Medium Risk:** Requires coordinating two systems
- **Impact:** Unified location experience
- **Testing:** Test location queries with GPS photos

## Effort Estimate

- **Time:** 4-6 hours
- **Complexity:** Medium
- **Testing:** Test unified location queries
