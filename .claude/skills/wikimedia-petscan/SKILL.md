---
name: wikimedia-petscan
description: Use PetScan for multi-source Wikimedia queries — category intersections, template filtering, SPARQL integration, Wikidata item queries, and bulk data export via the URL API and PSID system
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
last_verified: 2026-06-30
skill_discovery_hints:
  - keywords: ["PetScan", "petscan", "category intersection", "category union", "category difference", "category overlap"]
  - keywords: ["multi-source query", "combine categories", "combine SPARQL", "combine PagePile", "combine templates"]
  - keywords: ["PSID", "query ID", "tool integration", "bulk export", "find files", "uncategorized files"]
  - keywords: ["find items without statements", "Wikidata quality", "missing Wikidata item", "redlink finder"]
---

> ℹ️ **User-Agent required:** All API examples in this skill access PetScan (`petscan.wmcloud.org`). Include a descriptive `User-Agent` header as described in the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill.

> 💡 **Related skills for complementary query approaches:**
> - **[wikipedia-categories](../wikipedia-categories/SKILL.md)** — Category tree navigation, `incategory:` policy, and the `category-intersect.py` asset
> - **[wikimedia-search-cirrussearch](../wikimedia-search-cirrussearch/SKILL.md)** — Full-text and structural search with CirrusSearch
> - **[wikidata](../wikidata/SKILL.md)** — SPARQL querying when PetScan's built-in SPARQL source is too limited
> - **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** — Commons-specific SPARQL queries for MediaInfo entities

---

## SOP: What PetScan Is

