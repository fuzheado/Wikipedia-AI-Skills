#!/bin/bash
# wd-vector-search.sh — Query the Wikidata Vector Database from the command line
#
# Finds Wikidata items (QIDs) and properties (PIDs) by semantic meaning,
# resolves each result to its label and description, and by default filters
# to only items that have a main-namespace Wikipedia article (not categories,
# templates, portals, etc.).
#
# Usage:
#   ./wd-vector-search.sh "query text"                         # Default: en articles, en labels
#   ./wd-vector-search.sh "query text" --K 10                  # Top 10 results
#   ./wd-vector-search.sh "query text" --lang fr               # French article filter, FR labels
#   ./wd-vector-search.sh "query text" --lang enwiki           # Explicit enwiki (same as en)
#   ./wd-vector-search.sh "query text" --lang enwikisource     # French Wikisource pages
#   ./wd-vector-search.sh "query text" --lang commonswiki      # Commons category names (not files)
#   ./wd-vector-search.sh "query text" --property              # Search properties (PIDs)
#   ./wd-vector-search.sh "query text" --no-filter             # All entities, no filtering
#   ./wd-vector-search.sh "query text" --similarity Q1,Q2      # Similarity score
#   ./wd-vector-search.sh "query text" --rerank                # Enable reranker (slower)
#   ./wd-vector-search.sh "query text" --json                  # Raw JSON output
#   ./wd-vector-search.sh --help | -h                          # This help text

set -euo pipefail

show_help() {
    cat <<'HELP'
wd-vector-search.sh — Query the Wikidata Vector Database

USAGE:
  ./wd-vector-search.sh <query> [options]

REQUIRED:
  query              Free-text description, label, or QID to search for

OPTIONS:
  --K N              Number of results to return (default: 5)
  --lang LANG        Language / project code (default: en)
                       Plain codes (en, fr, de, ar...) → {code}wiki filter
                       enwiki, frwikisource, commonswiki, enwiktionary...
                       commonswiki returns Commons category names (not files)
                       See --help lang for full list
  --property         Search Wikidata properties (PIDs) instead of items
  --similarity QIDS  Score query against specific comma-separated QIDs/PIDs
  --rerank           Enable cross-encoder reranker for better relevance (slower)
  --no-filter, --all Show ALL results, skip Wikipedia article filtering
  --json             Output raw JSON (for piping to jq, etc.)
  --help, -h         Show this help text

MORE:
  Full skill documentation: ../SKILL.md
  API docs:                https://wd-vectordb.wmcloud.org/docs
HELP
    exit 0
}

show_lang_help() {
    cat >&2 <<'LANGHELP'
--lang accepts language codes and full Wikimedia project codes:

  CODE              VECTOR DB    SITELINK FILTER     LABELS
  ──────────────────────────────────────────────────────────
  en  (default)     en           enwiki (mainspace)   English
  fr                fr           frwiki (mainspace)   French
  de                de           dewiki (mainspace)   German
  ar                ar           arwiki (mainspace)   Arabic
  enwiki            en           enwiki (mainspace)   English
  frwikisource      fr           frwikisource (any)   French
  enwiktionary      en           enwiktionary (any)   English
  commonswiki       en           commonswiki (any)    English    Category pages (not files)
  metawiki          en           metawiki (any)       English    All Meta pages
  wikidatawiki      en           wikidatawiki (any)   English    All Wikidata pages

  For language Wikipedias: only main-namespace articles pass.
  For other projects: any page with that sitelink is included.
  commonswiki sitelinks almost always point to Commons Category: pages.
  To find actual media files, search Commons directly (wikimedia-commons skill).
LANGHELP
}

