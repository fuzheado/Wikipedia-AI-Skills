---
name: wikimedia-search-cirrussearch
description: Search Wikimedia wikis using CirrusSearch — syntax cheat sheet (insource, hastemplate, linksto, deepcategory, haswbstatement), API parameters, prefix vs full-text vs title search, ranking caveats, maintenance queries, and combining search with PetScan, SPARQL, and categories
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["CirrusSearch", "search syntax", "find pages", "insource", "hastemplate", "linksto", "deepcategory", "haswbstatement"]
  - keywords: ["maintenance query", "search API", "prefix search", "full-text search", "title search"]
  - keywords: ["PetScan", "search results", "ranking", "search filter", "cross-wiki search"]
last_verified: 2026-06-11
depends_on: [wikimedia-api-access, wikipedia-categories]
---

> ⚠️ **User-Agent required:** All API examples in this skill access Wikimedia APIs. Requests without a descriptive `User-Agent` header will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

> 💡 **Related skills for search workflows:**
> - **[wikipedia-categories](../wikipedia-categories/SKILL.md)** — Category tree navigation, `incategory:` policy, PetScan, and category maintenance
> - **[wikimedia-commons](../wikimedia-commons/SKILL.md)** — Commons-specific `haswbstatement:`, MediaSearch, and file-type search
> - **[wikidata](../wikidata/SKILL.md)** — SPARQL querying for structured data when `haswbstatement:` is insufficient
> - **[wikidata-vector-search](../wikidata-vector-search/SKILL.md)** — Semantic/vector search on Wikidata when you don't know the exact label or QID
> - **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** — User-Agent headers, rate limiting, and base API usage
> - **[wikipedia-error-handling](../wikipedia-error-handling/SKILL.md)** — 429 handling and retry strategies

---

## Table of Contents

