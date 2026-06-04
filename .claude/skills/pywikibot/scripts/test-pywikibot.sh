#!/usr/bin/env bash
# test-pywikibot.sh — Verify Pywikibot installation and basic functionality
# Usage: bash test-pywikibot.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "  Pywikibot Installation Test"
echo "=========================================="
echo ""

# Step 1: Check Python
echo -n "1. Python 3.9+ "
PYTHON=$(command -v python3 || command -v python || echo "")
if [ -z "$PYTHON" ]; then
    echo -e "${RED}✗ Not found${NC}"
    echo "   Install Python 3.9+ from https://www.python.org/downloads/"
    exit 1
fi

PY_VER=$("$PYTHON" --version 2>&1 | grep -oP '\d+\.\d+')
MAJOR=$(echo "$PY_VER" | cut -d. -f1)
MINOR=$(echo "$PY_VER" | cut -d. -f2)

if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
    echo -e "${GREEN}✓${NC} ($("$PYTHON" --version))"
else
    echo -e "${RED}✗${NC} ($("$PYTHON" --version) — need 3.9+)"
    exit 1
fi

# Step 2: Check pywikibot installed
echo -n "2. Pywikibot installed "
if "$PYTHON" -c "import pywikibot; print(pywikibot.__version__)" 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC}"
else
    echo -e "${YELLOW}✗ Not found${NC}"
    echo "   Install: pip install pywikibot"
    echo "   Or clone: git clone https://gerrit.wikimedia.org/r/pywikibot/core.git"
fi

# Step 3: Check user-config.py
echo -n "3. user-config.py "
if [ -f "user-config.py" ]; then
    echo -e "${GREEN}✓${NC} (found in current dir)"
elif [ -f "$HOME/user-config.py" ]; then
    echo -e "${GREEN}✓${NC} (found in home dir)"
else
    echo -e "${YELLOW}✗ Not found${NC}"
    echo "   Create one or run: python -m pywikibot generate_user_files"
fi

# Step 4: Test read-only API access
echo -n "4. Read-only API access "
API_TEST=$("$PYTHON" -c "
import pywikibot
try:
    site = pywikibot.Site('en', 'wikipedia')
    page = pywikibot.Page(site, 'Wikipedia:Sandbox')
    print(f\"✓ (fetched {len(page.text)} bytes from '{page.title()}')\")
except Exception as e:
    print(f'✗ ({e})')
" 2>&1)

if echo "$API_TEST" | grep -q '✓'; then
    echo -e "   ${GREEN}$API_TEST${NC}"
else
    echo -e "   ${RED}$API_TEST${NC}"
fi

# Step 5: Bot framework
echo -n "5. Bot framework classes "
if "$PYTHON" -c "
from pywikibot.bot import BaseBot, ExistingPageBot, CurrentPageBot, ConfigParserBot
print('✓ (BaseBot, ExistingPageBot, CurrentPageBot, ConfigParserBot)')
" 2>/dev/null; then
    echo -e "   ${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Step 6: Wikidata support
echo -n "6. Wikidata support "
WD_TEST=$("$PYTHON" -c "
import pywikibot
try:
    repo = pywikibot.Site('wikidata', 'wikidata')
    item = pywikibot.ItemPage(repo, 'Q937')
    item.get()
    print(f\"✓ (read item Q937: {item.labels.get('en', '(no label)')})\")
except Exception as e:
    print(f'✗ ({e})')
" 2>&1)

if echo "$WD_TEST" | grep -q '✓'; then
    echo -e "   ${GREEN}$WD_TEST${NC}"
else
    echo -e "   ${RED}$WD_TEST${NC}"
fi

echo ""
echo "=========================================="
echo "  Test Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  - Run 'python pwb.py listpages -cat:Physics' (repo mode)"
echo "  - Run 'python pwb.py shell' for interactive mode"
echo "  - See the quick reference:"
echo "    python assets/pywikibot-quickref.py"
