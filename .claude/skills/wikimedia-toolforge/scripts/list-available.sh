#!/usr/bin/env bash
# Search for available libraries on the cdnjs mirror
# Usage: ./list-available.sh <search_term> [limit]

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SEARCH="${1:-}"
LIMIT="${2:-10}"

if [ -z "$SEARCH" ]; then
    echo -e "${RED}❌ No search term provided${NC}"
    echo "   Usage: ./list-available.sh <search_term> [limit]"
    echo ""
    echo "   Examples:"
    echo "     ./list-available.sh d3"
    echo "     ./list-available.sh chart 15"
    echo "     ./list-available.sh bootstrap"
    exit 1
fi

echo -e "${CYAN}🔍 Searching cdnjs for '${SEARCH}'${NC}"
echo ""

API_URL="https://api.cdnjs.com/libraries?search=${SEARCH}&fields=version,latest,name,description"

TMPFILE=$(mktemp /tmp/cdnjs-search.XXXXXX)
trap 'rm -f "$TMPFILE"' EXIT

curl -s -w "\n%{http_code}" -H "User-Agent: CDNCheck/1.0" --max-time 15 "$API_URL" > "$TMPFILE" 2>&1 || true

HTTP_CODE=$(tail -1 "$TMPFILE")
sed '$d' "$TMPFILE" > "${TMPFILE}.body"

if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}❌ API returned HTTP ${HTTP_CODE}${NC}" >&2
    exit 1
fi

python3 -c "
import json, sys

with open('${TMPFILE}.body') as f:
    data = json.load(f)
results = data.get('results', [])
limit = min(int(sys.argv[1]), len(results))

if not results:
    print('No libraries found.')
    sys.exit(0)

print(f'{\"Library\":<30} {\"Version\":<12} {\"CDN Path\":<50}')
print('-' * 94)
for r in results[:limit]:
    name = r.get('name', '')[:28]
    version = r.get('version', '')[:10]
    latest = r.get('latest', '')
    # Extract the path after ajax/libs/
    if 'ajax/libs/' in latest:
        path = latest.split('ajax/libs/')[1]
    else:
        path = latest
    print(f'{name:<30} {version:<12} {path:<50}')
print()
print(f'Showing top {limit} of {len(results)} results.')
" "$LIMIT"
