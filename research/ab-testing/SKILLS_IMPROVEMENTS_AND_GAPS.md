# Skills Improvements & Gaps — Derived from A/B Testing

**Based on 24 agent runs across 12 tasks in 3 rounds of A/B testing**
**Date:** 2026-06-09

---

## Part 1: Improvements to Existing Skills

After watching agents struggle (or breeze through) 12 different Wikipedia automation tasks, several systematic patterns emerged in how skills could be made more effective.

### 1.1 Missing "Known Limitations" Sections

**The pattern:** Multiple times across the tests, both the skills and no-skills agents hit the same undocumented API limitations. The skills variant had no advantage because the limitation wasn't documented anywhere.

**Specific gaps found:**

| Gap | Skill | Tasks Affected | Fix |
|-----|-------|:--------------:|-----|
| `revertrisk-language-agnostic` returns HTTP 422 `parent_revision_missing` for revision 1 (new pages have no parent to compare against) | `wikimedia-ml-services` | 6, 12 | Add a "Known Limitations" subsection: *"Revert-risk models require a parent revision — they cannot score brand-new pages. Use `articlequality` as a fallback for revision 1, with the understanding that it has ~60s processing latency."* |
| `articlequality` model has ~60s processing latency for very new revisions | `wikimedia-ml-services` | 6, 7 | Document the latency window: *"Newly created revisions may not be immediately available for scoring. The model returns empty scores for revisions less than ~60 seconds old."* |
| Pageviews REST API has ~48h data lag (today's data isn't complete) | `wikimedia-pageviews` | 1 | Currently mentioned in the Top Pages section but not in the per-article section. Make it a prominent warning. |
| `formatversion=2` changes the wikitext content key from `*` to `content` | `wikimedia-api-access` | 8 | The Action API skill documents `formatversion=2` but doesn't warn about the changed response key. |
| Wikidata SPARQL endpoint rate-limits aggressively (~1 req/min without established UA) | `wikidata` | 2, 5 | Document the rate limit and recommended backoff strategy. |
| Pywikibot `CategoryPageGenerator` renamed to `CategorizedPageGenerator` in v11.3 | `pywikibot` | 9 | Add a version compatibility note. |

**Fix template (add to each affected skill):**

````markdown
## Known Limitations

| Limitation | Workaround |
|------------|------------|
| [specific API behavior] | [how to handle it] |
````

### 1.2 Missing Error Response Documentation

**The pattern:** When an API call fails, agents waste time figuring out *what* went wrong. Skills should document common error responses.

**Examples from testing:**
- `action=compare` with `fromrev` pointing to a non-existent revision → returns `{"error": {"code": "missingrev"...}}` (Task 12)
- Lift Wing model with wrong model name → returns `{"error": "Model not found"}` with HTTP 404 (Task 11)
- EventStreams with wrong stream name → connection closes immediately with no error (Task 6)

**Fix:** Add an "Error Handling" subsection to each skill with the actual JSON error responses and how to interpret them.

### 1.3 Missing Cross-References Between Skills

**The pattern:** Many tasks required chaining multiple skills, but the skills don't tell agents which other skills to load for common workflows.

**Cross-references that would have helped:**

| From Skill | Should Reference | Why |
|------------|-----------------|-----|
| `wikidata` (SPARQL) | `wikimedia-ml-services` (quality scoring) | Common workflow: query items → score article quality |
| `wikidata` (SPARQL) | `wikimedia-pageviews` (traffic) | Common workflow: query items → get pageviews for ranking |
| `wikimedia-eventstreams` | `wikimedia-ml-services` | Common workflow: stream events → score ML models |
| `wikimedia-eventstreams` | `wikimedia-diffs` | Common workflow: detect edit → fetch diff |
| `wikimedia-eventstreams` | `wikipedia-pagetriage-api` | Common workflow: detect new page → check patrol status |
| `wikipedia-page-anatomy` | `wikipedia-templates` | Template taxonomy needed for structural analysis |
| `wikipedia-categories` | `wikidata` | Cross-wiki category analysis |
| `wikipedia-citations` | `wikimedia-wikitext` | Citation extraction requires AST parsing |

