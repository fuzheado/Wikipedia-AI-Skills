#!/usr/bin/env bash
# List unreviewed mainspace pages via the PageTriage API.
# Usage: ./list-unreviewed.sh <wiki> [limit]
#   wiki:  enwiki (default), testwiki, ruwiki, etc.
#   limit: number of results (default 50)
#
# Requires the patrol user right.  Unauthenticated users will get an
# empty result or a permission-denied error.

set -euo pipefail

WIKI="${1:-enwiki}"
LIMIT="${2:-50}"

# Map wiki short name to domain
declare -A DOMAINS
DOMAINS=(
  [enwiki]="en.wikipedia.org"
  [testwiki]="test.wikipedia.org"
  [ruwiki]="ru.wikipedia.org"
)
DOMAIN="${DOMAINS[$WIKI]:-${WIKI}.wikipedia.org}"

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
