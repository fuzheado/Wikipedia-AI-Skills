#!/usr/bin/env bash
# Show recent edits to a Wikipedia page with diff size, user, and edit summary.
#
# Usage:
#   ./scripts/recent-edits.sh "Albert Einstein"
#   ./scripts/recent-edits.sh "Python (programming language)" --limit 20
#   ./scripts/recent-edits.sh "Berlin" --json

set -euo pipefail

UA="edit-history-demo/1.0 (https://en.wikipedia.org; demo@example.com) WikiSkills"
API="https://en.wikipedia.org/w/api.php"

usage() {
    awk '/^# Usage:/ { found=1 } found && /^#/ { sub(/^# /, ""); print } found && /^$/ { exit }' "$0"
    exit 0
}

if [ $# -eq 0 ] || [ "$1" = "--help" ]; then
    usage
fi

JSON_FLAG=""
LIMIT=10
TITLE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --json) JSON_FLAG="--json"; shift ;;
        --limit) shift; LIMIT="$1"; shift ;;
        *) TITLE="$1"; shift ;;
    esac
done

if [ -z "$TITLE" ]; then
    echo "Error: missing article title"
    usage
fi

ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$TITLE'''))")

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

curl -s -H "User-Agent: $UA" \
    "${API}?action=query&prop=revisions&titles=${ENCODED}&rvlimit=${LIMIT}&rvprop=ids|timestamp|user|userid|size|comment|tags|flags&format=json" > "$TMPFILE"

python3 - "$TITLE" "$TMPFILE" "$JSON_FLAG" << 'PYEOF'
import json, sys

title = sys.argv[1]
path = sys.argv[2]
json_mode = len(sys.argv) > 3 and sys.argv[3] == "--json"

with open(path) as f:
    data = json.load(f)

pages = data.get("query", {}).get("pages", {})
if not pages:
    print("Page not found.")
    sys.exit(1)

page_id, page = next(iter(pages.items()))
info = page.get("pageid", "?")
resolved = page.get("title", title)

revs = page.get("revisions", [])
if not revs:
    print("No revisions found.")
    sys.exit(1)

def fmt_size(delta, size):
    """Format byte size change."""
    if delta is None:
        return f"{size}B"
    if delta > 0:
        return f"+{delta}B"
    elif delta < 0:
        return f"{delta}B"
    else:
        return "0B"

if json_mode:
    out = []
    for i, rev in enumerate(revs):
        prev_size = revs[i + 1].get("size", 0) if i + 1 < len(revs) else None
        cur_size = rev.get("size", 0)
        delta = (cur_size - prev_size) if prev_size is not None else None
        out.append({
            "revid": rev.get("revid"),
            "timestamp": rev.get("timestamp"),
            "user": rev.get("user", "(unknown)"),
            "anon": rev.get("userid", 0) == 0,
            "size": cur_size,
            "delta": delta,
            "comment": rev.get("comment", ""),
            "minor": rev.get("minor", False),
            "tags": rev.get("tags", []),
        })
    print(json.dumps(out, indent=2))
else:
    print(f"Recent edits to: {resolved}  (page ID: {info})")
    print()
    for i, rev in enumerate(revs):
        prev_size = revs[i + 1].get("size", 0) if i + 1 < len(revs) else None
        cur_size = rev.get("size", 0)
        delta = (cur_size - prev_size) if prev_size is not None else None

        revid = rev.get("revid", "?")
        user = rev.get("user", "(unknown)")
        timestamp = rev.get("timestamp", "?").replace("T", " ")[:19]
        comment = rev.get("comment", "")
        minor = " [m]" if rev.get("minor") else ""
        anon = " [anon]" if rev.get("userid", 0) == 0 else ""
        tags = rev.get("tags", [])
        tag_str = f" [{','.join(tags[:3])}]" if tags else ""
        size_str = fmt_size(delta, cur_size)

        print(f"  r{revid}{minor}{anon}{tag_str}")
        print(f"  [{timestamp}] {user}  ({size_str})")
        if comment:
            # Truncate long comments
            if len(comment) > 90:
                comment = comment[:90] + "..."
            print(f"  {comment}")
        print()
PYEOF
