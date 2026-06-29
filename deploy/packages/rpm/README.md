# Librarian RPM Package

Fedora/RHEL/CentOS package deployment for Librarian.

## Status

📋 Planned - Not yet implemented

## Prerequisites

- Fedora 36+ / RHEL 8+ / CentOS Stream 8+
- Root or sudo access

## Installation (Future)

```bash
# Download package
wget https://releases.librarian.dev/librarian-api-latest.x86_64.rpm

# Install
sudo dnf install ./librarian-api-latest.x86_64.rpm
```

## Configuration

After installation, configure:

```bash
# Set library path in environment
sudo bash -c 'echo "LIBRARIAN_LIBRARY_ROOT=/home/user/Documents" >> /etc/librarian/env'
sudo bash -c 'echo "DATABASE_URL=postgresql://librarian:password@localhost:5432/librarian" >> /etc/librarian/env'

# Restart service
sudo systemctl restart librarian-api
```

## Usage

```bash
# Start service
sudo systemctl start librarian-api

# Enable on boot
sudo systemctl enable librarian-api

# View status
sudo systemctl status librarian-api

# View logs
sudo journalctl -u librarian-api -f
```

## Upgrading

```bash
sudo dnf update ./librarian-api-latest.x86_64.rpm
sudo systemctl restart librarian-api
```

## Uninstalling

```bash
sudo dnf remove librarian-api
```

## Package Spec File

Located in `packages/rpm/` for future RPM build.

## Architecture Notes

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only
