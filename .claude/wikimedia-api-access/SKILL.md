---
name: wikimedia-api-access
description: Access Wikimedia APIs (REST, Action API, SPARQL) with correct User-Agent headers, rate limiting, and 429/403 error handling
license: MIT
compatibility: opencode
---

All requests to Wikimedia APIs **must** include a descriptive `User-Agent` header or they will be blocked (HTTP 403 or 429). This is enforced by the [Wikimedia Foundation User-Agent Policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy).

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
| REST API | `https://api.wikimedia.org/wiki/REST_API` | Modern Wikimedia API (all projects) |
| RESTBase | `https://en.wikipedia.org/api/rest_v1/` | Page summaries, mobile content, transforms |
| Pageviews | `https://wikimedia.org/api/rest_v1/metrics/pageviews/` | Traffic statistics |
| Wikidata Query (SPARQL) | `https://query.wikidata.org/sparql` | Structured data queries |
| Toolforge | `https://tools.wmflabs.org/` | Community tool hosting |

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
3. **Pacing** — For batch operations, add a small delay (at least 0.5s) between requests. For the Action API, respect the `maxlag` parameter.
4. **403 handling** — A 403 almost always means a bad/missing UA. Check the UA string before debugging anything else.
5. **User-Agent per project** — Parameterize the contact info so users can swap in their own details. Never hardcode someone else's email.
6. **SPARQL queries** — For Wikidata Query Service, always set the UA and use `&format=json`. Consider using `SPARQLWrapper` with the `agent` parameter.

## **Example Use Cases**

- **Fetch article content:** "Get the wikitext for 'Python (programming language)' using the Action API."
- **Search:** "Search English Wikipedia for articles about 'machine learning' and return the top 10 titles."
- **Get page metadata:** "Using the REST API, get the description and thumbnail for 'Albert Einstein'."
- **SPARQL query:** "Query Wikidata for all museums in Paris with their coordinates."
- **Batch lookup:** "For each page in this list of 50 titles, fetch the page ID and word count from the API."
- **Troubleshoot 403:** "Check the User-Agent header and confirm it follows the Wikimedia format."
