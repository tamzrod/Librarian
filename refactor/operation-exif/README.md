# Operation EXIF - Metadata Architecture Audit

**Date:** 2026-07-01
**Status:** Audit Complete
**Priority:** Architectural

## Executive Summary

This audit examines the second architectural layer exposed by the EXIF investigation: metadata ownership, persistence, lifecycle, and presentation. The original refactor stabilized ingestion, worker runtime, backend contracts, startup, migrations, and soft delete. This audit identifies critical gaps in how metadata flows through the system.

## Classification Legend

| Status | Description |
|--------|-------------|
| **Resolved** | Architecture is sound, implementation exists |
| **Partial** | Architecture exists but incomplete |
| **Open** | Missing architecture or implementation |
| **Architectural Violation** | Architecture exists but is violated |
| **Technical Debt** | Known issues, workarounds in place |

## Severity Legend

| Severity | Description |
|----------|-------------|
| **Critical** | Data loss, broken features |
| **High** | Significant feature gaps |
| **Medium** | Incomplete functionality |
| **Low** | Minor issues, nice-to-have |

---

## Findings Summary

| ID | Finding | Severity | Classification |
|----|---------|----------|----------------|
| E1 | mime_type Not Persisted | Critical | Architectural Violation |
| E2 | structured_data Dropped in Pipeline | Critical | Open |
| E3 | GPS Not Copied to locations Table | High | Open |
| E4 | Inconsistent Metadata Ownership | High | Architectural Violation |
| E5 | Thumbnail Persistence Missing | Medium | Open |
| E6 | OCR Output Not Persisted | Medium | Open |
| E7 | Embedding Storage Incomplete | Medium | Open |
| E8 | Location/EXIF Disconnect | High | Open |
| E9 | API/UI Metadata Gaps | Medium | Partial |
| E10 | Discovery vs Enrichment State Confusion | Low | Technical Debt |

---

## Architecture Overview

### Metadata Ownership Layers

```
┌─────────────────────────────────────────────────────────────────┐
│ DISCOVERY LAYER                                                  │
│ - path, extension, file_size, modified_time                     │
│ - artifact_type (derived from extension)                         │
│ - mime_type (NOT OWNED - critical gap)                          │
│ Owned by: CollectionWatcher, discover_artifact()                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PARSER LAYER                                                     │
│ - text content                                                   │
│ - structured_data (mime_type, dimensions, EXIF)                  │
│ - CHARACTER_COUNT, parser name                                   │
│ Owned by: Parsers (image_parser, csv_parser, etc.)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ INGESTION LAYER                                                  │
│ - Drops structured_data ← CRITICAL                               │
│ - Extracts: path, extension, file_size, character_count           │
│ - MISSING: mime_type, structured_data contents                  │
│ Owned by: CollectionWatcher._process_file()                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ WORKER LAYER                                                     │
│ - extract_photo_metadata: photo_metadata table                   │
│ - extract_text: document_content table                          │
│ - extract_locations: locations table                             │
│ - generate_embeddings: document_embeddings table                 │
│ Owned by: Workers (photo_metadata_extractor, etc.)              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ API LAYER                                                        │
│ - Reads from all tables                                          │
│ - Combines for responses                                         │
│ - GPS from photo_metadata (not locations)                       │
│ Owned by: API routes (explorer.py, timeline.py)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER                                               │
│ - Dashboard                                                      │
│ - Timeline                                                       │
│ - Map                                                            │
│ Owned by: React dashboard                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Dependency Graph

```
E1 ─────────┬───────────────────────────────────────────────────────► E4
mime_type   │                                                       Metadata
persistence │                                                       Ownership
            │
            ├───────────────────────────────────────────────────────► E2
            │                                                       structured_data
            │                                                       Dropped
            │
            └───────────────────────────────────────────────────────► E3
                                                                        GPS to
                                                                        locations
                                                                         │
                                                                         ▼
E8 ─────────────────────────────────────────────────────────────────► E9
Location/                                                                API/UI
EXIF                                                                    Gaps
Disconnect                                                              
                                                                         │
                                                                         ▼
