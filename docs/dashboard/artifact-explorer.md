# Artifact Explorer

## Philosophy

Artifact Explorer is the primary workspace of Librarian.

The Explorer is intentionally modeled after familiar desktop file managers such as:

- Windows Explorer
- Finder
- VSCode Explorer
- Obsidian Vault

The goal is immediate usability with minimal training.

Users should feel they are browsing evidence rather than operating a database.

---

## Core Principle: Discovery Precedes Understanding

**A file does not need to be understood to exist.**
**A file does not need a parser to become an artifact.**

When a file is dropped into the library, it immediately appears in Explorer with:
- A stable `document_id`
- Folder hierarchy visibility
- Existence confirmation

**Understanding is optional. The artifact exists because it was observed.**

---

## Architecture

### Source of Truth

Explorer uses the **documents table as its source of truth**. Explorer does NOT read the filesystem directly.

### Data Flow

```
Filesystem
    ↓ CollectionWatcher detects
Documents Table (canonical inventory)
    ↓ Explorer queries
API Response
    ↓ Frontend renders
Explorer UI
```

### Benefits

- **Instant navigation:** No filesystem scanning on each view
- **Cached hierarchy:** Folder structure pre-computed from document paths
- **Stable identifiers:** `document_id` never changes
- **Historical tracking:** Deleted files remain visible
- **Deleted file visibility:** Archive state preserved for audit

---

## Layout

Artifact Explorer uses a three-pane layout.

```
┌──────────┬──────────────────────────┬──────────────┐
│ Explorer │ View                    │ Metadata     │
└──────────┴──────────────────────────┴──────────────┘
```

---

## Left Pane - Explorer

### Purpose

Navigation.

### Responsibilities

- folder hierarchy
- expand/collapse folders
- artifact selection

Artifacts are displayed inside folders.

There is no separate artifact list.

Collapsed folders hide their contents.

### Data Source

The left pane receives its data from:

```
GET /api/v1/explorer/tree
```

This returns the root folder node. Child folders are loaded on-demand via:

```
GET /api/v1/explorer/folders/{folder_path}
```

### Examples

```
📁 library
    📁 photos
        📷 IMG_001.jpg
        📷 IMG_002.jpg

    📁 reports
        📄 report.pdf
```

This behavior intentionally mirrors desktop file managers.

### Unknown Artifacts

Artifacts with unsupported file types still appear in Explorer:

```
📁 unknown_files
    📄 encrypted.zip (no preview available)
    📄 proprietary.xyz (no enrichment)
```

Unknown artifacts are first-class citizens. They receive `document_id`, hashes, and tracking like any other artifact.

---

## Center Pane - View

### Purpose

Display artifacts using different perspectives.

This pane changes according to selected view mode.

### Supported Modes

1. **Grid View** - Thumbnail-focused layout.

2. **List View** - Dense information layout similar to file managers.

3. **Preview View** - Large artifact preview.

### Examples

**Images:** image preview

**Text:** text preview

**PDF:** embedded viewer

**Unknown:** preview unavailable (enrichment may add preview later)

The selected view mode affects only the center pane.

Folder hierarchy remains unchanged.

### Content Loading

Folder contents are loaded via:

```
GET /api/v1/explorer/folders/{folder_path}
```

This returns:
- `folders[]` - subfolders
- `documents[]` - artifacts in this folder

---

## Right Pane - Metadata

### Purpose

Display everything known about the selected artifact.

The metadata pane changes according to selected artifact.

### Examples

**Core Metadata:**
- filename
- path
- size
- extension
- hash
- ingestion timestamp

**Photo Metadata:**
- camera
- GPS
- EXIF timestamp
- dimensions

**OCR:** extracted text (if available)

**Entities:** detected entities (if available)

**Relationships:** linked artifacts (if available)

**Embeddings:** embedding availability (if available)

The metadata pane is enrichment-driven.

New enrichments add sections without requiring UI redesign.

### Document Details API

Metadata is loaded via:

```
GET /api/v1/explorer/documents/{document_id}
```

---

## Design Principle

```
Explorer controls navigation.
View controls perspective.
Metadata controls context.
```

These concerns remain independent.

Changing one must not affect the others.

---

## Mental Model

```
Folder Selected
    ↓
Center Pane displays folder contents
    ↓ API call to /folders/{path}

Artifact Selected
    ↓
Metadata Pane displays artifact knowledge
    ↓ API call to /documents/{id}

View Mode Selected
    ↓
Center Pane changes presentation only
```

---

## Discovery vs. Enrichment

### Discovery (Immediate)

When a file is added to the library:

1. CollectionWatcher detects the new file
2. Document record created immediately
3. Explorer updates to show the artifact
4. User can navigate to and select the artifact

**Time to visibility: milliseconds**

### Enrichment (Deferred)

Enrichment happens asynchronously via workers:

1. Hash worker computes file hashes
2. EXIF worker extracts photo metadata
3. OCR worker extracts text
4. Entity extraction identifies named entities
5. Embedding worker generates vectors

**Time to enrichment: seconds to minutes**

### Explorer Behavior

Explorer shows artifacts immediately upon discovery, regardless of enrichment state.

Artifacts without enrichment display:

- ✓ filename
- ✓ path
- ✓ extension
- ✓ file size
- ✓ `document_id`

Missing (expected later):
- metadata (enrichment pending)
- preview (enrichment pending)
- entities (enrichment pending)

---

## Long-Term Goal

The interface should feel closer to:

- VSCode
- Obsidian
- Finder

and less like:

- database administration tools
- server dashboards
- monitoring systems

---

## Success Criteria

A user should understand the Explorer without documentation.

Users familiar with desktop operating systems should immediately understand:

- navigation
- selection
- preview
- metadata

without learning Librarian-specific concepts.

**Instant visibility test:** Drop a file into the library and verify:
- ✓ It appears in Explorer within seconds
- ✓ It receives a `document_id`
- ✓ It can be selected and navigated to
- ✓ Even if no parser or worker exists for its type