1. [What CirrusSearch Is](#what-cirrussearch-is)
2. [Three Search Entry Points](#three-search-entry-points)
3. [CirrusSearch Syntax Quick Reference](#cirrussearch-syntax-quick-reference)
4. [Action API Search Parameters](#action-api-search-parameters)
5. [SOP: Building Search Queries](#sop-building-search-queries)
6. [SOP: Maintenance Queries](#sop-maintenance-queries)
7. [SOP: Combining Search with Other Tools](#sop-combining-search-with-other-tools)
8. [Ranking Caveats](#ranking-caveats)
9. [Guardrails](#guardrails)
10. [Cross-References](#cross-references)

---

## What CirrusSearch Is

CirrusSearch is the Elasticsearch-based search engine powering all Wikimedia wikis (Wikipedia, Commons, Wikidata, Wiktionary, etc.). It replaces the old MediaWiki search with faster indexing, stemming across 50+ languages, template expansion in search results, and a rich query syntax.

**Two search indexes to understand:**

| Index | Update Frequency | Used By |
|-------|-----------------|---------|
| Full-text search (Special:Search) | Near real-time (minutes, up to ~30 min) | `list=search`, `srwhat=text`, REST `/search/page` |
| Fuzzy title autocomplete (search suggestions) | Once daily | Search box suggestions, `srwhat=near_match` |

**Consequence:** A new page may take up to two days to appear in autocomplete suggestions but only minutes in full-text search. For important queries, always use `srwhat=text` or the REST API `/search/page` endpoint.

---

## Three Search Entry Points

CirrusSearch exposes three distinct ways to find pages, each with different behavior:

### 1. Full-Text Search (`srwhat=text`)

The standard search. Matches against the rendered page content (expanded templates included). Supports all CirrusSearch syntax keywords. This is what `Special:Search` and the default Action API `list=search` use.

```bash
# REST API (recommended for simple queries)
curl -s -H 'User-Agent: MyBot/1.0 (contact) ContentGapResearch' \
  'https://en.wikipedia.org/api/rest_v1/search/page?q=quantum+mechanics&limit=10'

# Action API (supports more filters)
curl -s -H 'User-Agent: MyBot/1.0 (contact) ContentGapResearch' \
  'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=quantum+mechanics&srwhat=text&format=json&srlimit=10'
```

### 2. Title / Near-Match Search (`srwhat=near_match`)

The "Go" feature. If a query nearly perfectly matches a page title, it redirects to that page. Otherwise returns title-similar results. Used by the search box's "go" behavior and autocomplete.

```bash
# Near-match title search
curl -s -H 'User-Agent: MyBot/1.0 (contact) ContentGapResearch' \
  'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=Albert+Einstein&srwhat=near_match&format=json'
```

### 3. Title Prefix Search

Finds pages whose title starts with a given string. This is what the search box autocomplete and the `prefix:` parameter use. Very fast but limited to title-only matching.

```bash
# Via prefix: parameter (must be LAST in query)
curl -s -H 'User-Agent: MyBot/1.0 (contact) ContentGapResearch' \
  'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=prefix:Albert_E&format=json'

# Via generator=prefixsearch on the Action API
curl -s -H 'User-Agent: MyBot/1.0 (contact) ContentGapResearch' \
  'https://en.wikipedia.org/w/api.php?action=query&generator=prefixsearch&gpssearch=Albert_E&prop=info&format=json'
```

**When to use which:**

| Task | Use |
|------|-----|
| Find articles by keyword | Full-text (`srwhat=text`) or REST `/search/page` |
| Jump to a known article title | Near-match (`srwhat=near_match`) |
| Find subpages or project pages by name | Prefix search (`srsearch=prefix:Project:Name`) |
| Batch-complete partial titles | `generator=prefixsearch` |
| Get structured results with metadata | Action API full-text + `srprop=size|wordcount|timestamp|snippet` |

---

## CirrusSearch Syntax Quick Reference

All keywords are **case-sensitive and lowercase**. Negate any keyword with `-` prefix.

### Core Search Keywords

| Keyword | What it does | Example |
|---------|-------------|---------|
| `intitle:` | Match words in page title only | `intitle:Einstein` — titles containing "Einstein" |
| `incategory:` | Match pages in a category (exact, no subcats) | `incategory:"Physics"` |
| `insource:` | Match **wikitext** (not rendered content) | `insource:"{{Infobox"` — pages whose source contains `{{Infobox` |
| `insource:/regex/` | Regex search on wikitext (case-sensitive) | `insource:/\\{\\{[Vv]al\\s*\\|/` |
| `insource:/regex/i` | Regex search on wikitext (case-insensitive) | `insource:/\\{\\{infobox/i` |
| `hastemplate:` | Find pages using a specific template | `hastemplate:"Infobox scientist"` |
| `linksto:` | Find pages with wikilinks **to** a given page | `linksto:"Albert Einstein"` |
| `deepcategory:` | Search category **and all subcategories** (up to 5 levels) | `deepcategory:"Physics"` |
| `haswbstatement:` | Filter by Wikidata statement | `haswbstatement:P31=Q5` — items with "instance of: human" |
| `prefix:` | Match pages whose title starts with text. **Must be last in query.** | `quantum prefix:Albert_E` |
| `subpageof:` | Find subpages of a given page | `subpageof:"Requests for comment"` |
| `morelike:` | Find pages with similar text content | `morelike:quantum|mechanics` |
| `articletopic:` | Filter by ML-derived topic (Wikipedia only) | `articletopic:books|films` |
| `filetype:` | Filter by file media type (Commons) | `filetype:video` |
| `filemime:` | Filter by MIME type (Commons) | `filemime:application/pdf` |
| `filesize:` | Filter by file size in KB (Commons) | `filesize:>1024` |
| `prefer-recent:` | Boost recently-edited pages in ranking | `prefer-recent:0.6,160` |
| `boost-templates:` | Boost pages using certain templates | `boost-templates:"Template:FA|200%"` |
| `inlanguage:` | Filter by language (Translate extension) | `inlanguage:ja` |
| `contentmodel:` | Filter by content model | `contentmodel:json` |
| `creationdate:` | Filter by page creation date | `creationdate:>=2024` |
| `lasteditdate:` | Filter by last edit date | `lasteditdate:today-1d` |
| `hasrecommendation:` | Filter by ML recommendation | `hasrecommendation:image` |
| `neartitle:` / `nearcoord:` | Geo-search by coordinates | `neartitle:"100km,San Francisco"` |
| `pageid:` | Restrict to specific page IDs | `pageid:12345\|67890` |
| `inlabel:` | Search Wikidata labels (Wikibase) | `inlabel:duck@en,fr` |
| `hasdescription:` | Search items with a description | `hasdescription:en` |

### Operators and Modifiers

| Modifier | Effect | Example |
|----------|--------|---------|
| `"phrase"` | Exact phrase match (no stemming) | `"Albert Einstein"` |
| `-` or `!` prefix | Exclude pages matching this term | `Einstein -intitle:Albert` |
| `~` | Fuzzy search (word) or proximity (phrase) | `Einstein~` or `"theory relativity"~2` |
| `*` wildcard | Zero or more characters (never at start) | `quant*m*` |
| `\?` wildcard | Exactly one character | `quan\?um` |
| `AND`, `OR` | Boolean operators (limited support) | `Einstein OR Bohr` |
| `~` at start of query | Skip search suggestions, go to results | `~Einstein` |
| `all:` | Search all namespaces | `all:prefix:Talk:` |
| `:` (single colon) | Main namespace only | `:Einstein` |

### Namespace Shorthand

Use a namespace prefix (followed by `:`) as the **first** term in the query:

| Shorthand | Searches |
|-----------|----------|
| `talk:` | Talk namespace |
| `file:` | File/Media namespace |
| `template:` | Template namespace |
| `category:` | Category namespace |
| `help:` | Help namespace |
| `user:` | User namespace |
| `all:` | All namespaces |
| `:` (single colon) | Main (article) namespace only |

### Negation Examples

```cirrus
# Pages that contain "Einstein" but whose title does NOT contain "Albert"
Einstein -intitle:Albert

# Pages in Category:Physics that are NOT in Category:Scientists
incategory:Physics -incategory:Scientists

# Pages that DON'T use a specific template
Einstein -hastemplate:"Infobox scientist"
```

### Regex Search on Insource

`insource:/regex/` runs a **regular expression** against the raw wikitext. This is powerful but expensive — always pair it with other filters to limit the search domain.

```cirrus
# Always add a non-regex filter to limit the search domain
insource:"{{Val" insource:/\\{\\{ *[Vv]al *\\|/

# Finding pages with a specific string in wikitext
insource:"http://example.com" insource:/http:\\/\\/example\\.com/

# Case-insensitive regex
insource:/\\{\\{infobox/i incategory:"Physicists"

# Regex on titles
intitle:/^Albert/
```

**⚠️ Bare regex searches are slow and may time out.** Always pair with at least one index-based filter (`incategory:`, `hastemplate:`, `intitle:`, quoted string `insource:`).

---

## Action API Search Parameters

When using the Action API (`action=query&list=search`), these parameters control how CirrusSearch behaves:

| Parameter | Values | Description |
|-----------|--------|-------------|
| `srsearch` | string | The search query (supports all CirrusSearch syntax) |
| `srlimit` | 1–500 | Number of results (default 10, max 50 for unprivileged, 500 for bots) |
| `sroffset` | integer | Pagination offset |
| `srnamespace` | 0–15+ | Namespace IDs separated by `\|` |
| `srwhat` | `text`, `title`, `near_match` | Search mode (see entry points above) |
| `srprop` | `size\|wordcount\|timestamp\|snippet\|redirecttitle\|...` | What metadata to return |
| `srbackend` | `CirrusSearch`, `MediaSearch` | Search backend (MediaSearch is Commons-specific) |
| `srsort` | `relevance`, `last_edit_desc`, `create_timestamp_desc`, `incoming_links_desc`, `random`, etc. | Sort order |
| `srinterwiki` | boolean | Include interwiki results |
| `srenablerewrites` | boolean | Allow CirrusSearch to rewrite queries (suggestions) |

### Complete srprop Fields

```python
srprop = "size|wordcount|timestamp|snippet|redirecttitle|redirectsnippet|sectiontitle|sectionsnippet|isfilematch|score|hasrelated"
```

The `score` field exposes CirrusSearch's internal relevance score — useful for debugging ranking issues.

### Python Request Pattern

```python
import requests

session = requests.Session()
session.headers.update({
    'User-Agent': 'MyBot/1.0 (https://example.com; user@example.com) ContentGapResearch'
})

def cirrus_search(query, wiki='en.wikipedia.org', limit=50, what='text', namespace=0):
    """Run a CirrusSearch query via the Action API."""
    url = f'https://{wiki}/w/api.php'
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': query,
        'srlimit': min(limit, 500),
        'srwhat': what,
        'srnamespace': namespace,
        'srprop': 'size|wordcount|timestamp|snippet|score',
        'format': 'json',
    }
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get('query', {}).get('search', [])
```

---

## SOP: Building Search Queries

### 1. Start Simple, Add Filters

```cirrus
# Too broad: returns millions of hits
Einstein

# Better: narrow by namespace and keywords
intitle:Einstein incategory:Physicists

# Best: combine index-based filters to define the search domain
hastemplate:"Infobox scientist" incategory:"Nobel laureates in Physics" intitle:Einstein
```

### 2. Use `incategory:` for Category Membership

`incategory:` matches pages directly in a category — it does **not** include subcategories. For recursive category search, use `deepcategory:`.

```cirrus
# Pages IN this category only
incategory:"Bridges in New York City"

# Pages in two categories simultaneously (AND)
incategory:"Suspension bridges" incategory:"Bridges in New York City"

# Pages in either category (OR) — use pipe within quotes
incategory:"Suspension bridges|Bridges in New York City"

# Pages NOT in a category
-Suspension incategory:"Bridges in New York City"
```

**⚠️ Important:** `incategory:` accepts the category name **without** the `Category:` prefix. Do not write `incategory:Category:Physics`.

### 3. Use `hastemplate:` for Template Presence

```cirrus
# Find all pages using a template
hastemplate:"Infobox scientist"

# Exclude pages using a template
hastemplate:"Infobox person" -hastemplate:"Infobox scientist"

# Combine with category filter
hastemplate:"Unreferenced" incategory:"Living people"
```

### 4. Use `linksto:` for Backlink Analysis

```cirrus
# Find all pages linking to a specific page
linksto:"Albert Einstein"

# Pages that mention "Einstein" but don't link to him
Einstein -linksto:"Albert Einstein"

# Check for broken incoming links
linksto:"Deleted article title"
```

### 5. Use `deepcategory:` for Recursive Category Search

```cirrus
# Search a category AND all its subcategories (up to 5 levels)
deepcategory:"Physics"

# Deep category with additional filter
deepcategory:"Physics" hastemplate:"Infobox scientist"
```

### 6. Use `haswbstatement:` for Structured Data Queries

Works on **any wiki with WikiBase structured data** — primarily Commons (file depicts/creator) and Wikidata (properties). Not for Wikipedia articles unless they have WikiBase statements.

```cirrus
# Commons: files depicting a human
haswbstatement:P180=Q5

# Commons: files depicting a human but NOT a beard
haswbstatement:P180=Q5 -haswbstatement:P180=Q115

# Commons: files by a specific creator
haswbstatement:P170=Q42

# Wikidata: items with a specific property
haswbstatement:P31=Q5

# Qualifier filtering (Commons)
haswbstatement:P180=Q146[P462=Q23445]

# OR logic (pipe)
haswbstatement:P180=Q146|P180=Q144

# Any statement existence
haswbstatement:*
```

**When to use `haswbstatement:` instead of SPARQL:**

- Query is simple equality on 1–2 properties
- Need sub-second response time
- Want to combine with full-text search terms

**When to use SPARQL instead:**

- Need numerical comparisons, date ranges, or aggregations
- Complex multi-hop graph queries
- Need `MINUS`, `UNION`, or subqueries

### 7. Use `prefix:` for Title Completion

The `prefix:` parameter **must be the last term** in the query.

```cirrus
# Pages whose title starts with "Albert"
prefix:Albert

# Pages in Talk namespace whose title starts with "Albert"
talk: prefix:Albert

# Main namespace only
: prefix:Albert

# Subpages of a particular page
prefix:Albert_Einstein/
```

---

## SOP: Maintenance Queries

These are practical queries for common patrolling and maintenance tasks. All work in the Wikipedia search box or via the API.

### Find Articles Missing Citations

```cirrus
# Pages with no inline citations (maintenance tag)
hastemplate:"Unreferenced" incategory:"Living people"

# Pages with bare URLs as citations
insource:"http://" -hastemplate:"cite web" -hastemplate:"cite news"
```

### Find Uncategorized Pages

```cirrus
# Pages without any category tag (use with caution — many are redirects or lists)
-haswbstatement:* incategory:"Wikipedia uncategorized"
```

Actually on Wikipedia, use:

```cirrus
incategory:"All uncategorized pages"
```

### Find Pages with Broken Template Usage

```cirrus
# Find transclusions of a deleted or nonexistent template
hastemplate:"Infobox nonexistent" -intitle:Infobox

# Find pages using a deprecated template
hastemplate:"Infobox person" insource:"Infobox person/core"
```

### Find Overcategorized Pages

```cirrus
# Pages in both a parent and a child category (common overcategorization)
incategory:"American physicists" incategory:"20th-century American physicists"
```

### Find Orphaned Pages

```cirrus
# Pages in a category with no incoming links (potential orphans)
incategory:"Physics" -linksto:"Special:Search"

# More practical: pages with few or no other pages linking to them
# (requires API processing — no single CirrusSearch query for this)
```

### Find Pages Needing Image

```cirrus
# Articles without infobox image
hastemplate:"Infobox scientist" -insource:"| image =" -insource:"|image ="
hastemplate:"Infobox person" -insource:"| image =" -insource:"|image ="
```

### Recent Edits in a Category

```cirrus
# Pages edited today in a specific category
incategory:"Physics" lasteditdate:today

# Pages edited in the last week in a specific category
incategory:"Physics" lasteditdate:>=today-7d

# Recently created pages
incategory:"Physics" creationdate:>=2025-01-01 lasteditdate:>=today-1d
```

### Find Pages with Specific Infobox

```cirrus
# Mainspace pages using a specific infobox
hastemplate:"Infobox settlement" incategory:"Populated places in France"

# Pages with multiple infoboxes (possible duplication)
hastemplate:"Infobox settlement" hastemplate:"Infobox French commune"
```

### Find All Subpages of a Project or User Page

```cirrus
subpageof:"Wikipedia:WikiProject Physics"
subpageof:"User:Example"
```

### Find Pages with Spelling/Dating Issues

```cirrus
# Pages that might use date formatting incorrectly
insource:"{{date" -hastemplate:"Use dmy dates" -hastemplate:"Use mdy dates"
```

### Script: Maintenance Query Runner

See `scripts/maintenance-queries.sh` for a CLI tool that runs common maintenance queries and outputs results as formatted lists.

### Python: Programmatic Maintenance Library

See `assets/maintenance_queries.py` for a Python module with pre-built maintenance query generators.

---

## SOP: Combining Search with Other Tools

### Search + PetScan

PetScan (`https://petscan.wmflabs.org/`) is an external tool for complex category intersections and data extraction. It complements CirrusSearch by handling:

- **Category intersections** — Find pages in multiple categories simultaneously
- **Template filtering** — Only pages with/without certain templates
- **Namespace filtering** — Scope to specific namespaces
- **Page size / redirect / page quality** filters
- **Export** as CSV, JSON, or Wiki table

**When to use PetScan vs CirrusSearch:**

| Task | Better tool | Why |
|------|------------|-----|
| Simple keyword + category search | CirrusSearch | Instant results, no external dependency |
| Category intersection (AND) | PetScan | Handles intersection server-side for large categories |
| Category union (OR) | CirrusSearch (`incategory:"A\|B"`) | Native syntax |
| Deep category search (>5 levels) | PetScan or SPARQL | CirrusSearch limited to 5 levels |
| Export bulk results as structured data | PetScan | Built-in CSV/JSON export |
| Combine category, template, page size, and namespace filters | Either | Both support it; PetScan has a UI |
| Quick CLI automation | CirrusSearch API | No external service dependency |

```bash
# PetScan API example — find intersection of two categories
curl -s 'https://petscan.wmflabs.org/?language=en&project=wikipedia&categories=Physicists%0AGerman%20scientists&ns%5B0%5D=1&interface_language=en&format=json' \
  -H 'User-Agent: MyBot/1.0 (contact) ContentGapResearch' \
  | python3 -c "import json,sys; data=json.load(sys.stdin); print('\n'.join(p['a']['title'] for p in data.get('*',[])))"
```

### Search + SQL Replicas

For large-scale analytics, combine CirrusSearch's filtered results with database queries:

1. Use CirrusSearch to get a focused set of page titles
2. Use SQL replicas (via Toolforge) to bulk-fetch pageviews, quality assessments, etc.

See **[wikimedia-api-strategy](../wikimedia-api-strategy/SKILL.md)** for the decision framework on when to use each approach.

### Search + SPARQL

CirrusSearch and SPARQL solve different problems:

- **CirrusSearch:** "Find all pages matching these text/structural criteria"
- **SPARQL:** "Find all items matching these graph pattern criteria"

They can be chained:

```
CirrusSearch → get page titles → resolve to Wikidata QIDs → SPARQL for structured enrichment
```

Example workflow:

```python
# 1. CirrusSearch finds pages
pages = cirrus_search("hastemplate:\"Infobox scientist\" incategory:\"Nobel laureates\"", limit=100)
titles = [p['title'] for p in pages]

# 2. Wikibase API resolves titles to QIDs
# (see wikidata skill for wbgetentities batch)

# 3. SPARQL enriches with structured data
# SELECT ?item ?itemLabel WHERE { VALUES ?item { wd:Q937 ... } ... }
```

### Search + Categories

See **[wikipedia-categories](../wikipedia-categories/SKILL.md)** for:
- Category tree navigation
- The three tests for valid categories (Verifiable/Neutral/Defining)
- Topic vs. set categories
- `DEFAULTSORT` and sort keys
- The full API query patterns for categories

---

## Ranking Caveats

Understanding how CirrusSearch ranks results is critical for building reliable maintenance queries and interpreting search output.

### 1. Ranking Includes Non-Obvious Factors

CirrusSearch ranking considers:
- **Text relevance** — keyword frequency, proximity, and field weighting
- **Incoming link count** — pages with more backlinks rank higher
- **Page size** — larger pages may rank higher
- **Heading count** — more structured pages rank higher
- **External link count** — more outbound links boost score
- **Redirect count** — more redirects to the page
- **Article quality** — Featured Articles and Good Articles get boosts
- **Recency** — `prefer-recent:` can bias towards newly edited pages
- **Template boosts** — `cirrussearch-boost-templates` or `boost-templates:`

**Consequence:** Results are NOT purely text-relevance ordered. A short, obscure article with low link count may appear below a much more popular page that mentions the search term in passing.

### 2. Sort Order Disables Scoring Keywords

When you use `srsort=last_edit_desc` or any explicit sort order, keywords like `prefer-recent:`, `boost-templates:`, and `articletopic:` have **no effect**. They are parsed but silently ignored.

### 3. Stemming Is Automatic

A search for "swim" also matches "swimming", "swimmer", and "swims". To disable stemming, use an exact phrase: `"swim"`.

### 4. Stop Words Are Ignored

Common words like "the", "a", "of" are ignored in most searches unless they appear in an exact phrase.

### 5. Template Content Is Indexed

Pages are indexed with their **expanded template output**, not raw wikitext. This means:
- `insource:` searches the **raw wikitext** (including template markup)
- Normal search searches the **rendered content** (expanded templates)
- A term that only appears through template transclusion will be found by normal search but NOT by `insource:`

### 6. Regex Searches Are Expensive

- Regex searches (`insource:/regex/`) scan pages character-by-character
- Only a limited number of regex searches can run simultaneously on the search cluster
- They time out after ~20 seconds if they don't finish
- **Always** pair with index-based filters to limit the search domain
- If only common trigrams can be extracted from your regex, it will be very slow

### 7. Index Freshness Matters

- Full-text index: near real-time (minutes, up to ~30 min)
- Title autocomplete index: updated once daily
- Template content updates: minutes to hours depending on the number of transcluding pages
- A null edit on a page forces re-indexing of that page

### 8. Search Results Have Hard Limits

| Limit | Value | Context |
|-------|-------|---------|
| Max results per API call | 50 (unauthenticated), 500 (bots) | `srlimit` parameter |
| Max results you can paginate to | 10,000 | Hard Elasticsearch limit |
| Deep category depth | 5 levels | `deepcategory:` |
| Categories in `deepcategory:` | 256 max | Configurable but unlikely to change |
| Regex search timeout | ~20 seconds | Cluster-wide limit |

---

## Guardrails

### 1. Always Escape Namespace in Prefix Queries

The `prefix:` parameter is **case-sensitive** for the pagename portion. The namespace portion (if present) is case-insensitive.

**Correct:**
```cirrus
prefix:Albert_Einstein/
```

**Incorrect:**
```cirrus
Albert_Einstein/ prefix:
```

### 2. `incategory:` Drops Subcategories — Use `deepcategory:`

`incategory:Physics` finds pages **directly** in `Category:Physics`, not its subcategories. For recursive search, use `deepcategory:Physics` (up to 5 levels).

### 3. `linksto:` Does Not Find Redirects

`linksto:"Albert Einstein"` finds pages with `[[Albert Einstein]]` but not `[[Albert Einstein (physicist)]]` even if that redirects to `Albert Einstein`. You must query each redirect target separately.

### 4. Namespace in `prefix:` Changes Behavior

```
# Searches main namespace for pages starting with "Physics"
prefix:Physics

# Searches ALL namespaces — the ":" makes prefix: a namespace filter
: prefix:Physics
```

### 5. `hastemplate:` Searches Post-Expansion

`hastemplate:` finds secondary template usage — if Template:A includes Template:B, searching `hastemplate:B` will find pages that use Template:A (because B is transcluded into the page output). `insource:` does NOT do this — it only finds raw wikitext mentions.

### 6. Stop Words Affect Your Queries

Don't search for common words alone — they'll be ignored. Combine with more specific terms.

### 7. Search API Rate Limits

Search is one of the most heavily used API endpoints. Respect these limits:
- **Unauthenticated:** ~5 requests/second
- **Bot/user-agent with contact:** ~50–100 requests/second (varies by wiki)
- **429 handling:** Implement exponential backoff using `Retry-After` header

See **[wikipedia-error-handling](../wikipedia-error-handling/SKILL.md)** for complete rate limiting guidance.

### 8. Don't Use Search for Single Page Lookups

For fetching a page by known title, use `action=query&prop=info|extracts&titles=Page_Title` or the REST API `/page/{title}/summary` — these are faster and don't count against search rate limits.

### 9. `haswbstatement:` Only Works on Wikidata-Compatibile Wikis

Not all wikis have Wikibase structured data enabled. Commons and Wikidata are the primary targets. On regular Wikipedia, `haswbstatement:` will generally not return results through the search interface.

### 10. `articletopic:` Is Wikipedia-Only

The `articletopic:` keyword uses ML topic models that only exist for Wikipedia (main namespace articles). It does not work on Commons, Wiktionary, or other projects.

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent headers, rate limiting, base API patterns |
| **[wikipedia-categories](../wikipedia-categories/SKILL.md)** | Category rules, `incategory:` policy, PetScan, category tree |
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | Commons-specific `haswbstatement:`, MediaSearch, file-type search |
| **[wikidata](../wikidata/SKILL.md)** | SPARQL for complex structured data queries |
| **[wikidata-vector-search](../wikidata-vector-search/SKILL.md)** | Semantic search on Wikidata when labels are unknown |
| **[wikimedia-api-strategy](../wikimedia-api-strategy/SKILL.md)** | Decision framework for search vs. SQL vs. SPARQL vs. EventStreams |
| **[wikipedia-error-handling](../wikipedia-error-handling/SKILL.md)** | 429 handling, retry strategies, error response formats |
| **[wikimedia-database](../wikimedia-database/SKILL.md)** | SQL replicas for bulk analytics after search filtering |
| **[pywikibot](../pywikibot/SKILL.md)** | `Site.search()`, `Site.prefixsearch()`, generators |
| **[wikipedia-page-anatomy](../wikipedia-page-anatomy/SKILL.md)** | Redirect/disambiguation detection, protection levels |
