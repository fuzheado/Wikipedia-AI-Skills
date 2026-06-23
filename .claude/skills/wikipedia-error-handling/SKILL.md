---
name: wikipedia-error-handling
description: Handle HTTP errors, rate limits, and API failures when interacting with Wikimedia APIs — retry strategies, backoff patterns, error response formats, and recovery procedures for the Action API, REST API, SPARQL, Lift Wing ML, and EventStreams
depends_on: [wikimedia-api-access]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["HTTP 429", "rate limit", "Retry-After", "too many requests", "backoff"]
  - keywords: ["HTTP 403", "forbidden", "User-Agent", "blocked", "access denied"]
  - keywords: ["error", "exception", "retry", "timeout", "connection", "failure", "debug"]
  - keywords: ["422", "parent revision", "model error", "Lift Wing error"]
  - keywords: ["SPARQL timeout", "query timeout", "504", "gateway"]
last_verified: 2026-06-10
---

> ⚠️ **User-Agent required:** All API calls below need a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

> 💡 **Related skills:**
> - **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** — User-Agent format, base API endpoints, and general rate limiting patterns
> - **[wikimedia-ml-services](../wikimedia-ml-services/SKILL.md)** — Lift Wing model errors (422, latency, model not found) — see Known Limitations section
> - **[wikimedia-eventstreams](../wikimedia-eventstreams/SKILL.md)** — SSE connection handling and canary event filtering
> - **[wikidata](../wikidata/SKILL.md)** — SPARQL-specific rate limits and query optimization
>
> Common workflows that combine multiple APIs are especially vulnerable to the errors documented here — a failure in one step can cascade through the entire pipeline.

---

## Reference: HTTP Status Codes for Wikimedia APIs

