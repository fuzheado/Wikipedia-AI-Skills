#!/usr/bin/env bash
# Toolforge Deployment Configuration
# Copy this file, edit the variables, and source it before running deploy scripts.
# Usage:
#   cp deploy-config.sh my-config.sh
#   source my-config.sh
#   ./deploy.sh ./my-app my-tool-name

# Your Toolforge shell/LDAP username
# Get this from https://toolforge.org/
export TOOLFORGE_USER="your-toolforge-username"

# Default tool name (override with command-line arg)
export TOOL_NAME="my-tool-name"

# Local directory containing your tool files
export LOCAL_DIR="./my-tool/"

# Remote path on Toolforge (default: /data/project/<tool_name>/)
export REMOTE_DIR="/data/project/${TOOL_NAME}/"

# Exclude patterns for rsync (space-separated)
export RSYNC_EXCLUDES=".git __pycache__ .env .DS_Store *.pyc node_modules"

# Web service backend type
export WEBSERVICE_TYPE="python3.11"
