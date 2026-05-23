#!/usr/bin/env bash
# Manage Kubernetes jobs on Toolforge
# Usage: ./manage-k8s.sh <tool_name> <action> [args...]

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
    echo "   Usage: ./manage-k8s.sh <tool_name> <action> [args...]"
    echo ""
    echo "   Actions:"
    echo "     run <job_name> <command>    Run a job"
    echo "     list                         List all jobs"
    echo "     logs <job_name>              Show job logs"
    echo "     delete <job_name>            Delete a job"
    echo "     status <job_name>            Check job status"
    echo ""
    echo "   Examples:"
    echo "     ./manage-k8s.sh my-tool run daily-collect \"python3 /data/project/my-tool/script.py\""
    echo "     ./manage-k8s.sh my-tool list"
    echo "     ./manage-k8s.sh my-tool logs daily-collect"
    echo "     ./manage-k8s.sh my-tool delete daily-collect"
    exit 1
fi

HOST="${TOOLFORGE_USER:-your-username}@login.toolforge.org"

case "$ACTION" in
    run)
        JOB_NAME="${3:-}"
        COMMAND="${4:-}"

        if [ -z "$JOB_NAME" ] || [ -z "$COMMAND" ]; then
            echo -e "${RED}❌ Missing job name or command${NC}"
            echo "   Usage: $0 <tool_name> run <job_name> <command>"
            exit 1
        fi

        echo -e "${CYAN}▶️  Running job '${JOB_NAME}' on ${TOOL_NAME}${NC}"
        echo -e "   Command: ${COMMAND}"
        echo ""

        ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; toolforge jobs run ${JOB_NAME} --command '${COMMAND}' --image python3.11 --wait 2>&1"
        ;;

    list)
        echo -e "${CYAN}📋 Jobs for ${TOOL_NAME}${NC}"
        ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; toolforge jobs list 2>&1"
        ;;

    logs)
        JOB_NAME="${3:-}"
        if [ -z "$JOB_NAME" ]; then
            echo -e "${RED}❌ Missing job name${NC}"
            echo "   Usage: $0 <tool_name> logs <job_name>"
            exit 1
        fi

        echo -e "${CYAN}📜 Logs for job '${JOB_NAME}' on ${TOOL_NAME}${NC}"
        ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; toolforge jobs logs ${JOB_NAME} 2>&1"
        ;;

    delete)
        JOB_NAME="${3:-}"
        if [ -z "$JOB_NAME" ]; then
            echo -e "${RED}❌ Missing job name${NC}"
            echo "   Usage: $0 <tool_name> delete <job_name>"
            exit 1
        fi

        echo -e "${YELLOW}🗑️  Deleting job '${JOB_NAME}' on ${TOOL_NAME}${NC}"
        ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; toolforge jobs delete ${JOB_NAME} 2>&1"
        ;;

    status)
        JOB_NAME="${3:-}"
        if [ -z "$JOB_NAME" ]; then
            # Overall status
            echo -e "${CYAN}📊 Job status for ${TOOL_NAME}${NC}"
            ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; toolforge jobs list 2>&1"
        else
            echo -e "${CYAN}📊 Status of job '${JOB_NAME}' on ${TOOL_NAME}${NC}"
            ssh "$HOST" "become ${TOOL_NAME} 2>/dev/null; toolforge jobs list 2>&1 | grep ${JOB_NAME} || echo 'Job not found'"
        fi
        ;;

    *)
        echo -e "${RED}❌ Unknown action: ${ACTION}${NC}"
        echo "   Valid actions: run, list, logs, delete, status"
        exit 1
        ;;
esac
