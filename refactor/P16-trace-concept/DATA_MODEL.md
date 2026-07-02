# DATA_MODEL.md — Schema Audit for Trace Support

## Overview

This document audits the existing data model to determine what already supports Trace functionality and what gaps need to be addressed.

## Audit Scope

The audit covers these core entities:
- `documents` — Primary artifact storage
- `photo_metadata` — EXIF and media metadata
- `locations` — Geographic data
- `entities` — Recognized people/places/objects
- `relationships` — Connections between artifacts
- `timeline_events` — Temporal event data

---

## 1. Documents (Primary Artifacts)

### Current Schema

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES collections(id),
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    mime_type VARCHAR(100),
    size_bytes BIGINT,
    width INTEGER,
    height INTEGER,
    duration_seconds REAL,
    hash_sha256 VARCHAR(64),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    modified_at TIMESTAMPTZ DEFAULT NOW(),
    captured_at TIMESTAMPTZ,  -- When content was captured (EXIF)
    
    -- Content
    content TEXT,  -- OCR text, transcript, etc.
    thumbnail_path TEXT,
    preview_path TEXT,
    
    -- Status
    is_indexed BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    is_favorite BOOLEAN DEFAULT FALSE,
    
    -- Classification
    document_type VARCHAR(50),  -- 'image', 'video', 'document', 'audio'
    
    -- Audit
    imported_at TIMESTAMPTZ DEFAULT NOW(),
    imported_from VARCHAR(255),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    extraction_metadata JSONB DEFAULT '{}'
);
```

### Trace Coverage Analysis

| Trace Property | Current Support | Notes |
|--------------|-----------------|-------|
| ID | ✅ Full | UUID primary key |
| Time: captured_at | ✅ Full | EXIF `captured_at` field |
| Time: created_at | ✅ Full | `created_at` timestamp |
| Time: modified_at | ✅ Full | `modified_at` timestamp |
| Location: coordinates | ⚠️ Partial | In `photo_metadata`, not here |
| Location: altitude | ⚠️ Partial | In `photo_metadata` |
| Location: accuracy | ❌ Missing | No accuracy field |
| Location: heading | ❌ Missing | No heading field |
| Location: speed | ❌ Missing | No speed field |
| Device: source | ⚠️ Partial | In `photo_metadata` |
| Device: make/model | ⚠️ Partial | In `photo_metadata` |
| Device: serial | ❌ Missing | No device serial |
| Device: type | ❌ Missing | No device categorization |
| Collection | ✅ Full | `collection_id` reference |
| Tags | ⚠️ Partial | In separate `tags` table |
| Entities | ⚠️ Partial | In separate `entities` table |
| Relationships | ⚠️ Partial | In separate `relationships` table |
| File type | ✅ Full | `document_type`, `mime_type` |
| Size/dimensions | ✅ Full | `size_bytes`, `width`, `height` |

### Gap Analysis: Documents

**✅ Already Supports Trace:**
- ID, timestamps, collection, file type, dimensions

**⚠️ Partially Supports:**
- Location data (in `photo_metadata` table, not directly accessible)

**❌ Missing for Trace:**
- Device serial number
- Device type categorization
- Location accuracy/heading/speed
- Direct access to location fields

**Recommendations:**
1. Add location fields directly to `documents` table for performance
2. Add device type enum/categorization
3. Create computed `location_cluster` field

---

## 2. Photo Metadata

### Current Schema

```sql
CREATE TABLE photo_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Camera info
    camera_make VARCHAR(100),
    camera_model VARCHAR(100),
    lens_info VARCHAR(255),
    serial_number VARCHAR(100),
    
    -- Capture settings
    iso INTEGER,
    aperture REAL,
    shutter_speed VARCHAR(50),
    focal_length REAL,
    flash BOOLEAN,
    
    -- Location (GPS)
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    gps_accuracy DOUBLE PRECISION,
    gps_timestamp TIMESTAMPTZ,
    
    -- Reverse geocoding
    location_country VARCHAR(100),
    location_state VARCHAR(100),
    location_city VARCHAR(100),
    location_suburb VARCHAR(100),
    location_street VARCHAR(255),
    location_formatted TEXT,
    
    -- Timestamps
    date_taken TIMESTAMPTZ,
    date_digitized TIMESTAMPTZ,
    
    -- Orientation
    orientation INTEGER,
    rotation INTEGER DEFAULT 0,
    
    -- Software
    software VARCHAR(255),
    
    -- Raw data
    exif_data JSONB DEFAULT '{}',
    
    -- Status
    is_geocoded BOOLEAN DEFAULT FALSE,
    is_processed BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_photo_metadata_location ON photo_metadata (latitude, longitude);
