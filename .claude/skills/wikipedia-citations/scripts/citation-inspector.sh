#!/usr/bin/env bash
# Show a summary of all citations on a Wikipedia page.
#
# Usage:
#   ./citation-inspector.sh Albert_Einstein
#   ./citation-inspector.sh "Albert Einstein" --lang fr
#   ./citation-inspector.sh Albert_Einstein --json

set -euo pipefail

PAGE="${1:?"Usage: $0 <page_title> [--lang LANG] [--json]"}"
LANG="en"
JSON=false

shift
while [[ $# -gt 0 ]]; do
    case "$1" in
        --lang) LANG="$2"; shift 2 ;;
        --json) JSON=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

PAGE=$(echo "$PAGE" | tr ' ' '_')
DOMAIN="${LANG}.wikipedia.org"
USER_AGENT="CitationInspector/1.0 (user@example.com) ContentGapResearch"

echo "📋 Citation Inspector: $PAGE ($LANG)"
echo

# Fetch page wikitext
WIKITEXT=$(curl -s "https://${DOMAIN}/w/api.php?action=parse&page=${PAGE}&prop=wikitext&format=json" \
  -H "User-Agent: $USER_AGENT" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('parse', {}).get('wikitext', {}).get('*', ''))
" 2>/dev/null)

if [[ -z "$WIKITEXT" ]]; then
    echo "❌ Could not fetch page."
    exit 1
fi

# Analyze citations
python3 -c "
import sys, re, json
from collections import Counter

wikitext = sys.stdin

# Count ref tags
ref_tags = len(re.findall(r'<ref[^>]*>', wikitext))
named_refs = len(set(re.findall(r'name=\"([^\"]+)\"', wikitext)))

# Find all citation templates
cite_templates = Counter()
cite_urls = []
cite_doi = []
bare_urls = []
has_archive = 0
no_archive = 0
has_access_date = 0

for m in re.finditer(r'\{\{(cite\s+\w+)([^}]*)\}\}', wikitext, re.IGNORECASE):
    tmpl = m.group(1).lower()
    cite_templates[tmpl] += 1
    params = m.group(2)
    
    if re.search(r'\|?\s*url\s*=\s*https?://', params, re.IGNORECASE):
        cite_urls.append(m.group(0))
        if re.search(r'\|?\s*archive-url\s*=\s*https?://', params, re.IGNORECASE):
            has_archive += 1
        else:
            no_archive += 1
    if re.search(r'\|?\s*doi\s*=\s*10\.', params, re.IGNORECASE):
        cite_doi.append(m.group(0))
    if re.search(r'\|?\s*access-date\s*=', params, re.IGNORECASE):
        has_access_date += 1

# Count bare URLs in ref tags
bare_urls = re.findall(r'<ref>(https?://[^\s<]+)</ref>', wikitext)

# Count dead link templates
dead_links = len(re.findall(r'\{\{dead\s*link', wikitext, re.IGNORECASE))
failed_verif = len(re.findall(r'\{\{failed\s*verification', wikitext, re.IGNORECASE))
cn_tags = len(re.findall(r'\{\{citation\s*needed', wikitext, re.IGNORECASE))

result = {
    'page': '$PAGE',
    'lang': '$LANG',
    'total_ref_tags': ref_tags,
    'named_references': named_refs,
    'bare_urls': len(bare_urls),
    'dead_link_templates': dead_links,
    'failed_verification_templates': failed_verif,
    'citation_needed_tags': cn_tags,
    'citations_with_url': len(cite_urls),
    'citations_with_archive': has_archive,
    'citations_without_archive': no_archive,
    'citations_with_doi': len(cite_doi),
    'citations_with_access_date': has_access_date,
    'cite_template_breakdown': dict(cite_templates.most_common()),
}

if '--json' in sys.argv:
    print(json.dumps(result, indent=2))
else:
    print(f'  📝 Total ref tags:        {ref_tags}')
    print(f'  🔤 Named refs:            {named_refs}')
    print(f'  🔗 Bare URLs:             {len(bare_urls)}')
    print(f'  🗄️  With archive URL:      {has_archive}')
    print(f'  📦 Without archive:        {no_archive}')
    print(f'  🆔 With DOI:               {len(cite_doi)}')
    print(f'  📅 With access-date:       {has_access_date}')
    print(f'  🚩 Dead link templates:    {dead_links}')
    print(f'  ❓ Failed verification:    {failed_verif}')
    print(f'  ⚠️  Citation needed tags:   {cn_tags}')
    print()
    print('  Template breakdown:')
    for tmpl, count in cite_templates.most_common():
        print(f'    {tmpl}: {count}')
" 2>/dev/null
