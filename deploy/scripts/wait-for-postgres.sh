#!/bin/bash
# Wait for PostgreSQL Script
#
# Waits for PostgreSQL to be ready before starting dependent services.
# This is used in startup scripts to ensure the database is available.
#
# Usage:
#   ./wait-for-postgres.sh [timeout]
#
# Arguments:
#   timeout: Maximum seconds to wait (default: 60)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Load environment variables
if [ -f "$PARENT_DIR/.env" ]; then
    source "$PARENT_DIR/.env"
fi

# Configuration with defaults
POSTGRES_USER="${POSTGRES_USER:-librarian}"
POSTGRES_DB="${POSTGRES_DB:-librarian}"
TIMEOUT="${1:-60}"
INTERVAL=2

echo "Waiting for PostgreSQL to be ready..."
echo "  Host: postgres"
echo "  User: $POSTGRES_USER"
echo "  Database: $POSTGRES_DB"
echo "  Timeout: ${TIMEOUT}s"

ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker compose -f "$PARENT_DIR/docker-compose.yml" exec -T postgres \
        pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
        echo ""
        echo "PostgreSQL is ready!"
        exit 0
    fi
    
    echo -n "."
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""
echo "ERROR: Timeout waiting for PostgreSQL"
exit 1
