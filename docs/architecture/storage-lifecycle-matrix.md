# Storage Lifecycle Matrix

**Version**: 1.0  
**Last Updated**: 2026-07-06

---

## Overview

This document maps all artifact types to their storage lifecycle characteristics, generation cost, and recovery strategy.

## Core Principle: Authority vs Cost

**Artifact is authoritative. Everything else is optional.**

Generation cost affects recovery strategy, NOT authority level.

---

## Authority Classification

| Category | Authority | Description |
|----------|-----------|-------------|
| **AUTHORITATIVE** | High | Original artifact, document row, SHA256 |
| **OPTIONAL** | None | All derived/enriched data |

### What IS Authoritative

- Original artifact file (the evidence)
- Document row in database (identity)
- SHA256 hash (integrity verification)

### What IS NOT Authoritative (All Optional)

- embeddings (expensive to regenerate)
- OCR (expensive to regenerate)
- object_detection (expensive to regenerate)
- transcription (expensive to regenerate)
- geolocation (expensive to regenerate)
- thumbnail (cheap to regenerate)
- preview (cheap to regenerate)

---

## Artifact Classification Matrix

| Artifact Type | Authority | Generation Cost | Recovery Strategy |
|--------------|-----------|----------------|-------------------|
| **embeddings** | Optional | High | Recovery framework justified |
| **OCR** | Optional | High | Recovery framework justified |
| **object_detection** | Optional | High | Recovery framework justified |
| **transcription** | Optional | High | Recovery framework justified |
| **geolocation** | Optional | Medium | Recovery framework justified |
| **photo_metadata** | Optional | Medium | Recovery framework justified |
| **entity_extraction** | Optional | Medium | Recovery framework justified |
| **event_extraction** | Optional | Medium | Recovery framework justified |
| **thumbnail** | Optional | Low | On-demand regeneration only |
| **preview** | Optional | Low | On-demand regeneration only |
| **resized_image** | Optional | Low | On-demand regeneration only |
| **filmstrip** | Optional | Low | On-demand regeneration only |

---

## What IS Corruption

Corruption only exists when:

| Condition | Description |
|-----------|-------------|
| Evidence missing | Original artifact file deleted |
| Record missing | Document row deleted from database |
| Hash mismatch | SHA256 doesn't match stored value |
| Identity mismatch | Path/content mismatch with document |

**Missing embedding = expensive cache miss (NOT corruption)**

**Missing OCR = expensive cache miss (NOT corruption)**

**Missing thumbnail = cheap cache miss (NOT corruption)**

---

## Recovery Strategy by Cost

### Expensive Optional Data

| Characteristic | Value |
|---------------|-------|
| Generation Cost | Medium to High |
| External Dependencies | May require API keys, models, GPU |
| Recovery Framework | Justified (expensive to regenerate) |
| Detection Tooling | Provided |
| Job Priority | Higher for recovery jobs |

**Missing these is always a cache miss, NEVER corruption.**

**Recovery is provided for efficiency, not because it's corruption.**

#### Embeddings

```
┌─────────────────────────────────────────────────────────────────┐
│ Artifact: embeddings                                            │
├─────────────────────────────────────────────────────────────────┤
│ Authority: OPTIONAL (cache miss, not corruption)               │
│ Cost: High (API calls or model inference)                      │
│ Recovery: Justified - regeneration is expensive                 │
├─────────────────────────────────────────────────────────────────┤
│ Missing = expensive cache miss                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### OCR

```
┌─────────────────────────────────────────────────────────────────┐
│ Artifact: OCR                                                   │
├─────────────────────────────────────────────────────────────────┤
│ Authority: OPTIONAL (cache miss, not corruption)               │
│ Cost: High (model inference, potentially GPU)                  │
│ Recovery: Justified - regeneration is expensive                 │
├─────────────────────────────────────────────────────────────────┤
│ Missing = expensive cache miss                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Object Detection

```
┌─────────────────────────────────────────────────────────────────┐
│ Artifact: object_detection                                       │
├─────────────────────────────────────────────────────────────────┤
│ Authority: OPTIONAL (cache miss, not corruption)               │
│ Cost: High (GPU, model inference)                               │
│ Recovery: Justified - regeneration is expensive                 │
├─────────────────────────────────────────────────────────────────┤
│ Missing = expensive cache miss                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### Cheap Optional Data (Thumbnails)

| Characteristic | Value |
|---------------|-------|
| Generation Cost | Low |
| External Dependencies | None |
| Recovery Framework | NOT required |
| Detection Tooling | NOT required |
| Startup Scans | NOT required |

**Missing thumbnails is always a cache miss, NEVER corruption.**

**No recovery framework needed - regenerate on demand.**

```
┌─────────────────────────────────────────────────────────────────┐
│ Artifact: thumbnail                                             │
├─────────────────────────────────────────────────────────────────┤
│ Authority: OPTIONAL (cache miss, not corruption)               │
│ Cost: Low (<1 second CPU)                                      │
│ Recovery: NOT required - regenerate on demand                   │
├─────────────────────────────────────────────────────────────────┤
│ Missing = cheap cache miss                                     │
│ No integrity audits required                                   │
│ No orphan tracking required                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Success Statement

> **Deleting every thumbnail file in the system shall NOT be considered corruption.**
> 
> The only consequence:
> - Placeholder images appear temporarily
> - Thumbnails regenerate automatically on demand
> 
> **This is the intended behavior.**

---

## Metadata Authority

### Authoritative Metadata

These fields must be accurate and in sync with filesystem:

| Field | Table | Authority |
|-------|-------|-----------|
| `id` | documents | Authoritative |
| `path` | documents | Authoritative |
| `sha256` | documents | Authoritative |
| `artifact_type` | documents | Authoritative |

### Advisory Metadata (Optional)

These fields may be stale or missing:

| Field | Table | Authority |
|-------|-------|-----------|
| `embedding_path` | documents | Advisory - optional data |
| `ocr_path` | documents | Advisory - optional data |
| `detection_path` | documents | Advisory - optional data |
| `transcription_path` | documents | Advisory - optional data |
| `thumbnail_path` | documents | Advisory - optional data |

---

## Deletion Behavior

### Deleting Evidence (CORRUPTION)

```
Deleting original artifact = CORRUPTION

Response:
1. Document marked as archived
2. Recovery not possible (evidence gone)
```

### Deleting Optional Data (CACHE MISS)

```
Deleting optional data = CACHE MISS (NOT corruption)

Expensive optional data:
1. Run recovery detection (optional)
2. Requeue regeneration jobs
3. Data regenerates

Cheap optional data (thumbnails):
1. Nothing required
2. Data regenerates on demand
3. Placeholder shown temporarily
```

---

## References

- [Derived Artifact Contract](./derived-artifact-contract.md) - Authority and cost principles
- [Artifact Lifecycle](./artifact-lifecycle.md) - Document lifecycle
- [Derived Artifact Recovery](../operations/derived-artifact-recovery.md) - Recovery for expensive optional data
- [Plugin Development Guide](../plugins/plugin-development-guide.md)
- [Architecture Glossary](./glossary.md) - Semantic definitions and terminology

---

*This matrix establishes that only the original artifact is authoritative. All derived/enriched data (expensive or cheap) is optional.*
