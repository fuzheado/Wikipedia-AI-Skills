#!/usr/bin/env bash
# SPARQL Quick Query for Wikidata
# Runs a SPARQL query against the Wikidata Query Service and displays results.
# Usage:
#   ./sparql-query.sh "SELECT ?item ?itemLabel WHERE { ... }"
#   ./sparql-query.sh --examples

set -euo pipefail

UA="sparql-query-demo/1.0 (https://www.wikidata.org; demo@example.com) WikiSkills"
ENDPOINT="https://query.wikidata.org/sparql"

if [ $# -eq 0 ] || [ "$1" = "--help" ]; then
    echo "Usage:"
    echo "  $0 \"<SPARQL query>\"    — Run a SPARQL query"
    echo "  $0 --examples           — Show example queries"
    exit 0
fi

if [ "$1" = "--examples" ]; then
    echo "=== SPARQL Example Queries ==="
    echo ""
    echo "1. All museums in Paris:"
    echo '   SELECT ?museum ?museumLabel WHERE {
#     ?museum wdt:P31 wd:Q33506;
#             wdt:P131 wd:Q90.
#     SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
#   }'
    echo ""
    echo "2. Children of Albert Einstein (Q937):"
    echo '   SELECT ?child ?childLabel WHERE {
#     wd:Q937 wdt:P40 ?child.
#     SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
#   }'
    echo ""
    echo "3. All humans (Q5) with their occupation (P106) and date of birth (P569), limited to 10:"
    echo '   SELECT ?person ?personLabel ?occupationLabel ?dob WHERE {
#     ?person wdt:P31 wd:Q5;
#             wdt:P106 ?occupation;
#             wdt:P569 ?dob.
#     SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
#   }
#   LIMIT 10'
    exit 0
fi

QUERY="$*"

echo "=== SPARQL Query ==="
echo "$QUERY"
echo ""
echo "Running..."
echo ""

curl -s -H "User-Agent: $UA" -H "Accept: application/sparql-results+json" \
    "$ENDPOINT?format=json&query=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$QUERY'''))")" \
    | python3 -c "
import json, sys

data = json.load(sys.stdin)
head = data.get('head', {}).get('vars', [])
results = data.get('results', {}).get('bindings', [])

if not results:
    print('No results.')
    sys.exit(0)

print(f'Results: {len(results)}')
print(f'Columns: {\" | \".join(head)}')
print('-' * 60)

for row in results[:25]:
    parts = []
    for var in head:
        val = row.get(var, {})
        parts.append(val.get('value', '(none)'))
    print(' | '.join(parts))

if len(results) > 25:
    print(f'... and {len(results) - 25} more results (showing first 25)')
"
