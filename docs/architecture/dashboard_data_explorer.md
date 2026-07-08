# Dashboard Data Explorer Architecture

## Overview

The Dashboard Data Explorer is an **operational inspection tool** for Librarian. It provides developers, operators, and advanced users with direct access to inspect the current state of the catalog backend.

### Designation

The Data Explorer is intentionally modeled after familiar operational tooling:

- **Grafana Explore** — ad-hoc querying and inspection
- **InfluxDB Data Explorer** — time-series data investigation
- **Kibana Discover** — document exploration and search

This document describes the architecture that enables backend-agnostic inspection capabilities.

---

## Purpose

### What the Data Explorer Is

The Data Explorer is a **read-first inspection interface** that allows users to:

- Validate ingestion results
- Inspect extracted data
- Verify relationships and connections
- Troubleshoot indexing issues
- Debug metadata extraction
- Check system state

### What the Data Explorer Is Not

The Data Explorer is **NOT**:

- The primary Librarian interface
- An evidence browser or retrieval tool
- A CRUD application
- A database administration tool (e.g., replacement for pgAdmin)
- A replacement for Librarian's evidence retrieval workflows

### Relationship to Evidence Retrieval

```
┌─────────────────────────────────────────────────────────────┐
│                   Librarian Core                            │
│                                                              │
│   Evidence Retrieval (Collections, Search, Agentic)         │
│   │                                                          │
│   │  PRIMARY WORKFLOW                                        │
│   │  Assembles evidence for AI reasoning                     │
│   ▼                                                          │
│   Evidence Packages → Agent → Answers                        │
│                                                              │
│   ─────────────────────────────────────────────────────      │
│                                                              │
│   Data Explorer (INSPECTION ONLY)                            │
│   │                                                          │
│   │  OPERATIONAL TOOL                                        │
│   │  Inspects catalog state, validates ingestion, debugs     │
│   ▼                                                          │
│   Developer/Operator debugging                                │
└─────────────────────────────────────────────────────────────┘
```

The Data Explorer exists **outside** the primary evidence retrieval workflow. It is a supporting tool for those who need to understand what Librarian has stored and how it arrived in that state.

---

## Architecture

### Layered Architecture

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
│          (PostgreSQL, SQLite, DuckDB, etc.)                 │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

| Layer | Responsibility |
|-------|---------------|
| **Dashboard** | Renders the UI, manages user interaction |
| **Data Explorer** | Coordinates state between UI and API |
| **Explorer Service** | Exposes inspection operations via REST API |
| **Backend Adapter** | Translates generic operations to backend-specific queries |
| **Catalog Backend** | Persists and retrieves catalog data |

### Key Invariant

**The Dashboard never communicates directly with the catalog backend.**

All inspection operations flow through the Explorer Service and Backend Adapter. This ensures:

1. Backend implementation is encapsulated
2. The UI remains unchanged when the backend changes
3. Multiple backends can be supported through adapter substitution

---

## Backend Adapter

### Role

The Backend Adapter is responsible for translating **generic inspection operations** into **backend-specific queries**.

### Inspection Interface

The adapter implements a standardized inspection interface:

```python
class ExplorerBackendAdapter(ABC):
    """Interface for catalog backend inspection operations."""
    
    @abstractmethod
    def list_objects(self, object_type: str, **filters) -> list[dict]:
        """List objects of a given type (documents, entities, events, etc.)."""
        raise NotImplementedError()
    
    @abstractmethod
    def describe_object(self, object_id: int, object_type: str) -> dict:
        """Get detailed description of a specific object."""
        raise NotImplementedError()
    
    @abstractmethod
    def read_records(self, table: str, filters: dict = None) -> list[dict]:
        """Read raw records from a table or collection."""
        raise NotImplementedError()
    
    @abstractmethod
    def read_metadata(self, document_id: int) -> dict:
        """Read all metadata for a document."""
        raise NotImplementedError()
    
    @abstractmethod
    def read_statistics(self) -> dict:
        """Read system statistics and counts."""
        raise NotImplementedError()
    
    @abstractmethod
    def execute_inspection_query(self, query: str, **params) -> dict:
        """Execute a backend-native inspection query."""
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
| `execute_inspection_query` | Raw SQL | Raw SQL | Query DSL |

### Backend Adapter Examples

#### PostgreSQL Adapter

```python
class PostgreSQLExplorerAdapter(ExplorerBackendAdapter):
    """PostgreSQL-specific inspection operations."""
    
    def list_objects(self, object_type: str, **filters) -> list[dict]:
        table_map = {
            'documents': 'documents',
            'entities': 'entities',
            'events': 'events',
            'locations': 'locations',
        }
        table = table_map.get(object_type)
        if not table:
            raise ValueError(f"Unknown object type: {object_type}")
        
        query = f"SELECT * FROM {table}"
        # Apply filters...
        return self._execute(query)
    
    def execute_inspection_query(self, query: str, **params) -> dict:
        """Execute raw SQL for advanced inspection."""
        return self._execute(query, params)
