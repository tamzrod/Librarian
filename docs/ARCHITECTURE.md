# Data Explorer Architecture

**Version**: 2.0  
**Status**: Architecture Specification  
**Scope**: Data Explorer Workspace

---

## Overview

Data Explorer is a specialized investigation workspace within Librarian. It provides read-only access to the reconstructed evidence catalog, enabling users to browse, inspect, and verify evidence and artifacts.

### Designation

Data Explorer is modeled after familiar operational inspection tools:

- **Grafana Explore** — ad-hoc querying and inspection
- **InfluxDB Data Explorer** — time-series data investigation
- **Kibana Discover** — document exploration and search

---

## Investigation Workspaces

Librarian Investigation consists of multiple sibling workspaces, each serving a distinct purpose:

```
┌─────────────────────────────────────────────────────────────┐
│                   Librarian Investigation                     │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Explorer   │  │    Trace    │  │  Entities   │        │
│  │  (primary)   │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │Relationships│  │Data Explorer│                          │
│  │             │  │ (specialized)│                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

| Workspace | Purpose |
|-----------|---------|
| **Explorer** | Primary investigation interface; high-level analysis and navigation |
| **Trace** | Tracks the provenance and derivation of evidence |
| **Entities** | Browses and manages extracted entities (people, organizations, devices) |
| **Relationships** | Explores connections between entities |
| **Data Explorer** | Lowest-level workspace; inspects raw evidence and artifacts |

### Workspace Hierarchy

Investigation workspaces operate at different abstraction levels:

```
HIGH LEVEL (Analysis Focus)
├── Explorer     — Primary investigation workspace
├── Trace        — Provenance and derivation tracking
├── Entities     — Named entity management
└── Relationships — Entity connections
        │
        ▼
LOW LEVEL (Evidence Focus)
└── Data Explorer — Evidence catalog inspection
```

**Data Explorer** is the lowest-level workspace. It exposes the catalog as-is without transformation, serving users who need to verify evidence rather than perform analysis.

---

## Data Explorer Responsibilities

### What Data Explorer SHALL Do

Data Explorer is responsible for:

| Responsibility | Description |
|---------------|-------------|
| **Browse collections** | Navigate artifact groupings |
| **Browse artifacts** | List and filter indexed files |
| **Browse evidence** | Access original artifacts and their records |
| **Inspect metadata** | View extracted file properties |
| **Inspect derived artifacts** | Examine enrichment results (EXIF, OCR, embeddings) |
| **Inspect extraction results** | Review entity, event, and location extractions |
| **Inspect relationships** | View connections attached to an artifact |
| **Navigate evidence** | Traverse the reconstructed catalog |

### What Data Explorer SHALL NOT Do

| Exclusion | Rationale |
|-----------|-----------|
| Perform investigation analysis | Reserved for Explorer |
| Display investigation timelines | Reserved for Trace |
| Replace Trace | Trace serves provenance tracking |
| Replace Entities | Entities serves entity management |
| Replace Relationships | Relationships serves connection exploration |
| Expose PostgreSQL terminology | Storage is abstracted |
| Expose SQL | Backend is encapsulated |
| Expose storage implementation | UI remains backend-agnostic |

---

## Architectural Principles

Data Explorer maintains the core Librarian philosophy:

| Principle | Application |
|-----------|-------------|
| **Filesystem Authoritative** | Original files are the source of truth |
| **Catalog Reconstructed** | Index rebuilt from filesystem |
| **Read-Only** | No write operations in standard usage |
| **Storage Abstraction** | Backend encapsulated behind adapter |
| **Backend Independent** | UI unchanged when backend changes |
| **No PostgreSQL in UI** | Database terminology never exposed |

---

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Dashboard                               │
│                   (Frontend UI)                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Data Explorer                            │
│              (Frontend State Management)                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Explorer Service                          │
│              (API Routes / Business Logic)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend Adapter                             │
│            (Backend-Specific Query Translation)              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Catalog Backend                             │
│              (PostgreSQL, SQLite, DuckDB)                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Invariant

**The Dashboard never communicates directly with the catalog backend.**

All operations flow through the Explorer Service and Backend Adapter, ensuring:
1. Backend implementation is encapsulated
2. UI remains unchanged when backend changes
3. Multiple backends supported through adapter substitution

---

## Layer Responsibilities

| Layer | Responsibility |
|-------|---------------|
| **Dashboard** | Renders UI, manages user interaction |
| **Data Explorer** | Coordinates state between UI and API |
| **Explorer Service** | Exposes inspection operations via REST |
| **Backend Adapter** | Translates generic operations to backend queries |
| **Catalog Backend** | Persists and retrieves catalog data |

---

## Backend Adapter

The Backend Adapter translates generic inspection operations into backend-specific queries.

### Inspection Interface

```python
class ExplorerBackendAdapter(ABC):
    """Interface for catalog backend inspection operations."""
    
    @abstractmethod
    def list_objects(self, object_type: str, **filters) -> list[dict]:
        """List objects of a given type."""
        raise NotImplementedError()
    
    @abstractmethod
    def describe_object(self, object_id: int, object_type: str) -> dict:
        """Get detailed description of a specific object."""
        raise NotImplementedError()
    
    @abstractmethod
    def read_records(self, table: str, filters: dict = None) -> list[dict]:
        """Read records from a table or collection."""
        raise NotImplementedError()
    
    @abstractmethod
    def read_metadata(self, document_id: int) -> dict:
        """Read all metadata for a document."""
        raise NotImplementedError()
    
    @abstractmethod
    def read_statistics(self) -> dict:
        """Read system statistics and counts."""
        raise NotImplementedError()
