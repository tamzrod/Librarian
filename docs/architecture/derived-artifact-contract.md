# Derived Artifact Contract

This document establishes the contractual rules for derived artifacts in the Librarian system. These rules govern how plugins and the core system must handle artifacts that may or may not exist at runtime.

## Core Principles

### 1. Derived artifacts are never authoritative

Derived artifacts represent processed interpretations of evidence, not the truth itself. They exist to improve user experience and enable advanced features, but they are not the system of record.

**Implication:** Any data validation or business logic must reference Tier 0 evidence, not Tier 1 artifacts.

### 2. Missing derived artifacts are valid runtime state

The absence of a derived artifact (thumbnail, embedding, OCR output) is not an error condition. The system must handle this gracefully without raising exceptions or blocking operations.

**Implication:** Database queries returning null for artifact references must be treated as normal, not exceptional.

### 3. Database references do not guarantee filesystem existence

A database record referencing an artifact path does not guarantee that file exists on the filesystem. The artifact may have been deleted, the volume may not be mounted, or the record may be stale.

**Implication:** Always verify filesystem existence before attempting to read artifact data.

### 4. Plugins must tolerate missing artifacts

Plugin execution must not fail when expected artifacts are missing. Plugins should gracefully degrade, report the absence, or trigger regeneration rather than crashing.

**Implication:** Implement null checks and missing-file handlers in all plugin code.

### 5. Missing artifacts must not corrupt evidence

The absence of a derived artifact must never affect the integrity of Tier 0 evidence. Evidence must remain immutable and unmodified regardless of artifact state.

**Implication:** Evidence paths must be read-only from the perspective of all plugins and workers.

---

## Valid vs Invalid States

### Valid States

These states represent expected, correct runtime behavior:

```
✓ thumbnail_path exists, thumbnail file exists
✓ thumbnail_path exists, thumbnail file MISSING  ← Valid, triggers regeneration
✓ embedding_path exists, embedding file MISSING  ← Valid, triggers regeneration
✓ OCR_path exists, OCR file MISSING             ← Valid, triggers regeneration
✓ detection_path exists, detection file MISSING  ← Valid, triggers regeneration
```

**Reasoning:** Missing derived artifacts are recoverable through regeneration. The system should respond by scheduling regeneration, not by failing.

### Invalid States

These states indicate data corruption or system misconfiguration:

```
✗ document row MISSING, original file exists     ← Database corruption
✗ document row exists, original file MISSING      ← Evidence loss (catastrophic)
✗ sha256 MISMATCH between record and file        ← Evidence corruption (catastrophic)
```

**Reasoning:** These states indicate loss or corruption of Tier 0 evidence, which is the authoritative data source.

---

## Implementation Requirements

### For Plugin Developers

1. **Check artifact existence before access:**
   ```python
   if artifact_path.exists():
       data = load_artifact(artifact_path)
   else:
       schedule_regeneration(document_id, artifact_type)
       return None  # or placeholder
   ```

2. **Never delete or modify evidence:**
   ```python
   # CORRECT: Read-only access to evidence
   original_file = evidence_path.open('rb')
   
   # INCORRECT: Attempting to modify evidence
   # evidence_path.write_bytes(...)  ← NEVER DO THIS
   ```

3. **Handle regeneration gracefully:**
   ```python
   if not artifact_cached:
       result = await regenerate(document_id)
       return result
   ```

### For Core System Developers

1. **Schema must allow nullable artifact references:**
   ```sql
   -- CORRECT: Artifact columns are nullable
   thumbnail_path TEXT,
   embedding_path TEXT,
   
   -- INCORRECT: Requiring artifacts to exist
   -- thumbnail_path TEXT NOT NULL  ← DO NOT DO THIS
   ```

2. **Queries must handle missing artifacts:**
   ```python
   results = query_documents()
   for doc in results:
       if doc.thumbnail_path and Path(doc.thumbnail_path).exists():
           display_thumbnail(doc.thumbnail_path)
       else:
           display_placeholder()
   ```

3. **Regeneration should be on-demand:**
   ```python
   # Schedule regeneration, don't block
   if artifact_missing:
       worker_queue.enqueue('regenerate', doc_id, artifact_type)
       return PlaceholderResponse(artifact_type, doc_id)
   ```

---

## Artifact Types and Their Contracts

| Artifact Type | Can Be Missing | Can Be Stale | Must Survive Reset |
|---------------|----------------|--------------|-------------------|
| Thumbnail | Yes | Yes | No |
| Embedding | Yes | Yes | No |
| OCR Output | Yes | Yes | No |
| Object Detection | Yes | Yes | No |
| Transcription | Yes | Yes | No |
| Document (Tier 0) | No | No | Yes |
| Checksum (Tier 0) | No | No | Yes |

---

## Debugging Checklist

When investigating artifact-related issues:

1. **Verify evidence exists** — Check Tier 0 data first
2. **Verify database record** — Confirm document row exists
3. **Verify artifact path** — Check if path column is populated
4. **Verify filesystem state** — Use `ls` or `Path.exists()` to confirm file
5. **Check volume mounts** — Use `docker inspect` to verify mounts
6. **Schedule regeneration** — If all above are valid but file is missing

**Never assume** that a database record implies filesystem existence.

---

## Common Anti-Patterns to Avoid

1. **Don't assume artifact exists:**
   ```python
   # WRONG
   with open(doc.thumbnail_path) as f:
       return f.read()
   
   # RIGHT
   if doc.thumbnail_path and Path(doc.thumbnail_path).exists():
       with open(doc.thumbnail_path) as f:
           return f.read()
   ```

2. **Don't fail on missing artifacts:**
   ```python
   # WRONG
   if not artifact.exists():
       raise ArtifactMissingError()
   
   # RIGHT
   if not artifact.exists():
       logger.warning(f"Artifact missing, scheduling regeneration: {doc_id}")
       return None
   ```

3. **Don't use artifacts for critical validation:**
   ```python
   # WRONG
   if doc.thumbnail_path:
       mark_as_processed(doc_id)
   
   # RIGHT
   if doc.sha256_verified:
       mark_as_processed(doc_id)
   ```