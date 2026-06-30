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

### Examples

```
📁 photos
    📷 IMG_001.jpg
    📷 IMG_002.jpg

📁 reports
    📄 report.pdf
```

This behavior intentionally mirrors desktop file managers.

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

**Unknown:** preview unavailable

The selected view mode affects only the center pane.

Folder hierarchy remains unchanged.

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

**OCR:** extracted text

**Entities:** detected entities

**Relationships:** linked artifacts

**Embeddings:** embedding availability

The metadata pane is enrichment-driven.

New enrichments add sections without requiring UI redesign.

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

Artifact Selected
    ↓
Metadata Pane displays artifact knowledge

View Mode Selected
    ↓
Center Pane changes presentation only
```

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
