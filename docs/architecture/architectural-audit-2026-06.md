# Architectural Audit — 2026-06

**Date:** 2026-06-30
**Scope:** Librarian codebase (artifact ingestion platform)

---

## 1. Current Architecture Diagram

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
│  │  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐  │    │
│  │  │   Backend    │  │ Collection     │  │  BackgroundJob       │  │    │
│  │  │  (PostgreSQL)│  │   Watcher      │  │  Processor           │  │    │
│  │  └──────────────┘  └────────────────┘  └──────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────────────┐
│                    INGESTION LAYER                                        │
│  ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────────┐  │
│  │ CollectionWatcher│    │ ParserRegistry  │    │  CollectionWatcher  │  │
│  │ (inotify/polling)│───▶│  (extension     │───▶│  ._process_file()  │  │
│  └──────────────────┘    │   routing)      │    └─────────────────────┘  │
│         │                └─────────────────┘              │               │
│         │                                                ▼               │
│         │                         ┌──────────────────────────────┐       │
│         │                         │      PostgreSQL Catalog      │       │
│         │                         │  ┌────────────────────────┐  │       │
│         │                         │  │   discover_artifact()  │  │       │
│         │                         │  │   (immediate insert)   │  │       │
│         │                         │  └────────────────────────┘  │       │
│         │                         └──────────────────────────────┘       │
│         └──────────────────────────────────────────────────────────────▶ │
│                                      │                                     │
└──────────────────────────────────────┼─────────────────────────────────────┘
                                       ▼
┌──────────────────────────────────────┼─────────────────────────────────────┐
│                         PARSERS LAYER                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   JSON   │  │   YAML   │  │   CSV    │  │  Image   │  │  Python  │   │
│  │  Parser  │  │  Parser  │  │  Parser  │  │  Parser  │  │  Parser  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Text   │  │   XML    │  │   INI    │  │  TOML    │  │  Future  │   │
│  │  Parser  │  │  Parser  │  │  Parser  │  │  Parser  │  │  Parser  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       WORKERS LAYER                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │
│  │   Content      │  │    Entity      │  │    Event       │           │
│  │   Extractor    │  │   Extractor    │  │   Extractor    │           │
│  └────────────────┘  └────────────────┘  └────────────────┘           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐           │
│  │   Location     │  │   Embedding     │  │    Photo       │           │
│  │   Extractor    │  │   Generator    │  │   Metadata     │           │
│  └────────────────┘  └────────────────┘  └────────────────┘           │
│                                                                          │
│  Job Queue (document_jobs table)                                        │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Leased via claim_job()  │  Exponential backoff retry         │   │
│  │  Renewal via renew_lease()│  Recovery via recover_expired_leases│   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL CATALOG                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  collections   │  │  documents     │  │ document_jobs  │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  document_      │  │  entities      │  │  events        │            │
│  │  content        │  │                │  │                │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  locations      │  │  relationships │  │  document_     │            │
│  │                │  │                │  │  embeddings    │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  evidence_      │  │  plugin_types  │  │  schema_       │            │
│  │  lineage        │  │                │  │  migrations    │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
                                       ▲
                                       │ Read-only mount
┌──────────────────────────────────────┼─────────────────────────────────────┐
│                         HOST FILESYSTEM                                  │
│                              /library                                     │
│                     (Source of truth — never modified)                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Source of Truth Hierarchy

| Level | System | Description |
|-------|--------|-------------|
| **1 (Immutable)** | Host Filesystem | `/library` volume — original files. Librarian never writes here. |
| **2 (Immutable)** | Document Identity | `documents.id` — assigned once, never changes, never reused |
| **3 (Declarative)** | Document Records | `documents` table — path, extension, hash, metadata |
| **4 (Derived)** | Extracted Content | `document_content`, entities, events, locations, embeddings |
| **5 (Provenance)** | Evidence Lineage | `evidence_lineage` table — extraction provenance |

**Key invariants (per RULES.md):**
- Filesystem is the source of truth (Rule 1)
- Original files must never be modified (Rule 2)
- Reindexing must always be possible (Rule 4)
- The catalog must remain organized even when the filesystem is not (Rule 8)

