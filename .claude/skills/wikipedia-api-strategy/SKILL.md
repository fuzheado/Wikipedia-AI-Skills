---
name: wikipedia-api-strategy
description: Choose the right Wikimedia API or tool for the task — a decision framework covering REST API, Action API, SPARQL, SQL database replicas, EventStreams, and Pywikibot, with latency/complexity/authentication trade-offs for each approach
depends_on: [wikimedia-api-access]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["which API", "best tool", "how to access", "API strategy", "choose between"]
  - keywords: ["REST vs Action", "SPARQL vs API", "Pywikibot vs API", "SQL vs API"]
  - keywords: ["performance", "fastest", "rate limit", "batch", "bulk", "scale"]
  - keywords: ["read only", "read write", "analytics", "real time"]
---

> ⚠️ **User-Agent required:** All API calls below need a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format, rate limiting, and error handling. If you get HTTP 403 or 429, load that skill before debugging.
>
> 💡 **Related skills:**
> - **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** — Base API patterns, User-Agent, rate limiting
> - **[wikidata](../wikidata/SKILL.md)** — SPARQL query patterns and Wikidata data model
> - **[pywikibot](../pywikibot/SKILL.md)** — Full bot framework for bulk editing
> - **[wikimedia-database](../wikimedia-database/SKILL.md)** — SQL database replicas via Toolforge SSH tunnel
> - **[wikimedia-eventstreams](../wikimedia-eventstreams/SKILL.md)** — Real-time event streaming
> - **[wikipedia-error-handling](../wikipedia-error-handling/SKILL.md)** — Error recovery for any approach

---

## Quick Decision Flowchart

```
What do you want to do?
│
├─ Read a single page or its summary?
│   → REST API (/page/summary, /page/html)       [fastest, simplest]
│
├─ Read multiple pages with filters?
│   ├─ Simple filter (by category, template, user)?
│   │   → Action API (list=categorymembers, etc.) [good for <500 items]
│   ├─ Complex relational query across entities?
│   │   → SPARQL (Wikidata Query Service)          [good for graph queries]
│   └─ Bulk analytics across millions of rows?
│       → SQL replicas (Toolforge database)        [100-1000× faster than API]
│
├─ Monitor changes in real-time?
│   → EventStreams (SSE)                           [only way for live data]
│
├─ Edit pages, run bots, or bulk operations?
│   → Pywikibot                                    [framework for all write ops]
│
└─ Check a page's patrol status or triage new pages?
    → PageTriage API                               [specialized extension]
```

---

## Reference: The Six Access Methods

| # | Method | Best For | Read/Write | Latency | Rate Limit | Auth Needed? | Base URL |
|:-:|--------|----------|:----------:|:-------:|:----------:|:------------:|----------|
| 1 | **REST API** | Single page reads, summaries, HTML content | Read only | Low (~200ms) | Per IP | No | `https://en.wikipedia.org/api/rest_v1/` |
| 2 | **Action API** | Multi-page queries, filtering, metadata, edits | Read + Write | Low (~200ms) | 200 req/s burst, 50 sustained | For edits | `https://en.wikipedia.org/w/api.php` |
| 3 | **SPARQL** | Complex graph queries, cross-entity relations | Read only | Medium (1-30s) | 1 req/s sustained, 60s timeout | No | `https://query.wikidata.org/sparql` |
| 4 | **SQL Replicas** | Bulk analytics, JOINs across tables, aggregates | Read only | Medium (~1s per query) | Connection pool limited | SSH tunnel + DB creds | Via Toolforge tunnel |
| 5 | **EventStreams** | Real-time monitoring, live feeds | Read only | Real-time (push) | None (server pushes) | No | `https://stream.wikimedia.org/v2/stream/` |
| 6 | **Pywikibot** | Bot operations, bulk edits, framework | Read + Write | Varies | Bot-specific | Bot password | Wraps Action API |

---

## Decision Trees by Task Category

### A. Reading Page Content

| If you need... | Use... | Because... |
|----------------|--------|------------|
| A page's first paragraph + thumbnail | **REST API** (`/page/summary/{title}`) | Fastest, simplest JSON, no pagination |
| Full rendered HTML of a page | **REST API** (`/page/html/{title}`) | Pre-rendered, ready for CSS/JS parsing |
| Raw wikitext of a page | **Action API** (`action=parse&prop=wikitext`) | REST API doesn't expose raw wikitext |
| Multiple pages' content at once | **Action API** with `titles=TITLE1\|TITLE2` | Batch up to 50 titles per call |
| A single revision's content | **REST API** (`/revision/{id}/content`) | Direct by revision ID, no page lookup needed |

**❌ Common mistake:** Using `action=parse` for a single page summary when the REST API's `/page/summary` returns cleaner JSON in one call.

### B. Querying Multiple Pages with Filters