CREATE INDEX idx_photo_metadata_date ON photo_metadata (date_taken);
CREATE INDEX idx_photo_metadata_camera ON photo_metadata (camera_make, camera_model);
```

### Trace Coverage Analysis

| Trace Property | Current Support | Notes |
|--------------|-----------------|-------|
| Device: make | ✅ Full | `camera_make` |
| Device: model | ✅ Full | `camera_model` |
| Device: serial | ✅ Full | `serial_number` |
| Device: lens | ✅ Full | `lens_info` |
| Location: lat/lng | ✅ Full | `latitude`, `longitude` |
| Location: altitude | ✅ Full | `altitude` |
| Location: accuracy | ✅ Full | `gps_accuracy` |
| Location: heading | ❌ Missing | No direction field |
| Location: speed | ❌ Missing | No velocity field |
| Location: reverse geocode | ✅ Full | Country/state/city/street |
| Location: formatted | ✅ Full | `location_formatted` |
| Time: date_taken | ✅ Full | `date_taken` |
| Time: date_digitized | ✅ Full | `date_digitized` |
| Capture settings | ✅ Full | ISO, aperture, shutter, focal |
| EXIF raw data | ✅ Full | `exif_data` JSONB |

### Gap Analysis: Photo Metadata

**✅ Already Supports Trace:**
- Device identification (make, model, serial, lens)
- GPS location (coordinates, altitude, accuracy)
- Reverse geocoding (all address components)
- Timestamps (date taken, digitized)
- Capture settings

**⚠️ Partially Supports:**
- Speed/heading (could be computed from GPS sequence)

**❌ Missing for Trace:**
- Direction/heading from GPS
- Velocity from GPS sequence
- Device type categorization (smartphone vs DSLR vs drone)

**Recommendations:**
1. Add `heading` and `speed` fields computed from GPS sequence
2. Create `device_type` derived field from camera_make/model
3. Add spatial index for efficient geo-queries

---

## 3. Locations

### Current Schema

```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Coordinates
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    altitude DOUBLE PRECISION,
    
    -- Geocoding
    place_id VARCHAR(255),  -- Google Places, etc.
    location_name VARCHAR(255),
    location_type VARCHAR(100),  -- 'country', 'state', 'city', 'poi'
    
    -- Address components
    address_line VARCHAR(255),
    street_number VARCHAR(50),
    street_name VARCHAR(100),
    locality VARCHAR(100),
    region VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    country_code VARCHAR(10),
    
    -- Formatted
    formatted_address TEXT,
    
    -- Semantic location
    semantic_label VARCHAR(100),  -- 'home', 'work', 'school'
    semantic_type VARCHAR(50),
    
    -- Accuracy
    accuracy_meters DOUBLE PRECISION,
    source VARCHAR(50),  -- 'gps', 'wifi', 'manual', 'reverse_geocode'
    
    -- Time spent
    arrival_time TIMESTAMPTZ,
    departure_time TIMESTAMPTZ,
    dwell_time_seconds INTEGER,
    
    -- Clustering
    geohash VARCHAR(12),
    cluster_id UUID,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_coordinates CHECK (
        latitude >= -90 AND latitude <= 90 AND
        longitude >= -180 AND longitude <= 180
    )
);

