# Librarian Dashboard

Operational dashboard for the Librarian evidence retrieval engine.

## Overview

The Dashboard is a separate React application that consumes the Librarian API. It provides real-time observability into the system through:

- **System Overview** - Key metrics and system health
- **Queue Monitor** - Job queue status and worker activity
- **Activity Feed** - Real-time event stream
- **Document Journey** - Document processing lifecycle
- **Extraction Viewer** - Extracted entities, events, and locations

## Architecture

```
Browser
   ↓
Dashboard (:3000)
   ↓ REST
Librarian API (:8000)
   ↓
PostgreSQL (:5432)
```

### Key Principles

1. **API is the single source of truth** - Dashboard never accesses the database directly
2. **No business logic duplication** - All processing happens in the backend
3. **Type safety** - TypeScript types are generated from OpenAPI schema
4. **Independent deployment** - Dashboard and API can be deployed separately

## Technology Stack

- **Frontend**: React 18, TypeScript
- **Build**: Vite 5
- **Charts**: Apache ECharts 5
- **Routing**: React Router 6
- **HTTP Client**: Axios

## Getting Started

### Prerequisites

- Node.js 18+
- Librarian API running on port 8000

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The dashboard will be available at http://localhost:3100

**Note:** When developing locally without Docker, set `VITE_API_URL=http://localhost:8001` to point to the API.

### Environment Variables

Create a `.env.local` file:

```bash
VITE_API_URL=http://localhost:8000
```

### Type Generation

Types are auto-generated from the OpenAPI schema:

```bash
npm run generate-types
```

### Building

```bash
npm run build
```

Output will be in the `dist/` directory.

### Validation

Validate that the dashboard is compatible with the API:

```bash
npm run validate-contract
```

## Docker

### Development Build

```bash
docker build -t librarian-dashboard:dev \
  --build-arg API_URL=http://localhost:8000 \
  .
```

### Production Deployment

Use the docker-compose configuration in `/deploy`:

```bash
cd ../deploy
docker compose up -d librarian-dashboard
```

The dashboard will be available at http://localhost:3000

## Project Structure

```
dashboard/
├── src/
│   ├── components/       # Reusable UI components
│   │   ├── charts/      # ECharts visualizations
│   │   └── *.tsx        # UI components
│   ├── hooks/           # React hooks for data fetching
│   ├── pages/           # Page components
│   ├── services/        # API client
│   ├── types/           # TypeScript types (auto-generated)
│   ├── App.tsx          # Main application
│   └── main.tsx         # Entry point
├── public/              # Static assets
├── docs/                # API contract documentation
├── Dockerfile           # Production container
├── nginx.conf           # Production nginx config
└── package.json
```

## Pages

### System Overview (`/overview`)

- Files, Documents, Directories counts
- Storage used
- Entities, Relationships, Events, Locations
- Workers and queue status
- Service health indicators

### Queue Monitor (`/queue`)

- Queue depth chart
- Running/queued/completed/failed job counts
- Job list with filtering
- Failure trend chart

### Activity Feed (`/activity`)

- Real-time event stream
- INFO/WARN/ERROR level indicators
- Similar to `tail -f` behavior

### Document Journey (`/documents`)

- Document list with status filtering
- Per-document processing timeline
- Lifecycle state visualization

### Extraction Viewer (`/extractions`)

- Document extraction results
- Entity, Event, Location listings
- Content preview

## API Contract

The dashboard consumes these endpoints:

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/v1/status` | System status |
| `GET /api/v1/stats` | Statistics |
| `GET /api/v1/documents/status` | Document status counts |
| `GET /api/v1/jobs/status` | Job status counts |
| `GET /api/v1/jobs` | List jobs |
| `GET /api/v1/operations/documents` | List documents |
| `GET /api/v1/operations/documents/{id}/journey` | Document journey |
| `GET /api/v1/operations/documents/{id}/extractions` | Extractions |
| `GET /api/v1/timeline` | Event timeline |

See `/docs/api-contract/` for full API documentation.

## Troubleshooting

### API Not Responding

1. Check the API is running on the correct port
2. Verify CORS is configured correctly
3. Check network connectivity

### Types Out of Sync

```bash
npm run generate-types
```

This will regenerate types from the OpenAPI schema.

### Build Failures

1. Clear node_modules and reinstall
2. Check TypeScript errors
3. Verify environment variables

## License

See the main Librarian repository.
