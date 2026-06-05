#!/usr/bin/env bash
# Extract all citation URLs from a Wikipedia page and check for dead links.
#
# Usage:
#   ./check-dead-links.sh Albert_Einstein
#   ./check-dead-links.sh "Albert Einstein"  (spaces auto-converted)
#   ./check-dead-links.sh Albert_Einstein --lang fr
#   ./check-dead-links.sh Albert_Einstein --verbose
#   ./check-dead-links.sh Albert_Einstein --parallel 10

set -euo pipefail

if [[ $# -eq 0 ]]; then
    echo "🔍 check-dead-links.sh — Extract URLs from a Wikipedia page and check each for dead links"
    echo ""
    echo "Usage: $0 <page_title> [--lang LANG] [--verbose] [--parallel N]"
    echo ""
    echo "Examples:"
    echo "  $0 Albert_Einstein"
    echo "  $0 'Albert Einstein' --lang fr"
    echo "  $0 Albert_Einstein --parallel 20"
    exit 1
fi

PAGE=""
LANG="en"
VERBOSE=false
PARALLEL=5

while [[ $# -gt 0 ]]; do
    case "$1" in
        --lang) LANG="$2"; shift 2 ;;
        --verbose) VERBOSE=true; shift ;;
        --parallel) PARALLEL="$2"; shift 2 ;;
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
echo "   Parallel checks: $PARALLEL"
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

# Extract all URLs
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

# ── Parallel URL checking with xargs ────────────────────────────────────────
# Each URL check is a simple function that prints a line of results.
# xargs -P handles concurrency, and we collect output.

WORKDIR=$(mktemp -d)

# Create a file with one line per URL check command
# Each job writes its result to workdir/result-{idx}.txt
CHECK_CMD_FILE="$WORKDIR/commands.txt"
> "$CHECK_CMD_FILE"

idx=0
while IFS= read -r url; do
    [[ -z "$url" ]] && continue
    idx=$((idx + 1))
    echo "$idx|$url" >> "$CHECK_CMD_FILE"
done < "$TMPFILE"

# The parallel worker: reads from stdin, processes one URL
worker() {
    local line="$1"
    local idx="${line%%|*}"
    local url="${line#*|}"
    local result_file="$WORKDIR/result-$idx.txt"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
      -H "User-Agent: $UA" "$url" 2>/dev/null || echo "000")

    {
        echo "url=$url"
        echo "http_code=$HTTP_CODE"
        if [[ "$HTTP_CODE" == "000" ]]; then
            echo "status=error"
        elif [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "304" ]]; then
            echo "status=live"
        elif [[ "$HTTP_CODE" -ge 301 && "$HTTP_CODE" -le 308 ]]; then
            echo "status=redirect"
        else
            echo "status=dead"
            ARCHIVE_URL=$(curl -s "https://archive.org/wayback/available?url=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$url'))")" \
              -H "User-Agent: $UA" 2>/dev/null | python3 -c "
import sys, json
d = json.load(sys.stdin)
snap = d.get('archived_snapshots', {}).get('closest', {})
if snap:
    print(snap.get('url', ''))
else:
    print('')
")
            echo "archive_url=$ARCHIVE_URL"
        fi
    } > "$result_file"
}
export -f worker
export UA WORKDIR

# Run workers in parallel using xargs
echo "   Launching $PARALLEL parallel workers..."
cat "$CHECK_CMD_FILE" | xargs -P "$PARALLEL" -I {} bash -c 'worker "$@"' _ {} 2>/dev/null

# ── Collect and display results ────────────────────────────────────────────
LIVE=0
DEAD=0
REDIRECTS=0
ARCHIVED=0
ERRORS=0

echo ""
for idx in $(seq 1 "$COUNT"); do
    result_file="$WORKDIR/result-$idx.txt"
    URL=$(sed -n "${idx}p" "$TMPFILE")
    DISPLAY_URL="${URL:0:90}"

    if [[ ! -f "$result_file" ]]; then
        echo "  [$idx/$COUNT] $DISPLAY_URL"
        echo "    ⚠  No result"
        ERRORS=$((ERRORS + 1))
        continue
    fi

    STATUS=""
    HTTP_CODE=""
    ARCHIVE_URL=""
    while IFS='=' read -r key value; do
        case "$key" in
            status) STATUS="$value" ;;
            http_code) HTTP_CODE="$value" ;;
            archive_url) ARCHIVE_URL="$value" ;;
        esac
    done < "$result_file"

    case "$STATUS" in
        live)
            echo "  [$idx/$COUNT] $DISPLAY_URL"
            echo "    ✅ $HTTP_CODE"
            LIVE=$((LIVE + 1)) ;;
        redirect)
            echo "  [$idx/$COUNT] $DISPLAY_URL"
            echo "    🔀 $HTTP_CODE (redirect)"
            REDIRECTS=$((REDIRECTS + 1)) ;;
        dead)
            echo "  [$idx/$COUNT] $DISPLAY_URL"
            echo "    ❌ $HTTP_CODE (dead)"
            DEAD=$((DEAD + 1))
            if [[ -n "$ARCHIVE_URL" ]]; then
                echo "    📦 Archived at: $ARCHIVE_URL"
                ARCHIVED=$((ARCHIVED + 1))
            else
                echo "    📦 No archive found"
            fi ;;
        error)
            echo "  [$idx/$COUNT] $DISPLAY_URL"
            echo "    ⚠  Connection error"
            ERRORS=$((ERRORS + 1)) ;;
    esac
done

rm -rf "$WORKDIR" "$TMPFILE"

echo ""
echo "═══════════════════════════════════════"
echo "  Results for $PAGE"
echo "  Total URLs checked: $COUNT"
echo "  ✅ Live:            $LIVE"
echo "  🔀 Redirects:       $REDIRECTS"
echo "  ❌ Dead:            $DEAD"
echo "  📦 Archived:        $ARCHIVED/$DEAD dead URLs have archives"
echo "  ⚠  Errors:          $ERRORS"
echo "═══════════════════════════════════════"
