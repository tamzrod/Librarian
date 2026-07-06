# Evidence Lifecycle

This document defines the three-tier persistence architecture for Librarian, establishing clear contracts for data durability and operational behavior.

## Tier Definitions

### Tier 0 — Evidence (Authoritative)

**Description:** The authoritative source of truth. Evidence represents the original, immutable input data that the system processes.

**Examples:**
- `/library` — The source directory containing original documents
- `documents` — Original file content stored in the database
- `sha256` — Cryptographic hashes that verify document integrity

**Properties:**
- **Immutable** — Evidence must never be modified after ingestion
- **Loss is catastrophic** — Deletion or corruption of evidence is irreversible and represents data loss
- **Plugins must never modify** — All processing must be read-only against evidence

**Operational Rules:**
- Evidence survives all reset operations (rebuild, reset, nuclear)
- Evidence integrity must be verifiable through checksums
- Any operation that modifies evidence must be considered destructive
- Database records referencing evidence must maintain referential integrity

---

### Tier 1 — Derived Artifacts (Regeneratable)

**Description:** Processing outputs generated from evidence. These artifacts can be recreated from Tier 0 data.

**Examples:**
- `thumbnails` — Preview images generated from photographs
- `embeddings` — Vector representations for semantic search
- `OCR output` — Text extracted from scanned documents
- `object detection` — Bounding boxes and labels from image analysis
- `transcriptions` — Text converted from audio/video content

**Properties:**
- **Optional** — System can function without these artifacts
- **Loss is recoverable** — Artifacts can be regenerated from evidence
- **Can be regenerated** — Full pipeline reprocessing will recreate these

**Operational Rules:**
- Derived artifacts may be deleted to free storage space
- Missing artifacts are valid runtime state (not errors)
- Regeneration should be triggered on demand, not automatically
- Database references to artifacts must tolerate null/missing values

---

### Tier 2 — Plugin Infrastructure

**Description:** Runtime dependencies and cached data required for plugin execution. These are independent of the evidence lifecycle.

**Examples:**
- `plugin dependencies` — Python packages required by plugins
- `plugin cache` — Cached compilation and runtime data
- `models` — ML model weights and configurations
- `pip cache` — Downloaded Python packages
- `huggingface cache` — Downloaded models and tokenizers

**Properties:**
- **Replaceable** — Can be removed and reinstalled without data loss
- **Downloadable** — Can be fetched from their original sources
- **Independent of evidence lifecycle** — Not tied to document or artifact data

**Operational Rules:**
- Tier 2 data can be safely deleted between reset operations
- Missing Tier 2 data should be regenerated from package registries
- Plugin execution failures due to missing Tier 2 data are recoverable
- Tier 2 data should not be backed up as part of evidence preservation

---

## Tier Comparison Matrix

| Property | Tier 0 (Evidence) | Tier 1 (Artifacts) | Tier 2 (Infrastructure) |
|----------|-------------------|--------------------|--------------------------|
| **Authority** | Source of truth | Derived from truth | Operational support |
| **Mutability** | Immutable | Mutable/regeneratable | Replaceable |
| **Loss impact** | Catastrophic | Recoverable | Recoverable |
| **Backup required** | Yes, always | Optional | No |
| **Survives nuclear reset** | Yes | No | No |
| **Survives reset** | Yes | No | Partial |
| **Survives rebuild** | Yes | Yes | Yes |

---

## Operational Implications

### For Developers

1. **Never modify Tier 0 data** — All processing should be read-only
2. **Design for regeneration** — Tier 1 artifacts should be reproducible
3. **Isolate dependencies** — Tier 2 should not leak into evidence paths

### For Operations

1. **Prioritize Tier 0 backups** — Evidence preservation is critical
2. **Treat Tier 1 absence as normal** — Missing artifacts are not errors
3. **Treat Tier 2 as disposable** — Infrastructure can be rebuilt from manifests

### For AI Agents

1. **Never infer Tier 0 existence from Tier 1 presence** — Artifacts don't guarantee evidence
2. **Report Tier 0 corruption immediately** — This is the highest severity issue
3. **Distinguish regeneration from recovery** — Tier 1 can be regenerated; Tier 0 cannot