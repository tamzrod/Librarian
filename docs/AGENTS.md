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