| Code | Meaning | Common Causes | Recovery |
|:----:|---------|---------------|----------|
| **200** | Success | — | Parse response body |
| **301** | Redirect | Using `http://` instead of `https://` | Use HTTPS |
| **400** | Bad Request | Missing or invalid parameters, malformed JSON body | Check parameter names and values against the API docs. For SPARQL: check query syntax. |
| **403** | Forbidden | Missing or generic User-Agent (e.g., `python-requests/2.x`, `curl/8.x`) | Set a descriptive User-Agent with contact info. See [wikimedia-api-access](../wikimedia-api-access/SKILL.md). |
| **404** | Not Found | Wrong model name (Lift Wing), non-existent page/revision, wrong endpoint URL | Check the endpoint URL and model name against the API docs. |
| **413** | Payload Too Large | SPARQL query too long for GET (URL length limit) | Use POST with query in body. For `wbgetentities`: reduce batch size below 50. |
| **422** | Unprocessable Entity | Lift Wing model rejects the input: `parent_revision_missing` on revision 1, missing required field | See model-specific error handling below |
| **429** | Too Many Requests | Rate limit exceeded — too many requests per second or per hour | Read `Retry-After` header and wait. Implement backoff (see below). |
| **500** | Internal Server Error | Transient server-side failure | Retry with backoff (max 3 attempts). If persistent, the API may be down. |
| **502** | Bad Gateway | Upstream service unavailable (common for SPARQL and Lift Wing) | Wait and retry with exponential backoff. These are usually transient. |
| **503** | Service Unavailable | Service overloaded or under maintenance | Wait at least 30s before retrying. Check [wikitech status](https://www.wikimediastatus.net/). |
| **504** | Gateway Timeout | Query took too long (common for complex SPARQL queries or heavy ML models) | Optimize the query, reduce batch size, or increase timeout. |

---

## SOP: Rate Limiting (429) — The Most Common Error

### How Rate Limiting Works

Wikimedia enforces rate limits at **two levels** simultaneously — you can hit either limit independently:

| Service | Anonymous Limit | Authenticated Limit | Granularity |
|---------|:---------------:|:------------------:|:------------|
| Action API | 200 req/s (burst), 50 req/s (sustained) | Higher for bots | Per IP + User-Agent |
| REST API | No documented hard limit, but aggressive 429 enforcement | Same | Per IP + User-Agent |
| SPARQL (WDQS) | 1 query per ~second (variable), 60s processing per 60s window | Same | Per User-Agent + IP pair |
| Lift Wing ML | 50,000 req/h, 15 req/s | 100,000 req/h, 100 req/s (OAuth) | Per IP (anon) or token (auth) |
| EventStreams | No rate limit (server pushes data) | Same | — |

### The Universal Retry Pattern

```python
import time
import requests

def api_call_with_retry(url, params=None, data=None, method="GET", max_retries=3):
    """Make an API call with exponential backoff on 429/5xx."""
    headers = {
        "User-Agent": "MyBot/1.0 (https://example.com; user@example.com) ProjectName"
    }
    
    for attempt in range(max_retries):
        if method == "GET":
            resp = requests.get(url, params=params, headers=headers, timeout=30)
        else:
            resp = requests.post(url, json=data, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            return resp.json()
        
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            wait = retry_after * (2 ** attempt)  # Exponential backoff
            print(f"Rate limited. Waiting {wait}s (attempt {attempt+1}/{max_retries})")
            time.sleep(wait)
            continue
        
        if 500 <= resp.status_code < 600:
            wait = (2 ** attempt) * 5
            print(f"Server error {resp.status_code}. Retrying in {wait}s")
            time.sleep(wait)
            continue
        
        # 400, 403, 404, 422 — don't retry, fix the request
        resp.raise_for_status()
    
    raise Exception(f"API call failed after {max_retries} retries. Last status: {resp.status_code}")
```

### Connection Reuse (Prevents Rate Limits)

```python
# Good: reuse the same session (reuses TCP connections, reduces load)
session = requests.Session()
session.headers.update({
    "User-Agent": "MyBot/1.0 (https://example.com; user@example.com) ProjectName"
})

# Make many calls through the same session:
for item in items:
    resp = session.get(API_URL, params=params)
    # ...
```

### Concurrent Workers and Burst Rate Limits

When scraping **many language editions** concurrently (e.g., fetching the same article from 300+ `{lang}.wikipedia.org` domains), the combined request rate can trigger 429s even though each individual session stays under the limit. This happens because Wikimedia enforces rate limits **per IP**, not per domain — hitting 300 different Wikipedia domains from one IP address still counts as one sustained stream.

**Symptoms:**
- First 50–100 requests succeed, then a burst of 429s
- Earlier requests in the batch succeed, later ones fail
- The rate limit is triggered by *sustained rate*, not total requests

**Prevention strategies (in order of effectiveness):**

1. **Reduce concurrent workers** — 6 workers is safer than 12 for large jobs:
   ```python
   with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
       futures = {executor.submit(fetch, l, t): (l, t) for l, t in languages}
   ```

2. **Add jitter between batch submissions** — Instead of submitting all futures at once, stagger them slightly:
   ```python
   import time, random
   futures = {}
   for i, (lang, title) in enumerate(languages):
       futures[executor.submit(fetch, lang, title)] = (lang, title)
       if i > 0 and i % 20 == 0:
           time.sleep(random.uniform(0.5, 1.5))  # brief pause every 20
   ```

3. **Cache aggressively** — Many use cases involve re-checking the same articles. Cache results to disk so that re-runs (e.g., with different parameters) skip HTTP entirely. A simple `{lang}:{title}` → `{response_text}` JSON file works well for this.

**Retry pattern for 429 with concurrent workers:**
```python
def fetch_with_retry(lang, title):
    """Fetch with exponential backoff on 429."""
    import time
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
    for attempt in range(4):
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json().get('extract')
        if resp.status_code == 429:
            retry_after = int(resp.headers.get('Retry-After', 2))
            time.sleep(retry_after + (2 ** attempt))  # backoff + Retry-After
            continue
        return None  # Other errors (404, etc.) are final
    return None
```

### SPARQL-Specific Rate Limiting

The Wikidata SPARQL endpoint has its own stricter limits (see the **[wikidata](../wikidata/SKILL.md)** skill for details). Key rules:

- **60-second timeout** per query (hard limit)
- **1 query per ~second** sustained (slower than other APIs)
- **429 includes `Retry-After` header** — respect it
- **429 without `Retry-After`** — wait at least 60 seconds
- Use `POST` for long queries (URL length limit on GET)

```python
def sparql_query(query, max_retries=3):
    """Execute a SPARQL query with WDQS-specific rate limit handling."""
    url = "https://query.wikidata.org/sparql"
    headers = {
        "User-Agent": "MyBot/1.0 (https://example.com; user@example.com) ProjectName",
        "Accept": "application/sparql-results+json",
    }
    
    for attempt in range(max_retries):
        # Use POST for long queries
        resp = requests.get(url, params={"format": "json", "query": query},
                          headers=headers, timeout=60)
        
        if resp.status_code == 200:
            return resp.json()
        
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            wait = max(retry_after, 10) * (2 ** attempt)
            print(f"SPARQL rate limited — waiting {wait}s")
            time.sleep(wait)
            continue
        
        if resp.status_code == 503:
            time.sleep(30 * (2 ** attempt))
            continue
        
        resp.raise_for_status()
    
    raise Exception("SPARQL query failed after retries")
```

---

## SOP: User-Agent Errors (403)

### Detection

```python
# If you get a 403, the most common cause is a missing or generic User-Agent
if resp.status_code == 403:
    print("403 Forbidden — likely missing or generic User-Agent")
    print("Set a descriptive User-Agent: 'MyBot/1.0 (contact@example.com) ProjectName'")
```

### Blocked User-Agent Strings

The following User-Agent strings are **always blocked** by Wikimedia:

- `python-requests/2.x` (any version)
- `curl/8.x` (any version)
- `Wget/1.x`
- `Python-urllib/3.x`
- `Java/1.x`
- Any empty or missing User-Agent header

### Correct User-Agent Format

```
<client-name>/<version> (<contact-info>) <project-name>
```

Examples:
```
MyBot/1.0 (https://example.com; bot@example.com) CategoryAnalysis
WikipediaQualityChecker/2.1 (https://meta.wikimedia.org; user@example.com) ABTesting
```

See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for full details.

---

## SOP: Lift Wing ML Model Errors

Lift Wing models have model-specific error responses that are not covered by standard HTTP codes.

### 422: Parent Revision Missing (New Pages)

**Applies to:** `revertrisk-language-agnostic`, `revertrisk-multilingual`, `revertrisk-wikidata`

**Cause:** Brand-new pages (revision 1) have no parent revision for the revert-risk model to compare against.

**Detection:**
```python
resp = requests.post(url, json=data, headers=headers, timeout=30)
if resp.status_code == 422:
    error = resp.json()
    if "parent_revision_missing" in str(error):
        print("Revision 1 cannot be scored by revert-risk models")
        # Fall back to articlequality model
```

**Workaround:** Use the `articlequality` model instead (it scores the revision itself, not the diff):
```python
fallback_url = "https://api.wikimedia.org/service/lw/inference/v1/models/articlequality:predict"
fallback_data = {"rev_id": rev_id, "lang": "en"}
```

**Note:** The `articlequality` model has ~60s processing latency for brand-new revisions (see Known Limitations in [wikimedia-ml-services](../wikimedia-ml-services/SKILL.md)).

### 422: Missing Required Field

**Applies to:** All Lift Wing models

**Cause:** Required field is missing from the request body (e.g., `rev_id`, `lang`, `title`).

**Fix:** Check the model's documented required fields. Common required fields by model:

| Model | Required Fields |
|-------|----------------|
| `revertrisk-language-agnostic` | `rev_id` (int), `lang` (string) |
| `articlequality` | `rev_id` (int), `lang` (string) |
| `outlink-topic-model` | `page_title` (string), `lang` (string) |
| `article-country` | `title` (string — note: not `page_title`), `lang` (string) |

### 404: Model Not Found

**Cause:** The model name in the URL is wrong, or the wiki code is wrong.

**Common mistakes:**
- Using `enwiki-articlequality` instead of the modern `articlequality` (note: the modern model is just `articlequality`, not `articlequality-language-agnostic`)
- Using a wiki code that doesn't have this model deployed (check the [model list](https://wikitech.wikimedia.org/wiki/Machine_Learning/LiftWing#Revscoring_models_(migrated_from_ORES)))
- Including `.predict` in the wrong place

### Empty Scores (Articlequality Latency)

**Applies to:** `articlequality`, `{wiki}-articlequality`

**Cause:** Revision is less than ~60 seconds old and hasn't been indexed by the model yet.

**Response when this happens:**
```json
{
  "enwiki": {
    "models": {"articlequality": {"version": "0.9.2"}},
    "scores": {}  # Empty — no score for this revision yet
  }
}
```

**Workaround:** Retry with a delay:
```python
def score_with_retry(rev_id, max_attempts=3, delay=30):
    for attempt in range(max_attempts):
        result = call_articlequality(rev_id)
        scores = result.get("enwiki", {}).get("scores", {})
        if str(rev_id) in scores:
            return scores[str(rev_id)]
        print(f"Score not ready yet (attempt {attempt+1}). Waiting {delay}s...")
        time.sleep(delay)
    return None  # Score unavailable
```

---

## SOP: EventStreams Connection Errors

### Connection Drops

**Cause:** EventStreams has a 15-minute idle timeout. The server closes the connection if no events arrive.

**Detection:** The SSE stream's `events()` generator stops yielding events, or the HTTP connection raises `ConnectionError`/`ChunkedEncodingError`.

**Recovery:** Reconnect with exponential backoff:
```python
import time
from sseclient import SSEClient

def consume_eventstream(url, max_reconnects=5):
    for attempt in range(max_reconnects):
        try:
            messages = SSEClient(url)
            for msg in messages:
                if msg.event == 'message':
                    yield msg
        except (ConnectionError, ChunkedEncodingError) as e:
            wait = min(30, 2 ** attempt)  # Cap at 30s
            print(f"Connection lost: {e}. Reconnecting in {wait}s...")
            time.sleep(wait)
```

### No Events (Silent Connection Drop)

**Detection:** The connection opens (HTTP 200) but no events arrive even though the stream should be active. This can happen if the stream name is wrong.

**Debugging:**
```python
# Wrong: silent failure
url = "https://stream.wikimedia.org/v2/stream/wrong-stream-name"
# Correct: should receive events immediately
url = "https://stream.wikimedia.org/v2/stream/recentchange"
```

**Fix:** Verify the stream name against the [stream catalog](https://stream.wikimedia.org/?doc) and the **[wikimedia-eventstreams](../wikimedia-eventstreams/SKILL.md)** skill.

### Canary Events

**Applies to:** All EventStreams streams

**Detection:** Events with `meta.domain == "canary"` are test events injected by WMF infrastructure.

**Handling:** Always filter them out:
```python
if event.get("meta", {}).get("domain") == "canary":
    continue  # Discard — this is a test event
```

---

## SOP: SPARQL Errors

### Query Timeout (HTTP 504)

**Cause:** Query exceeds the 60-second hard limit.

**Symptoms:** Empty results after a long wait, or HTTP 504 Gateway Timeout.

**Fixes:**
- Add `LIMIT` clause to reduce result set size
- Remove `SERVICE wikibase:label` temporarily and add it back after optimizing
- Add appropriate `FILTER` clauses to narrow the search space
- Use `values` clauses to restrict to known item sets

### Query Syntax Error (HTTP 400)

**Cause:** Invalid SPARQL syntax.

**Debugging:**
```python
if resp.status_code == 400:
    print("SPARQL syntax error. Check:")
    print("  1. All prefixes are declared (wd:, wdt:, p:, ps:, etc.)")
    print("  2. Curly braces are balanced")
    print("  3. FILTER syntax is correct")
    print("  4. String literals use quotes correctly")
    print(f"Response: {resp.text[:500]}")  # Error message often hints at the issue
```

### Empty SPARQL Results

**Cause:** The query is syntactically valid but returns no results. This is not an error, but can be confusing.

**Common reasons:**
- Wrong Q/P IDs (e.g., `Q38104` = Nobel Prize in Physics, not `Q38105`)
- Wrong property (e.g., `P166` = award received, not `P106`)
- No data exists for the combination you're querying
- Case sensitivity: property values may be case-sensitive

**Debugging:** Test the query in the [WDQS web UI](https://query.wikidata.org) first.

---

## SOP: General Debugging Strategy

When any Wikimedia API call fails, follow this checklist:

1. **Check the HTTP status code** — see the reference table at the top of this skill
2. **Check the User-Agent header** — is it descriptive? (see [wikimedia-api-access](../wikimedia-api-access/SKILL.md))
3. **Check the endpoint URL** — is it correct for this API?
4. **Check the request parameters** — are all required fields present? Correct types?
5. **Check for rate limiting** — did you make too many requests too quickly?
6. **Check the API documentation** — has the API changed? (check the relevant skill)
7. **Check network connectivity** — can you reach the endpoint at all? (`curl -I <url>`)
8. **Check for transient failures** — try again after a short delay

### API-Specific Error Response Examples

**Action API error response:**
```json
{
  "error": {
    "code": "missingparam",
    "info": "The \"titles\" parameter must be set.",
    "*": "See https://en.wikipedia.org/w/api.php for API usage"
  }
}
```

**Lift Wing ML error response:**
```json
{
  "error": "Model 'enwiki-nonexistent-model' not found",
  "error_type": "ModelNotFoundError"
}
```

**SPARQL error response:**
```json
{
  "error": "org.apache.jena.query.QueryParseException: ..."
}
```

### Logging Pattern for Debugging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Log every API call for debugging
session = requests.Session()
session.hooks['response'].append(
    lambda r, *args, **kwargs: logging.debug(
        f"{r.request.method} {r.url} → {r.status_code} ({len(r.content)} bytes)"
    )
)
```
