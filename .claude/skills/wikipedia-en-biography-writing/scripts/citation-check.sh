#!/usr/bin/env bash
# Validate citations in a Wikipedia biography draft
# Usage: ./citation-check.sh <draft_file>

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

FILE="${1:-}"

if [ -z "$FILE" ]; then
    echo -e "${RED}No file provided${NC}"
    echo "   Usage: ./citation-check.sh draft.md"
    echo ""
    echo "   Reads a Wikipedia draft and checks citations for common issues:"
    echo "     - Citation count and reference list presence"
    echo "     - Templates missing URLs or access-dates"
    echo "     - Empty template fields"
    echo "     - Hallucination risk flags (citation needed, clarify, etc.)"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo -e "${RED}File not found: ${FILE}${NC}"
    exit 1
fi

CONTENT=$(cat "$FILE")

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Citation Validation Report${NC}"
echo -e "${CYAN}  File: ${FILE}${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Citation count
CITE_COUNT=$(grep -c '<ref' "$FILE" 2>/dev/null || true)
REF_LIST=$(grep -c '{{reflist}}' "$FILE" 2>/dev/null || true)

echo -e "  ${CYAN}Citation Counts:${NC}"
echo -e "    Inline refs found:  ${CITE_COUNT}"
if [ "$REF_LIST" -gt 0 ]; then
    echo -e "    Reference list:     ${GREEN}Present${NC}"
else
    echo -e "    Reference list:     ${RED}Missing (add {{reflist}})${NC}"
fi
echo ""

# Template checks using awk (compatible with macOS)
MISSING_URL=$(awk '
BEGIN { count=0; in_cite=0; has_url=0 }
/{{cite (web|news|journal)/ { in_cite=1; has_url=0 }
in_cite && /\|url[[:space:]]*=/ { has_url=1 }
/}}/ && in_cite { if (!has_url) count++; in_cite=0 }
END { print count+0 }
' "$FILE" 2>/dev/null || echo 0)

MISSING_AD=$(awk '
BEGIN { count=0; in_cite=0; has_ad=0 }
/{{cite (web|news)/ { in_cite=1; has_ad=0 }
in_cite && /\|access-date[[:space:]]*=/ { has_ad=1 }
/}}/ && in_cite { if (!has_ad) count++; in_cite=0 }
END { print count+0 }
' "$FILE" 2>/dev/null || echo 0)

EMPTY_FIELDS=$(awk '
BEGIN { count=0; in_cite=0 }
/{{cite / { in_cite=1 }
in_cite && /\|[_a-zA-Z-]+[[:space:]]*=[[:space:]]*(\||}})/ { count++ }
/}}/ { in_cite=0 }
END { print count+0 }
' "$FILE" 2>/dev/null || echo 0)

echo -e "  ${CYAN}Template Issues:${NC}"
echo -e "    Templates missing URL:        ${MISSING_URL} $([ "$MISSING_URL" -gt 0 ] && echo '⚠️' || echo '✅')"
echo -e "    Templates missing access-date: ${MISSING_AD} $([ "$MISSING_AD" -gt 0 ] && echo '⚠️' || echo '✅')"
echo -e "    Empty template fields:         ${EMPTY_FIELDS} $([ "$EMPTY_FIELDS" -gt 0 ] && echo '⚠️' || echo '✅')"
echo ""

# Hallucination risk flags
HAS_CN=$(grep -c '{{citation needed}}' "$FILE" 2>/dev/null || true)
HAS_WHEN=$(grep -c '{{when}}' "$FILE" 2>/dev/null || true)
HAS_CLARIFY=$(grep -c '{{clarify}}' "$FILE" 2>/dev/null || true)

echo -e "  ${CYAN}Hallucination Risk Flags:${NC}"
echo -e "    {{citation needed}}:     ${HAS_CN} $([ "$HAS_CN" -gt 0 ] && echo '⚠️  Flagged by author' || echo '✅')"
echo -e "    {{when}}:                ${HAS_WHEN} $([ "$HAS_WHEN" -gt 0 ] && echo '⚠️  Flagged by author' || echo '✅')"
echo -e "    {{clarify}}:             ${HAS_CLARIFY} $([ "$HAS_CLARIFY" -gt 0 ] && echo '⚠️  Flagged by author' || echo '✅')"
echo ""

# Summary
echo -e "  ${CYAN}Summary:${NC}"
if [ "$CITE_COUNT" -eq 0 ]; then
    echo -e "    ${RED}No citations found! This draft needs inline references.${NC}"
elif [ "$CITE_COUNT" -lt 3 ]; then
    echo -e "    ${YELLOW}Low citation count (${CITE_COUNT}). Consider adding more sources.${NC}"
elif [ "$MISSING_URL" -gt 0 ] || [ "$MISSING_AD" -gt 0 ]; then
    echo -e "    ${YELLOW}Citations present but some have incomplete metadata.${NC}"
else
    echo -e "    ${GREEN}Citations look well-formed.${NC}"
fi
echo ""
echo -e "${CYAN}========================================${NC}"