**[PetScan](https://petscan.wmcloud.org/)** is a powerful multi-source querying tool for Wikimedia, created by Magnus Manske as the successor to CatScan2. Winner of the **Coolest Tool Award 2022**.

It generates lists of pages or Wikidata items matching criteria across up to **6 source tabs** simultaneously:

| Tab | What it queries | Example |
|-----|----------------|---------|
| **Categories** | Category tree membership, intersection/union/difference | Pages in `Category:Physics` AND `Category:Biography` |
| **Page properties** | Namespace, redirects, size, dates, edit types, ORES quality | Files only, created after 2024, not redirects |
| **Templates & links** | Template presence, outlinks, incoming links | Pages with `{{Infobox scientist}}` but NOT `{{Unreferenced}}` |
| **Other sources** | SPARQL, manual list, PagePile, search query | All QIDs from a SPARQL query, minus a manual exclusion list |
| **Wikidata** | Wikidata item filters — statements, properties, sitelinks, labels | Items with an occupation but no image |
| **Output** | Format, sorting, regex filter, file media types | JSON sorted by page size, with regex filter on title |

The key insight: **PetScan combines these sources into one result** using configurable logic (subset/union/difference/at-least-N). You can mix categories with SPARQL, templates with manual lists, etc. — including cross-wiki via Wikidata.

### Three Ways to Use PetScan

| Method | When | How |
|--------|------|-----|
| **Web UI** | One-off queries, exploration | `https://petscan.wmcloud.org/` — fill forms, tabs, click "Do it!" |
| **URL API** | Automation, scripts | Append URL parameters to the base URL, get JSON/CSV/XML/... |
| **PSID** | Share, rerun, tool integration | Every query gets a stable ID; `?psid=12345` re-runs it |

---

## SOP: PSID — Stable Query IDs

Since 2016, every submitted PetScan query is assigned a unique, stable numeric **PSID** (displayed in the result page). This enables:

- **Short URLs:** `https://petscan.wmcloud.org/?psid=552`
- **Re-running queries** without re-entering all parameters
- **Tool integration:** Many tools (WD-FIST, PagePile, Massviews) accept PSID as input
- **Caching:** PSID results are cached server-side for faster repeat access

> **PSIDs are anonymous** — no user identity is stored with them.

---

## SOP: URL Parameter Reference

PetScan accepts **50+ URL parameters** across all six tabs. Here are the most commonly used ones in automation:

### Categories Tab

| Parameter | Description |
|-----------|-------------|
| `language`| Wiki language code (`en`, `de`, `commons`, etc.) |
| `project` | Wikimedia project (`wikipedia`, `wiktionary`, `commons`, `wikidata`) |
| `categories` | Pipe-separated category names (no `Category:` prefix). Append `|N` to set per-category depth. |
| `depth` | Default category tree depth (0 = no recursion) |
| `combination` | `subset` (AND — all categories), `union` (OR — any category) |
| `negcats` | Pipe-separated categories to exclude |

### Page Properties Tab

| Parameter | Description |
|-----------|-------------|
| `ns[0]`, `ns[6]`, etc. | Namespace filter (set to `1` to include) |
| `show_redirects` | `no` (default), `only`, `yes` (include redirects) |
| `show_soft_redirects` | Same options for soft redirects |
| `show_disambiguation_pages` | Same options for disambiguation pages |
| `after`, `before` | Date filter (YYYYMMDDHHMMSS format) |
| `since_rev0` | Find pages created within a time window |
| `larger`, `smaller` | Page size range in bytes |
| `minlinks`, `maxlinks` | Internal link count range |
| `edits[bots]`, `edits[anons]` | Filter by last editor type (`1` to require, `0` to exclude) |
| `ores_prediction` | ORES quality class (`FA`, `GA`, `B`, `C`, `Start`, `Stub`) |
| `ores_prob_from`, `ores_prob_to` | ORES probability range |

### Templates & Links Tab

| Parameter | Description |
|-----------|-------------|
| `templates_yes` | Pipe-separated templates — page must have ALL of them |
| `templates_any` | Pipe-separated templates — page must have at least ONE |
| `templates_no` | Pipe-separated templates — page must have NONE |
| `outlinks_yes`, `outlinks_any`, `outlinks_no` | Same pattern for outgoing links |
| `links_to_all`, `links_to_any`, `links_to_no` | Same pattern for incoming links |

### Other Sources Tab

| Parameter | Description |
|-----------|-------------|
| `sparql` | Raw SPARQL query (URL-encoded) as a data source |
| `manual_list` | Newline-separated page titles or QIDs |
| `manual_list_wiki` | Wiki for the manual list (e.g., `enwiki`, `wikidatawiki`) |
| `pagepile` | PagePile ID |
| `search_query` | Free-text search query |
| `search_max_results` | Max results from search source |
| `source_combination` | How to combine sources: `subset`, `union`, or custom (e.g., `manual NOT sparql`) |

### Wikidata Tab

| Parameter | Description |
|-----------|-------------|
| `wikidata_item` | `with`, `without`, or `any` — whether items have a Wikidata ID |
| `wikidata_source_sites` | Wiki to use as source for site links |
| `wikidata_label_language` | Language for labels in results |
| `wpiu` | Wikidata property item use filter |
| `sitelinks_yes`, `sitelinks_any`, `sitelinks_no` | Filter by sitelink presence on specific wikis |
| `labels_yes`, `labels_any`, `labels_no` | Filter by label presence in specific languages |
| `min_sitelink_count`, `max_sitelink_count` | Sitelink count range |

### Output Tab

| Parameter | Description |
|-----------|-------------|
| `format` | `html`, `csv`, `tsv`, `wiki`, `json`, `jsonl`, `pagepile`, `kml`, `plain` |
| `sortby` | `none`, `title`, `size`, `date`, `incoming_links`, `random`, etc. |
| `sortorder` | `ascending` or `descending` |
| `output_limit` | Maximum number of results |
| `rxp_filter` | Regular expression to filter titles/labels |
| `file_media_types` | Pipe-separated media types (`BITMAP`, `VIDEO`, `AUDIO`, `3D`, etc.) |
| `page_image` | Include page image URL in output |
| `json-pretty` | Pretty-printed JSON (`1`) |

---

## SOP: Common API Patterns

All examples use `curl`. Replace `language`/`project` as needed.

### Category Intersection (AND)

Pages in ALL categories — equivalent to `category-intersect.py` in the **[wikipedia-categories](../wikipedia-categories/SKILL.md)** skill:

```bash
curl -s 'https://petscan.wmcloud.org/\
  ?language=en\
  &project=wikipedia\
  &categories=Physicists%7CGerman%20scientists\
  &ns%5B0%5D=1\
  &combination=subset\
  &format=json' \
  -H 'User-Agent: MyTool/1.0 (contact@example.com)'
```

### Category + Template Filter

Pages in `Category:Physics` that have `{{WikiProject Physics}}`:

```bash
curl -s 'https://petscan.wmcloud.org/\
  ?language=en\
  &project=wikipedia\
  &categories=Physics\
  &templates_yes=WikiProject%20Physics\
  &ns%5B0%5D=1\
  &format=json' \
  -H 'User-Agent: ...'
```

### Category + ORES Quality Filter

FA-class articles in a category:

```bash
curl -s 'https://petscan.wmcloud.org/\
  ?language=en\
  &project=wikipedia\
  &categories=Physics\
  &ores_prediction=FA\
  &ns%5B0%5D=1\
  &format=json' \
  -H 'User-Agent: ...'
```

### SPARQL as a Data Source

Get all items from a SPARQL query that are also in a category:

```bash
SPARQL_ENC=$(python3 -c "import urllib.parse; print(urllib.parse.quote(\"\"\"\
SELECT ?item WHERE { ?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q2519376 }
\"\"\"))")
curl -s "https://petscan.wmcloud.org/\
  ?language=en\
  &project=wikipedia\
  &categories=American%20jewellers\
  &sparql=$SPARQL_ENC\
  &combination=subset\
  &format=json" \
  -H 'User-Agent: ...'
```

### Manual List + SPARQL Exclusion

QIDs from a manual list, minus those that already have a certain occupation:

```bash
MANUAL="Q123\nQ456\nQ789"
MANUAL_ENC=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$MANUAL'''))")
SPARQL_EXCLUDE=$(python3 -c "import urllib.parse; print(urllib.parse.quote(\"\"\"\
SELECT ?item WHERE { ?item wdt:P31 wd:Q5 ; wdt:P106 wd:Q2519376 }\
\"\"\"))")
curl -s "https://petscan.wmcloud.org/\
  ?manual_list=$MANUAL_ENC\
  &manual_list_wiki=wikidatawiki\
  &sparql=$SPARQL_EXCLUDE\
  &source_combination=manual%20NOT%20sparql\
  &format=json" \
  -H 'User-Agent: ...'
```

### Items Without Wikidata Statements (Data Quality)

Find English Wikipedia articles in a category that have a Wikidata item but no statements:

```bash
curl -s 'https://petscan.wmcloud.org/\
  ?language=en\
  &project=wikipedia\
  &categories=United%20States%20geography%20stubs\
  &ns%5B0%5D=1\
  &wikidata_item=with\
  &wpiu_no_statements=1\
  &format=json' \
  -H 'User-Agent: ...'
```

### Commons: Find Uncategorized Files with a Language Template

```bash
curl -s 'https://petscan.wmcloud.org/\
  ?language=commons\
  &project=wikimedia\
  &categories=Uncategorized%20files\
  &depth=1\
  &ns%5B6%5D=1\
  &templates_yes=ro\
  &format=json' \
  -H 'User-Agent: ...'
```

### PSID-Based Query

Re-run a previously saved query:

```bash
curl -s 'https://petscan.wmcloud.org/?psid=552&format=json' \
  -H 'User-Agent: ...'
```

### Output as Wiki Table

Any format parameter changes the output:

```bash
curl -s 'https://petscan.wmcloud.org/\
  ?language=en&project=wikipedia&categories=Physics\
  &ns%5B0%5D=1&format=wiki' \
  -H 'User-Agent: ...'
```

---

## SOP: Multi-Source Combination Logic

When using multiple sources (categories + SPARQL + manual list + pagepile + search), the `combination` parameter controls how they are merged. With `source_combination`, you get more control:

| Value | Effect |
|-------|--------|
| `subset` (default) | Return only results present in ALL sources (AND) |
| `union` | Return results from ANY source (OR) |
| `source1 NOT source2` | Results from first source minus second |
| `source1 AND source2` | Explicit AND between named sources |

Sources are ordered as: categories → manual_list → pagepile → sparql → search. Use `source_combination` to reorder or mix.

> **Cross-wiki magic:** Use `common_wiki=wikidata` to merge results across different wikis. PetScan will resolve pages from different wikis through Wikidata to find common items.

---

## SOP: Integration with Other Tools

| Tool | How PetScan Feeds Into It |
|------|--------------------------|
| **PagePile** | Output format `pagepile` creates a new PagePile; or feed PSID into PagePile's "from external tool" field |
| **Massviews Analysis** | Use PagePile ID from PetScan as source → get pageviews for the query result set |
| **WD-FIST** | PSID → find free images for a list of articles |
| **QuickStatements** | Export as JSON/CSV, transform to QuickStatements format |

---

## Relationship to Other Skills

- **[wikipedia-categories](../wikipedia-categories/SKILL.md)** — Covers category tree concepts and ships `category-intersect.py` (uses PetScan's URL API for basic AND intersection). This skill covers the full parameter surface PetScan offers.
- **[wikimedia-search-cirrussearch](../wikimedia-search-cirrussearch/SKILL.md)** — CirrusSearch is faster for simple keyword+category. PetScan is the right choice when you need category intersection/union/difference, multi-source combination (categories + templates + SPARQL), ORES filtering, or bulk export. See the comparison table in that skill.
- **[wikidata](../wikidata/SKILL.md)** — For complex SPARQL queries that exceed PetScan's single-query input, use the Wikidata Query Service directly.
- **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** — For Commons-specific MediaInfo queries; PetScan complements with file media type filtering and uncategorized file detection.
- **[wikimedia-toolforge](../wikimedia-toolforge/SKILL.md)** — PetScan runs on Toolforge infrastructure.
