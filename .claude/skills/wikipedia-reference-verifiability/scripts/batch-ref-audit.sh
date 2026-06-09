#!/usr/bin/env bash
# Batch reference audit for recently created Wikipedia pages.
# Combines the PageTriage two-pass pipeline with reference URL analysis.
#
# Usage: ./batch-ref-audit.sh [--days 7] [--limit 100] [--no-quality]

set -euo pipefail

DAYS=7
LIMIT=100
NO_QUALITY=""

while [ $# -gt 0 ]; do
    case "$1" in
        --days) DAYS="$2"; shift 2 ;;
        --limit) LIMIT="$2"; shift 2 ;;
        --no-quality) NO_QUALITY="--no-quality"; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ASSETS="${SCRIPT_DIR}/../assets"

echo "Batch reference audit — last ${DAYS} days, up to ${LIMIT} pages"
echo "=============================================="
echo ""

# Use the patrol simulator from the pagetriage-api skill if available,
# otherwise fall back to direct API calls.
SIMULATOR="${SCRIPT_DIR}/../../pagetriage-api/assets/patrol_simulator.py"

if [ -f "$SIMULATOR" ]; then
    python3 "$SIMULATOR" \
        --days "$DAYS" \
        --limit "$LIMIT" \
        ${NO_QUALITY:+"--no-quality"} \
        2>&1
else
    # Independent implementation: fetch new pages and run refcheck
    echo "(pagetriage-api skill not found, using direct API)" >&2
    API="https://en.wikipedia.org/w/api.php"

    # Fetch new pages
    NEW_PAGES=$(curl -s "${API}" \
        --data-urlencode "action=query" \
        --data-urlencode "list=recentchanges" \
        --data-urlencode "rctype=new" \
        --data-urlencode "rcnamespace=0" \
        --data-urlencode "rcshow=!redirect" \
        --data-urlencode "rclimit=50" \
        --data-urlencode "rcprop=title|ids|user" \
        --data-urlencode "format=json" \
        | python3 -c "
import json, sys
data = json.load(sys.stdin)
for rc in data.get('query', {}).get('recentchanges', []):
    print(json.dumps({'title': rc['title'], 'pageid': rc['pageid']}))
" 2>&1)

    echo "$NEW_PAGES" | while IFS= read -r line; do
        TITLE=$(echo "$line" | python3 -c "import json,sys; print(json.load(sys.stdin)['title'])")
        PAGEID=$(echo "$line" | python3 -c "import json,sys; print(json.load(sys.stdin)['pageid'])")

        # Fetch wikitext
        WIKITEXT=$(curl -s "${API}" \
            --data-urlencode "action=query" \
            --data-urlencode "prop=revisions" \
            --data-urlencode "rvprop=content" \
            --data-urlencode "rvslots=main" \
            --data-urlencode "pageids=${PAGEID}" \
            --data-urlencode "format=json" \
            | python3 -c "
import json, sys
sys.path.insert(0, '${ASSETS}')
from ref_url_checker import has_any_url_refs
data = json.load(sys.stdin)
for pid, p in data.get('query', {}).get('pages', {}).items():
    revs = p.get('revisions', [])
    if not revs:
        break
    wt = revs[0].get('slots', {}).get('main', {}).get('*', '')
    if not wt:
        break
    has_url, total, url_count, _ = has_any_url_refs(wt)
    if total > 0 and not has_url:
        print(f'  ► {p[\"title\"]}  ({total} refs, 0 URLs)')
" 2>&1)

        if [ -n "$WIKITEXT" ]; then
            echo "$WIKITEXT"
        fi
    done
fi
