#!/usr/bin/env bash
# Compare two revisions of a Wikipedia page and show a summary of changes.
#
# For detailed diff parsing (HTML tables, added/removed lines), see the
# wikimedia-diffs skill.
#
# Usage:
#   ./scripts/compare-revisions.sh --page "Albert Einstein"  (latest two revs)
#   ./scripts/compare-revisions.sh "Albert Einstein" 123456789 123456790
#   ./scripts/compare-revisions.sh --from-rev 123 --to-rev 456 --json

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
FROM_REV=""
TO_REV=""
PAGE=""

while [ $# -gt 0 ]; do
    case "$1" in
        --json) JSON_FLAG="--json"; shift ;;
        --page) shift; PAGE="$1"; shift ;;
        --from-rev) shift; FROM_REV="$1"; shift ;;
        --to-rev) shift; TO_REV="$1"; shift ;;
        *)
            # Positional: try to interpret as page, from_rev, to_rev
            if [ -z "$PAGE" ] && ! echo "$1" | grep -qE '^[0-9]+$'; then
                PAGE="$1"
            elif [ -z "$FROM_REV" ]; then
                FROM_REV="$1"
            elif [ -z "$TO_REV" ]; then
                TO_REV="$1"
            fi
            shift
            ;;
    esac
done

# If no explicit revs, fetch latest two for the page
if [ -z "$FROM_REV" ] || [ -z "$TO_REV" ]; then
    if [ -z "$PAGE" ]; then
        echo "Error: specify --page, or provide a page name and two revision IDs"
        usage
    fi
    ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$PAGE'''))")
    REVS=$(curl -s -H "User-Agent: $UA" \
        "${API}?action=query&prop=revisions&titles=${ENCODED}&rvlimit=2&rvprop=ids|user|size|comment|timestamp&format=json")
    REV_IDS=$(python3 -c "
import json, sys
d = json.load(sys.stdin)
pages = d.get('query', {}).get('pages', {})
for pid, p in pages.items():
    revs = p.get('revisions', [])
    if len(revs) >= 2:
        print(revs[1]['revid'], revs[0]['revid'])
" <<< "$REVS")
    FROM_REV=$(echo "$REV_IDS" | awk '{print $1}')
    TO_REV=$(echo "$REV_IDS" | awk '{print $2}')

    if [ -z "$FROM_REV" ] || [ -z "$TO_REV" ]; then
        echo "Error: could not determine revision IDs"
        exit 1
    fi
fi

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

# Get diff metadata and revision info
curl -s -H "User-Agent: $UA" \
    "${API}?action=compare&fromrev=${FROM_REV}&torev=${TO_REV}&prop=diffsize|ids|title|size|user|comment|timestamp&format=json" > "$TMPFILE"

python3 - "$FROM_REV" "$TO_REV" "$TMPFILE" "$JSON_FLAG" << 'PYEOF'
import json, sys

from_rev = sys.argv[1]
to_rev = sys.argv[2]
path = sys.argv[3]
json_mode = len(sys.argv) > 4 and sys.argv[4] == "--json"

with open(path) as f:
    data = json.load(f)

cmp = data.get("compare", {})
if not cmp:
    print("Error: could not compare revisions.")
    sys.exit(1)

from_title = cmp.get("fromtitle", "?")
to_title = cmp.get("totitle", "?")
from_revid = cmp.get("fromrevid", from_rev)
to_revid = cmp.get("torevid", to_rev)
from_size = cmp.get("fromsize", 0)
to_size = cmp.get("tosize", 0)
diffsize = cmp.get("diffsize", 0)
from_user = cmp.get("fromuser", "?")
to_user = cmp.get("touser", "?")
from_comment = cmp.get("fromcomment", "")
to_comment = cmp.get("tocomment", "")
from_ts = cmp.get("fromtimestamp", "").replace("T", " ")[:19] if cmp.get("fromtimestamp") else ""
to_ts = cmp.get("totimestamp", "").replace("T", " ")[:19] if cmp.get("totimestamp") else ""

net_change = to_size - from_size

if json_mode:
    print(json.dumps({
        "from": {"revid": from_revid, "title": from_title, "size": from_size,
                 "user": from_user, "timestamp": from_ts, "comment": from_comment},
        "to": {"revid": to_revid, "title": to_title, "size": to_size,
               "user": to_user, "timestamp": to_ts, "comment": to_comment},
        "diff": {"diffsize": diffsize, "net_change": net_change},
    }, indent=2))
else:
    print("=== Revision Comparison ===")
    print()
    print(f"  From: r{from_revid}")
    if from_ts:   print(f"        {from_ts}")
    if from_user: print(f"        by {from_user}")
    if from_comment: print(f"        \"{from_comment[:80]}\"")
    print(f"        {from_size} bytes")
    print()
    print(f"  To:   r{to_revid}")
    if to_ts:   print(f"        {to_ts}")
    if to_user: print(f"        by {to_user}")
    if to_comment: print(f"        \"{to_comment[:80]}\"")
    print(f"        {to_size} bytes")
    print()
    print(f"  Diff size:   {diffsize} bytes changed (churn)")
    if net_change >= 0:
        print(f"  Net change:  +{net_change} bytes (added)")
    else:
        print(f"  Net change:  {net_change} bytes (removed)")
    print()
    print(f"  For detailed diff parsing (added/removed lines, HTML table),")
    print(f"  see the wikimedia-diffs skill or run:")
    print(f"    https://en.wikipedia.org/w/index.php?diff={to_revid}&oldid={from_revid}")
PYEOF
