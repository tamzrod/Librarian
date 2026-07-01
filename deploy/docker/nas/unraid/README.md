# Librarian Deployment - Unraid NAS

Deploy Librarian on Unraid NAS using Docker.

## Architecture

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only

## Prerequisites

- Unraid 6.9.0+
- Docker plugin installed
- Access to Docker templates (optional)

## Library Path Examples for Unraid

| Path | Description |
|------|-------------|
| `/mnt/user/documents` | User share documents |
| `/mnt/user/photos` | Photo library |
| `/mnt/cache/appdata/librarian` | App data location |

## Installation via Unraid Web UI

### 1. Open Docker Tab

Navigate to **Docker** tab in Unraid web interface.

### 2. Add Container

**Add another Container** → **Template**.

### 3. Use Template

Use this repository's Docker image:
```
librarian/api:latest
```

Or create custom container with:

**General**:
- Name: `librarian-api`
- Network Type: `bridge`

**Port Mappings**:
| Container Port | Host Port |
|----------------|-----------|
| 8000 | 8000 |

**Volume Mappings**:
| Container Path | Host Path | Mode |
|----------------|-----------|------|
| `/library` | `/mnt/user/documents` | Read-only |
| `/var/lib/postgresql/data` | `/mnt/cache/appdata/librarian/postgres` | Read-write |

**Environment Variables**:
| Variable | Value |
|----------|-------|
| `DATABASE_URL` | `postgresql://librarian:password@postgres:5432/librarian` |
| `LIBRARIAN_LIBRARY_ROOT` | `/library` |

### 4. Create PostgreSQL Container First

Create PostgreSQL container:

**Image**: `postgres:16-alpine`

**Environment**:
| Variable | Value |
|----------|-------|
| `POSTGRES_DB` | `librarian` |
| `POSTGRES_USER` | `librarian` |
| `POSTGRES_PASSWORD` | `your_password` |

**Volume**: `/var/lib/postgresql/data` → `/mnt/cache/appdata/librarian/postgres`

### 5. Start Both Containers

Start PostgreSQL first, then Librarian API.

## Installation via Docker Compose (SSH)

### 1. SSH to Unraid

```bash
ssh root@your-unraid-ip
```

### 2. Create Directory

```bash
mkdir -p /mnt/user/appdata/librarian
cd /mnt/user/appdata/librarian
```

### 3. Create Files

Create `.env`:
```env
POSTGRES_DB=librarian
POSTGRES_USER=librarian
POSTGRES_PASSWORD=your_secure_password
API_HOST_PORT=8000
LIBRARY_PATH=/mnt/user/documents
```

Copy `docker-compose.yml` from this repository.

### 4. Start Services

```bash
docker compose up -d
```

## Automatic Ingestion

**There is no:**
- ❌ Collection management
- ❌ Folder picker
- ❌ Import wizard
- ❌ Manual indexing button

Librarian **automatically and recursively** discovers all files under the library root. Automatic ingestion begins immediately after startup.

## Accessing the API

- **Local**: http://localhost:8000/docs
- **Network**: http://your-unraid-ip:8000/docs

## Common Commands

```bash
# Via SSH
cd /mnt/user/appdata/librarian

# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Restart
docker compose restart
```

## Upgrading

```bash
cd /mnt/user/appdata/librarian
docker compose pull
docker compose up -d
```

## Backup

### Database Backup

```bash
cd /mnt/user/appdata/librarian
docker compose exec postgres pg_dump -U librarian librarian > /mnt/user/backups/librarian_backup_$(date +%Y%m%d).sql
```

## Restore

```bash
docker compose exec -T postgres psql -U librarian librarian < backup_file.sql
```

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker compose logs librarian-api
docker compose logs postgres
```

### Permission Issues

Ensure paths are accessible:
```bash
ls -la /mnt/user/documents
```

### Network Issues

Check Unraid's Docker network settings.

## Data Persistence

Store PostgreSQL data on cache drive for better performance:
```
/mnt/cache/appdata/librarian/postgres
```

## Security Notes

1. Change default PostgreSQL password
2. Use Unraid's Docker network isolation
3. Configure Unraid firewall for API access
4. Consider VPN for remote access
5. Restrict library access to read-only
