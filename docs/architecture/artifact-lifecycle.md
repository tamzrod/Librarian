# Artifact Lifecycle

**Version**: 2.0  
**Last Updated**: 2026-07-06

---

## Overview

This document describes the canonical lifecycle of artifacts in Librarian, from discovery to archival.

The database is the canonical inventory of known artifacts. The database is no longer a cache of processed files.

---

## Core Principle: Authority vs Cost

**Artifact is authoritative.**

Everything attached to artifact is optional metadata, cache, or enrichment.

**Generation cost changes recovery strategy.**

**Generation cost does NOT change authority level.**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AUTHORITY MODEL                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  AUTHORITATIVE:                                                    │
│  • Original artifact file                                           │
│  • Document row in database                                        │
│  • SHA256 hash                                                     │
│                                                                     │
│  OPTIONAL (ALL same authority level - NONE):                       │
│  • embeddings (expensive to regenerate)                           │
│  • OCR (expensive to regenerate)                                   │
│  • object detection (expensive to regenerate)                        │
│  • transcription (expensive to regenerate)                          │
│  • thumbnails (cheap to regenerate)                                │
│  • previews (cheap to regenerate)                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## What IS Corruption

Corruption only exists when:

- Original evidence missing (artifact file deleted)
- Document row missing (database record deleted)
- SHA256 mismatch (artifact modified)
- Artifact identity mismatch (path/content mismatch)

**Missing optional data (embedding, OCR, thumbnail) is ALWAYS a cache miss, NEVER corruption.**

---

## Design Principle

**Artifact identity is immutable.**
**Knowledge is mutable.**

The artifact exists independently of our understanding of it.

---

## Discovery Precedes Understanding

Artifacts are discovered first. Understanding arrives later through independent enrichment workers.

**A file does not need to be understood to exist.**
**A file does not need a parser to become an artifact.**

---

## Artifact Identity

An artifact is identified by its `document_id`. Once assigned, this identifier never changes.

An artifact's identity is determined by its physical existence at a path. The system records the observation of an artifact.

---

## Lifecycle Stages

### 1. DISCOVERED

**State:** `DISCOVERED`

CollectionWatcher detects a new file. A document record is immediately created.

**Example record:**

```json
{
  "document_id": 42,
  "path": "/library/photos/IMG_001.jpg",
  "extension": ".jpg",
  "artifact_type": "unknown",
  "status": "DISCOVERED",
  "exists_on_disk": true,
  "discovered_at": "2024-01-15T10:30:00Z"
}
```

**Characteristics:**
- No parser required
- No enrichment performed
- Document exists in database immediately upon filesystem detection

### 2. CLASSIFIED

**State:** `METADATA_INDEXED`

Parser registry identifies the artifact type based on file extension.

**Type Examples:**

| Extension | Artifact Type |
|-----------|---------------|
| .jpg, .png, .gif | image |
| .pdf, .doc | document |
| .mp4, .mov | video |
| .zip, .tar | archive |
| .xyz | unknown |

**Characteristics:**
- Classification updates metadata only
- Document identity never changes
- Parser selection is based on extension mapping

### 3. ENRICHED (Optional)

**State:** `CONTENT_EXTRACTED`, `ENTITY_EXTRACTED`, etc.

Workers add knowledge to artifacts asynchronously. All enrichment is optional.

**Worker Examples:**

| Worker | Enrichment | Authority | Cost |
|--------|------------|-----------|------|
| hash | md5, sha1, sha256 | Optional | Low |
| exif | camera, GPS, timestamp | Optional | Low |
| ocr | extracted text | Optional | High |
| object_detection | detected objects | Optional | High |
| embedding | vector representation | Optional | High |
| entity_extraction | named entities | Optional | Medium |
| thumbnail | preview image | Optional | Low |

**Critical Distinction:**

```
┌─────────────────────────────────────────────────────────────────┐
│ ALL enrichment is OPTIONAL                                       │
│ Missing enrichment = cache miss (NOT corruption)                 │
│ Recovery strategy depends on cost, not authority                 │
└─────────────────────────────────────────────────────────────────┘
```

**Characteristics:**
- Workers operate using `document_id`
- Workers never create new documents
- Workers only enrich existing documents
- Workers may run independently and asynchronously
- Workers never depend on other workers
- Missing enrichment is NEVER corruption

### 4. ARCHIVED

**State:** `ARCHIVED`

Artifacts removed from disk are marked as archived.

**Example fields:**

