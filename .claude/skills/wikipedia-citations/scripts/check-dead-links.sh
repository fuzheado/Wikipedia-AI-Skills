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

PAGE=$(echo "$PAGE" | tr ' ' '_')
DOMAIN="${LANG}.wikipedia.org"
UA="DeadLinkCheck/1.0 (user@example.com) ContentGapResearch"

echo "🔍 Scanning citations on: $PAGE ($LANG)"
echo

WIKITEXT=$(curl -s "https://${DOMAIN}/w/api.php?action=parse&page=${PAGE}&prop=wikitext&format=json" \
  -H "User-Agent: $UA" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('parse', {}).get('wikitext', {}).get('*', ''))
")

if [[ -z "$WIKITEXT" ]]; then
    echo "❌ Could not fetch page content. Check the page title."
    exit 1
fi

# Extract all URLs, write to temp file to avoid subshell bug
TMPFILE=$(mktemp)
echo "$WIKITEXT" | python3 -c "
import sys, re
wikitext = sys.stdin.read()
urls = set()
for m in re.finditer(r'\|?\s*url\s*=\s*([^|\n}]+)', wikitext, re.IGNORECASE):
    url = m.group(1).strip()
    if url.startswith('http'):
        urls.add(url)
for m in re.finditer(r'<ref>(https?://[^\s<]+)</ref>', wikitext):
    urls.add(m.group(1))
for url in sorted(urls):
    print(url)
" > "$TMPFILE"

COUNT=$(wc -l < "$TMPFILE" | tr -d ' ')
echo "📊 Found $COUNT unique citation URLs"
echo

if [[ "$COUNT" -eq 0 ]]; then
    echo "No citation URLs to check."
    rm -f "$TMPFILE"
    exit 0
fi

# Use a temp file for results to avoid subshell pipe bug
RESULTSFILE=$(mktemp)
echo "0 0 0 0 0" > "$RESULTSFILE"  # live dead redirects archived errors

CHECKED=0
while IFS= read -r url; do
    [[ -z "$url" ]] && continue
    CHECKED=$((CHECKED + 1))

    # Truncate URL for display
    DISPLAY_URL="${url:0:90}"
    echo "[$CHECKED/$COUNT] $DISPLAY_URL"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
      -H "User-Agent: $UA" "$url" 2>/dev/null || echo "000")

    read -r LIVE DEAD REDIRECTS ARCHIVED ERRORS < "$RESULTSFILE"

    if [[ "$HTTP_CODE" == "000" ]]; then
        echo "  ⚠  Connection error"
        ERRORS=$((ERRORS + 1))
    elif [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "304" ]]; then
        echo "  ✅ $HTTP_CODE"
        LIVE=$((LIVE + 1))
    elif [[ "$HTTP_CODE" == "301" || "$HTTP_CODE" == "302" || "$HTTP_CODE" == "303" || "$HTTP_CODE" == "307" || "$HTTP_CODE" == "308" ]]; then
        echo "  🔀 $HTTP_CODE (redirect)"
        REDIRECTS=$((REDIRECTS + 1))
    else
        echo "  ❌ $HTTP_CODE (dead)"
        DEAD=$((DEAD + 1))

        ARCHIVE_CHECK=$(curl -s "https://archive.org/wayback/available?url=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$url'))")" \
          -H "User-Agent: $UA" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
snap = d.get('archived_snapshots', {}).get('closest', {})
if snap:
    print(f\"Archive: {snap.get('url', '')}\")
else:
    print('No archive')
")
        echo "  📦 $ARCHIVE_CHECK"
        if [[ "$ARCHIVE_CHECK" != "No archive" ]]; then
            ARCHIVED=$((ARCHIVED + 1))
        fi
    fi

    echo "$LIVE $DEAD $REDIRECTS $ARCHIVED $ERRORS" > "$RESULTSFILE"
done < "$TMPFILE"

read -r LIVE DEAD REDIRECTS ARCHIVED ERRORS < "$RESULTSFILE"
rm -f "$TMPFILE" "$RESULTSFILE"

echo
echo "═══════════════════════════════════════"
echo "  Results for $PAGE"
echo "  Total URLs checked: $COUNT"
echo "  ✅ Live:            $LIVE"
echo "  🔀 Redirects:       $REDIRECTS"
echo "  ❌ Dead:            $DEAD"
echo "  📦 Archived:        $ARCHIVED/$DEAD dead URLs have archives"
echo "  ⚠  Errors:          $ERRORS"
echo "═══════════════════════════════════════"
