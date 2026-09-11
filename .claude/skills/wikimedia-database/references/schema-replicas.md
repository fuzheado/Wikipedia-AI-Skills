# Wikimedia Replica Database Schema Reference

Key tables and columns in Wikimedia production replicas. Queries run against
databases ending in `_p` (e.g., `enwiki_p`, `commonswiki_p`, `wikidatawiki_p`).

---

## ⚠️ Commons: links tables are on a separate cluster (`x4`)

Since **2026-09-08**, the Commons links tables live in a new `x4` database cluster,
separate from the core (`s4`) cluster. This is a *location* change, not a schema
change — table and column names are unchanged — but the tables are only reachable
through a different hostname, and rows are no longer written to the old location.

**Tables moved to `x4`:** `linktarget`, `externallinks`, `pagelinks`,
`templatelinks`, `categorylinks`, `collation`, `imagelinks`, `globalimagelinks`,
`iwlinks`, `existencelinks`, `langlinks`

**Still on the core cluster, and also present on `x4`:** `page`, `redirect`

| Old hostname | New hostname (for the links tables) |
|---|---|
| `commonswiki.analytics.db.svc.wikimedia.cloud` | `links.commonswiki.analytics.db.svc.wikimedia.cloud` |
| `commonswiki.web.db.svc.wikimedia.cloud` | `links.commonswiki.web.db.svc.wikimedia.cloud` |
| `testcommonswiki.analytics.db.svc.wikimedia.cloud` | `links.testcommonswiki.analytics.db.svc.wikimedia.cloud` |
| `testcommonswiki.web.db.svc.wikimedia.cloud` | `links.testcommonswiki.web.db.svc.wikimedia.cloud` |

**The rule that bites:** *"any code performing JOINs between those tables and other
`commonswiki` … will need to be changed to perform the same operations in code
instead."* A cross-cluster `JOIN categorylinks … JOIN page` that used to work now
fails (or, if it hits the frozen core copies, returns silently stale results).

```python
# Two connections, one join — done in Python, not in SQL.
core_c = pymysql.connect(host=CORE_HOST, ...)    # commonswiki_p        -> page, redirect
links_c = pymysql.connect(host=LINKS_HOST, ...)  # links.commonswiki_p  -> categorylinks, ...

with core_c.cursor() as cur:
    cur.execute("SELECT page_id, page_title FROM page "
                "WHERE page_namespace = 14 AND page_is_redirect = 0")
    cats = {pid: title for pid, title in cur.fetchall()}

with links_c.cursor() as cur:
    cur.execute("SELECT cl_from, cl_to FROM categorylinks")
    membership = cur.fetchall()

# join in code, not in SQL
for cl_from, cl_to in membership:
    if cl_from in cats:
        ...
```