| If you need... | Use... | Because... |
|----------------|--------|------------|
| Pages in a category (flat) | **Action API** (`list=categorymembers`) | Direct, paginated, namespace filterable |
| Pages in a category tree (recursive) | **Action API** with `cmtype=page\|subcat` loop, or **SQL replicas** (faster) | The API is simpler but slower; SQL is 100× faster for deep trees |
| Pages using a template | **Action API** (`list=embeddedin`) | Direct `eititle` parameter, paginated |
| Pages edited by a user | **Action API** (`list=usercontribs`) | Direct `ucuser` parameter, date-range filterable |
| Pages matching a text search | **Action API** (`list=search`) or **REST API** (`/search/page`) | REST API returns cleaner results; Action API supports more filters |
| Complex cross-page analytics (e.g., "pages in Category:Physics sorted by pageviews with quality assessments") | **SQL replicas** | Would require 500+ API calls. One SQL query with JOINs handles it in seconds. |

**❌ Common mistake:** Using `list=categorymembers` + individual API calls per page for analytics (e.g., fetching pageviews for 100 articles). Instead: use SQL replicas for the JOIN, or SPARQL + batch pageviews call.

### C. Graph Queries and Structured Data

| If you need... | Use... | Because... |
|----------------|--------|------------|
| "Find all X that have property Y" | **SPARQL** | One query replaces N API calls |
| Cross-language article mapping | **SPARQL** (`schema:about`/`schema:isPartOf`) | Sitelinks are not queryable via regular properties |
| Items missing a property (e.g., no image) | **SPARQL** (`FILTER NOT EXISTS`) | Can't express "does not have" in the Action API |
| Simple property lookup for a known item | **Action API** (`wbgetentities`) | Faster than SPARQL for single-item lookups |
| Batch entity classification (e.g., "which of these 100 items are people?") | **Action API** (`wbgetentities` batch of 50) | Faster than 100 SPARQL calls; use SPARQL only if you need subclass traversal |

**❌ Common mistake:** Using SPARQL for single-item lookups. `wbgetentities` returns the same data in ~200ms vs SPARQL's ~2-30s.

### D. Bulk Data and Analytics

| If you need... | Use... | Because... |
|----------------|--------|------------|
| Top 100 most-viewed pages in a category | **SQL replicas** (`page_props` JOIN `categorylinks`) | One query. Equivalent API approach would require: (1) fetch category members, (2) fetch pageviews for each = 100+ API calls |
| Correlation between quality and pageviews | **SQL replicas** (`page_assessments` JOIN `page_props`) | Single JOIN vs hundreds of API calls |
| Count of articles by quality class for a WikiProject | **SQL replicas** | `SELECT pa_class, COUNT(*) ... GROUP BY pa_class` in seconds |
| Quick sort by pageviews for a small set (<50 articles) | **REST API** (`/pageviews/per-article/...`) | Simpler than setting up a database tunnel |
| One-time ad-hoc analysis of a few articles | **Action API** | No SSH tunnel setup needed |

**❌ Common mistake:** Using the API for what should be a database query. If you find yourself writing a loop that makes >50 API calls for the same type of data, switch to SQL replicas or SPARQL.

### E. Real-Time Monitoring

| If you need... | Use... | Because... |
|----------------|--------|------------|
| Watch edits as they happen | **EventStreams** (`recentchange` stream) | Only way to get sub-second notifications |
| Monitor new page creations | **EventStreams** (filter `type == "new"`) | Faster than polling `list=recentchanges` |
| Build a live dashboard | **EventStreams** + periodic API snapshots | Stream gives live data, API fills history |
| Historical replay of past events | **EventStreams** (`?since=` parameter) | Up to 31 days of replay available |
| Check if a specific page was recently edited | **Action API** (`prop=revisions&rvlimit=1`) | Simpler than consuming a stream for one check |

**❌ Common mistake:** Polling `list=recentchanges` every few seconds instead of using EventStreams. Polling wastes API rate limits and introduces latency. The stream pushes data instantly.

### F. Editing and Bot Operations

| If you need... | Use... | Because... |
|----------------|--------|------------|
| Make a single edit | **Action API** (`action=edit`) | Simple, no framework setup needed |
| Make many edits with consistent logic | **Pywikibot** | Built-in rate limiting, edit summaries, conflict detection, page generators |
| Bulk template replacement across a category | **Pywikibot** (`replace.py` script) | Ready-made script, handles page loading/saving/conflicts |
| Scrape infobox data into Wikidata | **Pywikibot** (`harvest_template.py` script) | Purpose-built for this exact workflow |
| Move/delete pages in bulk | **Pywikibot** (built-in scripts) | Handles redirects, rate limits, and error recovery |
| Upload media to Commons | **Pywikibot** (`image_transfer.py`) | Preserves attribution history across wikis |

**❌ Common mistake:** Writing raw `action=edit` API calls for bulk operations. Pywikibot handles throttling (`put_throttle`), edit conflict detection, and automatic retry — all of which you'd need to implement from scratch with the raw API.

---