```json
{
  "exists_on_disk": false,
  "deleted_at": "2024-01-20T14:00:00Z"
}
```

**Characteristics:**
- Records are preserved for auditability
- System avoids hard deletion whenever possible
- Archived artifacts remain queryable
- Historical relationships preserved

---

## Unknown Artifacts

Unknown artifacts are first-class citizens.

**Examples:**
- encrypted containers
- proprietary files
- unsupported formats
- damaged files

**Unknown artifacts still receive:**
- `document_id`
- hashes
- timestamps
- path tracking
- timeline presence
- relationship participation

**Lack of understanding does not imply lack of value.**

---

## Component Responsibilities

### CollectionWatcher

CollectionWatcher synchronizes reality with inventory.

**Responsibilities:**
- detect new files
- detect deleted files
- detect moved files
- update inventory state

**CollectionWatcher does NOT:**
- perform enrichment
- run parsers
- create workers

### Parser Registry

Parsers classify and normalize.

**Parsers are responsible for:**
- extension-to-type mapping
- basic metadata extraction
- content normalization

**Parsers do NOT:**
- determine existence
- create document records
- perform AI enrichment

**Critical rule: Parser failure must never prevent artifact creation.**

### Workers

Workers enrich artifacts.

**Worker characteristics:**
- operate using `document_id`
- never create documents
- may run independently
- may run asynchronously
- never depend on other workers
- produce OPTIONAL enrichment (never authoritative)

### Explorer

Explorer uses the documents table as its source of truth.

**Explorer does NOT:**
- read the filesystem directly
- perform discovery
- trigger enrichment

**Explorer benefits:**
- instant navigation
- cached hierarchy
- stable identifiers
- historical tracking
- deleted file visibility

---

## Success Criteria

Dropping a file into the library immediately produces:

- ✓ document record
- ✓ stable `document_id`
- ✓ explorer visibility

**Even if:**
- ✗ no parser exists
- ✗ no worker exists
- ✗ no enrichment exists

**The artifact exists because it was observed.**
**Understanding is optional.**
**Missing enrichment is always a cache miss, never corruption.**

---

## Digital Forensics Inspiration

This model follows evidence processing systems where:

```
Discovery
    precedes
Analysis

Evidence enters inventory immediately.
Analysis continues over time.
Optional enrichment does not affect authority.
```

---

## State Transitions

```
DISCOVERED
    ↓ METADATA_INDEXED
METADATA_INDEXED
    ↓ (optional enrichment)
[ENRICHED] - optional, may be expensive or cheap
    ↓
COMPLETE
    ↓ (archived)
ARCHIVED
```

**Note:** Any state may transition to FAILED for retry, but artifact identity is never lost.

---

## Thumbnail Specific Contract

Thumbnails are **optional enrichment** and follow this contract:

```
UI requests thumbnail
    ↓
Thumbnail exists?
    YES → return thumbnail
    NO  → queue generate_thumbnail job
           return placeholder image
```

**Worker Contract:**
```
generate_thumbnail job flow:
    1. generate thumbnail
    2. save thumbnail
    3. verify thumbnail exists
    4. mark job COMPLETE

A thumbnail job must NEVER be marked COMPLETE unless the file exists.
```

**Database Contract:**
`documents.thumbnail_path` is advisory metadata only.
- Does NOT guarantee file existence
- Does NOT guarantee cache validity
- Filesystem is the source of truth for thumbnail existence

**Success Criteria:**
> Deleting every thumbnail file in the system should NOT be considered corruption.
> The only consequence should be placeholder images appearing temporarily
> and thumbnails regenerating automatically on demand.

---

## Failure Handling

**Parser failure:** Artifact creation proceeds with `artifact_type: unknown`

**Worker failure:** Artifact remains in current state; retry is scheduled

**Missing enrichment:** Cache miss - regenerate on demand (NOT corruption)

**CollectionWatcher failure:** System alerts; discovery resumes on recovery

**Database failure:** System degraded; discovery buffers locally

---

## References

- [Derived Artifact Contract](./derived-artifact-contract.md) - Authority vs cost principles
- [Storage Lifecycle Matrix](./storage-lifecycle-matrix.md) - Artifact classification
- [Derived Artifact Recovery](../operations/derived-artifact-recovery.md) - Recovery for expensive optional data
- [Plugin Development Guide](../plugins/plugin-development-guide.md)
- [Architecture Glossary](./glossary.md) - Semantic definitions and terminology
