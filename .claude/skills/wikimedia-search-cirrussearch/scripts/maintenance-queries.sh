#!/usr/bin/env bash
# Maintenance Queries — Pre-built CirrusSearch maintenance queries for common patrolling tasks
# Usage:
#   ./maintenance-queries.sh list              — List all available query types
#   ./maintenance-queries.sh <type> [limit]    — Run a query (default limit 20)
#   ./maintenance-queries.sh <type> --json     — Raw JSON output
#   ./maintenance-queries.sh --help

set -euo pipefail

UA="maintenance-queries/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; user@example.com) WMSkills"
WIKI="en.wikipedia.org"
LIMIT=20
RAW_JSON=false
QUERY=""

types() {
    cat <<'TYPES'
Available maintenance query types:

  unsourced-blp       Living people articles with no sources (BLP unsourced)
  unsourced-pages     All unsourced articles
  dead-links          Articles tagged with dead link templates
  missing-image       Pages with an infobox but no image parameter
  uncategorized       Recently created uncategorized pages
  recently-created     Pages created in the last N days (default 7)
  recent-category     Pages in a category edited recently (requires CAT= param)
  stub-category       Pages in a specific stub category (requires CAT= param)
  template-usage      Pages using a specific template (requires TEMPLATE= param)
  linksto-page        Pages linking to a specific page (requires LINKSTO= param)
  subpages-of         Subpages of a given page (requires PARENT= param)
  deprecated-tmpl     Pages using deprecated templates
  copyedit-needed     Articles needing copy editing
  pov-check           Articles flagged for POV/neutrality review
  no-categories       Pages in the uncategorized tracking category
  recent-stubs        Recent articles tagged as stubs
  overcategorized     Pages with parent+child category overlap
  no-image-blp        BLP articles without an infobox image

Set environment variables for parameterized queries:
  CAT=CategoryName      For recent-category, stub-category
  TEMPLATE=TemplateName For template-usage
  LINKSTO=PageTitle     For linksto-page
  PARENT=PageName       For subpages-of
  DAYS=N                For recently-created (default 7)
TYPES
}

if [ $# -eq 0 ]; then
    echo "Usage: $0 <type> [limit] [--json]"
    echo ""
    types
    exit 1
fi

case "$1" in
    --help|-h|list) types; exit 0 ;;
esac

TYPE="$1"
shift

while [ $# -gt 0 ]; do
    case "$1" in
        --json) RAW_JSON=true; shift ;;
        --wiki) WIKI="$2"; shift 2 ;;
        *) LIMIT="$1"; shift ;;
    esac
done

# Apply DAYS default
DAYS="${DAYS:-7}"

