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

---

## Parser Responsibilities

Parsers are responsible for:

- artifact ingestion
- validation
- normalization
- basic metadata extraction
- document creation

**Parsers must remain lightweight and deterministic. Parsers do NOT perform AI enrichment.**

---

## Worker Responsibilities

Workers enrich artifacts.

### Examples by Type

| Type | Enrichments |
|------|-------------|
| Image | photo metadata, OCR, object detection, face recognition, embeddings, thumbnails |
| PDF | text extraction, OCR, entity extraction |
| Video | frame extraction, OCR, object detection |

### Operational Characteristics

- Workers operate independently
- Workers may fail independently
- Artifacts remain valid even if some enrichments fail

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
