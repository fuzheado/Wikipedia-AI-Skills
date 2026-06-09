#!/usr/bin/env bash
# ============================================================================
# navigation-inspector.sh — Analyze page navigation structure
#
# Traces the navigation template hierarchy, subpage structure, and link tree
# of a wiki page. Shows what menu templates are used, what /Sub templates
# would be loaded dynamically, and the subpage hierarchy.
#
# Usage:
#   ./scripts/navigation-inspector.sh "AvoinGLAM/Past activities" --wiki meta
#   ./scripts/navigation-inspector.sh "Project/Page" --links
#   ./scripts/navigation-inspector.sh "Project/Page/Subpage" --hierarchy
#   ./scripts/navigation-inspector.sh --help
# ============================================================================

set -euo pipefail

# --- Configuration ---------------------------------------------------------
WIKI="${WIKI:-https://meta.wikimedia.org}"
USER_AGENT="${WIKIMEDIA_USER_AGENT:-MediaWikiNavigationSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch}"

# --- Help ------------------------------------------------------------------
show_help() {
    cat <<EOF
Usage: $(basename "$0") [options] <page-title>

Analyze navigation structure of a wiki page.

ARGUMENTS:
  page-title        Title of the page to inspect

OPTIONS:
  --wiki WIKI       Wiki base URL (default: https://meta.wikimedia.org)
  --links           Show all navigational links on the page
  --hierarchy       Show subpage hierarchy tree
  --menu-only       Show only the menu templates
  --help            Show this help and exit

EXAMPLES:
  $(basename "$0") "AvoinGLAM/Past activities" --wiki meta
  $(basename "$0") "Project/Page" --links
  $(basename "$0") "Project/Page/Subpage" --hierarchy
EOF
    exit 0
}

# --- Parse arguments -------------------------------------------------------
PAGE_TITLE=""
SHOW_LINKS=false
SHOW_HIERARCHY=false
MENU_ONLY=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h) show_help ;;
        --wiki) WIKI="$2"; shift 2 ;;
        --links) SHOW_LINKS=true; shift ;;
        --hierarchy) SHOW_HIERARCHY=true; shift ;;
        --menu-only) MENU_ONLY=true; shift ;;
        *)
            if [[ -z "$PAGE_TITLE" ]]; then
                PAGE_TITLE="$1"
            else
                echo "Error: Unexpected argument: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "$PAGE_TITLE" ]]; then
    echo "Error: No page title specified." >&2
    exit 1
fi

API_URL="${WIKI}/w/api.php"

echo "🔍 Navigation Inspector"
echo "═══════════════════════════════════════════"
echo "  Page:  $PAGE_TITLE"
echo "  Wiki:  $WIKI"
echo ""

# --- Step 1: Page info ----------------------------------------------------
echo "─── Page Info ───"
PAGE_INFO=$(curl -s -S \
    -H "User-Agent: ${USER_AGENT}" \
    "${API_URL}?action=query&prop=info&titles=${PAGE_TITLE}&format=json" 2>/dev/null)

PAGE_ID=$(echo "$PAGE_INFO" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pid, pdata in data.get('query', {}).get('pages', {}).items():
    print(f\"{pdata.get('pageid', 'N/A')} | {pdata.get('length', 0)} bytes | exists: {pid != '-1'}\")
" 2>/dev/null)
echo "  Page ID / Size: $PAGE_ID"

# --- Step 2: Subpage hierarchy -------------------------------------------
echo ""
echo "─── Subpage Hierarchy ───"
echo "  Full:      $PAGE_TITLE"

# Parse hierarchy
python3 -c "
title = '$PAGE_TITLE'
parts = title.split('/')
print(f'  Root:      {parts[0]}')
for i in range(1, len(parts)):
    prefix = '/'.join(parts[:i+1])
    indent = '  ' + '  ' * i
    print(f'{indent}└── {parts[i]}  ({prefix})')
"

# --- Step 3: Templates used -----------------------------------------------
echo ""
echo "─── Templates on Page ───"

TEMPLATES=$(curl -s -S \
    -H "User-Agent: ${USER_AGENT}" \
    "${API_URL}?action=query&prop=templates&titles=${PAGE_TITLE}&tllimit=500&format=json" 2>/dev/null)

echo "$TEMPLATES" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pid, pdata in data.get('query', {}).get('pages', {}).items():
    templates = pdata.get('templates', [])
    for t in templates:
        ns = t.get('ns', 0)
        title = t.get('title', '')
        icon = '📄'
        if title.endswith('.css'):
            icon = '🎨'
        elif '/Sub' in title:
            icon = '🔗'
        elif 'navigation' in title.lower() or 'nav' in title.lower():
            icon = '🧭'
        elif 'box' in title.lower() or 'card' in title.lower():
            icon = '📦'
        print(f'  {icon} [{ns}] {title}')
    if not templates:
        print('  (no templates found)')
" 2>/dev/null

# --- Step 4: /Sub template detection ---------------------------------------
echo ""
echo "─── /Sub Template Detection ───"

python3 -c "
import json, urllib.request, urllib.parse
import sys

wiki = '$WIKI'
title = '$PAGE_TITLE'
ua = '$USER_AGENT'
api = f'{wiki}/w/api.php'

# Parse hierarchy to find potential /Sub templates
parts = title.split('/')
sub_candidates = []

# Check parent/Sub, grandparent/Sub, etc.
for i in range(len(parts), 0, -1):
    prefix = '/'.join(parts[:i])
    cand = f'Template:{prefix}/Sub'
    sub_candidates.append(cand)

# Also check just the root project
sub_candidates.append(f'Template:{parts[0]}/Sub')

for cand in sub_candidates:
    params = urllib.parse.urlencode({
        'action': 'query',
        'prop': 'info',
        'titles': cand,
        'format': 'json',
    }, quote_via=urllib.parse.quote)
    req = urllib.request.Request(f'{api}?{params}', headers={'User-Agent': ua})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            for pid, pdata in data.get('query', {}).get('pages', {}).items():
                if pid != '-1':
                    print(f'  ✅ EXISTS: {cand}')
                else:
                    print(f'  ❌ Not found: {cand}')
    except Exception as e:
        print(f'  ⚠️  Error checking {cand}: {e}')
" 2>/dev/null

# --- Step 5: Links (optional) ---------------------------------------------
if [[ "$SHOW_LINKS" == true ]]; then
    echo ""
    echo "─── Page Links ───"
    LINKS=$(curl -s -S \
        -H "User-Agent: ${USER_AGENT}" \
        "${API_URL}?action=query&prop=links&titles=${PAGE_TITLE}&pllimit=500&format=json" 2>/dev/null)
    
    echo "$LINKS" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pid, pdata in data.get('query', {}).get('pages', {}).items():
    links = pdata.get('links', [])
    # Sort by namespace
    ns_groups = {}
    for link in links:
        ns = link.get('ns', 0)
        ns_groups.setdefault(ns, []).append(link['title'])
    for ns, titles in sorted(ns_groups.items()):
        ns_name = {0: 'Main', 10: 'Template', 14: 'Category'}.get(ns, f'NS{ns}')
        print(f'  [{ns_name}]')
        for t in sorted(titles)[:20]:
            print(f'    → {t}')
        if len(titles) > 20:
            print(f'    ... and {len(titles) - 20} more')
" 2>/dev/null
fi

echo ""
echo "═══ Analysis Complete ═══"
