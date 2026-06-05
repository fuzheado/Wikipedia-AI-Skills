#!/usr/bin/env bash
# Interactive Lift Wing playground — no arguments to memorize.
#
# Presents a menu of models, prompts for input, and shows formatted results.
#
# Usage:
#   bash scripts/playground.sh
#
# Requirements: curl, jq, python3 (for json.tool)

set -euo pipefail

BASE_URL="https://api.wikimedia.org/service/lw/inference/v1/models"
REC_URL="https://api.wikimedia.org/service/lw/recommendation/api/v1/translation"
USER_AGENT="LiftWingPlayground/1.0 (user@example.com) ContentGapResearch"
LANG="en"

# ── Color helpers ────────────────────────────────────────────────────────────
BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
RESET='\033[0m'

info()  { echo -e "${CYAN}${1}${RESET}"; }
ok()    { echo -e "${GREEN}✓ ${1}${RESET}"; }
warn()  { echo -e "${YELLOW}⚠ ${1}${RESET}"; }
err()   { echo -e "${RED}✗ ${1}${RESET}"; }
header(){ echo -e "\n${BOLD}${1}${RESET}\n"; }

# ── API call helper ──────────────────────────────────────────────────────────
call_model() {
    local model="$1" payload="$2"
    curl -s -X POST "${BASE_URL}/${model}:predict" \
        -H "Content-Type: application/json" \
        -H "User-Agent: $USER_AGENT" \
        -d "$payload"
}

call_recommendation() {
    local params="$1"
    curl -s "${REC_URL}?${params}" \
        -H "User-Agent: $USER_AGENT"
}

# ── Input helpers ────────────────────────────────────────────────────────────
get_rev_id() {
    local input
    while true; do
        echo -n "→ Enter a revision ID (or press Enter for 123456789): " >&2
        read -r input
        input="${input:-123456789}"
        if [[ "$input" =~ ^[0-9]+$ ]]; then
            echo "$input"
            return 0
        fi
        warn "That's not a number. Try again."
    done
}

get_page_title() {
    local input
    echo -n "→ Enter a page title (use underscores, e.g. Albert_Einstein): " >&2
    read -r input
    echo "${input:-Albert_Einstein}"
}

get_text() {
    local input
    echo -n "→ Enter some text to analyze: " >&2
    read -r input
    echo "${input:-Albert Einstein was a German-born theoretical physicist.}"
}

get_source_lang() {
    local input
    echo -n "→ Source language code [en]: " >&2
    read -r input
    echo "${input:-en}"
}

get_target_lang() {
    local input
    echo -n "→ Target language code [fr]: " >&2
    read -r input
    echo "${input:-fr}"
}

# ── Display formatters ───────────────────────────────────────────────────────
show_json() {
    echo "$1" | python3 -m json.tool 2>/dev/null || echo "$1"
}

show_revertrisk() {
    local json="$1"
    local pred
    pred=$(echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('output',{}).get('prediction','?'))" 2>/dev/null)
    local prob_true prob_false
    prob_true=$(echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('output',{}).get('probabilities',{}).get('true','?'))" 2>/dev/null)
    prob_false=$(echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('output',{}).get('probabilities',{}).get('false','?'))" 2>/dev/null)

    if [[ "$pred" == "True" ]]; then
        echo -e "${RED}🔴 RISKY — Revert probability: $(python3 -c "print(f'{$prob_true:.1%}')")${RESET}"
    elif [[ "$pred" == "False" ]]; then
        echo -e "${GREEN}🟢 SAFE — Revert probability: $(python3 -c "print(f'{$prob_true:.1%}')")${RESET}"
    fi
    echo "   Confidence: safe=$prob_false risky=$prob_true"
}