---

## 3. Regeneratable vs Persistent Data Classification

### Persistent (Never Deleted)

| Data | Storage | Rationale |
|------|---------|-----------|
| Artifact identity | `documents.id` | Immutable identifier, never recycled |
| Artifact path | `documents.path` | Source of truth reference |
| Artifact hashes | `documents.sha256` | Integrity verification |
| File metadata | `documents.modified_time`, `file_size` | Audit trail |
| Soft-deleted records | `documents.exists_on_disk = false` | "Discovery precedes understanding" |
| Deleted timestamps | `documents.deleted_at` | Historical tracking |
| Entity definitions | `entities` table | Extracted knowledge |
| Event definitions | `events` table | Extracted knowledge |
| Location definitions | `locations` table | Extracted knowledge |
| Migration history | `schema_migrations` | Audit and rollback capability |

### Regeneratable (Can Be Reconstructed)

| Data | Source | Method |
|------|--------|--------|
| Content extraction | Filesystem | Workers re-read files |
| Entity extraction | `document_content` | Workers re-analyze |
| Event extraction | `document_content` | Workers re-parse timestamps |
| Location extraction | `document_content` | Workers re-parse coordinates |
| Embeddings | `document_content` | Workers re-generate vectors |
| Parser metadata | Filesystem + Parsers | Workers re-parse |
| Job queue state | `document_jobs` | Re-created on re-indexing |

### Ambiguous / At Risk

| Data | Concern |
|------|---------|
| `document_jobs` | May contain transient state (attempt counts, errors). Partial reprocessing may be needed. |
| `evidence_lineage` | If content is regenerated with different parameters, lineage becomes stale. |
| Photo EXIF data | Not regeneratable if source file loses metadata. |

---

## 4. Lifecycle Definitions

### Document Lifecycle (states defined in `postgres_backend.py`)

```
┌─────────────┐
│  DISCOVERED │  File detected, metadata not yet indexed
└──────┬──────┘
       │ METADATA_INDEXED (parser classified)
       ▼
┌───────────────────┐
│  METADATA_INDEXED │  Metadata extracted, content not yet processed
└──────┬────────────┘
       │ CONTENT_EXTRACTED (ContentExtractor)
       ▼
┌────────────────────┐
│  CONTENT_EXTRACTED │  Text content extracted
└──────┬─────────────┘
       │ ENTITY_EXTRACTED (EntityExtractor)
       ▼
┌─────────────────┐
│ ENTITY_EXTRACTED │  Entities identified
└──────┬──────────┘
       │ RELATIONSHIPS_BUILT
       ▼
┌─────────────────────┐
│  RELATIONSHIPS_BUILT │  Relationships mapped
└──────┬──────────────┘
       │ EMBEDDED (EmbeddingGenerator)
       ▼
┌─────────┐
│ EMBEDDED │  Vector embeddings generated
└────┬────┘
     │ COMPLETE
     ▼
┌──────────┐
│ COMPLETE │  All processing stages complete
└──────────┘
     │ FAILED (any state can transition)
     ▼
┌────────┐
│ FAILED │  Processing failed after max retries
└────────┘
```

**Valid Transitions** (from `postgres_backend.py`):

```python
VALID_TRANSITIONS = {
    DISCOVERED: {METADATA_INDEXED, FAILED},
    METADATA_INDEXED: {CONTENT_EXTRACTED, FAILED},
    CONTENT_EXTRACTED: {ENTITY_EXTRACTED, FAILED},
    ENTITY_EXTRACTED: {RELATIONSHIPS_BUILT, FAILED},
    RELATIONSHIPS_BUILT: {EMBEDDED, FAILED},
    EMBEDDED: {COMPLETE, FAILED},
    COMPLETE: {FAILED},           # Can fail after completion
    FAILED: {METADATA_INDEXED},   # Retry path
}
```

### Job Lifecycle

```
QUEUED ──▶ IN_PROGRESS ──▶ COMPLETED
              │
              │ (error, retries exhausted)
              ▼
        FAILED_PERMANENT

QUEUED ──▶ CANCELLED
```

