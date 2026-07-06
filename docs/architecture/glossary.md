# Architecture Glossary

**Version**: 1.0  
**Last Updated**: 2026-07-06  
**Status**: Authoritative Reference

---

## Purpose

This glossary establishes the official vocabulary for Librarian. It is the **semantic source of truth** for:

- Documentation writers
- Architecture decision makers
- Plugin developers
- Operations staff
- AI agents
- Future maintainers

When terms conflict across documents, this glossary takes precedence.

---

## Core Definitions

### Artifact

**Definition:** The original evidence object.

**Characteristics:**
- Authoritative
- Immutable
- Uniquely identified by identity (id, sha256, path)
- Loss or modification constitutes **corruption**

**Examples:**
- Image file (`.jpg`, `.png`, `.heic`)
- Video file (`.mp4`, `.mov`)
- Document file (`.pdf`, `.doc`)
- Audio file (`.mp3`, `.wav`)
- Archive file (`.zip`, `.tar`)

**Non-examples:**
- Thumbnails (cache)
- Embeddings (cache)
- OCR results (cache)
- Object detection (cache)

---

### Artifact Identity

**Definition:** The properties that uniquely define an artifact.

**Characteristics:**
- Immutable
- Authoritative
- Loss or mismatch constitutes **corruption**

**Examples:**
- `document_id` (database primary key)
- `sha256` (content hash)
- `original_path` (filesystem location)
- `original_filename`

**Corruption Triggers:**
- Missing `document_id`
- `sha256` mismatch with file content
- Path no longer resolves to file
- Filename changed without update

---

### Evidence

**Definition:** The combination of authoritative artifact and its identity.

**Components:**
1. Original artifact file
2. Artifact identity (id, sha256, path)
3. Authoritative database record

**Examples:**
- `documents` row in database
- Original file on filesystem
- SHA256 hash stored alongside file

**Note:** Evidence is the only thing that can be corrupted. Everything else is optional.

---

### Corruption

**Definition:** Loss, modification, or inconsistency of authoritative evidence.

**Characteristics:**
- Irreversible data loss
- Requires investigation
- Indicates system failure

**Examples (What IS Corruption):**
- Original artifact file deleted
- `documents` row missing
- `sha256` hash mismatch with file
- Artifact identity inconsistency
- Database corruption
- Filesystem corruption

**Non-examples (What is NOT Corruption):**
- Missing thumbnail
- Missing embeddings
- Missing OCR results
- Missing object detection
- Missing EXIF enrichment
- Missing geolocation
- Missing timeline events

**Key Principle:** Only evidence can be corrupted. Optional data can only have cache misses.

---

### Enrichment

**Definition:** Optional information derived from or attached to an artifact.

**Characteristics:**
- Optional (not required for system function)
- Regeneratable from evidence
- Non-authoritative
- May be expensive or cheap to compute

**Examples:**
- OCR text extraction
- Vector embeddings
- Object detection results
- EXIF metadata extraction
- Geolocation enrichment
- Timeline events
- Entity extraction
- Face detection

**Authority Level:** NONE

**Loss = Cache miss (NOT corruption)**

---

### Cache

**Definition:** Regeneratable data derived from authoritative evidence.

**Characteristics:**
- Derived from evidence (never the other way around)
- Regeneratable
- May be cheap or expensive to regenerate
- Authority level: NONE

**Examples:**
- Thumbnails
- Previews
- Image resizes
- Filmstrip frames
- Embeddings (expensive cache)
- OCR results (expensive cache)
- Object detection (expensive cache)

**Key Principle:** Regeneration cost affects recovery strategy, not authority level.

---

### Cache Miss

**Definition:** Expected runtime state where optional cache data does not exist.

**Characteristics:**
- Expected behavior for optional data
- Not corruption
- Triggers regeneration
- May be cheap or expensive to fill

**Examples:**
- Thumbnail not generated yet
- Embedding not computed yet
- OCR not run yet
- Object detection not performed yet
- File deleted after enrichment (metadata stale)

