#!/usr/bin/env bash
# category-tree.sh — Explore a Wikipedia category hierarchy from the CLI
#
# Usage:
#   ./category-tree.sh Physics                  # Subcategories, 2 levels deep
#   ./category-tree.sh Physics 3                # Subcategories, 3 levels deep
#   ./category-tree.sh Physics 2 pages          # Articles + subcategories
#   ./category-tree.sh Physics 1 all            # Everything (pages, subcats, files)
#   ./category-tree.sh Physics 1 parents        # Go upward (parent categories)
#   ./category-tree.sh Physics 2 categories en  # Specify language
#
# Requires: curl, jq, python3

set -euo pipefail

CATEGORY="${1:?Usage: $0 <category> [depth=2] [mode=categories|pages|all|parents] [lang=en]}"
DEPTH="${2:-2}"
MODE="${3:-categories}"
LANG="${4:-en}"
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
    # Match a div with class attribute
    m = re.match(r"<div\s+class=\"([^\"]*)\"[^>]*>", html[i:])
    if m:
        stack.append(m.group(1))
        i += m.end()
        continue

    # Match a div without class attribute (other attributes ok)
    m = re.match(r"<div[^>]*>", html[i:])
    if m:
        stack.append("")
        i += m.end()
        continue

    # Closing div
    m = re.match(r"</div>", html[i:])
    if m:
        if stack:
            stack.pop()
        i += m.end()
        continue

    # Links — record if we are inside at least one CategoryTreeSection
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
