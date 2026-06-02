#!/usr/bin/env bash
# Fetch top pageviews for a Wikimedia project on a given date
# Usage: ./top-pages.sh [project] [date] [limit]

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT="${1:-en.wikipedia}"
DATE="${2:-$(date -v-3d +%Y/%m/%d 2>/dev/null || date -d '3 days ago' +%Y/%m/%d 2>/dev/null || echo "2026/05/20")}"
LIMIT="${3:-25}"
UA="${WIKIMEDIA_UA:-PageviewsBot/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; test@wikimedia.org) PageviewsTool}"

echo -e "${CYAN}📊 Top Pageviews${NC}"
echo -e "   Project: ${PROJECT}"
echo -e "   Date:    ${DATE}"
echo ""

URL="https://wikimedia.org/api/rest_v1/metrics/pageviews/top/${PROJECT}/all-access/${DATE}"
TMPFILE=$(mktemp /tmp/pageviews_top.XXXXXX)
trap 'rm -f "$TMPFILE"' EXIT

curl -s -w "\n%{http_code}" \
    -H "User-Agent: ${UA}" \
    --max-time 15 \
    "${URL}" > "$TMPFILE" 2>&1

HTTP_CODE=$(tail -1 "$TMPFILE")
sed '$d' "$TMPFILE" > "${TMPFILE}.body"
BODY_FILE="${TMPFILE}.body"

if [[ "$HTTP_CODE" != "200" ]]; then
    echo -e "${RED}❌ API returned HTTP ${HTTP_CODE}${NC}"
    python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('detail','Unknown error'))" "$BODY_FILE" 2>/dev/null
    exit 1
fi

python3 -c "
import json, sys

data = json.load(open(sys.argv[1]))
items = data.get('items', [])
if not items:
    print('No data available for this date.')
    sys.exit(0)
articles = items[0].get('articles', [])
limit = min(int(sys.argv[2]), len(articles))
print(f'{\"Rank\":<6} {\"Article\":<55} {\"Views\":>12}')
print('-' * 75)
for i, a in enumerate(articles[:limit], 1):
    title = a.get('article', '')
    views = a.get('views', 0)
    print(f'#{i:<4}  {title:<55} {views:>12,}')
print()
print(f'Showing top {limit} of {len(articles)} articles')
" "$BODY_FILE" "$LIMIT"