show_quality() {
    local json="$1"
    local grade pred
    grade=$(echo "$json" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for k,v in d.items():
    if isinstance(v,dict) and 'scores' in v:
        for r,s in v['scores'].items():
            print(s.get(list(s.keys())[0],{}).get('score',{}).get('prediction','?'))
" 2>/dev/null)
    echo "   Predicted grade: ${grade:-N/A}"
}

show_readability() {
    local json="$1"
    local score fk
    score=$(echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('output',{}).get('score','?'))" 2>/dev/null)
    fk=$(echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('output',{}).get('fk_score_proxy','?'))" 2>/dev/null)
    echo "   Readability score: $score"
    echo "   Grade level (approx): $fk"
}

show_topics() {
    local json="$1"
    echo "$json" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d.get('prediction',{}).get('results',[]):
    print(f\"   {r['topic']}: {r['score']:.1%}\")
" 2>/dev/null
}

show_langid() {
    local json="$1"
    local lang score name
    lang=$(echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('wikicode','?'))" 2>/dev/null)
    score=$(echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('score','?'))" 2>/dev/null)
    name=$(echo "$json" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('languagename','?'))" 2>/dev/null)
    echo "   Language: $name ($lang)"
    echo -e "   Confidence: ${GREEN}$(python3 -c "print(f'{float($score):.1%}')" 2>/dev/null)${RESET}"
}

# ── Model runners ────────────────────────────────────────────────────────────

run_revertrisk() {
    header "🛡️  Revert Risk"
    echo "Models: revertrisk-language-agnostic | revertrisk-multilingual | revertrisk-wikidata"
    echo -n "→ Which model? [language-agnostic]: " >&2
    read -r model_choice
    model_choice="${model_choice:-language-agnostic}"

    if [[ "$model_choice" == "wikidata" ]]; then
        local rev_id
        rev_id=$(get_rev_id)
        echo
        info "Scoring..."
        local resp
        resp=$(call_model "revertrisk-wikidata" "{\"rev_id\": $rev_id}")
        show_json "$resp" | head -15
        show_revertrisk "$resp"
    else
        local rev_id
        rev_id=$(get_rev_id)
        local model_name
        if [[ "$model_choice" == "multilingual" ]]; then
            model_name="revertrisk-multilingual"
        else
            model_name="revertrisk-language-agnostic"
        fi
        echo
        info "Scoring..."
        local resp
        resp=$(call_model "$model_name" "{\"rev_id\": $rev_id, \"lang\": \"$LANG\"}")
        show_json "$resp" | head -15
        show_revertrisk "$resp"
    fi
}

run_article_quality() {
    header "🏆 Article Quality"
    echo "1) Revscoring model (FA/GA/B/C/Start/Stub grades) — requires rev_id"
    echo "2) Modern model (continuous quality score) — requires rev_id"
    echo -n "→ Which one? [1]: " >&2
    read -r choice
    choice="${choice:-1}"

    local rev_id
    rev_id=$(get_rev_id)
    echo
    info "Scoring..."

    if [[ "$choice" == "2" ]]; then
        local resp
        resp=$(call_model "articlequality" "{\"rev_id\": $rev_id, \"lang\": \"$LANG\"}")
        show_json "$resp"
        local score
        score=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d.get('score',0):.3f}\")" 2>/dev/null)
        echo -e "   Quality score: ${BOLD}$score${RESET} (0-1, higher = better)"
    else
        local resp
        resp=$(call_model "enwiki-articlequality" "{\"rev_id\": $rev_id}")
        show_json "$resp" | head -20
        show_quality "$resp"
    fi
}

run_readability() {
    header "📖 Readability"
    local rev_id
    rev_id=$(get_rev_id)
    echo
    info "Scoring..."
    local resp
    resp=$(call_model "readability" "{\"rev_id\": $rev_id, \"lang\": \"$LANG\"}")
    show_json "$resp"
    show_readability "$resp"
}

run_topics() {
    header "🏷️  Topic Classification"
    local title
    title=$(get_page_title)
    echo
    info "Classifying..."
    local resp
    resp=$(call_model "outlink-topic-model" "{\"page_title\": \"$title\", \"lang\": \"$LANG\"}")
    show_json "$resp" | head -15
    echo
    show_topics "$resp"
}

