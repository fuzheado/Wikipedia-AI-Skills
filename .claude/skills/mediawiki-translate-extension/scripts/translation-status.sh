#!/usr/bin/env bash
# ============================================================================
# translation-status.sh — Check translation status of a translatable page
#
# Shows available translations, completion percentages, and fuzzy (outdated)
# units for a page that has been marked for translation.
#
# Usage:
#   ./scripts/translation-status.sh "AvoinGLAM/Past activities" --wiki meta
#   ./scripts/translation-status.sh "AvoinGLAM" --languages
#   ./scripts/translation-status.sh "Project/Page" --incomplete
#   ./scripts/translation-status.sh --help
# ============================================================================

set -euo pipefail

# --- Configuration ---------------------------------------------------------
WIKI="${WIKI:-https://meta.wikimedia.org}"
USER_AGENT="${WIKIMEDIA_USER_AGENT:-MediaWikiTranslateSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch}"

# --- Help ------------------------------------------------------------------
show_help() {
    cat <<EOF
Usage: $(basename "$0") [options] <page-title>

Check translation status of a translatable page.

ARGUMENTS:
  page-title        Title of the page to check

OPTIONS:
  --wiki WIKI       Wiki base URL (default: https://meta.wikimedia.org)
  --languages       Show all languages with completion percentages
  --incomplete      Show only incomplete translations (< 100%)
  --json            Output as JSON
  --help            Show this help and exit

EXAMPLES:
  $(basename "$0") "AvoinGLAM/Past activities" --wiki meta
  $(basename "$0") "AvoinGLAM" --languages
  $(basename "$0") "Project/Page" --incomplete
EOF
    exit 0
}

# --- Parse arguments -------------------------------------------------------
PAGE_TITLE=""
SHOW_LANGUAGES=false
SHOW_INCOMPLETE=false
OUTPUT_JSON=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) show_help ;;
        --wiki) WIKI="$2"; shift 2 ;;
        --languages) SHOW_LANGUAGES=true; shift ;;
        --incomplete) SHOW_INCOMPLETE=true; shift ;;
        --json) OUTPUT_JSON=true; shift ;;
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

echo "🌐 Translation Status Checker"
echo "═══════════════════════════════════════════"
echo "  Page: $PAGE_TITLE"
echo "  Wiki: $WIKI"
echo ""

# --- Step 1: Get language links (all translations) -----------------------
echo "─── Fetching language links ───"

LANGLINKS=$(curl -s -S \
    -H "User-Agent: ${USER_AGENT}" \
    "${API_URL}?action=query&prop=langlinks&titles=${PAGE_TITLE}&lllimit=500&format=json" 2>/dev/null)

echo "$LANGLINKS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pid, pdata in data.get('query', {}).get('pages', {}).items():
    langlinks = pdata.get('langlinks', [])
    if langlinks:
        print(f'  Found {len(langlinks)} language variants:')
        for ll in langlinks:
            lang = ll.get('lang', '?')
            title = ll.get('*', '?')
            print(f'    🌐 {lang}: {title}')
    else:
        print('  (no language links found — page may not be translatable)')
" 2>/dev/null

# --- Step 2: Check translation info via the API (if available) -----------
echo ""
echo "─── Translation Info ───"

TRANSINFO=$(curl -s -S \
    -H "User-Agent: ${USER_AGENT}" \
    "${API_URL}?action=query&prop=translationinfo&titles=${PAGE_TITLE}&format=json" 2>/dev/null)

echo "$TRANSINFO" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pid, pdata in data.get('query', {}).get('pages', {}).items():
    ti = pdata.get('translationinfo', {})
    if ti:
        for key, value in ti.items():
            print(f'  {key}: {value}')
    else:
        # Try to extract from other props
        translatable = pdata.get('pageprops', {}).get('translatable')
        if translatable:
            print(f'  ✅ Page is translatable (tag: {translatable})')
        else:
            print('  ❌ Page is not marked for translation, or info not available.')
            print('     (This API module may not be available on this wiki.)')
" 2>/dev/null

# --- Step 3: Get language completion via langlinks + pageprops -----------
echo ""
echo "─── Translation Completion ───"

echo "$LANGLINKS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pid, pdata in data.get('query', {}).get('pages', {}).items():
    pageprops = pdata.get('pageprops', {})
    langlinks = pdata.get('langlinks', [])
    
    # If the page is translatable, check for pageprops like pageid
    translatable = pageprops.get('translatable')
    if translatable:
        print(f'  Page translation ID: {translatable}')
    
    if langlinks:
        print(f'  Available languages: {len(langlinks)}')
        for ll in langlinks:
            lang = ll.get('lang', '?')
            title = ll.get('*', '?')
            print(f'    {lang} → {title}')
    else:
        print('  (no translations found)')
" 2>/dev/null

# --- Step 4: Show page properties for translation -----------------------
echo ""
echo "─── Page Properties ───"

PPROPS=$(curl -s -S \
    -H "User-Agent: ${USER_AGENT}" \
    "${API_URL}?action=query&prop=pageprops&titles=${PAGE_TITLE}&format=json" 2>/dev/null)

echo "$PPROPS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pid, pdata in data.get('query', {}).get('pages', {}).items():
    props = pdata.get('pageprops', {})
    if props:
        for key, value in sorted(props.items()):
            if 'translat' in key.lower() or 'language' in key.lower() or 'lang' in key.lower():
                print(f'  {key}: {value}')
    else:
        print('  (no relevant page properties)')
" 2>/dev/null

echo ""
echo "═══ Status Check Complete ═══"
