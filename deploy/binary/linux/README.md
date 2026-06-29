# Librarian Linux Binary Deployment

Standalone Linux executable for Librarian.

## Architecture

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only

## Prerequisites

- Linux (64-bit)
- glibc 2.17+
- PostgreSQL 16+ (or use built-in SQLite for portable mode)

## Installation

### Option 1: Installer (Future)

```bash
sudo apt install ./librarian-api.deb
```

### Option 2: Portable (Future)

1. Download `Librarian-linux.tar.gz`
2. Extract to any directory
3. Run `./LibrarianAPI`

### Option 3: Build from Source

```bash
cd deploy/binary/linux
chmod +x build.sh
./build.sh
```

## Library Configuration

### Via Environment Variable

```bash
export LIBRARIAN_LIBRARY_ROOT=/home/user/Documents
```

### Via Command Line

```bash
./LibrarianAPI --library /home/user/Documents
```

### Via Configuration File

Create `config.env`:
```
LIBRARIAN_LIBRARY_ROOT=/home/user/Documents
DATABASE_URL=postgresql://librarian:password@localhost:5432/librarian
```

## Automatic Ingestion

**There is no:**
- ❌ Collection management
- ❌ Folder picker
- ❌ Import wizard
- ❌ Manual indexing button

Librarian **automatically and recursively** discovers all files under the library root. Automatic ingestion begins immediately after startup.

## Usage

### Start API Server

```bash
# Default
./LibrarianAPI

# With custom library
./LibrarianAPI --library /mnt/storage

# With custom port
./LibrarianAPI --port 8001
```

### Start GUI

```bash
./LibrarianGUI
```

## Accessing the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Status**: http://localhost:8000/api/v1/status

## Database Configuration

### PostgreSQL

```bash
export DATABASE_URL="postgresql://librarian:password@localhost:5432/librarian"
```

### SQLite (Portable Mode)

```bash
export DATABASE_URL="sqlite:///./librarian.db"
```

## Systemd Service (Optional)

Create `/etc/systemd/system/librarian-api.service`:

```ini
[Unit]
Description=Librarian API Server
After=network.target postgresql.service

[Service]
Type=simple
User=librarian
WorkingDirectory=/opt/librarian
Environment="LIBRARIAN_LIBRARY_ROOT=/home/user/Documents"
Environment="DATABASE_URL=postgresql://librarian:password@localhost:5432/librarian"
ExecStart=/opt/librarian/LibrarianAPI
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable librarian-api
sudo systemctl start librarian-api
```

## Upgrading

1. Stop service: `sudo systemctl stop librarian-api`
2. Replace executable
3. Restart: `sudo systemctl start librarian-api`

## Backup

```bash
pg_dump -U librarian librarian > backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### Port Already in Use

```bash
# Find process
sudo lsof -i :8000

# Kill process
sudo kill <pid>
```

### Permission Denied

```bash
# Fix executable permissions
chmod +x LibrarianAPI

# Fix library permissions
chmod -R 755 /path/to/library
```

## Portable Mode Structure

```
Librarian/
├── LibrarianAPI           # API server
├── LibrarianGUI           # Optional GUI
├── library/              # Your library files
├── database/             # SQLite database
└── config/              # Configuration files
```

## Security Notes

1. Use strong database passwords
2. Run as dedicated user: `sudo useradd -r librarian`
3. Configure firewall: `sudo ufw allow 8000`
4. Consider TLS for production
5. Restrict library permissions