## Performance Comparison: API vs. SQL for the Same Task

This table shows how much work each approach requires for an equivalent result:

| Task | Action API | SPARQL | SQL Replicas | Speed Ratio |
|------|:----------:|:------:|:------------:|:-----------:|
| Top 50 articles in a category by pageviews | 50-200 calls (category + pageviews per article) | 1 query (with pageview data caveats) | **1 query** (JOIN) | **API:SQL ≈ 1:200** |
| Count articles by quality class for a WikiProject | 1 call per assessment × N pages | 1 query (if items have P31) | **1 query** (GROUP BY) | **API:SQL ≈ 1:500** |
| "Find all physicists born before 1900" | Not feasible (would need to scan all pages) | **1 query** | Complex (would need wikidata IDs) | **SPARQL:API ≈ 1:∞** |
| Fetch 10 random article summaries | **1 call** (REST API, 10 titles) | Overkill | Overkill | **REST is fastest** |
| Monitor new pages for 1 hour | 360 polls × API calls | Not applicable | Not applicable | **EventStreams:API ≈ 1:360** |

> 💡 **Rule of thumb:** If your task involves more than 50 individual items, consider whether a single SPARQL query or SQL query could replace the loop.

---

## SOP: Strategy Selection in Practice

### Step 1: Define Your Task

```
Is it:
  A single page/entity?       → Method 1 or 2
  A batch of related items?   → Method 2, 3, or 4
  A complex relation?          → Method 3 (SPARQL)
  Bulk analytics?              → Method 4 (SQL)
  Real-time?                   → Method 5 (EventStreams)
  Writing/editing?             → Method 6 (Pywikibot) or 2 (Action API)
```

### Step 2: Check Constraints

```
Do you have:
  Database access (SSH + credentials)?   → SQL replicas available
  A registered bot account?              → Pywikibot available (higher rate limits)
  No authentication at all?              → REST/Action API (read-only), SPARQL, EventStreams
  A need for speed?                      → REST API (fastest for reads), SQL (fastest for analytics)
```

### Step 3: Combine When Necessary

Some of the most powerful workflows **combine** methods:

```
1.  Action API (categorymembers)  →  Get list of articles
2.  + SPARQL (sitelinks)          →  Cross-reference with Wikidata
3.  + REST API (pageviews)        →  Rank by popularity
4.  + Pywikibot (editing)         →  Act on the results
```

Or an even faster alternative using SQL:

```
1.  SQL replicas (JOIN)           →  All analytics in one query
2.  + Pywikibot (editing)         →  Act on the results
```

### Step 4: Avoid Common Anti-Patterns

| ❌ Anti-Pattern | Why | ✅ Better Approach |
|---|---|---|
| Polling `list=recentchanges` every 5 seconds | Wastes rate limit, misses events | Use EventStreams for push-based monitoring |
| Fetching pageviews for 100+ articles one by one via REST API | 100+ API calls, takes minutes | Use SQL `page_props` JOIN or batch the API calls |
| SPARQL query for a single known QID | 2-30s response time for a 200ms task | Use `wbgetentities` via Action API |
| Raw `action=edit` for a 1000-page template migration | No throttling, no conflict handling, no edit summary enforcement | Use Pywikibot `replace.py` |
| Looping through category members with individual API calls per page | N+1 query problem | Use SQL replicas or batch API calls |
| Fetching full page wikitext just to get the page ID | Wasteful — ridiculously oversized response | Use `prop=info&inprop=url` (much smaller response) |
| Using the Action API when you need rendered HTML | Returns raw wikitext, requires client-side rendering | Use REST API `/page/html/{title}` for ready-to-render HTML |
| Implementing your own bot framework | You'll rewrite Pywikibot's throttling, conflict detection, and page generators from scratch | Use Pywikibot — it has 20+ years of battle-testing |

---

## Appendix: Quick Reference Cards

### Read Operations — Fastest Path by Data Size

```
1-10 items     → REST API (single calls)
10-500 items   → Action API (batch parameters, list modules)
500-5000 items → SPARQL (one query) or Action API (paginated)
5000+ items    → SQL replicas (single JOIN/aggregation query)
```

### Write Operations — By Scale

```
1 edit         → Action API (action=edit, simplest)
10-100 edits   → Pywikibot (custom script with page generator)
100+ edits     → Pywikibot (built-in scripts like replace.py, harvest_template.py)
```

### Real-Time Data

```
Live monitoring     → EventStreams (SSE push)
Periodic checks     → Action API (polling, but minimize frequency)
Historical replay   → EventStreams (?since= parameter, up to 31 days)
```

### Authentication Requirements

```
Read-only, no auth     → REST API, Action API (query), SPARQL, EventStreams
Read + Write           → Bot password (Action API) or OAuth (Pywikibot)
SQL replicas           → Toolforge SSH key + database credentials
Higher rate limits     → OAuth (Lift Wing, REST API) or bot flag (Pywikibot)
```
