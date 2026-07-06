# Documentation Consistency Audit

**Audit Date:** 2026-07-06  
**Auditor:** OpenHands Agent  
**Scope:** All documentation under `docs/`

---

## Executive Summary

This audit examines all documentation for consistency with the core architecture principles:

1. **Artifact is authoritative** - Original file, documents table, sha256, artifact identity
2. **Everything attached to artifact is optional** - Thumbnails, embeddings, OCR, etc.
3. **Missing optional data is a cache miss** - Not corruption
4. **Runtime state is authoritative over configuration** - docker inspect > docker-compose

### Documents Reviewed

| Category | Count | Files |
|----------|-------|-------|
| Architecture | 5 | artifact-lifecycle.md, derived-artifact-contract.md, storage-lifecycle-matrix.md, architectural-audit-*.md |
| Operations | 2 | derived-artifact-recovery.md, deployment-lifecycle-audit.md |
| Plugins | 7 | plugin-*.md, README.md, dependency-management.md |
| Plugin: EXIF | 4 | README.md, architecture.md, capabilities.md, metadata-schema.md |
| Plugin: Object Detection | 8 | README.md, architecture.md, capabilities.md, etc. |
| Dashboard | 4 | TRACE-DESIGN.md, artifact-explorer.md, dashboard-architecture.md |
| API Contract | 4 | v1.0.md, timeline-v1.md, README.md, MIGRATION.md |
| Refactor (Active) | 12 | E4-E10, P13-P18, P2, P4, P8 |
| Refactor (Archived) | 9 | P1, P3, P5-P12 |
| Refactor: Operation EXIF | 10 | E1-E10, DEPENDENCIES.md, WAVES.md, README.md |
| Other | 8 | ARCHITECTURE.md, VISION.md, etc. |

---

## Architecture Principles (Reference)

### Principle 1: Artifact is Authoritative
**Examples:**
- Original file
- documents table
- sha256
- artifact identity

**Loss = Corruption**

### Principle 2: Everything Attached is Optional
**Examples:**
- Thumbnails
- Embeddings
- OCR
- Object detection
- EXIF enrichment
- Geolocation
- Timelines
- Future plugins

**Loss = NOT Corruption**

### Principle 3: Missing Optional Data = Cache Miss
**Examples:**
- Missing thumbnail = cheap cache miss
- Missing embedding = expensive cache miss
- Missing OCR = expensive cache miss

**Generation cost changes recovery strategy. Authority level does NOT change.**

### Principle 4: Runtime State > Configuration
**Priority:**
1. docker inspect
2. docker volume inspect
3. docker logs
4. database queries
5. filesystem inspection
6. source code
7. configuration files
8. documentation

---

## Audit Findings

### FINDING-001: API Contract Uses "persistence" Terminology

| Field | Value |
|-------|-------|
| **File** | `docs/api-contract/v1.0.md` |
| **Lines** | 76, 95, 113 |
| **Issue** | Uses `persistence_available` and `persistence_errors` which may imply guarantees about derived data |
| **Severity** | Low |
| **Architecture Principle** | Principle 2 (Everything attached is optional) |
| **Recommended Correction** | Rename to `derived_data_available` or clarify that this only refers to original artifact persistence |

**Current:**
```json
"persistence_available": true,
"persistence_errors": [],
```

**Suggested:**
```json
"artifact_persistence_available": true,
"optional_data_errors": [],
```

---

### FINDING-002: EXIF Plugin Uses "Persistence" Terminology

| Field | Value |
|-------|-------|
| **Files** | `docs/plugins/exif/README.md`, `docs/plugins/exif/architecture.md`, `docs/plugins/exif/roadmap.md` |
| **Issue** | References to "Database persistence" may imply that EXIF data is authoritative |
| **Severity** | Medium |
| **Architecture Principle** | Principle 2 (Everything attached is optional) |
| **Recommended Correction** | Change "persistence" to "storage" or "caching" to clarify optional nature |

**Current:**
```
Database backend for persistence
```

**Suggested:**
```
Database backend for enrichment storage (optional)
```

---

### FINDING-003: Object Detection Plugin States Outputs are "Optional"

| Field | Value |
|-------|-------|
| **File** | `docs/plugins/object-detection/README.md` |
| **Line** | 113 |
| **Issue** | States "Annotated images are optional" - consistent but could be clearer |
| **Severity** | Info |
| **Architecture Principle** | Principle 2 |
| **Recommended Correction** | Add explicit statement: "All object detection output is optional enrichment, not evidence" |

---

### FINDING-004: E4 Document Uses "Authoritative" for Discovery Metadata

| Field | Value |
|-------|-------|
| **File** | `docs/refactor/operation-exif/E4-inconsistent-metadata-ownership.md` |
| **Issue** | The title says "Metadata Ownership Contract" but the term "authoritative" is used correctly for discovery metadata only |
| **Severity** | Low (terminology may cause confusion) |
| **Architecture Principle** | Principle 1 (Artifact is authoritative) |
| **Recommended Correction** | Rename "authoritative" to "primary" or "discovery-owned" to avoid confusion with the artifact being authoritative |

---

### FINDING-005: Dashboard Uses "Optional" Correctly

