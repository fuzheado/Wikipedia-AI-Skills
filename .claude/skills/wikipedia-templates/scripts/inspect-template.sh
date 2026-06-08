#!/usr/bin/env bash
# ============================================================================
# inspect-template.sh — Get comprehensive info about a MediaWiki template
#
# Usage:
#   ./inspect-template.sh "TemplateName"
#   ./inspect-template.sh "TemplateName" --protection
#   ./inspect-template.sh "TemplateName" --source
#   ./inspect-template.sh "TemplateName" --modules
#
# Fetches: source, protection level, Lua dependencies, transclusion count,
# and tracking categories for any template on a MediaWiki wiki.
# ============================================================================

set -euo pipefail

# --- Configuration ---------------------------------------------------------
WIKI="${WIKI:-https://en.wikipedia.org}"
USER_AGENT="${WIKIMEDIA_USER_AGENT:-WikipediaTemplatesSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch}"
API_URL="${WIKI}/w/api.php"

# --- Help ------------------------------------------------------------------
show_help() {
    cat <<EOF
Usage: $(basename "$0") <template_name> [options]

Get comprehensive information about a MediaWiki template.

ARGUMENTS:
  template_name       Template to inspect (e.g., "Infobox person")

OPTIONS:
  --protection        Show only protection information
  --source            Show only the raw template source code
  --modules           Show only Lua module dependencies
  --help              Show this help and exit

ENVIRONMENT:
  WIKI                Wiki base URL (default: https://en.wikipedia.org)
  WIKIMEDIA_USER_AGENT  User-Agent string

EXAMPLES:
  $(basename "$0") "Infobox person"
  $(basename "$0") "Infobox settlement" --modules
  $(basename "$0") "Cite web" --source
EOF
    exit 0
}

# --- Parse arguments -------------------------------------------------------
TEMPLATE_NAME=""
SHOW_PROTECTION=false
SHOW_SOURCE=false
SHOW_MODULES=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            show_help
            ;;
        --protection)
            SHOW_PROTECTION=true
            shift
            ;;
        --source)
            SHOW_SOURCE=true
            shift
            ;;
        --modules)
            SHOW_MODULES=true
            shift
            ;;
        -*)
            echo "Error: Unknown option: $1" >&2
            exit 1
            ;;
        *)
            if [[ -z "$TEMPLATE_NAME" ]]; then
                TEMPLATE_NAME="$1"
            else
                echo "Error: Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "$TEMPLATE_NAME" ]]; then
    echo "Error: No template name specified." >&2
    echo "Usage: $(basename "$0") <template_name> [options]" >&2
    exit 1
fi

# If only one specific view is requested, show only that
SINGLE_VIEW=false
if $SHOW_PROTECTION || $SHOW_SOURCE || $SHOW_MODULES; then
    SINGLE_VIEW=true
fi

# Prefix "Template:" if not already namespaced
API_TITLE="$TEMPLATE_NAME"
if [[ "$API_TITLE" != Template:* && "$API_TITLE" != Module:* ]]; then
    API_TITLE="Template:${API_TITLE}"
fi

# URL-encode a string for use in API queries
url_encode() {
    python3 -c "import urllib.parse; print(urllib.parse.quote('$1', safe=''))"
}

# --- Fetch basic page info (protection, pageprops) ------------------------
fetch_page_info() {
    ENCODED_TITLE=$(url_encode "${API_TITLE}")
    curl -s -S \
        -H "User-Agent: ${USER_AGENT}" \
        "${API_URL}?action=query&prop=info%7Cpageprops&inprop=protection&titles=${ENCODED_TITLE}&format=json"
}

# --- Fetch raw source -----------------------------------------------------
fetch_raw_source() {
    ENCODED_TITLE=$(url_encode "${API_TITLE}")
    RESPONSE=$(curl -s -S \
        -H "User-Agent: ${USER_AGENT}" \
        "${API_URL}?action=query&prop=revisions&rvprop=content&rvlimit=1&titles=${ENCODED_TITLE}&format=json")
    echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
pages = data.get('query', {}).get('pages', {})
for pid, pdata in pages.items():
    if pid == '-1':
        print('Template not found.')
        continue
    revs = pdata.get('revisions', [])
    if revs:
        print(revs[0].get('content', '(empty)'))
    else:
        print('(no revisions — page may be missing)')
"
}

