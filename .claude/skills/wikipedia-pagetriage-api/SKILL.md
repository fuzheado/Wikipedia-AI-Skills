---
name: wikipedia-pagetriage-api
description: Work with the PageTriage extension (New Pages Feed / Page Curation) — list unreviewed pages, check review status, tag pages, and patrol new content on wikis where PageTriage is deployed
depends_on: [wikimedia-api-access]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["PageTriage", "NPP", "new page patrol", "unreviewed", "page curation"]
  - keywords: ["pagetriagelist", "patrol", "new pages feed", "review status"]
last_verified: 2026-06-10
---

> ⚠️ **PageTriage is primarily deployed on English Wikipedia.** As of mid-2026,
> the extension is in active production use only on **enwiki** and **testwiki**.
> Deployment to ruwiki is in progress. Several other wikis (fr, id, ur, ar, fa, ml)
> have open Phabricator requests (e.g. T44322, T68260, T99251) but no confirmed rollout.
> The `$wgPageTriageEnableEnglishWikipediaFeatures` configuration flag controls
> enwiki-specific features. Before assuming PageTriage is available on a given wiki,
> verify at `Special:Version` or check for `action=pagetriagelist` in the API sandbox
> (`/w/api.php?action=help&modules=main`).

> ⚠️ **Patrol right required for write operations.** Listing unreviewed pages and
> marking pages as reviewed requires the `patrol` user right (granted to New Page
> Reviewers and administrators). Read-only status checks on individual pages
> are available to all users via `prop=info&inprop=protection`.

---

## SOP: Checking PageTriage Availability on a Wiki

```bash
curl -s -H "User-Agent: MyBot/1.0 (user@example.com) PageTriageCheck" \
  "https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&siprop=extensions&format=json" \
  | python3 -c "import sys,json; ext=[e['name'] for e in json.load(sys.stdin)['query']['extensions'] if 'PageTriage' in e['name']]; print('✓ PageTriage enabled' if ext else '✗ PageTriage not available')"
```

Or check the API sandbox for PageTriage-specific modules:

```bash
# Look for pagetriagelist in the module list
curl -s -H "User-Agent: MyBot/1.0 (user@example.com) PageTriageCheck" \
  "https://en.wikipedia.org/w/api.php?action=help&modules=main&format=json" | grep -i pagetriage
```

---

## SOP: PageTriage Review Status Codes

The `pagetriage_page` SQL table stores review status in the `ptrp_reviewed` column:

| Value | Meaning | Notes |
|-------|---------|-------|
| `0` | **Unreviewed** | Needs NPP review |
| `1` | **Reviewed** | Marked reviewed by a reviewer |
| `2` | **Patrolled** | Marked as patrolled (typically by an admin) |
| `3` | **Autopatrolled** | Creator has the autopatrolled right; page was auto-marked |

The legacy `action=query&list=unreviewedpages` API also uses a `filterlevel` parameter:

| `filterlevel` | Meaning |
|---------------|---------|
| `0` | Pages not reviewed at all (`ptrp_reviewed = 0`) |
| `1` | Pages not checked for quality (`ptrp_reviewed = 0` or `1`) |

---

## Reference: PageTriage API Endpoints

The PageTriage extension adds the following API modules:

### `action=pagetriagelist` — List pages in the queue

```
GET https://en.wikipedia.org/w/api.php?action=pagetriagelist&...&format=json
```

| Parameter | Values | Description |
|---|---|---|
| `page_id` | integer | Get metadata for a single page ID |
| `showreviewed` | 1 | Include reviewed pages |
| `showunreviewed` | 1 | Include unreviewed pages |
| `showredirs` | 1 | Include redirects |
| `showdeleted` | 1 | Include deleted pages |
| `showothers` | 1 | Include pages in other namespaces |
| `limit` | 1–max | Max results (use `max` for 500) |
| `offset` | string | Pagination cursor |

**Notes:**
- Must specify at least one of `showreviewed`/`showunreviewed`
- Returns metadata blobs per page including creation date, creator, page length
- Requires the `patrol` right

**Example — last 50 unreviewed articles:**
```bash
curl -s -H "User-Agent: MyBot/1.0 (user@example.com) PageTriageCheck" \
  "https://en.wikipedia.org/w/api.php?action=pagetriagelist&showunreviewed=1&noredirects=1&limit=50&format=json"
```

### `action=pagetriageaction` — Mark reviewed/unreviewed

```
POST https://en.wikipedia.org/w/api.php?action=pagetriageaction&...
```

| Parameter | Values | Description |
|---|---|---|
| `pageid` | integer | Page to act on |
| `reviewed` | 1 | Mark as reviewed |
| `reviewed` | 0 | Mark as unreviewed (un-patrol) |
| `enqueue` | 1 | Add to the review queue |
| `token` | string | CSRF token (`action=query&meta=tokens`) |

**Example — mark a page as reviewed:**
```bash
curl -s -X POST "https://en.wikipedia.org/w/api.php" \
  -H "User-Agent: MyBot/1.0 (user@example.com) PageTriageCheck" \
  -d "action=pagetriageaction" \
  -d "pageid=12345" \
  -d "reviewed=1" \
  -d "token=YOUR_CSRF_TOKEN" \
  -d "format=json"
```

