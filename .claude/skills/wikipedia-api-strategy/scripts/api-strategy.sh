#!/usr/bin/env bash
# Recommend the best Wikimedia API or tool for a given task.
#
# Usage:
#   ./api-strategy.sh                       # Show interactive menu
#   ./api-strategy.sh "pageviews 50 articles in category"  # Describe your task
#   ./api-strategy.sh --task "query"        # Explicit task flag
#   ./api-strategy.sh --compare API SQL     # Compare approaches
#   ./api-strategy.sh --help                # Show this help
#
# Task categories (auto-detected from keywords):
#   read, batch, analytics, realtime, edit, graph, patrol

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

TASK=""

# ── Parse arguments ──────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --task|-t) TASK="$2"; shift 2 ;;
        --compare) shift; echo -e "${BOLD}Approach comparison${NC}"; echo; compare_approaches "$@"; exit 0 ;;
        --help|-h) head -30 "$0" | grep -E '^#' | sed 's/^# \?//'; exit 0 ;;
        *) TASK="$*"; break ;;
    esac
done

# ── Comparison function ──────────────────────────────────────────────────────
compare_approaches() {
    local a1="${1:-}" a2="${2:-}"
    if [ -z "$a1" ] || [ -z "$a2" ]; then
        echo -e "${RED}Usage: --compare <approach1> <approach2>${NC}"
        echo "  Approaches: api, rest, sparql, sql, eventstreams, pywikibot"
        exit 1
    fi

    declare -A LABELS=(
        [api]="Action API" [rest]="REST API" [sparql]="SPARQL"
        [sql]="SQL Replicas" [eventstreams]="EventStreams" [pywikibot]="Pywikibot"
    )

    echo -e "  ${BOLD}${LABELS[$a1]:-$a1}${NC} vs ${BOLD}${LABELS[$a2]:-$a2}${NC}"
    echo "  For detailed comparison, see the decision table in SKILL.md."
    echo
    echo "  Quick rule of thumb:"
    case "$a1-$a2" in
        api-sparql|sparql-api)
            echo "    SPARQL is better for graph queries (find X related to Y)."
            echo "    Action API is better for simple lookups (get page metadata)." ;;
        api-sql|sql-api)
            echo "    SQL is 100-1000× faster for bulk analytics."
            echo "    Action API is simpler for small (<50 item) tasks." ;;
        api-eventstreams|eventstreams-api)
            echo "    EventStreams is for live monitoring (push)."
            echo "    Action API is for historical data (pull)." ;;
        api-pywikibot|pywikibot-api)
            echo "    Pywikibot for bulk edits and bot operations."
            echo "    Action API for single edits or read-only queries." ;;
        rest-api|api-rest)
            echo "    REST API for single-page reads (simpler JSON)."
            echo "    Action API for multi-page queries (more filters)." ;;
        sparql-sql|sql-sparql)
            echo "    SPARQL for graph traversal across entities."
            echo "    SQL for aggregations, JOINs, and analytics on Wikipedia data." ;;
        *)
            echo "    See the decision tree in SKILL.md for detailed guidance." ;;
    esac
}