```

### Operation Mapping

| Generic Operation | PostgreSQL | DuckDB | Elasticsearch |
|-------------------|------------|--------|---------------|
| `list_objects` | `SELECT` | `SELECT` | `_search` |
| `describe_object` | `SELECT WHERE id` | `SELECT WHERE id` | `_doc/id` |
| `read_records` | `SELECT * FROM` | `SELECT * FROM` | Index `_search` |
| `read_metadata` | JOIN on doc_id | JOIN on doc_id | Nested document |
| `read_statistics` | `COUNT(*)` queries | `SUMMARIZE` | Aggregations |

---

## API Design

### Endpoint Structure

```
GET  /api/v1/explorer/objects              # List available object types
GET  /api/v1/explorer/objects/{type}      # List objects of a type
GET  /api/v1/explorer/objects/{type}/{id} # Describe specific object
GET  /api/v1/explorer/records/{table}      # Read raw records
GET  /api/v1/explorer/metadata/{id}        # Read document metadata
GET  /api/v1/explorer/statistics           # Read system statistics
POST /api/v1/explorer/query                # Execute inspection query
```

### Response Format

```json
{
  "success": true,
  "data": [...],
  "metadata": {
    "backend_type": "postgresql",
    "execution_time_ms": 12,
    "row_count": 100
  }
}
```

---

## Deployment Model

Librarian is deployed via Docker Compose.

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                           │
│  ┌─────────────────┐  ┌─────────────────────────────────┐ │
│  │  Librarian API  │  │         Catalog Backend          │ │
│  │    (Port 8001)   │  │         (PostgreSQL)             │ │
│  └────────┬────────┘  └─────────────────────────────────┘ │
│           │                                                   │
│           │ /library (read-only volume)                      │
│           ↓                                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    Host Filesystem                        ││
│  │              /path/to/documents                          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Configuration

| Setting | Description |
|---------|-------------|
| Library root | Docker volume mapping (`/path/to/host:/library:ro`) |
| Catalog | Environment variable (`DATABASE_URL`) |
| API | Exposed on port 8001 |

### Single Library Design

- One library root per deployment
- One catalog per deployment
- Multiple Librarian instances for multiple libraries

---

## Directory Structure

```
Library Root (mounted volume)
├── documents/
│   ├── contracts/
│   │   └── abc_contract.pdf
│   └── invoices/
│       └── invoice_001.pdf
├── photos/
│   ├── 2026/
│   │   └── IMG_20260101.jpg
│   └── 2025/
└── notes/
    └── meeting_notes.md
