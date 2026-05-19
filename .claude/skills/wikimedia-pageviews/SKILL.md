---
name: wikimedia-pageviews
description: Retrieve traffic and popularity statistics for Wikipedia articles using cached SQL properties (sorting/filtering) or the REST API (precise historical data)
license: MIT
compatibility: opencode
---

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
    headers = {'User-Agent': 'MIT OCW Bot/1.0 (https://meta.wikimedia.org/wiki/Wiki_MIT; andrew.lih@gmail.com) ContentGapResearch'}
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/all-agents/{article_title}/daily/{start_date}/{end_date}"
    
    response = requests.get(url, headers=headers)
    return response.json().get('items', []) if response.status_code == 200 else []

```

## **Constraint & Guardrails**

1. **The "No Table" Rule:** The agent must **never** attempt to query a table named `pageviews`, `traffic`, or `hits` in the SQL replicas. They do not exist.
2. **SQL Casting:** The `pp_value` in `page_props` is stored as a string (BLOB). To sort numerically, the agent must use `CAST(pp_value AS UNSIGNED)`.
3. **API Rate Limits:** When fetching views for multiple pages, the agent should implement a small delay or use a single session object to avoid being throttled by the Wikimedia REST API.
4. **Title Formatting:** SQL returns titles with underscores (e.g., `Potomac,_Maryland`). The Pageview API accepts these directly, but the agent should ensure no leading/trailing spaces exist.

## **Example Use Cases**

* **SQL Cheat:** "Find the 10 most popular articles about 'Software Engineering' based on daily averages."
* **API Precise:** "How many views did the page '2024 Summer Olympics' get between July 1st and August 1st, 2024?"
* **Hybrid:** "Identify the 'Top Importance' Medicine stubs and then use the API to find which one had the highest traffic spike last week."

