#!/usr/bin/env bash
# Page anatomy summary — fetch a compact overview of a Wikipedia article's structure.
#
# Reports: title, page ID, infobox type, protection level, redirect status,
# disambiguation status, visible and hidden categories, template count,
# and WikiProject assessment banners from the talk page.
#
# Usage:
#   ./scripts/page-summary.sh "Albert Einstein"
#   ./scripts/page-summary.sh "Python (programming language)" --json

set -euo pipefail

UA="page-anatomy-demo/1.0 (https://en.wikipedia.org; demo@example.com) WikiSkills"
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

ENCODED=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$TITLE'''))")

# Fetch data, write to temp files for safe Python processing
TMP_SUMMARY=$(mktemp)
TMP_TALK=$(mktemp)
trap 'rm -f "$TMP_SUMMARY" "$TMP_TALK"' EXIT

curl -s -H "User-Agent: $UA" \
    "${API}?action=query&prop=info|categories|templates|pageprops&titles=${ENCODED}&redirects=1&inprop=protection&cllimit=80&tllimit=80&format=json" > "$TMP_SUMMARY"

TALK_ENCODED=$(python3 -c "import urllib.parse; import sys; print(urllib.parse.quote('Talk: ' + sys.argv[1]))" "$TITLE")
curl -s -H "User-Agent: $UA" \
    "${API}?action=query&prop=revisions&titles=${TALK_ENCODED}&rvslots=*&rvprop=content&format=json" > "$TMP_TALK"

python3 - "$TITLE" "$TMP_SUMMARY" "$TMP_TALK" "$JSON_FLAG" << 'PYEOF'
import json, sys, re

title = sys.argv[1]
summary_path = sys.argv[2]
talk_path = sys.argv[3]
json_mode = len(sys.argv) > 4 and sys.argv[4] == "--json"

with open(summary_path) as f:
    data = json.load(f)
with open(talk_path) as f:
    talk_data = json.load(f)

pages = data.get("query", {}).get("pages", {})
redirects = data.get("query", {}).get("redirects", [])

if not pages:
    print("Page not found.")
    sys.exit(1)

page_id, page = next(iter(pages.items()))
resolved_title = page.get("title", title)

# Protection
protections = page.get("protection", [])

# Categories
cats = page.get("categories", [])
visible_cats = [c["title"] for c in cats if "hidden" not in c]
hidden_cats = [c["title"] for c in cats if "hidden" in c]

# Templates
templates = page.get("templates", [])
infobox_templates = [t["title"] for t in templates if "Infobox" in t["title"]]

# Page props
pageprops = page.get("pageprops", {})
is_disambig = "disambiguation" in str(pageprops)
wikibase_id = pageprops.get("wikibase_item", "")

# Talk page assessment
talk_pages = talk_data.get("query", {}).get("pages", {})
assessments = []
for tp_id, tp in talk_pages.items():
    if "missing" not in tp:
        revs = tp.get("revisions", [])
        if revs:
            content = revs[0].get("slots", {}).get("main", {}).get("content", "")
            for m in re.finditer(r"\{\{WikiProject\s+(\w+)\s*\|([^}]+)\}\}", content):
                project = m.group(1)
                params_str = m.group(2)
                cls = re.search(r"class\s*=\s*(\w+)", params_str)
                imp = re.search(r"importance\s*=\s*(\w+)", params_str)
                assessments.append({
                    "project": project,
                    "class": cls.group(1) if cls else None,
                    "importance": imp.group(1) if imp else None,
                })

if json_mode:
    out = {
        "title": resolved_title,
        "page_id": page.get("pageid"),
        "length_bytes": page.get("length", 0),
        "is_redirect": bool(redirects),
        "is_disambiguation": is_disambig,
        "wikibase_qid": wikibase_id,
        "infobox_types": infobox_templates,
        "template_count": len(templates),
        "visible_categories": len(visible_cats),
        "hidden_categories": len(hidden_cats),
        "protection": {p["type"]: {"level": p["level"], "expiry": p.get("expiry", "infinity")} for p in protections},
        "assessments": assessments,
    }
    print(json.dumps(out, indent=2))
else:
    print(f"=== Page Summary: {resolved_title} ===")
    print(f"  Page ID:       {page.get('pageid', 'N/A')}")
    print(f"  Length:        {page.get('length', 0)} bytes")
    if redirects:
        print(f"  ⚠️  Redirect:    → {redirects[0].get('to', '?')}")
    if is_disambig:
        print(f"  ℹ️  Disambiguation page")
    if wikibase_id:
        print(f"  Wikidata:      {wikibase_id}")
    print()
    print(f"  Infobox:       {infobox_templates[0] if infobox_templates else 'None'}")
    print(f"  Templates:     {len(templates)} total")
    print(f"  Categories:    {len(visible_cats)} visible, {len(hidden_cats)} hidden")
    print()
    if protections:
        print(f"  Protection:")
        for p in protections:
            expiry = p.get("expiry", "infinity")
            print(f"    {p['type']}: {p['level']} ({expiry})")
    else:
        print(f"  Protection:    None (open)")
    print()
    if assessments:
        print(f"  Assessments ({len(assessments)}):")
        for a in assessments[:5]:
            c = f"class={a['class']}" if a['class'] else ""
            i = f"importance={a['importance']}" if a['importance'] else ""
            tags = ", ".join(filter(None, [c, i]))
            print(f"    {a['project']}: {tags}")
        if len(assessments) > 5:
            print(f"    ... and {len(assessments) - 5} more")
    else:
        print(f"  Assessments:   No WikiProject banners found")
    if visible_cats:
        print()
        print(f"  Categories ({len(visible_cats)}):")
        for c in visible_cats[:8]:
            print(f"    {c}")
        if len(visible_cats) > 8:
            print(f"    ... and {len(visible_cats) - 8} more")
PYEOF
