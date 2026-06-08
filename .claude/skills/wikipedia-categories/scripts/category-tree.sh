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
# Requires: curl, jq

set -euo pipefail

CATEGORY="${1:?Usage: $0 <category> [depth=2] [mode=categories|pages|all|parents] [lang=en]}"
DEPTH="${2:-2}"
MODE="${3:-categories}"
LANG="${4:-en}"
API="https://${LANG}.wikipedia.org/w/api.php"

echo "🔍 Category tree for: $CATEGORY"
echo "   Mode: $MODE, Depth: $DEPTH, Wiki: ${LANG}.wikipedia.org"
echo ""

# Build the options JSON
OPTIONS=$(cat <<EOF
{"mode":"${MODE}","depth":${DEPTH}}
EOF
)

# Fetch category tree
response=$(curl -s "${API}" \
  --data-urlencode "action=categorytree" \
  --data-urlencode "category=${CATEGORY}" \
  --data-urlencode "options=${OPTIONS}" \
  --data-urlencode "format=json" \
  -H "User-Agent: WikipediaCategoriesSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills) CategoryExplorer"
)

# Check for errors
if echo "$response" | jq -e '.error' > /dev/null 2>&1; then
  echo "❌ API Error:"
  echo "$response" | jq -r '.error.info // "Unknown error"'
  exit 1
fi

# Extract the category tree HTML from the response
html=$(echo "$response" | jq -r '.categorytree // empty')

if [ -z "$html" ]; then
  echo "ℹ️  No results or empty tree."
  exit 0
fi

# Parse HTML list structure into indented text
# The CategoryTree extension returns <ul><li> elements
echo "$html" | python3 -c "
import sys, html as htmlmod, re

html = sys.stdin.read()

# Strip outer <ul> and </ul>
html = re.sub(r'^<ul>|</ul>\s*$', '', html, flags=re.DOTALL).strip()

def parse_li(text, indent=0):
    results = []
    # Match <li>...</li> blocks
    pattern = r'<li>(.*?)</li>'
    for match in re.finditer(pattern, text, re.DOTALL):
        content = match.group(1)
        # Remove <span> tags but keep text
        content_clean = re.sub(r'<span[^>]*>|</span>', '', content)
        # Decode HTML entities
        text_content = htmlmod.unescape(content_clean)
        # Check for nested <ul>
        ul_match = re.search(r'(.*?)<ul>(.*?)</ul>(.*)', text_content, re.DOTALL)
        if ul_match:
            before = ul_match.group(1).strip()
            nested = ul_match.group(2).strip()
            after = ul_match.group(3).strip()
            combined = before
            if after:
                combined += ' ' + after
            results.append((indent, combined.strip()))
            results.extend(parse_li(nested, indent + 1))
        else:
            results.append((indent, text_content.strip()))
    return results

items = parse_li(html)
for indent, name in items:
    prefix = '  ' * indent + '├─ ' if indent > 0 else ''
    if indent > 0:
        print(f\"{prefix}{name}\")
    else:
        print(f\"  📂 {name}\")
"
