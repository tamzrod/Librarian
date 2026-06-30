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
├── storage/              # Database layer
│   └── postgres_backend.py
├── workers/              # Background job processors
├── deploy/                # Docker deployment
│   └── docker-compose.yml
└── docs/
    └── api-contract/     # API contract documentation
```

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
