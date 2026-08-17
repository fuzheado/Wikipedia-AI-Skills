---
name: xtools
description: "Query XTools — the canonical Wikimedia statistics API: page info, top editors, edit counts, prose stats, and admin/patroller metrics for any wiki"
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["xtools", "article info", "top editors", "edit count", "editor statistics", "who edits this page"]
  - keywords: ["admin stats", "patroller stats", "prose stats", "page assessments", "stats api"]
  - keywords: ["edit summaries", "month counts", "timecard", "global contributions", "pages created"]
last_verified: 2026-08-17
---

> ⚠️ **User-Agent required:** All requests below require a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

XTools is the canonical Wikimedia statistics API (`xtools.wmcloud.org/api`) — the same engine behind the XTools web tools that editors use daily for edit counts, article info, and top-editor questions. Maintained by MusikAnimal and Samwilson. It pre-computes answers that would otherwise take many Action API calls.

**When to use XTools:** when the question is an *aggregate statistic* — "how many edits has user X made?", "who are the top editors of this page?", "what's this page's assessment and creator?", "how much prose does it have?", "how many edits did admins make last month?" — and you want one request instead of dozens.

**⚠️ Prefer the Action/REST API first.** XTools' own docs say the [Action API](https://www.mediawiki.org/wiki/API:Main_page) and [REST API](https://www.mediawiki.org/wiki/API:REST_API) are *considerably faster* and allow asynchronous requests. Use the Action API for: raw revision text, diffs, per-revision metadata, or anything a single `prop=revisions`/`list=usercontribs` call can answer. Use XTools when the aggregate is not cheaply derivable — or when you need XTools-only metrics (prose, bot data, admin/patroller stats).

## API Basics

