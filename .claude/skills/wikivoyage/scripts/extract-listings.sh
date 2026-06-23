#!/usr/bin/env bash
# ============================================================================
# Wikivoyage Listing Extractor
# ============================================================================
# Fetches a Wikivoyage article and extracts all structured listings into JSON.
#
# Usage:
#   ./extract-listings.sh <article> [lang]
#
# Examples:
#   ./extract-listings.sh "Tokyo"
#   ./extract-listings.sh "Paris" fr
#   ./extract-listings.sh "Andorra" en
# ============================================================================

set -euo pipefail

ARTICLE="${1:-}"
LANG="${2:-en}"

if [ -z "$ARTICLE" ]; then
    echo "Usage: $0 <article> [lang]"
    echo ""
    echo "Fetches a Wikivoyage article and extracts all listings as JSON."
    echo ""
    echo "Examples:"
    echo "  $0 Tokyo"
    echo "  $0 Paris fr"
    exit 1
fi

API="https://${LANG}.wikivoyage.org/w/api.php"

# Fetch the page wikitext
echo "Fetching '${ARTICLE}' from ${LANG}.wikivoyage.org..." >&2
RESPONSE=$(curl -s -G "${API}" \
    --data-urlencode "action=parse" \
    --data-urlencode "page=${ARTICLE}" \
    --data-urlencode "prop=wikitext" \
    --data-urlencode "format=json" \
    -H "User-Agent: WvScript/1.0 (https://github.com/wikimedia/Wikipedia-AI-Skills)")

WIKITEXT=$(echo "$RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
try:
    print(data['parse']['wikitext']['*'])
except KeyError:
    print('ERROR: Could not fetch article. Check name and language.', file=sys.stderr)
    sys.exit(1)
")

# Extract all listing templates using a simple Python parser
python3 -c "
import re, sys, json

wikitext = sys.stdin.read()

# List of listing template names
listing_types = {'see', 'do', 'buy', 'eat', 'drink', 'sleep', 'listing', 'marker'}

# Find all {{template|param=value|...}} patterns
# This uses a simplified approach — for production use mwparserfromhell
pattern = r'\{\{(' + '|'.join(listing_types) + r')\s*\|([^}]+)\}\}'
matches = re.finditer(pattern, wikitext, re.IGNORECASE | re.DOTALL)

listings = []
for m in matches:
    ttype = m.group(1).lower()
    params_str = m.group(2)

    # Parse parameters (simple split by | — note: can break on nested templates)
    listing = {'_type': ttype}
    for param in params_str.split('|'):
        if '=' in param:
            key, value = param.split('=', 1)
            listing[key.strip()] = value.strip()

    listings.append(listing)

print(json.dumps(listings, indent=2, ensure_ascii=False))
" <<< "$WIKITEXT"
