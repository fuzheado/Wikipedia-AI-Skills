"""
Cross-API Pipeline Example

Demonstrates chaining multiple Wikimedia APIs in a real-world workflow:
1. Pageviews API (top pages, underscore titles)
2. Action API (Wikidata ID resolution, space titles)
3. Wikidata API (batch entity classification via wbgetentities)
4. Action API (content analysis via parse)

Key lesson: handle title format differences between APIs.

Load these skills for context:
- wikimedia-pageviews  — Scenario C (Top Pages endpoint)
- wikidata             — SOP: Batch Entity Classification from Wikipedia Titles
- wikimedia-api-access — General implementation pattern, User-Agent, rate limiting

Usage:
    python3 cross-api-pipeline.py [--limit N] [--top-only]

    --limit N     Number of top pages to fetch (default: 50)
    --top-only    Just print the top pages without entity classification
"""

import argparse
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HEADERS = {
    'User-Agent': 'CrossAPIDemo/1.0 (https://example.com; user@example.com) ContentGapResearch'
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# Common P31 (instance of) Q IDs for entity classification
P31_HUMAN = 'Q5'
P31_FILM = 'Q11424'
P31_CITY = 'Q515'
P31_RIVER = 'Q4022'
P31_MOUNTAIN = 'Q12136'
P31_TAXON = 'Q16521'
P31_VIDEO_GAME = 'Q7889'
P31_BOOK = 'Q571'
P31_COMPANY = 'Q4830453'
P31_ORGANIZATION = 'Q43229'
P31_UNIVERSITY = 'Q3918'

KNOWN_TYPES = {
    P31_HUMAN: 'human',
    P31_FILM: 'film',
    P31_CITY: 'city',
    P31_RIVER: 'river',
    P31_MOUNTAIN: 'mountain',
    P31_TAXON: 'taxon/species',
    P31_VIDEO_GAME: 'video game',
    P31_BOOK: 'book',
    P31_COMPANY: 'company',
    P31_ORGANIZATION: 'organization',
    P31_UNIVERSITY: 'university',
}

# Namespace prefixes to filter out of top-pages results
SKIP_PREFIXES = ('Special:', 'Wikipedia:', 'Template:', 'Category:', 'Main_Page', 'File:', 'Help:', 'Portal:')


# ---------------------------------------------------------------------------
# Step 1: Get most popular articles from Pageviews API
# ---------------------------------------------------------------------------

def get_top_titles(limit=50):
    """Fetch the most-viewed articles on English Wikipedia.

    Uses the top-pages endpoint (date format: YYYY/MM/DD with slashes).
    Returns list of (title_with_underscores, view_count) tuples.
    """
    date = (datetime.now(timezone.utc) - timedelta(days=3)).strftime('%Y/%m/%d')
    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/"
        f"en.wikipedia/all-access/{date}"
    )
    resp = SESSION.get(url)
    if resp.status_code != 200:
        print(f"Error fetching top pages (HTTP {resp.status_code}): {resp.text[:200]}")
        return []

    data = resp.json()
    articles = data['items'][0]['articles']

    # Filter to main-namespace articles only
    results = []
    for a in articles:
        title = a['article']
        if not title.startswith(SKIP_PREFIXES):
            results.append((title, a['views']))
            if len(results) >= limit:
                break

    return results


# ---------------------------------------------------------------------------
# Step 2: Batch-resolve Wikipedia titles to Wikidata IDs via Action API
# ---------------------------------------------------------------------------

def get_wikidata_ids(titles_with_views):
    """Resolve Wikipedia titles to Wikidata Q IDs in batches of 50.

    ⚠️ Normalizes titles from underscores (Pageviews format) to
    spaces (Action API format) when looking up in the response dict.

    Returns list of (original_title, view_count, wikidata_id) tuples.
    Only titles that have a corresponding Wikidata item are included.
    """
    results = []
    for i in range(0, len(titles_with_views), 50):
        batch = [t for t, v in titles_with_views[i:i+50]]
        params = {
            'action': 'query',
            'titles': '|'.join(batch),
            'prop': 'pageprops',
            'ppprop': 'wikibase_item',
            'format': 'json',
        }
        data = SESSION.get('https://en.wikipedia.org/w/api.php', params=params).json()

        # Build dict with space-normalized keys (Action API returns spaces)
        id_by_title = {}
        for pid, info in data['query']['pages'].items():
            if 'missing' not in info and 'pageprops' in info:
                wid = info['pageprops'].get('wikibase_item')
                if wid:
                    id_by_title[info['title']] = wid  # key has spaces

        for t, v in titles_with_views[i:i+50]:
            # ⚠️ Normalize from underscores to spaces before lookup
            wid = id_by_title.get(t.replace('_', ' '))
            if wid:
                results.append((t, v, wid))

        time.sleep(0.5)  # rate limiting

    return results