**Fix:** Add a "Related Skills" section to each skill's front matter:

```yaml
related_skills:
  - wikimedia-ml-services: "For scoring article quality of queried items"
  - wikimedia-pageviews: "For ranking items by popularity"
```

And/or add a "Common Workflows" section with multi-skill code examples.

### 1.4 Missing Quick-Reference Decision Tables

**The pattern:** The `wikipedia-categories` skill's quick-reference table ("I want to..." → "Use this API") was consistently the most effective format. It reduced time-to-solution to near-zero. Other skills don't use this format.

**Skills that would benefit most:**

| Skill | Suggested Table Header |
|-------|----------------------|
| `wikidata` | "I want to find..." → "Use this query..." |
| `wikimedia-ml-services` | "I want to predict..." → "Use this model..." |
| `wikimedia-eventstreams` | "I want to monitor..." → "Use this stream..." |
| `wikimedia-commons` | "I want to find media..." → "Use this search..." |
| `wikimedia-pageviews` | "I want to rank by..." → "Use this data source..." |
| `wikipedia-templates` | "I want to detect..." → "Use this template pattern..." |

**Fix:** Add a 3-column decision table near the top of each skill: **Goal** | **API/Module** | **Key Parameters**.

### 1.5 Inconsistent Code Example Quality

**The pattern:** Some skills include complete, ready-to-copy Python functions (e.g., `wikimedia-pageviews` has a `get_historical_views()` function that needs only the article title). Others show only curl commands or fragmentary params dictionaries.

**Examples of best practice (from testing):**
- `wikimedia-pageviews`: Complete `get_historical_views(article_title, start_date, end_date)` function with headers, URL construction, and error handling (Tasks 1, 5)
- `wikimedia-diffs`: Complete `action=compare` code with revision-fetching preamble (Task 12)

**Examples needing improvement:**
- `wikidata`: SPARQL examples are shown as raw query strings without Python request code. Add: `requests.get(endpoint, params={"format": "json", "query": query}, headers=headers)` wrapper.
- `wikimedia-commons`: Shows curl examples for search but not Python. Add: `requests.get("https://commons.wikimedia.org/w/api.php", params={...}, headers=headers)`.
- `wikipedia-pagetriage-api`: Shows parameter names but no complete request/response cycle.

**Fix:** Every API call example should follow this template:

````python
import requests

HEADERS = {"User-Agent": "Bot/1.0 (contact@example.com) Project"}
API = "https://en.wikipedia.org/w/api.php"

params = {
    "action": "query",
    # ... all required parameters ...
    "format": "json",
}
response = requests.get(API, params=params, headers=HEADERS, timeout=30)
data = response.json()
# Access: data["path"]["to"]["field"]
````

### 1.6 Missing Response Format Documentation

**The pattern:** Several skills tell agents what to send but not what they'll get back. This was the biggest time sink in the no-skills runs — guessing at JSON response structures.

**Worst offender:** `wikimedia-ml-services`. The Lift Wing `enwiki-articlequality` model returns an ORES-compatible nested envelope:
```json
{"enwiki": {"scores": {"{revid}": {"articlequality": {"score": {"prediction": "GA", "probability": {...}}}}}}}
```
The no-skills agent guessed `data["output"]["prediction"]` — a reasonable guess that was completely wrong. This cost **~10 minutes** of debugging.

**Fix:** After every API request example, show the exact JSON response structure with annotations:

````python
# Response structure:
# {
#   "enwiki": {
#     "scores": {
#       "{revid}": {
#         "articlequality": {
#           "score": {
#             "prediction": "FA|GA|B|C|Start|Stub",  # <-- quality class
#             "probability": {                        # <-- per-class confidence
#               "FA": 0.0, "GA": 0.0, "B": 0.0, ...
#             }
#           }
#         }
#       }
#     }
#   }
# }
# Access: data["enwiki"]["scores"][str(revid)]["articlequality"]["score"]["prediction"]
````