```

### Exclusion Patterns

Globally configured patterns:
- `.git/` — Version control
- `node_modules/` — Dependencies
- Hidden files (`.` prefix)
- Large binary files (configurable threshold)

---

## Core Abstractions

| Abstraction | Description | Authority |
|-------------|-------------|-----------|
| **Artifact** | Original evidence file | Authoritative |
| **Document** | Indexed artifact with metadata | Authoritative |
| **Entity** | Named thing (person, company, location) | Derived |
| **Event** | Timestamped occurrence | Derived |
| **Location** | Geographic point or named place | Derived |
| **Evidence** | Artifact + identity combination | Authoritative |

### Authority Hierarchy

```
AUTHORITATIVE (Level 1)
├── Original artifact file
├── documents table row
├── sha256 hash
└── artifact identity
    Loss = CORRUPTION

OPTIONAL (Level 2)
├── Thumbnails, previews
├── Embeddings, OCR, object detection
├── EXIF enrichment, geolocation
└── Timeline events, entities
    Loss = CACHE MISS (not corruption)
```

---

## Design Goals

| Goal | Description |
|------|-------------|
| **Storage Agnostic** | UI operates through abstraction; no backend-specific logic |
| **Backend Replaceable** | New backends require only a new adapter |
| **Inspection Focused** | Read-first design; no write operations |
| **Minimal Assumptions** | Adapter avoids assuming SQL or specific languages |
| **Extensible** | Adapters plug in via dependency injection |
| **Safe** | Read-only by default; modifications require explicit opt-in |

---

## Non-Goals

| Non-Goal | Rationale |
|----------|-----------|
| Primary investigation interface | Explorer serves this purpose |
| Evidence analysis | Reserved for Explorer |
| Timeline display | Reserved for Trace |
| Entity management | Reserved for Entities |
| Relationship exploration | Reserved for Relationships |
| Database administration | pgAdmin, DBeaver are more appropriate |
| Schema modification | Migrations handle changes |

---

## Security Considerations

### Read-Only by Default

- No INSERT, UPDATE, or DELETE operations exposed
- All operations are audit-logged
- Administrative write access requires separate authentication

### Query Validation

```python
def execute_inspection_query(self, query: str, **params) -> dict:
    forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER']
    if any(keyword in query.upper() for keyword in forbidden):
        raise PermissionError("Write operations not permitted")
    
    timeout = "SET statement_timeout = '30s'"
    return self._execute(f"{timeout}; {query}", params)
```

### Access Control

- Disabled by default for production
- Restricted to authenticated operators
- Isolated from public-facing interfaces

---

## Future Extensibility

### Adding New Backends

1. Create adapter class implementing `ExplorerBackendAdapter`
2. Register adapter in backend configuration
3. Wire via dependency injection

No changes required to:
- API routes
- Frontend components
- Data models

---

## Summary

Data Explorer is the **lowest-level investigation workspace** in Librarian. It provides operational inspection capabilities for browsing and verifying the reconstructed evidence catalog.

### Key Points

| Point | Description |
|-------|-------------|
| **Position** | Specialized sibling workspace |
| **Purpose** | Inspection, validation, verification |
| **Abstraction** | UI never depends on backend |
| **Extensibility** | New backends via adapter substitution |

### Design Principles

1. **Storage agnostic** — UI never depends on backend implementation
2. **Backend replaceable** — Adapters encapsulate all backend logic
3. **Read-first** — Inspection focus; writes are administrative exceptions
4. **Specialized, not primary** — One of multiple investigation workspaces

Data Explorer provides the operational visibility needed to understand, validate, and verify Librarian's evidence catalog—without interfering with the primary investigation experience.

