# Librarian Deployment - Windows (Docker)

Deploy Librarian on Windows using Docker Desktop.

## Architecture

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only

## Prerequisites

- Windows 10/11 Pro or Windows Server 2019+
- Docker Desktop with WSL 2 backend
- 4GB RAM minimum (8GB recommended)
- 10GB disk space for database

## Installation

### 1. Install Docker Desktop

Download from https://www.docker.com/products/docker-desktop

Enable WSL 2 backend during installation.

### 2. Clone Repository

```powershell
git clone <repository-url>
cd Librarian/deploy/docker/windows
```

### 3. Configure Environment

```powershell
Copy-Item .env.example .env
# Edit .env with your library path
```

Example `.env` configuration:
```env
LIBRARY_PATH=C:/Users/YourName/Documents
POSTGRES_PASSWORD=your_secure_password
API_HOST_PORT=8001
```

### 4. Start Services

```powershell
docker compose up -d
```

### 5. Verify

```powershell
docker compose ps
curl http://localhost:8001/health
```

## Library Configuration

### Mounting Your Library

Set `LIBRARY_PATH` in `.env` to point to your documents:

```env
# Example paths
LIBRARY_PATH=C:/Users/YourName/Documents
LIBRARY_PATH=D:/MyLibrary
LIBRARY_PATH=E:/Work/Projects
```

### Automatic Ingestion

**There is no:**
- ❌ Collection management
- ❌ Folder picker
- ❌ Import wizard
- ❌ Manual indexing button

Librarian **automatically and recursively** discovers all files under the library root. Automatic ingestion begins immediately after startup.

## Accessing the API

- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health
- **Status**: http://localhost:8001/api/v1/status
- **Stats**: http://localhost:8001/api/v1/stats
- **Timeline**: http://localhost:8001/api/v1/timeline

## Common Commands

### Start

```powershell
docker compose up -d
```

### Stop

```powershell
docker compose down
```

### View Logs

```powershell
docker compose logs -f
docker compose logs -f librarian-api
```

### Restart

```powershell
docker compose restart
```

## Upgrading

```powershell
docker compose pull
docker compose up -d
```

## Backup

### Database Backup

```powershell
docker compose exec postgres pg_dump -U librarian librarian > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql
```

### Restore

```powershell
docker compose exec -T postgres psql -U librarian librarian < backup_file.sql
```

## Troubleshooting

### Docker Desktop Not Running

```powershell
Start-Service Docker
```

### Port Already in Use

Change `API_HOST_PORT` in `.env`:
```env
API_HOST_PORT=8001
```

### Volume Mount Issues

Ensure paths use forward slashes and exist:
```powershell
Test-Path "C:/Users/YourName/Documents"
```

### View Container Logs

```powershell
docker compose logs postgres
docker compose logs librarian-api
```

## Data Persistence

Database data is stored in a named Docker volume (`librarian_postgres_data`).

To completely remove all data:
```powershell
docker compose down -v
```

## Security Notes

1. Change default `POSTGRES_PASSWORD`
2. Use strong passwords in production
3. Consider TLS for production deployments
4. Restrict library access to read-only when possible