# ── Analyze task keywords and recommend ─────────────────────────────────────
recommend() {
    local task_lower
    task_lower=$(echo "$1" | tr '[:upper:]' '[:lower:]')

    echo -e "${BOLD}${CYAN}Task Analysis${NC}"
    echo "  Task: $1"
    echo

    # Detect category from keywords
    local category=""

    if echo "$task_lower" | grep -qE 'read|summary|content|page\b|article\b|single'; then
        category="read"
    elif echo "$task_lower" | grep -qE 'analytics|aggregate|count|stats|statistics|top\b|rank|average|report'; then
        category="analytics"
    elif echo "$task_lower" | grep -qE 'batch|bulk|many|multiple|list\b|all\b|categor|template|500'; then
        category="batch"
    elif echo "$task_lower" | grep -qE 'realtime|real.time|live\b|stream|monitor|watch|recent'; then
        category="realtime"
    elif echo "$task_lower" | grep -qE 'edit|write|create|update|delete|bot\b|save|upload'; then
        category="edit"
    elif echo "$task_lower" | grep -qE 'graph|relation|sparql|wikidata|connect|linked|semantic|property|qid'; then
        category="graph"
    elif echo "$task_lower" | grep -qE 'patrol|review|triage|new.page|unreviewed'; then
        category="patrol"
    fi

    if [ -z "$category" ]; then
        echo -e "  ${YELLOW}Could not auto-detect task category.${NC}"
        echo -e "  Keywords recognized: read, batch, analytics, realtime, edit, graph, patrol"
        echo
        echo -e "  ${BOLD}For a general task, these rules apply:${NC}"
        category="general"
    fi

    echo -e "${BOLD}Category: ${category}${NC}"
    echo

    case "$category" in
        read)
            echo -e "  ${GREEN}→ REST API${NC} (fastest for single pages)"
            echo "    https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
            echo
            echo "  If you need multiple pages at once:"
            echo -e "  ${GREEN}→ Action API${NC} (batch up to 50 titles)"
            echo "    action=query&titles=TITLE1|TITLE2&prop=extracts"
            echo
            echo "  If you need raw wikitext:"
            echo -e "  ${GREEN}→ Action API${NC} (action=parse&prop=wikitext)"
            echo
            echo "  Trade-offs:"
            echo "    REST API: simpler JSON, limited endpoints, faster"
            echo "    Action API: more parameters, more data formats, slightly slower"
            ;;
        batch)
            echo -e "  ${GREEN}→ Action API${NC} (for <500 items with simple filters)"
            echo "    Use list=categorymembers, list=embeddedin, list=search, etc."
            echo "    Batch parameters (titles=|ids=) handle up to 50 per call."
            echo
            echo -e "  ${GREEN}→ SQL Replicas${NC} (for >500 items or complex filters)"
            echo "    Requires SSH tunnel to Toolforge. 100-1000× faster."
            echo "    SELECT p.page_title FROM categorylinks cl"
            echo "    JOIN page p ON cl.cl_from = p.page_id"
            echo "    WHERE cl.cl_to = 'Category_name' AND p.page_namespace = 0"
            echo
            echo -e "  ${YELLOW}Tip:${NC} If you're writing a loop with >50 API calls, switch to SQL."
            ;;
        analytics)
            echo -e "  ${GREEN}→ SQL Replicas${NC} (fastest — single query)"
            echo "    JOINs across page, page_props, page_assessments, categorylinks"
            echo "    Example: top 50 pages by pageviews in a category"
            echo
            echo "  If you don't have database access:"
            echo -e "  ${GREEN}→ SPARQL${NC} (for graph analytics across Wikidata)"
            echo "    Example: count items by type, find items without a property"
            echo
            echo -e "  ${GREEN}→ Action API + batch pageviews${NC} (for small sets, <50 items)"
            echo "    Simpler but slower — no SSH tunnel needed"
            echo
            echo -e "  ${RED}✗ Avoid:${NC} Looping through API calls for >50 items."
            echo "    A SQL query that runs in 2s replaces 500+ API calls."
            ;;
        realtime)
            echo -e "  ${GREEN}→ EventStreams${NC} (only way for live data)"
            echo "    stream.wikimedia.org/v2/stream/recentchange"
            echo "    Push-based, no rate limits, sub-second delivery"
            echo
            echo "  If you need historical context alongside live data:"
            echo -e "  ${GREEN}→ EventStreams + Action API${NC} (stream + occasional snapshots)"
            echo
            echo -e "  ${RED}✗ Avoid:${NC} Polling list=recentchanges every few seconds."
            echo "    This wastes rate limits and introduces latency."
            ;;
        edit)
            echo -e "  ${GREEN}→ Pywikibot${NC} (recommended for all bot operations)"
            echo "    Built-in: rate limiting, edit conflicts, page generators"
            echo "    Ready-made scripts: replace.py, harvest_template.py, etc."
            echo
            echo "  For a single edit only:"
            echo -e "  ${GREEN}→ Action API${NC} (action=edit, simpler for one-off fixes)"
            echo
            echo -e "  ${YELLOW}Tip:${NC} For >10 edits, use Pywikibot. The built-in throttling"
            echo "    and conflict detection will save you from community complaints."
            ;;
        graph)
            echo -e "  ${GREEN}→ SPARQL${NC} (Wikidata Query Service)"
            echo "    https://query.wikidata.org/sparql"
            echo "    Best for: cross-entity queries, transitive properties, FILTER NOT EXISTS"
            echo
            echo "  For single-entity lookups only:"
            echo -e "  ${GREEN}→ Action API${NC} (wbgetentities — faster for one QID at a time)"
            echo "    200ms vs 2-30s for the same data via SPARQL"
            echo
            echo -e "  ${YELLOW}Tip:${NC} Use SPARQL for complex queries, wbgetentities for simple lookups."
            echo "    For batch classification (50+ entities), use wbgetentities with ids=|."
            ;;
        patrol)
            echo -e "  ${GREEN}→ PageTriage API${NC}"
            echo "    action=pagetriagelist (list unreviewed)"
            echo "    action=pagetriageaction (mark reviewed)"
            echo "    Requires patrol right for write operations."
            echo
            echo "  Without patrol rights:"
            echo -e "  ${GREEN}→ Action API${NC} (list=recentchanges&rctype=new)"
            echo "    Read-only, works for anyone."
            echo
            echo -e "  ${YELLOW}Note:${NC} PageTriage is primarily deployed on enwiki."
            ;;
        general)
            echo -e "  ${CYAN}Start with the decision tree in SKILL.md:${NC}"
            echo
            echo "    Single page read        → REST API"
            echo "    Multiple pages (filters) → Action API"
            echo "    Complex relations        → SPARQL"
            echo "    Bulk analytics           → SQL Replicas"
            echo "    Real-time monitoring     → EventStreams"
            echo "    Editing / bot operations → Pywikibot"
            echo "    Page patrol/triage       → PageTriage API"
            ;;
    esac
}