### 1.7 Missing Multi-Language/Wiki Patterns

**The pattern:** Tasks 5 and 11 required making requests to multiple language Wikipedias (en.wikipedia.org, fr.wikipedia.org, de.wikipedia.org). The current skills are mostly English-centric.

**Specific gaps:**
- `wikimedia-pageviews`: Shows only `en.wikipedia` as the project parameter. No guidance on the `{lang}.wikipedia.org` pattern for other languages (Task 11).
- `wikidata`: Doesn't show how to query sitelinks for multiple languages simultaneously (Task 5). The `schema:isPartOf` pattern is not documented.
- `wikimedia-api-access`: Mentions enwiki but doesn't explain `{$lang}.wikipedia.org` URL substitution pattern.

**Fix:** Add a "Cross-Wiki Operations" subsection to each skill showing the `{lang}` parameterization pattern.

### 1.8 Summary: Improvement Priority Matrix

| Improvement | Effort | Impact | Priority |
|-------------|:------:|:------:|:--------:|
| Add "Known Limitations" sections | Low | 🟢 High (prevents trial-and-error) | **1** |
| Document exact JSON response structures | Low | 🟢 High (biggest time-sink discovered) | **2** |
| Add quick-reference decision tables | Medium | 🟢 High (most effective format) | **3** |
| Add cross-references between skills | Low | 🟡 Medium (improves multi-skill workflows) | **4** |
| Standardize code example quality | Medium | 🟡 Medium (faster copy-paste) | **5** |
| Document error responses | Medium | 🟡 Medium (reduces debugging time) | **6** |
| Add multi-language patterns | Low | 🔵 Lower (niche use case) | **7** |

---

## Part 2: New Skills That Would Fill Gaps

Several recurring pain points emerged that existing skills don't address. These would benefit from entirely new skills.

### 2.1 New Skill: `wikipedia-error-handling`

**Problem observed:** Both skills and no-skills agents hit HTTP 429 (rate limiting), 403 (bad User-Agent), 422 (model-specific errors), and 400 (bad parameters). Each agent handled these differently — some added exponential backoff, some just crashed, some ignored the errors.

**What it would cover:**
- HTTP status code reference for Wikimedia APIs: 200, 301, 400, 403, 429, 500, 502
- Rate limiting: `Retry-After` header, exponential backoff formulas, connection pooling with `requests.Session()`
- User-Agent policy enforcement (currently in `wikimedia-api-access` — could be centralized)
- Common error responses for each major API (Action API, REST API, SPARQL, Lift Wing, EventStreams)
- Retry strategies: when to retry, when to fall back, when to fail gracefully
- Circuit breaker pattern for long-running batch jobs

