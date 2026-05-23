#!/usr/bin/env bash
# Wikimedia Commons search demo — MediaSearch vs CirrusSearch (traditional)
# Both modes search the File namespace (ns=6) by default, but --ns can override.
# Usage:
#   ./commons-search.sh "query"                  — CirrusSearch, ns=6
#   ./commons-search.sh --media "query"          — MediaSearch, ns=6
#   ./commons-search.sh --ns 0 "query"           — CirrusSearch, ns=0 (gallery pages)
#   ./commons-search.sh --ns 0,6,14 "query"      — CirrusSearch, multiple namespaces
#   ./commons-search.sh --media --ns 0 "query"   — MediaSearch, custom namespace
#   ./commons-search.sh --help                   — This help message

set -euo pipefail

UA="commons-search-demo/1.0 (https://commons.wikimedia.org; demo@example.com) WMSkills"

usage() {
    awk '/^# / { sub(/^# /, ""); print } /^$/ { exit }' "$0"
    exit 0
}

# URL-encode a string
urlencode() {
    python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$1"
}

# ---- Argument parsing ----
MEDIA_MODE=false
NAMESPACE="6"

while [ $# -gt 0 ]; do
    case "$1" in
        --help)
            usage
            ;;
        --media)
            MEDIA_MODE=true
            shift
            ;;
        --ns)
            if [ $# -lt 2 ]; then
                echo "Error: --ns requires a namespace number or comma-separated list (e.g. 6 or 0,6,14)"
                exit 1
            fi
            NAMESPACE="$2"
            shift 2
            ;;
        *)
            # Everything else is the query
            break
            ;;
    esac
done

QUERY="$*"
if [ -z "$QUERY" ]; then
    echo "Error: missing query"
    usage
fi

if [ "$MEDIA_MODE" = true ]; then
    echo "=== MediaSearch (semantic) ==="
else
    echo "=== CirrusSearch (full-text) ==="
fi
echo "Query: $QUERY"
echo "Namespace(s): $NAMESPACE"
echo ""

ENCODED=$(urlencode "$QUERY")
API_URL="https://commons.wikimedia.org/w/api.php"

if [ "$MEDIA_MODE" = true ]; then
    RESPONSE=$(curl -s -H "User-Agent: $UA" \
        "${API_URL}?action=query&list=search&srsearch=${ENCODED}&srnamespace=${NAMESPACE}&srbackend=MediaSearch&format=json&srlimit=10")
else
    RESPONSE=$(curl -s -H "User-Agent: $UA" \
        "${API_URL}?action=query&list=search&srsearch=${ENCODED}&srnamespace=${NAMESPACE}&format=json&srlimit=10")
fi

echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    print('Error: API returned non-JSON response. Check network or User-Agent.')
    sys.exit(1)

results = data.get('query', {}).get('search', [])
if not results:
    print('No results found.')
else:
    # Map namespace IDs to names (Commons-specific)
    ns_names = {0: 'Gallery', 6: 'File', 10: 'Template', 12: 'Help', 14: 'Category'}
    for r in results:
        ns_id = r.get('ns', 0)
        ns_label = ns_names.get(ns_id, f'NS{ns_id}')
        title = r['title']
        print(f'  • {title}  [{ns_label}]')
        snippet = r.get('snippet', 'N/A')[:120]
        if snippet != 'N/A':
            print(f'    {snippet}...')
        print()
"
