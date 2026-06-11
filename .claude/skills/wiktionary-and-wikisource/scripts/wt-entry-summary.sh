#!/usr/bin/env bash
# =============================================================================
# wt-entry-summary.sh — Fetch a Wiktionary entry and show its structure
#
# Retrieves the wikitext for a word from a Wiktionary language edition and
# displays the language sections and part-of-speech structure found.
#
# Usage:
#   ./wt-entry-summary.sh <word> [lang]
#
# Examples:
#   ./wt-entry-summary.sh word          # English (default)
#   ./wt-entry-summary.sh mot fr        # French
#   ./wt-entry-summary.sh Haus de       # German
#   ./wt-entry-summary.sh --help        # This help
# =============================================================================

set -euo pipefail

WORD="${1:-}"
LANG="${2:-en}"

if [ -z "$WORD" ] || [ "$WORD" = "--help" ]; then
    echo "Usage: $0 <word> [lang]"
    echo ""
    echo "Fetch a Wiktionary entry and show its structure."
    echo ""
    echo "Arguments:"
    echo "  word         The word to look up"
    echo "  lang         Language edition (default: en)"
    echo ""
    echo "Examples:"
    echo "  $0 word              # English Wiktionary"
    echo "  $0 mot fr            # French Wiktionary"
    echo "  $0 Haus de           # German Wiktionary"
    echo "  $0 言葉 ja           # Japanese Wiktionary"
    exit 0
fi

API="https://${LANG}.wiktionary.org/w/api.php"
UA="WiktEntrySummary/1.0 (https://example.com; user@example.com)"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Wiktionary Entry Summary                                    ║"
echo "║  Word: $WORD"
echo "║  Wiki: ${LANG}.wiktionary.org"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Fetch wikitext
echo "Fetching page..."
WIKITEXT=$(curl -s -G "$API" \
    --data-urlencode "action=parse" \
    --data-urlencode "page=$WORD" \
    --data-urlencode "prop=wikitext" \
    --data-urlencode "format=json" \
    -H "User-Agent: $UA" \
    | python3 -c "
import sys, json, re
try:
    data = json.load(sys.stdin)
    if 'parse' in data and 'wikitext' in data['parse']:
        wt = data['parse']['wikitext']['*']
        print(wt)
    else:
        error = data.get('error', {}).get('info', 'Unknown error')
        print(f'ERROR: {error}')
except json.JSONDecodeError:
    print('ERROR: Failed to parse API response')
")

if [[ "$WIKITEXT" == ERROR:* ]]; then
    echo "❌ $WIKITEXT"
    exit 1
fi

# Extract language sections
echo ""
echo "────────────────────────────────────────────"
echo "Language sections found:"
echo "────────────────────────────────────────────"
echo "$WIKITEXT" | python3 -c "
import sys, re

text = sys.stdin.read()

# Split on ---- (5 hyphens)
sections = re.split(r'^-{5,}\s*$', text, flags=re.MULTILINE)

found_langs = []
for section in sections:
    m = re.search(r'^==([^=]+)==', section, re.MULTILINE)
    if m:
        lang = m.group(1).strip()
        # Count part-of-speech headings
        poses = re.findall(r'^===([^=]+)===', section, re.MULTILINE)
        pos_list = ', '.join(poses[:5])
        if len(poses) > 5:
            pos_list += f' ... and {len(poses)-5} more'
        
        # Count definitions
        defs = len(re.findall(r'^#\s', section, re.MULTILINE))
        examples = len(re.findall(r'^#:\s', section, re.MULTILINE))
        
        print(f'  • {lang}')
        print(f'    POS sections ({len(poses)}): {pos_list}')
        print(f'    Definitions: {defs}, Examples: {examples}')
        print()
        found_langs.append(lang)

if not found_langs:
    print('  No language sections found.')
    print()
    print('Raw wikitext first 500 chars:')
    print(text[:500])
"

echo "────────────────────────────────────────────"
echo "Templates used:"
echo "────────────────────────────────────────────"
echo "$WIKITEXT" | python3 -c "
import sys, re
text = sys.stdin.read()
templates = set(re.findall(r'\{\{([a-zA-Z][a-zA-Z0-9 -]+)', text))
sorted_t = sorted(templates)[:20]
for t in sorted_t:
    print(f'  • {t}')
if len(templates) > 20:
    print(f'  ... and {len(templates)-20} more')
"

# Show interwiki links if available
echo ""
echo "────────────────────────────────────────────"
echo "Interwiki links (same word in other languages):"
echo "────────────────────────────────────────────"
curl -s -G "$API" \
    --data-urlencode "action=query" \
    --data-urlencode "titles=$WORD" \
    --data-urlencode "prop=langlinks" \
    --data-urlencode "lllimit=20" \
    --data-urlencode "format=json" \
    -H "User-Agent: $UA" \
    | python3 -c "
import sys, json
data = json.load(sys.stdin)
pages = data.get('query', {}).get('pages', {})
for pid, pdata in pages.items():
    if pid == '-1':
        print('  Word not found')
        continue
    langlinks = pdata.get('langlinks', [])
    for link in langlinks[:20]:
        print(f\"  {link['lang']}: {link.get('*', '?')}\")
    if len(langlinks) > 20:
        print(f'  ... and {len(langlinks)-20} more')
    if not langlinks:
        print('  No interwiki links')
"

echo ""
echo "Done."
