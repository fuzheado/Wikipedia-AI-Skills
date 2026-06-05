#!/usr/bin/env bash
# Score a single revision or page via the Lift Wing ML API.
#
# Usage:
#   ./score-revision.sh <wiki> <rev_id|page_title> <model> [lang]
#
# Examples:
#   # Score revert risk for an edit (modern model)
#   ./score-revision.sh enwiki 123456789 revertrisk-language-agnostic en
#
#   # Score article quality (frozen Revscoring model, uses rev_id)
#   ./score-revision.sh enwiki 123456789 enwiki-articlequality
#
#   # Score readability (modern model, uses page_title)
#   ./score-revision.sh enwiki Albert_Einstein readability en
#
#   # Topic classification (modern model, uses page_title)
#   ./score-revision.sh enwiki Douglas_Adams outlink-topic-model en
#
#   # Language identification
#   ./score-revision.sh enwiki Albert_Einstein langid en
#
#   # Authenticated (replace YOUR_TOKEN with your OAuth token)
#   TOKEN=your_token_here ./score-revision.sh enwiki 123456789 revertrisk-multilingual en

set -euo pipefail

# ── Parse arguments ──────────────────────────────────────────────────────────
WIKI="${1:?"Usage: $0 <wiki> <rev_id|page_title> <model> [lang]"}"
INPUT="${2:?"Usage: $0 <wiki> <rev_id|page_title> <model> [lang]"}"
MODEL="${3:?"Usage: $0 <wiki> <rev_id|page_title> <model> [lang]"}"
LANG="${4:-}"

BASE_URL="https://api.wikimedia.org/service/lw/inference/v1/models"
USER_AGENT="LiftWingCLI/1.0 (user@example.com) ContentGapResearch"

# ── Modern models that always need a lang parameter ──────────────────────────
NEEDS_LANG=(
    revertrisk-language-agnostic
    revertrisk-multilingual
    outlink-topic-model
    readability
    reference-need
    reference-risk
    langid
    article-descriptions
    article-country
    articlequality-language-agnostic
)

# ── Build the JSON payload ───────────────────────────────────────────────────
if [[ "$INPUT" =~ ^[0-9]+$ ]]; then
    JSON_DATA=$(jq -n --argjson rev_id "$INPUT" '{rev_id: $rev_id}')
else
    JSON_DATA=$(jq -n --arg title "$INPUT" '{page_title: $title}')
fi

# Default lang to "en" if the model needs it but none was provided
if [[ -z "$LANG" ]]; then
    for m in "${NEEDS_LANG[@]}"; do
        if [[ "$MODEL" == "$m" ]]; then
            LANG="en"
            echo "→ Defaulting lang to 'en' (required by model '$MODEL')" >&2
            break
        fi
    done
fi

if [[ -n "$LANG" ]]; then
    JSON_DATA=$(echo "$JSON_DATA" | jq --arg lang "$LANG" '. + {lang: $lang}')
fi

# ── Resolve model name ───────────────────────────────────────────────────────
is_modern_model() {
    local m="$1"
    # Models with hyphens that are NOT wiki-prefixed Revscoring models
    case "$m" in
        revertrisk-*|outlink-topic-model|langid|readability|\
        reference-need|reference-risk|article-descriptions|article-country|\
        articlequality-language-agnostic|content-translation-recommendation)
            return 0 ;;
        *)
            # If it already looks like wiki-model (has a hyphen before second word),
            # treat as fully qualified
            if [[ "$m" == *-* && "$m" != *-* ]]; then
                return 0
            fi
            return 1 ;;
    esac
}

if is_modern_model "$MODEL" || [[ "$MODEL" == *-* ]]; then
    FULL_MODEL="$MODEL"
else
    FULL_MODEL="${WIKI}-${MODEL}"
fi

URL="${BASE_URL}/${FULL_MODEL}:predict"

echo "→ POST $URL" >&2
echo "→ Data: $JSON_DATA" >&2

# ── Build curl args  (no eval!) ──────────────────────────────────────────────
CURL_ARGS=(
    -s
    -X POST
    "$URL"
    -H "Content-Type: application/json"
    -H "User-Agent: $USER_AGENT"
    -d "$JSON_DATA"
)

if [[ -n "${TOKEN:-}" ]]; then
    CURL_ARGS+=(-H "Authorization: Bearer $TOKEN")
    echo "→ Authenticated (TOKEN set)" >&2
fi

# ── Execute ──────────────────────────────────────────────────────────────────
RESPONSE=$(curl "${CURL_ARGS[@]}")
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
