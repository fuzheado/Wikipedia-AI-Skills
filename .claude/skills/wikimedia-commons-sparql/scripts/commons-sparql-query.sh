#!/usr/bin/env bash
# commons-sparql-query.sh — Run a SPARQL query against Commons structured data
#
# Usage:
#   ./commons-sparql-query.sh "SELECT ?file WHERE { ?file wdt:P180 wd:Q42 } LIMIT 10"
#   ./commons-sparql-query.sh --ql "SELECT ?file WHERE { ?file wdt:P180 wd:Q42 } LIMIT 10"
#   ./commons-sparql-query.sh --wcqs "SELECT ?file WHERE { ?file wdt:P180 wd:Q42 } LIMIT 10"
#
# Default endpoint: QLever (no auth required)
# Use --wcqs for the official endpoint (requires WCQS_AUTH_TOKEN env var)

set -euo pipefail

QL_URL="https://qlever.cs.uni-freiburg.de/api/wikimedia-commons"
WCQS_URL="https://commons-query.wikimedia.org/sparql"

endpoint="$QL_URL"
auth_cookie=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --ql)
            endpoint="$QL_URL"
            shift
            ;;
        --wcqs)
            endpoint="$WCQS_URL"
            if [[ -z "${WCQS_AUTH_TOKEN:-}" ]]; then
                echo "Error: WCQS_AUTH_TOKEN environment variable is not set." >&2
                echo "Set it to your wcqsOauth cookie value." >&2
                echo "See: https://commons.wikimedia.org/wiki/Commons:SPARQL_query_service/API_endpoint" >&2
                exit 1
            fi
            auth_cookie="Cookie: wcqsOauth=$WCQS_AUTH_TOKEN"
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--ql|--wcqs] \"SPARQL_QUERY\""
            echo ""
            echo "Endpoints:"
            echo "  --ql     QLever (default, no auth required)"
            echo "  --wcqs   Official WCQS (requires WCQS_AUTH_TOKEN env var)"
            echo ""
            echo "Examples:"
            echo "  $0 \"SELECT ?file WHERE { ?file wdt:P180 wd:Q42 } LIMIT 10\""
            echo "  $0 --wcqs \"SELECT ?file WHERE { ?file wdt:P180 wd:Q42 } LIMIT 10\""
            exit 0
            ;;
        *)
            break
            ;;
    esac
done

if [[ $# -lt 1 ]]; then
    echo "Error: No SPARQL query provided." >&2
    echo "Usage: $0 [--ql|--wcqs] \"SPARQL_QUERY\"" >&2
    exit 1
fi

query="$1"

echo "Endpoint: $endpoint" >&2
echo "Query: $query" >&2
echo "---" >&2

if [[ -n "$auth_cookie" ]]; then
    curl -s -X POST "$endpoint" \
        -H "Accept: application/sparql-results+json" \
        -H "User-Agent: CommonsSPARQLScript/1.0 (https://example.com; user@example.com)" \
        -H "$auth_cookie" \
        --cookie-jar /tmp/wcqs-cookies-$$.txt \
        -L \
        -d "query=$query" | python3 -m json.tool 2>/dev/null || curl -s -X POST "$endpoint" \
            -H "Accept: application/sparql-results+json" \
            -H "User-Agent: CommonsSPARQLScript/1.0 (https://example.com; user@example.com)" \
            -H "$auth_cookie" \
            --cookie-jar /tmp/wcqs-cookies-$$.txt \
            -L \
            -d "query=$query"
else
    curl -s -G "$endpoint" \
        --data-urlencode "query=$query" \
        -H "Accept: application/sparql-results+json" \
        -H "User-Agent: CommonsSPARQLScript/1.0 (https://example.com; user@example.com)" | python3 -m json.tool 2>/dev/null || curl -s -G "$endpoint" \
            --data-urlencode "query=$query" \
            -H "Accept: application/sparql-results+json" \
            -H "User-Agent: CommonsSPARQLScript/1.0 (https://example.com; user@example.com)"
fi