CREATE INDEX idx_locations_geohash ON locations (geohash);
CREATE INDEX idx_locations_cluster ON locations (cluster_id);
CREATE INDEX idx_locations_semantic ON locations (semantic_label);
```

### Trace Coverage Analysis

| Trace Property | Current Support | Notes |
|--------------|-----------------|-------|
| Location: coordinates | ✅ Full | `latitude`, `longitude` |
| Location: altitude | ✅ Full | `altitude` |
| Location: accuracy | ✅ Full | `accuracy_meters` |
| Location: address | ✅ Full | All address components |
| Location: formatted | ✅ Full | `formatted_address` |
| Location: semantic | ✅ Full | `semantic_label`, `semantic_type` |
| Location: geohash | ✅ Full | `geohash` for clustering |
| Location: cluster | ✅ Full | `cluster_id` |
| Location: source | ✅ Full | `source` field |
| Time: arrival/departure | ✅ Full | `arrival_time`, `departure_time` |
| Time: dwell time | ✅ Full | `dwell_time_seconds` |
| POI reference | ✅ Full | `place_id`, `location_name` |

### Gap Analysis: Locations

**✅ Already Supports Trace:**
- All core location properties
- Semantic location labels
- Clustering support (geohash, cluster_id)
- Time spent tracking (arrival/departure/dwell)
- Source tracking

**❌ Missing for Trace:**
- Heading/direction
- Velocity/speed
- Route/path association

**Recommendations:**
1. Current schema is comprehensive for location data
2. Add `heading` field for direction-aware features
3. Consider `route_id` foreign key for path association

---

## 4. Entities

### Current Schema

```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Entity type
    entity_type VARCHAR(50) NOT NULL,  -- 'person', 'place', 'object', 'logo', 'text'
    
    -- Entity details
    name VARCHAR(255),
    label VARCHAR(255),  -- Display label
    
    -- Classification
    category VARCHAR(100),  -- For objects: 'vehicle', 'animal', 'food', etc.
    subcategory VARCHAR(100),
    
    -- Confidence
    confidence DOUBLE PRECISION DEFAULT 1.0,
    
    -- Location in image
    bounding_box JSONB,  -- {x, y, width, height}
    centroid_x INTEGER,
    centroid_y INTEGER,
    
    -- For people
    face_id UUID,
    is_known BOOLEAN DEFAULT FALSE,
    person_id UUID REFERENCES persons(id),
    
    -- For places
    place_id VARCHAR(255),  -- POI reference
    location_latitude DOUBLE PRECISION,
    location_longitude DOUBLE PRECISION,
    
    -- For text
    text_content TEXT,
    text_language VARCHAR(10),
    is_ocr BOOLEAN DEFAULT FALSE,
    
    -- Source
    source VARCHAR(50),  -- 'ai_detection', 'ocr', 'manual', 'face_recognition'
    model_version VARCHAR(50),
    
    -- Status
    is_verified BOOLEAN DEFAULT FALSE,
    is_reviewed BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_entities_document ON entities (document_id);
CREATE INDEX idx_entities_type ON entities (entity_type);
CREATE INDEX idx_entities_person ON entities (person_id) WHERE person_id IS NOT NULL;
CREATE INDEX idx_entities_name ON entities (name) WHERE name IS NOT NULL;
```

### Trace Coverage Analysis

| Trace Property | Current Support | Notes |
|--------------|-----------------|-------|
| Entities: people | ✅ Full | `entity_type='person'`, `person_id` |
| Entities: places | ✅ Full | `entity_type='place'`, `place_id` |
| Entities: objects | ✅ Full | `entity_type='object'`, `category` |
| Entities: logos | ✅ Full | `entity_type='logo'` |
| Entities: text | ✅ Full | `entity_type='text'`, `text_content` |
| Confidence | ✅ Full | `confidence` field |
| Bounding box | ✅ Full | `bounding_box`, centroid |
| Known status | ✅ Full | `is_known`, `person_id` |
| Source tracking | ✅ Full | `source` field |

### Gap Analysis: Entities

**✅ Already Supports Trace:**
- All entity types (people, places, objects, logos, text)
- Confidence scoring
- Spatial location in image
- Person database integration
- POI reference for places
- Source/model tracking

**⚠️ Partially Supports:**
- Entity relationships (need `relationships` table)

**Recommendations:**
1. Current schema is comprehensive
2. Add entity-to-entity relationships
3. Consider `entity_aliases` for alternate names

---

## 5. Relationships

### Current Schema

```sql
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source entity
    source_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'document', 'entity', 'person', 'location'
    
    -- Target entity
    target_id UUID NOT NULL,
    target_type VARCHAR(50) NOT NULL,  -- 'document', 'entity', 'person', 'location'
    
    -- Relationship type
    relationship_type VARCHAR(100) NOT NULL,
    -- Types: 'similar_to', 'duplicate_of', 'part_of', 'contains',
    --        'taken_with', 'same_location', 'same_event', 'same_person',
    --        'derived_from', 'reply_to', 'references', 'custom'
    
    -- Properties
    confidence DOUBLE PRECISION DEFAULT 1.0,
    is_directional BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    
    -- Source of relationship
    source VARCHAR(50),  -- 'ai_detection', 'user', 'import', 'computed'
    
    -- Status
    is_verified BOOLEAN DEFAULT FALSE,
    is_auto_generated BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_relationship UNIQUE (source_id, source_type, target_id, target_type, relationship_type)
);

