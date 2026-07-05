# EXIF Plugin

**Status:** ✅ Implemented  
**Type:** Discovery Metadata Extractor  
**Reference Implementation:** This plugin serves as the reference implementation for future plugins.

---

## Overview

The EXIF plugin extracts metadata from image files, including camera information, GPS coordinates, timestamps, and technical details. This is the first and most mature plugin in the Librarian system.

---

## Inputs

| Format | Extensions | Supported |
|--------|------------|-----------|
| JPEG | .jpg, .jpeg | ✅ |
| HEIC | .heic, .heif | ✅ |
| PNG | .png | ✅ |
| TIFF | .tiff, .tif | ✅ |
| WebP | .webp | ✅ |

---

## Processing

The plugin performs the following extraction operations:

### 1. EXIF Extraction

Reads EXIF data embedded in image files:
- Camera make and model
- Lens information
- Software/firmware version
- Image dimensions
- Color space
- Orientation

### 2. GPS Extraction

Extracts geolocation data:
- Latitude (decimal degrees)
- Longitude (decimal degrees)
- Altitude (meters)

### 3. Camera Extraction

Captures device information:
- Camera make (e.g., "Canon", "Apple", "Samsung")
- Camera model (e.g., "EOS R5", "iPhone 14 Pro")
- Lens model

### 4. Timestamp Extraction

Extracts date/time information:
- Original capture date (DateTimeOriginal)
- Digitized date (DateTimeDigitized)
- File modification date

### 5. Thumbnail Generation

Generates preview thumbnails:
- Thumbnail images for display
- Preview generation for UI

---

## Artifacts

| Artifact | Description | Storage |
|----------|-------------|---------|
| metadata | Complete EXIF data as JSON | photo_metadata table |
| gps_coordinates | Parsed GPS data | photo_metadata table |
| thumbnails | Generated preview images | thumbnails/ directory |

---

## Searchable Metadata

The following metadata fields are indexed for search:

| Field | Type | Example | Searchable |
|-------|------|---------|------------|
| camera_make | string | "Apple" | ✅ |
| camera_model | string | "iPhone 14 Pro" | ✅ |
| lens_model | string | "iPhone 14 Pro back camera 6.765mm f/1.78" | ✅ |
| timestamp_original | datetime | "2026-01-01T12:25:10" | ✅ |
| gps_latitude | float | 14.635189 | ✅ |
| gps_longitude | float | 121.092548 | ✅ |
| altitude | float | 57.2 | ✅ |
| width | int | 3000 | ✅ |
| height | int | 4000 | ✅ |
| orientation | int | 1 | ❌ |
| file_format | string | "JPEG" | ✅ |

---

## Plugin Configuration

```yaml
plugins:
  photo_metadata:
    enabled: true
    job_type: extract_photo_metadata
```

---

## Implementation Details

### Files

| File | Purpose |
|------|---------|
| `workers/photo_metadata_extractor.py` | Worker handler for EXIF extraction |
| `parsers/image_parser.py` | Image parsing and EXIF extraction logic |
| `storage/postgres_backend.py` | Metadata persistence |

### Database Schema

```sql
-- photo_metadata table stores extracted EXIF data
CREATE TABLE photo_metadata (
    document_id UUID PRIMARY KEY REFERENCES documents(id),
    gps_latitude DOUBLE PRECISION,
    gps_longitude DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    camera_make VARCHAR(255),
    camera_model VARCHAR(255),
    lens_model VARCHAR(255),
    timestamp_original TIMESTAMP,
    timestamp_digitized TIMESTAMP,
    width INTEGER,
    height INTEGER,
    orientation INTEGER,
    file_format VARCHAR(50),
    raw_exif JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Lifecycle

```
Image File
  ↓
Collection Watcher discovers file
  ↓
Scanner creates document record
  ↓
PhotoMetadataExtractor worker processes
  ↓
Metadata saved to photo_metadata table
  ↓
API exposes via /timeline/photo/{document_id}
  ↓
Dashboard renders in Explorer
```

---

## Example Output

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "camera_make": "HONOR",
  "camera_model": "BRP-NX1",
  "lens_model": null,
  "timestamp_original": "2026-01-01T12:25:10",
  "gps_latitude": 14.635189,
  "gps_longitude": 121.092548,
  "altitude": 57.2,
  "width": 3000,
  "height": 4000,
  "orientation": 1,
  "file_format": "JPEG"
}
```

---

## Verification

```bash
# Run photo metadata tests
python -m pytest tests/test_photo_metadata.py -v

# Verify plugin registry
python -c "from registry.plugin_registry import get_plugin_registry; print(get_plugin_registry().list_enabled())"

# Test extraction on sample image
python -c "from parsers.image_parser import extract_photo_metadata; print(extract_photo_metadata('samples/IMG_20260101_122510.jpg'))"
```

---

## Related Documentation

- [EXIF Capabilities](./capabilities.md)
- [EXIF Metadata Schema](./metadata-schema.md)
- [EXIF Architecture](./architecture.md)
- [EXIF Roadmap](./roadmap.md)
- [Operation EXIF](../../refactor/operation-exif/)