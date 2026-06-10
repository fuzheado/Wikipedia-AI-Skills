# Code Example Consistency Analysis

**Analysis of all 29 skills in Wikipedia-AI-Skills — no changes made**

---

## 1. Code Language Distribution

| Category | Count | Skills |
|:--------:|:-----:|--------|
| **Python + curl/bash** | 17 | pagetriage-api, pywikibot, wikidata, wikimedia-api-access, wikimedia-database, wikimedia-diffs, wikimedia-eventstreams, wikimedia-ml-services, wikimedia-page-assessment, wikimedia-pageviews, wikimedia-toolforge, wikimedia-wikitext, wikipedia-citations, wikipedia-edit-history, wikipedia-en-article-audit, wikipedia-reference-verifiability, wikipedia-wikitables |
| **curl/bash only** | 10 | mediawiki-page-navigation, mediawiki-translate-extension, wikidata-vector-search, wikimedia-cdn-assets, wikimedia-commons, wikimedia-page-styling, wikipedia-en-biography-writing, wikipedia-page-anatomy, wikipedia-talk-page, wikipedia-templates |
| **Python only** | 2 | wikipedia-categories, wikipedia-error-handling |

**Observation:** 10/29 skills (34%) have no Python examples at all — only curl. This means agents who prefer Python must translate from curl syntax mentally.

---

## 2. Python Code Inconsistencies

### 2a. `timeout` parameter — used in only 5/19 skills with Python

| Skill | Has `timeout=`? |
|-------|:--------------:|
| wikidata | ✅ `timeout=60` |
| wikimedia-api-access | ✅ `timeout=30` |
| wikipedia-citations | ✅ `timeout=timeout` |
| wikipedia-error-handling | ✅ `timeout=30` |
| **All others with Python** | ❌ **No timeout set** (14 skills) |

**Risk:** Without explicit timeouts, requests can hang indefinitely, especially for SPARQL queries (60s default) or heavy Lift Wing models (10-30s).

### 2b. Error handling — used in only 7/19 skills with Python

| Pattern | Skills |
|---------|--------|
| `resp.raise_for_status()` | wikidata, wikimedia-ml-services, wikipedia-error-handling |
| `if resp.status_code == 200:` | wikimedia-api-access, wikimedia-pageviews, wikimedia-wikitext, wikipedia-citations |
| **No error handling in code examples** | pagetriage-api, pywikibot, wikimedia-database, wikimedia-diffs, wikimedia-eventstreams, wikimedia-page-assessment, wikimedia-toolforge, wikipedia-categories, wikipedia-edit-history, wikipedia-en-article-audit, wikipedia-reference-verifiability, wikipedia-wikitables |

**Observation:** The most common pattern in the no-skills A/B test failures was unhandled errors (429 rate limits, 422 model errors, 403 bad User-Agent). Yet most skill code examples don't show error handling.

### 2c. `requests.Session()` — used in only 8/19 skills

| Pattern | Skills |
|:-------:|--------|
| ✅ Use `Session()` | wikidata, wikimedia-api-access, wikimedia-database, wikimedia-diffs, wikimedia-ml-services, wikipedia-citations, wikipedia-error-handling |
| ❌ Direct `requests.get()` | pagetriage-api, pywikibot, wikimedia-eventstreams, wikimedia-page-assessment, wikimedia-pageviews, wikimedia-toolforge, wikimedia-wikitext, wikipedia-categories, wikipedia-edit-history, wikipedia-en-article-audit, wikipedia-reference-verifiability, wikipedia-wikitables |

**Observation:** Session reuse reduces rate-limit risk (keeps TCP connections alive) and should be standard.

### 2d. API URL variable name

