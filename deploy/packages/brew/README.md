# Librarian Homebrew Package

Homebrew deployment for macOS and Linux.

## Status

📋 Planned - Not yet implemented

## Prerequisites

- macOS 11+ or Linux
- Homebrew installed

## Installation (Future)

### macOS

```bash
brew tap librarian/tap
brew install librarian-api
```

### Linux

```bash
brew tap librarian/tap
brew install librarian-api
```

## Configuration

After installation, configure:

```bash
# Set library path
export LIBRARIAN_LIBRARY_ROOT=/Users/yourname/Documents

# Set database URL
export DATABASE_URL=postgresql://librarian:password@localhost:5432/librarian
```

Or create a config file at `~/.librarian/env`.

## Usage

```bash
# Start API server
librarian-api

# With custom library
librarian-api --library /Users/yourname/Documents

# As service
brew services start librarian-api
```

## Upgrading

```bash
brew update
brew upgrade librarian-api
```

## Uninstalling

```bash
brew uninstall librarian-api
brew untap librarian/tap
```

## Homebrew Tap Structure

Future tap at `homebrew-tap/librarian-api.rb`

## Architecture Notes

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only
