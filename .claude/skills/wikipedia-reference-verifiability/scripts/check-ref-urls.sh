#!/usr/bin/env bash
# Check references for a Wikipedia page and report URL presence.
# Usage: ./check-ref-urls.sh "Page Title"
#
# Fetches the page wikitext, pipes it to Python for analysis.
# Avoids shell quoting issues by passing data via stdin.

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"Page Title\" [\"Another Title\" ...]" >&2
    exit 1
fi

API="https://en.wikipedia.org/w/api.php"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ASSETS="${SCRIPT_DIR}/../assets"

for TITLE in "$@"; do
    echo "========================================"
    echo "  $TITLE"
    echo "========================================"

    # Fetch wikitext via API, pipe through Python for analysis
    curl -s "${API}" \
        --data-urlencode "action=query" \
        --data-urlencode "titles=${TITLE}" \
        --data-urlencode "prop=revisions" \
        --data-urlencode "rvprop=content" \
        --data-urlencode "rvslots=main" \
        --data-urlencode "format=json" \
        | python3 -c "
import json, sys

sys.path.insert(0, '${ASSETS}')
from ref_url_checker import has_any_url_refs

data = json.load(sys.stdin)
pages = data.get('query', {}).get('pages', {})

for pid, p in pages.items():
    if pid == '-1':
        print('  ✗ Page not found.')
        break

    revs = p.get('revisions', [])
    if not revs:
        print('  ∼ No content.')
        break

    wikitext = revs[0].get('slots', {}).get('main', {}).get('*', '')
    if not wikitext:
        print('  ∼ Empty page.')
        break

    has_url, total, url_count, samples = has_any_url_refs(wikitext)

    print(f'  Total references: {total}')
    print(f'  With URLs:        {url_count}')
    print(f'  Without URLs:     {total - url_count}')

    if total == 0:
        print('  (no references found)')
    elif has_url:
        print('  → PASS: at least one reference has a URL')
    else:
        print('  → ALERT: NO references have a URL')

    if samples:
        print()
        print('  URL-free reference samples:')
        for s in samples:
            print(f'    • {s}')
" 2>&1

    echo
done
