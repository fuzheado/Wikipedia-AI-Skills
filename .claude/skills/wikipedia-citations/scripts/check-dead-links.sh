#!/usr/bin/env bash
# Extract all citation URLs from a Wikipedia page and check for dead links.
#
# Usage:
#   ./check-dead-links.sh Albert_Einstein
#   ./check-dead-links.sh "Albert Einstein"  (spaces auto-converted)
#   ./check-dead-links.sh Albert_Einstein --lang fr
#   ./check-dead-links.sh Albert_Einstein --verbose

set -euo pipefail

if [[ $# -eq 0 ]]; then
    echo "🔍 check-dead-links.sh — Extract URLs from a Wikipedia page and check each for dead links"
    echo ""
    echo "Usage: $0 <page_title> [--lang LANG] [--verbose]"
    echo ""
    echo "Examples:"
    echo "  $0 Albert_Einstein"
    echo "  $0 'Albert Einstein' --lang fr"
    exit 1
fi

PAGE=""
LANG="en"
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --lang) LANG="$2"; shift 2 ;;
        --verbose) VERBOSE=true; shift ;;
        -*) echo "Unknown option: $1"; exit 1 ;;
        *)
            if [[ -z "$PAGE" ]]; then
                PAGE="$1"
            else
                echo "Unexpected argument: $1"
                exit 1
            fi
            shift ;;
    esac
done

# Convert spaces to underscores
PAGE=$(echo "$PAGE" | tr ' ' '_')
DOMAIN="${LANG}.wikipedia.org"
USER_AGENT="DeadLinkCheck/1.0 (user@example.com) ContentGapResearch"

echo "🔍 Scanning citations on: $PAGE ($LANG)"
echo

# Fetch page wikitext
WIKITEXT=$(curl -s "https://${DOMAIN}/w/api.php?action=parse&page=${PAGE}&prop=wikitext&format=json" \
  -H "User-Agent: $USER_AGENT" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('parse', {}).get('wikitext', {}).get('*', ''))
" 2>/dev/null)

if [[ -z "$WIKITEXT" ]]; then
    echo "❌ Could not fetch page content. Check the page title."
    exit 1
fi

# Extract all URLs from citation templates
URLS=$(echo "$WIKITEXT" | python3 -c "
import sys, re

wikitext = sys.stdin.read()

# Find all cite template URLs
urls = []
for m in re.finditer(r'\|?\s*url\s*=\s*([^|\n}]+)', wikitext, re.IGNORECASE):
    url = m.group(1).strip()
    if url.startswith('http'):
        urls.append(url)

# Find bare URLs in ref tags  
for m in re.finditer(r'<ref>(https?://[^\s<]+)</ref>', wikitext):
    urls.append(m.group(1))

for url in urls:
    print(url)
" 2>/dev/null | sort -u)

COUNT=$(echo "$URLS" | grep -c . || echo 0)
echo "📊 Found $COUNT unique citation URLs"
echo

if [[ "$COUNT" -eq 0 ]]; then
    echo "No citation URLs to check."
    exit 0
fi

LIVE=0
DEAD=0
ERRORS=0
ARCHIVED=0
CHECKED=0

echo "$URLS" | while IFS= read -r url; do
    [[ -z "$url" ]] && continue
    CHECKED=$((CHECKED + 1))

    if $VERBOSE; then
        echo "[$CHECKED/$COUNT] Checking: ${url:0:80}..."
    fi

    # Check HTTP status
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
      -H "User-Agent: $USER_AGENT" \
      "$url" 2>/dev/null || echo "000")

    if [[ "$HTTP_CODE" == "000" ]]; then
        echo "   ⚠  Connection error"
        ERRORS=$((ERRORS + 1))
    elif [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "304" ]]; then
        if $VERBOSE; then
            echo "   ✅ $HTTP_CODE"
        fi
        LIVE=$((LIVE + 1))
    elif [[ "$HTTP_CODE" == "301" || "$HTTP_CODE" == "302" ]]; then
        echo "   🔀 $HTTP_CODE (redirect)"
        LIVE=$((LIVE + 1))
    else
        echo "   ❌ $HTTP_CODE (dead)"
        DEAD=$((DEAD + 1))

        # Check Wayback Machine for archive
        ARCHIVE_CHECK=$(curl -s "https://archive.org/wayback/available?url=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$url'))")" \
          -H "User-Agent: $USER_AGENT" 2>/dev/null \
          | python3 -c "
import sys, json
d = json.load(sys.stdin)
snap = d.get('archived_snapshots', {}).get('closest', {})
if snap:
    print(f\"Archived at: {snap.get('url', '')}\")
else:
    print('No archive')
" 2>/dev/null)
        echo "   📦 $ARCHIVE_CHECK"
        if [[ "$ARCHIVE_CHECK" != "No archive" ]]; then
            ARCHIVED=$((ARCHIVED + 1))
        fi
    fi
done

echo
echo "═══════════════════════════════════════"
echo "  Results for $PAGE"
echo "  Total URLs checked: $COUNT"
echo "  ✅ Live: $LIVE"
echo "  ❌ Dead: $DEAD"
echo "  📦 Archived: $ARCHIVED"
echo "  ⚠  Errors: $ERRORS"
echo "═══════════════════════════════════════"
