#!/usr/bin/env bash
# Expand a bare URL into a {{cite web}} template.
# Fetches the page title from the URL's HTML <title> tag.
#
# Usage:
#   ./expand-bare-url.sh https://example.com/article
#   ./expand-bare-url.sh https://en.wikipedia.org/wiki/Main_Page
#   ./expand-bare-url.sh "https://example.com/article" "Article Title" "Example News"

set -euo pipefail

URL="${1:?"Usage: $0 <url> [title] [website]"}"

USER_AGENT="ExpandBareURL/1.0 (user@example.com) ContentGapResearch"

# Try to fetch the page title from the URL
if [[ $# -ge 2 ]]; then
    TITLE="$2"
else
    echo "→ Fetching page title from $URL ..." >&2
    TITLE=$(curl -sL -H "User-Agent: $USER_AGENT" "$URL" \
      | grep -oP '<title[^>]*>\K[^<]+' 2>/dev/null | head -1 | sed 's/ - Wikipedia//' | sed 's/^ *//;s/ *$//')
    TITLE="${TITLE:-Untitled}"
fi

if [[ $# -ge 3 ]]; then
    WEBSITE="$3"
else
    # Extract domain name as website
    WEBSITE=$(echo "$URL" | sed -E 's|https?://||; s|www\.||; s|/.*||')
fi

ACCESS_DATE=$(date "+%d %B %Y")

echo "{{cite web"
echo " |url=$URL"
echo " |title=$TITLE"
echo " |website=$WEBSITE"
echo " |access-date=$ACCESS_DATE"
echo "}}"
