# Librarian Deployment - Linux (Docker)

Deploy Librarian on Linux using Docker Compose.

## Architecture

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only

## Prerequisites

- Linux (Ubuntu 20.04+, Debian 11+, Fedora 36+)
- Docker Engine 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum (4GB recommended)
- 10GB disk space for database

## Installation

### 1. Install Docker

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Fedora
sudo dnf install docker-compose
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. Clone Repository

```bash
git clone <repository-url>
cd Librarian/deploy/docker/linux
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit with your library path
```

Example `.env` configuration:
```env
LIBRARY_PATH=/home/user/Documents
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
LIBRARY_PATH=/home/user/Documents
LIBRARY_PATH=/mnt/storage
LIBRARY_PATH=/mnt/nas/documents
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

## Deployment Helper Scripts

The following helper scripts are provided for streamlined development operations:

### Quick Start with `dev.sh`

The primary development interface for Docker operations:

```bash
./dev.sh update      # Update code and restart (preserves data)
./dev.sh status      # Show deployment status
./dev.sh logs        # Tail all logs
./dev.sh logs api    # Tail API logs
./dev.sh logs worker # Tail worker logs
./dev.sh rebuild     # Force clean rebuild (preserves data)
./dev.sh reset       # Destroy and recreate (DESTRUCTIVE)
./dev.sh start       # Start containers
./dev.sh stop        # Stop containers
./dev.sh restart     # Restart containers
```

### Update Script (`update.sh`)

Updates to the latest code and restarts containers while preserving data:

```bash
./update.sh
```

Workflow:
- Pulls latest code from git
- Pulls latest Docker images
- Stops containers (preserving PostgreSQL volume and library data)
- Builds and starts containers
- Waits for health checks
- Displays service status

### Rebuild Script (`rebuild.sh`)

Force a clean rebuild while preserving persistent data:

```bash
./rebuild.sh
```

Preserves:
- PostgreSQL volume
- Library contents

### Reset Script (`reset.sh`)

Destroy the entire environment and recreate from scratch:

```bash
./reset.sh
```

⚠️ **WARNING**: This will delete all database data. You will be prompted to confirm.

### Status Script (`status.sh`)

Display deployment status including:

```bash
./status.sh
```

Example output:
```
┌─────────────────────────────────────────┐
│         Librarian Deployment Status     │
└─────────────────────────────────────────┘

API:        HEALTHY
Database:   HEALTHY
Workers:    1
Documents:  3434
Queue:      0 queued
DB Size:    32 MB
Containers: 3 running

Quick Links:
  Health:  http://localhost:8000/health
  API:     http://localhost:8000/docs
  Stats:   http://localhost:8000/api/v1/stats
```

### Logs Script (`logs.sh`)

Interactive log viewer:

```bash
./logs.sh api       # View API server logs
./logs.sh worker    # View worker logs
./logs.sh postgres  # View PostgreSQL logs
./logs.sh all       # View all logs (default)
./logs.sh api --tail 200    # Last 200 lines
./logs.sh all --since 30m   # Last 30 minutes
```

## Manual Docker Commands

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
./update.sh
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

### Docker Daemon Not Running

```bash
sudo systemctl start docker
sudo systemctl enable docker
```

### Port Already in Use

Change `API_PORT` in `.env`:
```env
API_PORT=8001
```

### Permission Issues

```bash
# Fix volume permissions
sudo chown -R $(id -u):$(id -g) ./volumes
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
3. Configure firewall for API port if needed
4. Consider TLS for production deployments
5. Restrict library access to read-only when possible