### `action=pagetriagetagging` — Apply curation tags

```
POST https://en.wikipedia.org/w/api.php?action=pagetriagetagging&...
```

| Parameter | Values | Description |
|---|---|---|
| `pageid` | integer | Page to tag |
| `taglist` | comma-separated | Tags from the curation toolbar (e.g. `db-g11`, `maintenance`) |
| `wikitext` | string | Wikitext to add/append to the page |
| `token` | string | CSRF token |

Requires the `patrol` right and is rate-limited via `pagetriage-tagging-action`.

### `action=query&list=unreviewedpages` — Legacy unreviewed list

```
GET https://en.wikipedia.org/w/api.php?action=query&list=unreviewedpages&...&format=json
```

| Parameter | Values | Description |
|---|---|---|
| `filterlevel` | 0, 1 | 0 = not reviewed, 1 = not quality-checked |
| `filterredir` | redirects, nonredirects, all | Include/exclude redirects |
| `namespace` | integer | Namespace to search |
| `limit` | 1–max | Results per page |
| `start` / `end` | page title | Title range boundaries |

**Note:** This is a simpler, older API that doesn't require the `patrol` right for reading,
but it only returns titles — no metadata blobs. Prefer `action=pagetriagelist` when you need
metadata and have patrol access.

---

## Reference: Finding New Pages Without Patrol Rights

If you do not have the `patrol` right, you can still discover newly created pages via
`list=recentchanges` and then check their patrol status using `rcprop=patrolled`
(requires the `patrolmarks` right — a broader permission often granted to the same
users). For truly unauthenticated access, use `list=recentchanges` without the
`patrolled` flag:

```bash
# Last 50 new mainspace pages (no patrol info — works for anyone)
curl -s -H "User-Agent: MyBot/1.0 (user@example.com) PageTriageCheck" \
  "https://en.wikipedia.org/w/api.php?action=query&list=recentchanges&rctype=new&rcnamespace=0&rclimit=50&format=json"
```

The response includes `pageid`, `revid`, `title`, `user`, and `timestamp` but no
patrol status. You can then fetch the wikitext and run your own analysis (see the
**[wikipedia-reference-verifiability](../wikipedia-reference-verifiability/SKILL.md)**
skill for one approach).

---

## Reference: PageTriage Database Table

When you have Toolforge SQL replica access, the `pagetriage_page` table
(on the `enwiki` replica) provides direct, efficient access:

```sql
SELECT ptrp_page_id, ptrp_reviewed, ptrp_created, ptrp_deleted
FROM pagetriage_page
WHERE ptrp_reviewed = 0
  AND ptrp_deleted = 0
  AND ptrp_created >= NOW() - INTERVAL 7 DAY
ORDER BY ptrp_created DESC
LIMIT 100;
```

This is much faster than the API for bulk queries and supports arbitrary joins
with the `page` and `revision` tables. See the **[wikimedia-database](../wikimedia-database/SKILL.md)**
skill for SSH tunnel setup.

---

## Tooling

### 🔧 List Unreviewed Pages (`scripts/list-unreviewed.sh`)

Query the last N unreviewed mainspace pages via the PageTriage API:

```bash
./scripts/list-unreviewed.sh enwiki 50
./scripts/list-unreviewed.sh testwiki 10
```

Outputs a table of page IDs, titles, creation dates, and creators.

### 🔧 Check Patrol Status (`scripts/check-status.sh`)

Check whether one or more specific pages have been reviewed:

```bash
./scripts/check-status.sh "Albert Einstein"
./scripts/check-status.sh "Betka Ait Mokran" "LOL: Slutty Bass"
```

Uses `prop=info&inprop=protection` and checks for the `autopatrolled` or `patrolled`
tags on the page.

### 🐍 Python PageTriage Client (`assets/pagetriage_client.py`)

A lightweight Python class that wraps the PageTriage API:

```python
from assets.pagetriage_client import PageTriageClient

client = PageTriageClient("enwiki")

# List unreviewed pages (needs patrol right)
pages = client.list_unreviewed(limit=50)
for p in pages:
    print(p["pageid"], p["title"], p["creation_date"])

# Check review status (no auth needed)
status = client.get_review_status("Albert Einstein")
print(f"Reviewed: {status['reviewed']}, by: {status['reviewer']}")
```

### 🐍 Patrol Simulator (`assets/patrol_simulator.py`)

Demonstrates the two-pass pipeline from the npp-finder tool: fetch new pages →
run reference analysis → enrich matches. Useful as a template for custom
patrol agents and NPP workflows.

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikipedia-reference-verifiability](../wikipedia-reference-verifiability/SKILL.md)** | Reference URL analysis for triaging new pages |
| **[wikipedia-notability-assessment](../wikipedia-notability-assessment/SKILL.md)** | Notability evaluation of unreviewed pages |
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent and authentication for PageTriage API calls |
| **[wikimedia-database](../wikimedia-database/SKILL.md)** | SQL queries against `pagetriage_page` table for bulk analysis |
| **[wikimedia-eventstreams](../wikimedia-eventstreams/SKILL.md)** | Real-time new page detection via `page-create` stream |