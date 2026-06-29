# Librarian Windows Package Manager (winget)

Windows Package Manager deployment for Librarian.

## Status

📋 Planned - Not yet implemented

## Prerequisites

- Windows 10 1809+ or Windows 11
- winget installed (included in Windows 11, downloadable for Windows 10)

## Installation (Future)

```powershell
winget install Librarian.API
```

## Configuration

After installation, configure library path:

```powershell
# Via environment variable
$env:LIBRARIAN_LIBRARY_ROOT = "C:\Users\YourName\Documents"

# Or via command line
LibrarianAPI.exe --library "C:\Users\YourName\Documents"
```

## Upgrading

```powershell
winget upgrade Librarian.API
```

## Uninstalling

```powershell
winget uninstall Librarian.API
```

## Package Manifest

Located in `packages/winget/` for future winget publication.

## Architecture Notes

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only
