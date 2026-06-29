#!/bin/bash
# Librarian Development Interface
# Single command for daily development operations.
#
# Usage:
#   ./dev.sh update      Update code and restart containers
#   ./dev.sh rebuild     Force clean rebuild (preserves data)
#   ./dev.sh reset       Destroy and recreate everything
#   ./dev.sh status      Show deployment status
#   ./dev.sh logs        Tail logs (see logs.sh for options)
#   ./dev.sh smoke       Run smoke tests
#   ./dev.sh start       Start containers
#   ./dev.sh stop        Stop containers
#   ./dev.sh restart     Restart containers

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_usage() {
    echo -e "${CYAN}Librarian Development Interface${NC}"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  ${GREEN}update${NC}      Update to latest code and restart (preserves data)"
    echo "  ${GREEN}rebuild${NC}     Force clean rebuild (preserves data)"
    echo "  ${GREEN}reset${NC}       Destroy everything and recreate (DESTRUCTIVE)"
    echo "  ${GREEN}status${NC}      Show deployment status"
    echo "  ${GREEN}logs${NC}         Tail logs (use: logs api, logs worker, etc.)"
    echo "  ${GREEN}smoke${NC}        Run smoke tests (imports + docker + health)"
    echo "  ${GREEN}test${NC}         Alias for smoke"
    echo "  ${GREEN}start${NC}        Start containers"
    echo "  ${GREEN}stop${NC}         Stop containers"
    echo "  ${GREEN}restart${NC}      Restart containers"
    echo ""
    echo "Examples:"
    echo "  $0 update"
    echo "  $0 status"
    echo "  $0 logs api"
    echo "  $0 smoke --imports  # Quick import check only"
    echo "  $0 smoke            # Full test with docker"
    echo ""
}

# Main command dispatcher
case "${1:-}" in
    update)
        echo -e "${BLUE}==> Updating deployment...${NC}"
        exec ./update.sh
        ;;
    rebuild)
        echo -e "${BLUE}==> Rebuilding deployment...${NC}"
        exec ./rebuild.sh
        ;;
    reset)
        exec ./reset.sh
        ;;
    status)
        exec ./status.sh
        ;;
    logs)
        shift
        exec ./logs.sh "$@"
        ;;
    smoke|test)
        echo -e "${BLUE}==> Running smoke tests...${NC}"
        exec ./smoke_test.sh "$@"
        ;;
    start)
        echo -e "${BLUE}==> Starting containers...${NC}"
        docker compose up -d
        echo -e "${GREEN}Done.${NC}"
        ;;
    stop)
        echo -e "${BLUE}==> Stopping containers...${NC}"
        docker compose down
        echo -e "${GREEN}Done.${NC}"
        ;;
    restart)
        echo -e "${BLUE}==> Restarting containers...${NC}"
        docker compose restart
        echo -e "${GREEN}Done.${NC}"
        ;;
    -h|--help|help)
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac