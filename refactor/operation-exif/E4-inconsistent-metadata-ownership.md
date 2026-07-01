# E4: Metadata Ownership Contract

**Status:** Completed  
**Severity:** High  
**Classification:** Architectural Violation  
**Completed:** 2026-07-01

## Executive Summary

This document establishes the authoritative ownership boundaries for all metadata in Librarian. Every metadata field has exactly one owner, eliminating duplication, synchronization issues, and unclear APIs.

## Core Principle: Discovery vs Enrichment

Metadata is classified into two layers with distinct ownership:

### Discovery Metadata
- **When:** Exists immediately upon artifact discovery
- **Source:** Filesystem (no processing required)
- **Owner:** `inventory` (CollectionWatcher)
- **Characteristics:** Rebuildable from filesystem, never depends on workers

### Enrichment Metadata
- **When:** Asynchronous, extracted by workers
- **Source:** Worker processing
- **Owner:** `photo_metadata`, `document_content`, `entities`, `locations`, `events`, `embeddings`
- **Characteristics:** Independently rebuildable, worker-owned

---

## Metadata Ownership Matrix

### Field                     Owner                  Layer          Persistence Table
-------------------------------------------------------------------------------------------
**Discovery Metadata**
`path`                       inventory              discovery      documents
`extension`                  inventory              discovery      documents
`file_size`                  inventory              discovery      documents
`modified_time`              inventory              discovery      documents
`mime_type`                  inventory              discovery      documents
`artifact_type`              inventory              discovery      documents
`sha256`                     inventory              discovery      documents
`status`                     system                 discovery      documents
`exists_on_disk`             inventory              discovery      documents
`deleted_at`                 inventory              discovery      documents
`lifecycle_state`            system                 discovery      documents

**Enrichment Metadata**
`timestamp_original`          photo_metadata         enrichment     photo_metadata
`timestamp_digitized`        photo_metadata         enrichment     photo_metadata
`timestamp_metadata`         photo_metadata         enrichment     photo_metadata
`gps_latitude`               photo_metadata         enrichment     photo_metadata
`gps_longitude`              photo_metadata         enrichment     photo_metadata
`gps_altitude`               photo_metadata         enrichment     photo_metadata
`camera_make`                photo_metadata         enrichment     photo_metadata
`camera_model`               photo_metadata         enrichment     photo_metadata
`lens_model`                 photo_metadata         enrichment     photo_metadata
`width`                      photo_metadata         enrichment     photo_metadata
`height`                     photo_metadata         enrichment     photo_metadata
`orientation`                photo_metadata         enrichment     photo_metadata
`file_format`                photo_metadata         enrichment     photo_metadata
`raw_exif`                   photo_metadata         enrichment     photo_metadata

`content`                    document_content       enrichment     document_content
`content_hash`               document_content       enrichment     document_content
`character_count`            document_content       enrichment     document_content
`encoding`                    document_content       enrichment     document_content
`extraction_method`           document_content       enrichment     document_content

`entities`                   entities               enrichment     entities/document_entities
`entity_type`                entities               enrichment     entities
`normalized_value`           entities               enrichment     entities

`locations`                  locations              enrichment     locations/document_locations
`latitude`                   locations              enrichment     locations
`longitude`                  locations              enrichment     locations

`events`                     events                 enrichment     events/document_events
`timestamp`                  events                 enrichment     events
`event_type`                 events                 enrichment     events
`description`                events                 enrichment     events

`embeddings`                 embeddings             enrichment     document_embeddings
`dimensions`                 embeddings             enrichment     document_embeddings
`model`                      embeddings             enrichment     document_embeddings

`thumbnail_path`             thumbnail_store        enrichment     (E5 - future)

---

## Detailed Ownership Contracts

### 1. Inventory (Discovery Metadata)

**Owner:** `inventory`  
**Component:** `CollectionWatcher`  
**Layer:** Discovery  
**Persistence:** `documents` table

#### Owned Fields
| Field | Source | Rebuildable From |
|-------|--------|------------------|
| `path` | Filesystem | Filesystem |
| `extension` | Filesystem | Filesystem |
| `file_size` | Filesystem (st_size) | Filesystem |
| `modified_time` | Filesystem (st_mtime) | Filesystem |
| `mime_type` | Extension mapping | Filesystem |
| `artifact_type` | Parser (optional) | Filesystem |
| `sha256` | Computed on discovery | Filesystem |
| `status` | System | N/A (derived) |
| `exists_on_disk` | System | Filesystem |
| `deleted_at` | System | Filesystem |
| `lifecycle_state` | System | N/A (derived) |

