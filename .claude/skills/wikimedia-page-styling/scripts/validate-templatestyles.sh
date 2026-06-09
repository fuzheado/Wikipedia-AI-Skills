#!/usr/bin/env bash
# ============================================================================
# validate-templatestyles.sh — Validate CSS against TemplateStyles allowlist
#
# Checks CSS files or wiki CSS templates for properties that are not allowed
# by MediaWiki's TemplateStyles sanitizer. Flags disallowed properties and
# values so you can fix them before deploying.
#
# Usage:
#   ./scripts/validate-templatestyles.sh path/to/style.css
#   ./scripts/validate-templatestyles.sh --wiki meta "Template:Project/style.css"
#   ./scripts/validate-templatestyles.sh style.css --strict
#   ./scripts/validate-templatestyles.sh --help
# ============================================================================

set -euo pipefail

# --- Configuration ---------------------------------------------------------
WIKI="${WIKI:-https://meta.wikimedia.org}"
USER_AGENT="${WIKIMEDIA_USER_AGENT:-WikimediaPageStylingSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch}"

# Allowed CSS properties (core set — matching MediaWiki TemplateStyles v2+)
# This is a representative subset; the full list is maintained at:
# https://github.com/wikimedia/mediawiki-extensions-TemplateStyles
ALLOWED_PROPERTIES=(
    # Box model
    "width" "height" "min-width" "max-width" "min-height" "max-height"
    "padding" "padding-top" "padding-right" "padding-bottom" "padding-left"
    "margin" "margin-top" "margin-right" "margin-bottom" "margin-left"
    "box-sizing"
    # Display & layout
    "display" "flex" "flex-direction" "flex-wrap" "flex-flow"
    "flex-grow" "flex-shrink" "flex-basis"
    "grid" "grid-template" "grid-template-columns" "grid-template-rows" "grid-template-areas"
    "grid-column" "grid-column-start" "grid-column-end"
    "grid-row" "grid-row-start" "grid-row-end"
    "grid-area" "gap" "grid-gap" "column-gap" "row-gap"
    "order" "align-items" "align-content" "align-self"
    "justify-items" "justify-content" "justify-self"
    "place-items" "place-content" "place-self"
    # Positioning
    "position" "top" "right" "bottom" "left"
    "overflow" "overflow-x" "overflow-y" "z-index"
    "float" "clear"
    # Typography
    "font" "font-family" "font-size" "font-weight" "font-style" "font-variant"
    "line-height" "text-align" "text-decoration" "text-transform"
    "text-overflow" "text-shadow"
    "letter-spacing" "word-spacing" "white-space"
    "word-break" "overflow-wrap" "hyphens"
    "direction" "unicode-bidi"
    "column-count" "column-gap" "column-width" "columns"
    # Color & background
    "color" "background" "background-color"
    "background-image" "background-repeat" "background-size"
    "background-position" "background-attachment"
    "background-clip" "background-origin"
    "opacity"
    # Border & outline
    "border" "border-collapse"
    "border-color" "border-style" "border-width"
    "border-top" "border-right" "border-bottom" "border-left"
    "border-top-color" "border-top-style" "border-top-width"
    "border-right-color" "border-right-style" "border-right-width"
    "border-bottom-color" "border-bottom-style" "border-bottom-width"
    "border-left-color" "border-left-style" "border-left-width"
    "border-radius" "border-top-left-radius" "border-top-right-radius"
    "border-bottom-left-radius" "border-bottom-right-radius"
    "outline" "outline-color" "outline-style" "outline-width"
    # Visual effects
    "box-shadow" "filter" "backdrop-filter"
    "transform" "transition" "transition-property"
    "transition-duration" "transition-timing-function" "transition-delay"
    "animation" "animation-name" "animation-duration"
    "animation-timing-function" "animation-delay"
    "animation-iteration-count" "animation-direction"
    "animation-fill-mode" "animation-play-state"
    # Lists
    "list-style" "list-style-type" "list-style-image" "list-style-position"
    # Tables
    "table-layout" "empty-cells" "caption-side" "vertical-align"
    # Content
    "content" "counter-increment" "counter-reset" "quotes"
    # UI
    "cursor" "visibility" "clip" "clip-path" "pointer-events"
    "resize" "user-select" "caret-color"
)

# Properties that are allowed but with restrictions
RESTRICTED_PROPERTIES=(
    "background-image:url()"  # url() not allowed, only gradients
    "font-family:custom"      # Only generic families and @font-face hosted on WMF
    "cursor:url()"            # Custom URL cursors not allowed
    "clip-path:url()"         # External URL clip-paths not allowed
)

# --- Help ------------------------------------------------------------------
show_help() {
    cat <<EOF
Usage: $(basename "$0") [options] <css-source>

Validate a CSS file or wiki CSS template against the TemplateStyles allowlist.

ARGUMENTS:
  css-source        Path to a local .css file, or a wiki template name
                    (e.g., "Project/style.css")

OPTIONS:
  --wiki WIKI       Wiki base URL (default: https://meta.wikimedia.org)
  --strict          Also warn about restricted/flagged properties
  --help            Show this help and exit

ENVIRONMENT:
  WIKI              Wiki base URL
  WIKIMEDIA_USER_AGENT  User-Agent string

EXAMPLES:
  $(basename "$0") path/to/style.css
  $(basename "$0") --wiki meta "AvoinGLAM/style.css"
  $(basename "$0") style.css --strict
EOF
    exit 0
}

# --- Parse arguments -------------------------------------------------------
CSS_SOURCE=""
STRICT=false
LOCAL_FILE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h)
            show_help
            ;;
        --wiki)
            WIKI="$2"
            shift 2
            ;;
        --strict)
            STRICT=true
            shift
            ;;
        *)
            if [[ -z "$CSS_SOURCE" ]]; then
                CSS_SOURCE="$1"
            else
                echo "Error: Unexpected argument: $1" >&2
                echo "Usage: $(basename "$0") [options] <css-source>" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "$CSS_SOURCE" ]]; then
    echo "Error: No CSS source specified." >&2
    echo "Usage: $(basename "$0") [options] <css-source>" >&2
    exit 1
