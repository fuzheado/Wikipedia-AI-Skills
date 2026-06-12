#!/usr/bin/env bash
# Notability Checker CLI — Assess whether a subject meets Wikipedia notability guidelines
# Usage:
#   ./notability-check.sh "Jane Smith" \
#       --type academic \
#       --desc "Professor of quantum physics at MIT, named chair" \
#       --source "Nature profile|news_feature|yes|yes|yes"
#   ./notability-check.sh --help

set -euo pipefail

UA="notability-check/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; user@example.com) WMSkills"

usage() {
    grep '^#' "$0" | sed 's/^# \?//' | sed '$d'
    echo ""
    echo "Options:"
    echo "  --type, -t TYPE      Subject type (academic, artist, company, event, film, etc.)"
    echo "  --desc, -d TEXT      Subject description (required)"
    echo "  --source, -s FORMAT  Source in format: title|type|reliable|independent|significant"
    echo "                       (can repeat: -s 'Src1|news|yes|yes|yes' -s 'Src2|academic|yes|yes|yes')"
    echo "  --json               Output as JSON"
    echo "  --afd                Output AfD-ready summary"
    echo "  --short              One-line summary"
    echo "  --help               Show this message"
}

die() {
    echo "Error: $1" >&2
    usage >&2
    exit 1
}

if [ "$#" -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
    exit 0
fi

# Parse arguments
NAME=""
TYPE=""
DESC=""
JSON=false
FORMAT="full"
SOURCES=()

while [ $# -gt 0 ]; do
    case "$1" in
        --type|-t) TYPE="$2"; shift 2 ;;
        --desc|-d) DESC="$2"; shift 2 ;;
        --source|-s) SOURCES+=("$2"); shift 2 ;;
        --json) JSON=true; shift ;;
        --afd) FORMAT="afd"; shift ;;
        --short) FORMAT="short"; shift ;;
        --) shift; NAME="$*"; break ;;
        *) NAME="$1"; shift ;;
    esac
done

test -n "$NAME" || die "Subject name is required."
test -n "$DESC" || die "Subject description (--desc) is required."

# Build Python arguments
PY_ARGS=()
PY_ARGS+=("--description" "$DESC")

if [ -n "$TYPE" ]; then
    PY_ARGS+=("--type" "$TYPE")
fi

for src in "${SOURCES[@]+${SOURCES[@]}}"; do
    [ -n "$src" ] || continue
    PY_ARGS+=("--source" "$src")
done

if [ "$JSON" = true ]; then
    PY_ARGS+=("--json")
fi

if [ "$FORMAT" = "afd" ]; then
    PY_ARGS+=("--afd")
elif [ "$FORMAT" = "short" ]; then
    PY_ARGS+=("--short")
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ASSETS_DIR="$SCRIPT_DIR/../assets"

python3 "$ASSETS_DIR/notability_checker.py" "$NAME" "${PY_ARGS[@]}"
