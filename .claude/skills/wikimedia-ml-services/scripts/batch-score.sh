#!/usr/bin/env bash
# Batch score multiple revisions via Lift Wing with rate-limit awareness.
#
# Reads revision IDs or page titles (one per line) and scores each one.
#
# Usage:
#   echo "123456789" | ./batch-score.sh enwiki revertrisk-language-agnostic
#   cat revids.txt | ./batch-score.sh enwiki revertrisk-language-agnostic
#   ./batch-score.sh enwiki revertrisk-multilingual < revids.txt
#
# Input format (auto-detected):
#   - All digits → treated as revision IDs
#   - Contains non-digits → treated as page titles
#
# Options:
#   --delay <ms>    Delay between requests in milliseconds (default: 200)
#   --output <fmt>  Output format: json (default) or csv
#   --lang <code>   Language code (default: en)
#   --token <str>   OAuth token for authenticated requests

set -euo pipefail

WIKI="${1:?"Usage: $0 <wiki> <model> [options]"}"
MODEL="${2:?"Usage: $0 <wiki> <model> [options]"}"
DELAY=200
OUTPUT="json"
LANG="en"
TOKEN=""

shift 2

while [[ $# -gt 0 ]]; do
    case "$1" in
        --delay) DELAY="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --lang) LANG="$2"; shift 2 ;;
        --token) TOKEN="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

BASE_URL="https://api.wikimedia.org/service/lw/inference/v1/models"
USER_AGENT="LiftWingBatch/1.0 (user@example.com) ContentGapResearch"

# Determine if model is modern or Revscoring
is_modern_model() {
    local m="$1"
    case "$m" in
        revertrisk-*|outlink-topic-model|langid|readability|reference-need|reference-risk|article-descriptions|article-country|articlequality-language-agnostic|content-translation-recommendation)
            return 0 ;;
        *) return 1 ;;
    esac
}

if is_modern_model "$MODEL"; then
    FULL_MODEL="$MODEL"
else
    FULL_MODEL="${WIKI}-${MODEL}"
fi

URL="${BASE_URL}/${FULL_MODEL}:predict"

# Build auth header
AUTH_FLAGS=""
if [[ -n "$TOKEN" ]]; then
    AUTH_FLAGS="-H \"Authorization: Bearer $TOKEN\""
fi

count=0
errors=0

# CSV header
if [[ "$OUTPUT" == "csv" ]]; then
    echo "input,prediction,probability,error"
fi

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    line=$(echo "$line" | tr -d '[:space:]')

    # Determine if input is rev_id or page_title
    if [[ "$line" =~ ^[0-9]+$ ]]; then
        JSON_DATA=$(jq -n --argjson rev_id "$line" '{rev_id: $rev_id, lang: $lang}' --arg lang "$LANG")
    else
        JSON_DATA=$(jq -n --arg title "$line" '{page_title: $title, lang: $lang}' --arg lang "$LANG")
    fi

    echo "→ ($((count+1))) Scoring: $line" >&2

    RESPONSE=$(eval curl -s -X POST "$URL" \
        -H "Content-Type: application/json" \
        $AUTH_FLAGS \
        -H "User-Agent: $USER_AGENT" \
        -d "$JSON_DATA" 2>/dev/null) || {
        echo "⚠ Error: curl failed for $line" >&2
        errors=$((errors + 1))
        count=$((count + 1))
        continue
    }

    if [[ "$OUTPUT" == "json" ]]; then
        # Echo the input ID with the response as JSON
        echo "{\"input\": \"$line\", \"response\": $RESPONSE}"
    elif [[ "$OUTPUT" == "csv" ]]; then
        # Try to extract prediction and probability
        PRED=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    # Try modern model format first
    if 'prediction' in d:
        p = d['prediction']
        prob = d.get('probability', '')
    elif 'predictions' in d and d['predictions']:
        score = d['predictions'][0].get('score', {})
        p = score.get('prediction', '')
        prob = score.get('probability', {})
    else:
        p = ''
        prob = ''
    print(json.dumps({'prediction': str(p), 'probability': str(prob)}))
except Exception:
    print(json.dumps({'prediction': 'ERROR', 'probability': ''}))
" 2>/dev/null || echo '{"prediction": "PARSE_ERROR", "probability": ""}')
        PRED_VAL=$(echo "$PRED" | python3 -c "import sys,json; print(json.load(sys.stdin).get('prediction',''))")
        PROB_VAL=$(echo "$PRED" | python3 -c "import sys,json; print(json.load(sys.stdin).get('probability',''))")
        echo "$line,$PRED_VAL,$PROB_VAL,"
    fi

    count=$((count + 1))
    sleep "$(echo "scale=3; $DELAY / 1000" | bc)"
done

echo "✓ Done. $count scored, $errors errors." >&2
