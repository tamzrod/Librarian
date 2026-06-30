# Evidence Timeline API v1.0

**Version:** 1.0  
**Status:** Active  
**Phase:** 1B (REST API Exposure)

---

## Overview

The Evidence Timeline API provides read-only access to photo metadata extracted from images. This API is part of Phase 1B, which exposes the metadata collected in Phase 1A through versioned REST endpoints.

**Key Principles:**
- Read-only access to timeline data
- No direct PostgreSQL access from consumers
- All data obtained through REST APIs only
- Versioned API surface for stability

---

## Base URL

```
/api/v1/timeline
```

---

## Endpoints

### GET /api/v1/timeline/stats

Get statistics for the Evidence Timeline.

**Response:**
```json
{
  "photos_total": 127,
  "gps_tagged": 98,
  "unique_cameras": 4,
  "first_photo_timestamp": "2025-01-15T09:42:18Z",
  "last_photo_timestamp": "2026-06-30T14:32:10Z"
}
```

**Fields:**
| Field | Type | Description |
|-------|------|-------------|
| photos_total | integer | Total number of photos with metadata |
| gps_tagged | integer | Photos with GPS coordinates |
| unique_cameras | integer | Distinct camera make/model combinations |
| first_photo_timestamp | string | ISO 8601 timestamp of earliest photo |
| last_photo_timestamp | string | ISO 8601 timestamp of latest photo |

---

### GET /api/v1/timeline/photos

List photos with optional filters and pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| camera | string | null | Filter by camera (matches make or model) |
| gps_only | boolean | false | Only return photos with GPS coordinates |
| start_date | string | null | Filter photos after this date (ISO 8601) |
| end_date | string | null | Filter photos before this date (ISO 8601) |
| limit | integer | 50 | Maximum results (1-100) |
| offset | integer | 0 | Pagination offset |

**Example Request:**
```
GET /api/v1/timeline/photos?camera=BRP-NX1&gps_only=true&limit=20
```

**Response:**
```json
{
  "data": [
    {
      "document_id": 1,
      "filename": "IMG_20260101_122510.jpg",
      "timestamp": "2026-01-01T12:25:10Z",
      "camera_make": "HONOR",
      "camera_model": "BRP-NX1",
      "gps_latitude": 14.635189,
      "gps_longitude": 121.092548
    }
  ],
  "pagination": {
    "total": 98,
    "limit": 20,
    "offset": 0,
    "returned": 1
  },
  "filters": {
    "camera": "BRP-NX1",
    "gps_only": true,
    "start_date": null,
    "end_date": null
  }
}
```

---

### GET /api/v1/timeline/map

Get GPS markers for map display.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 1000 | Maximum markers (1-5000) |
| offset | integer | 0 | Pagination offset |

**Response:**
```json
{
  "markers": [
    {
      "document_id": 1,
      "latitude": 14.635189,
      "longitude": 121.092548,
      "timestamp": "2026-01-01T12:25:10Z",
      "camera": "HONOR BRP-NX1",
      "filename": "IMG_20260101_122510.jpg"
    }
  ],
  "count": 1
}
```

**Note:** Only photos with valid GPS coordinates are returned.

---

### GET /api/v1/timeline/photo/{document_id}

Get full metadata for a single photo.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| document_id | integer | Document ID from the database |

**Response:**
```json
{
  "document_id": 1,
  "filename": "IMG_20260101_122510.jpg",
  "timestamp": "2026-01-01T12:25:10Z",
  "timestamp_digitized": "2026-01-01T12:25:15Z",
  "gps_latitude": 14.635189,
  "gps_longitude": 121.092548,
  "gps_altitude": -57.2,
  "camera_make": "HONOR",
  "camera_model": "BRP-NX1",
  "lens_model": null,
  "width": 3000,
  "height": 4000,
  "orientation": 1,
  "file_format": "JPEG",
  "extracted_at": "2026-06-30T14:32:10Z"
}
```

**Error Responses:**
| Status | Description |
|--------|-------------|
| 404 | Photo metadata not found |

---

## Response Schemas

### PhotoSummary
```typescript
interface PhotoSummary {
  document_id: number
  filename: string
  timestamp: string | null    // ISO 8601
  camera_make: string | null
  camera_model: string | null
  gps_latitude: number | null
  gps_longitude: number | null
}
```

### PhotoMapMarker
```typescript
interface PhotoMapMarker {
  document_id: number
  latitude: number              // Always present
  longitude: number             // Always present
  timestamp: string | null     // ISO 8601
  camera: string | null         // Combined make + model
  filename: string
}
```

### PhotoDetail
```typescript
interface PhotoDetail {
  document_id: number
  filename: string
  timestamp: string | null
  timestamp_digitized: string | null
  gps_latitude: number | null
  gps_longitude: number | null
  gps_altitude: number | null
  camera_make: string | null
  camera_model: string | null
  lens_model: string | null
  width: number
  height: number
  orientation: number | null
  file_format: string
  extracted_at: string
}
```

### TimelineStats
```typescript
interface TimelineStats {
  photos_total: number
  gps_tagged: number
  unique_cameras: number
  first_photo_timestamp: string | null
  last_photo_timestamp: string | null
}
```

---

## Filtering Behavior

### Camera Filter
- Partial match on camera_make or camera_model
- Case-insensitive
- Example: `camera=honor` matches "HONOR BRP-NX1"

### GPS Filter
- `gps_only=true` returns only photos with both latitude and longitude
- `gps_only=false` (default) returns all photos

### Date Filters
- `start_date`: Photos taken on or after this date
- `end_date`: Photos taken on or before this date
- Format: ISO 8601 (YYYY-MM-DD or full timestamp)

### Pagination
- Results are sorted by timestamp descending (most recent first)
- Offset-based pagination
- Default limit: 50, max: 100

---

## Error Handling

All errors follow the standard API error format:

```json
{
  "error": "Error message",
  "detail": "Additional details"
}
```

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Non-Goals (Not Implemented)

This API phase intentionally excludes:
- Reverse geocoding
- Route calculations
- Map rendering
- Dashboard pages
- Playback
- Clustering
- Object recognition
- Facial recognition
- OCR
- AI generated tags

These features may be added in future phases.

---

## Example Usage

### Dashboard: Load map markers
```javascript
const response = await fetch('/api/v1/timeline/map');
const { markers } = await response.json();
// markers ready for map library (Leaflet, Google Maps, etc.)
```

### Dashboard: Filter by camera
```javascript
const response = await fetch('/api/v1/timeline/photos?camera=iPhone&gps_only=true');
const { data, pagination } = await response.json();
```

### Dashboard: Timeline view
```javascript
const response = await fetch('/api/v1/timeline/photos?start_date=2026-01-01&end_date=2026-06-30');
const { data } = await response.json();
// data sorted by timestamp descending
```

---

## Versioning

This is v1.0 of the Evidence Timeline API.

Breaking changes will result in a version bump. Non-breaking additions (new fields, new endpoints) do not require a version change.

See [API Contract README](./README.md) for overall versioning strategy.
