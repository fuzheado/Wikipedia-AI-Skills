---
name: wikimedia-api-access
description: Access Wikipedia and Wikimedia APIs (REST, Action API, SPARQL) with correct User-Agent headers, rate limiting, and 429/403 error handling
license: MIT
compatibility: opencode
---

All requests to Wikimedia APIs **must** include a descriptive `User-Agent` header or they will be blocked (HTTP 403 or 429). This is enforced by the [Wikimedia Foundation User-Agent Policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy).

> **💡 Pi users:** If you use the [pi coding agent](https://github.com/earendil-works/pi-coding-agent), install the companion extension from this repo to **automatically inject the User-Agent header** on every `curl`, `wget`, `python`, and `node` command that targets a Wikimedia server — no manual intervention needed. See the [README](../../../README.md#pi-agent-setup) for setup instructions.

## **User-Agent Format**

The generic format is:

```
<client name>/<version> (<contact information>) <project identifier>/<version>
```

Parts that are not applicable can be omitted. The contact information should be an email address, website URL, or wiki user page.

### **Required Pattern**

```python
headers = {
    'User-Agent': 'YourBot/1.0 (https://your-site.com; your@email.com) ProjectName'
}
```

The `ProjectName` (e.g. `ContentGapResearch`) helps Wikimedia distinguish traffic from different tools.

### **Concrete Example**

```python
import requests

headers = {
    'User-Agent': 'my-wiki-bot/1.0 (https://example.com; user@example.com) ContentGapResearch'
}

response = requests.get('https://en.wikipedia.org/w/api.php', headers=headers)
```

## **Why This Matters**

- Requests without a `User-Agent` or with generic agents (`python-requests/x`, `curl`, `Python-urllib`) are blocked with HTTP **403** or **429** errors.
- A descriptive UA allows Wikimedia to contact you if your bot misbehaves.
- Always include "bot" in the UA string (case-insensitive) for automated agents — this helps Wikimedia classify traffic correctly and provide accurate statistics.
- **Never** copy a browser's UA string for bot requests — bot-like behavior with a browser UA will be treated as malicious.

## **Key API Endpoints**

| API | Base URL | Common Use |
|-----|----------|------------|
| Action API | `https://en.wikipedia.org/w/api.php` | Search, page content, edits, categories |
| REST API | `https://en.wikipedia.org/api/rest_v1/` | Page summaries, mobile content, transforms |
| Pageviews | `https://wikimedia.org/api/rest_v1/metrics/pageviews/` | Traffic statistics |
| Commons Analytics | `https://wikimedia.org/api/rest_v1/metrics/commons-analytics/` | GLAM category/file usage stats (monthly, pre-compiled) |
| Lift Wing ML | `https://api.wikimedia.org/service/lw/inference/v1/models/` | ML predictions (revert risk, article quality, topics) |
| Wikidata Query (SPARQL) | `https://query.wikidata.org/sparql` | Structured data queries |
| Toolforge | `https://tools.wmflabs.org/` | Community tool hosting |

> 💡 **These APIs are project-agnostic.** The Action API and REST API shown above with `en.wikipedia.org` are MediaWiki APIs that work on **any** Wikimedia project — just swap the domain. For example:
> - **Commons:** `https://commons.wikimedia.org/w/api.php` — search media files, fetch EXIF metadata, inspect categories
> - **Wikidata:** `https://www.wikidata.org/w/api.php` — query entities, manage labels and descriptions, fetch claims
> - **Wiktionary:** `https://en.wiktionary.org/w/api.php` — dictionary data, word definitions, etymology
> - **Meta-Wiki:** `https://meta.wikimedia.org/w/api.php` — global user info, cross-wiki settings, Wikimedia Foundation policies
>
> The query parameters and response structures are the same; only the domain and the wiki's content differ.

## **General Implementation Pattern**

```python
import requests
import time

SESSION = requests.Session()
SESSION.headers.update({
    'User-Agent': 'my-wiki-bot/1.0 (https://example.com; user@example.com) ContentGapResearch'
})

def wikimedia_request(url, params=None, max_retries=3):
    for attempt in range(max_retries):
        resp = SESSION.get(url, params=params, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 429:
            retry_after = int(resp.headers.get('Retry-After', 10))
            time.sleep(retry_after)
            continue
        if resp.status_code == 403:
            raise PermissionError(
                "403 Forbidden — likely a missing or invalid User-Agent. "
                "See: https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy"
            )
        resp.raise_for_status()
    raise Exception(f"Request failed after {max_retries} retries")
```

### **Browser-Based JavaScript**

Browser JavaScript cannot control the `User-Agent` header (the browser sets it). Instead, use the `Api-User-Agent` header:

```javascript
fetch('https://en.wikipedia.org/w/api.php?action=query&format=json', {
    headers: new Headers({
        'Api-User-Agent': 'MyScript/1.0'
    })
})
```

## **Rate Limiting & Error Handling Guardrails**

1. **Connection reuse** — Always use a `requests.Session()` (or equivalent) to reuse connections. Do not create a new connection per request.
2. **Retry-After** — On 429, respect the `Retry-After` header value. Never retry immediately.
3. **Pacing & Batching** — For batch operations, add a small delay (at least 0.5s) between requests. For the Action API, respect the `maxlag` parameter. **Always use the largest batch size the API supports** (e.g., `rvlimit=500`, `uclimit=500`) rather than fetching items one at a time. See the **SOP: Batching and Pagination for Efficiency** in the [`wikipedia-edit-history`](../wikipedia-edit-history/SKILL.md) skill for detailed patterns.
4. **403 handling** — A 403 almost always means a bad/missing UA. Check the UA string before debugging anything else.
5. **User-Agent per project** — Parameterize the contact info so users can swap in their own details. Never hardcode someone else's email.
6. **SPARQL queries** — For Wikidata Query Service, always set the UA and use `&format=json`. Consider using `SPARQLWrapper` with the `agent` parameter.

### 429 Retry-After Handling

When a 429 (Too Many Requests) response is received, Wikimedia includes a
`Retry-After` header specifying the number of seconds to wait. **Do not retry
immediately with a fixed backoff** (e.g., always waiting exactly 5 seconds)
— this is counterproductive and may lead to a temporary ban. Always use the
server-supplied value:

```python
if resp.status_code == 429:
    retry_after = int(resp.headers.get('Retry-After', 10))
    time.sleep(retry_after)
    continue  # retry the request in a loop
```

### Common Causes of 429 Responses

- **Too many requests in a short window** even with a proper User-Agent.
  Stay under ~2 requests/second for batch operations, and add deliberate
  delays (0.3–0.5s) between requests.
- **Too many titles in a single `titles` parameter.** Keep batches under 50
  titles per call for `prop=pageprops` and 50 IDs per call for `wbgetentities`.
- **Fetching very large pages via `action=parse` without a section limit.**
  Add `rvsection=0` or `section=0` if you only need the lead section, or
  use `exintro` with `prop=extracts` for a concise summary.

## **Example Use Cases**

- **Fetch article content:** "Get the wikitext for 'Python (programming language)' using the Action API."
- **Search:** "Search English Wikipedia for articles about 'machine learning' and return the top 10 titles."
- **Get page metadata:** "Using the REST API, get the description and thumbnail for 'Albert Einstein'."
- **SPARQL query:** "Query Wikidata for all museums in Paris with their coordinates."
- **Batch lookup:** "For each page in this list of 50 titles, fetch the page ID and word count from the API."
- **Troubleshoot 403:** "Check the User-Agent header and confirm it follows the Wikimedia format."

---

## **Tooling**

This skill includes helper scripts, reference docs, and templates:

### 🔧 Connectivity Test (`scripts/test-api.sh`)

Tests 14 endpoints across 6 API families with your User-Agent and reports which ones work.

```bash
# Test with the default User-Agent
./scripts/test-api.sh

# Test with YOUR User-Agent
./scripts/test-api.sh "MyBot/1.0 (https://example.com; me@example.com) MyProject"
```

Tests 14 endpoints across 6 API families:
- 📡 Core APIs (Action API: siteinfo, search, page content) — 3 tests
- 🌐 REST APIs (page summary, mobile-html) — 3 tests
- 🔗 SPARQL / Wikidata — 2 tests
- 📊 Pageviews API — 1 test
- 🖼️  Commons Analytics API — 3 tests (category metrics, top wikis, top edited)
- 🧠 Lift Wing ML API — 2 tests (POST-based, revert risk + article quality)

**Note on Commons Analytics:** Data is only available for categories on the
[allow list](https://gitlab.wikimedia.org/repos/data-engineering/airflow-dags/-/blob/main/main/dags/commons/commons_category_allow_list.tsv)
and their subcategories. The `category-metrics-snapshot` and `top-wikis-per-category`
tests use `Smithsonian_American_Art_Museum` (an allow-listed category) and should
return data. See `references/endpoints.md` for details on the allow list.

### 📚 API Endpoint Reference (`references/endpoints.md`)

Full catalog of Wikimedia endpoints organized by API family:
- Action API parameters and pagination pattern
- REST API and RESTBase endpoints
- Pageviews API parameters and date formats
- SPARQL query patterns
- Quick selection guide (task → best endpoint)

Read it when you need to find the right endpoint:

```bash
# Load by asking the agent, or reference directly
cat references/endpoints.md
```

### 🐍 Python Client Template (`assets/user-agent-template.py`)

A ready-to-use Python client with:
- Proper User-Agent configuration
- `requests.Session` with connection reuse
- Rate limiting (configurable delay between requests)
- Automatic retry with exponential backoff on 429/timeouts
- Helpful error messages for 403 (bad UA) and 404
- Convenience methods for all major API types
- Works as a standalone demo script

```bash
# Copy and customize
cp assets/user-agent-template.py my_bot.py
# Edit my_bot.py with your User-Agent, then run
python3 my_bot.py
```

Supports:
```python
from user_agent_template import WikimediaClient

with WikimediaClient("MyBot/1.0 (user@example.com) MyProject") as client:
    # Action API
    results = client.search("Albert Einstein", limit=5)
    extract = client.get_page_extract("Python (programming language)")
    
    # REST API
    summary = client.page_summary("Albert Einstein")
    
    # SPARQL
    entities = client.sparql_query("SELECT ?item WHERE { ... }")
    entity = client.get_entity("Q937")
    
    # Pageviews
    top = client.top_pageviews("en.wikipedia")
```
