# Librarian Deployment Guide

Comprehensive deployment framework for Librarian evidence retrieval engine across multiple platforms.

## Architecture Overview

Librarian uses a **single-library architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                     HOST FILESYSTEM                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              YOUR LIBRARY ROOT                        │   │
│  │  C:/Users/You/Documents  (Windows)                 │   │
│  │  /home/you/Documents     (Linux/macOS)              │   │
│  │  /volume1/Documents      (Synology)                  │   │
│  │  /mnt/user/Documents     (Unraid)                   │   │
│  │  /mnt/tank/Documents     (TrueNAS)                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                    recursive scan                            │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   /library                            │   │
│  │              (container mount)                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                  │
│                    automatic ingestion                       │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PostgreSQL CATALOG                       │   │
│  │         (entities, events, locations)                │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Key Principles

- **Single Library Root**: One directory tree per deployment
- **Automatic Ingestion**: Files are discovered and indexed automatically
- **API-First**: REST API is the primary interface
- **GUI as Client**: GUI communicates exclusively via API (optional)

## Deployment Methods

### Container Deployment (Docker)

| Platform | Location | Status |
|----------|----------|--------|
| Windows | `docker/windows/` | ✅ Ready |
| Linux | `docker/linux/` | ✅ Ready |
| macOS | `docker/macos/` | ✅ Ready |
| Synology NAS | `docker/nas/synology/` | ✅ Ready |
| Unraid NAS | `docker/nas/unraid/` | ✅ Ready |
| TrueNAS | `docker/nas/truenas/` | ✅ Ready |

### Native Binary Deployment

| Platform | Location | Status |
|----------|----------|--------|
| Windows | `binary/windows/` | 📋 Planned |
| Linux | `binary/linux/` | 📋 Planned |
| macOS | `binary/macos/` | 📋 Planned |

### Package Manager Deployment

| Platform | Package Manager | Location | Status |
|----------|-----------------|----------|--------|
| Windows | winget | `packages/winget/` | 📋 Planned |
| Linux (Debian/Ubuntu) | apt/deb | `packages/deb/` | 📋 Planned |
| Linux (Fedora/RHEL) | rpm | `packages/rpm/` | 📋 Planned |
| macOS/Linux | Homebrew | `packages/brew/` | 📋 Planned |

## Quick Start

### Docker Deployment

1. Choose your platform:
   ```bash
   # Linux/macOS
   cd deploy/docker/linux
   
   # Windows
   cd deploy/docker/windows
   
   # Synology NAS
   cd deploy/docker/nas/synology
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your library path
   ```

3. Start:
   ```bash
   docker compose up -d
   ```

4. Access:
   - Dashboard: http://localhost:3100
   - API: http://localhost:8001
   - API Docs: http://localhost:8001/docs

## Library Configuration

### Mounting Your Library

The library root is mounted at `/library` inside the API container. Configure it via `LIBRARY_PATH` in `.env`:

| Environment | Example Path |
|-------------|--------------|
| Windows | `C:/Users/YourName/Documents` |
| Linux | `/mnt/storage` |
| NAS | `/mnt/nas/documents` |
| Docker | `./volumes/library` |

### Automatic File Discovery

**There is no:**
- ❌ Collection management
- ❌ Folder picker
- ❌ Import wizard
- ❌ Manual indexing button

Librarian **automatically and recursively** discovers all files and subfolders under the library root. Automatic ingestion begins immediately after startup.

### Library Structure Example

```
/path/to/your/documents/
├── contracts/
│   ├── client_abc_contract.pdf
│   └── vendor_xyz_agreement.pdf
├── invoices/
│   ├── 2026/
│   │   └── invoice_001.pdf
│   └── 2025/
├── photos/
│   ├── site_visits/
│   │   └── IMG_20260115.jpg
│   └── events/
├── notes/
│   ├── meeting_notes.md
│   └── project_planning.md
└── reports/
    └── quarterly_report.xlsx
```

## Services

### PostgreSQL

- **Image**: postgres:16-alpine
- **Internal**: `postgres:5432` (Docker service discovery)
- **Host**: NOT exposed (internal network only)
- **Data**: Persisted to Docker volume
- **Initialization**: Runs `postgres/init.sql` on first startup

### Librarian API

- **Internal**: `librarian-api:8000`
- **Host Port**: 8001 (via `API_HOST_PORT`)
- **Library**: Mounted read-only at `/library`
- **Database**: Connects to PostgreSQL via `postgres:5432`
- **Access**: http://localhost:8001

### Librarian Dashboard

- **Internal**: `librarian-dashboard:3000`
- **Host Port**: 3100 (via `DASHBOARD_HOST_PORT`)
- **Purpose**: Operational dashboard for system observability
- **API**: Connects to `librarian-api:8000` via Docker network
- **Access**: http://localhost:3100

### Librarian GUI (Optional - Legacy)

Uncomment the `librarian-gui` section in `docker-compose.yml` to enable.

### Nginx (Optional)

Uncomment the `nginx` section in `docker-compose.yml` and configure `nginx/nginx.conf` for reverse proxy.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | librarian | Database name (internal) |
| `POSTGRES_USER` | librarian | Database user (internal) |
| `POSTGRES_PASSWORD` | librarian | Database password (internal) |
| `API_HOST_PORT` | 8001 | API host port (internal: 8000) |
| `DASHBOARD_HOST_PORT` | 3100 | Dashboard host port (internal: 3000) |
| `LIBRARY_PATH` | ./volumes/library | Host path to library |

## Management Scripts

### Backup

```bash
# Create a backup
./scripts/backup.sh

# Create a named backup
./scripts/backup.sh my_backup_20260115
```

Backups are saved to `backups/` directory with `.dump` and `.meta` files.

### Restore

```bash
# List available backups
ls backups/*.dump

# Restore from backup
./scripts/restore.sh librarian_backup_20260115_120000
```

### Wait for PostgreSQL

```bash
./scripts/wait-for-postgres.sh
```

Useful for custom startup scripts.

## Stopping the Stack

```bash
docker compose down
```

To remove volumes (including database data):

```bash
docker compose down -v
```

## Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f librarian-api
docker compose logs -f postgres
```

### Check Status

```bash
docker compose ps
```

## Troubleshooting

### API Won't Start

1. Check if PostgreSQL is healthy:
   ```bash
   docker compose ps postgres
   ```

2. View API logs:
   ```bash
   docker compose logs librarian-api
   ```

3. Verify environment variables:
   ```bash
   docker compose config
   ```

### Database Connection Issues

1. Ensure PostgreSQL is running:
   ```bash
   docker compose up -d postgres
   ```

2. Wait for PostgreSQL to be ready:
   ```bash
   ./scripts/wait-for-postgres.sh
   ```

3. Check DATABASE_URL format:
   ```
   postgresql://user:password@host:port/dbname
   ```

### Library Not Being Scanned

1. Verify volume mount:
   ```bash
   docker compose exec librarian-api ls -la /library
   ```

2. Check LIBRARY_PATH in `.env` points to correct directory

3. Ensure files exist in the mounted directory

## Security Notes

1. **Change default passwords** in production
2. **Use TLS** in production (configure nginx)
3. **Restrict library access** to read-only when possible
4. **Regular backups** using `./scripts/backup.sh`

## Future Features

- GUI accessible at http://localhost:8080 (when enabled, legacy)
- Nginx reverse proxy (when enabled)
- Automated backups via cron
- API authentication and authorization
