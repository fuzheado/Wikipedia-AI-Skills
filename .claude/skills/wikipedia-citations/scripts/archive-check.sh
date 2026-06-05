#!/usr/bin/env bash
# Check if a URL is archived on the Wayback Machine.
#
# Usage:
#   ./archive-check.sh https://example.com/article
#   ./archive-check.sh "https://example.com/article"  # with quotes for special chars

set -euo pipefail

if [[ $# -eq 0 ]]; then
    echo "🔍 archive-check.sh — Check if a URL is archived on the Wayback Machine"
    echo ""
    echo "Usage: $0 <url>"
    echo ""
    echo "Examples:"
    echo "  $0 https://example.com/article"
    echo "  $0 'https://en.wikipedia.org/wiki/Main_Page'"
    exit 1
fi

URL="${1:?}"
USER_AGENT="ArchiveCheck/1.0 (user@example.com) ContentGapResearch"

echo "🔍 Checking: $URL"
echo

RESPONSE=$(curl -s "https://archive.org/wayback/available?url=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$URL'))")" \
  -H "User-Agent: $USER_AGENT")

AVAILABLE=$(echo "$RESPONSE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
snap = d.get('archived_snapshots', {})
if snap:
    closest = snap.get('closest', {})
    print(f\"YES\\nARCHIVE_URL={closest.get('url', '')}\\nTIMESTAMP={closest.get('timestamp', '')}\\nSTATUS={closest.get('status', '')}\")
else:
    print('NO')
" 2>/dev/null)

if [[ "$AVAILABLE" == "NO" ]]; then
    echo "❌ No archive found on the Wayback Machine."
    echo
    echo "To save this page:"
    echo "  curl -X POST -H 'User-Agent: $USER_AGENT' 'https://web.archive.org/save/$URL'"
    exit 1
fi

echo "✅ Archive found!"
echo "$AVAILABLE" | while IFS='=' read -r key value; do
    case "$key" in
        ARCHIVE_URL) echo "   Archive URL: $value" ;;
        TIMESTAMP) 
            # Convert YYYYMMDDHHMMSS to readable date
            READABLE=$(echo "$value" | sed -E 's/(....)(..)(..)(..)(..)(..)/\1-\2-\3 \4:\5:\6/')
            echo "   Snapshot date: $READABLE" ;;
        STATUS) echo "   Status: $value" ;;
    esac
done
echo
echo "Open in browser:"
echo "$(echo "$AVAILABLE" | grep ARCHIVE_URL | cut -d= -f2-)"