```

#### DuckDB Adapter

```python
class DuckDBExplorerAdapter(ExplorerBackendAdapter):
    """DuckDB-specific inspection operations."""
    
    def execute_inspection_query(self, query: str, **params) -> dict:
        """Execute DuckDB SQL."""
        return self._duckdb_conn.execute(query, params).fetchdf().to_dict(orient='records')
```

---

## Current Implementation

### PostgreSQL as Default Backend

The current implementation operates on **PostgreSQL** as the catalog backend.

```python
# Current: Direct PostgreSQL adapter
class PostgreSQLExplorerAdapter(ExplorerBackendAdapter):
    def __init__(self, connection_pool):
        self.pool = connection_pool
    
    def list_documents(self, **filters) -> list[dict]:
        # Direct SQL queries
        ...
```

### Implementation Transparency

PostgreSQL is **not hidden**—it is an acknowledged implementation detail:

```
PostgreSQL (current)
    │
    ├── Well-documented schema
    ├── Standard SQL queries
    └── Adapter encapsulates all backend-specific logic
```

The UI and Explorer Service know nothing about PostgreSQL. They work exclusively through the Backend Adapter interface.

---

## User Interface

### Three Primary Areas

The Data Explorer UI consists of three primary areas:

```
┌────────────────────────────────────────────────────────────────────┐
│                        Data Explorer                                │
├──────────────┬─────────────────────────────┬───────────────────────┤
│              │                             │                        │
│   Explorer   │         Inspector          │        Query          │
│              │                             │                        │
│  Navigation  │   Object Display            │   Raw Query           │
│              │                             │                        │
│  ──────────  │   ──────────                │   ──────────           │
│              │                             │                        │
│  - Objects   │   - Structure               │   - SQL Editor         │
│  - Types     │   - Records                 │   - Query DSL          │
│  - Filters   │   - Metadata                │   - Results            │
│  - Search    │   - Relationships           │   - History            │
│              │   - Statistics              │                        │
└──────────────┴─────────────────────────────┴───────────────────────┘
```

### Explorer Pane

Navigation through backend objects.

| Feature | Description |
|---------|-------------|
| Object Browser | Tree or list view of available objects |
| Type Filter | Filter by document, entity, event, location |
| Quick Search | Search across object names and identifiers |
| Breadcrumb | Current navigation context |

### Inspector Pane

Displays detailed information about selected objects.

| Tab | Content |
|-----|---------|
| Structure | Object schema and field definitions |
| Records | Raw record data in tabular format |
| Metadata | Computed metadata (counts, sizes, timestamps) |
| Relationships | Connections to other objects |
| Statistics | Aggregated statistics for the selected object |

### Query Pane (Optional/Advanced)

Backend-native query interface for advanced inspection.

| Backend | Query Language |
|---------|---------------|
| PostgreSQL | SQL |
| DuckDB | SQL |
| Elasticsearch | Query DSL |
| ClickHouse | SQL |

**The query interface is pluggable.** When a new backend is added, a corresponding query adapter provides the appropriate query language support.

---

## Design Goals

The Data Explorer is designed according to these principles:

| Goal | Description |
|------|-------------|
| **Storage Agnostic** | UI operates through abstraction; no backend-specific logic in frontend |
| **Backend Replaceable** | New backends require only a new adapter, not UI changes |
| **Inspection Focused** | Read-first design; no write operations in standard usage |
| **Read-Primary Design** | Optimized for inspection; writes are administrative exceptions |
| **Minimal Backend Assumptions** | Adapter interface avoids assuming SQL or specific query languages |
| **Extensible Adapter Architecture** | Adapters plug in via dependency injection; no hardcoded backends |
| **Safe Operational Tooling** | Read-only by default; modifications require explicit opt-in |

---

## Non-Goals

The Data Explorer explicitly excludes the following:

| Non-Goal | Rationale |
|----------|-----------|
| Primary Librarian interface | Evidence retrieval workflows are the primary interface |
| Evidence browser | Dedicated views handle evidence browsing |
| CRUD application | Inspection is read-first; writes are administrative exceptions |
| Database administration | pgAdmin, DBeaver, and similar tools are more appropriate |
| Schema modification | The Explorer reads schema; migrations handle changes |
| Query optimization | Backend-specific optimization is outside scope |

---

## Future Extensibility

### Adding New Backends

To add a new backend (e.g., ClickHouse):

1. **Create the adapter class:**

```python
class ClickHouseExplorerAdapter(ExplorerBackendAdapter):
    """ClickHouse-specific inspection operations."""
    
    def list_objects(self, object_type: str, **filters) -> list[dict]:
        # ClickHouse-specific implementation
        ...
    
    def execute_inspection_query(self, query: str, **params) -> dict:
        # ClickHouse SQL or HTTP interface
        ...
