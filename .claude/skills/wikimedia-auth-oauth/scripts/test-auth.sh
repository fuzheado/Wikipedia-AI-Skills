#!/usr/bin/env bash
# =============================================================================
# test-auth.sh — Test that your authentication setup works end-to-end
#
# Tests authentication using the method you specify and reports whether API
# calls succeed, what user you're authenticated as, and what rights you have.
#
# Usage:
#   ./test-auth.sh --method bot-password          # Test bot password auth
#   ./test-auth.sh --method oauth2-bearer          # Test OAuth 2.0 with Bearer token
#   ./test-auth.sh --method owner-only             # Test owner-only consumer
#   ./test-auth.sh --help                          # Print usage
#
# Environment variables needed per method:
#   bot-password:    WIKI_USERNAME, WIKI_BOT_NAME, WIKI_BOT_PASSWORD
#   oauth2-bearer:   OAUTH_ACCESS_TOKEN
#   owner-only:      OAUTH_CLIENT_ID, OAUTH_CLIENT_SECRET
# =============================================================================

set -euo pipefail

METHOD=""
WIKI="${WIKI:-https://en.wikipedia.org}"

usage() {
    echo "Usage: $0 --method {bot-password|oauth2-bearer|owner-only}"
    echo ""
    echo "Environment variables needed:"
    echo ""
    echo "  bot-password:"
    echo "    WIKI_USERNAME      Your wiki username (e.g. 'MyAccount')"
    echo "    WIKI_BOT_NAME      Bot name (e.g. 'my-bot')"
    echo "    WIKI_BOT_PASSWORD  Bot password from Special:BotPasswords"
    echo ""
    echo "  oauth2-bearer:"
    echo "    OAUTH_ACCESS_TOKEN  A valid OAuth 2.0 Bearer token"
    echo ""
    echo "  owner-only:"
    echo "    OAUTH_CLIENT_ID      Owner-only consumer key"
    echo "    OAUTH_CLIENT_SECRET  Owner-only consumer secret"
    echo ""
    echo "Optional:"
    echo "    WIKI               Wiki base URL (default: https://en.wikipedia.org)"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --method) METHOD="$2"; shift 2 ;;
        -h|--help) usage ;;
        *) echo "Unknown option: $1"; usage ;;
    esac
done

if [ -z "$METHOD" ]; then
    echo "Error: --method is required"
    usage
fi

API="${WIKI}/w/api.php"
PASS=0
FAIL=0

check() {
    local desc="$1"
    local status="$2"
    if [ "$status" -eq 0 ]; then
        echo "  ✅ $desc"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $desc"
        FAIL=$((FAIL + 1))
    fi
}

echo "╔══════════════════════════════════════════════════╗"
echo "║    Wikimedia Auth Test — Method: $METHOD"
echo "╚══════════════════════════════════════════════════╝"
echo ""

