# Architectural Audit — 2026-07

**Date:** 2026-07-01
**Previous Audit:** 2026-06-30
**Scope:** Librarian codebase (artifact ingestion platform)
**Type:** Post-Refactor Follow-up Audit

---

## Executive Summary

This audit re-evaluates the findings from the 2026-06 architectural audit against the current repository state. Significant architectural progress has been made since the previous audit, with 8 of 12 planned refactors completed.

### Status Distribution

| Category | Count |
|----------|-------|
| **Resolved** | 5 findings |
| **Partially Resolved** | 4 findings |
| **Still Open** | 2 findings |
| **Superseded** | 1 finding |

### Completed Refactor Plans

| Plan | Status | Resolution |
|------|--------|------------|
| P1 — Consolidate Ingestion Paths | ✅ Completed | Legacy ingestion removed |
| P3 — Enforce Backend Interface | ✅ Completed | ABC + validation added |
| P5 — Add Worker Abstract Base | ✅ Completed | BaseWorker ABC implemented |
| P6 — Add Integration Tests | ✅ Completed | test_pipeline*.py added |
| P7 — Add Missing DB Indexes | ✅ Completed | Migration 009 added |
| P9 — Standardise Environment Variables | ✅ Completed | Centralized in environment.py |
| P10 — Document Schema Migrations | ✅ Completed | CHANGELOG.md created |
| P11 — Remove JSON Persistence | ✅ Completed | Files deleted |
| P12 — ParserRegistry Extensions | ✅ Completed | get_supported_extensions() added |

### Remaining Refactor Plans

| Plan | Status | Notes |
|------|--------|-------|
| P2 — Unify Worker Runtime | ⚠️ Partially Complete | Duplication reduced but not unified |
| P4 — Replace Singleton with DI | 🔴 Still Open | High-risk, intentionally deferred |
| P8 — Fix Soft Delete | ⚠️ Partially Complete | Fallback still exists |

---

## 1. Detailed Finding Status

### V-001: Dual Ingestion Paths
**Original Status:** Open
**Current Status:** ✅ Resolved

**Evidence:**
- `ingestion/librarian.py` deleted
- `ingestion/persistence.py` deleted
- `run_initial_scan()` in `app_state.py` now uses `CollectionWatcher.scan_collection()` (lines 291-324)
- All ingestion routes through `discover_artifact()` path

**Implementation Reference:**
```python
# api/app_state.py:308
stats = self.watcher.scan_collection()
```

**Files Affected:**
- `api/app_state.py` — refactored `run_initial_scan()`
- `ingestion/collection_watcher.py` — `scan_collection()` is now the single ingestion entry point

---

### V-002: AppState Singleton Without Lifecycle Control
**Original Status:** Open
**Current Status:** ⚠️ Partially Resolved

**Evidence:**
- `AppState` class exists but still uses global `_state` singleton (line 393 in `app_state.py`)
- No FastAPI dependency injection implemented
- Module-level `get_app_state()`, `initialize_app()`, `shutdown_app()` still present

**Remaining Work:**
- P4 is intentionally last due to blast radius
- No dependency injection infrastructure implemented yet
- Routes still import from `api.app_state` module-level functions

**Files Affected:**
- `api/app_state.py`
- `api/routes/*.py`

---

### V-003: BackgroundJobProcessor Duplicates Worker Logic
**Original Status:** Open
**Current Status:** ⚠️ Partially Resolved

**Evidence:**
- Both `BackgroundJobProcessor` (lines 23-143 in `app_state.py`) and `Worker` (lines 25-237 in `workers/worker.py`) still exist independently
- Both implement: `register_handler()`, `start()`, `stop()`, `get_stats()`
- `run_worker()` in `workers/worker.py` uses `.process` method binding (line 257-262)
- `BackgroundJobProcessor` also uses `.process` method binding (lines 349-368)

**Progress Made:**
- Handler registration unified through `process()` method
- Both use same method signature convention now

**Remaining Work:**
- P2 (Unify Worker Runtime) not yet completed
- Need to choose canonical implementation and remove duplication
- Current state: Both implementations maintained for embedded vs standalone scenarios

**Files Affected:**
- `api/app_state.py` — `BackgroundJobProcessor`
- `workers/worker.py` — `Worker` class

---

### V-004: Missing Abstract Base for Job Handlers
**Original Status:** Open
**Current Status:** ✅ Resolved

**Evidence:**
- `workers/base.py` created with `BaseWorker` ABC
- All 6 worker classes now inherit from `BaseWorker`:
  - `ContentExtractor` (line 19)
  - `EntityExtractor`
  - `EventExtractor`
  - `LocationExtractor`
  - `EmbeddingGenerator`
  - `PhotoMetadataExtractor`
- All implement `process(job: dict) -> dict` method

**Files Affected:**
- `workers/base.py` — new file
- `workers/*.py` — updated to inherit from `BaseWorker`

