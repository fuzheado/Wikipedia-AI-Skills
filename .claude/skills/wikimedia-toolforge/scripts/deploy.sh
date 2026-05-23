#!/usr/bin/env bash
# Deploy files to a Toolforge tool via rsync
# Usage: ./deploy.sh <local_dir> <tool_name> [remote_dir]
#   local_dir:  Local directory containing your tool files
#   tool_name:  Toolforge tool name
#   remote_dir: Remote path (default: /data/project/<tool_name>/)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

LOCAL_DIR="${1:-}"
TOOL_NAME="${2:-}"
REMOTE_DIR="${3:-/data/project/${TOOL_NAME}/}"

if [ -z "$LOCAL_DIR" ] || [ -z "$TOOL_NAME" ]; then
    echo -e "${RED}❌ Missing arguments${NC}"
    echo "   Usage: ./deploy.sh <local_dir> <tool_name> [remote_path]"
    echo ""
    echo "   Examples:"
    echo "     ./deploy.sh ./my-web-app my-web-tool"
    echo "     ./deploy.sh ./scripts/ my-tool /data/project/my-tool/scripts/"
    exit 1
fi

if [ ! -d "$LOCAL_DIR" ]; then
    echo -e "${RED}❌ Local directory not found: ${LOCAL_DIR}${NC}"
    exit 1
fi

if [ -z "${TOOLFORGE_USER:-}" ]; then
    echo -e "${RED}❌ TOOLFORGE_USER is not set${NC}"
    echo "   Set it: export TOOLFORGE_USER='your-toolforge-username'"
    exit 1
fi

echo -e "${CYAN}📦 Deploying to Toolforge${NC}"
echo -e "   Tool:    ${TOOL_NAME}"
echo -e "   Local:   ${LOCAL_DIR}"
echo -e "   Remote:  ${TOOLFORGE_USER}@login.toolforge.org:${REMOTE_DIR}"
echo ""

# Dry-run first
echo -e "${YELLOW}📋 Dry run — showing what would be transferred:${NC}"
rsync -avz --dry-run --exclude '.*' \
    "${LOCAL_DIR}/" \
    "${TOOLFORGE_USER}@login.toolforge.org:${REMOTE_DIR}" 2>&1 | head -30 || {
    echo -e "${RED}❌ rsync dry-run failed. Check your SSH connection.${NC}"
    echo "   Make sure your SSH key is loaded (ssh-add -l) and your Toolforge account exists."
    exit 1
}

# Skip confirmation prompt in non-interactive contexts (e.g., pi)
if [ -t 0 ]; then
    echo ""
    echo -ne "${YELLOW}Proceed with deployment? (y/n):${NC} "
    read -r CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo -e "${YELLOW}Deployment cancelled.${NC}"
        exit 0
    fi
else
    echo -e "${YELLOW}Non-interactive — proceeding automatically.${NC}"
fi

# Actual deployment
echo ""
echo -e "${CYAN}🚀 Deploying...${NC}"
rsync -avz --exclude '.*' \
    "${LOCAL_DIR}/" \
    "${TOOLFORGE_USER}@login.toolforge.org:${REMOTE_DIR}"

echo ""
echo -e "${GREEN}✅ Deployment complete${NC}"

# Optionally set executable permissions for .sh and .py files
echo ""
echo -e "${YELLOW}🔧 Setting executable permissions${NC}"
ssh "${TOOLFORGE_USER}@login.toolforge.org" \
    "become ${TOOL_NAME} find ${REMOTE_DIR} -type f \( -name '*.sh' -o -name '*.py' \) -exec chmod +x {} +" 2>/dev/null || true

echo -e "${GREEN}✅ Permissions set${NC}"
echo ""
echo -e "   ${CYAN}Next steps:${NC}"
echo -e "   1. SSH into Toolforge:  ssh ${TOOLFORGE_USER}@login.toolforge.org"
echo -e "   2. Become the tool:     become ${TOOL_NAME}"
echo -e "   3. Start web service:   webservice --backend=kubernetes python3.11 start"
echo -e "   4. Check status:        webservice --backend=kubernetes python3.11 status"
