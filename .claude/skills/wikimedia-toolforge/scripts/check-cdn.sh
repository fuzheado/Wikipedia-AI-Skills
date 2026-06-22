#!/usr/bin/env bash
# Verify a Wikimedia CDN asset URL is accessible
# Usage: ./check-cdn.sh <url_or_library> [version] [file]
#   url_or_library: Full URL or library name (e.g., jquery, d3, bootstrap)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

CDN_BASE="https://tools-static.wmflabs.org/cdnjs/ajax/libs"
API_BASE="https://api.cdnjs.com/libraries"

INPUT="${1:-}"

if [ -z "$INPUT" ]; then
    echo -e "${RED}❌ No URL or library name provided${NC}"
    echo "   Usage: ./check-cdn.sh <url>"
    echo "          ./check-cdn.sh <library> [version] [file]"
    echo ""
    echo "   Examples:"
    echo "     ./check-cdn.sh https://tools-static.wmflabs.org/cdnjs/ajax/libs/jquery/3.6.0/jquery.min.js"
    echo "     ./check-cdn.sh jquery 3.6.0 jquery.min.js"
    echo "     ./check-cdn.sh d3 7.9.0 d3.min.js"
    echo "     ./check-cdn.sh twitter-bootstrap 5.3.0 css/bootstrap.min.css"
    exit 1
fi

# If input is a full URL, check it directly
if [[ "$INPUT" == https://* ]]; then
    URL="$INPUT"
    echo -e "${CYAN}🔍 Checking CDN URL${NC}"
    echo -e "   URL: ${URL}"
else
    LIBRARY="$INPUT"
    VERSION="${2:-}"
    FILE="${3:-}"

    if [ -z "$VERSION" ]; then
        # Search for the library to find latest version
        echo -e "${CYAN}🔍 Searching for library '${LIBRARY}'...${NC}"
        SEARCH_URL="${API_BASE}?search=${LIBRARY}&fields=version,latest,name"
        RESP=$(curl -s -H "User-Agent: CDNCheck/1.0" --max-time 10 "$SEARCH_URL")
        
        LATEST=$(echo "$RESP" | python3 -c "
import json, sys
data = json.load(sys.stdin)
results = data.get('results', [])
if results:
    r = results[0]
    latest_url = r.get('latest', '')
    # Extract version from URL
    parts = latest_url.split('/')
    if 'ajax/libs' in latest_url:
        idx = parts.index('libs') + 2
    else:
        idx = -1
    ver = parts[idx] if idx > 0 and idx < len(parts) else r.get('version', '')
    print(f\"{r['name']}|{ver}\")
else:
    print('NOT_FOUND')
" 2>/dev/null)

        if [ "$LATEST" = "NOT_FOUND" ]; then
            echo -e "${RED}❌ Library '${LIBRARY}' not found on cdnjs.${NC}"
            echo "   Try a different name at https://api.cdnjs.com/libraries?search=${LIBRARY}"
            exit 1
        fi

        LIB_NAME=$(echo "$LATEST" | cut -d'|' -f1)
        VERSION=$(echo "$LATEST" | cut -d'|' -f2)
        echo -e "   Found: ${LIB_NAME} v${VERSION}"
    fi

    # If no file specified, guess based on library name
    if [ -z "$FILE" ]; then
        FILE="${LIBRARY}.min.js"
    fi

    URL="${CDN_BASE}/${LIBRARY}/${VERSION}/${FILE}"
    echo -e "   Constructed: ${URL}"
fi

echo ""

# Check the URL
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "User-Agent: CDNCheck/1.0 (toolforge; cdn-check)" \
    --max-time 10 \
    "$URL" 2>&1)

case "$HTTP_CODE" in
    200)
        echo -e "${GREEN}✅ Available (HTTP 200)${NC}"
        ;;
    301|302|307|308)
        echo -e "${YELLOW}⚠️  Redirect (HTTP ${HTTP_CODE})${NC}"
        FINAL_URL=$(curl -s -o /dev/null -w "%{redirect_url}" \
            -H "User-Agent: CDNCheck/1.0" --max-time 10 "$URL")
        echo -e "   → ${FINAL_URL}"
        ;;
    403|404)
        echo -e "${RED}❌ Not found (HTTP ${HTTP_CODE})${NC}"
        echo -e "   The asset may not be mirrored on the Toolforge CDN."
        echo -e "   Try a different version or file name."
        echo -e "   Search alternatives: https://api.cdnjs.com/libraries?search=${LIBRARY:-}"
        ;;
    *)
        echo -e "${RED}❌ Error (HTTP ${HTTP_CODE})${NC}"
        ;;
esac