#### API Source
- `GET /api/explorer/...` - All discovery fields available

#### UI Source
- Explorer folder tree
- Document listing
- Detail panel (basic info)

---

### 2. Photo Metadata (Enrichment Metadata)

**Owner:** `photo_metadata`  
**Component:** `PhotoMetadataExtractor` (worker)  
**Layer:** Enrichment  
**Persistence:** `photo_metadata` table

#### Owned Fields
| Field | Source | Notes |
|-------|--------|-------|
| `timestamp_original` | EXIF DateTimeOriginal | When photo was taken |
| `timestamp_digitized` | EXIF DateTimeDigitized | When digitized |
| `timestamp_metadata` | EXIF DateTime | File modification |
| `gps_latitude` | EXIF GPS | Decimal degrees |
| `gps_longitude` | EXIF GPS | Decimal degrees |
| `gps_altitude` | EXIF GPS | Meters |
| `camera_make` | EXIF | Manufacturer |
| `camera_model` | EXIF | Model name |
| `lens_model` | EXIF | Lens identifier |
| `width` | Image/PIL | Pixels |
| `height` | Image/PIL | Pixels |
| `orientation` | EXIF | 1=normal, 3=rotated180, 6=rotated270, 8=rotated90 |
| `file_format` | EXIF/MIME | Detected format |
| `raw_exif` | EXIF | JSONB for debugging |

#### Parser Responsibility
`parsers/image_parser.py` provides `width` and `height` via PIL (lightweight), but `PhotoMetadataExtractor` re-extracts these via EXIF for completeness.

#### Ownership Note
GPS coordinates belong exclusively to `photo_metadata`, NOT to `locations`. Semantic locations extracted from text belong to `locations`. See E8 for Map Aggregation Layer integration.

#### API Source
- `GET /api/timeline/...` - Photo-specific endpoints
- `GET /api/explorer/documents/{id}` - Includes photo_metadata

#### UI Source
- Timeline view
- Map view
- Photo detail panel

---

### 3. Document Content (Enrichment Metadata)

**Owner:** `document_content`  
**Component:** `ContentExtractor` (worker)  
**Layer:** Enrichment  
**Persistence:** `document_content` table

#### Owned Fields
| Field | Source | Notes |
|-------|--------|-------|
| `content` | Parser | Extracted text |
| `content_hash` | Computed | SHA256 of content |
| `character_count` | Computed | Len of content |
| `encoding` | Detected | Text encoding |
| `extraction_method` | System | 'textract', 'ocr', etc. |

#### Parser Responsibility
Parsers (`TextParser`, `JsonParser`, etc.) extract text content. `ContentExtractor` worker persists to database.

#### Ownership Note
OCR output for images is stored in `document_content` with `extraction_method = 'ocr'`. The `RUN_OCR` job type handles image OCR.

#### API Source
- `GET /api/questions/...` - Uses content for Q&A
- `GET /api/search/...` - Content search

---

### 4. Entities (Enrichment Metadata)

**Owner:** `entities`  
**Component:** `EntityExtractor` (worker)  
**Layer:** Enrichment  
**Persistence:** `entities` + `document_entities` tables

#### Owned Fields
| Field | Source | Notes |
|-------|--------|-------|
| `type` | Extractor | PERSON, ORGANIZATION, etc. |
| `value` | Extractor | Raw extracted value |
| `normalized_value` | Extractor | Lowercase, normalized |

#### Ownership Note
Entities are derived from `document_content`. Parser `structured_data` may contain entity-like data but is NOT persisted.

#### API Source
- `GET /api/explorer/documents/{id}/entities` - Document entities
- `GET /api/search/entities/...` - Entity search

---

### 5. Locations (Enrichment Metadata)

**Owner:** `locations`  
**Component:** `LocationExtractor` (worker)  
**Layer:** Enrichment  
**Persistence:** `locations` + `document_locations` tables