| Pattern | Skills |
|:-------:|--------|
| ✅ Has `API_URL`, `API`, or `BASE_URL` variable | wikidata, wikimedia-api-access, wikimedia-diffs, wikimedia-pageviews, wikimedia-wikitext, wikipedia-citations, wikipedia-error-handling |
| ❌ URL hardcoded inline | pagetriage-api, pywikibot, wikimedia-database, wikimedia-eventstreams, wikimedia-ml-services, wikimedia-page-assessment, wikipedia-edit-history, wikipedia-en-article-audit, wikipedia-reference-verifiability, wikipedia-wikitables |

### 2e. Import style — inconsistent

| Style | Example | Skills |
|:-----:|---------|--------|
| `import requests` | Standard | 12 skills |
| `from requests_sse import EventSource` | SSE-specific | wikimedia-eventstreams |
| `import pywikibot` | Framework | pywikibot, wikipedia-categories |
| `import mwparserfromhell` | Parser | wikimedia-wikitext, wikipedia-citations, wikipedia-wikitables, wikipedia-reference-verifiability |
| `import os, subprocess, pymysql` | DB | wikimedia-database, wikimedia-page-assessment |

**Observation:** Each skill has its own import style based on its domain, which is appropriate. No standardization needed here — each domain requires different libraries.

---

## 3. Curl Inconsistencies

### 3a. `-s` (silent) flag

| Pattern | Skills |
|:-------:|--------|
| ✅ Uses `curl -s` consistently | 9 skills (100% of curl lines in those skills) |
| ❌ Uses bare `curl` (no `-s`) | **wikimedia-ml-services — 7 curl lines, 0 use -s** |

**Risk:** Bare `curl` without `-s` shows transfer progress information in stderr, which can confuse agents parsing the output.

### 3b. User-Agent in curl commands

| Status | Skills |
|:-------|--------|
| ✅ `-H "User-Agent: ..."` in curl | wikidata-vector-search, mediawiki-page-navigation, mediawiki-translate-extension, wikimedia-page-styling, wikimedia-ml-services, wikimedia-eventstreams, wikipedia-citations |
| ❌ **No User-Agent in curl examples** | **wikimedia-commons, wikipedia-page-anatomy, wikipedia-talk-page, wikipedia-templates, pagetriage-api, wikipedia-en-article-audit** |

**Risk:** Copy-pasting these curl examples without a User-Agent will result in HTTP 403 errors. The skills mention User-Agent requirements in the text but don't enforce it in the actual code examples.

---

## 4. Response Structure Documentation

| Level | Skills |
|:-----:|--------|
| ✅ **Annotated JSON with field descriptions and access patterns** | wikidata (new), wikimedia-ml-services (new), wikimedia-diffs (new), wikipedia-error-handling |
| ⚠️ **JSON shown without access pattern comments** | wikimedia-pageviews, wikipedia-citations, wikimedia-eventstreams |
| ❌ **No response structure shown** | pagetriage-api, pywikibot, wikimedia-api-access, wikimedia-commons, wikimedia-database, wikimedia-page-assessment, wikimedia-page-styling, wikimedia-toolforge, wikimedia-wikitext, wikipedia-categories, wikipedia-edit-history, wikipedia-en-article-audit, wikipedia-en-biography-writing, wikipedia-page-anatomy, wikipedia-reference-verifiability, wikipedia-talk-page, wikipedia-templates, wikipedia-wikitables |

**Observation:** This was identified as the single biggest time sink in the A/B test (10 minutes debugging ML response format). Most skills still lack response structure docs.

---

## 5. SPARQL Example Format

| Pattern | Count | Skills |
|:-------:|:-----:|--------|
| ✅ Python-wrapped with response parsing | 3 blocks | wikidata (2 of 3 SPARQL blocks now have Python wrappers) |
| ❌ Raw SPARQL only, no Python | 1 block | wikidata (the P279 subclass example is still raw SPARQL only) |

---

## 6. Cross-Cutting Quality Scoring

The table below scores each skill that has Python examples across 6 dimensions:

