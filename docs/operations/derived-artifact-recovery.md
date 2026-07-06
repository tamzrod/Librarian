# Derived Artifact Recovery

## Overview

This document describes the optional recovery system for expensive optional data in Librarian.

> **IMPORTANT: This is NOT about corruption.**
> 
> Missing optional data (embedding, OCR, object detection) is ALWAYS a cache miss, NEVER corruption.
> 
> Recovery is provided for efficiency, not because missing data is corruption.

See [Derived Artifact Contract](../architecture/derived-artifact-contract.md) for the authoritative statement.

---

## Core Principle

**Artifact is authoritative. Everything else is optional.**

| Category | Authority | Missing = |
|----------|-----------|------------|
| Original artifact | Authoritative | **CORRUPTION** |
| Embedding | Optional | Cache miss |
| OCR | Optional | Cache miss |
| Object Detection | Optional | Cache miss |
| Thumbnail | Optional | Cache miss |

**Recovery framework exists for EFFICIENCY, not because it's corruption.**

When optional data is missing:
1. Expensive optional data: Recovery framework requeues jobs efficiently
2. Cheap optional data (thumbnails): On-demand regeneration suffices

---

## What IS Recovery

Recovery is a convenience feature for expensive optional data.

It allows:
- Efficient bulk requeuing of expensive regeneration jobs
- Detection of missing expensive data
- Prioritized job scheduling for recovery

**Recovery does NOT mean the data was corrupted.**

---

## Supported Data Types

This recovery framework covers **expensive optional data only**.

| Artifact Type | Generation Cost | Missing = | Recovery |
|---------------|----------------|-----------|----------|
| embedding | High | Cache miss | Provided |
| ocr | High | Cache miss | Provided |
| object_detection | High | Cache miss | Provided |
| transcription | High | Cache miss | Provided |
| geolocation | Medium | Cache miss | Provided |
| thumbnail | Low | Cache miss | **NOT Provided** |
| preview | Low | Cache miss | **NOT Provided** |

> **Thumbnails and other cheap optional data are NOT managed by this framework.**
> They are cheap to regenerate and handled by on-demand regeneration.

---

## Architecture Principles

### Core Tenets

1. **Artifact is authoritative**: The original artifact is ground truth.
2. **Optional data is advisory**: Embeddings, OCR, etc. are not evidence.
3. **Missing = cache miss**: Optional data missing is NOT corruption.
4. **Recovery = efficiency**: Recovery exists to efficiently requeue expensive jobs.
5. **Selective repair**: Only missing data is requeued; healthy data is never regenerated.

### Design Philosophy

Expensive optional data (embeddings, OCR, object detection):
- **Optional**: The system functions without them; they enhance but don't block operation
- **Not evidence**: They are advisory metadata, not authoritative
- **Expensive to regenerate**: API calls, model inference, GPU usage
- **Recovery is a convenience**: Efficient bulk requeuing, not corruption repair

---

## Detection Workflow

### Purpose

Detection identifies the state of expensive optional data. It is informational only.

### Classification

Detection categorizes optional data as:

- **VALID**: Both metadata and file exist and match
- **MISSING**: Metadata exists but file is missing (stale metadata)
- **ORPHAN**: File exists but no metadata reference
- **PENDING**: Neither metadata nor file exists (expected - not enriched yet)

### What Detection Tells You

```
Detection shows: "5491 embeddings MISSING"
                    ↓
This means: 5491 cache misses
This is NOT: Corruption
This needs: Optional regeneration (if desired)
```

---

## Recovery Workflow

### Purpose

Recovery efficiently requeues expensive regeneration jobs for missing optional data.

**This is NOT repairing corruption. This is requeuing cache misses.**

### Recovery Process

```
1. Run detection to identify MISSING expensive data
   ↓
2. For each MISSING record:
   a. Clear stale metadata (optional)
   b. Create new job with appropriate priority
   ↓
3. Report results
```

### Safety Mechanisms

