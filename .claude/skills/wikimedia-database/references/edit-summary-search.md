# Edit Summary Search on Wikipedia

Searching edit summaries (the text comment accompanying each revision) is a
surprisingly hard problem. There is no built-in full-text index, no API
endpoint, and no off-the-shelf tool that searches across all users. This
reference catalogs every viable approach, ranked by practicality.

## Why It's Hard

The `comment` table (MediaWiki ≥1.30) stores all edit summaries in `comment_text`,
linked via `revision.rev_comment_id → comment.comment_id`.

**Indexes on the `comment` table:**

| Index | Column | Purpose |
|-------|--------|---------|
| `PRIMARY` | `comment_id` | Row lookup |
| `comment_hash` | `comment_hash` | CRC32 dedup (best-effort) |

There is **no index on `comment_text`** — no BTREE, no FULLTEXT. A `LIKE
'%term%'` requires a full table scan of billions of rows. Without additional
constraints, this times out on Toolforge/Quarry replicas.

The old `revision.rev_comment` TINYBLOB field was removed in MediaWiki 1.35.

## Approach 1: Σ (Sigma) Edit Summary Search

- **URL:** https://iw.toolforge.org/sigma/summary.py
- **Created by:** User:Σ
- **What it does:** Searches edit summaries of a **single user** on a wiki.
  Supports namespace filter, date range, case sensitivity, and section-title
  exclusion.
- **How it works:** Constrained SQL (`WHERE actor_name = ...`) to stay within
  replica limits.
- **Limitation:** One user at a time. Doesn't work well for users with very few
  edits (no results to match against).

## Approach 2: Constrained SQL on Replicas

Viable only when **both** a user filter AND a date constraint are present:

```sql
SELECT rev_id, rev_timestamp, actor_name, comment_text
FROM revision
JOIN comment ON rev_comment_id = comment_id
JOIN actor ON rev_actor = actor_id
WHERE actor_name = 'ExampleUser'
  AND comment_text LIKE '%search term%'
  AND rev_timestamp > '20240101000000'
LIMIT 100;
```

Without `actor_name` + `rev_timestamp` constraints, this will time out.

The `revision_userindex` table can substitute for `revision` when filtering by
user (it has an index on `rev_actor`).

## Approach 3: XML Dumps

The `stub-meta-history` dump includes revision metadata (edit summaries, but
not full page text):

- **enwiki size:** ~122 GB compressed (as of July 2026)
- **URL:** `https://dumps.wikimedia.org/enwiki/latest/`
- **Files:** `enwiki-latest-stub-meta-history*.xml.gz`

Process with a streaming SAX parser in Python — don't load the full file into
memory. A single pass can grep all edit summaries across all of Wikipedia
history. Good for one-time research projects.

## Approach 4: EventStreams (Real-Time Only)

Filter live edits by summary text via SSE. Supports up to 31 days of replay
via `?since=`. Good for monitoring; useless for historical search beyond the
replay window.

URL: `https://stream.wikimedia.org/v2/stream/recentchange`

## Approach 5: Special:Contributions + Ctrl+F

For a single user with moderate edit count: load their contributions page,
browser-search within. No tooling required. Completely manual.

## What Doesn't Work

| Approach | Why |
|----------|-----|
| **CirrusSearch** | Indexes page wikitext, not revision metadata. No `insummary:` keyword. |
| **Action API search** | `list=search` uses CirrusSearch — same limitation. |
| **Action API recentchanges** | Returns summaries but has no filter parameter for summary text. |
| **Unconstrained SQL** | `LIKE '%term%'` without user+date filters = timeout. |

## Structural Gap

There is **no open Phabricator task** (as of July 2026) for adding a FULLTEXT
index to `comment_text`. The `MediaWiki-Comment-store` project workboard covers
other concerns (ping notifications, mobile length limits, section-link
formatting) but not search. This is a genuine blind spot in the platform.
