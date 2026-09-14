#!/usr/bin/env bash
# =============================================================================
# ws-page-status.sh — Show proofreading progress for a Wikisource work
#
# Queries the Wikisource API for proofreading statistics on a given Index:
# page, showing how many pages are at each quality level.
#
# Usage:
#   ./ws-page-status.sh <lang> <index_title>
#
# Examples:
#   ./ws-page-status.sh en "Index:Pride and Prejudice"
#   ./ws-page-status.sh fr "Index:Les Misérables"
#   ./ws-page-status.sh --help
# =============================================================================

set -euo pipefail

LANG="${1:-}"
INDEX="${2:-}"

if [ -z "$LANG" ] || [ "$LANG" = "--help" ] || [ -z "$INDEX" ]; then
    echo "Usage: $0 <lang> <index_title>"
    echo ""
    echo "Show proofreading progress for a Wikisource work."
    echo ""
    echo "Arguments:"
    echo "  lang          Language code (en, fr, de, etc.)"
    echo "  index_title   Title of the Index: page"
    echo ""
    echo "Examples:"
    echo "  $0 en \"Index:Pride and Prejudice\""
    echo "  $0 fr \"Index:Les Misérables\""
    exit 0
fi

API="https://${LANG}.wikisource.org/w/api.php"
UA="WsPageStatus/1.0 (https://example.com; user@example.com)"

# URL-encode the index title for the API
ENCODED_INDEX=$(python3 -c "import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1]))" "$INDEX")

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Wikisource Proofreading Status                              ║"
echo "║  Work: $INDEX"
echo "║  Wiki: ${LANG}.wikisource.org"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Fetch proofread info via the API
echo "Fetching proofreading data..."
RESULT=$(curl -s -G "$API" \
    --data-urlencode "action=query" \
    --data-urlencode "titles=$INDEX" \
    --data-urlencode "prop=proofreadinfo" \
    --data-urlencode "piprop=quality" \
    --data-urlencode "format=json" \
    -H "User-Agent: $UA" \
    | python3 -c "
import sys, json

data = json.load(sys.stdin)
pages = data.get('query', {}).get('pages', {})

# Find the Index page
index_data = None
for pid, pdata in pages.items():
    if pid == '-1':
        print('ERROR: Index page not found')
        sys.exit(1)
    index_data = pdata
    break

quality = {0: 0, 1: 0, 2: 0, 3: 0}
quality_labels = {0: 'Without text', 1: 'Problematic', 2: 'Proofread', 3: 'Validated'}

# Check for quality data
pr_data = index_data.get('proofreadinfo', {})
if 'quality' in pr_data:
    for page_id, q in pr_data['quality'].items():
        quality[int(q)] = quality.get(int(q), 0) + 1

total = sum(quality.values())

if total == 0:
    print('ERROR: No pages found. The Index may not exist or have no pages.')
    sys.exit(1)

done = quality[2] + quality[3]
pct = round(done / total * 100)

print(f'Total pages: {total}')
print()
for level in [3, 2, 1, 0]:
    count = quality[level]
    bar_len = round(count / total * 40) if total > 0 else 0
    bar = '█' * bar_len + '░' * (40 - bar_len)
    print(f'  {quality_labels[level]:15s} {count:4d}  {bar} {count/total*100:5.1f}%')
print()
print(f'Completed: {done}/{total} ({pct}%)')
print(f'Remaining: {total - done}')
")

if [[ "$RESULT" == ERROR:* ]]; then
    echo "❌ $RESULT"
    exit 1
fi

echo "$RESULT"
echo ""

# Show page-by-page breakdown (compact)
echo "────────────────────────────────────────────"
echo "Would you like to see a page-by-page breakdown?"
echo "Pass --verbose to the script for full details."
echo "────────────────────────────────────────────"
echo ""
echo "Tip: To list pages at a specific quality level, use:"
echo "  https://${LANG}.wikisource.org/w/index.php?title=Special:PagesWithProofreadErrors&quality=0"
echo ""
