#!/usr/bin/env bash
# Wikimedia API Connectivity Test
# Usage: ./test-api.sh [user-agent-string]
# Tests 12+ endpoints across 6 API families.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

UA="${1:-WikimediaApiTest/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; test@wikimedia.org) SkillTest}"
PASS=0
FAIL=0

echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Wikimedia API Connectivity Test${NC}"
echo -e "${CYAN}  User-Agent: ${UA}${NC}"
echo -e "${CYAN}  $(date)${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo ""

# Commons Analytics — use an allow-listed category for tests
# See: https://gitlab.wikimedia.org/repos/data-engineering/airflow-dags/-/blob/main/main/dags/commons/commons_category_allow_list.tsv
COMMONS_CATEGORY="Smithsonian_American_Art_Museum"

TMPDIR=$(mktemp -d /tmp/wikimedia-api-test.XXXXXX)
trap 'rm -rf "$TMPDIR"' EXIT

# ──────────────────────────────────────────────
# Shared response checker
# ──────────────────────────────────────────────
_check_response() {
    local name="$1"
    local outfile="$2"
    local expected_field="$3"

    local http_code
    http_code=$(tail -1 "$outfile")
    sed '$d' "$outfile" > "${outfile}.body"
    local body_file="${outfile}.body"

    # 404 with structured JSON = endpoint exists, no data for params
    if [[ "$http_code" == "404" ]]; then
        if grep -q '"detail"' "${body_file}" 2>/dev/null; then
            echo -e "${YELLOW}⚠️  No Data${NC} (HTTP 404 — endpoint exists, no data for parameters)"
            PASS=$((PASS + 1))
            return
        fi
    fi

    if [[ "$http_code" == "200" ]]; then
        if grep -q "${expected_field}" "${body_file}" 2>/dev/null; then
            echo -e "${GREEN}✅ OK${NC} (HTTP $http_code)"
            PASS=$((PASS + 1))
        else
            echo -e "${YELLOW}⚠️  Partial${NC} (HTTP $http_code — response received, missing expected content)"
            PASS=$((PASS + 1))
        fi
    elif [[ "$http_code" == "403" ]]; then
        echo -e "${RED}❌ BLOCKED${NC} (HTTP 403 — User-Agent rejected)"
        FAIL=$((FAIL + 1))
    elif [[ "$http_code" == "429" ]]; then
        echo -e "${YELLOW}⚠️  RATE LIMITED${NC} (HTTP 429)"
        FAIL=$((FAIL + 1))
    else
        echo -e "${RED}❌ FAIL${NC} (HTTP $http_code)"
        FAIL=$((FAIL + 1))
    fi
}

# ──────────────────────────────────────────────
# Helper: test a GET endpoint
# ──────────────────────────────────────────────
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_field="$3"
    local curl_args="${4:-}"

    echo -ne "  Testing ${name}... "
    local outfile="${TMPDIR}/response.txt"
    curl -s -w "\n%{http_code}" \
        -H "User-Agent: ${UA}" \
        --max-time 15 \
        ${curl_args} \
        "${url}" > "$outfile" 2>&1 || true

    _check_response "$name" "$outfile" "$expected_field"
}

# ──────────────────────────────────────────────
# Helper: test a POST endpoint
# ──────────────────────────────────────────────
test_post_endpoint() {
    local name="$1"
    local url="$2"
    local data="$3"
    local expected_field="$4"

    echo -ne "  Testing ${name}... "
    local outfile="${TMPDIR}/response.txt"
    curl -s -X POST -w "\n%{http_code}" \
        -H "User-Agent: ${UA}" \
        -H "Content-Type: application/json" \
        -d "${data}" \
        --max-time 15 \
        "${url}" > "$outfile" 2>&1 || true

    _check_response "$name" "$outfile" "$expected_field"
}

# ══════════════════════════════════════════════
# 1. Action API
# ══════════════════════════════════════════════
echo -e "${CYAN}📡 Core APIs (Action API)${NC}"
test_endpoint \
    "Action API (siteinfo)" \
    "https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&format=json" \
    '"sitename"'

