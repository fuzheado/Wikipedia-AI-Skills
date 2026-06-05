#!/usr/bin/env bash
# Show a summary of all citations on a Wikipedia page.
#
# Usage:
#   ./citation-inspector.sh Albert_Einstein
#   ./citation-inspector.sh "Albert Einstein" --lang fr
#   ./citation-inspector.sh Albert_Einstein --json
#   ./citation-inspector.sh --lang fr Albert_Einstein

set -euo pipefail

LANG="en"
JSON=false
PAGE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --lang) LANG="$2"; shift 2 ;;
        --json) JSON=true; shift ;;
        -*) echo "Unknown option: $1"; exit 1 ;;
        *)
            if [[ -z "$PAGE" ]]; then
                PAGE="$1"
            else
                echo "Unexpected argument: $1"
                exit 1
            fi
            shift ;;
    esac
done

if [[ -z "$PAGE" ]]; then
    echo "Usage: $0 <page_title> [--lang LANG] [--json]"
    exit 1
fi

PAGE=$(echo "$PAGE" | tr ' ' '_')
DOMAIN="${LANG}.wikipedia.org"
UA="CitationInspector/1.0 (user@example.com) ContentGapResearch"

# Header goes to stderr so --json output is clean on stdout
echo "📋 Citation Inspector: $PAGE ($LANG)" >&2
echo >&2

WIKITEXT=$(curl -s "https://${DOMAIN}/w/api.php?action=parse&page=${PAGE}&prop=wikitext&format=json" \
  -H "User-Agent: $UA" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('parse', {}).get('wikitext', {}).get('*', ''))
")

if [[ -z "$WIKITEXT" ]]; then
    echo "❌ Could not fetch page '$PAGE'." >&2
    exit 1
fi

RESULT=$(echo "$WIKITEXT" | python3 -c "
import sys, re, json
from collections import Counter

wikitext = sys.stdin.read()
ref_tags = len(re.findall(r'<ref[^>]*>', wikitext))
named_refs = len(set(re.findall(r'name=\"([^\"]+)\"', wikitext)))
bare_urls = re.findall(r'<ref>(https?://[^\s<]+)</ref>', wikitext)
dead_links = len(re.findall(r'\{\{dead\s*link', wikitext, re.IGNORECASE))
failed_verif = len(re.findall(r'\{\{failed\s*verification', wikitext, re.IGNORECASE))
cn_tags = len(re.findall(r'\{\{citation\s*needed', wikitext, re.IGNORECASE))

cite_templates = Counter()
has_archive = 0
no_archive = 0
cite_doi = 0
has_access_date = 0

for m in re.finditer(r'\{\{(cite\s+\w+)([^}]*)\}\}', wikitext, re.IGNORECASE):
    tmpl = m.group(1).lower()
    cite_templates[tmpl] += 1
    params = m.group(2)
    if re.search(r'\|\s*url\s*=\s*https?://', params, re.IGNORECASE):
        if re.search(r'\|\s*archive-url\s*=\s*https?://', params, re.IGNORECASE):
            has_archive += 1
        else:
            no_archive += 1
    if re.search(r'\|\s*doi\s*=\s*10\.', params, re.IGNORECASE):
        cite_doi += 1
    if re.search(r'\|\s*access-date\s*=', params, re.IGNORECASE):
        has_access_date += 1

print(json.dumps({
    'total_ref_tags': ref_tags,
    'named_references': named_refs,
    'bare_urls': len(bare_urls),
    'dead_link_templates': dead_links,
    'failed_verification_templates': failed_verif,
    'citation_needed_tags': cn_tags,
    'citations_with_url': no_archive + has_archive,
    'citations_with_archive': has_archive,
    'citations_without_archive': no_archive,
    'citations_with_doi': cite_doi,
    'citations_with_access_date': has_access_date,
    'cite_template_breakdown': dict(cite_templates.most_common()),
}))
")

if [[ -z "$RESULT" ]]; then
    echo "  ⚠  Could not analyze citations." >&2
    exit 1
fi

if [[ "$JSON" == "true" ]]; then
    echo "$RESULT" | python3 -m json.tool
else
    REF_TAGS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['total_ref_tags'])")
    if [[ "$REF_TAGS" == "0" ]]; then
        echo "  ℹ️  No citation ref tags found on this page." >&2
        echo "  The page may not exist, may be a redirect, or may have no inline citations." >&2
        exit 0
    fi

    echo "$RESULT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  📝 Total ref tags:        {d[\"total_ref_tags\"]}')
print(f'  🔤 Named refs:            {d[\"named_references\"]}')
print(f'  🔗 Bare URLs:             {d[\"bare_urls\"]}')
print(f'  🗄️  With archive URL:      {d[\"citations_with_archive\"]}')
print(f'  📦 Without archive:        {d[\"citations_without_archive\"]}')
print(f'  🆔 With DOI:               {d[\"citations_with_doi\"]}')
print(f'  📅 With access-date:       {d[\"citations_with_access_date\"]}')
print(f'  🚩 Dead link templates:    {d[\"dead_link_templates\"]}')
print(f'  ❓ Failed verification:    {d[\"failed_verification_templates\"]}')
print(f'  ⚠️  Citation needed tags:   {d[\"citation_needed_tags\"]}')
print()
templates = d.get('cite_template_breakdown', {})
if templates:
    print('  Template breakdown:')
    for tmpl, count in templates.items():
        print(f'    {tmpl}: {count}')
"
fi