- **Base URL:** `https://xtools.wmcloud.org/api` — **not versioned** (no `/v1/`). Breaking renames happen; the `warning` property in any response announces deprecations — **always log it**.
- **Parameters:** `{project}` accepts a domain (`en.wikipedia.org`) or database name (`enwiki`). Article titles are full titles, URL-encoded. Dates are `YYYY-MM-DD`. Usernames accept IPs and CIDR ranges.
- **Docs:** [mediawiki.org/wiki/XTools/API](https://www.mediawiki.org/wiki/XTools/API) (+ [Page](https://www.mediawiki.org/wiki/XTools/API/Page) / [User](https://www.mediawiki.org/wiki/XTools/API/User) / [Project](https://www.mediawiki.org/wiki/XTools/API/Project)) — full endpoint reference in [references/](references/page-api.md).
- **Response:** JSON with a `project` echo, the data, and an `elapsed_time` (server processing seconds). Errors are [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807) problem+json: `status`, `title`, `details`.
- **Etiquette:** make requests **synchronously** — one full round trip before the next. No parallel bursts. Responses are `cache-control: private, must-revalidate` — every request is a full compute round trip (0.1–1.9s typical, heavier for `admin_stats`).

**Quick smoke test:**

```bash
curl -s "https://xtools.wmcloud.org/api/page/pageinfo/en.wikipedia.org/Albert_Einstein" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
# {"project":"en.wikipedia.org","page":{"namespace":0,"page_title":"Albert Einstein",...},
#  "views":..., "watchers":..., "editors":..., "creator":..., "assessment":...,
#  "elapsed_time":0.47}
```

## SOP: Page Statistics in One Call (`pageinfo`)

```python
import requests

def pageinfo(project, title, ua):
    r = requests.get(f"https://xtools.wmcloud.org/api/page/pageinfo/{project}/{title}",
                     headers={'User-Agent': ua}, timeout=60)
    r.raise_for_status()
    d = r.json()
    if 'warning' in d:  # deprecation / behavior-change announcements — log these
        print("XTools warning:", d['warning'])
    return d
```

Returns (all in one call): `views` (30-day), `watchers`, `editors` (total distinct), `creator`/`creator_editcount`, `assessment` (class + badge), `created_at`/`modified_at`, `anon_edits`, `minor_edits`, `page_length`. ⚠️ **Use `pageinfo`, not `articleinfo`** — the old name was renamed in Aug 2024 and is excluded from the docs (it still returns 200, which makes it a silent-wrong-answer trap).

## SOP: Top Editors of a Page

```bash
curl -s "https://xtools.wmcloud.org/api/page/top_editors/en.wikipedia.org/Albert_Einstein/2024-01-01/2024-12-31/10" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
```

Path: `top_editors/{project}/{article}/{start}/{end}/{limit}` — `limit` max 5000, `?nobots=1` excludes bots. Response: `top_editors` list with `user_text` (username or IP), `count`, `rank`, `is_bot`, `edits_removed`/`edits_restored` (revert stats).

## SOP: User Edit Counts

```bash
curl -s "https://xtools.wmcloud.org/api/user/simple_editcount/en.wikipedia.org/Fuzheado" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
# {"user_id":..., "username":"Fuzheado", "live_edit_count":..., "deleted_edit_count":...,
#  "user_groups":[...], "global_user_groups":[...], "elapsed_time":0.77}
```

- Usernames, **IPs, and CIDR ranges** all work as `{username}`.
- High-edit-count users degrade gracefully: `approximate: true` + a `warning` array ("substantially high number of edits. Showing limited results."). Above **600,000 edits** the API returns **501** — that's expected, not an error in your code.
- `simple_editcount/{project}/{username}/{namespace}/{start}/{end}` for scoped counts.

## SOP: What Has a User Done? (`top_edits`)

```bash
curl -s "https://xtools.wmcloud.org/api/user/top_edits/en.wikipedia.org/Fuzheado/0" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
```

`top_edits/{project}/{username}/{namespace}` — top-edited pages by a user, or pass a page title instead of namespace for all their edits to one page. ⚠️ **Responses are large** for active editors (hundreds of KB) — request only what you need and be prepared to paginate via `offset` timestamps.

## SOP: Prose Statistics

```bash
curl -s "https://xtools.wmcloud.org/api/page/prose/en.wikipedia.org/Albert_Einstein" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
# {"bytes":..., "characters":..., "words":..., "sections":..., "references":..., "unique_references":...}
```

Prose/reference counts (the old "Prosesize" metric) — **not available from the Action API in this form**. Useful for article-quality checks and the "how big is the readable content" question.

## Constraint & Guardrails

1. **Prefer Action/REST API when it suffices** — XTools is compute-heavy by design; the official docs say the standard APIs are considerably faster. XTools is for aggregates, not bulk or raw data.
2. **Synchronous requests only** — one round trip at a time. No parallel fan-out, no retry storms. 503 = overloaded, back off for minutes.
3. **Log the `warning` property** — it announces deprecations and behavior changes. The API is unversioned; names have been renamed before (`articleinfo`→`pageinfo`).
4. **501 is a feature** — "user has made too many edits (max 600,000)". Also expect `approximate` + `warning` for very high counts. Handle both without retry loops.
5. **504 after 900s** — heavy queries are killed server-side after 15 minutes. Use date ranges and `limit` to keep requests small.
6. **`top_edits` responses are huge** — never dump them; use namespace/page scoping and offsets.
7. **Assessments overlap** — XTools `assessments` batches multiple pages in one call; for deep per-page assessment queries (all WikiProjects, importance), use [wikimedia-page-assessment](../wikimedia-page-assessment/SKILL.md).
8. **No pageviews here** — XTools has no traffic endpoints; that's [wikimedia-pageviews](../wikimedia-pageviews/SKILL.md).

## Example Use Cases

* "What share of this article did the top 5 editors write, and how many bots edited it this year?" (`top_editors` + `bot_data`)
* "How many edits has this user made, in which namespaces, and what's their global edit count?" (`simple_editcount` + `globalcontribs`)
* "Which pages did this user create, and do any carry an assessment?" (`pages` + `assessments`)
* "How active were admins on this wiki last quarter?" (`project/admin_stats`)
* "How much readable prose does this article have vs. template cruft?" (`prose`)
* "What's this page's WikiProject assessment and who created it?" (`pageinfo`)

## Tooling

### 📚 Endpoint Reference (`references/`)

- [page-api.md](references/page-api.md) — pageinfo, top_editors, prose, links, assessments, bot_data, automated_edits: full schemas + worked examples
- [user-project-api.md](references/user-project-api.md) — all user endpoints + project-level stats (admin/patroller/steward): full schemas + worked examples

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent header and request patterns for all calls |
| **[wikipedia-edit-history](../wikipedia-edit-history/SKILL.md)** | Revision-level history — XTools aggregates the same data; use it when one call beats many |
| **[wikimedia-pageviews](../wikimedia-pageviews/SKILL.md)** | Traffic statistics — XTools deliberately has no pageviews endpoints; pair them for readership + editor context |
| **[wikiwho](../wikiwho/SKILL.md)** | Token-level authorship — XTools' Authorship tool is powered by WikiWho but counts characters, not tokens |
| **[wikimedia-page-assessment](../wikimedia-page-assessment/SKILL.md)** | Deep per-page assessment queries; XTools `assessments` is the batch variant |
| **[wikimedia-api-strategy](../wikimedia-api-strategy/SKILL.md)** | Deciding between APIs — XTools vs Action API trade-offs |