test_endpoint \
    "Action API (search)" \
    "https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Albert%20Einstein&format=json&srlimit=1" \
    '"search"'

test_endpoint \
    "Action API (page content)" \
    "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=true&explaintext=true&titles=Python%20(programming%20language)&format=json" \
    '"extract"'

# ══════════════════════════════════════════════
# 2. REST API
# ══════════════════════════════════════════════
echo ""
echo -e "${CYAN}🌐 REST APIs${NC}"
test_endpoint \
    "REST API (page summary)" \
    "https://en.wikipedia.org/api/rest_v1/page/summary/Albert_Einstein" \
    '"title"'

test_endpoint \
    "REST API (page summary — second test)" \
    "https://en.wikipedia.org/api/rest_v1/page/summary/Albert_Einstein" \
    '"title"'

test_endpoint \
    "RESTBase (mobile-html)" \
    "https://en.wikipedia.org/api/rest_v1/page/mobile-html/Albert_Einstein" \
    "Albert Einstein" \
    "-L"

# ══════════════════════════════════════════════
# 3. SPARQL / Wikidata
# ══════════════════════════════════════════════
echo ""
echo -e "${CYAN}🔗 SPARQL / Wikidata${NC}"
test_endpoint \
    "Wikidata Query (SPARQL)" \
    'https://query.wikidata.org/sparql?format=json&query=SELECT%20*%20WHERE%20%7B%20BIND(%22hello%22%20AS%20%3Fgreeting)%20%7D' \
    '"greeting"'

test_endpoint \
    "Wikidata Entity Lookup (Q937)" \
    "https://www.wikidata.org/wiki/Special:EntityData/Q937.json" \
    '"Q937"'

# ══════════════════════════════════════════════
# 4. Pageviews API
# ══════════════════════════════════════════════
echo ""
echo -e "${CYAN}📊 Pageviews API${NC}"
pv_date=$(date -v-3d +%Y/%m/%d 2>/dev/null || date -d '3 days ago' +%Y/%m/%d 2>/dev/null || echo "2026/05/20")
test_endpoint \
    "Pageviews (top articles)" \
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/${pv_date}" \
    '"articles"'

# ══════════════════════════════════════════════
# 5. Commons Analytics API
# ══════════════════════════════════════════════
echo ""
echo -e "${CYAN}🖼️  Commons Analytics API${NC}"

test_endpoint \
    "Commons: top wikis per category" \
    "https://wikimedia.org/api/rest_v1/metrics/commons-analytics/top-wikis-per-category-monthly/${COMMONS_CATEGORY}/shallow/2025/01" \
    '"items"'

test_endpoint \
    "Commons: category metrics snapshot" \
    "https://wikimedia.org/api/rest_v1/metrics/commons-analytics/category-metrics-snapshot/${COMMONS_CATEGORY}/20250101/20250301" \
    '"items"'

test_endpoint \
    "Commons: top edited categories (shallow)" \
    "https://wikimedia.org/api/rest_v1/metrics/commons-analytics/top-edited-categories-monthly/shallow/all-edit-types/2025/06" \
    '"items"'

# ══════════════════════════════════════════════
# 6. Lift Wing ML API
# ══════════════════════════════════════════════
echo ""
echo -e "${CYAN}🧠 Lift Wing ML API${NC}"

test_post_endpoint \
    "Lift Wing: revert risk (language-agnostic)" \
    "https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-language-agnostic:predict" \
    '{"rev_id": 1355663707, "lang": "en"}' \
    '"prediction"'

test_post_endpoint \
    "Lift Wing: article quality (enwiki)" \
    "https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-articlequality:predict" \
    '{"rev_id": 1355663707}' \
    '"FA"'

# ══════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════
echo ""
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}Passed: ${PASS}${NC}"
echo -e "  ${RED}Failed: ${FAIL}${NC}"
echo -e "  Total:  $((PASS + FAIL))"
if [[ "$FAIL" -eq 0 ]]; then
    echo -e "  ${GREEN}Result: All APIs reachable ✅${NC}"
else
    echo -e "  ${RED}Result: Some endpoints failed ❌${NC}"
fi
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
