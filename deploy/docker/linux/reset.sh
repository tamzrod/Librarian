#!/bin/bash
# Librarian Deployment - Reset Script
# DESTROYS the entire environment and recreates from scratch.
# WARNING: This will delete all database data and reset the environment.

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

# Display warning
echo ""
echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║           WARNING: This will destroy all data!                 ║${NC}"
echo -e "${RED}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${RED}║  This script will:                                            ║${NC}"
echo -e "${RED}║  - Remove all containers                                      ║${NC}"
echo -e "${RED}║  - Delete PostgreSQL database (ALL DATA WILL BE LOST)        ║${NC}"
echo -e "${RED}║  - Remove Docker system cache                                 ║${NC}"
echo -e "${RED}║  - Rebuild and start fresh containers                         ║${NC}"
echo -e "${RED}║                                                                ║${NC}"
echo -e "${RED}║  Your library files will NOT be deleted, but the database     ║${NC}"
echo -e "${RED}║  index will be rebuilt from scratch.                          ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Prompt for confirmation
read -p "Are you sure you want to continue? Type 'yes' to confirm: " confirm

if [ "$confirm" != "yes" ]; then
    echo_status "Reset cancelled."
    exit 0
fi

echo_status "Stopping and removing containers..."
docker compose down -v || true

echo_status "Pruning Docker system..."
docker system prune -f

echo_status "Building images..."
if ! docker compose up -d --build; then
    fail "Docker build/start failed."
fi

echo ""
echo_status "Checking service status..."
docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || echo_warn "Could not get container status"

echo ""
echo -e "${GREEN}Reset complete.${NC}"
echo ""
echo_warn "Database has been reset. Re-indexing will begin automatically."