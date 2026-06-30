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

## Dashboard Sections

### Investigation Workspace

- Artifact Explorer
- Evidence Timeline
- Map View
- Entity View
- Relationship View

### Operational Workspace

- System Overview
- Queue Monitor
- Activity Feed
- Extraction Viewer
- Worker Status

---

## Investigation Views

### Artifact Explorer

| Aspect | Description |
|--------|-------------|
| **Primary Organization** | file and folder hierarchy |
| **Purpose** | Answer: "What files exist?" |
| **Features** | folder tree, list view, grid view, preview pane, metadata pane, enrichment status |

> Artifact Explorer becomes the primary user workspace.

### Evidence Timeline

| Aspect | Description |
|--------|-------------|
| **Primary Organization** | time |
| **Purpose** | Answer: "What happened and when?" |
| **Sources** | EXIF timestamps, file timestamps, email timestamps, event timestamps, log timestamps |

### Map View

| Aspect | Description |
|--------|-------------|
| **Primary Organization** | location |
| **Purpose** | Answer: "Where did things happen?" |
| **Sources** | GPS EXIF, extracted locations, future geospatial metadata |

### Entity View

| Aspect | Description |
|--------|-------------|
| **Primary Organization** | entity |
| **Purpose** | Answer: "What references this thing?" |

### Relationship View

| Aspect | Description |
|--------|-------------|
| **Primary Organization** | graph relationships |
| **Purpose** | Answer: "How are artifacts connected?" |

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
- Notion
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