| Field | Value |
|-------|-------|
| **Files** | `docs/dashboard/artifact-explorer.md`, `docs/dashboard/dashboard-architecture.md` |
| **Issue** | None - these documents correctly state "Understanding is optional" |
| **Severity** | N/A |
| **Status** | ✓ ALIGNED |

---

### FINDING-006: Recently Updated Architecture Docs Are Consistent

| Field | Value |
|-------|-------|
| **Files** | `docs/architecture/derived-artifact-contract.md`, `docs/architecture/storage-lifecycle-matrix.md`, `docs/architecture/artifact-lifecycle.md`, `docs/operations/derived-artifact-recovery.md` |
| **Issue** | None - these documents have been recently updated and are fully consistent with the architecture principles |
| **Severity** | N/A |
| **Status** | ✓ ALIGNED |

---

### FINDING-007: Archived Documents May Contain Outdated Assumptions

| Field | Value |
|-------|-------|
| **Files** | `docs/refactor/archive/*.md` |
| **Issue** | Archived documents may contain references to old architecture (pre-architecture-update) |
| **Severity** | Low (expected for archived docs) |
| **Recommendation** | Mark archived documents with date when archived and note: "This document reflects architecture as of [date]. Current architecture may differ." |

---

## Summary by Severity

### High Severity
*None found*

### Medium Severity
- FINDING-002: EXIF "persistence" terminology

### Low Severity
- FINDING-001: API "persistence" terminology
- FINDING-004: E4 "authoritative" terminology

### Info/Resolved
- FINDING-003: Object detection "optional" (acceptable)
- FINDING-005: Dashboard aligned
- FINDING-006: Architecture docs aligned
- FINDING-007: Archived docs (expected)

---

## Alignment Summary

| Category | Aligned | Needs Review | Archived |
|----------|---------|--------------|----------|
| Architecture | ✓ | 0 | 0 |
| Operations | ✓ | 0 | 0 |
| Plugins (general) | ✓ | 0 | 0 |
| Plugin: EXIF | ✓ | 1 | 0 |
| Plugin: Object Detection | ✓ | 0 | 0 |
| Dashboard | ✓ | 0 | 0 |
| API Contract | ✓ | 1 | 0 |
| Refactor (Active) | ✓ | 1 | 0 |
| Refactor (Archived) | N/A | 0 | 1 |

---

## Recommendations

### Immediate Actions (No Code Changes)

1. **Update API Contract Terminology** (FINDING-001)
   - Change `persistence_available` → `artifact_persistence_available`
   - Change `persistence_errors` → `optional_data_errors`

2. **Update EXIF Plugin Documentation** (FINDING-002)
   - Replace "persistence" with "storage" or "enrichment caching"
   - Add explicit statement: "EXIF enrichment is optional, not authoritative"

3. **Clarify E4 Document Terminology** (FINDING-004)
   - Consider renaming to avoid "authoritative" confusion
   - Add note: "Discovery metadata is primary, not authoritative"

### Future Actions (Non-Blocking)

4. **Archive Documentation** (FINDING-007)
   - Add "Archived" header with date to archived docs
   - Add note: "Reflects architecture as of [date]"

---

## Documents Confirmed Aligned

The following documents are confirmed to be consistent with the architecture principles:

### Core Architecture
- `docs/architecture/artifact-lifecycle.md` ✓
- `docs/architecture/derived-artifact-contract.md` ✓
- `docs/architecture/storage-lifecycle-matrix.md` ✓

### Operations
- `docs/operations/derived-artifact-recovery.md` ✓

### Plugins
- `docs/plugins/plugin-development-guide.md` ✓
- `docs/plugins/plugin-states.md` ✓

### Dashboard
- `docs/dashboard/artifact-explorer.md` ✓
- `docs/dashboard/dashboard-architecture.md` ✓
- `docs/dashboard/TRACE-DESIGN.md` ✓

---

## Mental Model Summary

### For Developers
- Original artifact file is truth
- Documents table is authoritative inventory
- Everything else is optional enrichment

### For Operators
- Missing thumbnail = refresh browser
- Missing embedding = expected until computed
- Missing OCR = expected until computed
- Only original file loss = corruption

### For AI Agents
- Artifact identity (path, sha256) = do not question
- Derived data paths = may be stale, regenerate if needed
- Database presence ≠ filesystem presence for optional data

### For Future Plugins
- All plugin output is optional
- Plugin enabled ≠ dependencies installed (check runtime)
- Plugin output loss = cache miss, not corruption

---

## Appendix: Audit Methodology

### Files Examined
All `.md` files under `docs/` directory were scanned for:
- "corruption"
- "authoritative"
- "integrity"
- "derived artifact"
- "optional"
- "cache"
- "persistence"
- "recovery"

### Keyword Analysis
Files containing keywords were manually reviewed for:
1. Correct usage per architecture principles
2. Consistency with other documentation
3. Potential for confusion or hallucination

### Runtime-First Check
Configuration files and documentation were checked for assumptions about:
- Mount existence (configuration ≠ runtime)
- Dependency installation (enabled ≠ available)
- Database sync (metadata ≠ filesystem)

---

*Audit completed: 2026-07-06*