# Build the CirrusSearch query string
case "$TYPE" in
    unsourced-blp)
        QUERY='hastemplate:"BLP unsourced" incategory:"Living people"'
        DESC="Unsourced BLP articles"
        ;;
    unsourced-pages)
        QUERY='hastemplate:"Unreferenced" -incategory:"Living people"'
        DESC="Unsourced articles (non-BLP)"
        ;;
    dead-links)
        QUERY='hastemplate:"Dead link" incategory:"All articles with dead external links"'
        DESC="Articles with dead links"
        ;;
    missing-image)
        QUERY='hastemplate:"Infobox person" -insource:"|image =" -insource:"|image="'
        DESC="Infobox person pages without image"
        ;;
    uncategorized)
        QUERY="incategory:\"All uncategorized pages\" creationdate:>=today-${DAYS}d"
        DESC="Recently created uncategorized pages (${DAYS}d)"
        ;;
    recently-created)
        QUERY="creationdate:>=today-${DAYS}d"
        DESC="Pages created in the last ${DAYS} days"
        ;;
    recent-category)
        CAT="${CAT:-}"
        if [ -z "$CAT" ]; then
            echo "Error: CAT= is required for recent-category. E.g. CAT=Physics"
            exit 1
        fi
        QUERY="incategory:\"${CAT}\" lasteditdate:>=today-${DAYS}d"
        DESC="Recently edited pages in Category:${CAT} (${DAYS}d)"
        ;;
    stub-category)
        CAT="${CAT:-}"
        if [ -z "$CAT" ]; then
            echo "Error: CAT= is required for stub-category. E.g. CAT=Physics stubs"
            exit 1
        fi
        QUERY="incategory:\"${CAT}\""
        DESC="Pages in Category:${CAT}"
        ;;
    template-usage)
        TEMPLATE="${TEMPLATE:-}"
        if [ -z "$TEMPLATE" ]; then
            echo "Error: TEMPLATE= is required for template-usage. E.g. TEMPLATE='Infobox scientist'"
            exit 1
        fi
        QUERY="hastemplate:\"${TEMPLATE}\""
        DESC="Pages using Template:${TEMPLATE}"
        ;;
    linksto-page)
        LINKSTO="${LINKSTO:-}"
        if [ -z "$LINKSTO" ]; then
            echo "Error: LINKSTO= is required for linksto-page. E.g. LINKSTO='Albert Einstein'"
            exit 1
        fi
        QUERY="linksto:\"${LINKSTO}\""
        DESC="Pages linking to ${LINKSTO}"
        ;;
    subpages-of)
        PARENT="${PARENT:-}"
        if [ -z "$PARENT" ]; then
            echo "Error: PARENT= is required for subpages-of. E.g. PARENT='Wikipedia:WikiProject Physics'"
            exit 1
        fi
        QUERY="subpageof:\"${PARENT}\""
        DESC="Subpages of ${PARENT}"
        ;;
    deprecated-tmpl)
        QUERY='incategory:"Pages using deprecated templates"'
        DESC="Pages using deprecated templates"
        ;;
    copyedit-needed)
        QUERY='hastemplate:"Copy edit"'
        DESC="Articles needing copy editing"
        ;;
    pov-check)
        QUERY='hastemplate:"POV" incategory:"All articles with unsourced statements"'
        DESC="Articles flagged for POV/neutrality review"
        ;;
    no-categories)
        QUERY='incategory:"All uncategorized pages"'
        DESC="Pages with no categories"
        ;;
    recent-stubs)
        QUERY="creationdate:>=today-${DAYS}d incategory:\"All stub articles\""
        DESC="Stub articles created in the last ${DAYS} days"
        ;;
    overcategorized)
        QUERY='incategory:"Wikipedia articles that are excessively categorized"'
        DESC="Overcategorized pages"
        ;;
    no-image-blp)
        QUERY='hastemplate:"Infobox person" incategory:"Living people" -insource:"|image =" -insource:"|image="'
        DESC="BLP articles with infobox but no image"
        ;;
    *)
        echo "Unknown type: $TYPE"
        echo ""
        types
        exit 1
        ;;
esac

echo "=== $DESC ==="
echo "Query: $QUERY"
echo ""

ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")
API_URL="https://${WIKI}/w/api.php"
LIMIT_INT=$LIMIT

if [ "$RAW_JSON" = true ]; then
    curl -s -H "User-Agent: $UA" \
        "${API_URL}?action=query&list=search&srsearch=${ENCODED}&srnamespace=0&srwhat=text&srprop=size|wordcount|timestamp|snippet&format=json&srlimit=${LIMIT_INT}"
    exit 0
fi

RESPONSE=$(curl -s -H "User-Agent: $UA" \
    "${API_URL}?action=query&list=search&srsearch=${ENCODED}&srnamespace=0&srwhat=text&srprop=size|wordcount|timestamp|snippet&format=json&srlimit=${LIMIT_INT}")

python3 -c "
import json, sys, re

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    print('Error: API returned non-JSON response.')
    sys.exit(1)

results = data.get('query', {}).get('search', [])
total = data.get('query', {}).get('searchinfo', {}).get('totalhits', 0)

print(f'Wiki:      $WIKI')
print(f'Type:      $TYPE')
print(f'Hits:      {total}')
print(f'Showing:   {len(results)}')
print()

if not results:
    print('No results found.')
    sys.exit(0)

for i, r in enumerate(results, 1):
    title = r['title']
    size = r.get('size', '?')
    wordcount = r.get('wordcount', '?')
    timestamp = r.get('timestamp', '')
    snippet = re.sub(r'<[^>]+>', '', r.get('snippet', ''))[:120]
    print(f'{i:3d}. {title}')
    if snippet:
        print(f'     {snippet}...')
    print(f'     {size}B | {wordcount} words | {timestamp}')
    print()
" <<< "$RESPONSE"
