#!/bin/bash
# Librarian Deployment - Status Script
# Display running containers, health status, queue depth, and statistics.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if jq is available for JSON parsing
JQ_AVAILABLE=false
if command -v jq &> /dev/null; then
    JQ_AVAILABLE=true
fi

# Get API health status
get_api_status() {
    if curl -sf http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${RED}UNHEALTHY${NC}"
    fi
}

# Get Dashboard health status
get_dashboard_status() {
    if curl -sf http://localhost:3100/health > /dev/null 2>&1; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${RED}UNHEALTHY${NC}"
    fi
}

# Get PostgreSQL status
get_db_status() {
    if docker compose exec -T postgres pg_isready -U librarian -d librarian > /dev/null 2>&1; then
        echo -e "${GREEN}HEALTHY${NC}"
    else
        echo -e "${RED}UNHEALTHY${NC}"
    fi
}

# Get worker count
get_worker_count() {
    # Count running worker containers
    local count=$(docker compose ps --filter "name=librarian-worker" --status running -q 2>/dev/null | wc -l)
    if [ -z "$count" ] || [ "$count" -eq 0 ]; then
        # Fallback: check container name pattern
        count=$(docker ps --filter "name=librarian-worker" --format "{{.Names}}" 2>/dev/null | wc -l)
    fi
    echo "${count:-0}"
}

# Get container count
get_container_count() {
    local count=$(docker compose ps -q 2>/dev/null | wc -l)
    if [ -z "$count" ] || [ "$count" -eq 0 ]; then
        count=$(docker ps --filter "name=librarian" --format "{{.Names}}" 2>/dev/null | wc -l)
    fi
    echo "${count:-0}"
}

# Get queue depth from API
get_queue_depth() {
    if [ "$JQ_AVAILABLE" = true ]; then
        local stats=$(curl -sf http://localhost:8001/api/v1/stats 2>/dev/null)
        if [ -n "$stats" ]; then
            local pending=$(echo "$stats" | jq -r '.pending // .queue_depth // 0')
            echo "${pending} queued"
            return
        fi
    fi
    
    # Fallback: show "unknown" if we can't get queue info
    echo "unknown"
}

# Get document count from API
get_document_count() {
    if [ "$JQ_AVAILABLE" = true ]; then
        local stats=$(curl -sf http://localhost:8001/api/v1/stats 2>/dev/null)
        if [ -n "$stats" ]; then
            local docs=$(echo "$stats" | jq -r '.document_count // .documents // 0')
            echo "${docs}"
            return
        fi
    fi
    
    # Fallback: show "unknown" if we can't get document count
    echo "unknown"
}

# Get database size
get_db_size() {
    local size=$(docker compose exec -T postgres psql -U librarian -d librarian -t -c "SELECT pg_size_pretty(pg_database_size('librarian'));" 2>/dev/null | tr -d '[:space:]')
    if [ -n "$size" ] && [ "$size" != "" ]; then
        echo "$size"
    else
        echo "unknown"
    fi
}

# Display status
echo ""
echo "┌─────────────────────────────────────────┐"
echo "│         Librarian Deployment Status     │"
echo "└─────────────────────────────────────────┘"
echo ""
printf "%-12s %s\n" "API:" "$(get_api_status)"
printf "%-12s %s\n" "Dashboard:" "$(get_dashboard_status)"
printf "%-12s %s\n" "Database:" "$(get_db_status)"
printf "%-12s %s\n" "Workers:" "$(get_worker_count)"
printf "%-12s %s\n" "Documents:" "$(get_document_count)"
printf "%-12s %s\n" "Queue:" "$(get_queue_depth)"
printf "%-12s %s\n" "DB Size:" "$(get_db_size)"
printf "%-12s %s\n" "Containers:" "$(get_container_count) running"
echo ""
echo "─────────────────────────────────────────"
echo ""

# Show container details
echo "Container Details:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker ps --filter "name=librarian" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers running"
echo ""

# Show quick links
echo "Quick Links:"
echo "  Health:     http://localhost:8001/health"
echo "  API:        http://localhost:8001/docs"
echo "  Dashboard:  http://localhost:3100"
echo "  Stats:      http://localhost:8001/api/v1/stats"