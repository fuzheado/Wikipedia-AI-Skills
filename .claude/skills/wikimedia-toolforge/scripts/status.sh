#!/usr/bin/env bash
# Check Toolforge service and job status for a tool
# Usage: ./status.sh <tool_name>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

TOOL_NAME="${1:-}"

if [ -z "$TOOL_NAME" ]; then
    echo -e "${RED}❌ No tool name provided${NC}"
    echo "   Usage: ./status.sh <tool_name>"
    echo "   Checks web service status, jobs, and disk usage for a Toolforge tool."
    exit 1
fi

if [ -z "${TOOLFORGE_USER:-}" ]; then
    echo -e "${YELLOW}⚠️  TOOLFORGE_USER not set. Using 'your-username'.${NC}"
    echo "   Set it: export TOOLFORGE_USER='your-toolforge-username'"
    TOOLFORGE_USER="your-username"
fi

HOST="${TOOLFORGE_USER}@login.toolforge.org"

echo -e "${CYAN}🔍 Toolforge Status Check: ${TOOL_NAME}${NC}"
echo -e "   User: ${TOOLFORGE_USER}"
echo ""

# Web service status
echo -e "${CYAN}📡 Web Service Status${NC}"
ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; webservice --backend=kubernetes python3.11 status 2>&1" || \
ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; webservice --backend=kubernetes node status 2>&1" || \
ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; webservice --backend=kubernetes php8.2 status 2>&1" || \
ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; webservice --backend=kubernetes static status 2>&1" || \
echo -e "   ${YELLOW}Could not determine web service status (no standard backend?)${NC}"
echo ""

# Kubernetes jobs
echo -e "${CYAN}⏳ Kubernetes Jobs${NC}"
ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; toolforge jobs list 2>&1" || \
echo -e "   ${YELLOW}No jobs found or could not list jobs${NC}"
echo ""

# Disk usage
echo -e "${CYAN}💾 Disk Usage${NC}"
ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; du -sh /data/project/${TOOL_NAME}/ 2>&1" || \
echo -e "   ${YELLOW}Could not get disk usage${NC}"
echo ""

# Active SSH sessions for the tool
echo -e "${CYAN}🔌 Active Processes${NC}"
ssh "$HOST" "ps aux | grep ${TOOL_NAME} | grep -v grep | head -10" 2>/dev/null || \
echo -e "   ${YELLOW}No active processes found${NC}"
echo ""

echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}Status check complete for ${TOOL_NAME}${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
