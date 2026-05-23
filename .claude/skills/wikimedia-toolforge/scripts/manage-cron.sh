#!/usr/bin/env bash
# Manage cron jobs for a Toolforge tool
# Usage: ./manage-cron.sh <tool_name> <action> [schedule] [command]

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

TOOL_NAME="${1:-}"
ACTION="${2:-}"

if [ -z "$TOOL_NAME" ] || [ -z "$ACTION" ]; then
    echo -e "${RED}❌ Missing arguments${NC}"
    echo "   Usage: ./manage-cron.sh <tool_name> <action> [args...]"
    echo ""
    echo "   Actions:"
    echo "     list               List cron jobs"
    echo "     add <schedule> <cmd>  Add a cron job"
    echo "     remove <pattern>   Remove jobs matching pattern"
    echo "     clear              Remove all cron jobs"
    echo ""
    echo "   Examples:"
    echo "     ./manage-cron.sh my-tool list"
    echo "     ./manage-cron.sh my-tool add '0 2 * * *' 'python3 /data/project/my-tool/daily.py >> /data/project/my-tool/logs/cron.log 2>&1'"
    echo "     ./manage-cron.sh my-tool remove daily.py"
    exit 1
fi

HOST="${TOOLFORGE_USER:-your-username}@login.toolforge.org"

case "$ACTION" in
    list)
        echo -e "${CYAN}📋 Cron jobs for ${TOOL_NAME}${NC}"
        echo ""
        ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; crontab -l 2>&1" || \
            echo -e "   ${YELLOW}No cron jobs found${NC}"
        ;;

    add)
        SCHEDULE="${3:-}"
        CMD="${4:-}"

        if [ -z "$SCHEDULE" ] || [ -z "$CMD" ]; then
            echo -e "${RED}❌ Missing schedule or command${NC}"
            echo "   Usage: $0 <tool_name> add '<schedule>' '<command>'"
            echo "   Example: $0 my-tool add '0 2 * * *' 'python3 /data/project/my-tool/script.py'"
            exit 1
        fi

        echo -e "${CYAN}➕ Adding cron job to ${TOOL_NAME}${NC}"
        echo -e "   Schedule: ${SCHEDULE}"
        echo -e "   Command:  ${CMD}"
        echo ""

        # Escape for SSH
        ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; (crontab -l 2>/dev/null; echo '${SCHEDULE} ${CMD}') | crontab - 2>&1"
        echo -e "${GREEN}✅ Cron job added${NC}"
        ;;

    remove)
        PATTERN="${3:-}"
        if [ -z "$PATTERN" ]; then
            echo -e "${RED}❌ Missing pattern${NC}"
            echo "   Usage: $0 <tool_name> remove <pattern>"
            echo "   Removes all cron lines containing the pattern."
            exit 1
        fi

        echo -e "${YELLOW}🗑️  Removing cron jobs matching '${PATTERN}' from ${TOOL_NAME}${NC}"
        ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; crontab -l 2>/dev/null | grep -v '${PATTERN}' | crontab - 2>&1"
        echo -e "${GREEN}✅ Removed matching cron jobs${NC}"
        ;;

    clear)
        echo -e "${YELLOW}⚠️  Clearing ALL cron jobs for ${TOOL_NAME}${NC}"
        echo -ne "${YELLOW}Are you sure? (y/n):${NC} "
        read -r CONFIRM
        if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
            ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; crontab -r 2>&1"
            echo -e "${GREEN}✅ All cron jobs cleared${NC}"
        else
            echo -e "${YELLOW}Cancelled${NC}"
        fi
        ;;

    *)
        echo -e "${RED}❌ Unknown action: ${ACTION}${NC}"
        echo "   Valid actions: list, add, remove, clear"
        exit 1
        ;;
esac
