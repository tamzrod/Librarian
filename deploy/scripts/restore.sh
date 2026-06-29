#!/bin/bash
# Librarian Restore Script
#
# Restores a PostgreSQL database from a backup.
#
# Usage:
#   ./restore.sh backup_name
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

# Check for backup name argument
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_name>"
    echo ""
    echo "Available backups:"
    ls -1 "$BACKUP_DIR"/*.dump 2>/dev/null || echo "No backups found in $BACKUP_DIR"
    exit 1
fi

BACKUP_NAME="$1"
BACKUP_PATH="$BACKUP_DIR/${BACKUP_NAME}.dump"

if [ ! -f "$BACKUP_PATH" ]; then
    echo "Error: Backup file not found: $BACKUP_PATH"
    exit 1
fi

echo "=== Librarian Restore ==="
echo "Backup: $BACKUP_PATH"
echo "Database: $POSTGRES_DB"
echo ""

# Confirm before restoring
echo "WARNING: This will replace all existing data in the database!"
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "Restoring database..."

# Stop the API to prevent connections during restore
echo "Stopping API..."
docker compose -f "$PARENT_DIR/docker-compose.yml" stop librarian-api || true

# Restore the database
docker compose -f "$PARENT_DIR/docker-compose.yml" exec -T postgres \
    pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    --clean --if-exists --no-owner --no-acl \
    < "$BACKUP_PATH"

echo ""
echo "Restarting API..."
docker compose -f "$PARENT_DIR/docker-compose.yml" start librarian-api

echo ""
echo "Restore complete!"
