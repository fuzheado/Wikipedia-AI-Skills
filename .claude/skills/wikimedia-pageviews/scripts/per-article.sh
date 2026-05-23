#!/usr/bin/env bash
# Fetch historical pageviews for a specific article
# Usage: ./per-article.sh <article_title> [start_date] [end_date] [project]

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ARTICLE="${1:-}"
START="${2:-$(date -v-30d +%Y%m%d 2>/dev/null || date -d '30 days ago' +%Y%m%d 2>/dev/null || echo "20260423")}"
END="${3:-$(date +%Y%m%d 2>/dev/null || echo "20260523")}"
PROJECT="${4:-en.wikipedia}"
UA="${WIKIMEDIA_UA:-PageviewsBot/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; test@wikimedia.org) PageviewsTool}"

if [ -z "$ARTICLE" ]; then
    echo -e "${RED}❌ No article title provided${NC}"
    echo "   Usage: ./per-article.sh <article_title> [start_date] [end_date] [project]"
    echo ""
    echo "   Examples:"
    echo "     ./per-article.sh Albert_Einstein"
    echo "     ./per-article.sh Python_(programming_language) 20260101 20260301"
    echo "     ./per-article.sh Barack_Obama 20240101 20241231 en.wikipedia"
    exit 1
fi

echo -e "${CYAN}📈 Pageviews for: ${ARTICLE}${NC}"
echo -e "   Period:  ${START} to ${END}"
echo -e "   Project: ${PROJECT}"
echo ""

URL="https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/${PROJECT}/all-access/all-agents/${ARTICLE}/daily/${START}/${END}"
TMPFILE=$(mktemp /tmp/pageviews_article.XXXXXX)
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
from datetime import datetime

data = json.load(open(sys.argv[1]))
items = data.get('items', [])
article = data.get('title', sys.argv[2])

if not items:
    print('No pageview data available for this period.')
    sys.exit(0)

total = sum(item.get('views', 0) for item in items)
days = len(items)
avg = total / days if days > 0 else 0
max_item = max(items, key=lambda x: x.get('views', 0))
min_item = min(items, key=lambda x: x.get('views', 0))

print(f'Article: {article}')
print(f'Period:  {items[0][\"timestamp\"][:8]} to {items[-1][\"timestamp\"][:8]}')
print(f'Days:    {days}')
print(f'Total:   {total:,} views')
print(f'Avg:     {avg:,.0f} views/day')
print(f'Max:     {max_item[\"views\"]:,} views on {max_item[\"timestamp\"][:8]}')
print(f'Min:     {min_item[\"views\"]:,} views on {min_item[\"timestamp\"][:8]}')
print()
print(f'{\"Date\":<12} {\"Views\":>10} {\"Bar\":<30}')
print('-' * 54)
for item in items:
    date = item['timestamp'][:8]
    views = item.get('views', 0)
    bar_len = int((views / max_item['views']) * 30) if max_item['views'] > 0 else 0
    bar = '█' * bar_len
    print(f'{date:<12} {views:>10,}  {bar}')
" "$BODY_FILE" "$ARTICLE"
