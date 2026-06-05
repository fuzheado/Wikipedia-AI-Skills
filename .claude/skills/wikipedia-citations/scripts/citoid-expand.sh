#!/usr/bin/env bash
# Expand a URL, DOI, ISBN, or PMID into a full citation template using Citoid.
#
# Usage:
#   ./citoid-expand.sh https://example.com/article
#   ./citoid-expand.sh 10.7554/eLife.32259       # DOI
#   ./citoid-expand.sh 978-0-262-52316-5          # ISBN
#   ./citoid-expand.sh https://example.com --raw  # Show raw JSON

set -euo pipefail

if [[ $# -eq 0 ]]; then
    echo "🧠 citoid-expand.sh — Auto-generate a full citation template from a URL, DOI, ISBN, or PMID"
    echo ""
    echo "Usage: $0 <url|doi|isbn|pmid> [--raw]"
    echo ""
    echo "Examples:"
    echo "  $0 https://example.com/article"
    echo "  $0 10.7554/eLife.32259"
    echo "  $0 978-0-262-52316-5"
    exit 1
fi

INPUT="${1:?}"
RAW=false
if [[ "${2:-}" == "--raw" ]]; then
    RAW=true
fi

USER_AGENT="CitoidExpand/1.0 (user@example.com) ContentGapResearch"

# Determine if input is a URL or an identifier
if [[ "$INPUT" =~ ^https?:// ]]; then
    # URL — pass through as-is
    ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$INPUT', safe=''))")
elif [[ "$INPUT" =~ ^10\. ]]; then
    # DOI
    ENCODED="$INPUT"
elif [[ "$INPUT" =~ ^[0-9-]{10,}$ ]] || [[ "$INPUT" =~ ^978 ]]; then
    # ISBN (10 or 13 digits with optional hyphens)
    ENCODED="$INPUT"
else
    echo "⚠  Could not determine input type. Treating as URL."
    ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$INPUT', safe=''))")
fi

echo "🔍 Fetching citation metadata from Citoid..." >&2
echo "   Input: $INPUT" >&2
echo

RESPONSE=$(curl -s "https://en.wikipedia.org/api/rest_v1/data/citation/zotero/${ENCODED}" \
  -H "User-Agent: $USER_AGENT")

if [[ "$RAW" == true ]]; then
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    exit 0
fi

# Try to parse and convert to wiki template
echo "$RESPONSE" | python3 -c "
import sys, json

data = json.load(sys.stdin)
if not data:
    print('❌ No citation data found.')
    sys.exit(1)

c = data[0]  # First (best) match

item_type = c.get('itemType', 'webpage')
url = c.get('url', '')
title = c.get('title', '')
date = c.get('date', '')
access_date = c.get('accessDate', '')

type_map = {
    'journalArticle': 'cite journal',
    'book': 'cite book',
    'bookSection': 'cite book',
    'newspaperArticle': 'cite news',
    'magazineArticle': 'cite magazine',
    'webpage': 'cite web',
    'report': 'cite report',
    'thesis': 'cite thesis',
    'conferencePaper': 'cite conference',
    'patent': 'cite patent',
    'film': 'cite AV media',
    'podcast': 'cite podcast',
    'interview': 'cite interview',
    'map': 'cite map',
}
template = type_map.get(item_type, 'cite web')

parts = [f'{{{{{template}}}']
if url: parts.append(f' |url={url}')
if title: parts.append(f' |title={title}')
if item_type == 'webpage':
    website = c.get('websiteTitle', '') or c.get('publisher', '')
    if website: parts.append(f' |website={website}')
if date: parts.append(f' |date={date}')
if access_date: parts.append(f' |access-date={access_date}')
if item_type == 'newspaperArticle':
    paper = c.get('publicationTitle', '')
    if paper: parts.append(f' |newspaper={paper}')
if item_type == 'journalArticle':
    journal = c.get('publicationTitle', '') or c.get('journalTitle', '')
    if journal: parts.append(f' |journal={journal}')
    vol = c.get('volume', '')
    if vol: parts.append(f' |volume={vol}')
    issue = c.get('issue', '')
    if issue: parts.append(f' |issue={issue}')
    pages = c.get('pages', '')
    if pages: parts.append(f' |pages={pages}')
    doi = c.get('DOI', '')
    if doi: parts.append(f' |doi={doi}')
if item_type == 'book':
    pub = c.get('publisher', '')
    if pub: parts.append(f' |publisher={pub}')
    isbn_list = c.get('ISBN', [])
    if isbn_list: parts.append(f' |isbn={isbn_list[0]}')

authors = c.get('author', [])
for i, (last, first) in enumerate(authors, 1):
    if i == 1:
        parts.append(f' |last={last} |first={first}')
    else:
        parts.append(f' |last{i}={last} |first{i}={first}')

parts.append('}}')
print('\\n'.join(parts))
" 2>/dev/null || {
    echo "⚠  Could not parse Citoid response. Raw data:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
}