E7 ◄───────────────────────────────────────────────────────────────── E6
Embeddings ◄───────────────────────────────────────────────────────── OCR
             │                                                         │
             │                                                         ▼
             └───────────────────────────────────────────────────────► E5
             Thumbnail                                                  │
             Persistence                                                ▼
                                                                          E10
                                                                          State
                                                                          Confusion
```

---

## Implementation Waves

### Wave 1 - Critical Fixes (High Priority)

| Task | Description | Parallelizable |
|------|-------------|----------------|
| E1 | Fix mime_type persistence | Yes |
| E2 | Persist structured_data or extract to photo_metadata | No - depends on E1 |
| E3 | Copy GPS from photo_metadata to locations | No - depends on E2 |

### Wave 2 - Architectural Fixes (Medium Priority)

| Task | Description | Parallelizable |
|------|-------------|----------------|
| E4 | Consolidate metadata ownership | Yes |
| E8 | Connect LocationExtractor to photo_metadata | No - depends on E3 |
| E7 | Complete embedding storage | Yes |

### Wave 3 - Feature Completions (Lower Priority)

| Task | Description | Parallelizable |
|------|-------------|----------------|
| E5 | Implement thumbnail persistence | Yes |
| E6 | Implement OCR persistence | Yes |
| E9 | Fill API/UI gaps | No - depends on E3, E7 |
| E10 | Clarify state transitions | Yes |

---

## Quick Reference

### What Works ✓

1. **Discovery metadata**: path, extension, file_size, modified_time correctly persisted
2. **Parser infrastructure**: All parsers produce structured_data with metadata
3. **Worker infrastructure**: Job queue, worker runtime, status transitions
4. **PhotoMetadataExtractor**: Correctly extracts EXIF, GPS, camera data to photo_metadata
5. **Timeline API**: Correctly queries photo_metadata for map and timeline

### What's Broken ✗

1. **mime_type**: Schema exists, never populated
2. **structured_data**: Produced by parsers, dropped at ingestion
3. **GPS locations**: Extracted to photo_metadata, never copied to locations table
4. **Thumbnails**: Job queued, not implemented
5. **OCR**: Job queued, output not persisted
6. **Embeddings**: Table exists, storage incomplete

---

## Status Tracking

Update this section as work progresses:

| Task | Status | Started | Completed | Notes |
|------|--------|---------|-----------|-------|
| E1 | Planned | - | - | mime_type persistence |
| E2 | Planned | - | - | structured_data handling |
| E3 | Planned | - | - | GPS to locations |
| E4 | Planned | - | - | Metadata ownership |
| E5 | Planned | - | - | Thumbnails |
| E6 | Planned | - | - | OCR persistence |
| E7 | Planned | - | - | Embeddings |
| E8 | Planned | - | - | Location/EXIF |
| E9 | Planned | - | - | API/UI gaps |
| E10 | Planned | - | - | State confusion |

---

## Affected Files Reference

### Core Ingestion

| File | Role |
|------|------|
| `ingestion/collection_watcher.py` | Metadata drops here |
| `ingestion/scanner.py` | Discovery metadata source |
| `ingestion/indexer.py` | Indexing logic |

### Storage

| File | Role |
|------|------|
| `storage/postgres_backend.py` | Document persistence |
| `storage/migrations/*.sql` | Schema definitions |

### Workers

| File | Role |
|------|------|
| `workers/photo_metadata_extractor.py` | EXIF extraction |
| `workers/content_extractor.py` | Text extraction |
| `workers/location_extractor.py` | Location extraction |
| `workers/entity_extractor.py` | Entity extraction |

### API

| File | Role |
|------|------|
| `api/routes/explorer.py` | Document queries |
| `api/routes/timeline.py` | Photo metadata queries |
| `api/routes/operations.py` | System stats |

### Parsers

| File | Role |
|------|------|
| `parsers/image_parser.py` | Image metadata extraction |
| `parsers/csv_parser.py` | Structured data parsing |
| `parsers/json_parser.py` | JSON parsing |

---

## Next Steps

1. Review each E1-E10 document in detail
2. Prioritize based on business impact
3. Sequence implementation based on dependencies
4. Add test coverage for each fix
5. Update status tracking as work progresses

---

**Document Version:** 1.0
**Audit Completed:** 2026-07-01
**Next Review:** After Wave 1 implementation
