# Derived Artifact Contract

**Version**: 1.0  
**Last Updated**: 2026-07-06

---

## Overview

This document defines the architectural contract for optional metadata and enrichment in Librarian, establishing how generation cost affects recovery strategy without changing authority level.

## Core Principle: Authority vs Cost

**Artifact is authoritative.**

Everything attached to artifact is optional metadata, cache, or enrichment.

**Generation cost changes recovery strategy.**

**Generation cost does NOT change authority level.**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AUTHORITY MODEL                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  AUTHORITATIVE:                                                    │
│  • Original artifact file (the evidence)                           │
│  • Document row in database (identity)                              │
│  • SHA256 hash (integrity)                                         │
│                                                                     │
│  OPTIONAL (expensive or cheap - same authority level):            │
│  • embeddings (expensive cache miss)                               │
│  • OCR (expensive cache miss)                                      │
│  • object detection (expensive cache miss)                          │
│  • transcription (expensive cache miss)                            │
│  • geolocation (expensive cache miss)                              │
│  • thumbnails (cheap cache miss)                                   │
│  • previews (cheap cache miss)                                     │
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

**Missing embedding = expensive cache miss (NOT corruption)**

**Missing OCR = expensive cache miss (NOT corruption)**

**Missing thumbnail = cheap cache miss (NOT corruption)**

---

## Generation Cost Classification

While authority level is the same for all optional data, generation cost affects the recovery strategy:

### Expensive Optional Data

| Artifact Type | Generation Cost | External Dependencies |
|---------------|----------------|----------------------|
| embeddings | High (API calls, model inference) | Yes (API keys) |
| OCR | High (model inference) | Yes (models) |
| object_detection | High (GPU, model) | Yes (GPU, models) |
| transcription | High (API/GPU) | Yes (API/models) |
| geolocation_enrichment | Medium | Yes (API) |

**Recovery Strategy:** Full recovery framework justified because regeneration is expensive.

### Cheap Optional Data

| Artifact Type | Generation Cost | External Dependencies |
|---------------|----------------|----------------------|
| thumbnail | Low (<1s CPU) | None |
| preview | Low (<1s CPU) | None |
| resized_image | Low (<1s CPU) | None |
| filmstrip | Low (<1s CPU) | None |

**Recovery Strategy:** Regenerate on demand. No recovery framework needed.

---

## Contract Diagrams

### Expensive Optional Data Contract

```
┌─────────────────────────────────────────────────────────────────────┐
│              EXPENSIVE OPTIONAL DATA (embeddings, OCR, etc.)        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Authority: OPTIONAL (cache miss, not corruption)                   │
│  Cost: EXPENSIVE to regenerate                                     │
│  Recovery: Full recovery framework justified                         │
│                                                                     │
│  Missing embedding = expensive cache miss                           │
│  Missing OCR = expensive cache miss                                 │
│  Missing object detection = expensive cache miss                    │
│                                                                     │
│  Operations:                                                        │
│  • Detection: Identify missing expensive optional data              │
│  • Recovery: Requeue expensive regeneration jobs                    │
│  • Priority: Higher priority for recovery jobs                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Cheap Optional Data Contract

```
┌─────────────────────────────────────────────────────────────────────┐
│                   CHEAP OPTIONAL DATA (thumbnails)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Authority: OPTIONAL (cache miss, not corruption)                   │
│  Cost: CHEAP to regenerate                                          │
│  Recovery: On-demand regeneration only                              │
│                                                                     │
│  Missing thumbnail = cheap cache miss                              │
│  Missing preview = cheap cache miss                                 │
│                                                                     │
│  Behavior:                                                          │
│  • UI requests data                                                │
│  • Data exists? → return data                                      │
│  • Data missing? → queue job, return placeholder                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Thumbnail Specific Contract

Thumbnails are cheap optional data.

### Thumbnail Behavior

```
UI requests thumbnail
    ↓
Thumbnail exists?
    YES → return thumbnail
    NO  → queue generate_thumbnail job
           return placeholder image
```

### Worker Contract

```
generate_thumbnail job flow:
    1. generate thumbnail
    2. save thumbnail
    3. verify thumbnail exists
    4. mark job COMPLETE

A thumbnail job must NEVER be marked COMPLETE unless the file exists.
```

### Database Contract

`documents.thumbnail_path` is **advisory metadata only**.

It does NOT guarantee:
- File existence
- Cache validity
- Filesystem integrity

**The filesystem is the source of truth for thumbnail existence.**

---

## Success Criteria

### For All Optional Data

> **Missing optional data (embedding, OCR, thumbnail) is always a cache miss, NEVER corruption.**
>
> The system does not guarantee optional data exists.
> The system regenerates optional data when requested.
>
> For expensive optional data: Recovery framework requeues jobs efficiently.
> For cheap optional data: On-demand regeneration suffices.

### Specific to Thumbnails

> **Deleting every thumbnail file in the system should not be considered corruption.**
> 
> The only consequence is temporary placeholder images and automatic regeneration.
> 
> **This is the intended behavior.**

---

## What IS and IS NOT Appropriate

### For Cheap Optional Data (Thumbnails)

| ❌ Do NOT Implement | Reason |
|---------------------|--------|
| Recovery frameworks | Not needed - cache misses are expected |
| Integrity audits | Not needed - data is optional |
| Repair registries | Not needed - regenerate on demand |
| Startup scans | Not needed - regenerate on demand |
| Orphan file tracking | Not needed - orphan data is benign |

| ✓ Appropriate | Implementation |
|--------------|----------------|
| On-demand generation | Generate when requested |
| Job queuing | Queue job when cache miss |
| Placeholder images | Return placeholder when missing |
| Metadata updates | Update path when generated |

### For Expensive Optional Data

| ✓ Appropriate | Implementation |
|--------------|----------------|
| Recovery frameworks | Requeue expensive jobs efficiently |
| Detection tooling | Identify missing expensive data |
| Job priority management | Prioritize recovery jobs |
| Batch processing | Efficient bulk regeneration |

---

## References

- [Artifact Lifecycle](./artifact-lifecycle.md) - Document lifecycle management
- [Storage Lifecycle Matrix](./storage-lifecycle-matrix.md) - Artifact storage characteristics
- [Derived Artifact Recovery](../operations/derived-artifact-recovery.md) - Recovery operations for expensive optional data
- [Plugin Development Guide](../plugins/plugin-development-guide.md)
- [Architecture Glossary](./glossary.md) - Semantic definitions and terminology

---

*This document establishes that all optional data (expensive or cheap) has the same authority level: NONE. Only the original artifact is authoritative.*