#### Owned Fields
| Field | Source | Notes |
|-------|--------|-------|
| `name` | Text extraction | "San Francisco, CA" |
| `latitude` | Geocoding (future) | Optional |
| `longitude` | Geocoding (future) | Optional |

#### Ownership Note
Text-extracted locations (from document content) belong to `locations`. GPS coordinates from EXIF belong to `photo_metadata`. These are distinct sources unified by E8 Map Aggregation Layer.

#### API Source
- `GET /api/search/locations/...` - Location search

---

### 6. Events (Enrichment Metadata)

**Owner:** `events`  
**Component:** `EventExtractor` (worker)  
**Layer:** Enrichment  
**Persistence:** `events` + `document_events` tables

#### Owned Fields
| Field | Source | Notes |
|-------|--------|-------|
| `timestamp` | Text extraction | Date/time string |
| `event_type` | Extractor | DATE, TIME, RELATIVE, etc. |
| `description` | Extractor | Human-readable |

#### Ownership Note
Events are derived from `document_content`. No overlap with `photo_metadata.timestamps`.

#### API Source
- `GET /api/search/events/...` - Event search

---

### 7. Embeddings (Enrichment Metadata)

**Owner:** `embeddings`  
**Component:** `EmbeddingGenerator` (worker)  
**Layer:** Enrichment  
**Persistence:** `document_embeddings` table

#### Owned Fields
| Field | Source | Notes |
|-------|--------|-------|
| `embedding` | Model output | JSON-serialized vector |
| `model` | System | 'openai', 'sentence-transformers', 'tfidf' |
| `dimensions` | Computed | Vector dimension count |

#### Ownership Note
Embeddings are generated from `document_content`. Image/video embeddings may come from OCR/transcription output.

#### API Source
- Semantic search (internal use)

---

### 8. Thumbnail Store (Planned - E5)

**Owner:** `thumbnail_store`  
**Component:** ThumbnailGenerator (worker)  
**Layer:** Enrichment  
**Persistence:** Filesystem + metadata table (future)

#### Owned Fields
| Field | Source | Notes |
|-------|--------|-------|
| `thumbnail_path` | Generator | Filesystem path |
| `width` | Generator | Thumbnail dimensions |
| `height` | Generator | Thumbnail dimensions |

---

## Ownership Rules

### Discovery Phase Rules
1. **Discovery metadata is filesystem-derived:** path, extension, file_size, modified_time, mime_type
2. **Discovery happens immediately:** No worker processing required
3. **Discovery is idempotent:** Same file = same discovery metadata
4. **Discovery metadata is never dropped:** Always persisted

### Enrichment Phase Rules
1. **Enrichment metadata is worker-produced:** Only available after processing
2. **Each worker owns its domain:** PhotoMetadataExtractor owns photo metadata, EntityExtractor owns entities
3. **Enrichment is async:** Discovery completes before enrichment starts
4. **Enrichment may be partial:** Some fields may be NULL if extraction fails

### Ownership Boundaries
1. **No field duplication:** GPS in photo_metadata ONLY, not in locations
2. **No cross-layer ownership:** Discovery owns discovery, enrichment owns enrichment
3. **Parser → Worker handoff is explicit:** Parser output feeds into worker input
4. **structured_data is transient:** Produced by parser, consumed by workers, NOT persisted

---

## Data Flow Diagram

```
FILESYSTEM
    │
    │ (immediate, no worker)
    ▼
┌─────────────────────────────────────────────────────────────┐
│                     DISCOVERY PHASE                         │
│  CollectionWatcher → discover_artifact() → documents table  │
│                                                              │
│  Owns: path, extension, file_size, modified_time,           │
│        mime_type, artifact_type, sha256                      │
└─────────────────────────────────────────────────────────────┘
    │
    │ (creates jobs)
    ▼
┌─────────────────────────────────────────────────────────────┐
│                     ENRICHMENT PHASE                         │
│  Workers (async) → save_*() methods → persistence tables      │
│                                                              │
│  PhotoMetadataExtractor → photo_metadata table                │
│    Owns: gps_*, camera_*, timestamp_*, dimensions, raw_exif   │
│                                                              │
│  ContentExtractor → document_content table                   │
│    Owns: content, content_hash, character_count              │
│                                                              │
│  EntityExtractor → entities + document_entities              │
│    Owns: type, value, normalized_value                       │
│                                                              │
│  LocationExtractor → locations + document_locations          │
│    Owns: name, (geocoded lat/lon if available)              │
│                                                              │
│  EventExtractor → events + document_events                   │
│    Owns: timestamp, event_type, description                 │
│                                                              │
│  EmbeddingGenerator → document_embeddings                    │
│    Owns: embedding vector, model, dimensions                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Parser vs Worker Responsibility Matrix

```
Field              Parser Produces    Worker Extracts    Persistence
----------------------------------------------------------------------
path                    ✓                   -              documents
extension               ✓                   -              documents
mime_type               ✓ (map)             -              documents
artifact_type           ✓ (map)             -              documents
file_size               -                   -              documents
modified_time           -                   -              documents

