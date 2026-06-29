# Librarian macOS Binary Deployment

Standalone macOS executable for Librarian.

## Architecture

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only

## Prerequisites

- macOS 11+ (Big Sur or later)
- Apple Silicon or Intel
- PostgreSQL 16+ (or use built-in SQLite for portable mode)

## Installation

### Option 1: Homebrew (Future)

```bash
brew install librarian-api
```

### Option 2: DMG Installer (Future)

1. Download `Librarian.dmg`
2. Open and drag to Applications
3. Launch from Applications

### Option 3: Portable (Future)

1. Download `Librarian-macos.tar.gz`
2. Extract to any directory
3. Run `./LibrarianAPI`

### Option 4: Build from Source

```bash
cd deploy/binary/macos
chmod +x build.sh
./build.sh
```

## Library Configuration

### Via Environment Variable

```bash
export LIBRARIAN_LIBRARY_ROOT=/Users/yourname/Documents
```

### Via Command Line

```bash
./LibrarianAPI --library /Users/yourname/Documents
```

### Via Configuration File

Create `config.env`:
```
LIBRARIAN_LIBRARY_ROOT=/Users/yourname/Documents
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
./LibrarianAPI --library /Users/yourname/Documents

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

## LaunchAgent (Optional)

Create `~/Library/LaunchAgents/com.librarian.api.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.librarian.api</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/Librarian/LibrarianAPI</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>LIBRARIAN_LIBRARY_ROOT</key>
        <string>/Users/yourname/Documents</string>
        <key>DATABASE_URL</key>
        <string>postgresql://librarian:password@localhost:5432/librarian</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Enable:
```bash
launchctl load ~/Library/LaunchAgents/com.librarian.api.plist
```

## Upgrading

1. Stop service: `launchctl unload ~/Library/LaunchAgents/com.librarian.api.plist`
2. Replace executable
3. Restart: `launchctl load ~/Library/LaunchAgents/com.librarian.api.plist`

## Backup

```bash
pg_dump -U librarian librarian > ~/Documents/librarian_backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### Port Already in Use

```bash
# Find process
lsof -i :8000

# Kill process
kill <pid>
```

### Permission Denied

```bash
# Fix executable permissions
chmod +x LibrarianAPI

# Allow in System Preferences > Security & Privacy
```

### Apple Silicon Performance

Native ARM64 builds recommended for M1/M2/M3 chips.

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
2. macOS may prompt for network access permission
3. Consider app signing for distribution
4. Use TLS for production
5. Restrict library permissions