---

### V-005: Soft Delete Incomplete
**Original Status:** Open
**Current Status:** ⚠️ Partially Resolved

**Evidence:**
- `mark_deleted()` exists in `StorageBackend` ABC with docstring (line 47-59 in `backend.py`)
- `collection_watcher._mark_deleted()` still has fallback (lines 238-249):
  ```python
  if hasattr(self.backend, 'mark_deleted'):
      self.backend.mark_deleted(artifact_path)
  elif hasattr(self.backend, 'save_document'):
      # Fallback: update exists_on_disk via save_document
  ```

**Remaining Work:**
- P8 not yet completed
- Fallback path still exists for backward compatibility
- No startup validation of `exists_on_disk` column

**Files Affected:**
- `ingestion/collection_watcher.py` — fallback still present
- `storage/postgres_backend.py` — implementation needs verification

---

### V-006: Hardcoded Library Root
**Original Status:** Open
**Current Status:** ✅ Resolved

**Evidence:**
- Environment variables centralized in `environment.py`
- `LIBRARIAN_LIBRARY_ROOT` is canonical with `LIBRARY_ROOT` as deprecated alias (lines 42-46)
- Startup logging of library root in `api/app.py` (line 37)
- Deprecation warning for legacy aliases

**Files Affected:**
- `environment.py` — centralized env var handling
- `api/app.py` — startup logging

---

### V-007: EvidenceBuilder Uses hasattr Checks
**Original Status:** Open
**Current Status:** ✅ Resolved

**Evidence:**
- `evidence/evidence_builder.py` no longer uses `hasattr` checks
- Direct calls to backend methods:
  ```python
  def get_documents(self, query):
      return self.backend.search_documents(query) or []
  ```
- `StorageBackend` ABC has `@abstractmethod` decorators on all required methods
- `validate_backend_instance()` added for runtime validation

**Files Affected:**
- `evidence/evidence_builder.py`
- `storage/backend.py`

---

## 2. Technical Debt Register Status

| ID | Item | Original Status | Current Status | Notes |
|----|------|-----------------|----------------|-------|
| TD-001 | Remove legacy pipeline | Open | ✅ Resolved | Files deleted |
| TD-002 | Consolidate Worker/BJP | Open | ⚠️ Partially Resolved | P2 pending |
| TD-003 | Add ABC/Protocol for StorageBackend | Open | ✅ Resolved | Implemented |
| TD-004 | Add ABC/Protocol for Workers | Open | ✅ Resolved | BaseWorker ABC |
| TD-005 | Remove JSON persistence | Open | ✅ Resolved | Files deleted |
| TD-006 | Document schema migrations | Open | ✅ Resolved | CHANGELOG.md |
| TD-007 | Add missing indexes | Open | ✅ Resolved | Migration 009 |
| TD-008 | Replace global AppState with DI | Open | 🔴 Still Open | P4 pending |
| TD-009 | Add exists_on_disk validation | Open | ⚠️ Partially Resolved | No startup check |
| TD-010 | Standardize env vars | Open | ✅ Resolved | Centralized |
| TD-011 | Add integration tests | Open | ✅ Resolved | 3 test files |
| TD-012 | ParserRegistry extensions | Open | ✅ Resolved | Method added |

---

## 3. Scalability Concerns Update

### Resolved

| Risk | Resolution |
|------|------------|
| **Missing evidence_lineage indexes** | ✅ Migration 009 adds `idx_evidence_lineage_created_at` |
| **Missing document_jobs indexes** | ✅ Migration 009 adds `idx_document_jobs_created_at` |

### Partially Resolved

| Risk | Status | Notes |
|------|--------|-------|
| **Connection pool exhaustion** | ⚠️ Still creates per-op connections | No pooling implemented |
| **Initial scan memory** | ⚠️ Better (single path) | No streaming, but removed legacy duplication |

### Still Open

| Risk | Status |
|------|--------|
| **Embedding storage bloat** | 🔴 TEXT storage, no pgvector |
| **Job queue contention** | 🔴 Single table, no partitioning |
| **Polling fallback** | 🔴 30-second polling still present |
| **No query timeout** | 🔴 No statement timeout |
| **Evidence lineage explosion** | 🔴 No pruning strategy |

---