# ── Main ─────────────────────────────────────────────────────────────────────
if [ -z "$TASK" ]; then
    # Interactive mode: show menu
    echo -e "${BOLD}${CYAN}Wikipedia API Strategy Selector${NC}"
    echo
    echo "Describe what you want to do, or pick a category:"
    echo
    echo -e "  ${BOLD}1${NC}  Read a single page"
    echo -e "  ${BOLD}2${NC}  Batch query (multiple pages with filters)"
    echo -e "  ${BOLD}3${NC}  Analytics / bulk data"
    echo -e "  ${BOLD}4${NC}  Real-time monitoring"
    echo -e "  ${BOLD}5${NC}  Edit pages / bot operations"
    echo -e "  ${BOLD}6${NC}  Graph queries / Wikidata relations"
    echo -e "  ${BOLD}7${NC}  Page patrol / triage"
    echo -e "  ${BOLD}q${NC}  Quit"
    echo
    echo -e "  Or describe your task in words: ${CYAN}./api-strategy.sh \"pageviews for 50 physics articles\"${NC}"
    echo
    read -rp "Choice [1-7/q]: " choice
    echo

    case "$choice" in
        1) recommend "read a single article" ;;
        2) recommend "batch query multiple pages by category" ;;
        3) recommend "analytics bulk data" ;;
        4) recommend "realtime monitor" ;;
        5) recommend "edit bot" ;;
        6) recommend "graph sparql wikidata" ;;
        7) recommend "patrol triage" ;;
        q|Q) exit 0 ;;
        *) echo -e "${RED}Unknown choice${NC}"; exit 1 ;;
    esac
else
    recommend "$TASK"
fi