### Artifact Inventory Model

Per `artifact-lifecycle.md`:
- **Discovery precedes understanding** — a file exists immediately upon discovery
- **Parser availability does not affect existence** — unknown formats are first-class citizens
- **Understanding is optional** — artifacts without parsers remain discoverable

---

## 5. Component Responsibilities

### Storage Layer

| Component | File | Responsibility |
|-----------|------|----------------|
| `StorageBackend` | `storage/backend.py` | Abstract interface for persistence |
| `PostgresBackend` | `storage/postgres_backend.py` | PostgreSQL implementation of StorageBackend |
| `MigrationManager` | `storage/migration_manager.py` | Schema versioning and upgrades |

### Ingestion Layer

| Component | File | Responsibility |
|-----------|------|----------------|
| `CollectionWatcher` | `ingestion/collection_watcher.py` | Filesystem monitoring (inotify/polling), file change detection |
| `ParserRegistry` | `registry/parser_registry.py` | Extension-based parser routing |
| `Scanner` | `ingestion/scanner.py` | Directory traversal and file metadata |
| `Indexer` | `ingestion/indexer.py` | Document normalization for indexing |
| `Librarian` | `ingestion/librarian.py` | Legacy ingestion orchestrator |
| `Persistence` | `ingestion/persistence.py` | JSON snapshot save/load (legacy) |

### Parsers

| Component | File | Handled Types |
|-----------|------|---------------|
| `JsonParser` | `parsers/json_parser.py` | `.json` |
| `YamlParser` | `parsers/yaml_parser.py` | `.yaml`, `.yml` |
| `CsvParser` | `parsers/csv_parser.py` | `.csv` |
| `XmlParser` | `parsers/xml_parser.py` | `.xml` |
| `IniParser` | `parsers/ini_parser.py` | `.ini`, `.cfg` |
| `TomlParser` | `parsers/toml_parser.py` | `.toml` |
| `PythonParser` | `parsers/python_parser.py` | `.py` |
| `TextParser` | `parsers/text_parser.py` | `.txt`, `.md` |
| `ImageParser` | `parsers/image_parser.py` | `.jpg`, `.png`, `.gif`, etc. |

### Workers

| Component | File | Job Type |
|-----------|------|----------|
| `ContentExtractor` | `workers/content_extractor.py` | `extract_text` |
| `EntityExtractor` | `workers/entity_extractor.py` | `extract_entities` |
| `EventExtractor` | `workers/event_extractor.py` | `extract_events` |
| `LocationExtractor` | `workers/location_extractor.py` | `extract_locations` |
| `EmbeddingGenerator` | `workers/embedding_generator.py` | `generate_embeddings` |
| `PhotoMetadataExtractor` | `workers/photo_metadata_extractor.py` | `extract_photo_metadata` |

### Query Layer

| Component | File | Responsibility |
|-----------|------|----------------|
| `QueryPlanner` | `core/query_planner.py` | Regex-based intent detection |
| `QueryExecutor` | `core/query_executor.py` | Evidence assembly |
| `EvidenceBuilder` | `evidence/evidence_builder.py` | Evidence package construction |
| `AnswerSynthesizer` | `core/answer_synthesizer.py` | Response generation |
| `ask()` | `core/ask.py` | End-to-end query pipeline |

### API Layer

| Component | File | Responsibility |
|-----------|------|----------------|
| `app.py` | `api/app.py` | FastAPI application, routes |
| `app_state.py` | `api/app_state.py` | Global singleton state management |
| `BackgroundJobProcessor` | `api/app_state.py` | In-process job execution |
| Route modules | `api/routes/*.py` | Resource endpoints |

### Graph Analysis

| Component | File | Responsibility |
|-----------|------|----------------|
| `DependencyGraph` | `graph/dependency_graph.py` | Import relationship mapping |
| `DependencyIndexer` | `graph/dependency_indexer.py` | Python import extraction |
| `RepositoryHotspots` | `graph/repository_hotspots.py` | High-coupling detection |
| `RepositorySummary` | `graph/repository_summary.py` | Codebase overview |

---

## 6. Architectural Violations Discovered

