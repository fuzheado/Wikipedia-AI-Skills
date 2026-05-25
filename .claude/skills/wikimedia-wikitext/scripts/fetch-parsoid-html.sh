#!/usr/bin/env bash
# Fetch a Wikipedia page as clean Parsoid HTML via the REST API
# Usage: ./fetch-parsoid-html.sh <page_title> [output_file]

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PAGE="${1:-}"
OUTPUT="${2:-}"

if [ -z "$PAGE" ]; then
    echo -e "${RED}❌ No page title provided${NC}"
    echo "   Usage: ./fetch-parsoid-html.sh <page_title> [output_file]"
    echo ""
    echo "   Examples:"
    echo "     ./fetch-parsoid-html.sh 'Python (programming language)'"
    echo "     ./fetch-parsoid-html.sh 'Albert Einstein' albert.html"
    exit 1
fi

# Check for curl
if ! command -v curl &>/dev/null; then
    echo -e "${RED}❌ curl not found. Please install curl.${NC}"
    exit 1
fi

# Use default User-Agent if none set
UA="${WIKI_UA:-WikitextSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)}"

# MediaWiki REST API expects underscores for spaces in the URL path
ENCODED_PAGE="${PAGE// /_}"

URL="https://en.wikipedia.org/w/rest.php/v1/page/${ENCODED_PAGE}/html"

echo -e "${CYAN}📄 Fetching Parsoid HTML for: ${PAGE}${NC}"
echo -e "   URL: ${URL}"
echo ""

# Create temp file for response
TMPFILE=$(mktemp)
HTTP_CODE=$(curl -s -o "$TMPFILE" -w "%{http_code}" \
    -H "User-Agent: ${UA}" \
    -H "Accept: text/html; charset=utf-8; profile=\"https://www.mediawiki.org/wiki/Specs/HTML/2.1.0\"" \
    "$URL" 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    SIZE=$(wc -c < "$TMPFILE")
    echo -e "${GREEN}✅ Success (HTTP 200) — ${SIZE} bytes retrieved${NC}"
    echo ""

    if [ -n "$OUTPUT" ]; then
        mv "$TMPFILE" "$OUTPUT"
        echo -e "   Saved to: ${OUTPUT}"
    else
        # Print first 50 lines as preview
        echo -e "${YELLOW}📋 Preview (first 30 lines):${NC}"
        head -30 "$TMPFILE"
        echo ""
        echo -e "${YELLOW}... (full output in temp file: ${TMPFILE})${NC}"
    fi

    # Print table extraction hint
    echo ""
    echo -e "${CYAN}💡 Tip:${NC} To extract tables, pipe this HTML to a Python script:"
    echo "   python3 -c \"import pandas as pd; import sys;"
    echo "     tables = pd.read_html(sys.stdin); print(f'Found {len(tables)} tables')\" < ${OUTPUT:-$TMPFILE}"
else
    echo -e "${RED}❌ Error (HTTP ${HTTP_CODE})${NC}"
    cat "$TMPFILE" 2>/dev/null || true
    rm -f "$TMPFILE"
    exit 1
fi
