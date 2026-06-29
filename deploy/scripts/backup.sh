#!/bin/bash
# Librarian Backup Script
#
# Creates a backup of the PostgreSQL database and optionally
# the library volume.
#
# Usage:
#   ./backup.sh [backup_name]
#
# Environment variables (from .env):
#   POSTGRES_USER: PostgreSQL user (default: librarian)
#   POSTGRES_DB: PostgreSQL database name (default: librarian)

set -e

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$PARENT_DIR/.env" ]; then
    source "$PARENT_DIR/.env"
fi

# Configuration with defaults
POSTGRES_USER="${POSTGRES_USER:-librarian}"
POSTGRES_DB="${POSTGRES_DB:-librarian}"
BACKUP_DIR="${BACKUP_DIR:-$PARENT_DIR/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${1:-librarian_backup_${TIMESTAMP}}"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "=== Librarian Backup ==="
echo "Backup name: $BACKUP_NAME"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
docker compose -f "$PARENT_DIR/docker-compose.yml" exec -T postgres \
    pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --no-owner --no-acl --format=custom \
    > "$BACKUP_DIR/${BACKUP_NAME}.dump"

echo "Database backup complete: $BACKUP_DIR/${BACKUP_NAME}.dump"

# Optional: Backup library metadata (not the files themselves)
# Library files should be backed up separately using your backup strategy
echo ""
echo "Note: Library files are NOT included in this backup."
echo "Use your standard backup strategy for the library volume:"
echo "  $LIBRARY_PATH"

# Create metadata file
cat > "$BACKUP_DIR/${BACKUP_NAME}.meta" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$(date -Iseconds)",
    "database": "$POSTGRES_DB",
    "user": "$POSTGRES_USER",
    "type": "database"
}
EOF

echo ""
echo "Backup complete!"
echo "Files:"
echo "  - $BACKUP_DIR/${BACKUP_NAME}.dump"
echo "  - $BACKUP_DIR/${BACKUP_NAME}.meta"

# List recent backups
echo ""
echo "Recent backups:"
ls -lh "$BACKUP_DIR"/*.dump 2>/dev/null | tail -5 || echo "No backups found"
