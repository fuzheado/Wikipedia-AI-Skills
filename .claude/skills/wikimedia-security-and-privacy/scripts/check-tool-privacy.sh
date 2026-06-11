#!/usr/bin/env bash
# =============================================================================
# check-tool-privacy.sh — Scan your tool's source for common privacy issues
#
# Scans a directory of source code for patterns that could cause privacy or
# security problems in Wikimedia tools. Reports findings with file:line.
#
# Usage:
#   ./check-tool-privacy.sh /path/to/tool/directory
#   ./check-tool-privacy.sh /path/to/tool/directory --verbose
#   ./check-tool-privacy.sh --help
# =============================================================================

set -euo pipefail

VERBOSE=0
SCAN_DIR=""

for arg in "$@"; do
    case "$arg" in
        --verbose|-v) VERBOSE=1 ;;
        -h|--help)
            echo "Usage: $0 [--verbose] <directory>"
            echo ""
            echo "Scans source code for common Wikimedia privacy/security issues:"
            echo ""
            echo "  HIGH priority (likely problems):"
            echo "    • Hardcoded credentials or tokens"
            echo "    • Raw IP logging in application code"
            echo "    • innerHTML with user-controlled data"
            echo "    • eval() in user-facing code"
            echo "    • Direct email/realname field exposure in API responses"
            echo ""
            echo "  MEDIUM priority (check manually):"
            echo "    • Logging API responses without sanitization"
            echo "    • Storing user data without expiration"
            echo "    • Missing Content-Type or CSP headers"
            echo "    • Raw HTML rendering of user input"
            echo ""
            echo "  SUGGESTION (good practices):"
            echo "    • Permission checks before edit actions"
            echo "    • User data deletion endpoints"
            echo "    - Data retention / cache TTL"
            exit 0
            ;;
        *)
            if [ -d "$arg" ]; then
                SCAN_DIR="$arg"
            else
                echo "Error: '$arg' is not a directory"
                exit 1
            fi
            ;;
    esac
done

if [ -z "$SCAN_DIR" ]; then
    echo "Error: specify a directory to scan"
    echo "Usage: $0 [--verbose] <directory>"
    exit 1
fi

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Privacy & Security Scan                                     ║"
echo "║  Directory: $SCAN_DIR"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

TOTAL_HIGH=0
TOTAL_MED=0
TOTAL_SUGGEST=0

# ── Helper: count and show matches ─────────────────────────────────────────

check_pattern() {
    local severity="$1"       # HIGH, MED, SUGGESTION
    local label="$2"
    local pattern="$3"
    local file_ext="$4"       # e.g. "*.py", "*.js", or "" for all
    
    local count=0
    local results=""
    
    if [ -n "$file_ext" ]; then
        results=$(grep -rn "$pattern" "$SCAN_DIR" --include="$file_ext" 2>/dev/null || true)
    else
        results=$(grep -rn "$pattern" "$SCAN_DIR" 2>/dev/null || true)
    fi
    
    if [ -n "$results" ]; then
        count=$(echo "$results" | wc -l | tr -d ' ')
        echo "  [$severity] $label ($count match(es))"
        if [ "$VERBOSE" -eq 1 ]; then
            echo "$results" | head -20 | while IFS= read -r line; do
                echo "    → $line"
            done
            if [ "$count" -gt 20 ]; then
                echo "    ... and $(($count - 20)) more"
            fi
        fi
        echo ""
    fi
    
    case "$severity" in
        HIGH) TOTAL_HIGH=$((TOTAL_HIGH + count)) ;;
        MED)  TOTAL_MED=$((TOTAL_MED + count)) ;;
        SUGGESTION) TOTAL_SUGGEST=$((TOTAL_SUGGEST + count)) ;;
    esac
}

# ── HIGH priority checks ───────────────────────────────────────────────────

echo "────────────────────────────────────────────"
echo "HIGH priority"
echo "────────────────────────────────────────────"

# Hardcoded secrets (Python, JS, shell)
check_pattern "HIGH" "Hardcoded 'client_secret' or 'secret'" \
    'client_secret|consumer_secret|CLIENT_SECRET|OAUTH_SECRET' "*.py"
check_pattern "HIGH" "Hardcoded 'password' or 'token' literal" \
    '(?<!os\.environ|os\.getenv|os\.env)\b(password|secret|token)\s*=\s*["'"'"']' "*.py"

# innerHTML with user-controlled data (JavaScript/gadgets)
check_pattern "HIGH" "innerHTML assignment (XSS risk)" \
    '\.innerHTML\s*=' "*.js"
check_pattern "HIGH" "innerHTML in .html() jQuery" \
    '\.html\s*\(' "*.js"

# eval
check_pattern "HIGH" "eval() usage (XSS risk)" \
    '\beval\s*\(' "*.js"

# Raw IP logging in application code (not in framework logs)
check_pattern "HIGH" "Logging request.remote_addr/request.ip" \
    '(remote_addr|request\.ip|request\.remote)' "*.py"

# Email/realname exposure
check_pattern "HIGH" "Returning email or realname in API" \
    '"(email|realname)"' "*.py"

echo ""

# ── MEDIUM priority checks ─────────────────────────────────────────────────

echo "────────────────────────────────────────────"
echo "MEDIUM priority — review manually"
echo "────────────────────────────────────────────"

# Logging full API responses
check_pattern "MED" "Logging full API response object" \
    '(logger\.(debug|info|warn)|print|printf).*response|result|data' "*.py"

# Storing data without TTL (caches without expiration)
check_pattern "MED" "Dictionary used as cache without TTL" \
    '\.cache\s*=\s*\{\}|_cache\s*=\s*\{\}' "*.py"

# Missing CSP headers (Flask)
check_pattern "MED" "Flask app without obvious Talisman/CSP" \
    '(Flask|flask)\s*\(' "*.py"

# Raw user content in responses
check_pattern "MED" "F-string or format with user content in response" \
    'f".*\{.*user\|username\|title' "*.py"
check_pattern "MED" "Returning request.form data directly" \
    'request\.(form|args|json)\[.*\]' "*.py"

echo ""

# ── SUGGESTION checks ──────────────────────────────────────────────────────

echo "────────────────────────────────────────────"
echo "SUGGESTION — consider adding"
echo "────────────────────────────────────────────"

# Missing permission checks
check_pattern "SUGGESTION" "Edit action without visible rights check" \
    'action.*edit|action=edit' "*.py"

# Missing data deletion endpoint
check_pattern "SUGGESTION" "No /delete-my-data endpoint found" \
    'delete.*data|delete.*account|remove.*data' "*.py"

# Cache without TTL
check_pattern "SUGGESTION" "Cache class without expiration logic" \
    'class.*[Cc]ache' "*.py"

echo ""
echo "────────────────────────────────────────────"
echo "Results: $TOTAL_HIGH HIGH, $TOTAL_MED MEDIUM, $TOTAL_SUGGEST suggestions"
echo "────────────────────────────────────────────"
echo ""
echo "Note: This is a heuristic scan. Every match should be manually reviewed."
echo "False positives are expected — verify each finding."
