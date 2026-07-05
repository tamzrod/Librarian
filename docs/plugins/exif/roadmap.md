# EXIF Plugin Roadmap

**Plugin:** EXIF Metadata Extraction  
**Status:** ✅ Implemented (Phase 1)

---

## Overview

This document outlines the roadmap for the EXIF plugin, including completed features and planned improvements.

---

## Completed Features

### Phase 1: Core EXIF (✅ Done)

| Feature | Status | Notes |
|---------|--------|-------|
| JPEG EXIF extraction | ✅ | Full support |
| HEIC EXIF extraction | ✅ | Modern devices |
| PNG limited support | ✅ | Basic metadata |
| TIFF support | ✅ | Camera/scanner files |
| GPS coordinate extraction | ✅ | Decimal conversion |
| Camera make/model | ✅ | Device identification |
| Lens information | ✅ | DSLR support |
| Timestamp parsing | ✅ | ISO 8601 format |
| Orientation handling | ✅ | 1-8 flags |
| Database persistence | ✅ | photo_metadata table |
| API exposure | ✅ | /timeline/photo endpoint |
| Frontend display | ✅ | Explorer integration |

---

## Planned Features

### Phase 2: Enhanced Metadata

| Feature | Priority | Complexity | Status |
|---------|----------|------------|--------|
| WebP EXIF support | Medium | Low | 📋 Planned |
| RAW file support (CR2, NEF, ARW) | Low | High | 📋 Planned |
| Enhanced GPS handling | Medium | Medium | 📋 Planned |
| Multi-image support (TIFF stacks) | Low | Medium | 📋 Planned |

### Phase 3: Integration

| Feature | Priority | Complexity | Status |
|---------|----------|------------|--------|
| Reverse geocoding | High | High | 📋 Planned |
| Map aggregation layer | High | High | 📋 Planned |
| GPS track support | Medium | Medium | 📋 Planned |
| Location clustering | Medium | Medium | 📋 Planned |

### Phase 4: Performance

| Feature | Priority | Complexity | Status |
|---------|----------|------------|--------|
| Batch processing | Medium | Medium | 📋 Planned |
| Parallel extraction | Medium | Medium | 📋 Planned |
| Selective tag reading | Low | Low | 📋 Planned |
| Caching layer | Low | Medium | 📋 Planned |

---

## Enhancement Details

### WebP EXIF Support

WebP is a modern image format with limited EXIF support. The plugin currently reads basic metadata but could be enhanced:

```python
# Planned enhancement
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp', '.heic', '.heif'}
```

**Challenge:** WebP EXIF is stored differently than JPEG EXIF.

### RAW File Support

Support for camera RAW formats:
- Canon: .cr2, .cr3
- Nikon: .nef
- Sony: .arw
- Fuji: .raf
- Adobe: .dng

**Challenge:** Requires additional libraries (libraw, dcraw) or cloud services.

### Reverse Geocoding

Convert GPS coordinates to human-readable addresses:

```
Input: 14.635189, 121.092548
Output: "123 Main Street, Quezon City, Metro Manila, Philippines"
```

**Challenge:** Requires external API (Google Maps, OpenStreetMap) or local database.

### Map Aggregation Layer

Unified location API that combines:
- GPS coordinates from EXIF
- Semantic locations from location extractor
- User-defined locations

**Challenge:** Schema integration and deduplication.

---

## Technical Debt

| Item | Description | Priority |
|------|-------------|----------|
| Backfill strategy | Update existing documents with mime_type | Medium |
| Error recovery | Better retry logic for transient failures | Medium |
| Logging | Structured logging for extraction events | Low |
| Metrics | Telemetry for extraction performance | Low |

---

## Dependencies

### Current Dependencies

| Library | Purpose | Status |
|---------|---------|--------|
| Pillow | Image processing | ✅ Required |
| psycopg2 | Database | ✅ Required |

### Future Dependencies

| Library | Purpose | Status |
|---------|---------|--------|
| libraw/dcraw | RAW file support | 📋 Optional |
| geopy | Reverse geocoding | 📋 Optional |
| exifread | Alternative EXIF reader | 📋 Optional |

---

## Testing Roadmap

| Test Type | Coverage | Status |
|-----------|----------|--------|
| Unit tests | Core extraction | ✅ 22 tests passing |
| Integration tests | Database persistence | ✅ |
| E2E tests | Full pipeline | ✅ |
| Performance tests | Large collections | 📋 Planned |
| Format tests | All supported formats | 📋 Planned |

---

## Migration Notes

### v1.0 → v2.0

When adding new metadata fields:

1. Update schema in `metadata-schema.md`
2. Add database migration in `storage/migrations/`
3. Update parser to extract new fields
4. Update API routes to expose new fields
5. Add tests for new fields
6. Update this roadmap

---

## References

- [Operation EXIF](../../refactor/operation-exif/) - Original audit
- [Plugin Architecture](../README.md) - System architecture
- [Metadata Schema](./metadata-schema.md) - Current schema