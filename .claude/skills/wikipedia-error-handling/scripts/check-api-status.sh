#!/usr/bin/env bash
# Check if a Wikimedia API endpoint is reachable and responding correctly.
#
# Usage:
#   ./check-api-status.sh                      # Check all known endpoints
#   ./check-api-status.sh --endpoint pageviews  # Check a specific endpoint
#   ./check-api-status.sh --help               # Show this help
#
# Endpoints:
#   enwiki       English Wikipedia Action API
#   commons      Wikimedia Commons Action API
#   wikidata     Wikidata Action API
#   rest         English Wikipedia REST API
#   pageviews    Wikimedia Pageviews API
#   sparql       Wikidata SPARQL endpoint
#   liftwing     Lift Wing ML inference API
#   eventstreams Wikimedia EventStreams
#   toolforge    Toolforge (cdnjs mirror)

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}${1}${NC}"; }
ok()    { echo -e "${GREEN}  ✓ ${1}${NC}"; }
warn()  { echo -e "${YELLOW}  ⚠ ${1}${NC}"; }
err()   { echo -e "${RED}  ✗ ${1}${NC}"; }

UA="${WIKI_UA:-ErrorHandlingSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)}"
TARGET=""
TIMEOUT=10

# ── Parse arguments ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --endpoint) TARGET="$2"; shift 2 ;;
        --help|-h) head -30 "$0" | grep -E '^#' | sed 's/^# \?//'; exit 0 ;;
        *) echo -e "${RED}❌ Unknown: $1${NC}"; exit 1 ;;
    esac
done

# ── Define endpoints ─────────────────────────────────────────────────────────
check_endpoint() {
    local name="$1" url="$2" method="${3:-GET}" data="${4:-}" label="${5:-$name}"

    if [ -n "$TARGET" ] && [ "$TARGET" != "$name" ]; then
        return
    fi

    echo -e "${BOLD}${label}${NC}"
    echo "  URL: $url"

    local start_time end_time status_code response
    start_time=$(date +%s%N)

    if [ "$method" = "POST" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" \
            -H "User-Agent: ${UA}" -H "Content-Type: application/json" \
            -d "$data" "$url" 2>/dev/null || echo "CURL_FAILED")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" \
            -H "User-Agent: ${UA}" "$url" 2>/dev/null || echo "CURL_FAILED")
    fi

    end_time=$(date +%s%N)
    local elapsed_ms=$(( (end_time - start_time) / 1000000 ))

    case "$response" in
        200|201) ok "HTTP $response (${elapsed_ms}ms)" ;;
        301|302) warn "HTTP $response — redirected (${elapsed_ms}ms)" ;;
        403)     err "HTTP $response — Forbidden (check User-Agent)" ;;
        429)     err "HTTP $response — Rate limited" ;;
        CURL_FAILED) err "Connection failed (timeout: ${TIMEOUT}s)" ;;
        *)       err "HTTP $response (${elapsed_ms}ms)" ;;
    esac
    echo
}

# ── Run checks ───────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}Wikimedia API Status Check${NC}"
echo -e "${CYAN}$(date)${NC}\n"

check_endpoint "enwiki" \
    "https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=general&format=json" \
    GET "" "🔹 English Wikipedia (Action API)"

check_endpoint "commons" \
    "https://commons.wikimedia.org/w/api.php?action=query&meta=siteinfo&siprop=general&format=json" \
    GET "" "🔹 Wikimedia Commons (Action API)"

check_endpoint "wikidata" \
    "https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q937&props=labels&format=json" \
    GET "" "🔹 Wikidata (wbgetentities)"

check_endpoint "rest" \
    "https://en.wikipedia.org/api/rest_v1/page/summary/Albert_Einstein" \
    GET "" "🔹 English Wikipedia (REST API)"

check_endpoint "pageviews" \
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/Albert_Einstein/daily/20250101/20250131" \
    GET "" "🔹 Pageviews API"

check_endpoint "sparql" \
    "https://query.wikidata.org/sparql?format=json&query=SELECT%20?item%20?itemLabel%20WHERE%20%7B%20wd:Q937%20wdt:P106%20?item.%20SERVICE%20wikibase:label%20%7B%20bd:serviceParam%20wikibase:language%20%22en%22.%20%7D%20%7D" \
    GET "" "🔹 Wikidata SPARQL"

check_endpoint "liftwing" \
    "https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-language-agnostic:predict" \
    POST '{"rev_id": 123456789, "lang": "en"}' "🔹 Lift Wing ML (revertrisk)"

check_endpoint "eventstreams" \
    "https://stream.wikimedia.org/v2/stream/recentchange" \
    GET "" "🔹 EventStreams (recentchange)"

check_endpoint "toolforge" \
    "https://tools-static.wmflabs.org/cdnjs/ajax/libs/jquery/3.6.0/jquery.min.js" \
    GET "" "🔹 Toolforge CDN"

if [ -z "$TARGET" ]; then
    echo -e "\n${BOLD}Done.${NC}  Use --endpoint <name> to check a single endpoint."
fi