run_reference() {
    header "🔗 Reference Quality"
    echo "1) Reference need (how much needs citations)"
    echo "2) Reference risk (citation quality)"
    echo -n "→ Which one? [1]: " >&2
    read -r choice
    choice="${choice:-1}"

    local rev_id
    rev_id=$(get_rev_id)
    echo
    info "Scoring..."

    if [[ "$choice" == "2" ]]; then
        local resp
        resp=$(call_model "reference-risk" "{\"rev_id\": $rev_id, \"lang\": \"$LANG\"}")
        show_json "$resp"
        local risk count
        risk=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('reference_risk_score','?'))" 2>/dev/null)
        count=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('reference_count','?'))" 2>/dev/null)
        echo "   Risk score: $risk | References found: $count"
    else
        local resp
        resp=$(call_model "reference-need" "{\"rev_id\": $rev_id, \"lang\": \"$LANG\"}")
        show_json "$resp"
        local score
        score=$(echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d.get('reference_need_score',0):.1%}\")" 2>/dev/null)
        echo "   Citation need: $score of text needs citations"
    fi
}

run_langid() {
    header "🌐 Language Identification"
    local text
    text=$(get_text)
    echo
    info "Identifying..."
    local resp
    resp=$(call_model "langid" "{\"text\": \"$text\"}")
    show_json "$resp"
    show_langid "$resp"
}

run_country() {
    header "🌍 Article Country"
    local title
    title=$(get_page_title)
    echo
    info "Predicting..."
    local resp
    resp=$(call_model "article-country" "{\"title\": \"$title\", \"lang\": \"$LANG\"}")
    echo "$resp" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d.get('prediction',{}).get('results',[]):
    print(f\"   {r['country']}: {r['score']:.0%}\")
" 2>/dev/null
}

run_translation() {
    header "🔁 Content Translation Recommendations"
    local source target seed
    source=$(get_source_lang)
    target=$(get_target_lang)
    echo -n "→ Seed article (optional): " >&2
    read -r seed
    echo
    info "Fetching recommendations..."

    local params="source=$source&target=$target&count=5"
    if [[ -n "$seed" ]]; then
        params="$params&seed=$seed"
    fi

    local resp
    resp=$(call_recommendation "$params")
    echo "$resp" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for r in d.get('recommendations',[]):
    print(f\"   • {r['title']} (langlinks: {r.get('langlinks_count','?')}, pageviews: {r.get('pageviews','?')})\")
" 2>/dev/null
}

# ── Main menu ────────────────────────────────────────────────────────────────

clear
header "🧠 Lift Wing ML Playground"
echo "Interactively explore Wikimedia's ML prediction models."
echo "All calls are anonymous (50k req/hr limit)."
echo

while true; do
    echo -e "${BOLD}Select a model to try:${RESET}"
    echo "  1) 🛡️  Revert Risk — score an edit's vandalism risk"
    echo "  2) 🏆 Article Quality — grade or score an article"
    echo "  3) 📖 Readability — measure how readable an article is"
    echo "  4) 🏷️  Topic Classification — what is this article about?"
    echo "  5) 🔗 Reference Quality — citation coverage and risk"
    echo "  6) 🌐 Language Identification — detect a text's language"
    echo "  7) 🌍 Article Country — which country is this about?"
    echo "  8) 🔁 Translation Recommendations — find articles to translate"
    echo "  0) Exit"
    echo
    echo -n "→ Choice [1-8 or 0]: " >&2
    read -r choice

    case "$choice" in
        1) run_revertrisk ;;
        2) run_article_quality ;;
        3) run_readability ;;
        4) run_topics ;;
        5) run_reference ;;
        6) run_langid ;;
        7) run_country ;;
        8) run_translation ;;
        0) echo; ok "Goodbye!"; exit 0 ;;
        *) warn "Invalid choice. Enter 1-8 or 0." ;;
    esac

    echo
    echo -n "Press Enter to continue..." >&2
    read -r
    clear
done
