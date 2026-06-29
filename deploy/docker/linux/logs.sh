#!/bin/bash
# Librarian Deployment - Logs Script
# Interactive log viewer for containers.
#
# Usage:
#   ./logs.sh api        # View API logs
#   ./logs.sh worker     # View worker logs
#   ./logs.sh postgres   # View PostgreSQL logs
#   ./logs.sh all        # View all logs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_usage() {
    echo "Librarian Logs Viewer"
    echo ""
    echo "Usage: $0 <service>"
    echo ""
    echo "Services:"
    echo "  api       - View API server logs"
    echo "  worker    - View worker logs"
    echo "  postgres  - View PostgreSQL logs"
    echo "  all       - View all logs (default)"
    echo ""
    echo "Options:"
    echo "  -h, --help    Show this help message"
    echo "  -n <lines>    Number of lines to show (default: 100)"
    echo "  --since <time> Show logs since duration (e.g., 5m, 1h)"
    echo "  --tail <n>    Number of lines to show from end (default: 100)"
    echo ""
    echo "Examples:"
    echo "  $0 api"
    echo "  $0 worker"
    echo "  $0 all --since 30m"
    echo "  $0 postgres -n 200"
    echo ""
}

# Parse arguments
SERVICE="all"
LINES=100
SINCE=""
TAIL_FLAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        api)
            SERVICE="api"
            shift
            ;;
        worker)
            SERVICE="worker"
            shift
            ;;
        postgres)
            SERVICE="postgres"
            shift
            ;;
        all)
            SERVICE="all"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -n)
            LINES="$2"
            shift 2
            ;;
        --since)
            SINCE="$2"
            shift 2
            ;;
        --tail)
            TAIL_FLAG="-n $2"
            LINES="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Build docker compose logs command
LOG_CMD="docker compose logs"

if [ -n "$TAIL_FLAG" ]; then
    LOG_CMD="$LOG_CMD -n $LINES"
elif [ -n "$SINCE" ]; then
    LOG_CMD="$LOG_CMD --since $SINCE"
else
    LOG_CMD="$LOG_CMD -n $LINES"
fi

# Color mapping for services
show_header() {
    local name=$1
    printf "\n${BLUE}═══════════════════════════════════════════════════${NC}\n"
    printf "${BLUE}  %s${NC}\n" "$name"
    printf "${BLUE}═══════════════════════════════════════════════════${NC}\n\n"
}

# Execute logs command based on service
case $SERVICE in
    api)
        show_header "Librarian API Logs"
        $LOG_CMD librarian-api -f
        ;;
    worker)
        show_header "Librarian Worker Logs"
        $LOG_CMD librarian-worker -f
        ;;
    postgres)
        show_header "PostgreSQL Logs"
        $LOG_CMD postgres -f
        ;;
    all)
        # Use docker compose follow for all services
        show_header "All Librarian Logs"
        $LOG_CMD -f
        ;;
esac