### V-001: Dual Ingestion Paths
**Severity:** Medium
**Location:** `ingestion/librarian.py`, `ingestion/collection_watcher.py`

Two distinct ingestion pipelines exist:
1. **Legacy path:** `Librarian.ingest()` → `parse_file()` → JSON persistence
2. **Current path:** `CollectionWatcher` → `discover_artifact()` → PostgreSQL

`app_state.py:run_initial_scan()` uses the legacy path, then duplicates into PostgreSQL via `save_document()`. This creates inconsistency and doubles processing.

**Impact:** Initial scan bypasses the artifact inventory model; duplicate entry points.

---

### V-002: AppState Singleton Without Lifecycle Control
**Severity:** Medium
**Location:** `api/app_state.py`

`AppState` is a global singleton (`_state`) managed via module-level functions. This pattern:
- Creates hidden global state
- Makes testing difficult
- Prevents multi-library deployments
- Couples all components to a single backend instance

**Impact:** Violates component replaceability principle; prevents horizontal scaling.

---

### V-003: BackgroundJobProcessor Duplicates Worker Logic
**Severity:** Medium
**Location:** `api/app_state.py:BackgroundJobProcessor`, `workers/worker.py:Worker`

`BackgroundJobProcessor` reimplements the `Worker` class with near-identical logic:
- Lease management
- Job claiming
- Handler registration
- Retry logic
- Graceful shutdown

Both exist but neither is clearly designated as the canonical implementation.

**Impact:** Code duplication, divergent behavior over time.

---

### V-004: Missing Abstract Base for Job Handlers
**Severity:** Low
**Location:** `workers/*.py`

Worker classes (`ContentExtractor`, `EntityExtractor`, etc.) lack a common interface. Each implements a custom `extract_*` method signature. The `run_worker()` function instantiates these directly and extracts the method as a bound callable.

**Impact:** Tight coupling between worker initialization and handler registration; fragile registration pattern.

---

### V-005: Soft Delete Incomplete
**Severity:** Low
**Location:** `storage/postgres_backend.py`, `ingestion/collection_watcher.py`

`mark_deleted()` exists in `StorageBackend` interface but may not be implemented in all code paths. `collection_watcher._mark_deleted()` has a fallback that sets `exists_on_disk` but the column may not exist in all schema versions.

**Impact:** Deleted file tracking may fail silently.

---

### V-006: Hardcoded Library Root
**Severity:** Low
**Location:** `api/app.py`, `api/app_state.py`

`LIBRARY_ROOT = "/library"` is hardcoded with an environment variable fallback. The environment variable name (`LIBRARIAN_LIBRARY_ROOT`) is inconsistent with potential naming conventions elsewhere.

**Impact:** Deployment flexibility limited; path assumptions embedded in code.

---

### V-007: EvidenceBuilder Uses hasattr Checks
**Severity:** Low
**Location:** `evidence/evidence_builder.py`

```python
if hasattr(self.backend, 'search_documents'):
    return self.backend.search_documents(query) or []
return []
```

This pattern assumes `EvidenceBuilder` may be used with backends lacking these methods. This defensive coding masks interface violations rather than enforcing contracts.

**Impact:** Silent failures when backend is incomplete; hard to diagnose.

---

## 7. Technical Debt Register

| ID | Item | Location | Effort | Risk |
|----|------|----------|--------|------|
| TD-001 | Remove `ingestion/librarian.py` legacy pipeline | `ingestion/librarian.py` | Medium | Low |
| TD-002 | Consolidate `Worker` and `BackgroundJobProcessor` | `workers/worker.py`, `api/app_state.py` | Medium | Medium |
| TD-003 | Add ABC/Protocol for `StorageBackend` | `storage/backend.py` | Low | Low |
| TD-004 | Add ABC/Protocol for Worker handlers | `workers/*.py` | Low | Low |
| TD-005 | Remove `ingestion/persistence.py` JSON snapshot code | `ingestion/persistence.py` | Low | Low |
| TD-006 | Document schema version 1-4 migration behavior | `storage/migrations/` | Low | Medium |
| TD-007 | Add missing indexes for `evidence_lineage` | `storage/migrations/schema.sql` | Low | Medium |
| TD-008 | Replace global `AppState` singleton with DI | `api/app_state.py` | High | Medium |
| TD-009 | Add `exists_on_disk` column validation at startup | `storage/postgres_backend.py` | Low | Low |
| TD-010 | Standardize environment variable naming | `api/app.py`, `api/app_state.py` | Low | Low |
| TD-011 | Add integration tests for full ingestion pipeline | `tests/` | Medium | Medium |
| TD-012 | Add `ParserRegistry.get_supported_extensions()` method | `registry/parser_registry.py` | Low | Low |

