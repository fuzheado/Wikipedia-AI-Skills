#!/usr/bin/env bash
# List all archived discussion subpages for a given talk page.
#
# Usage:
#   ./scripts/list-archives.sh "Albert Einstein"
#   ./scripts/list-archives.sh "Talk:Albert Einstein"
#   ./scripts/list-archives.sh "Python (programming language)" --json

set -euo pipefail

UA="talk-page-demo/1.0 (https://en.wikipedia.org; demo@example.com) WikiSkills"
API="https://en.wikipedia.org/w/api.php"

usage() {
    awk '/^# Usage:/ { found=1 } found && /^#/ { sub(/^# /, ""); print } found && /^$/ { exit }' "$0"
    exit 0
}

if [ $# -eq 0 ] || [ "$1" = "--help" ]; then
    usage
fi

JSON_FLAG=""
TITLE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --json) JSON_FLAG="--json"; shift ;;
        *) TITLE="$1"; shift ;;
    esac
done

if [ -z "$TITLE" ]; then
    echo "Error: missing article title"
    usage
fi

# Normalize: if given an article title (not already Talk:), prepend Talk:
if [[ "$TITLE" != Talk:* ]]; then
    TALK_PAGE="Talk:${TITLE}"
else
    TALK_PAGE="$TITLE"
fi

ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''${TALK_PAGE}/Archive'''))")

# Fetch archives and write to temp file
TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

curl -s -H "User-Agent: $UA" \
    "${API}?action=query&list=prefixsearch&pssearch=${ENCODED}&pslimit=100&format=json" > "$TMPFILE"

python3 - "$TALK_PAGE" "$TMPFILE" "$JSON_FLAG" << 'PYEOF'
import json, sys

talk_page = sys.argv[1]
path = sys.argv[2]
json_mode = len(sys.argv) > 3 and sys.argv[3] == "--json"

with open(path) as f:
    data = json.load(f)

results = data.get("query", {}).get("prefixsearch", [])
archives = [r["title"] for r in results if r["title"] != talk_page]

if json_mode:
    print(json.dumps({
        "talk_page": talk_page,
        "archive_count": len(archives),
        "archives": archives,
    }, indent=2))
else:
    if not archives:
        print(f"Talk page: {talk_page}")
        print("No archive subpages found.")
        sys.exit(0)
    print(f"Talk page: {talk_page}")
    print(f"Archives: {len(archives)} found")
    print()
    for a in archives:
        print(f"  • {a}")
PYEOF