fi

# --- Determine if local file or wiki template ------------------------------
if [[ -f "$CSS_SOURCE" ]]; then
    LOCAL_FILE=true
    CSS_CONTENT=$(cat "$CSS_SOURCE")
    echo "📄 Validating local file: $CSS_SOURCE"
else
    LOCAL_FILE=false
    echo "🌐 Fetching wiki template: $CSS_SOURCE from $WIKI"
    
    # Normalize template name
    TEMPLATE_NAME="$CSS_SOURCE"
    if [[ "$TEMPLATE_NAME" != */* ]] && [[ "$TEMPLATE_NAME" != Template:* ]]; then
        TEMPLATE_NAME="Template:${TEMPLATE_NAME}"
    fi
    
    API_URL="${WIKI}/w/api.php"
    RESPONSE=$(curl -s -S -w '%{http_code}' \
        -X POST \
        -H "User-Agent: ${USER_AGENT}" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        --data-urlencode "action=parse" \
        --data-urlencode "page=${TEMPLATE_NAME}" \
        --data-urlencode "prop=text" \
        --data-urlencode "format=json" \
        "${API_URL}" 2>/dev/null)
    
    HTTP_CODE="${RESPONSE: -3}"
    BODY="${RESPONSE%???}"
    
    if [[ "$HTTP_CODE" != "200" ]]; then
        echo "Error: API returned HTTP ${HTTP_CODE}" >&2
        exit 1
    fi
    
    CSS_CONTENT=$(echo "$BODY" | python3 -c "
import json, sys, html
data = json.load(sys.stdin)
text = data.get('parse', {}).get('text', {}).get('*', '')
# Extract CSS content - strip HTML wrapper
from bs4 import BeautifulSoup
soup = BeautifulSoup(text, 'html.parser')
# Look for <pre> or just the text content
pre = soup.find('pre')
if pre:
    print(pre.get_text())
else:
    # Try to extract just the CSS from the response
    import re
    css_match = re.search(r'<pre[^>]*>(.*?)</pre>', text, re.DOTALL)
    if css_match:
        print(html.unescape(css_match.group(1)))
    else:
        print(text)
" 2>/dev/null || echo "$CSS_CONTENT")
fi

# --- Validate CSS ----------------------------------------------------------
if [[ -z "$CSS_CONTENT" ]]; then
    echo "Error: No CSS content found." >&2
    exit 1
fi

echo ""
echo "🔍 Analyzing CSS..."
echo ""

# Extract all CSS property names using a simple regex
VIOLATIONS=0
WARNINGS=0

while IFS= read -r line; do
    # Skip comments, empty lines, and at-rules
    [[ "$line" =~ ^[[:space:]]*(\*|/|\}) ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    [[ "$line" =~ ^@ ]] && continue
    
    # Extract property name (before the colon)
    if [[ "$line" =~ [[:space:]]*([a-zA-Z@-]+)[[:space:]]*: ]]; then
        PROP="${BASH_REMATCH[1]}"
        
        # Check against allowed list
        FOUND=false
        for ALLOWED in "${ALLOWED_PROPERTIES[@]}"; do
            if [[ "$PROP" == "$ALLOWED" ]]; then
                FOUND=true
                break
            fi
        done
        
        if [[ "$FOUND" == false ]]; then
            echo "  ❌ DISALLOWED: ${line}"
            VIOLATIONS=$((VIOLATIONS + 1))
        elif [[ "$STRICT" == true ]]; then
            # Check for restricted values
            if [[ "$PROP" == "background-image" ]] && [[ "$line" =~ url\( ]]; then
                echo "  ⚠️  RESTRICTED: ${line} — background-image: url() not allowed"
                WARNINGS=$((WARNINGS + 1))
            elif [[ "$PROP" == "font-family" ]] && [[ ! "$line" =~ (sans-serif|serif|monospace|cursive|fantasy|system-ui) ]]; then
                echo "  ⚠️  RESTRICTED: ${line} — custom font may not be available"
                WARNINGS=$((WARNINGS + 1))
            fi
        fi
    fi
done < <(echo "$CSS_CONTENT" | tr ';' '\n')

# --- Summary ---------------------------------------------------------------
echo ""
echo "═══════════════════════════════════════════"
echo "  Validation Complete"
echo "═══════════════════════════════════════════"
echo "  Disallowed properties: $VIOLATIONS"
if [[ "$STRICT" == true ]]; then
    echo "  Restricted property uses: $WARNINGS"
fi
echo ""

if [[ $VIOLATIONS -gt 0 ]]; then
    echo "  ❌ Fix the disallowed properties above before deploying."
    echo "     See references/allowed-properties.md for the complete allowlist."
    exit 1
else
    echo "  ✅ No disallowed properties found."
    exit 0
fi
