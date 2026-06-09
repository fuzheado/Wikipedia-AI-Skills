#!/usr/bin/env bash
# ============================================================================
# extract-translatable-strings.sh — Extract translatable strings from a page
#
# Extracts all <translate> sections and their translation unit IDs from a
# wiki page or template. Useful for auditing translation coverage or
# preparing translation files.
#
# Usage:
#   ./scripts/extract-translatable-strings.sh "AvoinGLAM" --wiki meta
#   ./scripts/extract-translatable-strings.sh "Template:AvoinGLAM/Main navigation"
#   ./scripts/extract-translatable-strings.sh "Page" --ids
#   ./scripts/extract-translatable-strings.sh "Page" --tvars
#   ./scripts/extract-translatable-strings.sh --help
# ============================================================================

set -euo pipefail

# --- Configuration ---------------------------------------------------------
WIKI="${WIKI:-https://meta.wikimedia.org}"
USER_AGENT="${WIKIMEDIA_USER_AGENT:-MediaWikiTranslateSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch}"

# --- Help ------------------------------------------------------------------
show_help() {
    cat <<EOF
Usage: $(basename "$0") [options] <page-title>

Extract translatable strings from a wiki page.

ARGUMENTS:
  page-title        Title of the page to extract from

OPTIONS:
  --wiki WIKI       Wiki base URL (default: https://meta.wikimedia.org)
  --ids             Show translation unit IDs only (no content)
  --tvars           Show <tvar> variables used
  --markdown        Output as Markdown table
  --help            Show this help and exit

EXAMPLES:
  $(basename "$0") "AvoinGLAM" --wiki meta
  $(basename "$0") "Template:AvoinGLAM/Main navigation"
  $(basename "$0") "AvoinGLAM/Past activities" --ids
  $(basename "$0") "Template:Project/Navigation" --tvars
EOF
    exit 0
}

# --- Parse arguments -------------------------------------------------------
PAGE_TITLE=""
SHOW_IDS=false
SHOW_TVARS=false
OUTPUT_MD=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) show_help ;;
        --wiki) WIKI="$2"; shift 2 ;;
        --ids) SHOW_IDS=true; shift ;;
        --tvars) SHOW_TVARS=true; shift ;;
        --markdown) OUTPUT_MD=true; shift ;;
        *)
            if [[ -z "$PAGE_TITLE" ]]; then
                PAGE_TITLE="$1"
            else
                echo "Error: Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "$PAGE_TITLE" ]]; then
    echo "Error: No page title specified." >&2
    exit 1
fi

API_URL="${WIKI}/w/api.php"

echo "📝 Extract Translatable Strings"
echo "═══════════════════════════════════════════"
echo "  Page:  $PAGE_TITLE"
echo "  Wiki:  $WIKI"
echo ""

# --- Fetch page content (raw wikitext) ------------------------------------
echo "─── Fetching page wikitext ───"

RAW_URL="${WIKI}/w/index.php"
RESPONSE=$(curl -s -S -w '%{http_code}' \
    -H "User-Agent: ${USER_AGENT}" \
    "${RAW_URL}?title=${PAGE_TITLE}&action=raw" 2>/dev/null)

HTTP_CODE="${RESPONSE: -3}"
WIKITEXT="${RESPONSE%???}"

if [[ "$HTTP_CODE" != "200" ]]; then
    echo "Error: HTTP ${HTTP_CODE} when fetching page." >&2
    exit 1
fi

if [[ -z "$WIKITEXT" ]]; then
    echo "Error: Empty response." >&2
    exit 1
fi

echo "  Content length: ${#WIKITEXT} characters"
echo ""

# --- Extract <translate> sections -----------------------------------------
echo "─── Translation Units ───"

echo "$WIKITEXT" | python3 -c "
import json, re, sys

wikitext = sys.stdin.read()
show_ids = $([ $SHOW_IDS == true ] && echo "True" || echo "False")
show_tvars = $([ $SHOW_TVARS == true ] && echo "True" || echo "False")
output_md = $([ $OUTPUT_MD == true ] && echo "True" || echo "False")

# Find all <translate>...</translate> sections
translate_sections = re.findall(
    r'<translate>(.*?)</translate>', wikitext, re.DOTALL
)

if not translate_sections:
    print('  (no <translate> sections found)')
    sys.exit(0)

print(f'  Found {len(translate_sections)} <translate> section(s)\\n')

# Find all translation unit markers and their content
all_units = []
all_tvars = []

for section in translate_sections:
    # Find all translation units (<!--T:N--> followed by content)
    units = re.findall(
        r'<!--T:(\d+)-->(.*?)(?=<!--T:\d+-->|\Z)', section, re.DOTALL
    )
    for unit_id, content in units:
        content = content.strip()
        all_units.append((int(unit_id), content))
        
        # Extract tvar variables
        tvars = re.findall(r'<tvar\s+name=\"([^\"]+)\">', content)
        for tvar in tvars:
            all_tvars.append((int(unit_id), tvar))

# Also find units that are just inline (no marker)
# Pattern: <!--T:N--> text or just text with markers
for section in translate_sections:
    # Split by <!--T:--> markers
    parts = re.split(r'(<!--T:\d+-->)', section)
    i = 0
    while i < len(parts):
        marker_match = re.match(r'<!--T:(\d+)-->', parts[i])
        if marker_match:
            unit_id = int(marker_match.group(1))
            if i + 1 < len(parts):
                content = parts[i + 1].strip()
                # Check if it's just a heading marker
                if content and not content.startswith('==') or (content.startswith('==') and len(content) < 100):
                    pass  # It's already in all_units or it's a heading
            i += 2
        else:
            i += 1

# Deduplicate
seen_ids = set()
unique_units = []
for uid, content in all_units:
    if uid not in seen_ids:
        seen_ids.add(uid)
        unique_units.append((uid, content))

if show_ids:
    print(f'  Translation unit IDs: {[u[0] for u in sorted(unique_units)]}')
    print(f'  Total: {len(unique_units)} units')
elif output_md:
    print('| ID | Content |')
    print('|-----|---------|')
    for uid, content in sorted(unique_units):
        # Truncate long content for table
        display = content[:80].replace('|', '\\|')
        print(f'| T:{uid} | {display} |')
else:
    for uid, content in sorted(unique_units):
        # Show first line of content
        first_line = content.split('\\n')[0][:100]
        print(f'  [{uid}] {first_line}')
    print(f'\\n  Total: {len(unique_units)} units')

# Show tvar variables
if show_tvars:
    unique_tvars = list(set(all_tvars))
    if unique_tvars:
        print(f'\\n  <tvar> Variables:')
        for uid, tvar_name in sorted(unique_tvars):
            print(f'    Unit {uid}: {tvar_name}')
        print(f'  Total: {len(unique_tvars)} tvars')
" 2>/dev/null

# --- Extract heading patterns --------------------------------------------
echo ""
echo "─── Heading Structure (for translation) ───"

echo "$WIKITEXT" | python3 -c "
import re, sys
wikitext = sys.stdin.read()
# Find markdown-style headings in translate sections
translate_sections = re.findall(
    r'<translate>(.*?)</translate>', wikitext, re.DOTALL
)
for section in translate_sections:
    headings = re.findall(r'(={2,6})\s*(.*?)\s*\1', section)
    for level, text in headings:
        lvl = len(level)
        indent = '  ' * (lvl - 1)
        print(f'{indent}{\"|\" * lvl} {text}')
" 2>/dev/null

echo ""
echo "═══ Extraction Complete ═══"