BASE="https://wd-vectordb.wmcloud.org"
USER_AGENT="WikidataVectorSearchScript/1.0 (https://github.com/wikipedia-ai-skills; embedding@wikimedia.de) WikipediaAISkills"
K=5
RAW_LANG="en"
MODE="item"
QUERY=""
SIMILARITY=""
JSON=0
RERANK=0
NO_FILTER=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --K)          K="$2"; shift 2 ;;
        --lang)       RAW_LANG="$2"; shift 2 ;;
        --property)   MODE="property"; shift ;;
        --similarity) MODE="similarity"; SIMILARITY="$2"; shift 2 ;;
        --rerank)     RERANK=1; shift ;;
        --json)       JSON=1; shift ;;
        --no-filter|--all) NO_FILTER=1; shift ;;
        --help|-h)    show_help ;;
        --help-lang)  show_lang_help; exit 1 ;;
        -*)
            echo "Unknown option: $1" >&2
            echo "Try --help for usage." >&2
            exit 1 ;;
        *)  QUERY="$1"; shift ;;
    esac
done

if [[ -z "$QUERY" ]]; then
    echo "Error: no query provided." >&2
    echo "Usage: $0 \"query\" [options]" >&2
    echo "Try   $0 --help    for full usage." >&2
    exit 1
fi

# ── Parse --lang value into three components ───────────────────────
# VDB_LANG    — language code sent to the Vector DB API (en, fr, all, etc.)
# SITE_CODE   — sitelink project code for the filter (enwiki, frwikisource, etc.)
# LABEL_LANG  — language for label/description display
parse_lang() {
    local raw="$1"
    [[ "$raw" == *.* ]] && raw="${raw%%.*}"
    # Normalize the language code using Python/i18n_utils
    # Handles alias codes: zh-yue→yue, no→nb, bat-smg→sgs, etc.
    local normalized
    normalized=$(python3 -c "
import sys
sys.path.insert(0, '$(dirname "$0")/../../wikimedia-i18n-l10n-for-tools/assets')
try:
    from i18n_utils import normalize_language_code
    print(normalize_language_code('$raw'))
except ImportError:
    print('$raw')
" 2>/dev/null || echo "$raw")
    case "$normalized" in
        commons|commonswiki)
            VDB_LANG="en"; SITE_CODE="commonswiki";    LABEL_LANG="en" ;;
        meta|metawiki)
            VDB_LANG="en"; SITE_CODE="metawiki";       LABEL_LANG="en" ;;
        wikidata|wikidatawiki)
            VDB_LANG="en"; SITE_CODE="wikidatawiki";    LABEL_LANG="en" ;;
        mediawiki|mediawikiwiki)
            VDB_LANG="en"; SITE_CODE="mediawikiwiki";  LABEL_LANG="en" ;;
        species|specieswiki)
            VDB_LANG="en"; SITE_CODE="specieswiki";     LABEL_LANG="en" ;;
        *)
            if [[ "$normalized" =~ ^([a-z]{2,})(wiki|wikisource|wiktionary|wikivoyage|wikibooks|wikinews|wikiquote|wikiversity|wikimedia)$ ]]; then
                VDB_LANG="${BASH_REMATCH[1]}"
                SITE_CODE="$normalized"
                LABEL_LANG="$VDB_LANG"
            else
                VDB_LANG="$normalized"
                SITE_CODE="${normalized}wiki"
                LABEL_LANG="$VDB_LANG"
            fi
            ;;
    esac
}

parse_lang "$RAW_LANG"

# URL-encode the query
encoded_query=$(python3 -c "import sys,urllib.parse; print(urllib.parse.quote('$QUERY'))")

# ── Phase 1: Query the Vector Database ─────────────────────────────

echo "🔍  Searching Wikidata Vector Database..." >&2
echo "    Query: $QUERY" >&2
echo "    Mode:  $MODE" >&2
echo "    Lang:  $VDB_LANG (site filter: $SITE_CODE, labels: $LABEL_LANG)" >&2

