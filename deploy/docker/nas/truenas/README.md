# Librarian Deployment - TrueNAS

Deploy Librarian on TrueNAS using Docker/Jails.

## Architecture

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only

## Prerequisites

- TrueNAS CORE 13.0+ or TrueNAS SCALE (Docker/Containers)
- Dataset created for PostgreSQL data
- Jail/VM for dependencies (CORE) or Container setup (SCALE)

## Library Path Examples for TrueNAS

| Path | Description |
|------|-------------|
| `/mnt/tank/documents` | Main tank documents |
| `/mnt/tank/data/library` | Data pool library |
| `/mnt/pool1/photos` | Photo library |

## Installation via TrueNAS SCALE (Containers)

### 1. Create Dataset

**Storage → Pools → Create Dataset**
- Name: `librarian`
- Share Type: `Generic`

### 2. Create PostgreSQL Dataset

**Storage → Pools → Create Dataset**
- Name: `librarian/postgres`
- Share Type: `Generic`

### 3. Create Containers

Using TrueNAS SCALE's **Apps** or Docker Compose:

#### PostgreSQL

```yaml
# Use in TrueNAS UI or docker-compose
image: postgres:16-alpine
environment:
  POSTGRES_DB: librarian
  POSTGRES_USER: librarian
  POSTGRES_PASSWORD: your_password
volumes:
  - /mnt/tank/librarian/postgres:/var/lib/postgresql/data
```

#### Librarian API

```yaml
image: librarian/api:latest
environment:
  DATABASE_URL: postgresql://librarian:password@postgres:5432/librarian
  LIBRARIAN_LIBRARY_ROOT: /library
volumes:
  - /mnt/tank/documents:/library:ro
ports:
  - "8000:8000"
```

## Installation via TrueNAS CORE (Jails)

### 1. Create Jail

**Jails → Add Jail**
- Name: `librarian-api`
- Base: `12.2-RELEASE`
- Networking: DHCP or Static IP

### 2. Install Dependencies

```bash
# In jail
pkg update
pkg install -y python3 py311-pip postgresql13-server

# Enable PostgreSQL
sysrc postgresql_enable=yes
```

### 3. Configure PostgreSQL

```bash
# Initialize database
/usr/local/etc/rc.d/postgresql oneinit
/usr/local/etc/rc.d/postgresql start

# Create database
su - postgres -c "psql -c \"CREATE DATABASE librarian;\""
su - postgres -c "psql -c \"CREATE USER librarian WITH PASSWORD 'password';\""
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE librarian TO librarian;\""
```

### 4. Install Librarian

```bash
# In jail
pip install librarian

# Configure environment
export DATABASE_URL=postgresql://librarian:password@localhost:5432/librarian
export LIBRARIAN_LIBRARY_ROOT=/mnt/library

# Start
librarian-api
```

## Mounting Library on TrueNAS

### Via SMB Share (Recommended)

1. **Shares → Windows (SMB) → Add**
2. Path: `/mnt/tank/documents`
3. Configure as read-only for container

### Via NFS

1. **Shares → Unix (NFS) → Add**
2. Path: `/mnt/tank/documents`

## Automatic Ingestion

**There is no:**
- ❌ Collection management
- ❌ Folder picker
- ❌ Import wizard
- ❌ Manual indexing button

Librarian **automatically and recursively** discovers all files under the library root. Automatic ingestion begins immediately after startup.

## Accessing the API

- **Local**: http://localhost:8000/docs
- **Network**: http://your-truenas-ip:8000/docs

## Common Commands

### TrueNAS SCALE

```bash
# Via Docker/Container CLI
docker compose -f /mnt/tank/appdata/librarian/docker-compose.yml logs -f
```

### TrueNAS CORE

```bash
# In jail
service postgresql status
librarian-api status
```

## Upgrading

### TrueNAS SCALE

```bash
docker compose pull
docker compose up -d
```

### TrueNAS CORE

```bash
# In jail
pip install --upgrade librarian
service librarian-api restart
```

## Backup

### Database Backup (SCALE)

```bash
docker compose exec postgres pg_dump -U librarian librarian > /mnt/tank/backups/librarian_backup_$(date +%Y%m%d).sql
```

### Database Backup (CORE)

```bash
# In jail as postgres user
pg_dump -U librarian librarian > /mnt/tank/backups/librarian_backup_$(date +%Y%m%d).sql
```

## Restore

```bash
docker compose exec -T postgres psql -U librarian librarian < backup_file.sql
```

## Troubleshooting

### TrueNAS SCALE

Check container logs:
```bash
docker compose logs -f librarian-api
```

### TrueNAS CORE

Check service status:
```bash
service postgresql status
ps aux | grep librarian
```

## Data Persistence

Store data on fast pool (SSD) for better performance:
```
/mnt/tank/librarian/postgres
```

## Security Notes

1. Change default PostgreSQL password
2. Use TrueNAS's built-in user management
3. Configure firewall for API access
4. Consider VPN for remote access
5. Restrict library share to read-only
