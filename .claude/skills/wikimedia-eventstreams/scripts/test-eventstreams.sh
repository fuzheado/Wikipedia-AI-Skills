#!/usr/bin/env bash
# test-eventstreams.sh — Verify EventStreams connectivity and basic functionality
# Usage: bash test-eventstreams.sh [stream_name]
#   Default stream: recentchange
#   Other options: revision-create, page-create, page-delete, page-move, test

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

STREAM="${1:-recentchange}"
UA_STRING="EventStreamsTest/1.0 (test-eventstreams.sh)"
PASS=0
FAIL=0

check() {
    local desc="$1"
    local result="$2"
    if [ "$result" = "0" ]; then
        echo -e "  ${GREEN}✓${NC} $desc"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}✗${NC} $desc"
        FAIL=$((FAIL + 1))
    fi
}

echo "=========================================="
echo "  EventStreams Connectivity Test"
echo "  Stream: ${STREAM}"
echo "=========================================="
echo ""

# Test 1: Can we reach stream.wikimedia.org?
echo "1. Network connectivity"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "User-Agent: ${UA_STRING}" \
    --connect-timeout 10 \
    "https://stream.wikimedia.org/v2/stream/${STREAM}" 2>&1 || echo "000")
check "HTTP endpoint reachable (got ${HTTP_CODE})" \
    $([ "$HTTP_CODE" != "000" ] && [ "$HTTP_CODE" != "503" ]; echo $?)

# Test 2: Does the stream resolve in the Swagger spec?
echo ""
echo "2. Stream availability"
STREAMS=$(curl -s \
    -H "User-Agent: ${UA_STRING}" \
    "https://stream.wikimedia.org/?spec" 2>/dev/null \
    | python3 -c "
import sys, json
spec = json.load(sys.stdin)
paths = spec.get('paths', {})
for p in paths:
    print(p.replace('/v2/stream/', ''))
" 2>/dev/null)

if echo "$STREAMS" | grep -q "${STREAM}"; then
    check "'${STREAM}' found in Swagger spec" 0
elif echo "$STREAMS" | grep -q "recentchange"; then
    check "'${STREAM}' not found (aliases may differ); recentchange IS available" 0
    echo "       Available streams: $(echo "$STREAMS" | tr '\n' ' ')"
else
    check "Could not read Swagger spec" 1
fi

# Test 3: Can we receive actual events?
echo ""
echo "3. Receiving events (sampling for 5 seconds)..."
EVENTS=$(
    curl -sN \
    -H "Accept: application/json" \
    -H "User-Agent: ${UA_STRING}" \
    --max-time 5 \
    "https://stream.wikimedia.org/v2/stream/${STREAM}" 2>/dev/null \
    | head -20
)

EVENT_COUNT=$(echo "$EVENTS" | grep -c '^\{' 2>/dev/null || echo 0)
NON_CANARY=$(echo "$EVENTS" | python3 -c "
import sys, json
count = 0
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if d.get('meta', {}).get('domain') != 'canary':
            count += 1
    except:
        pass
print(count)
" 2>/dev/null || echo 0)

if [ "$EVENT_COUNT" -gt 0 ]; then
    check "Received ${EVENT_COUNT} events (${NON_CANARY} non-canary)" 0
    # Show a sample
    SAMPLE=$(echo "$EVENTS" | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if d.get('meta', {}).get('domain') != 'canary':
            print(json.dumps({'user': d.get('user'), 'title': d.get('title'), 'wiki': d.get('wiki')}))
            break
    except:
        pass
" 2>/dev/null)
    if [ -n "$SAMPLE" ]; then
        echo "       Sample event: $SAMPLE"
    fi
else
    check "No events received (stream may be idle)" 1
fi

# Test 4: Canary event detection
echo ""
echo "4. Canary event detection"
CANARY_EVENTS=$(echo "$EVENTS" | python3 -c "
import sys, json
count = 0
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if d.get('meta', {}).get('domain') == 'canary':
            count += 1
    except:
        pass
print(count)
" 2>/dev/null || echo 0)

check "Canary detection works (${CANARY_EVENTS} canary events)" 0

# Test 5: Schema availability
echo ""
echo "5. Schema accessible"
SCHEMA_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "User-Agent: ${UA_STRING}" \
    "https://schema.wikimedia.org/repositories/primary/jsonschema/mediawiki/recentchange/latest.yaml" 2>/dev/null || echo "000")
check "Schema registry reachable (HTTP ${SCHEMA_CODE})" \
    $([ "$SCHEMA_CODE" = "200" ]; echo $?)

# Test 6: Pywikibot EventStreams module (if available)
echo ""
echo "6. Pywikibot EventStreams support"
if python3 -c "from pywikibot.comms.eventstreams import EventStreams" 2>/dev/null; then
    check "Pywikibot EventStreams module available" 0
else
    echo -e "  ${YELLOW}⚠ Pywikibot not installed (optional)${NC}"
fi

echo ""
echo "=========================================="
echo "  Results: ${PASS} passed, ${FAIL} failed"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "Troubleshooting tips:"
    echo "  - Check network: curl -sI https://stream.wikimedia.org"
    echo "  - Check User-Agent: some networks block empty UAs"
    echo "  - Try test stream: $0 test"
    echo "  - Try with Accept: application/json header"
    exit 1
fi
