#!/usr/bin/env bash
# Close the SSH tunnel to Toolforge
# Usage: ./close-tunnel.sh [local_port]
#   local_port: The port the tunnel is listening on (default: 3307)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

LOCAL_PORT="${1:-${TOOLFORGE_DB_PORT:-3307}}"

echo -e "${CYAN}🔌 Closing Tunnel on 127.0.0.1:${LOCAL_PORT}${NC}"

# Find PIDs listening on the tunnel port
PIDS=$(lsof -ti :"$LOCAL_PORT" 2>/dev/null || true)

if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}⚠️  No process found on port ${LOCAL_PORT}${NC}"
    exit 0
fi

echo -e "   Found PIDs: ${PIDS}"

for pid in $PIDS; do
    # Get process name for display
    PROC_NAME=$(ps -p "$pid" -o comm= 2>/dev/null || echo "unknown")
    echo -e "   Killing ${PROC_NAME} (PID ${pid})..."
    kill "$pid" 2>/dev/null || true
done

# Brief wait, then force-kill any survivors
sleep 1
SURVIVORS=$(lsof -ti :"$LOCAL_PORT" 2>/dev/null || true)
if [ -n "$SURVIVORS" ]; then
    echo -e "   ${YELLOW}Force killing survivors: ${SURVIVORS}${NC}"
    for pid in $SURVIVORS; do
        kill -9 "$pid" 2>/dev/null || true
    done
fi

# Final check
if lsof -ti :"$LOCAL_PORT" &>/dev/null; then
    echo -e "${RED}❌ Failed to close tunnel${NC}"
    echo "   Manual: lsof -ti :${LOCAL_PORT} | xargs kill -9"
    exit 1
else
    echo -e "${GREEN}✅ Tunnel closed${NC}"
fi
