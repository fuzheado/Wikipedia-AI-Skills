#!/usr/bin/env bash
# List unreviewed mainspace pages via the PageTriage API.
#
# Usage: ./list-unreviewed.sh [wiki] [limit]
#   wiki:  enwiki (default), testwiki, ruwiki, etc.
#   limit: number of results (default 50)
#
# Requires the patrol user right.  Unauthenticated users will get an
# empty result or a permission-denied error.

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $(basename "$0") [wiki] [limit]" >&2
    echo "" >&2
    echo "List unreviewed mainspace pages via the PageTriage API." >&2
    echo "" >&2
    echo "  wiki   Wiki short name: enwiki (default), testwiki, ruwiki" >&2
    echo "  limit  Number of results (default 50)" >&2
    echo "" >&2
    echo "Examples:" >&2
    echo "  $(basename "$0")                  # enwiki, 50 results" >&2
    echo "  $(basename "$0") testwiki 10       # testwiki, 10 results" >&2
    exit 1
fi

WIKI="${1:-enwiki}"
LIMIT="${2:-50}"

# Map wiki short name to domain (portable, no bash 4+ associative arrays)
case "$WIKI" in
    enwiki)  DOMAIN="en.wikipedia.org" ;;
    testwiki) DOMAIN="test.wikipedia.org" ;;
    ruwiki)  DOMAIN="ru.wikipedia.org" ;;
    *)       DOMAIN="${WIKI}.wikipedia.org" ;;
esac

API="https://${DOMAIN}/w/api.php"

echo "Fetching ${LIMIT} unreviewed pages from ${DOMAIN} ..." >&2

curl -s "${API}" \
  --data-urlencode "action=pagetriagelist" \
  --data-urlencode "showunreviewed=1" \
  --data-urlencode "noredirects=1" \
  --data-urlencode "limit=${LIMIT}" \
  --data-urlencode "format=json" \
  | python3 -c "
import json, sys

data = json.load(sys.stdin)

# Check for errors
if 'error' in data:
    print(f\"ERROR: {data['error'].get('info', 'unknown')}\", file=sys.stderr)
    sys.exit(1)

pages = data.get('query', {}).get('pagetriagelist', [])
print(f\"{'PAGEID':<8} {'TITLE':<55} {'CREATED':<16} {'CREATOR':<20}\")
print('-' * 99)
for p in pages:
    meta = p.get('metadata', {})
    created = meta.get('created_at', '')[:10] if meta.get('created_at') else '?'
    creator = meta.get('user_name', '?') if meta.get('user_name') else '?'
    print(f\"{p.get('pageid', '?'):<8} {p.get('title', '?'):<55} {created:<16} {creator:<20}\")
print(f\"\n{len(pages)} results\", file=sys.stderr)
" 2>&1
