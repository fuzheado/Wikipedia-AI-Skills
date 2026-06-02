#!/usr/bin/env bash
# Notability Assessment Tool for Wikipedia Biographies
# Usage: ./check-notability.sh [subject_name]
# Guides through Wikipedia's notability criteria and produces a structured report.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SUBJECT="${1:-}"
MODE="${2:-interactive}"

if [ -z "$SUBJECT" ]; then
    echo -e "${RED}❌ No subject provided${NC}"
    echo "   Usage: ./check-notability.sh \"Subject Name\""
    echo ""
    echo "   Runs through Wikipedia notability criteria and produces a report."
    echo "   Also works as a structured reference for the agent:"
    echo "     ./check-notability.sh --guide    (print the guide)"
    exit 1
fi

if [ "$SUBJECT" = "--guide" ]; then
    echo -e "${CYAN}📋 Notability Assessment Guide for English Wikipedia${NC}"
    echo ""
    echo "Applicable to biography subjects. Check each criterion."
    echo ""
    echo "A. GENERAL NOTABILITY (WP:GNG)"
    echo "   □ Significant coverage in multiple reliable sources"
    echo "   □ Sources are independent of the subject"
    echo "   □ Coverage has depth (not just brief mentions)"
    echo ""
    echo "B. ANYBIO (WP:ANYBIO) — Subject has:"
    echo "   □ Received a major award (Nobel, Pulitzer, Oscar, etc.)"
    echo "   □ Been inducted into a notable hall of fame"
    echo "   □ Held a highly notable position (head of state, etc.)"
    echo ""
    echo "C. ACADEMIC (WP:NACADEMIC) — For scholars/professors:"
    echo "   □ Major academic award (e.g., Fields Medal, Turing Award)"
    echo "   □ Highly cited research (h-index or impact)"
    echo "   □ Named chair or distinguished professorship"
    echo "   □ Editor-in-chief of a top journal in the field"
    echo "   □ Elected to a national academy (NAS, Royal Society, etc.)"
    echo ""
    echo "D. ARTIST/CREATIVE (WP:NARTIST / WP:NCREATIVE):"
    echo "   □ Work exhibited at major museums or galleries"
    echo "   □ Significant critical attention in reputable publications"
    echo "   □ Representation in notable galleries (for visual artists)"
    echo "   □ Subject of multiple independent reviews"
    echo "   □ Major award in the field"
    echo ""
    echo "E. DECISION"
    echo "   ✅ Likely notable — meets GNG or at least one SNG"
    echo "   ⚠️  Borderline — needs more sources"
    echo "   ❌ Not notable — does not meet any criteria"
    exit 0
fi

echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Notability Assessment${NC}"
echo -e "${CYAN}  Subject: ${SUBJECT}${NC}"
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo ""

PASS=0
NEEDS_REVIEW=0

check() {
    local num="$1"
    local criterion="$2"
    local details="$3"

    echo -e "  ${num}. ${criterion}"
    echo -e "     ${details}"
    echo -ne "     ${YELLOW}Result (y/n/?):${NC} "
    if [ "$MODE" = "noninteractive" ]; then
        echo "(needs user input)"
        NEEDS_REVIEW=$((NEEDS_REVIEW + 1))
    else
        read -r answer
        case "$answer" in
            y|Y|yes|Yes)
                echo -e "     ${GREEN}✅${NC}"
                PASS=$((PASS + 1))
                ;;
            n|N|no|No)
                echo -e "     ${RED}❌${NC}"
                ;;
            *)
                echo -e "     ${YELLOW}⚠️  Needs review${NC}"
                NEEDS_REVIEW=$((NEEDS_REVIEW + 1))
                ;;
        esac
    fi
    echo ""
}

echo -e "${CYAN}A. GENERAL NOTABILITY (WP:GNG)${NC}"
check "A1" "Significant coverage" "Are there multiple reliable sources with substantial discussion of the subject?"
check "A2" "Independent sources" "Are the sources independent of the subject (not interviews, press releases, or autobiographies)?"
check "A3" "Depth of coverage" "Do the sources provide depth, not just brief mentions or directory listings?"

echo -e "${CYAN}B. ANYBIO${NC}"
check "B1" "Major award" "Has the subject received a major award (Nobel, Pulitzer, Oscar, Academy Award, etc.)?"
check "B2" "Hall of fame" "Has the subject been inducted into a notable hall of fame?"

echo -e "${CYAN}C. ACADEMIC (if applicable)${NC}"
check "C1" "Academic awards" "Has the subject received a major academic award (Fields Medal, Turing Award, etc.)?"
check "C2" "Named chair" "Does the subject hold a named chair or distinguished professorship?"
check "C3" "National academy" "Is the subject elected to a national academy?"

echo -e "${CYAN}D. ARTIST/CREATIVE (if applicable)${NC}"
check "D1" "Museum exhibition" "Has the subject's work been exhibited at major museums?"
check "D2" "Critical attention" "Has the subject received significant critical attention in reputable publications?"

echo ""
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
echo -e "  Results for: ${SUBJECT}"
echo -e "  ✅ Confirmed:   ${PASS}"
echo -e "  ⚠️  Needs review: ${NEEDS_REVIEW}"
echo -e "  ❌ Not met:     $((10 - PASS - NEEDS_REVIEW))"
echo ""

if [ "$PASS" -ge 3 ]; then
    echo -e "  ${GREEN}Verdict: Likely notable ✅${NC}"
    echo -e "  Subject meets multiple notability criteria."
    echo -e "  Proceed with drafting."
elif [ "$PASS" -ge 1 ]; then
    echo -e "  ${YELLOW}Verdict: Borderline ⚠️${NC}"
    echo -e "  Subject meets some criteria but may need more sources."
    echo -e "  Flag to user before proceeding."
else
    echo -e "  ${RED}Verdict: Does not appear notable ❌${NC}"
    echo -e "  Subject does not meet WP:GNG or any subject-specific guideline."
    echo -e "  Recommend not proceeding without additional significant sources."
fi
echo -e "${CYAN}══════════════════════════════════════════════════${NC}"
