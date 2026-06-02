#!/usr/bin/env bash
# Inspect wikitext: parse and report what mwparserfromhell sees
# Usage:
#   ./test-mwparser.sh              — run installation smoke test
#   ./test-mwparser.sh page.wikitext — inspect a wikitext file
#   ./test-mwparser.sh -             — read wikitext from stdin (pipe)
#
# Examples:
#   curl -s "https://en.wikipedia.org/w/index.php?title=Python_(programming_language)&action=raw" \
#     | ./test-mwparser.sh -
#
#   ./test-mwparser.sh article.wikitext

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

INSPECT_FILE="${1:-}"

# ── Prerequisite checks ──────────────────────────────────────

echo -e "${CYAN}🔍 Checking mwparserfromhell...${NC}"

if ! command -v python3 &>/dev/null; then
    echo -e "${RED}❌ python3 not found. Please install Python 3.10+.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ python3: $(python3 --version)${NC}"

if ! python3 -c "import mwparserfromhell" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  mwparserfromhell not installed.${NC}"
    echo "   Install: pip install mwparserfromhell"
    exit 1
fi
echo -e "${GREEN}✅ mwparserfromhell is installed${NC}"

# ── Mode: smoke test (no args) ────────────────────────────────

if [ -z "$INSPECT_FILE" ]; then
    echo ""
    echo -e "${CYAN}🧪 Running smoke test (no input file given)...${NC}"

    TMPFILE=$(mktemp /tmp/mwparser-test-XXXXXX.py)
    cat > "$TMPFILE" << 'PYEOF'
import mwparserfromhell

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

for t in code.filter_templates():
    if t.name.matches('Infobox person'):
        print(f'   Infobox name param: {t.get("name").value}')
        break

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
    exit 0
fi

# ── Mode: inspect wikitext input ──────────────────────────────

echo ""
echo -e "${CYAN}🔬 Inspecting wikitext...${NC}"

# Build the Python inspector script
TMPFILE=$(mktemp /tmp/mwparser-inspect-XXXXXX.py)

if [ "$INSPECT_FILE" = "-" ]; then
    echo -e "   Source: stdin (pipe mode)"
    # Write python script, then pipe wikitext alongside
    cat > "$TMPFILE" << 'PYEOF'
import sys, mwparserfromhell

wikitext = sys.stdin.read()
code = mwparserfromhell.parse(wikitext)

nodes = list(code.nodes)
templates = list(code.filter_templates())
wikilinks = list(code.filter_wikilinks())
extlinks = list(code.filter_external_links())
tags = list(code.filter_tags())
headings = list(code.filter_headings())
comments = list(code.filter_comments())

print(f"   Total AST nodes:          {len(nodes)}")
print(f"   Templates ({{{{...}}}}):       {len(templates)}")
print(f"   Wikilinks ([[...]]):      {len(wikilinks)}")
print(f"   External links ([...]):   {len(extlinks)}")
print(f"   Tags (<tag>):             {len(tags)}")
print(f"   Headings (==...==):       {len(headings)}")
print(f"   Comments (<!-- -->):      {len(comments)}")
print(f"   Raw wikitext length:      {len(wikitext)} chars")
print(f"   Plain text length:        {len(code.strip_code())} chars")
print()

# Report sections
if headings:
    print(f"── Sections ──")
    for h in headings:
        level = "=" * (h.level if hasattr(h, 'level') else 2)
        print(f"   {level} {h.title} {level}")
    print()

# Report templates (top 20)
if templates:
    print(f"── Templates (up to 20) ──")
    for t in templates[:20]:
        name = str(t.name).strip()
        params = list(t.params)
        if params:
            preview = "; ".join(f"{p.name.strip()}={str(p.value).strip()[:40]}" for p in params[:5])
            if len(params) > 5:
                preview += f" ... +{len(params)-5} more"
            print(f"   {{{{ {name} | {preview} }}}}")
        else:
            print(f"   {{{{ {name} }}}}")
    if len(templates) > 20:
        print(f"   ... and {len(templates) - 20} more")
    print()

# Report wikilinks (top 15)
if wikilinks:
    print(f"── Wikilinks (up to 15) ──")
    for link in wikilinks[:15]:
        title = str(link.title).strip()
        text = str(link.text).strip() if link.text else None
        if text and text != title.replace("_", " "):
            print(f"   [[ {title} | {text} ]]")
        else:
            print(f"   [[ {title} ]]")
    if len(wikilinks) > 15:
        print(f"   ... and {len(wikilinks) - 15} more")
    print()

