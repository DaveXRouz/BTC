#!/usr/bin/env bash
# NPS V4 Health Check — reports status for all docker-compose services
set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="$(dirname "$SCRIPT_DIR")"

cd "$COMPOSE_DIR"

SERVICES=(postgres redis oracle-service scanner-service api frontend nginx)
TOTAL=0
HEALTHY=0
UNHEALTHY=0
NOT_RUNNING=0

echo "NPS V4 Health Check"
echo "==================="
echo ""

for svc in "${SERVICES[@]}"; do
    TOTAL=$((TOTAL + 1))
    STATUS=$(docker compose ps --format json "$svc" 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        data = data[0] if data else {}
    print(data.get('Health', data.get('health', 'unknown')))
except Exception:
    print('not_running')
" 2>/dev/null || echo "not_running")

    case "$STATUS" in
        healthy)
            echo -e "  ${GREEN}[PASS]${NC} $svc"
            HEALTHY=$((HEALTHY + 1))
            ;;
        unhealthy)
            echo -e "  ${RED}[FAIL]${NC} $svc (unhealthy)"
            UNHEALTHY=$((UNHEALTHY + 1))
            ;;
        starting)
            echo -e "  ${YELLOW}[WAIT]${NC} $svc (starting)"
            UNHEALTHY=$((UNHEALTHY + 1))
            ;;
        *)
            echo -e "  ${RED}[----]${NC} $svc (not running)"
            NOT_RUNNING=$((NOT_RUNNING + 1))
            ;;
    esac
done

echo ""
echo "-------------------"
echo "Total: $TOTAL | Healthy: $HEALTHY | Unhealthy: $UNHEALTHY | Not running: $NOT_RUNNING"

if [ "$HEALTHY" -eq "$TOTAL" ]; then
    echo -e "${GREEN}All services healthy.${NC}"
    exit 0
else
    echo -e "${RED}Some services are not healthy.${NC}"
    exit 1
fi
