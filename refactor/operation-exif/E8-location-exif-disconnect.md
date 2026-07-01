# E8: Location/EXIF Disconnect → Map Aggregation Layer

**Status:** Open  
**Severity:** High  
**Classification:** Open  
**Priority:** 7

## Updated Approach: Map Aggregation Layer

**E3 has been CANCELLED.** This task now implements a Map Aggregation Layer that combines GPS from `photo_metadata` with semantic locations from the `locations` table.

### Key Design Decision

GPS coordinates should **NOT** be copied to the `locations` table. Instead, the API should aggregate both sources:

```
┌─────────────────────────────────────────────────────────────┐
│                 Map Aggregation Layer                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  GET /api/locations?document_id=123                         │
│       │                                                      │
│       ├──► photo_metadata.gps_* ──► GPS Locations            │
│       │                                                      │
│       └──► locations table ─────► Semantic Locations          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Rationale

1. **Discovery vs Enrichment:** GPS is Discovery metadata (immediately available from EXIF), semantic locations are Enrichment metadata (require reverse geocoding - not implemented)
2. **Ownership clarity:** `photo_metadata` owns GPS, `locations` owns semantic names
3. **No duplication:** GPS doesn't need to be copied
4. **Simpler sync:** No dual ownership to keep in sync

---

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
| `workers/location_extractor.py` | Extracts text locations |
| `workers/photo_metadata_extractor.py` | Extracts GPS to photo_metadata |
| `storage/postgres_backend.py` | Needs unified location query |
| `api/routes/explorer.py` | Needs to query both sources |
| `api/routes/timeline.py` | Currently queries photo_metadata only |

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
│ - Saves to: photo_metadata table (GPS stays here)          │
└─────────────────────────────────────────────────────────────┘
```

## Required Changes

### 1. Backend: Unified Location Query

```python
# storage/postgres_backend.py

def get_document_locations(self, document_id: int) -> list:
    """
    Get all locations for a document from both sources.
    Returns GPS from photo_metadata AND semantic locations from locations table.
    """
    locations = []
    
    # 1. GPS from photo_metadata
    photo_meta = self.get_photo_metadata(document_id)
    if photo_meta and photo_meta.get('gps_latitude'):
        locations.append({
            'type': 'GPS',
            'latitude': photo_meta['gps_latitude'],
            'longitude': photo_meta['gps_longitude'],
            'source': 'photo_metadata'
        })
    
    # 2. Semantic locations from locations table
    semantic = self.get_locations_for_document(document_id)
    for loc in semantic:
        loc['source'] = 'locations_table'
        locations.append(loc)
    
    return locations
```

### 2. API: Unified Location Endpoint

```python
# api/routes/locations.py (new or update existing)

@router.get("/documents/{document_id}/locations")
async def get_document_locations(document_id: int):
    """
    Returns all locations for a document:
    - GPS coordinates from photo_metadata
    - Semantic locations from locations table
    """
    locations = backend.get_document_locations(document_id)
    return {"document_id": document_id, "locations": locations}
```

### 3. API: Location Search (Optional Enhancement)

```python
# Find all photos near a GPS coordinate OR containing a location name

@router.get("/documents/by-location")
async def find_documents_by_location(
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    location_name: Optional[str] = None,
    radius_km: float = 10.0
):
    """
    Find documents by GPS proximity OR location name.
    """
    results = []
    
    # By GPS proximity
    if lat is not None and lon is not None:
        gps_docs = backend.find_documents_by_gps(lat, lon, radius_km)
        results.extend(gps_docs)
    
    # By location name
    if location_name:
        named_docs = backend.find_documents_by_location_name(location_name)
        results.extend(named_docs)
    
    # Deduplicate
    return {"documents": list(set(results))}
```

## Definition of Done

- [ ] `get_document_locations()` returns GPS from photo_metadata AND semantic from locations
- [ ] API endpoint returns unified location data
- [ ] Explorer can query both sources
- [ ] Timeline can query both sources
- [ ] GPS coordinates searchable via location queries

## Dependencies

- **Hard:** E2 (structured_data handling)

## Risk Assessment

- **Medium Risk:** Requires API changes, no schema changes
- **Impact:** Unified location experience
- **Testing:** Test location queries with GPS photos and text locations

## Effort Estimate

- **Time:** 4-6 hours
- **Complexity:** Medium
- **Testing:** Test unified location queries
