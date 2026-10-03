#!/usr/bin/env bash
# ============================================================================
# template-usage.sh — Find all pages using a template
#
# Usage:
#   ./template-usage.sh "TemplateName"
#   ./template-usage.sh "TemplateName" --count
#   ./template-usage.sh "TemplateName" --limit 20
#
# Uses the Action API's list=embeddedin to find pages transcluding a given
# template. Paginates automatically unless --limit is specified.
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

Find all pages that use (transclude) a given template.

ARGUMENTS:
  template_name       Template to search for (e.g., "Cn" or "Infobox person")

OPTIONS:
  --count             Show total count of pages using the template
  --limit N           Maximum results to show (default: auto-paginate all)
  --namespaces NS     Comma-separated namespace list (default: 0)
  --help              Show this help and exit

ENVIRONMENT:
  WIKI                Wiki base URL (default: https://en.wikipedia.org)
  WIKIMEDIA_USER_AGENT  User-Agent string

EXAMPLES:
  $(basename "$0") "Cn"
  $(basename "$0") "Infobox person" --count
  $(basename "$0") "Stub" --limit 10
  $(basename "$0") "Unreferenced" --namespaces 0
EOF
    exit 0
}

# --- Parse arguments -------------------------------------------------------
TEMPLATE_NAME=""
SHOW_COUNT=false
LIMIT=""
NAMESPACES="0"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            show_help
            ;;
        --count)
            SHOW_COUNT=true
            shift
            ;;
        --limit)
            if [[ -z "${2:-}" ]]; then
                echo "Error: --limit requires a number" >&2
                exit 1
            fi
            LIMIT="$2"
            shift 2
            ;;
        --namespaces)
            if [[ -z "${2:-}" ]]; then
                echo "Error: --namespaces requires a value" >&2
                exit 1
            fi
            NAMESPACES="$2"
            shift 2
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

# URL-encode a string for use in API queries
url_encode() {
    python3 -c "import urllib.parse; print(urllib.parse.quote('$1', safe=''))"
}

# Prefix "Template:" if not already namespaced
if [[ "$TEMPLATE_NAME" != Template:* && "$TEMPLATE_NAME" != Module:* ]]; then
    TEMPLATE_NAME="Template:${TEMPLATE_NAME}"
fi

# --- Fetch pages using the template ---------------------------------------
RESULTS=()
CONTINUE=""

while true; do
    ENCODED_TITLE=$(url_encode "${TEMPLATE_NAME}")
    # Build API query parameters
    PARAMS="action=query&list=embeddedin"
    PARAMS+="&eititle=${ENCODED_TITLE}"
    PARAMS+="&einamespace=${NAMESPACES}"
    PARAMS+="&eilimit=500"
    PARAMS+="&format=json"

    if [[ -n "$CONTINUE" ]]; then
        ENCODED_CONT=$(url_encode "${CONTINUE}")
        PARAMS+="&eicontinue=${ENCODED_CONT}"
    fi

    RESPONSE=$(curl -s -S -w '\n%{http_code}' \
        -H "User-Agent: ${USER_AGENT}" \
        "${API_URL}?${PARAMS}" 2>/dev/null || true)
    HTTP_CODE="${RESPONSE##*$'\n'}"
    BODY="${RESPONSE%$'\n'*}"

    # Never let a blocked/throttled API look like an empty result set: the empty
    # stdout used to be indistinguishable from "this template is unused".
    if [[ "$HTTP_CODE" != "200" ]]; then
        echo "Error: API returned HTTP ${HTTP_CODE} from ${API_URL}" >&2
        echo "  Retry later; if it persists, check the User-Agent policy" >&2
        echo "  (see the wikimedia-api-access skill) or whether the wiki is reachable." >&2
        exit 2
    fi

    # Parse the response
    NEW_ITEMS=$(printf '%s' "$BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
pages = data.get('query', {}).get('embeddedin', [])
for p in pages:
    ns = p.get('ns', 0)
    title = p.get('title', '')
    print(f'{ns}|{title}')
cont = data.get('continue', {}).get('eicontinue', '')
if cont:
    print(f'__CONTINUE__{cont}')
") || {
        echo "Error: unexpected API response from ${API_URL} (not JSON, or an API error object)" >&2
        exit 2
    }

    # Extract continuation token
    CONT_VAL=""
    while IFS= read -r line; do
        if [[ "$line" == __CONTINUE__* ]]; then
            CONT_VAL="${line#__CONTINUE__}"
        else
            RESULTS+=("$line")
        fi
    done <<< "$NEW_ITEMS"

    # Check limit
    if [[ -n "$LIMIT" ]]; then
        TOTAL_FETCHED="${#RESULTS[@]}"
        if (( TOTAL_FETCHED >= LIMIT )); then
            break
        fi
    fi

    if [[ -z "$CONT_VAL" ]]; then
        break
    fi
    CONTINUE="$CONT_VAL"
done

# --- Output results -------------------------------------------------------
TOTAL="${#RESULTS[@]}"

if $SHOW_COUNT; then
    echo "Total pages using ${TEMPLATE_NAME}: ${TOTAL}"
    if (( TOTAL > 0 )); then
        echo ""
        echo "--- First ${TOTAL} results ---"
    fi
fi

LIMIT_OUTPUT="${LIMIT:-$TOTAL}"
COUNT=0
for item in "${RESULTS[@]}"; do
    if [[ -n "$item" ]]; then
        echo "$item"
        COUNT=$((COUNT + 1))
        if [[ -n "$LIMIT" ]] && (( COUNT >= LIMIT )); then
            break
        fi
    fi
done

if (( TOTAL == 0 )); then
    echo "No pages found using ${TEMPLATE_NAME}."
fi
