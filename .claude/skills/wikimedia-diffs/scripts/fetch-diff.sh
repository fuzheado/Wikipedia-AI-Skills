#!/usr/bin/env bash
# Fetch a diff between two Wikipedia page revisions
# Usage: ./fetch-diff.sh [options]
#   --page <title>         Latest edit to a page
#   --from-rev <id>        Old revision ID (required)
#   --to-rev <id>          New revision ID (required)
#   --project <host>       Wikimedia project (default: en.wikipedia.org)
#   --json                 Output raw JSON
#   --save <file>          Save raw HTML diff to file

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

PAGE=""; FROM_REV=""; TO_REV=""; JSON=false; SAVE=""; PROJECT="en.wikipedia.org"
API_URL="https://${PROJECT}/w/api.php"
UA="${WIKI_UA:-DiffSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)}"

while [[ $# -gt 0 ]]; do
    case "$1" in --page) PAGE="$2"; shift 2 ;; --from-rev) FROM_REV="$2"; shift 2 ;;
        --to-rev) TO_REV="$2"; shift 2 ;; --json) JSON=true; shift ;;
        --save) SAVE="$2"; shift 2 ;; --project) PROJECT="$2"; API_URL="https://${PROJECT}/w/api.php"; shift 2 ;;
        *) echo -e "${RED}❌ Unknown: $1${NC}"; exit 1 ;;
    esac
done

if [ -z "$PAGE" ] && [ -z "$FROM_REV" ]; then
    echo -e "${RED}❌ Provide --page or --from-rev + --to-rev${NC}"
    echo "   ./fetch-diff.sh --page 'Albert Einstein'"
    echo "   ./fetch-diff.sh --from-rev 123456789 --to-rev 123456790"
    exit 1
fi

# If only --page given, resolve to revision IDs
if [ -n "$PAGE" ] && [ -z "$FROM_REV" ]; then
    echo -e "${CYAN}🔍 Resolving revision IDs for: ${PAGE}${NC}" >&2
    REV_DATA=$(curl -s -H "User-Agent: ${UA}" \
      "${API_URL}?action=query&prop=revisions&titles=${PAGE// /_}&rvlimit=2&rvprop=ids&format=json")
    FROM_REV=$(echo "$REV_DATA" | python3 -c "
import sys,json; d=json.load(sys.stdin)
p=list(d['query']['pages'].values())[0]
r=p['revisions']
print(r[1]['revid'], r[0]['revid'])" 2>/dev/null) || {
        echo -e "${RED}❌ Could not get revision IDs${NC}"; exit 1
    }
    TO_REV=$(echo "$FROM_REV" | cut -d' ' -f2)
    FROM_REV=$(echo "$FROM_REV" | cut -d' ' -f1)
fi

if [ -z "$TO_REV" ]; then
    echo -e "${RED}❌ Need --to-rev${NC}"; exit 1
fi

# Build params
PARAMS="action=compare&fromrev=${FROM_REV}&torev=${TO_REV}&prop=diff|diffsize|ids|title|size&format=json"
FULL_URL=$(echo "$PARAMS" | python3 -c "
import sys,urllib.parse; p=urllib.parse.parse_qsl(sys.stdin.read().strip())
base='${API_URL}'; qs=urllib.parse.urlencode(p); print(f'{base}?{qs}')")

echo -e "${CYAN}📋 Fetching diff${NC}"
echo -e "   From rev: ${FROM_REV}  →  To rev: ${TO_REV}"
echo ""

RESP=$(curl -s -H "User-Agent: ${UA}" "${FULL_URL}")

# Validate
echo "$RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if 'compare' in d else 1)" 2>/dev/null || {
    echo -e "${RED}❌ API error${NC}"; echo "$RESP" | python3 -m json.tool 2>/dev/null || echo "$RESP"; exit 1
}

# Summary
echo "$RESP" | python3 -c "
import sys, json
c = json.load(sys.stdin)['compare']
print(f\"   Title:    {c.get('fromtitle', '?')}\")
print(f\"   From rev: {c.get('fromrevid', '?')} (page {c.get('fromid', '?')})\")
print(f\"   To rev:   {c.get('torevid', '?')} (page {c.get('toid', '?')})\")
print(f\"   Page was: {c.get('fromsize', '?')} bytes → {c.get('tosize', '?')} bytes\")
ds = c.get('diffsize', 0)
fs = c.get('fromsize', 0)
ts = c.get('tosize', 0)
if isinstance(ds, (int, float)):
    net = ts - fs
    print(f\"   Changed:  {ds} bytes total (net: {net:+d})\")
    if net > 0:
        print(f'   Size:     +{net} bytes (added)')
    elif net < 0:
        print(f'   Size:     {-net} bytes (removed)')
print()
diff_html = c.get('*', '')
print(f'   Diff HTML: {len(diff_html)} chars')
"

# Output
if $JSON; then
    # JSON mode: suppress summary to stderr
    echo "$RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)['compare']
print(json.dumps({
    'title': d.get('fromtitle'),
    'page_id': d.get('fromid'),
    'from_revid': d.get('fromrevid'),
    'to_revid': d.get('torevid'),
    'fromsize': d.get('fromsize'),
    'tosize': d.get('tosize'),
    'diffsize': d.get('diffsize'),
    'net_change': d.get('tosize', 0) - d.get('fromsize', 0),
}, indent=2))
"
fi

if [ -n "$SAVE" ]; then
    echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['compare'].get('*',''))" > "$SAVE"
    >&2 echo -e "💾 HTML diff saved to: ${SAVE}"
fi
