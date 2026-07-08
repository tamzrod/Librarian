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
Dashboard (:3100)
   ↓ REST
Librarian API (:8001)
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
- Librarian API running on port 8001

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
VITE_API_URL=http://localhost:8001
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

## Build Metadata

The dashboard includes immutable build identification for version traceability.

### What's Included

Each build automatically includes:

- **Dashboard Version** - From `package.json` version field
- **Git Commit SHA** - Short hash of the commit that triggered the build
- **Build Timestamp** - UTC timestamp when the build was created
- **API Contract Version** - Version from `docs/api-contract/v1.0.md`
- **Environment** - `development`, `staging`, or `production`

### Viewing Build Information

Build metadata is displayed in the footer of the dashboard:

```
Dashboard v1.0.0 | Build a8c1d92 | Built 2026-06-30 14:32 UTC | API Contract v1.0 | production
```

### Optional Enhancements

- **Click the build hash** to open the corresponding GitHub commit page
- **Copy button** to copy full build info to clipboard

### Verifying Running Version

Operators can verify the running dashboard version by:

1. Looking at the footer in the dashboard UI
2. Inspecting Docker container labels:
   ```bash
   docker inspect librarian-dashboard --format='{{json .Config.Labels}}'
   ```
3. Checking the build artifact metadata

### Build Metadata Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VITE_BUILD_SHA` | Git commit short hash | `a8c1d92` |
| `VITE_BUILD_TIME` | ISO 8601 UTC timestamp | `2026-06-30T14:32:10Z` |
| `VITE_DASHBOARD_VERSION` | Dashboard version | `1.0.0` |
| `VITE_API_CONTRACT_VERSION` | API contract version | `v1.0` |
| `VITE_ENVIRONMENT` | Build environment | `production` |

## Docker

### Development Build

```bash
cd ../dashboard
docker build -t librarian-dashboard:dev \
  --build-arg API_URL=http://localhost:8001 \
  --build-arg VITE_BUILD_SHA=$(git rev-parse --short HEAD) \
  --build-arg VITE_BUILD_TIME=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --build-arg VITE_DASHBOARD_VERSION=dev \
  --build-arg VITE_API_CONTRACT_VERSION=v1.0 \
  --build-arg VITE_ENVIRONMENT=development \
  .
```

### Production Deployment

Use the docker-compose configuration in `/deploy`:

```bash
cd ../deploy
docker compose up -d librarian-dashboard
```

The dashboard will be available at http://localhost:3100

### Docker Build Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `API_URL` | Backend API URL | `http://localhost:8001` |
| `VITE_BUILD_SHA` | Git commit hash | `unknown` |
| `VITE_BUILD_TIME` | Build timestamp | (empty) |
| `VITE_DASHBOARD_VERSION` | Dashboard version | `dev` |
| `VITE_API_CONTRACT_VERSION` | API contract version | `v1.0` |
| `VITE_ENVIRONMENT` | Environment | `production` |

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