CREATE INDEX idx_relationships_source ON relationships (source_id, source_type);
CREATE INDEX idx_relationships_target ON relationships (target_id, target_type);
CREATE INDEX idx_relationships_type ON relationships (relationship_type);
```

### Trace Coverage Analysis

| Trace Property | Current Support | Notes |
|--------------|-----------------|-------|
| Relationships: linked | ✅ Full | Generic source/target |
| Relationships: derived | ✅ Full | `relationship_type='derived_from'` |
| Relationships: grouped | ✅ Full | `relationship_type='part_of'` |
| Relationships: same_event | ✅ Full | `relationship_type='same_event'` |
| Relationships: same_location | ✅ Full | `relationship_type='same_location'` |
| Relationships: similar | ✅ Full | `relationship_type='similar_to'` |
| Confidence | ✅ Full | `confidence` field |
| Directionality | ✅ Full | `is_directional` |

### Gap Analysis: Relationships

**✅ Already Supports Trace:**
- Generic relationship model supports all trace relationship types
- Confidence scoring
- Directionality
- Metadata for additional properties
- Source tracking

**⚠️ Partially Supports:**
- Route/path relationships (need specific type)
- Temporal sequence (need ordering field)

**Recommendations:**
1. Add `relationship_order` field for temporal sequences
2. Add specific route/path relationship types
3. Create `relationship_weight` for network analysis

---

## 6. Timeline Events

### Current Schema

```sql
CREATE TABLE timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES collections(id),
    
    -- Event identification
    event_type VARCHAR(100) NOT NULL,
    event_label VARCHAR(255),
    
    -- Temporal bounds
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INTEGER,
    
    -- Location
    location_id UUID REFERENCES locations(id),
    location_name VARCHAR(255),
    
    -- Related documents
    primary_document_id UUID REFERENCES documents(id),
    
    -- Coverage
    document_count INTEGER DEFAULT 0,
    covered_time_range JSONB,  -- {start, end} of covered period
    
    -- Event classification
    is_all_day BOOLEAN DEFAULT FALSE,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern VARCHAR(100),
    
    -- Significance
    importance_score DOUBLE PRECISION DEFAULT 0.5,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_timeline_events_time ON timeline_events (start_time, end_time);
CREATE INDEX idx_timeline_events_type ON timeline_events (event_type);
CREATE INDEX idx_timeline_events_location ON timeline_events (location_id);
```

### Trace Coverage Analysis

| Trace Property | Current Support | Notes |
|--------------|-----------------|-------|
| Event: timeline | ✅ Full | `start_time`, `end_time`, `duration` |
| Event: clustering | ✅ Full | `timeline_events` groups documents |
| Event: location | ✅ Full | `location_id` reference |
| Event: importance | ✅ Full | `importance_score` |
| Event: classification | ✅ Full | `event_type`, `event_label` |
| Event: document count | ✅ Full | `document_count` |
| Event: all-day flag | ✅ Full | `is_all_day` |

### Gap Analysis: Timeline Events

**✅ Already Supports Trace:**
- Event-based grouping
- Temporal bounds
- Location association
- Importance scoring
- Document coverage tracking

**⚠️ Partially Supports:**
- Nested events (need parent_id)

**Recommendations:**
1. Add `parent_event_id` for hierarchical events
2. Add `event_color` for visualization
3. Add `event_icon` for UI representation

---

## Summary: Gap Analysis

### Gaps Identified

| Category | Gap | Severity | Recommendation |
|----------|-----|----------|----------------|
| **Documents** | Device type categorization | Medium | Add `device_type` derived/enum field |
| **Documents** | Speed/heading fields | Low | Add from GPS sequence computation |
| **Documents** | Location direct access | Medium | Denormalize location to documents table |
| **Photo Metadata** | Heading/direction | Medium | Add computed field from GPS sequence |
| **Photo Metadata** | Velocity | Low | Add computed field from GPS sequence |
| **Locations** | Heading | Medium | Add field for direction tracking |
| **Locations** | Route association | Medium | Add `route_id` foreign key |
| **Relationships** | Order in sequence | Medium | Add `relationship_order` field |
| **Relationships** | Route relationship type | Low | Add specific route types |
| **Timeline Events** | Hierarchical events | Low | Add `parent_event_id` |

### What's Already Supported

```
✅ Core Trace Model
├── ID (UUID)
├── Time (captured_at, created_at, modified_at)
├── Location (coordinates, altitude, geohash, cluster)
├── Device (make, model, serial)
├── Collection (collection_id, path)
├── Tags (separate table with references)
├── Entities (people, places, objects, logos)
├── Relationships (generic model)
└── Timeline Events (grouping, clustering)

