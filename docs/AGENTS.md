# AGENTS.md

This document serves as the developer and AI-agent operating manual for Librarian.

## Project Structure

```
Librarian/
├── api/                    # FastAPI REST API
│   ├── app.py             # Main application
│   ├── app_state.py       # Application state management
│   ├── dependencies.py    # FastAPI dependencies
│   └── routes/            # API route handlers
│       ├── collections.py
│       ├── operations.py   # Dashboard observability endpoints
│       ├── pipeline.py
│       └── questions.py
├── dashboard/              # React operational dashboard
│   ├── src/
│   │   ├── components/    # UI components
│   │   │   └── charts/   # Apache ECharts visualizations
│   │   ├── hooks/        # React data hooks
│   │   ├── pages/        # Page components
│   │   ├── services/     # API client
│   │   └── types/        # TypeScript types
│   ├── Dockerfile        # Production container
│   └── nginx.conf        # Production nginx config
├── ingestion/              # File watching and ingestion
│   └── collection_watcher.py
├── parsers/                # Artifact parsers
│   └── image_parser.py    # Image ingestion (Phase 1)
├── registry/               # Parser registration
│   └── register_parsers.py
├── storage/              # Database layer
│   └── postgres_backend.py
├── workers/              # Background job processors
├── deploy/                # Docker deployment
│   └── docker-compose.yml
└── docs/
    └── api-contract/     # API contract documentation
```

## Parser vs Worker Responsibilities

Librarian distinguishes between **Parsers** (ingestion) and **Workers** (enrichment):

### Parsers (`parsers/`)

Parsers create the initial artifact record:
- Validate file format
- Extract basic metadata (dimensions, MIME type)
- Create document record in database
- Return lightweight artifact metadata

Example: `ImageParser` validates an image file, extracts dimensions, and creates a document record.

### Workers (`workers/`)

Workers enrich artifacts with derived information:
- May fail independently without invalidating the artifact
- Reference the same `document_id`
- Can run in parallel

Example: `PhotoMetadataExtractor` extracts EXIF data from images after ingestion.

### Architecture Principle

```
Parser (fast, lightweight)
    ↓
Document created (valid)

Worker (slower, may fail)
    ↓
Enrichment added (optional)
```

An artifact remains valid even if one or more workers fail. Each worker independently contributes to the artifact's enrichment.

## Dashboard vs Backend

The dashboard is a **separate application** that consumes the API:

| Aspect | Backend | Dashboard |
|--------|---------|-----------|
| Technology | Python/FastAPI | React/Vite/TypeScript |
| Port | 8000 | 3000 |
| Database Access | Direct | Via API only |
| Purpose | Data processing | Observability |

**Dashboard Rules:**
- NEVER access PostgreSQL directly
- NEVER import backend storage modules
- NEVER share backend business logic
- NEVER execute extraction or worker logic
- All data must come from REST API calls

## Building the Dashboard

```bash
cd dashboard
npm install
npm run build
```

## Docker Deployment

```bash
cd deploy
docker compose up -d
```

**Network Configuration:**
- PostgreSQL: Internal-only (`postgres:5432`) - NOT exposed to host
- API: `librarian-api:8000` (internal), host:8001
- Dashboard: `librarian-dashboard:3000` (internal), host:3100

**Access URLs:**
- Dashboard: http://localhost:3100
- API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## Architecture and Operations Documentation

For AI agents and developers investigating issues, the following documentation provides authoritative guidance:

### Evidence and Storage Lifecycle
- [Evidence Lifecycle](architecture/evidence-lifecycle.md) — Three-tier persistence architecture defining authoritative (Tier 0), regeneratable (Tier 1), and replaceable (Tier 2) data
- [Storage Lifecycle Matrix](architecture/storage-lifecycle-matrix.md) — Behavior of each storage component across rebuild, reset, and nuclear reset operations
- [Derived Artifact Contract](architecture/derived-artifact-contract.md) — Rules for handling regeneratable artifacts that may or may not exist at runtime

### Debugging and Investigation
- [Runtime-First Debugging](operations/runtime-first-debugging.md) — Debugging priority order and runtime evidence hierarchy
- [Runtime-First Investigation Rules](agents/runtime-first-investigation-rules.md) — Rules for AI agents investigating issues (trust runtime over configuration)

### Plugin Development
- [Plugin Contract](plugins/plugin-contract.md) — Required plugin declarations for dependencies, cache, artifacts, and database tables

### Key Principles

1. **Runtime state always overrides configuration** — `docker inspect` output takes precedence over docker-compose files
2. **Missing derived artifacts are valid** — Thumbnails, embeddings, and OCR output may be absent without being errors
3. **Evidence is immutable** — Original documents and checksums must never be modified
4. **Never infer mounts from configuration** — Always verify with `docker inspect` before assuming volumes are mounted
5. **Never propose fixes before proving runtime state** — Inspect containers, volumes, logs, database, and filesystem first