**Status / timeline:** hostnames announced and writes switched on 2026-09-08 (old
core tables frozen, to be dropped); exposing `x4` on the Wiki Replicas as a
separate section is still pending, after which queries return fresh data again but
with no access to the core copies of these tables. Tracked in
[T343131](https://phabricator.wikimedia.org/T343131) and
[T398709](https://phabricator.wikimedia.org/T398709); announcement
[News/2026 Commons links tables database split](https://wikitech.wikimedia.org/wiki/News/2026_Commons_links_tables_database_split).
Why: the Commons database has been growing too fast.

---

## `page` — Core page metadata

| Column | Type | Description |
|---|---|---|
| `page_id` | int | Unique page identifier |
| `page_namespace` | int | Namespace (0=Main, 1=Talk, 2=User, 6=File, 10=Template, 14=Category, 118=Draft, etc.) |
| `page_title` | varbinary(255) | Page title (URL-encoded, e.g., `Albert_Einstein`) |
| `page_is_redirect` | tinyint | 1 if this is a redirect page |
| `page_is_new` | tinyint | 1 if page has only one revision |
| `page_touched` | binary(14) | Timestamp of last page touch |
| `page_links_updated` | varbinary(14) | Timestamp of last links update |
| `page_latest` | int | `rev_id` of the latest revision |
| `page_len` | int | Content length in bytes |
| `page_content_model` | varbinary(32) | Content model (e.g., `wikitext`) |
| `page_is_redirect` | tinyint | Redirect status |

### Common namespace values

| Namespace ID | Name |
|---|---|
| 0 | Main (articles) |
| 1 | Talk |
| 2 | User |
| 3 | User talk |
| 4 | Project (Wikipedia) |
| 6 | File |
| 10 | Template |
| 14 | Category |
| 118 | Draft |
| 710 | Flow/Topic |

### Common queries

```sql
-- Get page info
SELECT page_id, page_title, page_len, page_touched
FROM page
WHERE page_title = 'Albert_Einstein' AND page_namespace = 0;

-- Get redirect target
SELECT rd_title, rd_namespace
FROM redirect
JOIN page ON rd_from = page_id
WHERE page_title = 'UK' AND page_namespace = 0;

-- Find uncategorized pages
SELECT page_title
FROM page
LEFT JOIN categorylinks ON cl_from = page_id
WHERE page_namespace = 0 AND cl_from IS NULL
LIMIT 50;
```

---

## `revision` / `revision_userindex` — Page revisions

| Column | Type | Description |
|---|---|---|
| `rev_id` | int | Unique revision ID |
| `rev_page` | int | `page_id` this revision belongs to |
| `rev_actor` | bigint | Actor ID (join with `actor` table) |
| `rev_timestamp` | binary(14) | Timestamp in `YYYYMMDDHHMMSS` format |
| `rev_minor_edit` | tinyint | 1 if minor edit |
| `rev_deleted` | tinyint | Deletion flags |
| `rev_len` | int | Revision text length |
| `rev_parent_id` | int | `rev_id` of the parent revision |
| `rev_sha1` | varbinary(32) | SHA-1 of revision text |
| `rev_comment_id` | bigint | Join with `comment` table for edit summary |

**Note:** Use `revision_userindex` instead of `revision` for queries
filtering by user. It has better indexes.

```sql
-- Recent edits to a page
SELECT rev_id, rev_timestamp, rev_minor_edit, rev_len
FROM revision
WHERE rev_page = 736  -- Albert Einstein
ORDER BY rev_timestamp DESC
LIMIT 20;

-- Count edits by user
SELECT COUNT(*) as edit_count
FROM revision_userindex
JOIN actor ON rev_actor = actor_id
WHERE actor_name = 'ExampleUser';
```

---

## `actor` — Unified actor (user) IDs

| Column | Type | Description |
|---|---|---|
| `actor_id` | bigint | Unique actor ID |
| `actor_name` | varbinary(255) | Username or IP address |
| `actor_user` | int | `user_id` from `user` table (NULL for IPs) |

---

## `page_props` — Page properties (key-value)

| Column | Type | Description |
|---|---|---|
| `pp_page` | int | `page_id` |
| `pp_propname` | varbinary(60) | Property name |
| `pp_value` | text | Property value |
| `pp_sortkey` | float | Sort key (for numeric properties) |

### Useful property names

| Property | Description | Value type |
|---|---|---|
| `pageview_daily_average` | Average daily pageviews | Float (use `CAST AS UNSIGNED`) |
| `wikibase_item` | Linked Wikidata Q-ID | String (e.g., `Q937`) |
| `noeditsection` | Disable section edit links | String |
| `displaytitle` | Custom display title | String |
| `defaultsort` | Default sort key | String |
| `page_image_free` | Free-license lead image | String (filename) |

```sql
-- Get average daily views for pages in a category
SELECT page_title, CAST(pp_value AS UNSIGNED) as avg_views
FROM page
JOIN page_props ON pp_page = page_id
JOIN categorylinks ON cl_from = page_id
WHERE cl_to = 'Physics'
  AND pp_propname = 'pageview_daily_average'
  AND page_namespace = 0
ORDER BY avg_views DESC
LIMIT 50;

-- Get Wikidata Q-IDs for a set of pages
SELECT page_title, pp_value as wikidata_qid
FROM page
JOIN page_props ON pp_page = page_id
WHERE pp_propname = 'wikibase_item'
  AND page_title IN ('Albert_Einstein', 'Isaac_Newton', 'Marie_Curie')
  AND page_namespace = 0;
```

---

## `categorylinks` — Category membership

| Column | Type | Description |
|---|---|---|
| `cl_from` | int | `page_id` of the page |
| `cl_to` | varbinary(255) | Category name (without `Category:` prefix) |
| `cl_type` | varbinary(10) | `page`, `subcat`, or `file` |

```sql
-- All pages in a category
SELECT page_title
FROM categorylinks
JOIN page ON cl_from = page_id
WHERE cl_to = 'Physics'
  AND page_namespace = 0
LIMIT 100;

-- Count of categories a page belongs to
SELECT page_title, COUNT(*) as category_count
FROM categorylinks
JOIN page ON cl_from = page_id
WHERE page_id = 736
GROUP BY page_title;

-- Subcategories of a category
SELECT cl_to as subcategory
FROM categorylinks
WHERE cl_from IN (
  SELECT page_id FROM page
  JOIN categorylinks ON cl_from = page_id
  WHERE cl_to = 'Physics' AND page_namespace = 14
)
AND cl_type = 'subcat';
```

---

## `pagelinks` — Internal page links

| Column | Type | Description |
|---|---|---|
| `pl_from` | int | Page that contains the link |
| `pl_namespace` | int | Target page namespace |
| `pl_title` | varbinary(255) | Target page title |

```sql
-- Count of pages linking to a given page
SELECT COUNT(*) as incoming_links
FROM pagelinks
WHERE pl_title = 'Albert_Einstein' AND pl_namespace = 0;
```

---

## `langlinks` — Interlanguage links

| Column | Type | Description |
|---|---|---|
| `ll_from` | int | Page ID |
| `ll_lang` | varbinary(20) | Language code (e.g., `fr`, `de`, `es`) |
| `ll_title` | varbinary(255) | Title in that language |

---

## Database naming conventions

| Database name | Content |
|---|---|
| `enwiki_p` | English Wikipedia |
| `commonswiki_p` | Wikimedia Commons |
| `wikidatawiki_p` | Wikidata |
| `dewiki_p` | German Wikipedia |
| `frwiki_p` | French Wikipedia |
| `metawiki_p` | Meta-Wiki |
| `enwiktionary_p` | English Wiktionary |
| `enwikisource_p` | English Wikisource |

Always use the `_p` suffix. The non-`_p` databases are the primary copy and
are not available via the Toolforge tunnel.
