# Librarian

Librarian is an **evidence retrieval and context reconstruction engine** operating on bounded collections.

## What Librarian Is

- **Evidence Retrieval Engine**: Assembles evidence packages from indexed artifacts
- **Context Reconstruction System**: Rebuilds context from fragmented, distributed information
- **Knowledge Catalog**: Preserves artifacts in their native format while building a searchable catalog
- **Agentic Reasoning Support**: Enables AI agents to reason over evidence from bounded collections

Librarian is designed for **bounded collections** - a folder, a project, a knowledge base - and helps reconstruct what exists within those boundaries.

## What Librarian Is Not

- A code assistant or chatbot
- A document chatbot
- A traditional RAG system
- A vector database wrapper
- A code analysis tool
- A source code indexer

## The Vision

Traditional RAG:
```
Question → Chunk Retrieval → LLM
```

Librarian:
```
Bounded Collection → Artifact Ingestion → Evidence Extraction → Evidence Assembly → Agentic Reasoning
```

Librarian focuses on **digesting whatever exists inside a folder**, preserving artifacts in their native format, and extracting evidence to support agentic reasoning.

## Core Principles

1. **Filesystem is the source of truth** - Original files are never modified
2. **Artifacts are preserved** - Content stays in native format; only evidence is extracted
3. **Derived data is disposable** - Reindexing is always possible
4. **The catalog remains organized** - Even when the filesystem is not
5. **Evidence over summaries** - Assemble facts, let the agent reason

## Example User Questions

- "Where was I on January 1 2026?"
- "Give me the profile of Client ABC."
- "Show me all photos related to Project X."
- "What happened during February 2026?"
- "What is the drop wire length in this CAD project?"

## Supported Artifact Types

Librarian can ingest and extract evidence from:

| Category | Types |
|----------|-------|
| Text | Plain text, Markdown, logs |
| Structured | JSON, YAML, TOML, CSV, XML, INI |
| Images | JPEG, PNG (with GPS/EXIF extraction) |
| Documents | PDF, DOC |
| Code | Python, and extensible to others |
| Future | Audio, video, CAD, emails, spreadsheets, databases, telemetry |

## Setup

### Python Dependencies

Librarian requires Python 3.11+ and the following packages:

```
pip install -r requirements.txt
```

**Core dependencies:**
- `fastapi>=0.100.0` - Web framework
- `uvicorn[standard]>=0.23.0` - ASGI server
- `pydantic>=2.0.0` - Data validation
- `psycopg>=3.1.0` - PostgreSQL driver
- `requests>=2.31.0` - HTTP client
- `Pillow>=10.0.0` - Image processing
- `PyYAML>=6.0` - YAML parsing
- `python-dateutil>=2.8.0` - Date utilities

### Docker Deployment

See [deploy/README.md](deploy/README.md) for detailed Docker deployment instructions.

```bash
cd deploy/docker/linux
docker compose up -d
```

## Environment Variables

Repository-owned environment variables follow two rules:

- Runtime variables use the `LIBRARIAN_` prefix.
- Deployment host port variables use the explicit `*_HOST_PORT` suffix.

Standard ecosystem variables keep their upstream names (`DATABASE_URL`, `POSTGRES_*`, `OPENAI_API_KEY`, `VITE_*`).

| Variable | Default | Notes |
|----------|---------|-------|
| `LIBRARIAN_LIBRARY_ROOT` | `/library` | Canonical runtime library root. Deprecated alias: `LIBRARY_ROOT`. |
| `DATABASE_URL` | unset | PostgreSQL connection string for the API and worker. |
| `LIBRARIAN_API_URL` | `http://localhost:8000` | Canonical API URL for the legacy Python GUI. Deprecated alias: `API_URL`. |
| `WORKER_ID` | unset | Optional worker identifier. |
| `EMBEDDING_MODEL` | auto-detected | Optional embedding backend override. |
| `OPENAI_API_KEY` | unset | Optional key for OpenAI embeddings. |

Deployment-specific variables, examples, and migration notes are documented in [deploy/README.md](deploy/README.md). Dashboard-specific `VITE_*` variables are documented in [dashboard/README.md](dashboard/README.md).

## Schema Migrations

Database schema upgrades are forward-only and run automatically at startup via `storage/migration_manager.py`.

- Operator guide: [docs/SCHEMA_MIGRATIONS.md](docs/SCHEMA_MIGRATIONS.md)
- Per-migration changelog: [storage/migrations/CHANGELOG.md](storage/migrations/CHANGELOG.md)

## Quick Start

```python
from core.librarian import Librarian
from core.evidence_builder import build_evidence
from core.query_planner import plan_query

lib = Librarian()
lib.ingest('/path/to/bounded/collection')

# Plan the query
plan = plan_query("Where was I on January 1 2026?")

# Build evidence package
evidence = build_evidence(plan['question'], plan, lib.backend)
```

The library may live anywhere. Librarian only cares that it can reach the shelves.
