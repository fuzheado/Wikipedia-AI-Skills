#!/usr/bin/env bash
# Setup SSH tunnel to Toolforge for Wikimedia database access
# Usage: ./setup-tunnel.sh [db_host] [local_port]
#   db_host:   Replica host (default: enwiki.analytics.db.svc.wikimedia.cloud)
#   local_port: Local port for tunnel (default: 3307)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

DB_HOST="${1:-enwiki.analytics.db.svc.wikimedia.cloud}"
LOCAL_PORT="${2:-${TOOLFORGE_DB_PORT:-3307}}"

echo -e "${CYAN}🔌 Wikimedia Database Tunnel Setup${NC}"
echo -e "  Target:  ${DB_HOST}:3306"
echo -e "  Local:   127.0.0.1:${LOCAL_PORT}"
echo ""

# ──────────────────────────────────
# 1. Check prerequisites
# ──────────────────────────────────

if [ -z "${TOOLFORGE_USER:-}" ]; then
    echo -e "${RED}❌ TOOLFORGE_USER is not set${NC}"
    echo "   Set it in your environment or .env file:"
    echo "   export TOOLFORGE_USER='your-toolforge-username'"
    exit 1
fi

# Check for ssh-agent
ssh-add -l &>/dev/null || {
    echo -e "${YELLOW}⚠️  ssh-agent not running or no keys added${NC}"
    echo "   Start it:  eval \"\$(ssh-agent -s)\" && ssh-add ~/.ssh/id_ed25519"
    echo "   (or your appropriate private key path)"
    exit 1
}

echo -e "${GREEN}✅ TOOLFORGE_USER=${TOOLFORGE_USER}${NC}"
echo -e "${GREEN}✅ SSH agent has keys${NC}"

# ──────────────────────────────────
# 2. Check if tunnel is already up
# ──────────────────────────────────

if command -v nc &>/dev/null; then
    if nc -z 127.0.0.1 "$LOCAL_PORT" 2>/dev/null; then
        echo -e "${GREEN}✅ Tunnel already active on 127.0.0.1:${LOCAL_PORT}${NC}"
        echo "   Process info:"
        lsof -i :"$LOCAL_PORT" 2>/dev/null | head -3 || true
        exit 0
    fi
elif command -v lsof &>/dev/null; then
    if lsof -i :"$LOCAL_PORT" &>/dev/null; then
        echo -e "${GREEN}✅ Tunnel already active on 127.0.0.1:${LOCAL_PORT}${NC}"
        exit 0
    fi
fi

# ──────────────────────────────────
# 3. Establish tunnel
# ──────────────────────────────────

echo -e "${CYAN}🔗 Establishing tunnel...${NC}"

# Check for autossh (preferred for persistence)
if command -v autossh &>/dev/null; then
    echo -e "   Using ${GREEN}autossh${NC} (auto-reconnecting)"
    autossh -M 0 \
        -o "ServerAliveInterval 30" \
        -o "ServerAliveCountMax 3" \
        -o "ExitOnForwardFailure yes" \
        -L "${LOCAL_PORT}:${DB_HOST}:3306" \
        "${TOOLFORGE_USER}@login.toolforge.org" \
        -N -v &
    AUTOSSH_PID=$!
    sleep 2
    echo -e "   autossh PID: ${AUTOSSH_PID}"
else
    echo -e "   Using ${YELLOW}ssh${NC} (consider 'brew install autossh' for persistence)"
    ssh -L "${LOCAL_PORT}:${DB_HOST}:3306" \
        "${TOOLFORGE_USER}@login.toolforge.org" \
        -N -o "ExitOnForwardFailure yes" &
    SSH_PID=$!
    sleep 3
    echo -e "   ssh PID: ${SSH_PID}"
fi

# ──────────────────────────────────
# 4. Verify tunnel
# ──────────────────────────────────

sleep 2
if command -v nc &>/dev/null && nc -z 127.0.0.1 "$LOCAL_PORT" 2>/dev/null; then
    echo -e "${GREEN}✅ Tunnel established on 127.0.0.1:${LOCAL_PORT}${NC}"
    echo ""
    echo -e "   To test:  ./scripts/query.sh \"SELECT 1\""
    echo -e "   To close: ./scripts/close-tunnel.sh"
else
    echo -e "${RED}❌ Tunnel may not be ready yet${NC}"
    echo "   Check with: lsof -i :${LOCAL_PORT}"
    echo "   Or try running manually:"
    echo "     ssh -L ${LOCAL_PORT}:${DB_HOST}:3306 ${TOOLFORGE_USER}@login.toolforge.org -N"
fi
