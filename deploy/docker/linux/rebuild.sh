#!/bin/bash
# Librarian Deployment - Rebuild Script
# Force a clean rebuild while preserving persistent data (PostgreSQL, library contents).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

fail() {
    echo_error "$1"
    exit 1
}

echo_status "Stopping containers..."
docker compose down || true

echo_status "Building images (no cache)..."
if ! docker compose build --no-cache; then
    fail "Docker build failed."
fi

echo_status "Starting containers..."
if ! docker compose up -d; then
    fail "Docker start failed."
fi

echo ""
echo_status "Checking service status..."
docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || echo_warn "Could not get container status"

echo ""
echo -e "${GREEN}Done.${NC}"
echo ""
echo_status "Data preserved:"
echo "  - PostgreSQL volume (postgres_data)"
echo "  - Library contents (\${LIBRARY_PATH:-./volumes/library})"