case "$MODE" in
    item)
        url="${BASE}/item/query/?query=${encoded_query}&lang=${VDB_LANG}&K=${K}"
        [[ "$RERANK" == "1" ]] && url+="&rerank=true"
        FILTER_ARTICLES=1
        ;;
    property)
        url="${BASE}/property/query/?query=${encoded_query}&lang=${VDB_LANG}&K=${K}"
        [[ "$RERANK" == "1" ]] && url+="&rerank=true"
        FILTER_ARTICLES=0
        ;;
    similarity)
        url="${BASE}/similarity-score/?query=${encoded_query}&qid=${SIMILARITY}&lang=${VDB_LANG}"
        FILTER_ARTICLES=0
        ;;
esac

echo "    Count: $K" >&2
[[ "$FILTER_ARTICLES" == 1 && "$NO_FILTER" == 0 ]] && if [[ "$SITE_CODE" == "commonswiki" ]]; then
    echo "    Filter: $SITE_CODE category pages only (--no-filter for ALL)" >&2
elif [[ "$SITE_CODE" == *wiki && "$SITE_CODE" != *wikimedia && "$SITE_CODE" != *wikisource && "$SITE_CODE" != *wiktionary && "$SITE_CODE" != *wikiquote && "$SITE_CODE" != *wikibooks && "$SITE_CODE" != *wikiversity && "$SITE_CODE" != *wikivoyage && "$SITE_CODE" != *wikinews ]]; then
    echo "    Filter: $SITE_CODE articles only (--no-filter for ALL)" >&2
else
    echo "    Filter: $SITE_CODE pages only (--no-filter for ALL)" >&2
fi
echo "" >&2

response=$(curl -sL -H "User-Agent: $USER_AGENT" "$url")

