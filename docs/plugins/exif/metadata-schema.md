# EXIF Plugin Metadata Schema

**Plugin:** EXIF Metadata Extraction  
**Status:** ✅ Implemented

---

## Overview

The EXIF plugin generates structured metadata following this JSON schema. This schema defines the canonical output format for all EXIF extraction operations.

---

## JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PhotoMetadata",
  "description": "EXIF metadata extracted from image files",
  "type": "object",
  "properties": {
    "plugin": {
      "type": "string",
      "const": "exif",
      "description": "Plugin identifier"
    },
    "version": {
      "type": "string",
      "const": "1.0",
      "description": "Schema version"
    },
    "document_id": {
      "type": "string",
      "format": "uuid",
      "description": "Document identifier in the system"
    },
    "gps": {
      "type": "object",
      "properties": {
        "latitude": {
          "type": "number",
          "minimum": -90,
          "maximum": 90,
          "description": "Latitude in decimal degrees"
        },
        "longitude": {
          "type": "number",
          "minimum": -180,
          "maximum": 180,
          "description": "Longitude in decimal degrees"
        },
        "altitude": {
          "type": "number",
          "description": "Altitude in meters"
        }
      },
      "description": "GPS coordinates if available"
    },
    "camera": {
      "type": "object",
      "properties": {
        "make": {
          "type": ["string", "null"],
          "description": "Camera manufacturer"
        },
        "model": {
          "type": ["string", "null"],
          "description": "Camera model"
        },
        "lens": {
          "type": ["string", "null"],
          "description": "Lens model"
        },
        "software": {
          "type": ["string", "null"],
          "description": "Firmware/software version"
        }
      },
      "description": "Camera information"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Original capture timestamp (ISO 8601)"
    },
    "dimensions": {
      "type": "object",
      "properties": {
        "width": {
          "type": "integer",
          "minimum": 1,
          "description": "Image width in pixels"
        },
        "height": {
          "type": "integer",
          "minimum": 1,
          "description": "Image height in pixels"
        }
      },
      "description": "Image dimensions"
    },
    "orientation": {
      "type": "integer",
      "enum": [1, 2, 3, 4, 5, 6, 7, 8],
      "description": "EXIF orientation flag (1=normal, 8=rotated 90° CW, etc.)"
    },
    "file_format": {
      "type": "string",
      "enum": ["JPEG", "PNG", "TIFF", "HEIC", "WebP"],
      "description": "Image file format"
    },
    "raw_exif": {
      "type": ["object", "null"],
      "description": "Complete raw EXIF data for debugging"
    }
  },
  "required": ["plugin", "version", "document_id"]
}
```

---

## Example Output

### Complete Output (with GPS)

```json
{
  "plugin": "exif",
  "version": "1.0",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "gps": {
    "latitude": 14.635189,
    "longitude": 121.092548,
    "altitude": 57.2
  },
  "camera": {
    "make": "HONOR",
    "model": "BRP-NX1",
    "lens": null,
    "software": null
  },
  "timestamp": "2026-01-01T12:25:10",
  "dimensions": {
    "width": 3000,
    "height": 4000
  },
  "orientation": 1,
  "file_format": "JPEG",
  "raw_exif": {
    "Make": "HONOR",
    "Model": "BRP-NX1",
    "DateTimeOriginal": "2026:01:01 12:25:10",
    "GPSLatitude": [14, 38, 6.68],
    "GPSLatitudeRef": "N",
    "GPSLongitude": [121, 5, 33.17],
    "GPSLongitudeRef": "E"
  }
}
```

### Minimal Output (no GPS, no camera)

```json
{
  "plugin": "exif",
  "version": "1.0",
  "document_id": "660e8400-e29b-41d4-a716-446655440001",
  "gps": null,
  "camera": {
    "make": null,
    "model": null,
    "lens": null,
    "software": null
  },
  "timestamp": null,
  "dimensions": {
    "width": 1920,
    "height": 1080
  },
  "orientation": 1,
  "file_format": "JPEG",
  "raw_exif": null
}
```

---

## Database Storage

The metadata is stored in the `photo_metadata` table:

```sql
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
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for GPS queries
CREATE INDEX idx_photo_metadata_gps ON photo_metadata (gps_latitude, gps_longitude);

-- Index for camera queries
CREATE INDEX idx_photo_metadata_camera ON photo_metadata (camera_make, camera_model);

-- Index for timestamp queries
CREATE INDEX idx_photo_metadata_timestamp ON photo_metadata (timestamp_original);
```

---

## Field Mapping

| JSON Field | Database Column | Type |
|------------|-----------------|------|
| document_id | document_id | UUID |
| gps.latitude | gps_latitude | DOUBLE PRECISION |
| gps.longitude | gps_longitude | DOUBLE PRECISION |
| gps.altitude | altitude | DOUBLE PRECISION |
| camera.make | camera_make | VARCHAR(255) |
| camera.model | camera_model | VARCHAR(255) |
| camera.lens | lens_model | VARCHAR(255) |
| timestamp | timestamp_original | TIMESTAMP |
| dimensions.width | width | INTEGER |
| dimensions.height | height | INTEGER |
| orientation | orientation | INTEGER |
| file_format | file_format | VARCHAR(50) |
| raw_exif | raw_exif | JSONB |