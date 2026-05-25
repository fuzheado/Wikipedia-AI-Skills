#!/usr/bin/env bash
# Test that mwparserfromhell is installed and functional
# Usage: ./test-mwparser.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🔍 Testing mwparserfromhell installation...${NC}"

# Check if Python is available
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌ python3 not found. Please install Python 3.10+.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ python3 found: $(python3 --version)${NC}"

# Check if mwparserfromhell is installed
if ! python3 -c "import mwparserfromhell" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  mwparserfromhell not installed.${NC}"
    echo "   Install it: pip install mwparserfromhell"
    exit 1
fi
echo -e "${GREEN}✅ mwparserfromhell is installed${NC}"

# Run smoke test with sample wikitext
echo ""
echo -e "${CYAN}🧪 Running smoke test...${NC}"

# Write test script to temp file to avoid heredoc/shell quoting issues
TMPFILE=$(mktemp /tmp/mwparser-test-XXXXXX.py)
cat > "$TMPFILE" << 'PYEOF'
import mwparserfromhell

# Sample wikitext with templates, links, and formatting
wikitext = """\
{{Infobox person
| name = Alice Smith
| birth_date = {{birth date|1985|06|15}}
| occupation = {{plainlist|
* Engineer
* Author
}}
}}

'''Early life'''
Alice Smith was born in [[New York City|New York]] and studied at [[University of Cambridge|Cambridge]].
She is known for her work in <ref>{{cite web |url=https://example.com |title=Bio}}</ref>.
"""

code = mwparserfromhell.parse(wikitext)
print(f'   AST nodes: {len(code.nodes)}')
print(f'   Templates: {len(list(code.filter_templates()))}')
for t in code.filter_templates():
    print(f'     - {t.name}')
print(f'   Wikilinks: {len(list(code.filter_wikilinks()))}')
print(f'   Tags: {len(list(code.filter_tags()))}')

# Verify template parameter extraction
for t in code.filter_templates():
    if t.name.matches('Infobox person'):
        print(f'   Infobox name param: {t.get("name").value}')
        break

# Verify strip_code output
plain = code.strip_code()
print(f'   Plain text length: {len(plain)} chars')
print(f'   Plain text starts with: "{plain[:50]}..."')
print()
print('   All tests passed!')
PYEOF

python3 "$TMPFILE"
RESULT=$?
rm -f "$TMPFILE"

if [ "$RESULT" -eq 0 ]; then
    echo -e "${GREEN}✅ Smoke test passed${NC}"
else
    echo -e "${RED}❌ Smoke test failed${NC}"
    exit 1
fi
