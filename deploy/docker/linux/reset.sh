#!/bin/bash
# Librarian Deployment - Reset Script
# DESTROYS the entire environment and recreates from scratch.
# WARNING: This will delete database data and derived artifacts.
# NOTE: Plugin dependencies and caches are PRESERVED by default.

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

# Check for --purge-plugins flag to also remove plugin data
PURGE_PLUGINS=false
for arg in "$@"; do
    case $arg in
        --purge-plugins)
            PURGE_PLUGINS=true
            ;;
        --help)
            echo "Usage: $0 [--purge-plugins]"
            echo ""
            echo "Options:"
            echo "  --purge-plugins  Also remove plugin dependencies and caches"
            exit 0
            ;;
    esac
done

# Display warning
echo ""
echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║           WARNING: This will destroy all data!                 ║${NC}"
echo -e "${RED}╠════════════════════════════════════════════════════════════════╣${NC}"
echo -e "${RED}║  This script will:                                            ║${NC}"
echo -e "${RED}║  - Remove all containers                                      ║${NC}"
echo -e "${RED}║  - Delete PostgreSQL database (ALL DATA WILL BE LOST)        ║${NC}"
echo -e "${RED}║  - Delete librarian-data (thumbnails, embeddings, etc.)     ║${NC}"
echo -e "${RED}║  - Remove Docker system cache                                 ║${NC}"
echo -e "${RED}║  - Rebuild and start fresh containers                         ║${NC}"
echo -e "${RED}║                                                                ║${NC}"
echo -e "${RED}║  Your library files will NOT be deleted.                     ║${NC}"
echo -e "${RED}║                                                                ║${NC}"
echo -e "${RED}║  Plugin dependencies and caches are PRESERVED by default.    ║${NC}"
echo -e "${RED}║  Use --purge-plugins to also remove them.                     ║${NC}"
echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Prompt for confirmation
read -p "Are you sure you want to continue? Type 'yes' to confirm: " confirm

if [ "$confirm" != "yes" ]; then
    echo_status "Reset cancelled."
    exit 0
fi

echo_status "Stopping and removing containers..."
# Remove containers but NOT volumes - we'll handle volumes explicitly
docker compose down || true

echo_status "Removing database and librarian-data volumes..."
# Remove only the volumes we want to reset
docker volume rm librarian-postgres_data 2>/dev/null || true
docker volume rm librarian-librarian_data 2>/dev/null || true

# Remove plugin volumes only if explicitly requested
if [ "$PURGE_PLUGINS" = true ]; then
    echo_warn "Purging plugin dependencies and caches..."
    docker volume rm librarian-plugin_dependencies 2>/dev/null || true
    docker volume rm librarian-plugin_cache 2>/dev/null || true
else
    echo_status "Plugin dependencies and caches preserved (use --purge-plugins to remove)"
fi

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
if [ "$PURGE_PLUGINS" != true ]; then
    echo_status "Plugin dependencies and caches are preserved."
fi