---

## 8. Recommended Refactors

### Priority 1: Consolidate Ingestion Paths

**Rationale:** Two parallel ingestion pipelines create confusion and maintenance burden.

**Actions:**
1. Deprecate `Librarian.ingest()` and `ingestion/persistence.py`
2. Route all initial scanning through `CollectionWatcher._scan_and_detect_changes()`
3. Ensure `run_initial_scan()` uses `discover_artifact()` path
4. Remove `parse_file()` calls from initial scan flow

**Estimated effort:** Medium

---

### Priority 2: Unify Worker Runtime

**Rationale:** Duplicate implementations of job processing create divergence risk.

**Actions:**
1. Extract common `WorkerRuntime` ABC or Protocol
2. Make `BackgroundJobProcessor` delegate to standalone `Worker` implementation
3. Or: Deprecate standalone `Worker` in favor of `BackgroundJobProcessor` if embedded execution is preferred

**Estimated effort:** Medium

---

### Priority 3: Enforce Backend Interface

**Rationale:** `hasattr` checks in `EvidenceBuilder` mask incomplete implementations.

**Actions:**
1. Add `@abstractmethod` decorators to `StorageBackend`
2. Replace `hasattr` checks with proper interface validation
3. Add runtime check that backend implements required methods

**Estimated effort:** Low

---

### Priority 4: Replace Singleton with Dependency Injection

**Rationale:** Global state prevents testability and multi-library deployments.

**Actions:**
1. Refactor `AppState` to be instantiable
2. Pass `AppState` instance via FastAPI dependency injection
3. Remove module-level `_state` variable

**Estimated effort:** High (requires API route refactoring)

---

## 9. Risks at Scale

### Scalability Concerns

| Risk | Description | Mitigation |
|------|-------------|------------|
| **Job queue contention** | Single `document_jobs` table with single `status` index; multiple workers will contend on claiming jobs | Implement job partitioning by `job_type` or `document_id` hash range |
| **Embedding storage bloat** | `document_embeddings.embedding` stores vectors as TEXT (JSON-serialized); no vector index (pgvector) | Plan for pgvector integration before scaling to millions of documents |
| **Initial scan on large libraries** | `Librarian.ingest()` loads entire library into memory as `self.index` | Stream processing; batched database writes |
| **Evidence lineage explosion** | `evidence_lineage` grows O(entities × documents) without cleanup | Add pruning/archival strategy for stale lineages |
| **Polling fallback** | If watchdog fails, 30-second polling interval on large filesystems | Implement batching/grouping of polling events |
| **Connection pool exhaustion** | `_get_connection()` creates new connection per operation | Implement connection pooling (psycopg pool) |
| **No query timeout** | Long-running queries can block workers | Add statement timeout configuration |

### Operational Concerns

| Risk | Description | Mitigation |
|------|-------------|------------|
| **Schema migration on large DB** | Migration 005 adds columns without concurrent index builds | Plan maintenance windows; use `CREATE INDEX CONCURRENTLY` |
| **Worker crash during enrichment** | Lease recovery is eventual; jobs may be delayed | Monitor `document_jobs.lease_until`; alerting on stale leases |
| **Parser errors corrupt metadata** | Parser failure sets `status: FAILED` but doesn't mark which stage | Add `failed_at` timestamp; store parser name in error |
| **No retry on initial scan failures** | `run_initial_scan()` fails silently on individual documents | Add retry queue for failed initial-indexed documents |

---

## 10. Long-Term Target Architecture

