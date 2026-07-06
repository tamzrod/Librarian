# Librarian Documentation Terminology Consistency Audit v2

**Document Type:** Terminology Consistency Audit  
**Status:** Complete  
**Date:** 2026-07-06  
**Reference Glossary:** [`docs/architecture/glossary.md`](https://github.com/username/librarian/blob/main/docs/architecture/glossary.md)  
**Audit Scope:** All documentation in `docs/` excluding source code, tests, and schema

---

## Executive Summary

This audit verifies that all documentation uses terminology defined in the Architecture Glossary. The audit examines corruption terminology, authority terminology, persistence terminology, integrity terminology, recovery terminology, runtime truth terminology, plugin terminology, and general terminology drift.

**Overall Assessment:** Documentation is largely consistent with the glossary. Minor terminology drift was identified in specific contexts.

---

## Audit Methodology

### Documents Reviewed (30 files)

| Category | Files |
|----------|-------|
| Architecture | `glossary.md`, `artifact-lifecycle.md`, `derived-artifact-contract.md`, `storage-lifecycle-matrix.md`, `architectural-audit-2026-06.md`, `architectural-audit-2026-07.md` |
| Operations | `deployment-lifecycle-audit.md`, `derived-artifact-recovery.md`, `plugin-dependency-infrastructure.md` |
| Plugins | `README.md`, `plugin-development-guide.md`, `plugin-states.md`, `dependency-management.md` |
| Audits | `documentation-consistency-audit.md` |
| Dashboard | `artifact-explorer.md`, `dashboard-architecture.md`, `evidence-timeline.md`, `TRACE-DESIGN.md` |
| ADRs | `0002-catalog-database-selection.md`, `0003-primary-language-selection.md`, `0005-single-library-model.md` |

### Terms Searched

- `corrupt`, `corruption`
- `integrity`
- `recovery`, `recover`
- `authoritative`, `authority`
- `evidence`
- `persistent`, `persistence`
- `cache miss`
- `regeneration`, `regenerate`
- `enrichment`, `enrich`
- `runtime truth`

---

## Audit Category Results

### Category 1: Corruption Terminology

**Definition (Glossary):** Corruption = Loss, modification, or inconsistency of authoritative evidence. Only evidence can be corrupted. Missing thumbnails/embeddings/OCR = cache miss, NOT corruption.

**Status:** ✅ COMPLIANT

Most documentation correctly distinguishes between corruption (evidence only) and cache miss (optional data). Examples of correct usage:

| Document | Correct Usage Found |
|----------|---------------------|
| `glossary.md` | "Only evidence can be corrupted. Optional data can only have cache misses." |
| `derived-artifact-contract.md` | "Missing embedding = expensive cache miss (NOT corruption)" |
| `storage-lifecycle-matrix.md` | "Missing these is always a cache miss, NEVER corruption" |
| `derived-artifact-recovery.md` | "This is NOT repairing corruption. This is requeuing cache misses." |
| `artifact-lifecycle.md` | "Missing optional data (embedding, OCR, thumbnail) is ALWAYS a cache miss, NEVER corruption." |

---

### Category 2: Authority Terminology

**Definition (Glossary):** Authoritative = Only the original artifact and its identity. Optional data (thumbnails, OCR, embeddings, enrichments) has authority level NONE.

**Status:** ✅ COMPLIANT

Documentation consistently identifies authoritative vs optional data:

| Document | Authority Statement |
|----------|---------------------|
| `glossary.md` | "Evidence is the only thing that can be corrupted." |
| `artifact-lifecycle.md` | "Artifact is authoritative." |
| `derived-artifact-contract.md` | "Artifact is authoritative. Everything else is optional." |
| `storage-lifecycle-matrix.md` | "Authority: OPTIONAL (cache miss, not corruption)" |

No authority leaks detected where optional data is incorrectly elevated to authoritative status.

---

### Category 3: Persistence Terminology

**Definition (Glossary):** Persistence ≠ Authority. Evidence persists permanently; cache may or may not persist.

**Status:** ⚠️ MINOR ISSUE IDENTIFIED

| Document | Finding | Severity |
|----------|---------|----------|
| `plugin-dependency-infrastructure.md:231` | "Can be safely cleared if corrupted" — "corrupted" should be "cleared" or "invalidated" | Informational |

**Analysis:** This phrase refers to plugin cache being cleared, not corruption. The term "corrupted" is used loosely here. Per the glossary, plugin cache loss = cache miss, not corruption.

---

### Category 4: Integrity Terminology

**Definition (Glossary):** Integrity applies to evidence only (SHA256 verification, file existence). Optional data does not require integrity checking.

**Status:** ✅ COMPLIANT

Documentation correctly applies integrity only to evidence:

| Document | Correct Usage |
|----------|---------------|
| `glossary.md` | "Integrity Does NOT Apply To: Thumbnails, Embeddings, OCR results" |
| `storage-lifecycle-matrix.md` | "No integrity audits required" (for optional data) |
| `derived-artifact-contract.md` | Lists SHA256 under evidence, not under optional data |

---

### Category 5: Recovery Terminology

**Definition (Glossary):** Recovery = Bulk efficient recreation of optional data (convenience). Regeneration = Individual recreation. Recovery ≠ Corruption repair.

**Status:** ✅ COMPLIANT

Documentation correctly distinguishes recovery from corruption repair:

| Document | Correct Distinction |
|----------|---------------------|
| `derived-artifact-recovery.md` | "Recovery framework exists for EFFICIENCY, not because it's corruption." |
| `derived-artifact-contract.md` | "Generation cost changes recovery strategy." |
| `glossary.md` | "Recovery is NOT: Corruption repair, Evidence restoration" |

---

### Category 6: Runtime Truth Terminology

**Definition (Glossary):** Runtime truth (docker inspect, docker logs, actual system state) overrides configuration assumptions.

**Status:** ✅ COMPLIANT

| Document | Runtime Truth Reference |
|----------|------------------------|
| `glossary.md` | Priority order: docker inspect > database > filesystem > configuration |
| `documentation-consistency-audit.md` | "Runtime state is authoritative over configuration - docker inspect > docker-compose" |

No problematic language found where configuration is incorrectly assumed to guarantee runtime behavior.

---

### Category 7: Plugin Terminology

**Definition (Glossary):** Plugin outputs are optional enrichments. Plugin failures do not invalidate evidence. Plugin output loss = cache miss.

**Status:** ✅ COMPLIANT

| Document | Correct Plugin Terminology |
|----------|---------------------------|
| `plugin-development-guide.md:27` | "Losing the output is a cache miss (NOT corruption)" |
| `plugin-development-guide.md:31` | "Must implement integrity auditing" (for Tier 1A derived artifacts) |
| `plugin-development-guide.md:44` | "NO integrity auditing" (for Tier 1B disposable cache) |
| `object-detection/README.md:61` | "No plugin is authoritative. Conflicting results are acceptable." |

---

### Category 8: Terminology Drift Detection

**Search Terms:** `corrupt`, `corruption`, `repair`, `restore`, `recover`, `integrity`, `persistence`, `evidence`, `authoritative`

**Status:** ✅ MINOR ISSUES ONLY

#### Finding 1: API Evidence Endpoint Naming

| Field | Analysis | Recommendation |
|-------|----------|----------------|
| `/questions/{id}/evidence` endpoint | The API uses "evidence" for query results, which is architecturally correct — these are assembled evidence packages derived from authoritative artifacts | ✅ Acceptable usage |

#### Finding 2: "Evidence" in Dashboard

| Location | Usage | Analysis |
|----------|-------|----------|
| `dashboard/artifact-explorer.md` | "browsing evidence" | ✅ Correct — browsing artifacts which are evidence |
| `dashboard/evidence-timeline.md` | "How did the evidence evolve?" | ✅ Correct — temporal view of artifacts |
| `dashboard/dashboard-architecture.md` | "primary workspace for browsing and analyzing evidence" | ✅ Correct |

#### Finding 3: Parser Error Description

| Document | Finding | Classification |
|----------|---------|----------------|
| `architectural-audit-2026-06.md:521` | "Parser errors corrupt metadata" | ⚠️ Ambiguous language |

**Analysis:** This phrase appears in a risk table describing that parser failures don't mark which stage failed. The word "corrupt" is used informally to mean "leave in error state," not technically "corruption" per the glossary. This is acceptable informal usage.

**Recommendation:** Consider rephrasing to "Parser errors set status: FAILED without marking which stage failed" for clarity.

---

## Findings Summary

### By Classification

| Classification | Count | Status |
|---------------|-------|--------|
| Terminology Drift | 1 | Informational |
| Glossary Violation | 0 | None |
| Ambiguous Language | 1 | Informational |
| Authority Leak | 0 | None |

### By Severity

| Severity | Count | Description |
|----------|-------|-------------|
| Informational | 2 | Minor; no action required |
| Moderate | 0 | - |
| Major | 0 | - |

---

## Detailed Findings

### Finding 1: Plugin Cache Clearance Terminology

| Field | Value |
|-------|-------|
| **Document** | `docs/operations/plugin-dependency-infrastructure.md` |
| **Line** | 231 |
| **Classification** | Terminology Drift |
| **Severity** | Informational |

**Existing Text:**
```
4. Can be safely cleared if corrupted
```

**Recommended Text:**
```
4. Can be safely cleared if invalidated
```

**Rationale:** Per glossary, plugin cache is optional and cannot be "corrupted." Cache may be invalidated or stale, but this is not corruption. Clearance is routine maintenance, not corruption repair.

---

### Finding 2: Parser Error Risk Description

| Field | Value |
|-------|-------|
| **Document** | `docs/architecture/architectural-audit-2026-06.md` |
| **Line** | 521 |
| **Classification** | Ambiguous Language |
| **Severity** | Informational |

**Existing Text:**
```
| **Parser errors corrupt metadata** | Parser failure sets `status: FAILED` but doesn't mark which stage | Add `failed_at` timestamp; store parser name in error |
```

**Recommended Text:**
```
| **Parser errors leave ambiguous state** | Parser failure sets `status: FAILED` but doesn't mark which stage | Add `failed_at` timestamp; store parser name in error |
```

**Rationale:** "Corrupt" is used informally here to mean "leave in unclear state." The actual risk is insufficient diagnostic information, not actual data corruption per the glossary definition.

---

## Positive Observations

The audit found the following areas of excellent terminology consistency:

1. **Cache Miss vs Corruption** — Documents consistently distinguish between missing optional data (cache miss) and evidence loss (corruption)

2. **Authority Hierarchy** — Documentation correctly identifies artifacts as authoritative and all derived data as optional

3. **Recovery Philosophy** — The distinction between recovery (convenience) and regeneration (individual recreation) is consistently applied

4. **Integrity Scope** — Documentation correctly limits integrity terminology to evidence, not optional data

5. **Plugin Outputs** — Plugin documentation correctly identifies outputs as optional enrichments, not evidence

---

## Recommendations

### Priority 1: No Immediate Action Required

All findings are informational. No glossary violations were identified that would cause reader confusion about:
- What is authoritative
- What is optional
- What can be regenerated
- What constitutes corruption
- What constitutes recovery

### Optional Improvements

1. Consider updating `plugin-dependency-infrastructure.md:231` to use "invalidated" instead of "corrupted" for consistency
2. Consider updating `architectural-audit-2026-06.md:521` to use "ambiguous state" instead of "corrupt metadata"

---

## Success Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| What is authoritative | ✅ Clear | "Artifact is authoritative. Everything else is optional." |
| What is optional | ✅ Clear | "Authority: OPTIONAL (cache miss, not corruption)" |
| What can be regenerated | ✅ Clear | "Missing thumbnail = cheap cache miss" |
| What constitutes corruption | ✅ Clear | "Evidence is the only thing that can be corrupted" |
| What constitutes recovery | ✅ Clear | "Recovery framework exists for EFFICIENCY, not because it's corruption" |

---

## Conclusion

The Librarian documentation demonstrates strong terminology consistency with the Architecture Glossary. Minor terminology drift was identified in 2 locations, both of which are informational and do not affect the reader's ability to correctly understand authoritative vs optional data concepts.

**Audit Result:** ✅ PASS with Informational Notes

---

*Audit conducted against glossary version 1.0 (2026-07-06)*
