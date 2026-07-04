#!/usr/bin/env bash
# Wikidata Q/P ID Lookup
# Fetches label, description, and basic statements for a Wikidata item or property.
# Usage:
#   ./wikidata-lookup.sh Q937    — Look up item Q937 (Albert Einstein)
#   ./wikidata-lookup.sh P31     — Look up property P31 (instance of)

set -euo pipefail

UA="wikidata-lookup/1.0 (https://www.wikidata.org; demo@example.com) WikiSkills"

if [ $# -eq 0 ]; then
    echo "Usage: $0 <Q-ID or P-ID>"
    echo "  e.g.: $0 Q937   (look up Albert Einstein)"
    echo "  e.g.: $0 P31    (look up 'instance of' property)"
    exit 1
fi

ID="$1"

# Validate: must start with Q or P followed by digits
if ! echo "$ID" | grep -qE '^[QP][0-9]+$'; then
    echo "Error: ID must be a Q-number or P-number (e.g., Q937, P31)"
    exit 1
fi

echo "=== Wikidata Lookup: $ID ==="
echo ""

API="https://www.wikidata.org/w/api.php"
PARAMS="action=wbgetentities&ids=$ID&props=labels|descriptions|aliases|claims|sitelinks&languages=en|mul&format=json"

TMPFILE=$(mktemp /tmp/wikidata-lookup.XXXXXX)
trap 'rm -f "$TMPFILE"' EXIT

curl -s -w "\n%{http_code}" -H "User-Agent: $UA" "$API?$PARAMS" > "$TMPFILE" 2>&1 || true

HTTP_CODE=$(tail -1 "$TMPFILE")
sed '$d' "$TMPFILE" > "${TMPFILE}.body"

if [ "$HTTP_CODE" != "200" ]; then
    echo "Error: API returned HTTP $HTTP_CODE" >&2
    exit 1
fi

python3 -c "
import json, sys

with open('${TMPFILE}.body') as f:
    data = json.load(f)
entities = data.get('entities', {})
if not entities:
    print('Entity not found.')
    sys.exit(1)

eid, entity = next(iter(entities.items()))

# Labels
labels = entity.get('labels', {})
label_data = labels.get('en', {})
label = label_data.get('value', '(no label)')
print(f'  Label:       {label}')

# Description
descriptions = entity.get('descriptions', {})
desc_data = descriptions.get('en', {})
desc = desc_data.get('value', '(no description)')
print(f'  Description: {desc}')

# Aliases
aliases = entity.get('aliases', {})
alias_list = aliases.get('en', [])
if alias_list:
    alias_str = ', '.join(a.get('value', '') for a in alias_list)
    print(f'  Aliases:     {alias_str}')

# Claims (summarized)
claims = entity.get('claims', {})
print(f'  Statements:  {sum(len(v) for v in claims.values())} total')
print()
print('  --- First few statements ---')
count = 0
for prop, claim_list in claims.items():
    for claim in claim_list[:1]:  # show first value per property
        mainsnak = claim.get('mainsnak', {})
        datavalue = mainsnak.get('datavalue', {})
        value = datavalue.get('value', {})
        datatype = mainsnak.get('datatype', '')

        if datatype == 'wikibase-item':
            val_id = value.get('id', '?')
            print(f'  {prop} → {val_id}')
        elif datatype == 'time':
            print(f'  {prop} → {value.get(\"time\", \"?\")}')
        elif datatype == 'string':
            print(f'  {prop} → {value}')
        elif datatype == 'commonsMedia':
            print(f'  {prop} → File:{value}')
        elif datatype == 'globe-coordinate':
            lat = value.get('latitude', '?')
            lon = value.get('longitude', '?')
            print(f'  {prop} → ({lat}, {lon})')
        else:
            print(f'  {prop} → {value}')

        count += 1
        if count >= 8:
            break
    if count >= 8:
        break

# Sitelinks
sitelinks = entity.get('sitelinks', {})
if sitelinks:
    wiki_count = len(sitelinks)
    print(f'  Wikipedia links: {wiki_count} languages')
    if wiki_count <= 5:
        for site, link_data in sitelinks.items():
            print(f'    {site}: {link_data.get(\"title\", \"?\")}')
    else:
        sites = list(sitelinks.keys())[:5]
        for site in sites:
            print(f'    {site}: {sitelinks[site].get(\"title\", \"?\")}')
        print(f'    ... and {wiki_count - 5} more')
"