### Principles to Preserve

1. **Filesystem as immutable source of truth** — No write operations to library volume
2. **Artifact inventory model** — Discovery precedes understanding; unknown formats are first-class
3. **Reindexability** — All derived data can be regenerated from source files
4. **API-first design** — All operations via REST; GUI is disposable
5. **Replaceable components** — Abstract interfaces for backends, workers, parsers

### Proposed Evolution

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           API LAYER (Stable Contract)                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  REST API (FastAPI)                                              │    │
│  │  - Resource endpoints (collections, documents, entities, etc.)  │    │
│  │  - Query endpoint (/api/v1/questions)                           │    │
│  │  - Admin endpoints (migrations, health)                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER (Business Logic)                     │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │
│  │  Ingestion       │  │  Query         │  │  Migration             │  │
│  │  Service         │  │  Service       │  │  Service               │  │
│  │  - Discovery     │  │  - Planning    │  │  - Version tracking    │  │
│  │  - Enrichment    │  │  - Execution   │  │  - Rollback support    │  │
│  │  - Job Queue     │  │  - Synthesis   │  │                        │  │
│  └──────────────────┘  └────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       STORAGE ABSTRACTIONS                               │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │
│  │  Artifact        │  │  Evidence       │  │  Job                   │  │
│  │  Repository      │  │  Repository     │  │  Queue                 │  │
│  │  (Protocol)      │  │  (Protocol)     │  │  (Protocol)            │  │
│  └──────────────────┘  └────────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    IMPLEMENTATION LAYER                                  │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  PostgreSQL Backend (single implementation for v1)              │    │
│  │  - ArtifactRepository → documents table                        │    │
│  │  - EvidenceRepository → entities, events, locations tables     │    │
│  │  - JobQueue → document_jobs table                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      WORKER RUNTIME                                      │
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────────────┐  │
│  │  Content         │  │  Entity        │  │  Photo                 │  │
│  │  Extractor       │  │  Extractor     │  │  Metadata Extractor   │  │
│  │                  │  │                │  │                        │  │
│  │  (Plugin)        │  │  (Plugin)      │  │  (Plugin)             │  │
│  └──────────────────┘  └────────────────┘  └────────────────────────┘  │
│                                                                          │
│  Worker Registry (dynamic plugin loading)                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Changes from Current

| Aspect | Current | Target |
|--------|---------|--------|
| **Ingestion** | Dual paths (Librarian + CollectionWatcher) | Single CollectionWatcher path |
| **Worker runtime** | Embedded BackgroundJobProcessor + standalone Worker | Unified WorkerRuntime, pluggable |
| **Storage** | PostgresBackend class | ArtifactRepository, EvidenceRepository, JobQueue protocols |
| **State management** | Global AppState singleton | Dependency injection |
| **Enrichment** | Static worker registration | Dynamic plugin loading |
| **Vector storage** | TEXT (JSON serialized) | pgvector with HNSW indexing |

### Migration Path

1. **Phase 1:** Deprecate legacy ingestion (`Librarian.ingest()`)
2. **Phase 2:** Extract `WorkerRuntime` ABC, consolidate implementations
3. **Phase 3:** Replace `StorageBackend` with typed protocols
4. **Phase 4:** Replace global `AppState` with FastAPI dependency injection
5. **Phase 5:** Implement worker plugin registry for dynamic loading
6. **Phase 6:** Add pgvector for production-scale embedding queries

---

## Appendix: File Inventory

| Path | Lines | Purpose |
|------|-------|---------|
| `api/app.py` | ~500 | FastAPI application |
| `api/app_state.py` | ~410 | Global state management |
| `storage/postgres_backend.py` | ~1000+ | Database implementation |
| `storage/migration_manager.py` | ~450 | Schema versioning |
| `ingestion/collection_watcher.py` | ~280 | Filesystem monitoring |
| `workers/worker.py` | ~285 | Job processor |
| `core/query_planner.py` | ~120 | Intent detection |
| `core/ask.py` | ~40 | Query pipeline |
| `evidence/evidence_builder.py` | ~75 | Evidence assembly |

---

*End of architectural audit.*
