#!/usr/bin/env bash
# Check the review/patrol status of one or more Wikipedia pages.
# Usage: ./check-status.sh "Page Title" ["Another Title" ...]
#
# Uses prop=info&inprop=protection which works without authentication
# for basic status, but patrol details require the patrolmarks right.

set -euo pipefail

if [ $# -eq 0 ]; then
    echo "Usage: $0 \"Page Title\" [\"Another Title\" ...]" >&2
    exit 1
fi

API="https://en.wikipedia.org/w/api.php"

# Build pipe-separated titles
TITLES=""
sep=""
for t in "$@"; do
    TITLES="${TITLES}${sep}${t}"
    sep="|"
done

echo "Checking status for: $@" >&2

curl -s "${API}" \
  --data-urlencode "action=query" \
  --data-urlencode "titles=${TITLES}" \
  --data-urlencode "prop=info" \
  --data-urlencode "inprop=protection" \
  --data-urlencode "format=json" \
  | python3 -c "
import json, sys

data = json.load(sys.stdin)
pages = data.get('query', {}).get('pages', {})

print(f\"{'PAGEID':<8} {'TITLE':<55} {'EXISTS':<8} {'LENGTH':<8} {'PROTECTION':<30}\")
print('-' * 109)
for pid, p in sorted(pages.items(), key=lambda x: x[1].get('title', '')):
    if pid == '-1':
        continue
    title = p.get('title', '?')
    exists = '✓' if not p.get('missing') else '✗ missing'
    length = p.get('length', '?')
    prot = p.get('protection', [])
    if prot:
        levels = [f\"{pp['type']}={pp['level']}\" for pp in prot]
        prot_str = ', '.join(levels)
    else:
        prot_str = 'none (open)'
    print(f\"{pid:<8} {title:<55} {exists:<8} {str(length):<8} {prot_str:<30}\")
" 2>&1
