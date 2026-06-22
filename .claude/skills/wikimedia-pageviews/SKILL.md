---
name: wikimedia-pageviews
description: Retrieve traffic and popularity statistics for Wikipedia articles using cached SQL properties (sorting/filtering) or the REST API (precise historical data)
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["pageviews", "traffic", "popularity", "article views", "views per article"]
  - keywords: ["top pages", "pageview API", "daily views", "analytics"]
last_verified: 2026-06-10
---

> ⚠️ **User-Agent required:** The REST API examples below require a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

Enables the agent to retrieve traffic and popularity statistics for Wikipedia articles. Since historical pageview logs are not stored in the SQL replicas, the agent must distinguish between using a **cached SQL property** for sorting and the **REST API** for precise historical data.

## **SOP: Data Source Selection**

### **Scenario A: Sorting/Filtering by General Popularity (SQL)**

If the task requires finding "popular pages" within a large SQL result set (e.g., "Top 100 most viewed pages in Category:Physics"), use the `page_props` table. This is much faster than making 100 API calls.

* **Property Name:** `pageview_daily_average`
* **Table:** `page_props`
* **Implementation:**

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

## **Constraint & Guardrails**

1. **The "No Table" Rule:** The agent must **never** attempt to query a table named `pageviews`, `traffic`, or `hits` in the SQL replicas. They do not exist.
2. **SQL Casting:** The `pp_value` in `page_props` is stored as a string (BLOB). To sort numerically, the agent must use `CAST(pp_value AS UNSIGNED)`.
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

SQL queries for working with pageview data in the `page_props` table:
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
