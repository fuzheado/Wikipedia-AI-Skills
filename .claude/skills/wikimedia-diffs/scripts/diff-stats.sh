#!/usr/bin/env bash
# Analyze diff statistics between two Wikipedia revisions
# Usage: ./diff-stats.sh --page <title>
#        ./diff-stats.sh --from-rev <id> --to-rev <id>

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

PAGE=""; FROM_REV=""; TO_REV=""; PROJECT="en.wikipedia.org"
UA="${WIKI_UA:-DiffSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)}"

while [[ $# -gt 0 ]]; do
    case "$1" in --page) PAGE="$2"; shift 2 ;; --from-rev) FROM_REV="$2"; shift 2 ;;
        --to-rev) TO_REV="$2"; shift 2 ;; --project) PROJECT="$2"; shift 2 ;;
        *) echo -e "${RED}❌ Unknown: $1${NC}"; exit 1 ;;
    esac
done

API_URL="https://${PROJECT}/w/api.php"

if [ -z "$PAGE" ] && [ -z "$FROM_REV" ]; then
    echo -e "${RED}❌ Provide --page or --from-rev --to-rev${NC}"; exit 1
fi

# Resolve page to revision IDs if needed
if [ -n "$PAGE" ] && [ -z "$FROM_REV" ]; then
    REV_DATA=$(curl -s -H "User-Agent: ${UA}" \
      "${API_URL}?action=query&prop=revisions&titles=${PAGE// /_}&rvlimit=2&rvprop=ids&format=json")
    FROM_REV=$(echo "$REV_DATA" | python3 -c "
import sys,json; d=json.load(sys.stdin)
p=list(d['query']['pages'].values())[0]; r=p['revisions']
print(r[1]['revid'], r[0]['revid'])" 2>/dev/null) || {
        echo -e "${RED}❌ Could not get revision IDs${NC}"; exit 1
    }
    TO_REV=$(echo "$FROM_REV" | cut -d' ' -f2)
    FROM_REV=$(echo "$FROM_REV" | cut -d' ' -f1)
fi

# Fetch diff
PARAMS="action=compare&fromrev=${FROM_REV}&torev=${TO_REV}&prop=diff|diffsize|ids|title|size&format=json"
FULL_URL=$(echo "$PARAMS" | python3 -c "
import sys,urllib.parse; p=urllib.parse.parse_qsl(sys.stdin.read().strip())
base='${API_URL}'; qs=urllib.parse.urlencode(p); print(f'{base}?{qs}')")

RESP=$(curl -s -H "User-Agent: ${UA}" "${FULL_URL}")

echo "$RESP" | python3 -c "
import sys, json, re

data = json.load(sys.stdin)
if 'error' in data:
    print(f'❌ {data[\"error\"].get(\"info\", \"API error\")}')
    sys.exit(1)

c = data['compare']
title = c.get('fromtitle', c.get('totitle', '?'))
fromsize = c.get('fromsize', 0)
tosize = c.get('tosize', 0)
diffsize = c.get('diffsize', 0)
fromrevid = c.get('fromrevid', '?')
torevid = c.get('torevid', '?')
diff_html = c.get('*', '')

# Calculate added/removed from sizes
net_change = tosize - fromsize
added = max(0, net_change)
removed = max(0, -net_change)

# The diffsize is total changed bytes, not net
# If we have the HTML diff, count <ins> and <del> tags for rough line estimates
ins_count = diff_html.count('<ins')
del_count = diff_html.count('<del')
change_count = diff_html.count('diffchange')
context_lines = diff_html.count('diff-context')

# Sections affected — look for diff-lineno (section line number markers)
sections = set(re.findall(r'Line (\d+):', diff_html))

print(f'📊 Diff Statistics: {title}')
print(f'   ├  From rev:       {fromrevid}')
print(f'   ├  To rev:         {torevid}')
print()
print(f'   ┌─ Size metrics')
print(f'   ├  Page was:       {fromsize:>8,} bytes')
print(f'   ├  Page is now:    {tosize:>8,} bytes')
print(f'   ├  Net change:     {net_change:>+8,} bytes')
print(f'   ├  Total churn:    {diffsize:>8,} bytes (added + removed)')
print(f'   └  Diff HTML:      {len(diff_html):>8,} chars')
print()
print(f'   ┌─ HTML diff elements')
print(f'   ├  Insertions:     {ins_count}')
print(f'   ├  Deletions:      {del_count}')
print(f'   ├  Changed spans:  {change_count}')
print(f'   ├  Context lines:  {context_lines}')
print(f'   └  Line numbers:   {len(sections)} sections')
print()

# Risk assessment
flags = []
if diffsize > 50000:
    flags.append(f'🔴  RED: Large change ({diffsize:,} bytes churn) — possible blanking or mass addition')
if net_change < -20000:
    flags.append(f'🔴  RED: Significant removal ({-net_change:,} bytes net removed)')
if net_change > 100000:
    flags.append(f'🟡  YELLOW: Large addition ({net_change:,} bytes)')
if ins_count == 0 and del_count == 0 and diffsize > 0:
    flags.append('⚡  NOTE: Unusual diff — no ins/del tags')
if diffsize == 0 and fromsize != tosize:
    flags.append('⚡  NOTE: Size changed but diffsize is 0')
print(f'   ┌─ Assessment')
total_changed = ins_count + del_count
if total_changed == 0:
    flags.append('✅  No changes detected')
elif total_changed < 10:
    flags.append(f'✅  Small edit ({total_changed} diff elements)')
elif total_changed < 100:
    flags.append(f'⚡  Moderate edit ({total_changed} diff elements)')
else:
    flags.append(f'🔄  Large edit ({total_changed} diff elements)')
for f in flags:
    print(f'   {f}')
" 2>/dev/null || echo -e "${RED}❌ Failed to analyze diff${NC}"