✅ Advanced Trace Features
├── Semantic locations
├── Reverse geocoding
├── Confidence scores
├── Importance scoring
├── Source tracking
├── Clustering (geohash, cluster_id)
└── Event grouping
```

### Schema Compatibility: HIGH

The existing schema **already supports the Trace concept** with minor additions:

1. **Location denormalization** — Add location fields to `documents` for faster access
2. **Device type categorization** — Derive device type from make/model
3. **Sequence ordering** — Add order field to relationships
4. **Direction tracking** — Add heading/velocity from GPS

---

## Migration Recommendations

### Phase 1: Schema Extensions

```sql
-- Add device_type to documents
ALTER TABLE documents ADD COLUMN device_type VARCHAR(50);
ALTER TABLE documents ADD COLUMN heading DOUBLE PRECISION;
ALTER TABLE documents ADD COLUMN speed DOUBLE PRECISION;

-- Add semantic_location to documents
ALTER TABLE documents ADD COLUMN semantic_location VARCHAR(100);

-- Add geohash denormalization
ALTER TABLE documents ADD COLUMN geohash VARCHAR(12);
ALTER TABLE documents ADD COLUMN location_cluster_id UUID;

-- Add relationship ordering
ALTER TABLE relationships ADD COLUMN relationship_order INTEGER DEFAULT 0;

-- Add heading to locations
ALTER TABLE locations ADD COLUMN heading DOUBLE PRECISION;

-- Add route association to locations
ALTER TABLE locations ADD COLUMN route_id UUID;
```

### Phase 2: Computed Fields

```sql
-- Create function to compute device_type from make/model
CREATE OR REPLACE FUNCTION compute_device_type(make VARCHAR, model VARCHAR)
RETURNS VARCHAR AS $$
  -- Smartphone patterns
  IF make IN ('Apple', 'Samsung', 'Google', 'OnePlus', 'Xiaomi', 'Huawei', 'HONOR', 'OPPO', 'Vivo') THEN
    RETURN 'smartphone';
  -- DSLR patterns
  ELSIF model ILIKE '%EOS%' OR model ILIKE '%D%' OR model ILIKE '%Z%' THEN
    RETURN 'dslr';
  -- Drone patterns
  ELSIF make IN ('DJI', 'Parrot', 'Autel') THEN
    RETURN 'drone';
  -- Action camera
  ELSIF make IN ('GoPro', 'Insta360') THEN
    RETURN 'action_camera';
  END IF;
  RETURN 'unknown';
$$ LANGUAGE plpgsql;

-- Create geohash function for locations
-- Using PostGIS extension for spatial operations
```

### Phase 3: Indexes

```sql
-- Create composite indexes for Trace queries
CREATE INDEX idx_documents_trace_time ON documents (captured_at DESC);
CREATE INDEX idx_documents_trace_location ON documents (latitude, longitude);
CREATE INDEX idx_documents_trace_device ON documents (device_type, captured_at);
CREATE INDEX idx_documents_trace_collection ON documents (collection_id, captured_at);
CREATE INDEX idx_documents_trace_type ON documents (document_type, captured_at);

-- Create GIST index for spatial queries
CREATE INDEX idx_documents_location_gist ON documents USING GIST (
  ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
);
```

---

## Conclusion

### Overall Assessment: ✅ COMPATIBLE

The existing data model **already supports the Trace concept** with ~90% coverage. The remaining gaps are minor and can be addressed with:

1. **Schema extensions** — Add 5-6 new columns across tables
2. **Computed fields** — Add functions for device type, geohash, heading
3. **Index optimization** — Add composite indexes for Trace queries

### No Major Refactoring Required

Trace can be implemented as a **view/query layer** on top of the existing schema, with targeted denormalization for performance.

### Recommended First Steps

1. Add `device_type`, `geohash`, `location_cluster_id` to `documents`
2. Add `relationship_order` to `relationships`
3. Create Trace query service that aggregates existing tables
4. Implement filter palette UI
5. Add composite indexes for performance

---

*Schema audit complete. Trace implementation is feasible with minimal schema changes.*