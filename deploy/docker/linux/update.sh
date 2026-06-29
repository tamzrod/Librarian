#!/bin/bash
# Librarian Deployment - Update Script
# Updates to the latest code and restarts containers while preserving data.

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

# Check if we're in a git repository
if [ ! -d .git ]; then
    fail "Not a git repository. Run this script from the project root."
fi

echo_status "Pulling latest code..."
if ! git pull; then
    fail "Git pull failed. Check your remote and branch."
fi

echo_status "Pulling latest Docker images..."
if ! docker compose pull; then
    fail "Docker image pull failed."
fi

echo_status "Stopping containers..."
docker compose down || true

echo_status "Building images..."
if ! docker compose up -d --build; then
    fail "Docker build/start failed."
fi

echo_status "Waiting for health checks..."
MAX_WAIT=120
INTERVAL=5
WAITED=0

wait_for_service() {
    local service=$1
    local url=$2
    local name=$3
    
    while [ $WAITED -lt $MAX_WAIT ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            return 0
        fi
        sleep $INTERVAL
        WAITED=$((WAITED + INTERVAL))
    done
    return 1
}

# Wait for API health
wait_for_service "api" "http://localhost:8000/health" "API" || {
    echo_warn "API health check timed out after ${MAX_WAIT}s"
}

echo ""
echo_status "Checking service status..."

# Display service status
docker compose ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || echo_warn "Could not get container status"

# Display health endpoint if available
echo ""
echo_status "Health endpoint response:"
curl -s http://localhost:8000/health 2>/dev/null || echo_warn "Could not reach health endpoint"

echo ""
echo -e "${GREEN}Done.${NC}"