```

2. **Register the adapter:**

```python
# In backend configuration
ADAPTERS = {
    'postgresql': PostgreSQLExplorerAdapter,
    'clickhouse': ClickHouseExplorerAdapter,
    # Future backends...
}
```

3. **Wire via dependency injection:**

```python
def get_explorer_adapter(backend_type: str) -> ExplorerBackendAdapter:
    adapter_class = ADAPTERS.get(backend_type)
    if not adapter_class:
        raise ValueError(f"Unknown backend type: {backend_type}")
    return adapter_class()
```

### UI Independence

The Dashboard UI depends only on the `ExplorerBackendAdapter` interface. Adding a new backend does not require:

- Changes to API routes
- Modifications to frontend components
- Updates to data models

### Pluggable Query Interfaces

The Query pane uses a backend-type selector:

```typescript
interface QueryInterface {
  backendType: string;
  queryLanguage: string;
  executeQuery(query: string): Promise<QueryResult>;
}

// Adapters provide their query language
PostgreSQLAdapter.queryLanguage = 'sql';
DuckDBAdapter.queryLanguage = 'sql';
ElasticsearchAdapter.queryLanguage = 'query-dsl';
```

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

### Error Handling

```json
{
  "success": false,
  "error": {
    "code": "QUERY_ERROR",
    "message": "Syntax error in SQL query",
    "backend_error": "column 'foo' does not exist"
  }
}
```

---

## Security Considerations

### Read-Only by Default

The Data Explorer operates in **read-only mode** by default:

- No INSERT, UPDATE, or DELETE operations exposed
- All operations are audit-logged
- Administrative write access requires separate authentication

### Query Validation

Raw query execution includes validation:

```python
def execute_inspection_query(self, query: str, **params) -> dict:
    # Reject writes
    forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE', 'ALTER']
    if any(keyword in query.upper() for keyword in forbidden):
        raise PermissionError("Write operations not permitted in explorer")
    
    # Apply statement timeout
    timeout = "SET statement_timeout = '30s'"
    return self._execute(f"{timeout}; {query}", params)
```

### Access Control

The Data Explorer should be:

- Disabled by default for production deployments
- Restricted to authenticated operators
- Isolated from public-facing Librarian interfaces

---

## Implementation Guidance

### Adapter Location

```
storage/
├── backend.py              # StorageBackend ABC (existing)
├── postgres_backend.py     # Storage implementation (existing)
└── explorer/
    ├── __init__.py
    ├── adapter.py          # ExplorerBackendAdapter ABC
    ├── postgres_adapter.py # PostgreSQL inspection adapter
    ├── duckdb_adapter.py   # Future: DuckDB adapter
    └── ...
```

### Service Location

```
api/
├── routes/
│   └── explorer.py         # Existing explorer routes
└── services/
    └── explorer_service.py # Backend-agnostic inspection logic
```

### Testing Strategy

```python
# test_explorer_adapters.py

def test_adapter_interface(postgres_adapter):
    """Verify adapter implements all required methods."""
    for method in ['list_objects', 'describe_object', 'read_records',
                   'read_metadata', 'read_statistics', 'execute_inspection_query']:
        assert hasattr(postgres_adapter, method)

def test_backend_agnostic(postgres_adapter, duckdb_adapter):
    """Verify adapters produce equivalent results for same operations."""
    postgres_results = postgres_adapter.list_objects('documents')
    duckdb_results = duckdb_adapter.list_objects('documents')
    assert normalize(postgres_results) == normalize(duckdb_results)
```

---

## Summary

The Dashboard Data Explorer is an **operational inspection tool** that enables developers, operators, and advanced users to examine the state of the Librarian catalog backend.

### Key Architectural Points

| Point | Description |
|-------|-------------|
| **Position** | Outside primary evidence retrieval workflow |
| **Purpose** | Inspection, validation, debugging, troubleshooting |
| **Architecture** | Dashboard → Data Explorer → Explorer Service → Backend Adapter → Catalog Backend |
| **Backend Adapter** | Translates generic operations to backend-specific queries |
| **UI Design** | Explorer (navigation) + Inspector (display) + Query (advanced) |
| **Extensibility** | New backends require only new adapter, not UI changes |

### Design Principles

1. **Storage agnostic** — UI never depends on backend implementation
2. **Backend replaceable** — Adapters encapsulate all backend logic
3. **Read-first** — Inspection focus; writes are administrative exceptions
4. **Pluggable** — Query interfaces adapt per backend type

The Data Explorer provides the operational visibility needed to understand, validate, and troubleshoot Librarian's catalog state—without interfering with the primary evidence retrieval experience.
