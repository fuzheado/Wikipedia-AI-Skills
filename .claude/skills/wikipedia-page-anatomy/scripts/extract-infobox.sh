#!/usr/bin/env bash
# Extract infobox field names and values from a Wikipedia article
#
# Uses wikitext_utils.py for reliable infobox extraction with proper
# brace-depth tracking. For more complex template parsing, see the
# wikimedia-wikitext skill (mwparserfromhell).
#
# Usage:
#   ./scripts/extract-infobox.sh "Albert Einstein"
#   ./scripts/extract-infobox.sh "Python (programming language)" --project fr.wikipedia
#   ./scripts/extract-infobox.sh "Berlin" --json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

usage() {
    awk '/^# Usage:/ { found=1 } found && /^#/ { sub(/^# /, ""); print } found && /^$/ { exit }' "$0"
    exit 0
}

if [ $# -eq 0 ] || [ "$1" = "--help" ]; then
    usage
fi

python3 "${SCRIPT_DIR}/assets/wikitext_utils.py" infobox "$@"
