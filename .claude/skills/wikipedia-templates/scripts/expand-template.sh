#!/usr/bin/env bash
# ============================================================================
# expand-template.sh — Expand a MediaWiki template via the Action API
#
# Usage:
#   ./expand-template.sh "TemplateName" "param1=val1|param2=val2"
#   echo "{{TemplateName|param=val}}" | ./expand-template.sh -
#
# Shows the fully expanded wikitext (templates, parser functions, magic words
# resolved) using the action=expandtemplates API.
# ============================================================================

set -euo pipefail

# --- Configuration ---------------------------------------------------------
WIKI="${WIKI:-https://en.wikipedia.org}"
USER_AGENT="${WIKIMEDIA_USER_AGENT:-WikipediaTemplatesSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch}"

# --- Help ------------------------------------------------------------------
show_help() {
    cat <<EOF
Usage: $(basename "$0") [template_name] [parameters]

Expand a MediaWiki template and show the fully rendered wikitext.

ARGUMENTS:
  template_name    Name of the template (e.g., "Infobox person")
  parameters       Pipe-separated parameters (e.g., "name=Test|birth_date=2024")
  -                Read template call from stdin (pipe mode)

OPTIONS:
  --help           Show this help and exit

ENVIRONMENT:
  WIKI             Wiki base URL (default: https://en.wikipedia.org)
  WIKIMEDIA_USER_AGENT  User-Agent string

EXAMPLES:
  $(basename "$0") "Infobox_person" "name=Albert Einstein|birth_date=14 March 1879"
  echo "{{Cn}}" | $(basename "$0") -
  WIKI=https://commons.wikimedia.org $(basename "$0") "Template:Information" "description=Test"
EOF
    exit 0
}

# --- Parse arguments -------------------------------------------------------
TEMPLATE_NAME=""
PARAMETERS=""
STDIN_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            show_help
            ;;
        -)
            STDIN_MODE=true
            shift
            ;;
        *)
            if [[ -z "$TEMPLATE_NAME" ]]; then
                TEMPLATE_NAME="$1"
            elif [[ -z "$PARAMETERS" ]]; then
                PARAMETERS="$1"
            else
                echo "Error: Unexpected argument: $1" >&2
                echo "Usage: $(basename "$0") [template_name] [parameters]" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

# --- Build the template call text -----------------------------------------
if $STDIN_MODE; then
    # Read from stdin
    TEXT=$(cat)
    if [[ -z "$TEXT" ]]; then
        echo "Error: No input received on stdin" >&2
        exit 1
    fi
elif [[ -n "$TEMPLATE_NAME" ]]; then
    if [[ -n "$PARAMETERS" ]]; then
        TEXT="{{$TEMPLATE_NAME|$PARAMETERS}}"
    else
        TEXT="{{$TEMPLATE_NAME}}"
    fi
else
    echo "Error: No template specified. Provide a template name or pipe input." >&2
    echo "Usage: $(basename "$0") [template_name] [parameters]" >&2
    exit 1
fi

# --- Call the API ----------------------------------------------------------
API_URL="${WIKI}/w/api.php"

RESPONSE=$(curl -s -S -w '%{http_code}' \
    -X POST \
    -H "User-Agent: ${USER_AGENT}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "action=expandtemplates" \
    --data-urlencode "text=${TEXT}" \
    --data-urlencode "format=json" \
    "${API_URL}" 2>/dev/null)

# Extract HTTP status code (last 3 chars) and body
HTTP_CODE="${RESPONSE: -3}"
BODY="${RESPONSE%???}"

# --- Check HTTP status ----------------------------------------------------
if [[ "$HTTP_CODE" != "200" ]]; then
    echo "Error: API returned HTTP ${HTTP_CODE}" >&2
    if [[ -n "$BODY" ]]; then
        echo "$BODY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f\"  {data['error'].get('info', '')}\", file=sys.stderr)
    if 'warnings' in data:
        for w in data['warnings'].values():
            msg = w.get('*', '')
            if msg:
                print(f\"  Warning: {msg}\", file=sys.stderr)
except Exception:
    pass
" 2>/dev/null || true
    fi
    exit 1
fi

# --- Parse JSON body ------------------------------------------------------
echo "$BODY" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'error' in data:
        print(f'API Error: {data[\"error\"].get(\"info\", \"Unknown\")}', file=sys.stderr)
        sys.exit(1)
    expanded = data.get('expandtemplates', {}).get('*', '')
    print(expanded)
except json.JSONDecodeError as e:
    print(f'JSON parse error: {e}', file=sys.stderr)
    sys.exit(1)
"
