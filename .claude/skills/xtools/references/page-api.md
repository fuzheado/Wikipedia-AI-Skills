# XTools Page API — Endpoint Reference

Base path: `/api/page/` on host `xtools.wmcloud.org` — `{project}` = domain (`en.wikipedia.org`) or dbname (`enwiki`); `{article}` = full title, URL-encoded. All responses include `project` echo and `elapsed_time`. Errors are RFC 7807 (`status`/`title`/`details`). Always log the `warning` property. See `SKILL.md` for etiquette and the "prefer Action API when it suffices" rule.

## pageinfo

`GET /api/page/pageinfo/{project}/{article}` — one-call page statistics. ⚠️ Use this name, not the legacy `articleinfo` (renamed 3.20.0, Aug 2024; the old path still returns 200 but is excluded from the docs).

```bash
curl -s "https://xtools.wmcloud.org/api/page/pageinfo/en.wikipedia.org/Albert_Einstein" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
```

```json
{
  "project": "en.wikipedia.org",
  "page": {"namespace": 0, "page_title": "Albert Einstein", "redirect": false},
  "views": 650000,
  "watchers": 1500,
  "editors": 11000,
  "creator": "Someone",
  "creator_editcount": 42,
  "created_at": "2001-12-17T00:00:00Z",
  "created_rev_id": 12345,
  "modified_at": "2026-08-01T12:00:00Z",
  "modified_rev_id": 987654321,
  "anon_edits": 2000,
  "minor_edits": 3000,
  "page_length": 150000,
  "assessment": {"class": "FA", "badge": "https://upload.wikimedia.org/...", "category": "Category:FA-Class articles"},
  "elapsed_time": 0.47
}
```

Notes: `watchers` is `null` when unknown; `author`/`last_edit_id`/`ip_edits` are legacy names for `creator`/`modified_rev_id`/`anon_edits`. `views` is approximate (30-day window).

## top_editors

`GET /api/page/top_editors/{project}/{article}/{start}/{end}/{limit}` — top editors by edit count. `limit` max **5000**; `?nobots=1` excludes bots; empty dates (`/../`) select all time.

```bash
curl -s "https://xtools.wmcloud.org/api/page/top_editors/en.wikipedia.org/Albert_Einstein/2024-01-01/2024-12-31/5" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
```

```json
{"project": "en.wikipedia.org", "page": {"page_title": "Albert Einstein"},
 "start": "2024-01-01", "end": "2024-12-31", "limit": 5,
 "top_editors": [
   {"user_text": "EditorA", "count": 120, "rank": 1, "is_bot": false,
    "edits_removed": 3, "edits_restored": 1},
   {"user_text": "192.0.2.10", "count": 45, "rank": 2, "is_bot": false,
    "edits_removed": 0, "edits_restored": 0}
 ], "elapsed_time": 0.24}
```

`edits_removed`/`edits_restored` reflect edits later reverted/restored. `user_text` is the raw username or IP (may be hidden for suppressed users).

## prose

`GET /api/page/prose/{project}/{article}` — readable-content statistics (the old "Prosesize" metric; not derivable from the Action API in one call).

```json
{"project": "en.wikipedia.org", "page": {"page_title": "Albert Einstein"},
 "bytes": 60000, "characters": 58000, "words": 10000, "sections": 25,
 "references": 200, "unique_references": 180, "elapsed_time": 0.71}
```

## links

`GET /api/page/links/{project}/{article}` — link graph counts.

```json
{"project": "en.wikipedia.org", "page": {"page_title": "Albert Einstein"},
 "links_out": 900, "links_in": 500, "redirects": 40, "elapsed_time": 0.3}
```

## assessments

`GET /api/page/assessments/{project}/{pages}` — batch assessment for pipe-separated pages (`Metallica|Pantera`). Results nested under `pages`, keyed per page, with per-WikiProject `class`/`importance` objects. For deep single-page assessment queries (all WikiProjects), use the [wikimedia-page-assessment](../../wikimedia-page-assessment/SKILL.md) skill instead.

```bash
curl -s "https://xtools.wmcloud.org/api/page/assessments/en.wikipedia.org/Albert%20Einstein" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
```

## bot_data

`GET /api/page/bot_data/{project}/{page}/{start}/{end}` — which bots edited the page and how much.

```json
{"project": "en.wikipedia.org", "page": {"page_title": "Albert Einstein"},
 "start": "2024-01-01", "end": "2024-12-31",
 "bot_data": [{"bot": "ExampleBot", "count": 15, "bytes_added": 5000, "bytes_removed": 200}],
 "elapsed_time": 0.4}
```

## automated_edits

`GET /api/page/autoamted_edits/{project}/{page}/{start}/{end}` — counts of (semi-)automated tools used on the page (note the misspelled path is the real one; the docs' own example URL uses `automated_edits` — try both if one 404s). ⚠️ Known bug: Page History output accuracy for this data is unreliable; treat as approximate.

## Error notes

- `404` — page does not exist (or wrong project/name).
- `504` — query killed server-side after 900s; narrow the date range or limit.
- Deprecated behavior shows up as the `warning` array — log it.
