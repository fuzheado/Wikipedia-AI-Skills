#!/usr/bin/env bash
# Fetch Multilingual Labels — Get Wikidata labels/descriptions in one or more languages
# Usage:
#   ./fetch-multilingual-labels.sh Q937                  — Labels in en (mul is added automatically)
#   ./fetch-multilingual-labels.sh Q937 'en|fr|de'       — Labels in multiple languages
#   ./fetch-multilingual-labels.sh Q937 'en|ar' --desc   — Include descriptions
#   ./fetch-multilingual-labels.sh Q937 en --aliases     — Include aliases
#   ./fetch-multilingual-labels.sh Q937,P31,P279 en      — Multiple entities
#   ./fetch-multilingual-labels.sh --help
#
# Language lists are pipe-separated: "en|fr|de". Commas are NOT a valid
# separator — wbgetentities warns and then silently returns ALL languages.
#
# `mul` (multiple languages) is appended automatically. Wikidata stores
# language-independent labels and aliases as `mul` default values, and a
# request that omits mul returns an empty labels object for items that have
# only a default (Q185, Q7186). See the wikidata skill, section
# "Getting Labels: `mul` Is Not Optional".
#
# Set WIKIMEDIA_USER_AGENT to your own contact string before batch use.

set -eo pipefail

UA="${WIKIMEDIA_USER_AGENT:-multilingual-labels/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; user@example.com) WMSkills}"

usage() {
    # Print only the leading comment block (the shebang is skipped and the
    # first non-comment line ends the block), so later #-comments stay out of
    # --help output.
    awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"
    exit 0
}

SHOW_DESC=false
SHOW_ALIASES=false

# Parse arguments
POSITIONAL=()
while [ $# -gt 0 ]; do
    case "$1" in
        --help|-h) usage ;;
        --desc|-d) SHOW_DESC=true; shift ;;
        --aliases|-a) SHOW_ALIASES=true; shift ;;
        --) shift; POSITIONAL+=("$@"); break ;;
        *) POSITIONAL+=("$1"); shift ;;
    esac
done

set -- "${POSITIONAL[@]}"

if [ $# -lt 1 ]; then
    echo "Error: Missing QID(s). Usage: $0 Q937 [langs]"
    exit 1
fi

QIDS="$1"
LANGS="${2:-en}"

# Normalize commas to pipes and always append `mul`. Commas are not accepted by
# wbgetentities (it warns, then ignores the filter), and a request without mul
# returns no labels at all for items that only carry a default value.
LANGS=$(printf '%s' "$LANGS" | tr ',' '|')
case "|${LANGS}|" in
    *"|mul|"*) ;;
    *) LANGS="${LANGS}|mul" ;;
esac

# Build the props parameter
PROPS="labels"
if [ "$SHOW_DESC" = true ]; then
    PROPS="${PROPS}|descriptions"
fi
if [ "$SHOW_ALIASES" = true ]; then
    PROPS="${PROPS}|aliases"
fi

API_URL="https://www.wikidata.org/w/api.php"

RESPONSE=$(curl -s -H "User-Agent: $UA" \
    "${API_URL}?action=wbgetentities&ids=${QIDS}&props=${PROPS}&languages=${LANGS}&format=json" \
    | python3 -c "
import json, sys

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    print('Error: API returned non-JSON response.')
    sys.exit(1)

entities = data.get('entities', {})
if not entities:
    print('No entities found.')
    sys.exit(1)

for qid, entity in entities.items():
    print(f'=== {qid} ===')
    labels = entity.get('labels', {})
    descs = entity.get('descriptions', {})
    aliases = entity.get('aliases', {})

    # Labels
    if labels:
        for lang, label in sorted(labels.items()):
            print(f'  [{lang}] label: {label[\"value\"]}')

    # Descriptions
    if descs:
        for lang, desc in sorted(descs.items()):
            print(f'  [{lang}] desc:  {desc[\"value\"]}')

    # Aliases
    if aliases:
        for lang, alias_list in sorted(aliases.items()):
            values = [a['value'] for a in alias_list]
            print(f'  [{lang}] aliases: {\", \".join(values)}')

    print()
")
echo "$RESPONSE"
