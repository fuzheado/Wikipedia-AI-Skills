#!/usr/bin/env bash
# deploy-python.sh — One-command deployment for Toolforge Python tools
# Usage: ./deploy-python.sh <tool-name> [--quick]

set -euo pipefail

TOOL="${1:?Usage: $0 <tool-name> [--quick]}"
QUICK="${2:-}"

TOOLFORGE_USER="${TOOLFORGE_USER:?Set TOOLFORGE_USER env var}"
TOOLFORGE_HOST="login.toolforge.org"
TOOL_DIR="/data/project/${TOOL}"

echo "=== Deploying ${TOOL} to Toolforge ==="

# Upload application files
echo "→ Uploading app.py and requirements.txt..."
scp app.py "${TOOLFORGE_USER}@${TOOLFORGE_HOST}:${TOOL_DIR}/"
[ -f requirements.txt ] && scp requirements.txt "${TOOLFORGE_USER}@${TOOLFORGE_HOST}:${TOOL_DIR}/"

# Upload static files if they exist
if [ -d static ]; then
    echo "→ Uploading static/ directory..."
    ssh "${TOOLFORGE_USER}@${TOOLFORGE_HOST}" "mkdir -p ${TOOL_DIR}/static"
    scp -r static/* "${TOOLFORGE_USER}@${TOOLFORGE_HOST}:${TOOL_DIR}/static/"
fi

# Set up virtual environment and install dependencies
if [ "$QUICK" != "--quick" ]; then
    echo "→ Setting up virtual environment..."
    ssh "${TOOLFORGE_USER}@${TOOLFORGE_HOST}" "
        become ${TOOL} bash -c '
            cd ${TOOL_DIR}
            python3 -m venv venv
            source venv/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
        '
    "
fi

# Restart the webservice
echo "→ Restarting webservice..."
ssh "${TOOLFORGE_USER}@${TOOLFORGE_HOST}" "become ${TOOL} webservice --backend=kubernetes python3.11 restart"

echo "✓ Deployed! Check https://${TOOL}.toolforge.org/"
