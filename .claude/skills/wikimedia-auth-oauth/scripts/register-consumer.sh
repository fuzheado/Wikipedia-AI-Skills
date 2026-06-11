#!/usr/bin/env bash
# =============================================================================
# register-consumer.sh — Interactive guide for registering an OAuth consumer
#
# This script doesn't register the consumer (that must be done via the web
# interface), but it guides you through the process and generates the
# cryptographic keys you'll need.
#
# Usage:
#   ./register-consumer.sh           # Interactive mode
#   ./register-consumer.sh --guide   # Print the guide only
# =============================================================================

set -euo pipefail

GUIDE_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --guide) GUIDE_ONLY=1 ;;
        -h|--help)
            echo "Usage: $0 [--guide]"
            echo "  --guide    Print the registration guide without prompts"
            exit 0
            ;;
    esac
done

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║      Wikimedia OAuth Consumer Registration Guide            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

if [ "$GUIDE_ONLY" -eq 0 ]; then
    echo "Let's determine what kind of consumer you need."
    echo ""
fi

echo "────────────────────────────────────────────────────────────────"
echo "STEP 1: Choose authentication method"
echo "────────────────────────────────────────────────────────────────"
echo ""
echo "  [1] Bot password — simplest, for personal scripts and bots"
echo "      → Create at: https://en.wikipedia.org/wiki/Special:BotPasswords"
echo "      → No registration needed, no admin approval"
echo "      → One bot password per script, per wiki"
echo ""
echo "  [2] OAuth 2.0 owner-only — for personal Toolforge tools"
echo "      → Register on meta with 'Owner-only' checked"
echo "      → Immediate approval, no admin needed"
echo "      → Uses client_credentials grant"
echo ""
echo "  [3] OAuth 2.0 public — for multi-user web apps"
echo "      → Register on meta as public consumer"
echo "      → Requires admin approval before other users can authorize"
echo "      → Uses authorization_code grant with PKCE if non-confidential"
echo ""
echo "  [4] OAuth 1.0a — legacy, only for maintaining existing tools"
echo "      → Register on meta (legacy protocol)"
echo "      → Requires request signing (HMAC-SHA1 or RSA-SHA1)"
echo ""

if [ "$GUIDE_ONLY" -eq 0 ]; then
    read -rp "Enter choice [1-4] (or press Enter to print full guide): " choice
    echo ""
fi

echo "────────────────────────────────────────────────────────────────"
echo "STEP 2: Register your consumer"
echo "────────────────────────────────────────────────────────────────"
echo ""
echo "  Go to: https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose"
echo ""
echo "  Fill in:"
echo "    • Application name — visible to users, be descriptive"
echo "    • Application description — what does your tool do?"
echo "    • Callback URL — for public OAuth: https://your-tool.example.org/callback"
echo "    • Contact email — so WMF can reach you about your tool"
echo ""
echo "  For OAuth 2.0, select:"
echo "    • OAuth protocol version: OAuth 2.0"
echo "    • Grants: minimum needed (see references/scopes-reference.md)"
echo "    • Owner-only? Check if personal tool; uncheck for public"
echo ""

if [ "$GUIDE_ONLY" -eq 0 ]; then
    read -rp "Press Enter to continue to Step 3... "
    echo ""
fi

echo "────────────────────────────────────────────────────────────────"
echo "STEP 3: Generate RSA keys (OAuth 1.0a only)"
echo "────────────────────────────────────────────────────────────────"
echo ""
echo "  If you chose OAuth 1.0a with RSA signing, generate a keypair:"
echo ""
echo "    # Generate private key"
echo "    openssl genrsa -out appkey.pem 4096"
echo ""
echo "    # Extract public key"
echo "    openssl rsa -in appkey.pem -pubout > appkey.pub"
echo ""
echo "  Paste the contents of appkey.pub into the"
echo "  'Public RSA key' field during registration."
echo ""

if [ "$GUIDE_ONLY" -eq 0 ]; then
    read -rp "Press Enter to continue to Step 4... "
    echo ""
fi

echo "────────────────────────────────────────────────────────────────"
echo "STEP 4: Test your consumer"
echo "────────────────────────────────────────────────────────────────"
echo ""
echo "  After registration, you'll receive:"
echo ""
echo "  For OAuth 2.0:"
echo "    • Client ID (public):  abc123..."
echo "    • Client Secret (secret): def456..."
echo ""
echo "  For OAuth 1.0a:"
echo "    • Consumer Token:  abc123..."
echo "    • Consumer Secret: def456..."
echo ""
echo "  Test with ./test-auth.sh (once created) or use:"
echo "    python3 assets/oauth2-client.py --test"
echo ""
echo "  Your own account can authorize immediately. Other users must"
echo "  wait for admin approval (can take hours to days)."
echo ""

if [ "$GUIDE_ONLY" -eq 0 ]; then
    read -rp "Press Enter to continue to Step 5... "
    echo ""
fi

echo "────────────────────────────────────────────────────────────────"
echo "STEP 5: Store credentials securely"
echo "────────────────────────────────────────────────────────────────"
echo ""
echo "  ❌ Never hardcode credentials in source code."
echo "  ❌ Never commit credentials to Git."
echo ""
echo "  ✅ Use environment variables:"
echo ""
echo "    export OAUTH_CLIENT_ID='abc123...'"
echo "    export OAUTH_CLIENT_SECRET='def456...'"
echo ""
echo "  ✅ On Toolforge, use:"
echo ""
echo "    become my-tool"
echo "    toolforge env set OAUTH_CLIENT_ID 'abc123...'"
echo "    toolforge env set OAUTH_CLIENT_SECRET 'def456...'"
echo ""
echo "  ✅ Use a .env file (gitignored) for local dev:"
echo ""
echo "    echo '.env' >> .gitignore"
echo "    # Then create .env with your credentials"
echo ""

if [ "$GUIDE_ONLY" -eq 1 ]; then
    echo "────────────────────────────────────────────────────────────────"
    echo "LINKS"
    echo "────────────────────────────────────────────────────────────────"
    echo ""
    echo "  Register consumer:  https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose"
    echo "  Bot passwords:      https://en.wikipedia.org/wiki/Special:BotPasswords"
    echo "  List consumers:     https://meta.wikimedia.org/wiki/Special:OAuthListConsumers"
    echo "  Manage consumers:   https://meta.wikimedia.org/wiki/Special:OAuthManageMyConsumers"
    echo "  OAuth docs:         https://www.mediawiki.org/wiki/OAuth/For_Developers"
    echo "  App guidelines:     https://meta.wikimedia.org/wiki/OAuth_app_guidelines"
    echo "  Beta cluster:       https://meta.wikimedia.beta.wmflabs.org"
    echo ""
fi
