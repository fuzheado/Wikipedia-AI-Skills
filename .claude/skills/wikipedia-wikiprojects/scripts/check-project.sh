#!/usr/bin/env bash
# check-project.sh — Check whether a WikiProject exists and show its metadata
# Usage:
#   ./check-project.sh Physics
#   ./check-project.sh "United States History"
set -euo pipefail

TOPIC="${1:?Usage: $0 <WikiProject topic>}"
USER_AGENT="WikiProjectChecker/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; tools@example.com)"

# Normalize: "United States History" → "United_States_History"
TITLE_NORMALIZED="${TOPIC// /_}"
PAGE_TITLE="Wikipedia:WikiProject_${TITLE_NORMALIZED}"
API="https://en.wikipedia.org/w/api.php"

echo "=== Checking WikiProject: $TOPIC ==="
echo "Page: $PAGE_TITLE"
echo ""

# Check if page exists and get basic info
RESPONSE=$(curl -s -H "User-Agent: $USER_AGENT" \
  "${API}?action=query&titles=${PAGE_TITLE}&prop=info|revisions&rvprop=timestamp|user|comment&rvlimit=1&inprop=url|protection&format=json")

# Parse with Python for readability
python3 -c "
import json, sys

data = json.loads('''$RESPONSE''')
pages = data.get('query', {}).get('pages', {})
page_id, page = next(iter(pages.items()))

if 'missing' in page:
    print('Status: ❌ NOT FOUND')
    print()
    # Try to suggest alternative
    print('Suggestions:')
    print(f'  1. Check spelling of \"$TOPIC\"')
    print(f'  2. Try the exact page name at:')
    print(f'     https://en.wikipedia.org/wiki/{PAGE_TITLE}')
    print(f'  3. Browse the directory:')
    print(f'     https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Council/Directory')
    sys.exit(1)

print(f\"Status: ✅ EXISTS (page ID: {page['pageid']})\")
print(f\"Title:  {page['title']}\")
print(f\"URL:    https://en.wikipedia.org/wiki/{page['title'].replace(' ', '_')}\")
print()

# Revisions
revs = page.get('revisions', [])
if revs:
    r = revs[0]
    print(f\"Last edited: {r['timestamp']}\")
    print(f\"By:          {r.get('user', 'unknown')}\")
    if r.get('comment'):
        print(f\"Summary:     {r['comment'][:120]}\")
print()

# Protection
protection = page.get('protection', [])
if protection:
    print('Protection:')
    for p in protection:
        print(f\"  {p['type']}: {p['level']} (expires {p.get('expiry', 'never')})\")
else:
    print('Protection: none')

# Check assessment subpage
"
echo ""

# Check the /Assessment subpage
ASSESS_TITLE="Wikipedia:WikiProject_${TITLE_NORMALIZED}/Assessment"
ASSESS_CHECK=$(curl -s -H "User-Agent: $USER_AGENT" \
  "${API}?action=query&titles=${ASSESS_TITLE}&format=json")

echo "Assessment subpage:"
python3 -c "
import json
data = json.loads('''$ASSESS_CHECK''')
pages = data.get('query', {}).get('pages', {})
page_id, page = next(iter(pages.items()))
if 'missing' in page:
    print('  ❌ Not found — project may be inactive')
else:
    print(f'  ✅ {page[\"title\"]}')
    print(f'  URL: https://en.wikipedia.org/wiki/{page[\"title\"].replace(\" \", \"_\")}')
"

echo ""
echo "Popular pages:"
echo "  https://en.wikipedia.org/wiki/Wikipedia:WikiProject_${TITLE_NORMALIZED}/Popular_pages"
echo ""
echo "Article alerts:"
echo "  https://en.wikipedia.org/wiki/Wikipedia:WikiProject_${TITLE_NORMALIZED}/Article_alerts"
