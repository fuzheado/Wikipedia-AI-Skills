---
name: wikimedia-pageviews
description: Retrieve traffic and popularity statistics for Wikipedia articles via the Wikimedia pageviews/AQS REST API — top-pages ranking, per-article history, media requests, and why the old page_props popularity cache no longer works
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["pageviews", "traffic", "popularity", "article views", "views per article"]
  - keywords: ["top pages", "pageview API", "daily views", "analytics"]
  - keywords: ["media views", "mediarequests", "file views", "image views", "media requests"]
last_verified: 2026-10-03
---

> ⚠️ **User-Agent required:** The REST API examples below require a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

Enables the agent to retrieve traffic and popularity statistics for Wikipedia articles. Historical pageview logs are not stored in the SQL replicas, and the old `page_props` popularity cache (`pageview_daily_average`) is no longer populated — **the API is the source of truth**, and SQL is only for producing the candidate set to rank (see Scenario A).

## **SOP: Data Source Selection**

### **Scenario A: Sorting/Filtering by General Popularity — no SQL path today**

⚠️ **The `page_props` popularity cache is retired.** The property this skill used to recommend,
`pageview_daily_average`, has **0 rows** on enwiki, commons, dewiki, frwiki, nlwiki and
wikidatawiki (verified 2026-09-20), and no `pageview*` property exists on any of them — while
`page_props` itself is healthy (`wikibase_item` has 10.3M rows on enwiki). Queries filtering on it
still parse, then return an **empty result set**: a silent wrong answer, not an error.
([Tool:Popular Pages](https://wikitech.wikimedia.org/wiki/Tool:Popular_Pages) reads the PageviewAPI
rather than writing a property.)

For "Top 100 most viewed pages in Category:Physics", the working shape is:

1. **Candidate set from SQL** — category membership via `categorylinks` + `linktarget` (no popularity data needed).
2. **Rank with the API** — AQS `pageviews/per-article` for a bounded set, the `top` endpoints for a
   site-wide ranking, or the [popularpages](https://github.com/wikimedia/popularpages) reports.
   Batch and pace per the wikimedia-api-access skill.

The SQL shortcut below is kept as the pattern to use **if** a popularity property is restored; do not
expect rows from it today.

* **Property Name (retired):** `pageview_daily_average`
* **Table:** `page_props`
* **Historical implementation:**

```sql
SELECT 
    p.page_title, 
    pp.pp_value AS avg_daily_views
FROM page p
JOIN page_props pp ON p.page_id = pp.pp_page
WHERE pp.pp_propname = 'pageview_daily_average'
  AND p.page_namespace = 0
ORDER BY CAST(pp.pp_value AS UNSIGNED) DESC
LIMIT 50;

```

### **Scenario B: Precise Historical Data (REST API)**

If the task requires specific dates, trends, or "total views last month," the agent must use the **Analytics QuickMetrics API**.

> **Batch shortcut for known sets:** if you need recent pageviews (rolling ~60
> days) for a *known set* of articles, skip the per-article loop — the Action
> API `prop=pageviews` returns up to **50 titles per call**. See
> `references/pageview-api.md` → "Batch: Action API prop=pageviews".

* **Endpoint:** `[https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/](https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/)`
* **Access Pattern:** `project / access / agent / article / granularity / start / end`
* **Implementation Pattern (Python):**

```python
import requests

def get_historical_views(article_title, start_date, end_date, project='en.wikipedia'):
    """
    article_title: Use underscores (e.g., 'Albert_Einstein')
    dates: 'YYYYMMDD' format
    """
    headers = {'User-Agent': 'Wiki Bot/1.0 (https://meta.wikimedia.org; your-email@example.com) WikiBot'}
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/all-agents/{article_title}/daily/{start_date}/{end_date}"
    
    response = requests.get(url, headers=headers, timeout=30)
    return response.json().get('items', []) if response.status_code == 200 else []

```

### **Scenario C: Getting the Most Popular Pages (REST API Top Endpoint)

If the task requires finding the most-viewed pages across a project (e.g.,
"Top 100 most read articles on English Wikipedia"), use the Top Pages REST
endpoint. This is much faster than querying per-article for thousands of pages.

* **Endpoint:** `https://wikimedia.org/api/rest_v1/metrics/pageviews/top/{project}/all-access/{date}`
* **Date Format:** `YYYY/MM/DD` with slashes (⚠️ different from the per-article
  endpoint which uses compact `YYYYMMDD`)
* **Data Lag:** ~48 hours (use a date at least 2 days ago)
* **Title Format:** Returns titles **with underscores** (e.g., `Donald_Trump`)

```python
import requests
from datetime import datetime, timedelta

headers = {'User-Agent': 'MyBot/1.0 (me@example.com) ContentGapResearch'}
end = datetime.utcnow() - timedelta(days=3)
date_str = end.strftime('%Y/%m/%d')  # Slashes: 2026/05/25

url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/top/en.wikipedia/all-access/{date_str}"
resp = requests.get(url, headers=headers, timeout=30)
data = resp.json()
for article in data['items'][0]['articles'][:10]:
    print(f"{article['rank']}. {article['article']} — {article['views']} views")
```

**Cross-API chaining:** The Top Pages endpoint is often the first step in a
pipeline that classifies popular articles by entity type. When chaining its
output with the Action API (e.g., to resolve Wikidata IDs), **normalize titles
from underscores to spaces** before looking up in Action API response
dictionaries:

```python
top_title = "Donald_Trump"  # from Pageviews Top
wikidata_id = action_api_dict.get(top_title.replace('_', ' '))  # ✅
# wikidata_id = action_api_dict.get(top_title)  # ❌ returns None
```

See the **Batch Entity Classification** SOP in the
[`wikidata`](../wikidata/SKILL.md#sop-batch-entity-classification-from-wikipedia-titles)
skill for the full pipeline, and the **Title Format Guide** in the
[`wikimedia-api-access`](../wikimedia-api-access/references/endpoints.md#11-title-format-guide-cross-api-gotcha)
endpoint reference for the complete cross-API table.

---

---

## **Media Views (mediarequests) — image/file load counts**

Pageview metrics count **page loads**; they do not count how often an image or
media file was actually served. For the latter, use the **Media Requests API**
(`/metrics/mediarequests/`):

- **Per-file time series (exists, tricky path):**
 `https://wikimedia.org/api/rest_v1/metrics/mediarequests/per-file/{referer}/{agent-type}/{file-path}/{granularity}/{start}/{end}`
 - `file-path` is the upload path URL-encoded **with the leading slash**
 (`/wikipedia/commons/0/00/Crab_Nebula.jpg` -> `%2Fwikipedia%2Fcommons%2F0%2F00%2FCrab_Nebula.jpg`;
 omit the slash and you get 404 "invalid route"). `referer` is
 `all-referers|internal|external|unknown` or a project domain; `agent-type` is
 `user|spider|all-agents`; `granularity` is `daily|monthly`.
 (Corrected 2026-08-14: an earlier note claimed per-file was removed - that
 was a path-format error.)
 - ⚠️ **`agent-type=automated` returns HTTP 400 on every mediarequests route**
 (verified 2026-09-05: per-file and aggregate, all referer values). There is no
 automated bin in the data: `all-agents` = `user` + `spider` exactly (diff 0 —
 re-verified 2026-09-15), so automated clients' image requests are **UA-counted
 as `user`** — media "user" ≠ pageview "user". HTML-only fetchers request ~no
 images, but for any request-per-pageview ratio pair media-user with
 pageviews(**user + automated**), or you inflate by 1/(1 − automated share) on
 high-agent articles.
- Per-day aggregate:
 `https://wikimedia.org/api/rest_v1/metrics/mediarequests/top/{referer}/{media-type}/{year}/{month}/{day}`
 - returns the day's top media files (`file_path`, `requests`, `rank`).
 `media-type` is one of `all-media-types`, `image`, `video`, `audio`,
 `document`, `other`; `referer` accepts `all-referers` or a project domain.
- ⚠️ **Only the top 1,000 files per day are returned.** A long-tail file
  missing from that day's top-1000 has no API-accessible count — aggregate
  over several days if you need a range.
- **Description-page views ≠ media views.** `pageviews/per-article` on a
  `File:` page counts views of the description page (typically a few dozen/day);
  media requests count every load of the underlying file (often thousands×
  more). Never use pageviews to answer "how many people viewed this image".
- **Pageviews ≠ media usage, generally.** Pageviews count *page loads*, never
  *media-file transfers/views*. For "how many times was a file served" use the
  **mediarequests AQS API** (`metrics/mediarequests/{aggregate,top,per-file}`);
  for "where is it embedded" use **GlobalUsage** (`prop=globalusage`); for
  "off-wiki reuse" use the **mediacounts `referer_external`** field. Full
  method matrix + gotchas: `wikimedia-commons` skill →
  `wikimedia-commons/references/media-usage-metrics.md`.

## **Constraint & Guardrails**

1. **The "No Table" Rule:** The agent must **never** attempt to query a table named `pageviews`, `traffic`, or `hits` in the SQL replicas. They do not exist.
2. **SQL Casting (historical):** when a `page_props` value is involved, `pp_value` is stored as a string (BLOB) — use `CAST(pp_value AS UNSIGNED)` to sort numerically. For `pageview_daily_average` this is moot: the property has no rows anywhere (see Scenario A).
3. **API Rate Limits:** When fetching views for multiple pages, the agent should implement a small delay or use a single session object to avoid being throttled by the Wikimedia REST API.
4. **Title Formatting:** SQL returns titles with underscores (e.g., `Potomac,_Maryland`). The Pageview API accepts these directly, but the agent should ensure no leading/trailing spaces exist.


## **Example Use Cases**

* **SQL Cheat:** "Find the 10 most popular articles about 'Software Engineering' based on daily averages."
* **API Precise:** "How many views did the page '2024 Summer Olympics' get between July 1st and August 1st, 2024?"
* **Hybrid:** "Identify the 'Top Importance' Medicine stubs and then use the API to find which one had the highest traffic spike last week."

---

## **Tooling**

This skill includes helper scripts, reference docs, and templates:

### 🔧 Top Pages (`scripts/top-pages.sh`)

Fetch the most viewed articles for a Wikimedia project on a given date.

```bash
./scripts/top-pages.sh [project] [date] [limit]

# Default: top 25 on en.wikipedia from 3 days ago
./scripts/top-pages.sh

# Top 50 on German Wikipedia
./scripts/top-pages.sh de.wikipedia 2026/05/20 50

# Top 10 on Commons
./scripts/top-pages.sh commons.wikimedia 2026/05/20 10
```

### 🔧 Per-Article Pageviews (`scripts/per-article.sh`)

Fetch historical daily pageviews for a specific article with a visual bar chart.

```bash
./scripts/per-article.sh <article_title> [start_date] [end_date] [project]

# Last 7 days
./scripts/per-article.sh Albert_Einstein

# Custom date range
./scripts/per-article.sh "Python_(programming_language)" 20260101 20260301

# Different project
./scripts/per-article.sh Barack_Obama 20240101 20241231 en.wikipedia
```

### 📚 Pageview API Reference (`references/pageview-api.md`)

Full reference for the Wikimedia Pageviews REST API:
- All endpoints (top, per-article, top-by-country, top-by-ec)
- Date format reference (slash vs compact — a common gotcha)
- Common query patterns with examples
- Error response guide

### 🐍 Analysis Template (`assets/analysis-template.py`)

A Python tool for fetching and analyzing pageview data:

```bash
# Top N articles
python3 assets/analysis-template.py --top 10

# Analyze an article's trend (30 days by default)
python3 assets/analysis-template.py Albert_Einstein 90

# Compare desktop vs mobile vs app
python3 assets/analysis-template.py Albert_Einstein 30 --compare

# Detailed daily breakdown
python3 assets/analysis-template.py Albert_Einstein 14 --detailed

# Raw JSON output (for further processing)
python3 assets/analysis-template.py Albert_Einstein 7 --json
```

Features:
- Trend analysis (up/down/stable) with daily change percentage
- Peak/low detection
- Access method comparison
- JSON export mode

### 🧩 Sample SQL Queries (`assets/example-queries.sql`)

SQL queries for working with pageview data in the `page_props` table — ⚠️ they query the **retired** `pageview_daily_average` property (0 rows on six wikis, see Scenario A), so they return empty result sets. Kept as the pattern for a future popularity property; the file header repeats this.
- Top pages by category
- Overall most viewed
- Pages without pageview data
- Cross-reference views vs editor interest
- Stubs with unexpectedly high traffic

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent and API patterns for REST API calls |
| **[wikidata](../wikidata/SKILL.md)** | Batch entity classification pipeline — resolve article titles to QIDs |
| **[wikimedia-page-assessment](../wikimedia-page-assessment/SKILL.md)** | Quality and importance ratings — Popular_pages bot bridges pageviews and assessments |
| **[wikipedia-categories](../wikipedia-categories/SKILL.md)** | Most-viewed-in-category workflows |