# Validate JSON
if ! echo "$response" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    if isinstance(d, dict) and 'detail' in d:
        print(f'ERROR: {d[\"detail\"]}', file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
except json.JSONDecodeError:
    print('ERROR: Non-JSON response from server', file=sys.stderr)
    sys.exit(1)
"; then
    exit 1
fi

# Raw JSON mode
if [[ "$JSON" == 1 ]]; then
    echo "$response"
    exit 0
fi

# ── Phase 2: Filter by sitelink (enwiki / frwikisource / commonswiki) ────

if [[ "$FILTER_ARTICLES" == 1 && "$NO_FILTER" == 0 ]]; then
    filtered_response=$(echo "$response" | python3 -c "
import json, sys, urllib.request

user_agent = '$USER_AGENT'
results = json.load(sys.stdin)
site_code = '$SITE_CODE'

EXCLUDED_PREFIXES = (
    'Category:', 'Template:', 'Portal:', 'Wikipedia:', 'Help:',
    'Draft:', 'Module:', 'File:', 'MediaWiki:', 'Book:',
    'Education Program:', 'TimedText:', 'Gadget:', 'Gadget definition:'
)

non_article_wikis = {
    'commonswiki', 'metawiki', 'wikidatawiki', 'mediawikiwiki',
    'incubatorwiki', 'specieswiki', 'outreachwiki',
    'strategywiki', 'tenwiki', 'testwiki'
}
other_suffixes = (
    'wikisource', 'wiktionary', 'wikiquote', 'wikibooks',
    'wikiversity', 'wikivoyage', 'wikinews', 'wikimedia'
)
is_language_wikipedia = (
    site_code.endswith('wiki')
    and site_code not in non_article_wikis
    and not site_code.endswith(other_suffixes)
)

qids = [r['QID'] for r in results if 'QID' in r]
if not qids:
    json.dump([], sys.stdout)
    sys.exit(0)

api_url = (
    'https://www.wikidata.org/w/api.php'
    '?action=wbgetentities'
    '&props=sitelinks'
    f'&ids={\"|\".join(qids)}'
    f'&sitefilter={site_code}'
    '&format=json'
)
req = urllib.request.Request(api_url, headers={'User-Agent': user_agent})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
except Exception:
    json.dump(results, sys.stdout)
    sys.exit(0)

entities = data.get('entities', {})

if is_language_wikipedia:
    def passes_filter(sitelinks):
        site = sitelinks.get(site_code)
        if not site:
            return False
        return not site.get('title', '').startswith(EXCLUDED_PREFIXES)
    filter_label = 'mainspace'
else:
    def passes_filter(sitelinks):
        return site_code in sitelinks
    filter_label = 'any'

filtered = [r for r in results if passes_filter(entities.get(r['QID'], {}).get('sitelinks', {}))]

removed = len(results) - len(filtered)
if removed:
    print(f'   (removed {removed} entities without a {site_code} {filter_label} page)', file=sys.stderr)
    if not filtered:
        print(f'   All top results lacked a {site_code} page. Try --no-filter or increase --K.', file=sys.stderr)

json.dump(filtered, sys.stdout)
")
else
    filtered_response="$response"
fi

# ── Phase 3: Resolve labels + descriptions (batch) and display ─────

echo "$filtered_response" | python3 -c "
import json, sys, urllib.request

response_data = json.load(sys.stdin)

if len(response_data) == 0:
    print('No results found.')
    sys.exit(0)

user_agent = '$USER_AGENT'
label_lang = '$LABEL_LANG'
K = int('$K')

is_property = 'PID' in response_data[0] if response_data else False
id_key = 'PID' if is_property else 'QID'
type_label = 'Property' if is_property else 'Item'

# Batch-fetch labels + descriptions
ids_to_fetch = [r[id_key] for r in response_data[:K]]
entity_data = {}
try:
    batch_url = (
        'https://www.wikidata.org/w/api.php'
        '?action=wbgetentities'
        f'&ids={\"|\".join(ids_to_fetch)}'
        '&props=labels|descriptions'
        f'&languages={label_lang}|mul|en'
        '&format=json'
    )
    req = urllib.request.Request(batch_url, headers={'User-Agent': user_agent})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
        entity_data = data.get('entities', {})
    need_fallback = any(
        not entity.get('labels') for entity in entity_data.values()
        if isinstance(entity, dict)
    )
    if need_fallback:
        fallback_url = (
            'https://www.wikidata.org/w/api.php'
            '?action=wbgetentities'
            f'&ids={\"|\".join(ids_to_fetch)}'
            '&props=labels|descriptions'
            '&format=json'
        )
        req2 = urllib.request.Request(fallback_url, headers={'User-Agent': user_agent})
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            fallback_data = json.load(resp2)
            fallback_entities = fallback_data.get('entities', {})
        for eid, entity in entity_data.items():
            if not entity.get('labels') and eid in fallback_entities:
                fallback = fallback_entities[eid]
                if fallback.get('labels'):
                    entity['labels'] = fallback['labels']
                if not entity.get('descriptions') and fallback.get('descriptions'):
                    entity['descriptions'] = fallback['descriptions']
except Exception:
    pass

print(f'  {type_label:>8}  {\"Score\":>6}  {\"Label\":50s}  {\"Description\"}')
print('  ' + '-' * 100)

count = 0
for r in response_data[:K]:
    entity_id = r[id_key]
    score = r.get('similarity_score', 0)
    source = r.get('source', '')
    
    entity = entity_data.get(entity_id, {})
    labels = entity.get('labels', {})
    descriptions = entity.get('descriptions', {})
    
    label = '?'
    desc = ''
    if label_lang in labels:
        label = labels[label_lang]['value']
    elif 'en' in labels:
        label = labels['en']['value']
    elif labels:
        label = next(iter(labels.values()))['value']
    if label_lang in descriptions:
        desc = descriptions[label_lang]['value']
    elif 'en' in descriptions:
        desc = descriptions['en']['value']
    elif descriptions:
        desc = next(iter(descriptions.values()))['value']
    
    src_icon = ''
    if 'Vector Search' in source and 'Keyword Search' in source:
        src_icon = '🧠🔤'
    elif 'Vector Search' in source:
        src_icon = '🧠'
    elif 'Keyword Search' in source:
        src_icon = '🔤'
    
    desc_display = desc[:70] if desc else ''
    print(f'{src_icon} {entity_id:>6}  {score:.4f}  {label[:50]:50s}  {desc_display}')
    count += 1

if count == 0:
    print('  No results found.')
" 2>&1