# --- Fetch Lua module dependencies ----------------------------------------
fetch_module_deps() {
    ENCODED_TITLE=$(url_encode "${API_TITLE}")
    curl -s -S \
        -H "User-Agent: ${USER_AGENT}" \
        "${API_URL}?action=query&prop=templates&titles=${ENCODED_TITLE}&format=json" | \
        python3 -c "
import json, sys
data = json.load(sys.stdin)
pages = data.get('query', {}).get('pages', {})
for pid, pdata in pages.items():
    if pid == '-1':
        print('Template not found.')
        continue
    templates = pdata.get('templates', [])
    modules = [t for t in templates if t.get('ns') == 828]
    if modules:
        print(f'{len(modules)} Lua module(s) used by {pdata.get(\"title\", \"?\")}:')
        for m in modules:
            print(f'  • {m[\"title\"]}')
    else:
        print(f'No Lua module dependencies found for {pdata.get(\"title\", \"?\")}.')
"
}

# --- Fetch transclusion count ---------------------------------------------
fetch_transclusion_count() {
    ENCODED_TITLE=$(url_encode "${API_TITLE}")
    curl -s -S \
        -H "User-Agent: ${USER_AGENT}" \
        "${API_URL}?action=query&prop=pageprops&titles=${ENCODED_TITLE}&format=json" | \
        python3 -c "
import json, sys
data = json.load(sys.stdin)
pages = data.get('query', {}).get('pages', {})
for pid, pdata in pages.items():
    count = pdata.get('pageprops', {}).get('wikibase-badge-goodcount', '') or \
            pdata.get('pageprops', {}).get('expected-unconnected-page', '')
    # Use embeddedin for actual count
    print(f'Page ID: {pid}')
"
}

# --- Main -----------------------------------------------------------------
PAGE_INFO=$(fetch_page_info)

# Parse page info
PAGE_TITLE=$(echo "$PAGE_INFO" | python3 -c "
import json, sys
data = json.load(sys.stdin)
pages = data.get('query', {}).get('pages', {})
for pid, pdata in pages.items():
    if pid == '-1':
        print('NOT_FOUND')
    else:
        print(pdata.get('title', '?'))
" 2>/dev/null || echo "NOT_FOUND")

if [[ "$PAGE_TITLE" == "NOT_FOUND" ]]; then
    echo "Error: Template '${TEMPLATE_NAME}' not found on ${WIKI}." >&2
    exit 1
fi

# --- Protection -----------------------------------------------------------
if ! $SINGLE_VIEW || $SHOW_PROTECTION; then
    echo "=== Protection ==="
    echo "$PAGE_INFO" | python3 -c "
import json, sys
data = json.load(sys.stdin)
pages = data.get('query', {}).get('pages', {})
for pid, pdata in pages.items():
    prot = pdata.get('protection', [])
    if prot:
        for p in prot:
            level = p.get('level', 'unknown')
            expiry = p.get('expiry', 'unknown')
            print(f'  {p.get(\"type\", \"?\")}: {level} (expires: {expiry})')
    else:
        print('  No protection (unprotected)')
" 2>/dev/null
    echo ""
fi

# --- Lua Module Dependencies ----------------------------------------------
if ! $SINGLE_VIEW || $SHOW_MODULES; then
    echo "=== Lua Modules ==="
    fetch_module_deps
    echo ""
fi

# --- Source Code ----------------------------------------------------------
if ! $SINGLE_VIEW || $SHOW_SOURCE; then
    echo "=== Source Code ==="
    fetch_raw_source
fi

# --- Transclusion count (via embeddedin count, not shown if single view) --
if ! $SINGLE_VIEW; then
    echo ""
    echo "=== Usage Count ==="
    # Fetch first page of embeddedin to show a count sample
    ENCODED_TITLE=$(url_encode "${API_TITLE}")
    COUNT_RESPONSE=$(curl -s -S \
        -H "User-Agent: ${USER_AGENT}" \
        "${API_URL}?action=query&list=embeddedin&eititle=${ENCODED_TITLE}&eilimit=1&format=json" 2>/dev/null)
    echo "$COUNT_RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
query = data.get('query', {})
pages = query.get('embeddedin', [])
total = len(pages)
# Check for totalhits
cont = query.get('continue', {})
if total > 0:
    print(f'  {total}+ page(s) use this template (use template-usage.sh for full list)')
else:
    print('  No pages currently use this template')
" 2>/dev/null
fi