text content            ✓                   -              document_content
structured_data         ✓                   -              (transient)

width/height            ✓ (PIL)             ✓ (EXIF)       photo_metadata
dimensions (final)      -                   ✓              photo_metadata

GPS/camera/timestamps   -                   ✓              photo_metadata
EXIF raw                -                   ✓              photo_metadata

entities                -                   ✓              entities
locations (text)        -                   ✓              locations
events                  -                   ✓              events
embeddings              -                   ✓              document_embeddings

ocr_text                -                   ✓              document_content
```

---

## Storage Locations Reference

| Table | Owner | Type |
|-------|-------|------|
| `documents` | inventory | Discovery |
| `photo_metadata` | photo_metadata | Enrichment |
| `document_content` | document_content | Enrichment |
| `entities` | entities | Enrichment |
| `document_entities` | entities | Enrichment (junction) |
| `locations` | locations | Enrichment |
| `document_locations` | locations | Enrichment (junction) |
| `events` | events | Enrichment |
| `document_events` | events | Enrichment (junction) |
| `document_embeddings` | embeddings | Enrichment |

---

## API Sources Reference

| Endpoint | Metadata Available | Source |
|----------|-------------------|--------|
| `GET /api/explorer/folders` | path, extension, file_size | inventory |
| `GET /api/explorer/documents/{id}` | discovery + photo_metadata | inventory + photo_metadata |
| `GET /api/timeline/stats` | photo_metadata counts | photo_metadata |
| `GET /api/timeline/photos` | photo_metadata | photo_metadata |
| `GET /api/timeline/map` | GPS + photo metadata | photo_metadata |
| `GET /api/search/entities` | entities | entities |
| `GET /api/search/locations` | locations | locations |
| `GET /api/search/events` | events | events |
| `GET /api/questions` | content + entities | document_content + entities |

---

## Definition of Done (E4)

- [x] Ownership policy documented
- [x] Parser ownership clear (discovery metadata only)
- [x] Worker ownership clear (enrichment metadata per worker)
- [x] Data flow between phases clear (Discovery → Enrichment)
- [x] No metadata dropped (except transient structured_data)
- [x] Ownership matrix created
- [x] Rules documented
- [x] Storage locations documented
- [x] API sources documented

---

## Implementation Notes

### E4 is Complete
This is a **documentation-only task**. No code changes were required because:

1. **Ownership is already correct in the implementation:**
   - `collection_watcher.py` correctly owns discovery metadata
   - Workers correctly own their respective enrichment metadata
   - Database schema reflects the ownership model

2. **The documentation clarifies what was implicit:**
   - Formalizes the Discovery vs Enrichment separation
   - Eliminates ambiguity about parser role
   - Documents the GPS/location boundary (E3 cancelled in favor of E8)

3. **Prevents future violations:**
   - New developers know where to add fields
   - PR reviewers can catch cross-layer ownership
   - E8 and future work have clear contracts

### Future Work
- E5 (Thumbnails): Will add `thumbnail_store` ownership
- E8 (Map Aggregation): Will define API-level unification without changing ownership

---

## Dependencies

- E1 (mime_type) - Complete - mime_type now correctly owned by inventory
- E2 (structured_data) - Future - Will document transient nature
- E3 (GPS to locations) - **Cancelled** - GPS stays in photo_metadata

---

## Risk Assessment

- **Risk:** None (documentation only)
- **Impact:** High (prevents ownership violations)
- **Testing:** Code review sufficient

## Effort

- **Time:** 2-3 hours
- **Complexity:** Low
- **Actual:** ~2 hours (analysis + documentation)
