# Librarian Debian/Ubuntu Package (deb)

Debian/Ubuntu package deployment for Librarian.

## Status

📋 Planned - Not yet implemented

## Prerequisites

- Debian 11+ or Ubuntu 20.04+
- Root or sudo access

## Installation (Future)

```bash
# Download package
wget https://releases.librarian.dev/librarian-api_latest_amd64.deb

# Install
sudo dpkg -i librarian-api_latest_amd64.deb

# Or use gdebi
sudo gdebi librarian-api_latest_amd64.deb
```

## Configuration

After installation, configure:

```bash
# Set library path in environment
echo 'LIBRARIAN_LIBRARY_ROOT=/home/user/Documents' | sudo tee /etc/librarian/env
echo 'DATABASE_URL=postgresql://librarian:password@localhost:5432/librarian' | sudo tee -a /etc/librarian/env

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
# Download new package
wget https://releases.librarian.dev/librarian-api_new_amd64.deb

# Install
sudo dpkg -i librarian-api_new_amd64.deb

# Restart
sudo systemctl restart librarian-api
```

## Uninstalling

```bash
sudo dpkg -r librarian-api
```

## Package Structure

```
librarian-api/
├── DEBIAN/
│   ├── control
│   ├── postinst
│   └── prerm
├── usr/
│   ├── bin/librarian-api
│   └── lib/librarian/
│       └── ...
└── etc/
    └── librarian/
        └── env
```

## Architecture Notes

**Single-Library Model:**
- One library root per deployment
- Automatic recursive file discovery
- API-First: REST API is the primary interface
- GUI is optional, communicates via API only