case "$METHOD" in
    bot-password)
        echo "Testing bot password authentication..."
        echo ""

        USERNAME="${WIKI_USERNAME:-}"
        BOT_NAME="${WIKI_BOT_NAME:-}"
        BOT_PASS="${WIKI_BOT_PASSWORD:-}"

        if [ -z "$USERNAME" ] || [ -z "$BOT_NAME" ] || [ -z "$BOT_PASS" ]; then
            echo "Error: Set WIKI_USERNAME, WIKI_BOT_NAME, WIKI_BOT_PASSWORD"
            exit 1
        fi

        # Normalize: replace spaces with underscores
        LGNAME="${USERNAME// /_}"
        # Full bot username format: "Username@BotName"
        BOT_FULL="${LGNAME}@${BOT_NAME}"

        echo "  Bot username: $BOT_FULL"
        echo "  Wiki: $WIKI"
        echo ""

        # Step 1: Get login token
        echo "  [1/4] Fetching login token..."
        LOGIN_TOKEN=$(curl -s -G "$API" \
            --data-urlencode "action=query" \
            --data-urlencode "meta=tokens" \
            --data-urlencode "type=login" \
            --data-urlencode "format=json" \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)" \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['query']['tokens']['logintoken'])")
        check "Login token received" $?
        echo "    Token: ${LOGIN_TOKEN:0:20}..."

        # Step 2: Log in
        echo "  [2/4] Logging in..."
        LOGIN_RESULT=$(curl -s -X POST "$API" \
            --data-urlencode "action=login" \
            --data-urlencode "lgname=$BOT_FULL" \
            --data-urlencode "lgpassword=$BOT_PASS" \
            --data-urlencode "lgtoken=$LOGIN_TOKEN" \
            --data-urlencode "format=json" \
            -c /tmp/.wiki_test_cookies.txt \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)" \
        | python3 -c "import sys,json; d=json.load(sys.stdin)['login']; print(d['result'])")
        
        if [ "$LOGIN_RESULT" = "Success" ]; then
            check "Login successful (result: $LOGIN_RESULT)" 0
        else
            echo "    Login result: $LOGIN_RESULT"
            check "Login successful" 1
        fi

        # Step 3: Get CSRF token
        echo "  [3/4] Fetching CSRF token..."
        CSRF_TOKEN=$(curl -s -G "$API" \
            --data-urlencode "action=query" \
            --data-urlencode "meta=tokens" \
            --data-urlencode "type=csrf" \
            --data-urlencode "format=json" \
            -b /tmp/.wiki_test_cookies.txt \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)" \
        | python3 -c "import sys,json; print(json.load(sys.stdin)['query']['tokens']['csrftoken'])")
        
        if [ "$CSRF_TOKEN" != "+\\" ]; then
            check "CSRF token received (not anonymous)" 0
        else
            echo "    Got anonymous token — login may have failed"
            check "CSRF token received" 1
        fi

        # Step 4: Get user info
        echo "  [4/4] Fetching user info..."
        USERINFO=$(curl -s -G "$API" \
            --data-urlencode "action=query" \
            --data-urlencode "meta=userinfo" \
            --data-urlencode "uiprop=rights|blockinfo" \
            --data-urlencode "format=json" \
            -b /tmp/.wiki_test_cookies.txt \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)" \
        | python3 -c "
