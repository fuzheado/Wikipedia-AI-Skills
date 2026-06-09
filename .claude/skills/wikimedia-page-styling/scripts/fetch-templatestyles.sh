#!/usr/bin/env bash
# ============================================================================
# fetch-templatestyles.sh — Fetch rendered CSS from a TemplateStyles template
#
# Downloads the compiled, sanitized CSS that the browser actually receives
# from a TemplateStyles template page. Useful for debugging what properties
# survived the sanitizer, and for comparing source vs. output.
#
# Usage:
#   ./scripts/fetch-templatestyles.sh "Project/style.css" --wiki meta
#   ./scripts/fetch-templatestyles.sh "Project/style.css" --diff
#   ./scripts/fetch-templatestyles.sh --help
# ============================================================================

set -euo pipefail

# --- Configuration ---------------------------------------------------------
WIKI="${WIKI:-https://meta.wikimedia.org}"
USER_AGENT="${WIKIMEDIA_USER_AGENT:-WikimediaPageStylingSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch}"

# --- Help ------------------------------------------------------------------
show_help() {
    cat <<EOF
Usage: $(basename "$0") [options] <template-name>

Fetch the rendered CSS from a TemplateStyles template.

ARGUMENTS:
  template-name     Template name (e.g., "Project/style.css")

OPTIONS:
  --wiki WIKI       Wiki base URL (default: https://meta.wikimedia.org)
  --diff            Show diff between source and rendered CSS
  --output FILE     Save rendered CSS to file
  --help            Show this help and exit

EXAMPLES:
  $(basename "$0") "AvoinGLAM/style.css" --wiki meta
  $(basename "$0") "Project/style.css" --diff
  $(basename "$0") "Project/style.css" --output rendered.css
EOF
    exit 0
}

# --- Parse arguments -------------------------------------------------------
TEMPLATE_NAME=""
SHOW_DIFF=false
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) show_help ;;
        --wiki) WIKI="$2"; shift 2 ;;
        --diff) SHOW_DIFF=true; shift ;;
        --output) OUTPUT_FILE="$2"; shift 2 ;;
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
    exit 1
fi

# Normalize template name
FULL_TEMPLATE="$TEMPLATE_NAME"
if [[ "$FULL_TEMPLATE" != Template:* ]] && [[ "$FULL_TEMPLATE" != */* ]]; then
    FULL_TEMPLATE="Template:${FULL_TEMPLATE}"
fi

echo "🌐 Fetching rendered stylesheet: $FULL_TEMPLATE from $WIKI"

# The browser loads templatestyles via load.php.
# We can get the compiled CSS by asking the API for the module content.
API_URL="${WIKI}/w/api.php"

# Step 1: Get the template content (the source CSS)
echo "  → Fetching source CSS..."
SOURCE_RESPONSE=$(curl -s -S -w '%{http_code}' \
    -X POST \
    -H "User-Agent: ${USER_AGENT}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "action=parse" \
    --data-urlencode "page=${FULL_TEMPLATE}" \
    --data-urlencode "prop=text" \
    --data-urlencode "format=json" \
    "${API_URL}" 2>/dev/null)

SOURCE_HTTP="${SOURCE_RESPONSE: -3}"
SOURCE_BODY="${SOURCE_RESPONSE%???}"

if [[ "$SOURCE_HTTP" != "200" ]]; then
    echo "Error: API returned HTTP ${SOURCE_HTTP}" >&2
    exit 1
fi

SOURCE_CSS=$(echo "$SOURCE_BODY" | python3 -c "
import json, sys, re, html
data = json.load(sys.stdin)
text = data.get('parse', {}).get('text', {}).get('*', '')
# Extract from <pre> tags
pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', text, re.DOTALL)
if pre_match:
    print(html.unescape(pre_match.group(1)))
else:
    # Just print the raw text
    print(text)
")

# Step 2: Get the rendered stylesheet via the load.php URL
# TemplateStyles modules are loaded as: ext.templatestyles;target=Template:Name
TARGET=$(echo "$FULL_TEMPLATE" | sed 's|/|.|g' | sed 's|Template:||')
MODULE_NAME="ext.templatestyles;target=${TARGET}"

echo "  → Fetching rendered (sanitized) CSS..."
RENDERED_URL="${WIKI}/w/load.php?modules=${MODULE_NAME}&only=styles&format=css"
RENDERED_CSS=$(curl -s -S -H "User-Agent: ${USER_AGENT}" "${RENDERED_URL}" 2>/dev/null)

if [[ -z "$RENDERED_CSS" ]] || echo "$RENDERED_CSS" | grep -qi "error\|exception"; then
    echo "  ⚠️  Could not fetch rendered CSS directly. The module may not be loaded yet."
    echo "     This is normal for newly created templates. Try viewing a page that uses the template first."
    RENDERED_CSS=""
fi

# --- Output -----------------------------------------------------------------
echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  TemplateStyles: $FULL_TEMPLATE"
echo "╚══════════════════════════════════════════════════╝"
echo ""

if [[ -n "$OUTPUT_FILE" ]]; then
    echo "$RENDERED_CSS" > "$OUTPUT_FILE"
    echo "  💾 Rendered CSS saved to: $OUTPUT_FILE"
fi

# Show source line count
SRC_LINES=$(echo "$SOURCE_CSS" | wc -l | tr -d ' ')
RND_LINES=$(echo "$RENDERED_CSS" | wc -l | tr -d ' ')
echo "  Source CSS:     $SRC_LINES lines"
echo "  Rendered CSS:   ${RND_LINES:-0} lines"
echo ""

if [[ "$SHOW_DIFF" == true ]] && [[ -n "$RENDERED_CSS" ]]; then
    echo "─── Source vs. Rendered Diff ───"
    diff <(echo "$SOURCE_CSS") <(echo "$RENDERED_CSS") 2>/dev/null || true
fi

# Show the rendered CSS
echo "$RENDERED_CSS"
