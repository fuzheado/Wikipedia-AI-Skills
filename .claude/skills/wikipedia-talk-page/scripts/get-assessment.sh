#!/usr/bin/env bash
# Fetch WikiProject assessment class and importance for a given article
# from its talk page. Parses WikiProject banners in the talk page wikitext.
#
# For bulk database queries, see the wikimedia-page-assessment skill.
#
# Usage:
#   ./scripts/get-assessment.sh "Albert Einstein"
#   ./scripts/get-assessment.sh "Python (programming language)" --json

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

# Get the talk page title and fetch its content
TALK_TITLE="Talk:${TITLE}"
ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$TALK_TITLE'''))")

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

curl -s -H "User-Agent: $UA" \
    "${API}?action=query&prop=revisions&titles=${ENCODED}&rvslots=*&rvprop=content&format=json" > "$TMPFILE"

python3 - "$TITLE" "$TMPFILE" "$JSON_FLAG" << 'PYEOF'
import json, sys, re

title = sys.argv[1]
path = sys.argv[2]
json_mode = len(sys.argv) > 3 and sys.argv[3] == "--json"

with open(path) as f:
    data = json.load(f)

pages = data.get("query", {}).get("pages", {})

# Check if talk page exists
page_exists = False
for pid, page in pages.items():
    if "missing" not in page:
        page_exists = True
        break

assessments = []
for pid, page in pages.items():
    if "missing" in page:
        continue
    revs = page.get("revisions", [])
    if not revs:
        continue
    content = revs[0].get("slots", {}).get("main", {}).get("*", "")

    for m in re.finditer(r"\{\{WikiProject\s+(\w[\w\s]*)\s*\|([^}]+)\}\}", content):
        project = m.group(1).strip()
        params_str = m.group(2)
        cls = re.search(r"class\s*=\s*(\w+)", params_str)
        imp = re.search(r"importance\s*=\s*(\w+)", params_str)
        listas = re.search(r"listas\s*=\s*([^|]+)", params_str)
        assessments.append({
            "project": project,
            "class": cls.group(1) if cls else None,
            "importance": imp.group(1) if imp else None,
            "listas": listas.group(1).strip() if listas else None,
        })

if json_mode:
    print(json.dumps({
        "article": title,
        "has_talk_page": page_exists,
        "assessment_count": len(assessments),
        "assessments": assessments,
    }, indent=2))
else:
    print(f"Article: {title}")
    if not page_exists:
        print("Talk page does not exist (no discussions have been started).")
        print("(Article may still have assessments in the database — "
              "use the wikimedia-page-assessment skill for bulk queries.)")
        sys.exit(0)
    if not assessments:
        print("No WikiProject banners found on talk page.")
        sys.exit(0)
    print(f"Assessments: {len(assessments)} WikiProject(s)")
    print()
    for a in assessments:
        c = f"class={a['class']}" if a['class'] else ""
        i = f"importance={a['importance']}" if a['importance'] else ""
        tags = ", ".join(filter(None, [c, i]))
        print(f"  {a['project']}: {tags}")
PYEOF