# Report tags (top 10)
if tags:
    print(f"── Tags (up to 10) ──")
    for tag in tags[:10]:
        tag_name = tag.tag if hasattr(tag, 'tag') else "?"
        closing = " />" if getattr(tag, 'self_closing', False) else f"</{tag_name}>"
        print(f"   <{tag_name}{closing}")
    if len(tags) > 10:
        print(f"   ... and {len(tags) - 10} more")
    print()

# Potential issues
issues = []
if not templates and not wikilinks and not tags:
    issues.append("No templates, links, or tags found — may not be wikitext?")
if len(wikitext) > 500000:
    issues.append(f"Large page ({len(wikitext)} chars) — parsing may be slow")

if issues:
    print(f"── Notes ──")
    for issue in issues:
        print(f"   ⚠️  {issue}")
    print()

print("   ✅ Inspection complete")
PYEOF

    python3 "$TMPFILE"
    RESULT=$?
    rm -f "$TMPFILE"
    exit $RESULT
fi

# File mode
if [ ! -f "$INSPECT_FILE" ]; then
    echo -e "${RED}❌ File not found: ${INSPECT_FILE}${NC}"
    exit 1
fi

SIZE=$(wc -c < "$INSPECT_FILE")
echo -e "   Source: ${INSPECT_FILE} (${SIZE} bytes)"

cat > "$TMPFILE" << 'PYEOF'
import sys, mwparserfromhell

filepath = sys.argv[1]
with open(filepath, "r", encoding="utf-8") as f:
    wikitext = f.read()

code = mwparserfromhell.parse(wikitext)

nodes = list(code.nodes)
templates = list(code.filter_templates())
wikilinks = list(code.filter_wikilinks())
extlinks = list(code.filter_external_links())
tags = list(code.filter_tags())
headings = list(code.filter_headings())
comments = list(code.filter_comments())

print(f"   Total AST nodes:          {len(nodes)}")
print(f"   Templates ({{{{...}}}}):       {len(templates)}")
print(f"   Wikilinks ([[...]]):      {len(wikilinks)}")
print(f"   External links ([...]):   {len(extlinks)}")
print(f"   Tags (<tag>):             {len(tags)}")
print(f"   Headings (==...==):       {len(headings)}")
print(f"   Comments (<!-- -->):      {len(comments)}")
print(f"   Raw wikitext length:      {len(wikitext)} chars")
print(f"   Plain text length:        {len(code.strip_code())} chars")
print()

# Sections
if headings:
    print(f"── Sections ──")
    for h in headings:
        level = "=" * (h.level if hasattr(h, 'level') else 2)
        print(f"   {level} {h.title} {level}")
    print()

# Templates (top 20)
if templates:
    print(f"── Templates (up to 20) ──")
    for t in templates[:20]:
        name = str(t.name).strip()
        params = list(t.params)
        if params:
            preview = "; ".join(f"{p.name.strip()}={str(p.value).strip()[:40]}" for p in params[:5])
            if len(params) > 5:
                preview += f" ... +{len(params)-5} more"
            print(f"   {{{{ {name} | {preview} }}}}")
        else:
            print(f"   {{{{ {name} }}}}")
    if len(templates) > 20:
        print(f"   ... and {len(templates) - 20} more")
    print()

# Wikilinks (top 15)
if wikilinks:
    print(f"── Wikilinks (up to 15) ──")
    for link in wikilinks[:15]:
        title = str(link.title).strip()
        text = str(link.text).strip() if link.text else None
        if text and text != title.replace("_", " "):
            print(f"   [[ {title} | {text} ]]")
        else:
            print(f"   [[ {title} ]]")
    if len(wikilinks) > 15:
        print(f"   ... and {len(wikilinks) - 15} more")
    print()

# Tags (top 10)
if tags:
    print(f"── Tags (up to 10) ──")
    for tag in tags[:10]:
        tag_name = tag.tag if hasattr(tag, 'tag') else "?"
        closing = " />" if getattr(tag, 'self_closing', False) else f"</{tag_name}>"
        print(f"   <{tag_name}{closing}")
    if len(tags) > 10:
        print(f"   ... and {len(tags) - 10} more")
    print()

# Potential issues
issues = []
if not templates and not wikilinks and not tags:
    issues.append("No templates, links, or tags found — may not be wikitext?")
if len(wikitext) > 500000:
    issues.append(f"Large page ({len(wikitext)} chars) — parsing may be slow")
if len(wikitext) == 0:
    issues.append("Empty file")

if issues:
    print(f"── Notes ──")
    for issue in issues:
        print(f"   ⚠️  {issue}")
    print()

print("   ✅ Inspection complete")
PYEOF

python3 "$TMPFILE" "$INSPECT_FILE"
RESULT=$?
rm -f "$TMPFILE"
exit $RESULT