**Evidence from testing:**
- Task 2: No-skills agent hit 429 on Wikidata SPARQL, added exponential backoff (skills variant luckily didn't hit it)
- Task 9: No-skills agent hit 429 on Action API, added 1s delay
- Task 12: Skills variant had to handle 422 from revert-risk model (no documented pattern)
- Task 8: Both variants had to handle Action API error responses (page not found, bad title)

### 2.2 New Skill: `wikipedia-bot-operations`

**Problem observed:** Task 9 asked agents to use Pywikibot for a citation cleanup. The skills variant had the Pywikibot framework knowledge but neither variant had systematic knowledge of **bot operations best practices** — edit summaries, rate limiting, conflict detection, community norms.

**What it would cover:**
- Edit summarization: format and conventions for automated edit summaries
- Throttling: how fast can a bot edit? Per-wiki rate limits. The `maxlag` parameter pattern.
- Conflict detection: edit conflicts, page protection, reverts
- Bot flags: when to request a bot flag, how to run unflagged
- Dry-run patterns: how to test without making real edits
- Community norms: the Wikipedia bot policy, acceptable use, disclosure requirements
- Watchlist impact: avoiding flooding watchlists
- `Assert=bot` parameter and how it affects rate limits

**Evidence from testing:**
- Task 9: Both variants did dry runs but neither generated proper edit summaries or considered rate limits
- Task 6: No-skills agent discovered rate limits at runtime
- The `pywikibot` skill covers the framework but not the operational best practices

### 2.3 New Skill: `wikipedia-api-strategy`

**Problem observed:** Agents frequently had to choose between Pywikibot, raw Action API, REST API, SPARQL, or database queries — and often picked suboptimal approaches. Task 5 (content gaps) could have been done with SPARQL alone but the agent used 3 separate APIs.

**What it would cover:**
- Decision tree for choosing the right tool:
  - *"I need to read a single page"* → REST API (`/page/summary`)
  - *"I need to edit pages in bulk"* → Pywikibot
  - *"I need complex cross-page analytics"* → SQL replicas (Toolforge)
  - *"I need graph queries"* → SPARQL
  - *"I need real-time data"* → EventStreams
  - *"I need ML predictions"* → Lift Wing
- When NOT to use Pywikibot (e.g., read-only analytics, SPARQL is cheaper)
- When to use SQL replicas vs API (Task 1: SQL `page_props` for bulk pageview sorting vs REST API for per-article data)
- Performance characteristics of each approach (latency, throughput, rate limits)
- Authentication requirements: when you need a bot account vs when you can read anonymously

**Evidence from testing:**
- Task 1: `wikimedia-pageviews` skill documents the SQL shortcut (`page_props.pageview_daily_average`) vs REST API — the no-skills variant didn't know about the SQL option
- Task 5: Used 3 separate APIs (Action API + SPARQL + Pageviews REST) — a single SPARQL query with pageview data would have been more efficient
- Task 10: Used 4 APIs (category members → Wikidata → Commons → pageviews) — some of this could be consolidated

### 2.4 New Skill: `wikipedia-cross-wiki-operations`

**Problem observed:** Tasks 5, 10, and 11 all required spanning multiple Wikimedia projects (Wikipedia + Wikidata + Commons) or multiple language editions. The knowledge needed is currently scattered across individual skills.

**What it would cover:**
- Cross-wiki URL patterns: `{$lang}.wikipedia.org`, `commons.wikimedia.org`, `www.wikidata.org`, `query.wikidata.org`
- Site link resolution: mapping Wikipedia titles to Wikidata QIDs (currently in `wikidata` skill) and back
- Inter-language link patterns: finding articles that exist in language A but not language B
- Cross-project data fusion: combining Commons metadata with Wikipedia content with Wikidata facts
- Multi-language API patterns: parallel requests to multiple language wikis with throttling
- Shared authentication: using a single bot session across multiple wikis

**Evidence from testing:**
- Task 5: Content gap analysis required English Wikipedia + Wikidata SPARQL — the skills variant had to piece together knowledge from `wikidata` + `wikipedia-categories` + `wikimedia-pageviews`
- Task 10: Commons media checking required Wikipedia + Wikidata + Commons — "cross-project" isn't a concept in any single skill
- Task 11: Cross-language comparison required the same fetch across 3 languages — each language needed its own API calls

### 2.5 New Skill: `wikipedia-content-analysis`

**Problem observed:** Several tasks required analyzing article content beyond just fetching it — checking structural health, extracting citations, measuring quality. These used a mix of `wikipedia-page-anatomy`, `wikipedia-citations`, `wikimedia-wikitext`, and `wikimedia-ml-services`, but there was no unified framework for "analyze this article."

**What it would cover:**
- Article quality assessment: combining Lift Wing ML scores with structural metrics (length, section count, citation count, image presence) into a composite quality score
- Readability analysis: Flesch-Kincaid scores, sentence length, paragraph structure
- Content completeness: infobox coverage, section diversity, citation density, image requirements
- Structural health scoring: lead section quality, section balance, TOC depth, navbox coverage
- Topic classification: what topics does this article cover? (using the `articletopic` ML model)

**Evidence from testing:**
- Task 7: Citation health × quality correlation required combining ML quality scores with citation analysis — no unified framework existed
- Task 8: Structural health check required mixing page-anatomy knowledge with template taxonomy with AST parsing
- The skills variant succeeded but had to individually load 4 separate skills

### 2.6 New Skill: `wikipedia-edit-patterns` (or expand `wikipedia-edit-history`)

**Problem observed:** Task 12 required not just fetching diffs but **classifying** them into change types (addition-heavy, deletion-heavy, replacement, etc.) and identifying patterns. The `wikimedia-diffs` skill provides the raw diff but doesn't help with interpretation.

**What it would cover:**
- Diff classification: detecting additions, deletions, replacements, re-orders, formatting changes
- Vandalism heuristics: large deletions, blanking, offensive content insertion, link spam
- Editor behavior patterns: edit frequency analysis, time-of-day patterns, page preferences
- Edit war detection: repeated reverts between the same editors on the same page
- Quality trends: does this article's quality improve or decline over time?

**Evidence from testing:**
- Task 12: Skills variant manually classified diffs by computing add/remove ratios — a skill could document this pattern and provide ready-to-use classification code
- Task 3: Revision history was fetched but not analyzed for patterns
- No existing skill helps agents interpret *what a diff means*

### 2.7 Summary: New Skill Priority Matrix

| New Skill | Addresses | Effort | Impact | Priority |
|-----------|-----------|:------:|:------:|:--------:|
| **`wikipedia-error-handling`** | All tasks hit errors; handling is ad-hoc | Medium | 🟢 High (every task benefits) | **1** |
| **`wikipedia-api-strategy`** | Agents pick suboptimal tools for the task | Medium | 🟢 High (prevents wrong approach) | **2** |
| **`wikipedia-cross-wiki-operations`** | 3/12 tasks spanned projects/languages | Medium | 🟡 Medium (growing need) | **3** |
| **`wikipedia-bot-operations`** | Pywikibot users need ops best practices | Medium | 🟡 Medium (niche but high value) | **4** |
| **`wikipedia-content-analysis`** | Article analysis spread across 4 skills | Large | 🟡 Medium (integration value) | **5** |
| **`wikipedia-edit-patterns`** | Diff classification was done manually | Large | 🔵 Lower (advanced use case) | **6** |

---

## Part 3: Cross-Cutting Improvements

### 3.1 Skills Metadata for Automatic Loading

Currently, an agent must manually specify which skills to load. Many tasks benefit from a predictable set of companion skills. The testing revealed natural clusters:

| Task Type | Skills Needed |
|-----------|--------------|
| **Read Wikipedia content** | `wikimedia-api-access` + `wikimedia-wikitext` + `wikipedia-page-anatomy` |
| **Analyze citations** | `wikipedia-citations` + `wikimedia-wikitext` + `wikimedia-api-access` |
| **Cross-wiki gap analysis** | `wikidata` + `wikipedia-categories` + `wikimedia-pageviews` + `wikimedia-api-access` |
| **Real-time monitoring** | `wikimedia-eventstreams` + `wikimedia-ml-services` + `wikimedia-diffs` + `wikimedia-api-access` |
| **Bot operations** | `pywikibot` + `wikipedia-citations` + `wikimedia-wikitext` + `wikimedia-api-access` |

**Recommendation:** Add a `recommended_bundles` field to skill front matter:

```yaml
recommended_bundles:
  read-article: ["wikimedia-api-access", "wikimedia-wikitext", "wikipedia-page-anatomy"]
  realtime-monitor: ["wikimedia-eventstreams", "wikimedia-ml-services", "wikimedia-diffs"]
```

### 3.2 Skills Versioning

Pywikibot v11.3 renamed `CategoryPageGenerator` → `CategorizedPageGenerator`. The current skill didn't mention this, costing 10 minutes of debugging. 

**Recommendation:** Add `last_verified` metadata to each skill:

```yaml
last_verified: 2026-05-15
verified_against:
  pywikibot: 11.3.0
  mediawiki: 1.43.0-wmf.14
```

And a `known_changes` section tracking API drift:

```yaml
known_changes:
  - version: "11.3.0"
    change: "CategoryPageGenerator renamed to CategorizedPageGenerator"
    impact: "Code using the old name will raise ImportError"
```

### 3.3 Skill Discovery During Task Execution

Agents can only benefit from skills they know to load. The testing assumed the skills were named in the task prompt. In production, the agent needs to *discover* which skills to load based on the task description.

**Recommendation:** Add a `skill_discovery_hints` field mapping common task keywords to skills:

```yaml
skill_discovery_hints:
  - keywords: ["pageview", "traffic", "popular", "views", "readership"]
    skill: wikimedia-pageviews
  - keywords: ["SPARQL", "Wikidata", "knowledge graph", "semantic query"]
    skill: wikidata
  - keywords: ["cite", "citation", "reference", "CS1", "bare URL", "dead link"]
    skill: wikipedia-citations
  - keywords: ["real-time", "stream", "SSE", "EventStreams", "live", "recent change"]
    skill: wikimedia-eventstreams
  - keywords: ["revert", "vandalism", "quality", "damaging", "good faith"]
    skill: wikimedia-ml-services
  - keywords: ["pywikibot", "bot framework", "page generator", "automated edit"]
    skill: pywikibot
  - keywords: ["Commons", "image", "media", "photo", "file", "upload"]
    skill: wikimedia-commons
  - keywords: ["diff", "revision comparison", "change", "edit comparison"]
    skill: wikimedia-diffs
```

---

## Part 4: What Worked Well (Don't Change)

The testing also revealed several skill patterns that were highly effective. These should be preserved and replicated:

### 4.1 Decision Tables (wikipedia-categories)

The quick-reference table at the top of `wikipedia-categories` was the single most effective format. It allowed the agent to find the right API module in seconds. This pattern should be the template for all skills.

### 4.2 Complete Code Functions (wikimedia-pageviews)

The `get_historical_views()` function in `wikimedia-pageviews` was a complete, copy-pasteable solution. The agent just called it with the article title. No parameter guessing, no URL construction, no header debugging.

### 4.3 SOP Sections (wikipedia-edit-history, wikimedia-diffs)

The "SOP: Batching and Pagination for Efficiency" section in `wikipedia-edit-history` was especially effective because it not only showed *what* to do but *why* (e.g., "requesting only needed fields reduces response size by ~85%"). This contextual knowledge helps agents understand the tradeoffs.

### 4.4 Cross-Skill References (wikimedia-api-access)

The pattern of `wikimedia-api-access` being referenced from every other skill ("⚠️ User-Agent required: ... See the wikimedia-api-access skill") establishes a clean dependency chain. Agents load it automatically when they read the warning.

### 4.5 Visual Comparison Tables (several skills)

Several skills use tables to compare approaches (e.g., "Strategy: AST Parsing vs Parsoid HTML" in `wikimedia-wikitext`, "ORES vs Lift Wing" in `wikimedia-ml-services`). These were effective at helping agents choose the right approach quickly.

---

## Summary: Highest-Impact Actions

| Action | Type | Effort | Impact |
|--------|------|:------:|:------:|
| Add "Known Limitations" to `wikimedia-ml-services` | Fix | 15 min | Prevents 2+ documented failure modes |
| Add complete JSON response structures to all API examples | Fix | 1 hour | Eliminates the single biggest time sink |
| Add decision tables to `wikidata`, `wikimedia-ml-services`, `wikimedia-commons` | Fix | 2 hours | Reduces time-to-solution by ~50% |
| Create `wikipedia-error-handling` skill | New | 3 hours | Every task benefits |
| Add cross-references between related skills | Fix | 1 hour | Improves multi-skill workflows |
| Create `wikipedia-api-strategy` skill | New | 4 hours | Prevents wrong-tool selection |
| Standardize code example format across all skills | Fix | 4 hours | Consistent copy-paste experience |
| Add `skill_discovery_hints` to all skills | Enhancement | 2 hours | Enables automatic skill loading |