**Handling:**
- Cheap cache miss: Regenerate on demand
- Expensive cache miss: Queue for background regeneration

---

### Regeneration

**Definition:** Recreating optional cache data from authoritative evidence.

**Characteristics:**
- Creates from evidence (never replaces evidence)
- Idempotent (can run multiple times safely)
- May be synchronous or asynchronous

**Examples:**
- Regenerating thumbnail from original image
- Rebuilding embeddings from original file
- Rerunning OCR on original document
- Re-running object detection on original image

---

### Recovery

**Definition:** Operational process that efficiently recreates missing optional data.

**Characteristics:**
- Convenience feature (NOT corruption repair)
- Efficient bulk requeuing
- Optional operation
- Exists for expensive cache regeneration

**Recovery is NOT:**
- Corruption repair
- Evidence restoration
- Data healing
- System repair

**Examples:**
- Bulk requeue of embedding generation jobs
- Batch OCR regeneration
- Thumbnail regeneration scan

**Key Principle:** Recovery exists for efficiency, not because missing cache is corruption.

---

### Persistence

**Definition:** How long data survives resets, rebuilds, upgrades, or recreation.

**Characteristics:**
- Independent of authority
- Volatility varies by data type
- Not a guarantee

**Persistence Tiers:**

| Data Type | Persistence | Reason |
|----------|-------------|--------|
| Original artifact | Permanent | User data |
| Document record | Permanent | Identity |
| SHA256 | Permanent | Integrity |
| Embeddings | Volatile | Cache (regeneratable) |
| OCR | Volatile | Cache (regeneratable) |
| Thumbnails | Volatile | Cache (regeneratable) |
| EXIF | Volatile | Cache (regeneratable) |

**Key Principle:** Persistence does NOT imply authority. Evidence persists; cache may or may not.

---

### Integrity

**Definition:** Verification that authoritative evidence is intact and unmodified.

**Characteristics:**
- Applies to evidence only
- Uses cryptographic verification
- Detects corruption

**Integrity Checks:**
- SHA256 hash comparison
- File existence verification
- Database record validation
- Identity consistency checks

**Integrity Does NOT Apply To:**
- Thumbnails
- Embeddings
- OCR results
- Any optional data

**Why:** Optional data is regeneratable; integrity checking is unnecessary overhead.

---

### Runtime Truth

**Definition:** Actual observed system state at a given moment.

**Priority Order (Highest to Lowest):**

1. `docker inspect` (container state)
2. `docker volume inspect` (volume state)
3. `docker logs` (runtime events)
4. Database queries (persistent state)
5. Filesystem inspection (files exist)
6. Source code (intended behavior)
7. Configuration files (expected state)
8. Documentation (described state)

**Key Principle:** Runtime truth overrides all assumptions, including configuration and documentation.

---

### Configuration Truth

**Definition:** Expected or intended system state as defined in configuration.

**Examples:**
- `docker-compose.yml`
- Environment variables
- Configuration files
- Source code assumptions
- Documentation claims

**Characteristics:**
- May not match runtime
- Should be verified against runtime
- Subordinate to runtime truth

**Key Principle:** Configuration assumes; runtime proves.

---

### Plugin Dependency

**Definition:** External resources required by a plugin to function.

**Characteristics:**
- May be optional or required
- Not evidence
- May be cached
- Loss = feature unavailable (not corruption)

**Examples:**
- ML models (YOLO, Whisper, etc.)
- Python packages (Pillow, OpenCV, etc.)
- Language packs
- External API keys
- External databases

**Plugin Enabled ≠ Dependencies Installed**

---

### Plugin Cache

**Definition:** Reusable runtime assets that improve plugin efficiency.

**Characteristics:**
- Optional for plugin function
- Downloaded/generated on first use
- Loss = bandwidth/time cost only
- Not evidence

**Examples:**
- Hugging Face model cache
- PyTorch model cache
- pip package cache
- Downloaded language models
- Cached API responses

---

## Words to Avoid

These terms cause confusion and should be replaced with precise alternatives:

### ❌ Do NOT Use

