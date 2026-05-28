# Wikimedia API Endpoints Reference

A comprehensive catalog of Wikimedia API endpoints. Use this reference to quickly find the right endpoint for a given task.

---

## 1. Action API (`api.php`)

The original workhorse API. Parameter-driven, supports read, write, and search operations.

| Base URL | Documentation |
|---|---|
| `https://en.wikipedia.org/w/api.php` | [API docs](https://en.wikipedia.org/w/api.php?action=help) |
| `https://commons.wikimedia.org/w/api.php` | Commons |
| `https://www.wikidata.org/w/api.php` | Wikidata |

### Common Operations

| Purpose | Parameters | Example |
|---|---|---|
| **Search pages** | `action=query&list=search&srsearch=<query>` | `?action=query&list=search&srsearch=Albert%20Einstein&format=json&srlimit=10` |
| **Get page content** | `action=query&prop=extracts&titles=<title>` | `?action=query&prop=extracts&exintro&explaintext&titles=Python_(programming_language)&format=json` |
| **Get page info** | `action=query&prop=info&titles=<title>` | `?action=query&prop=info&titles=Albert_Einstein&format=json` |
| **Get categories** | `action=query&prop=categories&titles=<title>` | `?action=query&prop=categories&titles=Albert_Einstein&format=json` |
| **Category members** | `action=query&list=categorymembers&cmtitle=Category:<name>` | `?action=query&list=categorymembers&cmtitle=Category:Physics&format=json&cmlimit=50` |
| **Page previews** | `action=query&generator=search&prop=extracts|pageimages&exintro&piprop=thumbnail` | Search with thumbnail and extract previews |
| **Backlinks** | `action=query&list=backlinks&bltitle=<title>` | `?action=query&list=backlinks&bltitle=Albert_Einstein&format=json&bllimit=10` |
| **Recent changes** | `action=query&list=recentchanges` | `?action=query&list=recentchanges&rcnamespace=0&format=json&rclimit=10` |
| **Parse wikitext** | `action=parse&page=<title>&prop=text` | `?action=parse&page=Albert_Einstein&prop=text&format=json` |
| **Page properties** | `action=query&prop=pageprops&titles=<title>` | `?action=query&prop=pageprops&titles=Albert_Einstein&format=json` |

### Parameters Reference

| Parameter | Purpose | Max Per Call |
|---|---|:---:|
| `format=json` | **Always** specify JSON output (also: `xml`, `php`, `jsonfm`) | — |
| `formatversion=2` | Modern format — numeric IDs as integers, cleaner structure | — |
| `origin=*` | CORS header — required for browser-based requests from other origins | — |
| `maxlag=<seconds>` | Respect server load (use `maxlag=5` for bulk operations) | — |
| `continue` | Required for paginated results — always check for `continue` in the response | — |
| `srlimit` | Search result limit | 50 |
| `cmlimit` | Category member limit | 500 |
| `rvlimit` | Revision history limit (5,000 for bots with `apihighlimits`) | 500 |
| `uclimit` | User contributions limit (5,000 for bots) | 500 |
| `exlimit` | Extract limit | 20 |
| `tllimit` | Transcluded templates limit | 500 |
| `cllimit` | Category list limit (categories on a page) | 500 |
| `bllimit` | Backlinks limit | 500 |
| `prop=extracts|pageimages` | Combine for page previews with thumbnails | — |

> 💡 **Batch efficiently:** Most `*limit` parameters accept up to **500** per call (or 5,000 for bots). Fetching 1,000 revisions with `rvlimit=500` takes 2 HTTP requests instead of 1,000 individual calls. For a full discussion of batching strategies, see the **SOP: Batching and Pagination for Efficiency** section in the [`wikipedia-edit-history`](../wikipedia-edit-history/SKILL.md) skill.

### Pagination Pattern

```bash
# Always check for a "continue" key in the response and resume from there
curl -s "https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Physics&format=json&cmlimit=50" | jq '.continue // empty'
```

---

## 2. REST API (`api/rest_v1/`)

Modern RESTful API with predictable URLs and JSON responses.

| Base URL | Documentation |
|---|---|
| `https://en.wikipedia.org/api/rest_v1/` | [REST API docs](https://en.wikipedia.org/api/rest_v1/) |
| `https://api.wikimedia.org/core/v1/wikipedia/en/` | Wikimedia API Gateway |

### Page Content

| Endpoint | Description |
|---|---|
| `GET /page/summary/{title}` | Short summary: extract, thumbnail, description |
| `GET /page/html/{title}` | Full page HTML |
| `GET /page/mobile-html/{title}` | Mobile-optimized HTML |
| `GET /page/with-edits/{title}` | Page content with edit metadata |
| `GET /page/pdf/{title}` | PDF export of a page |
| `GET /page/mobile-sections/{title}` | Sections for mobile (legacy) |
| `GET /page/mobile-sections-lead/{title}` | Lead section for mobile (legacy) |

### Page Metadata

| Endpoint | Description |
|---|---|
| `GET /page/related/{title}` | Related pages |
| `GET /page/random` | Random page |
| `GET /page/title/{title}` | Page info (ID, revision, etc.) |
| `GET /page/{title}/links` | Links from the page |
| `GET /page/{title}/links/{ns}` | Links in a specific namespace |
| `GET /page/{title}/media` | Media files on the page |
| `GET /page/{title}/language` | Language links |

### Wikimedia API Gateway (api.wikimedia.org)

Newer, project-agnostic API. Project name is part of the path.

| Endpoint | Description |
|---|---|
| `GET /core/v1/{project}/page/summary/{title}` | Page summary (e.g., project=`en.wikipedia`, `commons.wikimedia`) |
| `GET /core/v1/{project}/page/random` | Random page from project |
| `GET /core/v1/{project}/search/page?q={query}` | Search across a project |

---

## 3. RESTBase (legacy)

Predecessor to the REST API. Still functional, being phased out.

| Base URL | Documentation |
|---|---|
| `https://en.wikipedia.org/api/rest_v1/` | (shared URL with REST API) |

| Endpoint | Description |
|---|---|
| `GET /page/summary/{title}` | Same as REST API |
| `GET /page/mobile-html/{title}` | Same as REST API |
| `GET /page/mobile-sections/{title}` | Mobile sections (legacy) |

---

## 4. Pageviews API

All pageview data is on `wikimedia.org`, not `en.wikipedia.org`.

| Base URL | Documentation |
|---|---|
| `https://wikimedia.org/api/rest_v1/metrics/pageviews/` | [Pageviews API](https://wikimedia.org/api/rest_v1/) |

### Endpoints

| Endpoint | Description |
|---|---|
| `GET /per-article/{project}/{access}/{agent}/{article}/daily/{start}/{end}` | Daily pageviews for one article |
| `GET /top/{project}/{access}/{date}` | Top articles for a given date |
| `GET /top-by-country/{country}/{date}` | Top articles by country (CC by ISO 3166) |
| `GET /top-by-ec/{project}/{access}/{year}/{month}` | Top by editing community |

### Parameters

| Field | Values |
|---|---|
| `{project}` | `en.wikipedia`, `en.wiktionary`, `commons.wikimedia`, etc. |
| `{access}` | `all-access`, `desktop`, `mobile-web`, `mobile-app` |
| `{agent}` | `all-agents`, `user`, `spider`, `automated` |
| `{date}` | `YYYY/MM/DD` (with slashes) |
| `{start}` | `YYYYMMDD` (no slashes) |
| `{end}` | `YYYYMMDD` (no slashes) |

### Notes

- Data is delayed by ~48 hours
- `{date}` uses slash format, `{start}`/`{end}` use compact format
- Top endpoint requires a specific date, not a range

---

## 5. Commons Analytics API

Pre-compiled monthly statistics for Wikimedia Commons categories and media files,
focused on GLAM (galleries, libraries, archives, museums) impact measurement.

| Base URL | Documentation |
|---|---|
| `https://wikimedia.org/api/rest_v1/metrics/commons-analytics/` | [Commons analytics](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/commons.html) |

**Important:** Only categories on the [allow list](https://gitlab.wikimedia.org/repos/data-engineering/airflow-dags/-/blob/main/main/dags/commons/commons_category_allow_list.tsv)
and their subcategories (up to 7 levels deep) have data. To add a category, see
[Commons Impact Metrics on Wikitech](https://wikitech.wikimedia.org/wiki/Commons_Impact_Metrics).

### Allow List Discovery

To see which categories are currently being processed:

```bash
curl -sL "https://gitlab.wikimedia.org/repos/data-engineering/airflow-dags/-/raw/main/main/dags/commons/commons_category_allow_list.tsv"
```

This returns a TSV of all allow-listed category names (e.g., `Smithsonian_American_Art_Museum`,
`GLAM_Wiki_Events`). Subcategories of these are automatically included up to 7 levels deep.

### Category Endpoints

| Endpoint | Description |
|---|---|
| `GET /category-metrics-snapshot/{category}/{start}/{end}` | Time series of category metrics |
| `GET /edits-per-category-monthly/{category}/{scope}/{type}/{start}/{end}` | Edit counts for a category |
| `GET /pageviews-per-category-monthly/{category}/{scope}/{wiki}/{start}/{end}` | Pageviews for category's files on a wiki |
| `GET /top-edited-categories-monthly/{scope}/{type}/{year}/{month}` | Ranking of most edited categories |
| `GET /top-viewed-categories-monthly/{scope}/{wiki}/{year}/{month}` | Ranking of categories with most pageviews |
| `GET /top-wikis-per-category-monthly/{category}/{scope}/{year}/{month}` | Which wikis use a category's files most |
| `GET /top-pages-per-category-monthly/{category}/{scope}/{wiki}/{year}/{month}` | Pages embedding a category's files |
| `GET /top-editors-monthly/{category}/{scope}/{type}/{year}/{month}` | Top editors in a category |

### Media File Endpoints

| Endpoint | Description |
|---|---|
| `GET /media-file-metrics-snapshot/{file}/{start}/{end}` | Time series for a specific media file |
| `GET /pageviews-per-media-file-monthly/{file}/{wiki}/{start}/{end}` | Pageviews for a file on a wiki |
| `GET /top-viewed-media-files-monthly/{category}/{scope}/{wiki}/{year}/{month}` | Most viewed files in a category |
| `GET /top-wikis-per-media-file-monthly/{file}/{year}/{month}` | Wikis where a file is most viewed |
| `GET /top-pages-per-media-file-monthly/{file}/{wiki}/{year}/{month}` | Pages where a file is most viewed |

### User Endpoints

| Endpoint | Description |
|---|---|
| `GET /edits-per-user-monthly/{user}/{type}/{start}/{end}` | Edit counts for a user |

### Parameters

| Parameter | Values |
|---|---|
| `{scope}` | `shallow` (category only) or `deep` (includes subcategories) |
| `{type}` | `create`, `update`, or `all-edit-types` |
| `{wiki}` | Wikimedia project code (e.g., `enwiki`, `commonswiki`, `wikidatawiki`) |
| `{start}/{end}` | `YYYYMMDD` format for snapshots, `YYYY/MM` for monthly |
| `{year}/{month}` | `YYYY` / `MM` for ranking endpoints |

### Example

```bash
# Top viewed categories on English Wikipedia (June 2025)
curl -H 'User-Agent: MyBot/1.0' \
  'https://wikimedia.org/api/rest_v1/metrics/commons-analytics/top-viewed-categories-monthly/shallow/enwiki/2025/06'

# Category metrics for a specific allow-listed category
curl -H 'User-Agent: MyBot/1.0' \
  'https://wikimedia.org/api/rest_v1/metrics/commons-analytics/category-metrics-snapshot/Smithsonian_American_Art_Museum/20250101/20250601'

# Top edited categories
curl -H 'User-Agent: MyBot/1.0' \
  'https://wikimedia.org/api/rest_v1/metrics/commons-analytics/top-edited-categories-monthly/shallow/all-edit-types/2025/06'
```

---

## 6. Lift Wing ML API

Machine learning model predictions for page and edit quality, topics, revert risk,
readability, language identification, and more. Replaces the legacy ORES system.

| Base URL | Documentation |
|---|---|
| `https://api.wikimedia.org/service/lw/inference/v1/models/` | [Lift Wing API](https://api.wikimedia.org/wiki/Lift_Wing_API) |

**Note:** This is a POST-based API (JSON request body). Unlike other Wikimedia APIs,
the endpoint path includes the model name.

### Models

#### Edit Quality (some deprecated)
| Model | Endpoint | Status |
|---|---|---|
| Goodfaith | `{wiki}-goodfaith:predict` | ⚠️ Planned deprecation |
| Damaging | `{wiki}-damaging:predict` | ⚠️ Planned deprecation |
| Reverted | `{wiki}-reverted:predict` | Active |

#### Article Quality
| Model | Endpoint | Status |
|---|---|---|
| Article quality | `{wiki}-articlequality:predict` | Active — predicts FA/GA/B/C/Start/Stub |
| Draft quality | `{wiki}-draftquality:predict` | Active |
| Language-agnostic quality | `articlequality-language-agnostic:predict` | Active |

#### Article Topic
| Model | Endpoint | Status |
|---|---|---|
| Article topic | `{wiki}-articletopic:predict` | Active |
| Draft topic | `{wiki}-drafttopic:predict` | Active |
| Topic outlinks | `articletopic-outlink:predict` | Active |

#### Revert Risk (recommended)
| Model | Endpoint | Status |
|---|---|---|
| Language-agnostic | `revertrisk-language-agnostic:predict` | Active ✅ |
| Multilingual | `revertrisk-multilingual:predict` | Active ✅ |
| Wikidata | `revertrisk-wikidata:predict` | Active |

#### Other Models
| Model | Endpoint | Status |
|---|---|---|
| Readability | `readability:predict` | Active |
| Reference need | `reference-need:predict` | Active |
| Reference risk | `reference-risk:predict` | Active |
| Language identification | `language-identification:predict` | Active |
| Content translation | `content-translation-recommendation:predict` | Active |
| Article descriptions | `article-descriptions:predict` | Active |
| Article country | `article-country:predict` | Active |

### Usage

```bash
# Revert risk prediction for a revision
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: MyBot/1.0' \
  -d '{"rev_id": 1355663707, "lang": "en"}' \
  'https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-language-agnostic:predict'

# Article quality prediction
curl -X POST \
  -H 'Content-Type: application/json' \
  -H 'User-Agent: MyBot/1.0' \
  -d '{"rev_id": 1355663707}' \
  'https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-articlequality:predict'
```

### Response Formats

**Revert risk** returns:
```json
{
  "model_name": "revertrisk-language-agnostic",
  "model_version": "3",
  "wiki_db": "enwiki",
  "revision_id": 1355663707,
  "output": {
    "prediction": false,
    "probabilities": {"true": 0.49, "false": 0.51}
  }
}
```

**Article quality** returns ORES-style output:
```json
{
  "enwiki": {
    "models": {"articlequality": {"version": "0.9.2"}},
    "scores": {
      "1355663707": {
        "articlequality": {
          "score": {
            "prediction": "FA",
            "probability": {"FA": 0.51, "GA": 0.37, ...}
          }
        }
      }
    }
  }
}
```

---

## 7. Wikidata Query Service (SPARQL)

Wikidata's structured data query endpoint.

| Base URL | Documentation |
|---|---|
| `https://query.wikidata.org/sparql` | [SPARQL endpoint](https://query.wikidata.org/) |
| `https://query.wikidata.org/embed.html` | Interactive query builder |

### Parameters

| Parameter | Required | Description |
|---|---|---|
| `format=json` | Yes | Response format |
| `query=<encoded SPARQL>` | Yes | The SPARQL query itself |

### Common Query Patterns

```sparql
-- Get all museums in a city with coordinates
SELECT ?item ?itemLabel ?coords WHERE {
  ?item wdt:P31 wd:Q33506;          # instance of museum
         wdt:P131 wd:Q90;           # located in Paris
         wdt:P625 ?coords.          # coordinate location
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}

-- Get properties and values for a specific entity
SELECT ?property ?propertyLabel ?value ?valueLabel WHERE {
  wd:Q937 ?prop ?value.             # Q937 = Albert Einstein
  ?property wikibase:directClaim ?prop .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

### Important Notes

- Always use `format=json`
- Set a descriptive User-Agent or you'll get 403 errors
- Queries have a 60-second timeout
- Use `SERVICE wikibase:label` for human-readable labels
- Use `LIMIT` to constrain results
- SPARQLWrapper Python library is recommended for complex queries

---

## 8. Entity Data (Wikidata)

Direct JSON export of Wikidata entities.

| Base URL | Description |
|---|---|
| `https://www.wikidata.org/wiki/Special:EntityData/{Q-id}.json` | Full entity data in JSON |
| `https://www.wikidata.org/wiki/Special:EntityData/{Q-id}` | HTML page with entity data |
| `https://www.wikidata.org/wiki/Special:EntityData/{Q-id}.rdf` | RDF/XML format |

### Example

```bash
curl -H "User-Agent: MyBot/1.0 (me@example.com)" \
  "https://www.wikidata.org/wiki/Special:EntityData/Q937.json"
```

---

## 9. Site-Specific URLs

Wikipedia lives on many subdomains, but the API patterns are the same:

| Project | Action API | REST API |
|---|---|---|
| English Wikipedia | `en.wikipedia.org/w/api.php` | `en.wikipedia.org/api/rest_v1/` |
| Commons | `commons.wikimedia.org/w/api.php` | `commons.wikimedia.org/api/rest_v1/` |
| Wikidata | `www.wikidata.org/w/api.php` | N/A (use EntityData or SPARQL) |
| Wiktionary | `en.wiktionary.org/w/api.php` | `en.wiktionary.org/api/rest_v1/` |
| MediaWiki.org | `www.mediawiki.org/w/api.php` | `www.mediawiki.org/api/rest_v1/` |
| Meta-Wiki | `meta.wikimedia.org/w/api.php` | `meta.wikimedia.org/api/rest_v1/` |

---

## 10. Toolforge

| Base URL | Description |
|---|---|
| `https://tools.wmflabs.org/` | Community tool hosting |
| `https://admin.toolforge.org/` | Admin console |
| `https://wikitech.wikimedia.org/wiki/Help:Toolforge/Web` | Web hosting docs |

---

## 11. Title Format Guide (Cross-API Gotcha)

A critical gotcha when chaining multiple Wikimedia APIs: they return titles in
different formats. Failing to normalize causes silent data loss (dictionary
lookups return None, batches appear empty, etc.).

| API / Endpoint | Input Format | Output Format | Example Output |
|---|---|---|---|
| Pageviews Top | N/A | **Underscores** | `Donald_Trump` |
| Pageviews Per-Article | **Underscores** | **Underscores** | `Donald_Trump` |
| Action API `prop=pageprops` | Both accepted | **Spaces** | `Donald Trump` |
| Action API `action=parse` | Both accepted | Mixed | `Donald Trump` |
| REST API `/page/summary/{title}` | Spaces recommended | Spaces | `Donald Trump` |
| SQL (`page_props`, `page` table) | N/A | **Underscores** | `Donald_Trump` |

**Rule of thumb:** When building a dictionary whose keys are titles from the
Pageviews API or SQL (both underscore-delimited), normalize to spaces before
looking up in Action API response dicts.

```python
# ❌ Wrong — Pageviews title "Donald_Trump" won't match Action API key "Donald Trump"
wid = action_api_dict.get(pageview_title)

# ✅ Correct — normalize to spaces first
wid = action_api_dict.get(pageview_title.replace('_', ' '))
```

This is especially important in the batch entity classification pipeline
(Pageviews → Action API → Wikidata), where every title goes through this
transformation and a one-line mismatch can cause 90% of data to silently
disappear.

---

## Quick Selection Guide

| Task | Best Endpoint |
|---|---|
| "Get a page summary" | REST API: `/page/summary/{title}` |
| "Search articles" | Action API: `action=query&list=search` |
| "Get page wikitext" | Action API: `action=parse&page={title}&prop=text` |
| "Category members" | Action API: `action=query&list=categorymembers` |
| "Popular pages" | Pageviews API: `/top/{project}/all-access/{date}` |
| "Historical pageviews" | Pageviews API: `/per-article/{project}/...` |
| "Find Wikidata entity" | SPARQL or EntityData |
| "Get page thumbnail" | REST API: `/page/summary/{title}` (includes thumbnail) |
| "Page HTML for a tool" | RESTBase: `/page/mobile-html/{title}` |
| "Full entity dump" | EntityData: `Special:EntityData/{Q-id}.json` |
| "Check server status" | Action API: `action=query&meta=siteinfo` |