## 4. Updated Architectural Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            CLIENTS                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Web    │  │ Desktop  │  │   CLI    │  │   MCP    │  │  Future  │  │
│  │   GUI    │  │   GUI    │  │   Tool   │  │  Client  │  │  Mobile  │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       └──────────────┴─────────────┴─────────────┴─────────────┘        │
│                              │ REST API (stable contract)                 │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────────────┐
│                         Librarian API                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Application                            │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────┐ │    │
│  │  │Questions │  │Collections│ │Pipeline  │  │Timeline  │  │Exp.│ │    │
│  │  │  Route   │  │  Route   │  │  Route   │  │  Route   │  │orer│ │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────┘ │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                               │                                           │
│  ┌─────────────────────────────┴─────────────────────────────────────┐    │
│  │                      AppState (Global Singleton)                    │    │
│  │  ⚠️ PENDING: Replace with DI (P4)                                   │    │
│  │  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐  │    │
│  │  │   Backend    │  │ Collection     │  │  BackgroundJob       │  │    │
│  │  │  (PostgreSQL)│  │   Watcher     │  │  Processor           │  │    │
│  │  │  ✅ ABC+Val.  │  │  ✅ Single     │  │  ⚠️ Duplicate Worker │  │    │
│  │  └──────────────┘  └────────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────────────┐
│                    INGESTION LAYER                                        │
│  ✅ CONSOLIDATED — Single Path                                             │
│  ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────────┐  │
│  │ CollectionWatcher│───▶│ ParserRegistry  │───▶│  scan_collection()  │  │
│  │ (inotify/polling)│    │  (extension     │    │  ✅ Single Entry Pt  │  │
│  └──────────────────┘    │   routing)      │    └─────────────────────┘  │
│                           └─────────────────┘              │               │
└──────────────────────────────────────────────────────────────┼─────────────┘
                                                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       WORKERS LAYER                                      │
│  ✅ BaseWorker ABC — All extractors inherit                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │
│  │   Content      │  │    Entity      │  │    Event       │           │
│  │   Extractor    │  │   Extractor    │  │   Extractor    │           │
│  │  ✅ BaseWorker │  │  ✅ BaseWorker │  │  ✅ BaseWorker │           │
│  └────────────────┘  └────────────────┘  └────────────────┘           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │
│  │   Location     │  │   Embedding     │  │    Photo       │           │
│  │   Extractor    │  │   Generator    │  │   Metadata     │           │
│  │  ✅ BaseWorker │  │  ✅ BaseWorker │  │  ✅ BaseWorker │           │
│  └────────────────┘  └────────────────┘  └────────────────┘           │
│                                                                          │
│  ⚠️ Worker Runtime Duplication (P2 pending)                               │
│  ┌──────────────────────────┐  ┌──────────────────────────┐           │
│  │   BackgroundJobProcessor │  │   Worker (standalone)    │           │
│  │   (in api/app_state.py)  │  │   (in workers/worker.py) │           │
│  └──────────────────────────┘  └──────────────────────────┘           │
│                                                                          │
│  Job Queue (document_jobs table)                                        │
│  ✅ Migration 009 — Added indexes                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL CATALOG                                  │
│  ✅ Schema migrations fully documented in CHANGELOG.md                   │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  collections   │  │  documents     │  │ document_jobs  │            │
│  │                │  │  ✅ Artifact   │  │ ✅ Indexed     │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  evidence_      │  │  entities      │  │  events        │            │
│  │  lineage        │  │                │  │                │            │
│  │  ✅ Indexed     │  │                │  │                │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│  ...                                                                    
└─────────────────────────────────────────────────────────────────────────┘
                                       ▲
                                       │ Read-only mount
┌──────────────────────────────────────┼─────────────────────────────────────┐
│                         HOST FILESYSTEM                                  │
│                              /library                                     │
│                     ✅ Source of truth — never modified                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Remaining Work Summary

### High Priority (Critical Path)

| Item | Description | Prerequisite |
|------|-------------|--------------|
| P2 | Unify Worker Runtime | P5 ✅, P6 ✅ — ready to start |
| P4 | Replace Singleton with DI | High risk, planned last |

### Medium Priority

| Item | Description | Notes |
|------|-------------|-------|
| P8 | Fix Soft Delete | Fallback still exists |

### Low Priority / Long-term

| Item | Description |
|------|-------------|
| pgvector | Vector index for embeddings |
| Connection pooling | psycopg pool |
| Job partitioning | Queue scalability |
| Statement timeout | Query timeout |
| Evidence lineage pruning | Growth control |

---

## 6. Files Modified in Refactor Folder

See `/workspace/project/Librarian/refactor/README.md` for updated status.

### Summary of Changes Needed

1. **P1** — Mark Completed (✅ Done)
2. **P3** — Mark Completed (✅ Done)
3. **P5** — Mark Completed (✅ Done)
4. **P6** — Mark Completed (✅ Done)
5. **P7** — Mark Completed (✅ Done)
6. **P9** — Mark Completed (✅ Done)
7. **P10** — Mark Completed (✅ Done)
8. **P11** — Mark Completed (✅ Done)
9. **P12** — Mark Completed (✅ Done)
10. **P2** — Update to "In Progress" or "Partially Complete"
11. **P4** — Keep as "Planned" (intentionally deferred)
12. **P8** — Update to "Partially Complete"

---

*End of architectural audit update.*
