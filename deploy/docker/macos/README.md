# Librarian Deployment - macOS (Docker)

Deploy Librarian on macOS using Docker Desktop.

## Architecture

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only

## Prerequisites

- macOS 11+ (Big Sur or later)
- Apple Silicon or Intel
- Docker Desktop 4.0+
- 4GB RAM minimum (8GB recommended)
- 10GB disk space for database

## Installation

### 1. Install Docker Desktop

Download from https://www.docker.com/products/docker-desktop

### 2. Clone Repository

```bash
git clone <repository-url>
cd Librarian/deploy/docker/macos
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your library path
```

Example `.env` configuration:
```env
LIBRARY_PATH=/Users/yourname/Documents
POSTGRES_PASSWORD=your_secure_password
API_PORT=8000
```

### 4. Start Services

```bash
docker compose up -d
```

### 5. Verify

```bash
docker compose ps
curl http://localhost:8000/health
```

## Library Configuration

### Mounting Your Library

Set `LIBRARY_PATH` in `.env` to point to your documents:

```env
# Example paths
LIBRARY_PATH=/Users/yourname/Documents
LIBRARY_PATH=/Users/yourname/Dropbox
LIBRARY_PATH=/Volumes/External/Library
```

### Automatic Ingestion

**There is no:**
- ❌ Collection management
- ❌ Folder picker
- ❌ Import wizard
- ❌ Manual indexing button

Librarian **automatically and recursively** discovers all files under the library root. Automatic ingestion begins immediately after startup.

## Accessing the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Status**: http://localhost:8000/api/v1/status
- **Stats**: http://localhost:8000/api/v1/stats
- **Timeline**: http://localhost:8000/api/v1/timeline

## Common Commands

### Start

```bash
docker compose up -d
```

### Stop

```bash
docker compose down
```

### View Logs

```bash
docker compose logs -f
docker compose logs -f librarian-api
```

### Restart

```bash
docker compose restart
```

## Upgrading

```bash
docker compose pull
docker compose up -d
```

## Backup

### Database Backup

```bash
# Create backup directory
mkdir -p backups

# Backup database
docker compose exec postgres pg_dump -U librarian librarian > backups/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore

```bash
docker compose exec -T postgres psql -U librarian librarian < backups/backup_file.sql
```

## Troubleshooting

### Docker Desktop Not Running

Open Docker Desktop from Applications.

### Port Already in Use

Change `API_PORT` in `.env`:
```env
API_PORT=8001
```

### Apple Silicon Performance

Consider using Rosetta 2 for x86_64 containers:
```bash
docker compose build --platform linux/amd64
```

### View Container Logs

```bash
docker compose logs postgres
docker compose logs librarian-api
```

## Data Persistence

Database data is stored in a Docker named volume.

To completely remove all data:
```bash
docker compose down -v
```

## Security Notes

1. Change default `POSTGRES_PASSWORD`
2. Use strong passwords in production
3. Consider TLS for production deployments
4. Restrict library access to read-only when possible
5. Enable Docker Desktop's built-in firewall notifications