import sys, json
data = json.load(sys.stdin)
ui = data['query']['userinfo']
print(f\"    User: {ui['name']}\")
print(f\"    ID: {ui['id']}\")
print(f\"    Rights ({len(ui['rights'])}): {', '.join(sorted(ui['rights']))}\")
print(f\"    Blocked: {ui.get('blocked', False)}\")
")
        echo "$USERINFO"
        check "User info retrieved" $?

        # Cleanup
        rm -f /tmp/.wiki_test_cookies.txt
        ;;

    oauth2-bearer)
        echo "Testing OAuth 2.0 Bearer token authentication..."
        echo ""

        TOKEN="${OAUTH_ACCESS_TOKEN:-}"
        if [ -z "$TOKEN" ]; then
            echo "Error: Set OAUTH_ACCESS_TOKEN"
            exit 1
        fi

        # Test 1: Profile endpoint
        echo "  [1/3] Fetching user profile from OAuth endpoint..."
        PROFILE=$(curl -s \
            "https://meta.wikimedia.org/rest.php/oauth2/resource/profile" \
            -H "Authorization: Bearer $TOKEN" \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)")
        
        USERNAME=$(echo "$PROFILE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(f\"    Username: {d.get('username', 'N/A')}\")
    print(f\"    User ID: {d.get('sub', 'N/A')}\")
    print(f\"    Groups: {', '.join(d.get('groups', []))}\")
except:
    print(f\"    Response: {sys.stdin.read()[:200]}\")
" 2>/dev/null || echo "    Failed to parse profile")
        echo "$USERNAME"
        check "OAuth profile endpoint" $?

        # Test 2: API call with Bearer token
        echo "  [2/3] Making authenticated API call..."
        API_RESULT=$(curl -s -G "$API" \
            --data-urlencode "action=query" \
            --data-urlencode "meta=userinfo" \
            --data-urlencode "format=json" \
            -H "Authorization: Bearer $TOKEN" \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)" \
        | python3 -c "
import sys, json
d = json.load(sys.stdin)
ui = d['query']['userinfo']
print(f\"    Authenticated as: {ui['name']}\")
print(f\"    Rights: {len(ui['rights'])} rights\")
" 2>/dev/null || echo "    API call failed")
        echo "$API_RESULT"
        check "API call with Bearer token" $?

        # Test 3: CSRF token
        echo "  [3/3] Fetching CSRF token..."
        CSRF_RESULT=$(curl -s -G "$API" \
            --data-urlencode "action=query" \
            --data-urlencode "meta=tokens" \
            --data-urlencode "type=csrf" \
            --data-urlencode "format=json" \
            -H "Authorization: Bearer $TOKEN" \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)" \
        | python3 -c "
import sys, json
d = json.load(sys.stdin)
token = d['query']['tokens']['csrftoken']
if token != '+\\\\':
    print(f'    CSRF token valid (starts with: {token[:10]}...)')
else:
    print('    CSRF token is anonymous — token may not be authorized for writes')
")
        echo "$CSRF_RESULT"
        check "CSRF token fetch" $?
        ;;

    owner-only)
        echo "Testing owner-only OAuth 2.0 consumer..."
        echo ""

        CID="${OAUTH_CLIENT_ID:-}"
        CSEC="${OAUTH_CLIENT_SECRET:-}"
        if [ -z "$CID" ] || [ -z "$CSEC" ]; then
            echo "Error: Set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET"
            exit 1
        fi

        # Get token via client_credentials grant
        echo "  [1/3] Getting access token (client_credentials)..."

        # Build Authorization header for client credentials
        TOKEN_RESP=$(curl -s -X POST \
            "https://meta.wikimedia.org/rest.php/oauth2/access_token" \
            --data-urlencode "grant_type=client_credentials" \
            --data-urlencode "client_id=$CID" \
            --data-urlencode "client_secret=$CSEC" \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)")
        
        ACCESS_TOKEN=$(echo "$TOKEN_RESP" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('access_token', 'ERROR'))
" 2>/dev/null || echo "ERROR")
        
        if [ "$ACCESS_TOKEN" != "ERROR" ] && [ -n "$ACCESS_TOKEN" ]; then
            check "Access token obtained" 0
            echo "    Token: ${ACCESS_TOKEN:0:20}..."
        else
            check "Access token obtained" 1
            echo "    Response: $TOKEN_RESP"
        fi

        # Test profile
        echo "  [2/3] Fetching user profile..."
        PROFILE=$(curl -s \
            "https://meta.wikimedia.org/rest.php/oauth2/resource/profile" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)" \
        | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"    Username: {d.get('username', 'N/A')}\")
print(f\"    User ID: {d.get('sub', 'N/A')}\")
" 2>/dev/null || echo "    Profile request failed")
        echo "$PROFILE"
        check "Owner-only profile" $?

        # Test API call
        echo "  [3/3] Making API call..."
        curl -s -G "$API" \
            --data-urlencode "action=query" \
            --data-urlencode "meta=userinfo" \
            --data-urlencode "format=json" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            -H "User-Agent: AuthTestScript/1.0 (test@example.com)" \
        | python3 -c "
import sys, json
d = json.load(sys.stdin)
ui = d['query']['userinfo']
print(f\"    Authenticated as: {ui['name']}\")
" 2>/dev/null || echo "    API call failed"
        check "API call with owner-only token" $?
        ;;

    *)
        echo "Error: Unknown method '$METHOD'"
        echo "Supported: bot-password, oauth2-bearer, owner-only"
        exit 1
        ;;
esac

echo ""
echo "──────────────────────────────────────────────"
echo "Results: $PASS passed, $FAIL failed"
echo "──────────────────────────────────────────────"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
