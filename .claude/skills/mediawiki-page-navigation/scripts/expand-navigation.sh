#!/usr/bin/env bash
# ============================================================================
# expand-navigation.sh — Expand a navigation template call
#
# Shows the fully expanded wikitext output of a navigation template,
# resolving all parser functions, magic words, and conditional includes.
#
# Usage:
#   ./scripts/expand-navigation.sh "Project/Navigation" "image=File:hero.jpg"
#   ./scripts/expand-navigation.sh "Project/Navigation" --page "Project/Subpage"
#   ./scripts/expand-navigation.sh --help
# ============================================================================

set -euo pipefail

# --- Configuration ---------------------------------------------------------
WIKI="${WIKI:-https://meta.wikimedia.org}"
USER_AGENT="${WIKIMEDIA_USER_AGENT:-MediaWikiNavigationSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch}"

# --- Help ------------------------------------------------------------------
show_help() {
    cat <<EOF
Usage: $(basename "$0") [options] <template-name> [parameters]

Expand a navigation template and show fully rendered wikitext.

ARGUMENTS:
  template-name     Name of the navigation template
  parameters        Pipe-separated parameters (e.g., "image=File:x.jpg|title=Test")

OPTIONS:
  --wiki WIKI       Wiki base URL (default: https://meta.wikimedia.org)
  --page PAGE       Set the current page context (for #titleparts, {{FULLPAGENAME}})
  --help            Show this help and exit

EXAMPLES:
  $(basename "$0") "AvoinGLAM/Main navigation" "image=File:test.jpg"
  $(basename "$0") "Project/Navigation" --page "Project/Subpage"
  WIKI=https://commons.wikimedia.org $(basename "$0") "Commons:Navigation"
EOF
    exit 0
}

# --- Parse arguments -------------------------------------------------------
TEMPLATE_NAME=""
PARAMETERS=""
PAGE_CONTEXT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) show_help ;;
        --wiki) WIKI="$2"; shift 2 ;;
        --page) PAGE_CONTEXT="$2"; shift 2 ;;
        *)
            if [[ -z "$TEMPLATE_NAME" ]]; then
                TEMPLATE_NAME="$1"
            elif [[ -z "$PARAMETERS" ]]; then
                PARAMETERS="$1"
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
    exit 1
fi

# Normalize template name
FULL_TEMPLATE="$TEMPLATE_NAME"
if [[ "$FULL_TEMPLATE" != Template:* ]] && [[ "$FULL_TEMPLATE" != */* ]]; then
    FULL_TEMPLATE="Template:${FULL_TEMPLATE}"
fi

echo "🧭 Expanding navigation template"
echo "  Template: $FULL_TEMPLATE"
echo "  Wiki:     $WIKI"
if [[ -n "$PAGE_CONTEXT" ]]; then
    echo "  Context:  $PAGE_CONTEXT"
fi
if [[ -n "$PARAMETERS" ]]; then
    echo "  Params:   $PARAMETERS"
fi
echo ""

# Build the template call
if [[ -n "$PARAMETERS" ]]; then
    CALL="{{${FULL_TEMPLATE}|${PARAMETERS}}}"
else
    CALL="{{${FULL_TEMPLATE}}}"
fi

# If we have a page context, we need to simulate it
# Use action=expandtemplates with the page context
API_URL="${WIKI}/w/api.php"

EXPAND_PARAMS=(
    "action=expandtemplates"
    "text=${CALL}"
    "format=json"
)

if [[ -n "$PAGE_CONTEXT" ]]; then
    # The API doesn't have a direct "set current page" parameter.
    # We can use prop=revisions to get the page content, then expand.
    # But for template expansion, we wrap it in a page preview.
    EXPAND_PARAMS+=("title=${PAGE_CONTEXT}")
fi

# Build POST data
POST_DATA=""
for param in "${EXPAND_PARAMS[@]}"; do
    key="${param%%=*}"
    value="${param#*=}"
    if [[ -n "$POST_DATA" ]]; then
        POST_DATA+="&"
    fi
    POST_DATA+="$(python3 -c "import urllib.parse; print(urllib.parse.quote('${key}') + '=' + urllib.parse.quote('''${value}'''))")"
done

RESPONSE=$(curl -s -S -w '%{http_code}' \
    -X POST \
    -H "User-Agent: ${USER_AGENT}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "$POST_DATA" \
    "${API_URL}" 2>/dev/null)

HTTP_CODE="${RESPONSE: -3}"
BODY="${RESPONSE%???}"

if [[ "$HTTP_CODE" != "200" ]]; then
    echo "Error: API returned HTTP ${HTTP_CODE}" >&2
    echo "$BODY" | python3 -m json.tool 2>/dev/null || true
    exit 1
fi

# Extract the expanded wikitext
echo "$BODY" | python3 -c "
import json, sys
data = json.load(sys.stdin)
expanded = data.get('expandtemplates', {}).get('*', '')
print(expanded)
" 2>/dev/null
