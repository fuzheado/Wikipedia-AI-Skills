# XTools User & Project API — Endpoint Reference

Base: `https://xtools.wmcloud.org/api/...` — `{project}` = domain or dbname; `{username}` accepts **usernames, IPs, and CIDR ranges**; dates are `YYYY-MM-DD`; empty date values select all time. All responses include `elapsed_time`; log the `warning` property. Errors: RFC 7807.

## User endpoints

### simple_editcount

`GET /api/user/simple_editcount/{project}/{username}/{namespace}/{start}/{end}` — user ID, live/deleted edit counts, local + global groups. The most-used XTools endpoint.

```bash
curl -s "https://xtools.wmcloud.org/api/user/simple_editcount/en.wikipedia.org/Fuzheado" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
```

```json
{"project": "en.wikipedia.org", "username": "Fuzheado", "user_id": 12345,
 "namespace": 0, "live_edit_count": 20000, "deleted_edit_count": 50,
 "user_groups": ["autoreviewer", "editor"], "global_user_groups": ["global-ipblock-exempt"],
 "elapsed_time": 0.77}
```

⚠️ High-edit-count users: returns `approximate: true` + `warning` ("substantially high number of edits. Showing limited results."); above **600,000 edits** the API returns **501** — expected, not a bug. Don't retry on 501.

### pages_count / pages

- `GET /api/user/pages_count/{project}/{username}/{namespace}/{redirects}/{deleted}/{start}/{end}` — count of pages created (grouped by namespace). `redirects`: `noredirects|onlyredirects|all`; `deleted`: `live|deleted|all`.
- `GET /api/user/pages/{project}/{username}/{namespace}/{redirects}/{deleted}/{start}/{end}/{offset}` — paginated list; each entry has `page_title`, `namespace`, `redirect`, `timestamp`, `rev_id`, `rev_length`, `length`, `deleted`, `recreated`, `assessment` (class/badge/color/category).

### automated_editcount / automated_edits / nonautomated_edits

- `GET /api/user/automated_editcount/{project}/{username}/{namespace}/{start}/{end}/{tools}` — count of (semi-)automated edits; `tools=1` adds per-tool counts.
- `GET /api/user/automated_edits/{project}/{username}/{namespace}/{start}/{end}/{offset}` — the edits themselves; filter by tool with `?tool=Tool name`.
- `GET /api/user/nonautomated_edits/{project}/{username}/{namespace}/{start}/{end}/{offset}` — the non-automated ones (useful for "human vs bot" analysis).

### edit_summaries

`GET /api/user/edit_summaries/{project}/{username}/{namespace}/{start}/{end}` — edit-summary usage stats: `total`, `with_summaries`, `without_summaries`, `minor`, `minor_with_summaries`, and comment-length buckets. Great for editor-behavior research.

### top_edits

`GET /api/user/top_edits/{project}/{username}/{namespace}/{article}` — top-edited pages by a user; pass a page title as `article` (omit `namespace`) for all edits to one page. ⚠️ **Responses are large for active editors** (hundreds of KB); entries include `full_page_title`, `count`, `rank`, `assessment`, `timestamp`, `minor`, `reverted`, `length_change`, `comment`. Paginate with `offset` (timestamp-based).

### category_editcount

`GET /api/user/category_editcount/{project}/{username}/{categories}/{start}/{end}` — edits to pipe-separated categories. `categories` always returned as an array.

### log_counts

`GET /api/user/log_counts/{project}/{username}` — counts of logged actions (delete, protect, block, …) by action name.

### month_counts / timecard

- `GET /api/user/month_counts/{project}/{username}` — edits grouped by namespace → `YYYY-MM` → count (with `totals`).
- `GET /api/user/timecard/{project}/{username}` — edits per hour-of-day / day-of-week with a relative `scale` for heatmap-style analysis.

### globalcontribs

`GET /api/user/globalcontribs/{username}/{namespace}/{start}/{end}/{offset}` — edits across **all Wikimedia projects** (no project prefix in path!). ⚠️ Heavy for active users; expect large responses.

## Project endpoints

### normalize / namespaces

- `GET /api/project/normalize/{project}` — canonical domain for a project/dbname.
- `GET /api/project/namespaces/{project}` — namespace IDs → localized names.

### assessments & configuration

- `GET /api/project/assessments/{project}/{pages}` — batch page assessments (see page-api.md).
- `GET /api/project/assessments_configuration/{project}` — which classes/importance levels the project uses (some wikis have custom schemes).

### automated_tools

`GET /api/project/automated_tools/{project}` — the (semi-)automated tool registry for the project, nested under `tools` (label, link, description). (The old `/api/user/automated_tools` was removed in 3.18.0 — use this.)

### admin / patroller / steward stats

- `GET /api/project/admin_stats/{project}/{start}/{end}` — per-admin action counts (delete, protect, block, …). ⚠️ **Heavy**: measured 1.85s / 89 KB for enwiki — use date ranges.
- `GET /api/project/patroller_stats/{project}/{start}/{end}` — per-patroller revert/rollback counts.
- `GET /api/project/steward_stats/{project}/{start}/{end}` — steward actions (cross-wiki).
- `GET /api/project/admin_groups/{project}`, `patroller_groups`, `steward_groups` — current group membership lists. (Legacy `users_groups`/`admins_groups` endpoints were removed in 3.18.0.)

### largest_pages

`GET /api/project/largest_pages/{project}/{namespace}` — largest pages by byte size in a namespace. Niche but handy for cleanup drives.

## Worked examples

```bash
# Top 10 editors of an article in 2025, bots excluded
curl -s "https://xtools.wmcloud.org/api/page/top_editors/en.wikipedia.org/Metallica/2025-01-01/2025-12-31/10?nobots=1" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"

# Edit count for an IP address
curl -s "https://xtools.wmcloud.org/api/user/simple_editcount/en.wikipedia.org/24.49.192.8" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"

# Pages created by a user in mainspace, live pages only
curl -s "https://xtools.wmcloud.org/api/user/pages_count/en.wikipedia.org/Fuzheado/0/noredirects/live" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"

# Global edits across all projects
curl -s "https://xtools.wmcloud.org/api/user/globalcontribs/Fuzheado" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
```

## Error notes

- `404` — user/page/project not found (note: the API treats IP-with-no-edits as not found).
- `501` — user has >600,000 edits; expected for superusers/bots; do not retry.
- `503` — service overloaded; back off for minutes.
- `504` — query killed after 900s; narrow scope.