- **Dry-run mode**: Always run with `--dry-run` first to preview changes
- **Selective repair**: Only MISSING data is touched
- **No deletion**: Orphan files are reported but not automatically deleted
- **Idempotent**: Can be run multiple times safely

---

## CLI Usage

### List Available Data Types

```bash
python -m core.cli list
```

Output:
```
Available data types for optional recovery:

  Artifact Type          Missing =           Recovery Provided
  --------------------   -----------------   ----------------
  embedding              Cache miss          Yes
  ocr                    Cache miss          Yes
  object_detection       Cache miss          Yes
  transcription          Cache miss          Yes

NOTE: Thumbnails are cheap - use on-demand regeneration instead.
```

### Detect State

```bash
# Detect embeddings (example)
python -m core.cli detect embedding

# Detect with verbose output
python -m core.cli detect embedding -v
```

### Repair Missing Data

```bash
# Dry run (default) - shows what would be done
python -m core.cli repair embedding

# Execute
python -m core.cli repair embedding --fix
```

---

## Expected States

### Healthy State

```
================================================================
Detection Results: embedding
================================================================
  Total documents scanned:     5591
  Total files on disk:        5591
  Valid:                       5591
  Missing:                        0
  Orphan files:                   0
```

### Cache Miss State

```
================================================================
Detection Results: embedding
================================================================
  Total documents scanned:     5591
  Total files on disk:          100
  Valid:                         100
  Missing:                      5491  ← Cache misses (NOT corruption)
  Orphan files:                    0
```

**Both states are valid.** Missing = cache miss, not corruption.

---

## Failure Modes

### Detection Failures

| Failure | Cause | Resolution |
|---------|-------|------------|
| Cannot connect to database | PostgreSQL unavailable | Check database connectivity |
| Cannot list storage directory | Volume not mounted | Verify `/librarian-data` is mounted |
| Query timeout | Large database | Use pagination or increase timeout |

### Recovery Failures

| Failure | Cause | Resolution |
|---------|-------|------------|
| Cannot requeue job | Duplicate job exists | Already handled by job cancellation |
| Source file missing | Document deleted | Metadata cleared automatically |

---

## Runtime Validation

### Quick Check

```bash
# Check optional data state
python -m core.cli detect embedding | grep "Missing"
```

### What Missing Means

> Missing optional data = Cache miss (NOT corruption)
> 
> Missing = The data hasn't been generated yet, or was regenerated.
> 
> This is expected behavior for optional data.

---

## API Integration

```python
from storage.postgres_backend import PostgresBackend
from core.recovery import get_recovery_handler

backend = PostgresBackend()

# Get handler for expensive optional data
handler = get_recovery_handler('embedding', backend)

if handler:
    report = handler.detect()
    print(f"Missing: {len(report.missing)} (cache misses)")
    
    # Requeue if desired (for efficiency)
    if report.missing:
        handler.repair(report.missing, dry_run=False)

backend.close()
```

---

## Extending the Framework

To add support for new expensive optional data:

1. Create a new class inheriting from `BaseArtifactRecovery`
2. Implement required abstract methods
3. Register in `RECOVERY_HANDLERS` dict

**IMPORTANT:** Only add expensive optional data here.

**DO NOT add:**
- Thumbnails (use on-demand regeneration)
- Previews (use on-demand regeneration)
- Any cheap-to-regenerate data

---

## Security Considerations

- **Read-only detection**: Detection queries only; no modifications unless --fix is used
- **Controlled repairs**: Only metadata cleared and jobs requeued
- **No file deletion**: Orphan files are never automatically deleted
- **Audit trail**: All operations logged with document IDs

---

## References

- [Derived Artifact Contract](../architecture/derived-artifact-contract.md) - Authority vs cost principles
- [Storage Lifecycle Matrix](../architecture/storage-lifecycle-matrix.md) - Artifact classification
- [Artifact Lifecycle](../architecture/artifact-lifecycle.md) - Document lifecycle

---

*This document describes convenience recovery for expensive optional data. Missing optional data is always a cache miss, never corruption.

---

## Glossary

See [Architecture Glossary](../architecture/glossary.md) for definitions of key terms.
