#!/bin/bash
# Librarian Startup Smoke Test
# Validates the application can start correctly.
#
# This test catches startup regressions like:
# - Missing imports (NameError, ImportError)
# - Missing dependencies
# - Configuration errors
# - Route initialization failures
#
# Usage:
#   ./smoke_test.sh           # Full test with container deployment
#   ./smoke_test.sh --imports # Only test Python imports

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Go up to repository root (from deploy/docker/linux to repo root)
cd "$SCRIPT_DIR/../../.." && REPO_ROOT=$(pwd)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

FAILED=0

pass() {
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    FAILED=1
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

info() {
    echo -e "${BLUE}→${NC} $1"
}

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Librarian Startup Smoke Test"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Parse arguments
MODE="${1:-full}"

case "$MODE" in
    --imports|-i)
        MODE="imports"
        ;;
    --help|-h)
        echo "Usage: $0 [--imports]"
        echo ""
        echo "Modes:"
        echo "  (default)    Full test: imports + docker deployment + health check"
        echo "  --imports    Only test Python imports"
        exit 0
        ;;
esac

# Test 1: Python Import Validation
echo "─────────────────────────────────────────"
info "Test 1: Python Import Validation"
echo "─────────────────────────────────────────"

info "Running import validation tests..."
cd "$REPO_ROOT"
if python tests/test_imports.py > /tmp/import_test.log 2>&1; then
    pass "All FastAPI imports are valid"
else
    fail "Import validation failed"
    cat /tmp/import_test.log
    exit 1
fi

info "Testing api.app import (checks for syntax/import errors)..."
if python -c "
import ast
with open('api/app.py', 'r') as f:
    ast.parse(f.read())
print('Syntax OK')
" > /tmp/syntax_test.log 2>&1; then
    pass "api/app.py syntax is valid"
else
    fail "api/app.py has syntax errors"
    cat /tmp/syntax_test.log
    exit 1
fi

echo ""

if [ "$MODE" = "imports" ]; then
    echo "Import-only mode complete."
    echo ""
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}All import tests passed!${NC}"
        exit 0
    else
        exit 1
    fi
fi

# Test 2: Docker Deployment
echo "─────────────────────────────────────────"
info "Test 2: Docker Deployment"
echo "─────────────────────────────────────────"

cd "$REPO_ROOT/deploy/docker/linux"

info "Building and starting containers..."
if docker compose up -d --build > /tmp/docker_up.log 2>&1; then
    pass "Docker containers started"
else
    fail "Failed to start Docker containers"
    cat /tmp/docker_up.log
    exit 1
fi

info "Waiting for containers to be healthy..."
MAX_WAIT=120
INTERVAL=5
WAITED=0

while [ $WAITED -lt $MAX_WAIT ]; do
    # Check if API container is running
    API_STATUS=$(docker compose ps -q librarian-api 2>/dev/null)
    if [ -n "$API_STATUS" ]; then
        # Check health status
        if docker inspect --format='{{.State.Health.Status}}' librarian-api 2>/dev/null | grep -q "healthy"; then
            break
        fi
        # Check if it's in a restart loop
        RESTARTS=$(docker inspect --format='{{.RestartCount}}' librarian-api 2>/dev/null)
        if [ -n "$RESTARTS" ] && [ "$RESTARTS" -gt 5 ]; then
            fail "API container is in restart loop (restarted $RESTARTS times)"
            echo ""
            info "Container logs:"
            docker compose logs --tail=50 librarian-api
            exit 1
        fi
    fi
    sleep $INTERVAL
    WAITED=$((WAITED + INTERVAL))
    echo -n "."
done
echo ""

if [ $WAITED -ge $MAX_WAIT ]; then
    fail "Containers did not become healthy within ${MAX_WAIT}s"
    echo ""
    info "Container status:"
    docker compose ps
    echo ""
    info "Container logs:"
    docker compose logs --tail=30 librarian-api
    exit 1
fi

pass "Containers are healthy"
echo ""

# Test 3: Dashboard Health Endpoint
echo "─────────────────────────────────────────"
info "Test 3: Dashboard Health Endpoint"
echo "─────────────────────────────────────────"

info "Checking dashboard health endpoint..."
DASHBOARD_HEALTH=$(curl -sf http://localhost:3100/health 2>/dev/null || echo "")
if [ -n "$DASHBOARD_HEALTH" ]; then
    pass "Dashboard health endpoint is reachable"
else
    fail "Dashboard health endpoint returned no response"
    exit 1
fi

echo ""

# Test 4: API Health Endpoint
echo "─────────────────────────────────────────"
info "Test 4: API Health Endpoint"
echo "─────────────────────────────────────────"

info "Checking API health endpoint..."
HEALTH_RESPONSE=$(curl -sf http://localhost:8001/health 2>/dev/null || echo "")
if [ -n "$HEALTH_RESPONSE" ]; then
    pass "API health endpoint is reachable"
    echo ""
    info "Health response:"
    echo "$HEALTH_RESPONSE" | python -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    fail "API health endpoint returned no response"
    exit 1
fi

echo ""

# Test 5: API Status
echo "─────────────────────────────────────────"
info "Test 5: API Status Check"
echo "─────────────────────────────────────────"

info "Checking API status..."
STATUS_RESPONSE=$(curl -sf http://localhost:8001/api/v1/status 2>/dev/null || echo "")
if [ -n "$STATUS_RESPONSE" ]; then
    pass "API status endpoint is reachable"
    echo ""
    info "Status response:"
    echo "$STATUS_RESPONSE" | python -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
else
    warn "API status endpoint returned no response (may be OK if no data)"
fi

echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "  Test Summary"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All smoke tests passed!${NC}"
    echo ""
    echo "Services:"
    docker compose ps --format "table {{.Name}}\t{{.Status}}"
    echo ""
    echo "Quick links:"
    echo "  Dashboard: http://localhost:3100"
    echo "  Health:    http://localhost:8001/health"
    echo "  API:       http://localhost:8001/api/docs"
    echo ""
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    echo ""
    echo "Logs:"
    docker compose logs --tail=20
    exit 1
fi