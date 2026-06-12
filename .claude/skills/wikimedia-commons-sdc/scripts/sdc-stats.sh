#!/usr/bin/env bash
# sdc-stats.sh — Check SDC coverage for files in a Commons category
#
# Usage:
#   ./sdc-stats.sh "Category:Bridges in Paris"
#   ./sdc-stats.sh "Category:Media from iNaturalist" --csv

set -euo pipefail

show_usage() {
    cat >&2 <<EOF
Usage: $0 "Category:Name" [--csv]

Check what percentage of files in a Commons category have SDC statements.

Arguments:
  Category:Name   Commons category name (e.g., "Bridges in Paris")
  --csv           Output as CSV instead of human-readable

Examples:
  $0 "Category:Bridges in Paris"
  $0 "Category:Media from iNaturalist" --csv
EOF
    exit 1
}

# --- Guard: no args or --help ---
if [[ $# -eq 0 ]]; then
    show_usage
fi
for arg in "$@"; do
    if [[ "$arg" == "--help" || "$arg" == "-h" ]]; then
        show_usage
    fi
done

CATEGORY="$1"
shift
CSV_MODE=false
for arg in "$@"; do
    case "$arg" in
        --csv) CSV_MODE=true ;;
    esac
done

API="https://commons.wikimedia.org/w/api.php"
UA="SDCStats/1.0 (https://example.com; user@example.com)"
BATCH_SIZE=50

echo "Fetching files in $CATEGORY..." >&2

# Step 1: Get all files and their M IDs in the category
FILES=()
CMCONT=""
while :; do
    RESP=$(curl -s -G "$API" \
        -d "action=query" -d "list=categorymembers" \
        --data-urlencode "cmtitle=${CATEGORY}" \
        -d "cmtype=file" -d "cmlimit=max" -d "format=json" \
        ${CMCONT:+-d "cmcontinue=$CMCONT"} \
        -H "User-Agent: $UA")

    while IFS=$'\t' read -r pid title; do
        FILES+=("${pid}|${title}")
    done < <(echo "$RESP" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data['query']['categorymembers']:
    print(f\"{m['pageid']}\t{m['title']}\")
")

    CMCONT=$(echo "$RESP" | python3 -c "
import json, sys
data = json.load(sys.stdin)
c = data.get('continue', {})
print(c.get('cmcontinue', ''))
" 2>/dev/null || true)
    [[ -z "$CMCONT" ]] && break
done

TOTAL=${#FILES[@]}
echo "Found $TOTAL files." >&2

if [[ "$TOTAL" -eq 0 ]]; then
    echo "No files found."
    exit 0
fi

# Step 2: Batch-fetch SDC for all files
echo "Fetching SDC data..." >&2
HAS_CAPTION=0
HAS_DEPICTS=0
HAS_COPYRIGHT=0
HAS_LICENSE=0
HAS_CREATOR=0

for ((i=0; i<TOTAL; i+=BATCH_SIZE)); do
    BATCH=("${FILES[@]:i:BATCH_SIZE}")
    M_IDS=""
    for entry in "${BATCH[@]}"; do
        pid="${entry%%|*}"
        M_IDS="${M_IDS}${M_IDS:+,}M${pid}"
    done

    RESP=$(curl -s -G "$API" \
        -d "action=wbgetentities" -d "props=labels|claims" \
        --data-urlencode "ids=$M_IDS" -d "format=json" \
        -H "User-Agent: $UA")

    echo "$RESP" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for mid, ent in data.get('entities', {}).items():
    labels = ent.get('labels', {})
    claims = ent.get('claims', {})
    has_cap = 1 if labels else 0
    has_dep = 1 if 'P180' in claims else 0
    has_cop = 1 if 'P6216' in claims else 0
    has_lic = 1 if 'P275' in claims else 0
    has_cre = 1 if 'P170' in claims else 0
    print(f'{mid}\t{has_cap}\t{has_dep}\t{has_cop}\t{has_lic}\t{has_cre}')
" > /tmp/sdc-stats-$$.tmp

    while IFS=$'\t' read -r mid cap dep cop lic cre; do
        ((HAS_CAPTION += cap))
        ((HAS_DEPICTS += dep))
        ((HAS_COPYRIGHT += cop))
        ((HAS_LICENSE += lic))
        ((HAS_CREATOR += cre))
    done < /tmp/sdc-stats-$$.tmp

    echo "  Progress: $((i + ${#BATCH[@]}))/$TOTAL" >&2
done

rm -f /tmp/sdc-stats-$$.tmp

# Step 3: Output
if $CSV_MODE; then
    echo "category,total_files,with_captions,with_depicts,with_copyright,with_license,with_creator"
    echo "$CATEGORY,$TOTAL,$HAS_CAPTION,$HAS_DEPICTS,$HAS_COPYRIGHT,$HAS_LICENSE,$HAS_CREATOR"
else
    echo ""
    echo "=== SDC Coverage: $CATEGORY ==="
    echo "Total files:      $TOTAL"
    echo ""
    echo "With captions:    $HAS_CAPTION  ($(python3 -c "print(f'{$HAS_CAPTION/$TOTAL*100:.1f}%')"))"
    echo "With depicts:     $HAS_DEPICTS  ($(python3 -c "print(f'{$HAS_DEPICTS/$TOTAL*100:.1f}%')"))"
    echo "With copyright:   $HAS_COPYRIGHT  ($(python3 -c "print(f'{$HAS_COPYRIGHT/$TOTAL*100:.1f}%')"))"
    echo "With license:     $HAS_LICENSE  ($(python3 -c "print(f'{$HAS_LICENSE/$TOTAL*100:.1f}%')"))"
    echo "With creator:     $HAS_CREATOR  ($(python3 -c "print(f'{$HAS_CREATOR/$TOTAL*100:.1f}%')"))"
fi
