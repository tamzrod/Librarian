# Librarian Windows Binary Deployment

Standalone Windows executables for Librarian.

## Architecture

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only

## Prerequisites

- Windows 10/11 (64-bit)
- PostgreSQL 16+ (or use built-in SQLite for portable mode)

## Installation

### Option 1: Installer (Future)

Download `LibrarianSetup.exe` from releases and run installer.

### Option 2: Portable (Future)

1. Download `LibrarianPortable.zip`
2. Extract to any folder
3. Run `LibrarianAPI.exe` or `LibrarianGUI.exe`

### Option 3: Build from Source

```powershell
cd deploy/binary/windows
.\build.ps1
```

## Library Configuration

### Via Environment Variable

```powershell
$env:LIBRARIAN_LIBRARY_ROOT = "C:\Users\YourName\Documents"
```

### Via Command Line

```powershell
.\LibrarianAPI.exe --library "C:\Users\YourName\Documents"
```

### Via Configuration File

Create `config.env` in the application directory:
```
LIBRARIAN_LIBRARY_ROOT=C:\Users\YourName\Documents
DATABASE_URL=postgresql://user:pass@localhost:5432/librarian
```

## Automatic Ingestion

**There is no:**
- ❌ Collection management
- ❌ Folder picker
- ❌ Import wizard
- ❌ Manual indexing button

Librarian **automatically and recursively** discovers all files under the library root. Automatic ingestion begins immediately after startup.

## Usage

### API Server

```powershell
# Start API server
.\LibrarianAPI.exe

# With custom library path
.\LibrarianAPI.exe --library "D:\MyLibrary"

# With custom port
.\LibrarianAPI.exe --port 8001
```

### GUI Application

```powershell
# Start GUI
.\LibrarianGUI.exe
```

## Accessing the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Status**: http://localhost:8000/api/v1/status

## Database Configuration

### PostgreSQL

Set connection string:
```powershell
$env:DATABASE_URL = "postgresql://librarian:password@localhost:5432/librarian"
```

### SQLite (Portable Mode)

```powershell
$env:DATABASE_URL = "sqlite:///./librarian.db"
```

## Upgrading

1. Stop running instances
2. Replace executables
3. Restart

## Backup

Database backup:
```powershell
docker exec librarian-postgres pg_dump -U librarian librarian > backup.sql
```

## Troubleshooting

### Port Already in Use

```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process
taskkill /PID <pid> /F
```

### Database Connection Error

Ensure PostgreSQL is running:
```powershell
docker ps | findstr postgres
```

## Portable Mode Structure

```
Librarian/
├── LibrarianAPI.exe     # API server
├── LibrarianGUI.exe     # Optional GUI
├── library/            # Your library files
├── database/           # SQLite database (portable)
└── config/            # Configuration files
```

## Security Notes

1. Use strong database passwords
2. Consider TLS for production
3. Restrict library access when possible
