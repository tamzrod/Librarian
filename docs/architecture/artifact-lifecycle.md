# Artifact Lifecycle

## Overview

This document describes the canonical lifecycle of artifacts in Librarian, from discovery to archival.

The database is the canonical inventory of known artifacts. The database is no longer a cache of processed files.

---

## Core Principle: Discovery Precedes Understanding

Artifacts are discovered first. Understanding arrives later through independent enrichment workers.

**A file does not need to be understood to exist.**
**A file does not need a parser to become an artifact.**

---

## Architectural Model

### Previous Assumption (Incorrect)

```
Filesystem
    ↓
Parser
    ↓
Database record created
```

### New Architecture (Correct)

```
Filesystem
    ↓
CollectionWatcher
    ↓
Document record created immediately
    ↓
Parser selection
    ↓
Worker enrichment
    ↓
Knowledge accumulation
```

---

## Design Principle

**Artifact identity is immutable.**
**Knowledge is mutable.**

The artifact exists independently of our understanding of it.

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

### 3. ENRICHED

**State:** `CONTENT_EXTRACTED`, `ENTITY_EXTRACTED`, etc.

Independent workers add knowledge to existing artifacts.

**Worker Examples:**

| Worker | Enrichment |
|--------|------------|
| hash | md5, sha1, sha256 |
| exif | camera, GPS, timestamp |
| ocr | extracted text |
| object_detection | detected objects |
| embedding | vector representation |
| entity_extraction | named entities |

**Characteristics:**
- Workers operate using `document_id`
- Workers never create new documents
- Workers only enrich existing documents
- Workers may run independently and asynchronously
- Workers never depend on other workers

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
- ✗ no preview exists
- ✗ no enrichment exists

**The artifact exists because it was observed.**
**Understanding is optional.**

---

## Digital Forensics Inspiration

This model follows evidence processing systems where:

```
Discovery
    precedes
Analysis

Evidence enters inventory immediately.
Analysis continues over time.
```

---

## State Transitions

```
DISCOVERED
    ↓ METADATA_INDEXED
METADATA_INDEXED
    ↓ CONTENT_EXTRACTED
CONTENT_EXTRACTED
    ↓ ENTITY_EXTRACTED
ENTITY_EXTRACTED
    ↓ EMBEDDED
EMBEDDED
    ↓ COMPLETE
COMPLETE
    ↓ (archived)
ARCHIVED
```

**Note:** Any state may transition to FAILED for retry, but artifact identity is never lost.

---

## Failure Handling

**Parser failure:** Artifact creation proceeds with `artifact_type: unknown`

**Worker failure:** Artifact remains in current state; retry is scheduled

**CollectionWatcher failure:** System alerts; discovery resumes on recovery

**Database failure:** System degraded; discovery buffers locally
