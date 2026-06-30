# Dashboard Architecture

## Purpose

Document the long-term dashboard philosophy and information architecture for Librarian.

This document defines views and user workflows. It does NOT define implementation details.

---

## Core Principle

Librarian stores artifacts once and exposes them through multiple views.

### Examples

| View | Primary Organization |
|------|---------------------|
| Artifact Explorer | file |
| Evidence Timeline | time |
| Map View | location |
| Entity View | meaning |
| Relationship View | connections |

> **Note:** These are not separate systems. They are projections of the same underlying artifact database.

---

## Core Principle: Discovery Precedes Understanding

**A file does not need to be understood to exist.**
**A file does not need a parser to become an artifact.**

### Architectural Model

**Previous (Incorrect):**
```
Filesystem → Parser → Database record created
```

**New (Correct):**
```
Filesystem → CollectionWatcher → Document record created immediately → Parser selection → Worker enrichment → Knowledge accumulation
```

### Design Principle

```
Artifact identity is immutable.
Knowledge is mutable.

The artifact exists independently of our understanding of it.
```

---

## Artifact Inventory

The database is the **canonical inventory of known artifacts**. The database is **NOT a cache of processed files**.

### Inventory Properties

- **Immediate:** Artifacts appear in Explorer as soon as they are discovered
- **Stable:** Each artifact receives a permanent `document_id`
- **Queryable:** All artifacts are searchable regardless of enrichment state
- **Historical:** Deleted artifacts remain visible for auditability

### Explorer as Inventory Interface

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

## Workspaces

The dashboard is organized into two workspaces:

### Investigation Workspace

The primary workspace for browsing and analyzing evidence.

- [Artifact Explorer](./artifact-explorer.md) - Primary file browsing interface
- Timeline - Events organized chronologically
- Map - Geographic visualization
- Entities - Named things and references
- Relationships - Connections between artifacts

### Operations Workspace

Administrative views for monitoring and maintenance.

- Overview - System status and metrics
- Queue - Job queue monitoring
- Activity - Recent operations feed
- Extraction - Document enrichment status

---

## Artifact Model

The central object in Librarian is an **artifact**.

### Supported Types

- image
- document
- PDF
- email
- video
- audio
- archive
- sensor log
- phone extraction
- structured data

### Artifact Identifier

Artifacts receive a unique artifact identifier. Current implementation uses `document_id`. Future renaming to `artifact_id` is possible but not required.

### Unknown Artifacts

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

Parsers classify and normalize. Parsers do NOT determine existence.

**Parsers are responsible for:**
- extension-to-type mapping
- basic metadata extraction
- content normalization

**Critical rule: Parser failure must never prevent artifact creation.**

### Workers

Workers enrich artifacts.

**Worker characteristics:**
- operate using `document_id`
- never create documents
- may run independently
- may run asynchronously
- never depend on other workers

### Examples by Type

| Type | Enrichments |
|------|-------------|
| Image | photo metadata, OCR, object detection, face recognition, embeddings, thumbnails |
| PDF | text extraction, OCR, entity extraction |
| Video | frame extraction, OCR, object detection |

---

## Artifact Lifecycle

See [Artifact Lifecycle](../architecture/artifact-lifecycle.md) for complete lifecycle documentation.

### States

| State | Description |
|-------|-------------|
| DISCOVERED | File detected, document record created immediately |
| METADATA_INDEXED | Basic metadata extracted, type classified |
| CONTENT_EXTRACTED | Text content available |
| ENTITY_EXTRACTED | Named entities identified |
| EMBEDDED | Vector representation generated |
| COMPLETE | All enrichments finished |
| ARCHIVED | Removed from disk, record preserved |

### State Transition Rules

```
Any state may transition to FAILED for retry.
Artifact identity is never lost.
```

---

## Dashboard Design Principles

1. One artifact, many views.

2. Views do not own data.

3. Summary metrics consume minimal screen space.

4. Most screen space should display evidence.

5. Operational information must not dominate investigation workflows.

6. Navigation should be task-oriented rather than backend-oriented.

### Good vs. Avoid

| Good | Avoid |
|------|-------|
| Explorer | Tables |
| Timeline | Jobs |
| Map | Queue |
|  | Database concepts |

---

## User Experience Goal

The dashboard should feel closer to:

- VSCode
- Obsidian
- Finder
- modern forensic workspaces

and less like:

- server administration panels
- classic enterprise dashboards
- database administration tools

---

## Success Criteria

A user should be able to answer without understanding Librarian internals:

- What files exist?
- What happened?
- Where did it happen?
- Who was involved?
- How are things connected?

**Instant visibility:** Dropping a file into the library immediately produces:
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