# ---------------------------------------------------------------------------
# Step 3: Batch-classify entities via Wikidata wbgetentities
# ---------------------------------------------------------------------------

def classify_entities(entries):
    """Check which entities are instances of known types via P31.

    entries: list of (title, view_count, wikidata_id) tuples
    Returns dict mapping wikidata_id -> list of human-readable type labels.
    """
    classification = {}
    for i in range(0, len(entries), 50):
        batch = entries[i:i+50]
        ids = [e[2] for e in batch]
        params = {
            'action': 'wbgetentities',
            'ids': '|'.join(ids),
            'props': 'claims',
            'format': 'json',
        }
        data = SESSION.get('https://www.wikidata.org/w/api.php', params=params).json()

        for t, v, wid in batch:
            entity = data.get('entities', {}).get(wid, {})
            p31 = entity.get('claims', {}).get('P31', [])

            types = []
            for c in p31:
                ds = c.get('mainsnak', {}).get('datavalue', {})
                qid = ds.get('value', {}).get('id')
                if qid and qid in KNOWN_TYPES:
                    types.append(KNOWN_TYPES[qid])

            if types:
                classification[wid] = types

        time.sleep(0.5)

    return classification


# ---------------------------------------------------------------------------
# Step 4: Count {{citation needed}} tags via Action API parse
# ---------------------------------------------------------------------------

def count_citation_needed(title):
    """Count {{citation needed}} templates in a page's wikitext."""
    params = {
        'action': 'parse',
        'page': title.replace('_', ' '),  # parse accepts spaces
        'prop': 'wikitext',
        'format': 'json',
    }
    data = SESSION.get('https://en.wikipedia.org/w/api.php', params=params).json()
    text = data.get('parse', {}).get('wikitext', {}).get('*', '')
    if not text:
        return 0
    return len(re.findall(r'\{\{citation needed', text, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(limit=50, top_only=False):
    """Run the full multi-API pipeline and print results."""
    print(f"═══ Cross-API Pipeline Demo ═══\n")

    # Step 1: Top pages
    print(f"▶ Step 1: Fetching top {limit} pages from Pageviews API...")
    top = get_top_titles(limit=limit)
    print(f"   Got {len(top)} articles (filtered from top-{limit + len(SKIP_PREFIXES) + 5})\n")

    if top_only:
        print("Top pages:")
        for title, views in top[:10]:
            print(f"  {title}: {views:>10,} views")
        return

    # Step 2: Resolve Wikidata IDs
    print("▶ Step 2: Resolving Wikidata IDs via Action API...")
    entries = get_wikidata_ids(top)
    print(f"   Resolved {len(entries)}/{len(top)} articles to Wikidata items\n")

    if not entries:
        print("   No Wikidata IDs found. Exiting.")
        return

    # Step 3: Classify entities
    print("▶ Step 3: Classifying entities by P31 (instance of)...")
    classification = classify_entities(entries)
    grouped = {'human': [], 'other': [], 'unclassified': []}

    for title, views, wid in entries:
        types = classification.get(wid, [])
        if 'human' in types:
            grouped['human'].append((title, views, wid, types))
        elif types:
            grouped['other'].append((title, views, wid, types))
        else:
            grouped['unclassified'].append((title, views, wid, types))

    print(f"   Humans: {len(grouped['human'])}, "
          f"Other: {len(grouped['other'])}, "
          f"Unclassified: {len(grouped['unclassified'])}\n")

    # Step 4: Content analysis on humans (with citation needed check)
    print("▶ Step 4: Checking citation coverage on human biographies...")
    print()
    print(f"{'Title':<40} {'Views':>12} {'[cn]':>6}  Types")
    print(f"{'-'*40} {'-'*12} {'-'*6}  {'-'*20}")

    for title, views, wid, types in grouped['human'][:10]:
        cn = count_citation_needed(title)
        name = title.replace('_', ' ')
        type_str = ', '.join(types)
        print(f"{name:<40} {views:>12,} {cn:>6}  {type_str}")
        time.sleep(0.5)

    # Show a few non-human examples
    if grouped['other']:
        print()
        print("Non-human examples:")
        for title, views, wid, types in grouped['other'][:5]:
            name = title.replace('_', ' ')
            type_str = ', '.join(types)
            print(f"  {name:<40} {views:>10,}  [{type_str}]")

    print()
    print(f"═══ Pipeline complete ═══")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cross-API Wikimedia Pipeline Demo')
    parser.add_argument('--limit', type=int, default=50,
                        help='Number of top pages to fetch (default: 50)')
    parser.add_argument('--top-only', action='store_true',
                        help='Just print top pages without entity classification')
    args = parser.parse_args()

    run_pipeline(limit=args.limit, top_only=args.top_only)
