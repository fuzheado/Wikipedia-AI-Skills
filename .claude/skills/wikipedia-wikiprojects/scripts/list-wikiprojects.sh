#!/usr/bin/env bash
# list-wikiprojects.sh — List active WikiProjects by category
# Usage:
#   ./list-wikiprojects.sh              # All WikiProjects
#   ./list-wikiprojects.sh active       # Active WikiProjects only
#   ./list-wikiprojects.sh science      # Science-related WikiProjects
set -euo pipefail

CATEGORY="${1:-}"
THIS_DIR="$(cd "$(dirname "$0")" && pwd)"

USER_AGENT="WikiProjectLister/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; tools@example.com)"

# Map friendly category names to Category: wiki pages
get_category() {
  case "$1" in
    active)
      echo "Active_WikiProjects"
      ;;
    science)
      echo "Science_WikiProjects"
      ;;
    history)
      echo "History_WikiProjects"
      ;;
    geography)
      echo "Geography_WikiProjects"
      ;;
    culture)
      echo "Culture_WikiProjects"
      ;;
    technology)
      echo "Technology_WikiProjects"
      ;;
    *)
      echo "WikiProjects"
      ;;
  esac
}

echo "=== WikiProjects ==="
if [ -n "$CATEGORY" ]; then
  CAT_TITLE="$(get_category "$CATEGORY")"
  echo "Category: $CATEGORY → $CAT_TITLE"
  echo ""
else
  CAT_TITLE="WikiProjects"
fi

# Fetch from Action API
curl -s -H "User-Agent: $USER_AGENT" \
  "https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:${CAT_TITLE}&cmtype=page&cmlimit=50&format=json" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
pages = data.get('query', {}).get('categorymembers', [])
for p in pages:
    title = p['title']
    # Only show pages with 'WikiProject' in title
    if 'WikiProject' in title:
        print(f'  {title}')
print(f'\nTotal: {len(pages)} results (max 50)')
"