| Skill | Python? | timeout | Error handling | Session reuse | API URL var | Response docs | **Score** |
|-------|:-------:|:-------:|:--------------:|:-------------:|:-----------:|:-------------:|:---------:|
| wikipedia-error-handling | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **6/6** |
| wikimedia-api-access | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | **4/6** |
| wikidata | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **6/6** |
| wikimedia-diffs | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | **4/6** |
| wikimedia-ml-services | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | **4/6** |
| wikipedia-citations | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | **5/6** |
| wikimedia-pageviews | ✅ | ❌ | ✅ | ❌ | ✅ | ⚠️ | **3/6** |
| wikimedia-eventstreams | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **1/6** |
| wikimedia-wikitext | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | **3/6** |
| pywikibot | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **1/6** |
| pagetriage-api | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **1/6** |
| wikipedia-edit-history | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **1/6** |
| wikipedia-wikitables | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **1/6** |
| wikipedia-reference-verifiability | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **1/6** |
| wikipedia-en-article-audit | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **1/6** |
| wikimedia-database | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | **2/6** |
| wikimedia-page-assessment | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **1/6** |
| wikimedia-toolforge | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | **1/6** |
| wikipedia-categories | ✅ | ❌ | ❌ | ❌ | ❌ | ⚠️ | **2/6** |

---

## 7. Specific Issues Found

### Issue A: Curl examples without User-Agent headers (6 skills)
- `wikimedia-commons`, `wikipedia-page-anatomy`, `wikipedia-talk-page`, `wikipedia-templates`, `pagetriage-api`, `wikipedia-en-article-audit`
- These will produce HTTP 403 when copy-pasted verbatim
- Fix: Add `-H "User-Agent: Bot/1.0 (contact@example.com)"` to each curl example

### Issue B: No `timeout` in requests (14 skills)
- Most Python examples omit `timeout=`
- SPARQL and Lift Wing calls are especially vulnerable (can hang for 60s+)
- Fix: Add `timeout=30` (or `timeout=60` for SPARQL) to all `requests.get()`/`requests.post()` calls

### Issue C: No response structure docs (12 skills)
- Most skills show how to *call* an API but not what the response looks like
- The A/B test showed this was the #1 time sink
- Fix: Add a JSON response example with field annotations and an "Access pattern:" comment after every API call

### Issue D: Direct `requests.get()` without Session (10 skills)
- Missing TCP connection reuse pattern
- Fix: Replace `requests.get(url, ...)` with `session.get(url, ...)` and add `session = requests.Session()` at the top

### Issue E: `wikimedia-ml-services` curl without `-s` flag
- Only skill where bare `curl` (no `-s`) is used
- Fix: Replace `curl` with `curl -s` in all 7 instances

### Issue F: SPARQL example still raw (1 block)
- The P279 subclass traversal example in `wikidata/SKILL.md` is still shown as raw SPARQL only
- Fix: Wrap in a Python code block with `requests.get()` call, matching the other 2 SPARQL examples

---

## 8. Recommended Standard Pattern

Based on the best examples across skills (`wikipedia-error-handling`, `wikidata` post-fix, `wikimedia-api-access`), the recommended standard for all Python API call examples:

```python
import requests

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "MyBot/1.0 (https://example.com; user@example.com) ProjectName"
})
API_URL = "https://en.wikipedia.org/w/api.php"

params = {
    "action": "query",
    "titles": "Albert Einstein",
    "format": "json",
}

resp = SESSION.get(API_URL, params=params, timeout=30)
resp.raise_for_status()
data = resp.json()

# Response structure:
# {
#   "query": {
#     "pages": {
#       "12345": {
#         "title": "Albert Einstein",
#         ...key fields...
#       }
#     }
#   }
# }
# Access: data["query"]["pages"]["12345"]["title"]
```

And for curl examples:

```bash
curl -s 'https://en.wikipedia.org/w/api.php?action=query&format=json' \
  -H "User-Agent: MyBot/1.0 (user@example.com) ProjectName"
```
