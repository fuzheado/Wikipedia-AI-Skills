#!/usr/bin/env bash
# CirrusSearch CLI — Run CirrusSearch queries against any Wikimedia wiki
# Usage:
#   ./cirrus-search.sh "query"                    — Full-text search on enwiki, main namespace
#   ./cirrus-search.sh --wiki en.wikipedia.org "query"
#   ./cirrus-search.sh --ns 0 "query"
#   ./cirrus-search.sh --near "query"              — Near-match title search
#   ./cirrus-search.sh --prefix "prefix"           — Prefix search
#   ./cirrus-search.sh --limit 100 "query"
#   ./cirrus-search.sh --sort last_edit_desc "query"
#   ./cirrus-search.sh --prop "size|wordcount|timestamp|snippet|score" "query"
#   ./cirrus-search.sh --json "query"              — Raw JSON output
#   ./cirrus-search.sh --help

set -euo pipefail

UA="cirrus-search-cli/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; user@example.com) WMSkills"

usage() {
    grep '^#' "$0" | sed 's/^# \?//' | sed '$d'
    exit 0
}

# ---- Defaults ----
WIKI="en.wikipedia.org"
NAMESPACE="0"
SRWHAT="text"
LIMIT="20"
QUERY=""
SORT="relevance"
PROP="size|wordcount|timestamp|snippet"
RAW_JSON=false

while [ $# -gt 0 ]; do
    case "$1" in
        --help) usage ;;
        --wiki)
            WIKI="$2"; shift 2 ;;
        --ns|--namespace)
            NAMESPACE="$2"; shift 2 ;;
        --near)
            SRWHAT="near_match"; shift ;;
        --prefix)
            SRWHAT="title"; shift ;;
        --limit)
            LIMIT="$2"; shift 2 ;;
        --sort)
            SORT="$2"; shift 2 ;;
        --prop)
            PROP="$2"; shift 2 ;;
        --json)
            RAW_JSON=true; shift ;;
        --)
            shift; QUERY="$*"; break ;;
        *)
            QUERY="$1"; shift ;;
    esac
done

if [ -z "$QUERY" ]; then
    echo "Error: missing search query" >&2
    grep '^#' "$0" | sed 's/^# \?//' | sed '$d' >&2
    exit 1
fi

# URL-encode the query
ENCODED=$(python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")

API_URL="https://${WIKI}/w/api.php"

if [ "$RAW_JSON" = true ]; then
    curl -s -H "User-Agent: $UA" \
        "${API_URL}?action=query&list=search&srsearch=${ENCODED}&srnamespace=${NAMESPACE}&srwhat=${SRWHAT}&srsort=${SORT}&srprop=${PROP}&format=json&srlimit=${LIMIT}"
    exit 0
fi

# Formatted output
RESPONSE=$(curl -s -H "User-Agent: $UA" \
    "${API_URL}?action=query&list=search&srsearch=${ENCODED}&srnamespace=${NAMESPACE}&srwhat=${SRWHAT}&srsort=${SORT}&srprop=${PROP}&format=json&srlimit=${LIMIT}")

python3 -c "
import json, sys

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    print('Error: API returned non-JSON response. Check network or User-Agent.')
    sys.exit(1)

results = data.get('query', {}).get('search', [])
total = data.get('query', {}).get('searchinfo', {}).get('totalhits', 0)

ns_names = {0: 'Article', 1: 'Talk', 2: 'User', 4: 'Wikipedia', 6: 'File',
            10: 'Template', 14: 'Category'}

print(f'Wiki:      $WIKI')
print(f'Query:     $QUERY')
print(f'Namespace: $NAMESPACE')
print(f'Mode:      $SRWHAT')
print(f'Hits:      {total}')
print(f'Showing:   {len(results)}')
print()

if not results:
    print('No results found.')
    sys.exit(0)

for i, r in enumerate(results, 1):
    ns_id = r.get('ns', 0)
    ns_label = ns_names.get(ns_id, f'NS{ns_id}')
    title = r['title']
    snippet = r.get('snippet', '')
    size = r.get('size', '?')
    wordcount = r.get('wordcount', '?')
    timestamp = r.get('timestamp', '')
    score = r.get('score', '')

    # Strip HTML tags from snippet
    import re
    clean = re.sub(r'<[^>]+>', '', snippet)[:150]

    print(f'{i:3d}. {title}  [{ns_label}]')
    if clean:
        print(f'     {clean}...')
    print(f'     Size: {size}B | Words: {wordcount} | Date: {timestamp}')
    if score:
        print(f'     Score: {score}')
    print()
" <<< "$RESPONSE"
