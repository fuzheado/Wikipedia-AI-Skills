#!/usr/bin/env bash
# =============================================================================
# ws-text-extract.sh — Extract OCR text from a Wikisource Page: page
#
# Fetches the raw text layer from a Wikisource Page: namespace page,
# stripping header/footer templates to return just the proofread text.
#
# Usage:
#   ./ws-text-extract.sh <lang> <page_title>
#
# Examples:
#   ./ws-text-extract.sh en "Page:Pride and Prejudice/1"
#   ./ws-text-extract.sh fr "Page:Les Misérables/5"
#   ./ws-text-extract.sh --help
# =============================================================================

set -euo pipefail

LANG="${1:-}"
PAGE="${2:-}"

if [ -z "$LANG" ] || [ "$LANG" = "--help" ] || [ -z "$PAGE" ]; then
    echo "Usage: $0 <lang> <page_title>"
    echo ""
    echo "Extract OCR text from a Wikisource Page: page."
    echo ""
    echo "Arguments:"
    echo "  lang          Language code (en, fr, de, etc.)"
    echo "  page_title    Title of the Page: page"
    echo ""
    echo "Examples:"
    echo "  $0 en \"Page:Pride and Prejudice/1\""
    echo "  $0 fr \"Page:Les Misérables/5\""
    exit 0
fi

API="https://${LANG}.wikisource.org/w/api.php"
UA="WsTextExtract/1.0 (https://example.com; user@example.com)"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Wikisource Text Extraction                                  ║"
echo "║  Page: $PAGE"
echo "║  Wiki: ${LANG}.wikisource.org"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Fetch the wikitext
echo "Fetching page wikitext..."
WIKITEXT=$(curl -s -G "$API" \
    --data-urlencode "action=parse" \
    --data-urlencode "page=$PAGE" \
    --data-urlencode "prop=wikitext" \
    --data-urlencode "format=json" \
    -H "User-Agent: $UA" \
    | python3 -c "
import sys, json, re

data = json.load(sys.stdin)

if 'error' in data:
    print(f'ERROR: {data[\"error\"][\"info\"]}')
    sys.exit(1)

if 'parse' not in data:
    print(f'ERROR: Page not found: {\"$PAGE\"}')
    sys.exit(1)

wt = data['parse']['wikitext']['*']

# Strip header/footer templates
text = re.sub(r'\{\{header[^}]*\}\}', '', wt)
text = re.sub(r'\{\{footer[^}]*\}\}', '', wt)
text = re.sub(r'\{\{nop\}\}', '', text)
text = re.sub(r'\{\{c\|[^}]*\}\}', '', text)

# Strip other common formatting templates
text = re.sub(r'\{\{larger\|[^}]*\}\}', '', text)
text = re.sub(r'\{\{smaller\|[^}]*\}\}', '', text)
text = re.sub(r'\{\{gap\}\}', ' ', text)

# Strip <pages> tags
text = re.sub(r'<pages[^>]*/>', '', text)

# Clean up whitespace
text = re.sub(r'\n{3,}', '\n\n', text)
text = text.strip()

print(f'TEXT_LENGTH: {len(text)}')
print('---CONTENT---')
print(text)
")

if [[ "$WIKITEXT" == ERROR:* ]]; then
    echo "❌ $WIKITEXT"
    exit 1
fi

echo "$WIKITEXT"
echo ""
echo "────────────────────────────────────────────"
echo "Done."