| Avoid | Problem | Use Instead |
|-------|---------|-------------|
| "corrupted embeddings" | Embeddings aren't evidence | "missing embeddings" or "embeddings cache miss" |
| "corrupted thumbnail" | Thumbnails aren't evidence | "missing thumbnail" |
| "corrupted OCR" | OCR isn't evidence | "missing OCR results" |
| "persistence implies authority" | False assumption | "persistence is independent of authority" |
| "missing thumbnail is corruption" | Contradiction | "missing thumbnail is cache miss" |
| "repair corrupted cache" | Cache isn't corrupted | "regenerate cache" or "recover from cache miss" |
| "data integrity check for thumbnails" | Unnecessary | "no integrity check needed for optional cache" |
| "evidence of embeddings" | Embeddings aren't evidence | "optional enrichment" |
| "recover from corruption" for cache | Cache miss ≠ corruption | "recover from cache miss" |
| "rebuild evidence" for cache | Cache isn't evidence | "regenerate cache" |

### ✅ Correct Usage

| Use | Meaning |
|-----|---------|
| "missing thumbnails" | Expected cache miss |
| "missing embeddings" | Expected cache miss |
| "regenerate thumbnails" | On-demand cache fill |
| "recover from cache miss" | Efficient bulk regeneration |
| "evidence corruption" | Original file/record affected |
| "optional data unavailable" | Plugin not installed or failed |
| "cache invalidated" | Stale metadata or deleted file |

---

## Authority Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AUTHORITY HIERARCHY                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LEVEL 1: AUTHORITATIVE (ONLY THIS LEVEL)                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • Original artifact file                                    │   │
│  │ • documents table row                                        │   │
│  │ • sha256 hash                                                │   │
│  │ • artifact identity                                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Loss = CORRUPTION                                                │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  LEVEL 2: OPTIONAL (ALL EQUAL - NONE AUTHORITATIVE)               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ • Thumbnails           (cheap cache)                       │   │
│  │ • Previews             (cheap cache)                       │   │
│  │ • Embeddings           (expensive cache)                   │   │
│  │ • OCR                  (expensive cache)                  │   │
│  │ • Object Detection     (expensive cache)                   │   │
│  │ • EXIF Enrichment      (enrichment)                         │   │
│  │ • Geolocation          (enrichment)                         │   │
│  │ • Timeline Events      (enrichment)                         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  Loss = CACHE MISS (NOT corruption)                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Quick Reference

### Is It Corruption?

| Condition | Corruption? | Action |
|-----------|-------------|--------|
| Original file deleted | YES | Investigate |
| documents row missing | YES | Investigate |
| sha256 mismatch | YES | Investigate |
| Thumbnail missing | NO | Regenerate |
| Embedding missing | NO | Regenerate |
| OCR missing | NO | Regenerate |
| Object detection missing | NO | Regenerate |

### Cache Miss vs Corruption

| Scenario | Classification | Response |
|---------|----------------|----------|
| Original file gone | CORRUPTION | Investigate |
| documents row gone | CORRUPTION | Investigate |
| Thumbnail gone | Cache miss | Regenerate |
| Embedding gone | Cache miss | Regenerate |
| OCR gone | Cache miss | Regenerate |

### Recovery vs Regeneration

| Term | Meaning | When |
|------|---------|------|
| Regeneration | Individual recreation | On-demand |
| Recovery | Bulk efficient recreation | Operational convenience |

---

## Cross References

This glossary is referenced by:

- [Artifact Lifecycle](./artifact-lifecycle.md)
- [Derived Artifact Contract](./derived-artifact-contract.md)
- [Storage Lifecycle Matrix](./storage-lifecycle-matrix.md)
- [Derived Artifact Recovery](../operations/derived-artifact-recovery.md)
- [Plugin Development Guide](../plugins/plugin-development-guide.md)
- [Runtime Debugging Guide](../operations/runtime-first-debugging.md) _(if exists)_

---

*This glossary is the semantic source of truth for Librarian. When in doubt, refer here.*
