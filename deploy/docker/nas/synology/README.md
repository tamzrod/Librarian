# Librarian Deployment - Synology NAS

Deploy Librarian on Synology NAS using Docker.

## Architecture

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only

## Prerequisites

- Synology NAS with DSM 7.0+
- Container Manager package installed
- SSH access to NAS (optional but recommended)

## Library Path Examples for Synology

| Path | Description |
|------|-------------|
| `/volume1/Documents` | Default documents folder |
| `/volume1/PhotoLibrary` | Photo library |
| `/volume2/Work` | Secondary volume |
| `/volume1/homes/user/Documents` | User home documents |

## Installation via SSH

### 1. Connect to NAS

```bash
ssh admin@your-nas-ip
sudo -i
```

### 2. Create Directory

```bash
mkdir -p /volume1/docker/librarian
cd /volume1/docker/librarian
```

### 3. Download Configuration

Copy the contents of `deploy/docker/nas/synology/` to your NAS.

### 4. Configure Environment

```bash
cp .env.example .env
nano .env
```

Configure:
```env
POSTGRES_PASSWORD=your_secure_password
API_HOST_PORT=8000
LIBRARY_PATH=/volume1/Documents
```

### 5. Start Services

```bash
docker compose up -d
```

## Installation via Synology Container Manager (GUI)

### 1. Open Container Manager

Navigate to: **Package Center → Container Manager → Install**

### 2. Create Project

1. **Project → Create**
2. Name: `librarian`
3. Path: Choose your deployment folder
4. Source: Upload `docker-compose.yml`
5. Environment: Add variables from `.env.example`

### 3. Configure Volumes

| Host Path | Container Path | Mode |
|-----------|----------------|------|
| `/volume1/Documents` | `/library` | Read-only |
| `librarian_postgres_data` | `/var/lib/postgresql/data` | Read-write |

### 4. Start Project

Click **Next** → **Done**

## Accessing the API

Find the API port in Container Manager or connect via SSH:

- **Local**: http://localhost:8000/docs
- **Network**: http://your-nas-ip:8000/docs

## Accessing the GUI (Optional)

After starting services, access the optional GUI at:
- **Network**: http://your-nas-ip:8080

## Automatic Ingestion

**There is no:**
- ❌ Collection management
- ❌ Folder picker
- ❌ Import wizard
- ❌ Manual indexing button

Librarian **automatically and recursively** discovers all files under the library root. Automatic ingestion begins immediately after startup.

## Common Commands

### Via SSH

```bash
# Navigate to directory
cd /volume1/docker/librarian

# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Restart
docker compose restart
```

### Via Container Manager

Use the web interface for start/stop operations.

## Backup

### Database Backup

```bash
cd /volume1/docker/librarian
docker compose exec postgres pg_dump -U librarian librarian > backup_$(date +%Y%m%d).sql
```

### Backup to Synology

```bash
# Save to shared folder
docker compose exec postgres pg_dump -U librarian librarian > /volume1/Backups/librarian_backup_$(date +%Y%m%d).sql
```

## Restore

```bash
docker compose exec -T postgres psql -U librarian librarian < backup_file.sql
```

## Upgrading

```bash
cd /volume1/docker/librarian
docker compose pull
docker compose up -d
```

## Troubleshooting

### Container Won't Start

Check logs:
```bash
docker compose logs librarian-api
docker compose logs postgres
```

### Permission Denied

Ensure the Docker user has access to the library folder:
```bash
# Check permissions
ls -la /volume1/Documents

# Fix permissions if needed
chmod 755 /volume1/Documents
```

### Port Already in Use

Change `API_HOST_PORT` in `.env`:
```env
API_HOST_PORT=8001
```

### Database Connection Issues

Check PostgreSQL is healthy:
```bash
docker compose ps postgres
```

## Data Persistence

Database data is stored in Docker volume `librarian_postgres_data`.

To backup:
```bash
docker run --rm -v librarian_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup.tar.gz -C /data .
```

## Security Notes

1. **Change default passwords** in production
2. **Use strong PostgreSQL password**
3. **Configure firewall** to restrict API access
4. **Use TLS** via reverse proxy for remote access
5. **Restrict library access** to read-only when possible
