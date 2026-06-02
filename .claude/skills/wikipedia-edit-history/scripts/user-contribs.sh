#!/usr/bin/env bash
# Fetch recent contributions for a Wikipedia user with page titles and edit summaries.
#
# Usage:
#   ./scripts/user-contribs.sh "Example"
#   ./scripts/user-contribs.sh "192.168.1.1" --limit 20
#   ./scripts/user-contribs.sh "ClueBot NG" --json

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
LIMIT=20
USERNAME=""

while [ $# -gt 0 ]; do
    case "$1" in
        --json) JSON_FLAG="--json"; shift ;;
        --limit) shift; LIMIT="$1"; shift ;;
        *) USERNAME="$1"; shift ;;
    esac
done

if [ -z "$USERNAME" ]; then
    echo "Error: missing username"
    usage
fi

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

ENCODED_USER=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''${USERNAME}'''))")

curl -s -H "User-Agent: $UA" \
    "${API}?action=query&list=usercontribs&ucuser=${ENCODED_USER}&uclimit=${LIMIT}&ucprop=ids|title|timestamp|comment|size|sizediff|flags|tags&format=json" > "$TMPFILE"

python3 - "$USERNAME" "$TMPFILE" "$JSON_FLAG" << 'PYEOF'
import json, sys

username = sys.argv[1]
path = sys.argv[2]
json_mode = len(sys.argv) > 3 and sys.argv[3] == "--json"

with open(path) as f:
    data = json.load(f)

contribs = data.get("query", {}).get("usercontribs", [])
if not contribs:
    print(f"No contributions found for '{username}'.")
    sys.exit(0)

# User info from first result
user_id = contribs[0].get("userid", "?") if contribs else "?"

if json_mode:
    print(json.dumps({
        "username": username,
        "user_id": user_id,
        "total": len(contribs),
        "contributions": contribs,
    }, indent=2))
else:
    print(f"User: {username}  (ID: {user_id})")
    print(f"Showing {len(contribs)} recent contributions")
    print()
    for c in contribs:
        revid = c.get("revid", "?")
        title = c.get("title", "?")
        timestamp = c.get("timestamp", "?").replace("T", " ")[:19]
        comment = c.get("comment", "")
        size = c.get("size", 0)
        sizediff = c.get("sizediff", 0)
        minor = " [m]" if c.get("minor") else ""
        tags = c.get("tags", [])
        tag_str = f" [{','.join(tags[:3])}]" if tags else ""

        if sizediff > 0:
            size_str = f"+{sizediff}B → {size}B"
        elif sizediff < 0:
            size_str = f"{sizediff}B → {size}B"
        else:
            size_str = f"{size}B"

        print(f"  r{revid}{minor}{tag_str}")
        print(f"  [{timestamp}] {title}  ({size_str})")
        if comment:
            if len(comment) > 100:
                comment = comment[:100] + "..."
            print(f"  {comment}")
        print()
PYEOF
