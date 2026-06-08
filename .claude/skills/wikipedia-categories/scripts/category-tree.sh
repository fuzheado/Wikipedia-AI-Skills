#!/usr/bin/env bash
# category-tree.sh — Explore a Wikipedia category hierarchy from the CLI
#
# Uses action=categorytree (1 API call, returns pre-rendered HTML).
# For alternatives, see the skill's "Category Hierarchy" section.
#
# Requires: curl, jq, python3
#
# ⚠️ CategoryTree API HTML structure:
# The API returns <div>-based HTML, not <li>/<ul> lists. The nesting is:
#   <div class="CategoryTreeSection">
#     <div class="CategoryTreeItem"><a>Name</a></div>
#     <div class="CategoryTreeChildren">          ← may have style="display:none"
#       <div class="CategoryTreeSection">...       ← nested subcategories
#     </div>
#   </div>
#
# Key gotchas:
# 1. The parser must track ALL <div> tags, not just the ones it cares about.
#    If you skip CategoryTreeItem/CategoryTreeBullet divs, their </div>
#    closes will pop the wrong entry from your tracking stack.
# 2. Collapsed subcategories use <div class="CategoryTreeChildren"
#    style="display:none"> — the style attribute must not break the regex.
# 3. Empty category branches have a bare <div></div> inside the section.
#
# See the SKILL.md "Category Hierarchy" section for the table of div classes.

set -euo pipefail

usage() {
  cat <<'EOF'
category-tree.sh — Explore a Wikipedia category hierarchy

USAGE:
  ./category-tree.sh <category> [depth] [mode] [language]

ARGUMENTS:
  category   Category name (required, without "Category:" prefix)
  depth      How many levels deep to recurse (default: 2)
  mode       What to show (default: categories)
               categories  — subcategories only
               pages       — articles + subcategories
               all         — everything (pages, subcats, files)
               parents     — go upward (show parent categories)
  language   Wikipedia language code (default: en)

EXAMPLES:
  ./category-tree.sh Physics                  Deepest 2 levels
  ./category-tree.sh Physics 3                Deepest 3 levels
  ./category-tree.sh "2026 protests"          Category with spaces
  ./category-tree.sh Physics 2 pages          Show articles too
  ./category-tree.sh Physics 1 all            Everything at 1 level
  ./category-tree.sh Physics 1 parents        Show parent categories
  ./category-tree.sh Frankreich 1 categories de  German Wikipedia

HOW IT WORKS:
  Makes a single API call to action=categorytree — fast, one round-trip,
  but returns pre-rendered HTML that requires parsing. Subcategories are
  indented with ├─ and grouped under their parent marked with 📂.

  For a more data-rich alternative (structured JSON with page IDs,
  namespaces, sort keys), use list=categorymembers recursively via the
  Wikimedia Action API instead. That approach trades more API calls for
  clean JSON at the cost of N round-trips for depth N.
EOF
  exit 0
}

CATEGORY="${1:-}"
DEPTH="${2:-2}"
MODE="${3:-categories}"
LANG="${4:-en}"

if [ -z "$CATEGORY" ]; then
  usage
fi

API="https://${LANG}.wikipedia.org/w/api.php"

echo "🔍 Category tree for: $CATEGORY"
echo "   Mode: $MODE, Depth: $DEPTH, Wiki: ${LANG}.wikipedia.org"
echo ""

response=$(curl -s "${API}" \
  --data-urlencode "action=categorytree" \
  --data-urlencode "category=${CATEGORY}" \
  --data-urlencode "options=$(printf '{"mode":"%s","depth":%s}' "$MODE" "$DEPTH")" \
  --data-urlencode "format=json" \
  -H "User-Agent: WikipediaCategoriesSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills) CategoryExplorer"
)

if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
  echo "❌ API Error:"
  echo "$response" | jq -r '.error.info // "Unknown error"'
  exit 1
fi

echo "$response" | jq -r '.categorytree["*"] // empty' | python3 -c '
import sys, re
from html import unescape

html = sys.stdin.read().strip()
if not html:
    print("  (no results)")
    sys.exit(0)

# Track ALL div openings/closings with a stack.
# Only CategoryTreeSection counts for display depth.
stack = []
output = []
i = 0
while i < len(html):
    m = re.match(r"<div\s+class=\"([^\"]*)\"[^>]*>", html[i:])
    if m:
        stack.append(m.group(1))
        i += m.end()
        continue

    m = re.match(r"<div[^>]*>", html[i:])
    if m:
        stack.append("")
        i += m.end()
        continue

    m = re.match(r"</div>", html[i:])
    if m:
        if stack:
            stack.pop()
        i += m.end()
        continue

    m = re.match(r"<a[^>]*>([^<]+)</a>", html[i:])
    if m:
        section_depth = sum(1 for cls in stack if cls == "CategoryTreeSection")
        if section_depth >= 1:
            name = unescape(m.group(1)).strip()
            output.append((section_depth, name))
        i += m.end()
        continue

    i += 1

if not output:
    print("  (no results)")
else:
    for d, name in output:
        if d == 1:
            print(f"  📂 {name}")
        else:
            indent = "  " * (d - 2)
            print(f"{indent}  ├─ {name}")
'
