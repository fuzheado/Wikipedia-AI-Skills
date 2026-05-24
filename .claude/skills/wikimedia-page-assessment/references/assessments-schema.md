# Page Assessments Schema Reference

The PageAssessments extension parses WikiProject assessment banners from talk
pages and stores structured data in the `page_assessments` table. Queries run
against the `enwiki_p` database (or any `*wiki_p` replica that has the
extension installed).

## Deployment scope

PageAssessments is **not** a default extension across all Wikimedia wikis. It
is deployed on a per-wiki basis via WMF config. As of 2026, only 9 wikis have
it enabled (see the main `SKILL.md` for the full list). Most queries target
**English Wikipedia** (`enwiki_p`) because it has the most comprehensive
assessment coverage.

Attempting to query `page_assessments` on a wiki without the extension
(e.g. `dewiki_p`, `eswiki_p`, `jawiki_p`) will return an empty table or a
"table not found" error.

Official docs: https://www.mediawiki.org/wiki/Extension:PageAssessments

---

## `page_assessments` — Assessment values per page per project

One row per assessment — a single article may have multiple rows if assessed by
multiple WikiProjects.

| Column | Type | Null | Description |
|---|---|---|---|
| `pa_page_id` | int(10) unsigned | NO | Page ID of the *subject* article (namespace 0), not the talk page |
| `pa_project_id` | int(10) unsigned | NO | Foreign key to `page_assessments_projects.pap_project_id` |
| `pa_class` | varbinary(20) | YES | Quality grade (see values below). Binary — decode with `.decode('utf-8')` |
| `pa_importance` | varbinary(20) | YES | Priority within the WikiProject. Binary — decode with `.decode('utf-8')` |
| `pa_page_revision` | int(10) unsigned | NO | Revision ID when this assessment was last updated. Join with `revision` table to get the timestamp. |

> **Note:** The MediaWiki extension documentation lists `pa_assessed_timestamp` and
> `pa_page_namespace` as columns, but these are **not present** in the actual
> Wikimedia production replicas. The real schema uses `pa_page_revision` instead.

### Quality class values (`pa_class`)

Standard values, ordered from lowest to highest quality:

| Value | Meaning | Description |
|---|---|---|
| `Stub` | Stub | Very short, minimal information |
| `Start` | Start | Adequate but incomplete |
| `C` | C-class | Substantial but missing key content |
| `B` | B-class | Mostly complete with some gaps |
| `GA` | Good Article | Reviewed as meeting Good Article criteria |
| `FA` | Featured Article | The highest quality — reviewed community standard |
| `FL` | Featured List | Featured list-class article |
| `A` | A-class | Professional/encyclopedic (rare outside military history) |
| `List` | List | List article |
| `Book` | Book | Community book |
| `Category` | Category | Category page |
| `Disambig` | Disambig | Disambiguation page |
| `File` | File | File/media page |
| `Portal` | Portal | Portal page |
| `Project` | Project | WikiProject page |
| `Redirect` | Redirect | Redirect page |
| `Template` | Template | Template page |
| `NA` | N/A | Non-article page (used by some projects) |

### Importance values (`pa_importance`)

| Value | Meaning |
|---|---|
| `Top` | Essential for understanding the topic |
| `High` | Significant coverage needed |
| `Mid` | Reasonable coverage expected |
| `Low` | Minor but still within scope |
| `NA` | Not applicable (non-article pages) |
| `Unknown` | Not yet assessed |

---

## `page_assessments_projects` — WikiProject name mapping

Maps the integer `pa_project_id` to human-readable WikiProject titles.

| Column | Type | Null | Description |
|---|---|---|---|
| `pap_project_id` | int(10) unsigned | NO | Primary key |
| `pap_project_title` | varbinary(255) | YES | WikiProject name, e.g. `"Chemistry"`, `"Medicine"`, `"Biography"`. Binary — decode with `.decode('utf-8')` |
| `pap_parent_id` | int(10) unsigned | YES | Parent project ID for subprojects/task forces. NULL if top-level. |

### Notes

- WikiProject titles are stored as **varbinary** — always decode with `.decode('utf-8')`.
- Titles are **case-sensitive**: `"medicine"` ≠ `"Medicine"`.
- Common prefixes: `"WikiProject "` is **not** stored — the title is just
  `"Chemistry"`, not `"WikiProject Chemistry"`.
- Some projects have sub-pages like `"Biography (science and academia)"`.
- `pap_parent_id` lets you find subprojects: `SELECT * FROM page_assessments_projects WHERE pap_parent_id IS NOT NULL;`

---

## `page` — Core page resolution

Standard MediaWiki `page` table used to resolve `pa_page_id` to `page_title`.

| Column | Type | Description |
|---|---|---|
| `page_id` | int(10) unsigned | Primary key — joins to `pa_page_id` |
| `page_title` | varbinary(255) | URL-encoded title with underscores |
| `page_namespace` | int(11) | Namespace: `0` for mainspace articles |
| `page_is_redirect` | tinyint(4) | 1 if redirect |
| `page_len` | int(10) unsigned | Content length in bytes |

---

## Common join patterns

### Pattern A: Single article, all assessments

```sql
SELECT pap.pap_project_title AS wikiproject,
       pa.pa_class,
       pa.pa_importance
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
WHERE p.page_title = 'Albert_Einstein'
  AND p.page_namespace = 0;
```

### Pattern B: One row per article with concatenated assessments

```sql
SELECT p.page_title,
       GROUP_CONCAT(
           CONCAT(pap.pap_project_title, ':', pa.pa_class, '/', pa.pa_importance)
           SEPARATOR '; '
       ) AS assessments
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
WHERE p.page_namespace = 0
GROUP BY p.page_id, p.page_title
LIMIT 50;
```

### Pattern C: All articles in a WikiProject with their assessment

```sql
SELECT p.page_title,
       pa.pa_class,
       pa.pa_importance,
       pa.pa_page_revision
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
WHERE pap.pap_project_title = 'Chemistry'
  AND p.page_namespace = 0
  AND p.page_is_redirect = 0
ORDER BY pa.pa_class ASC, pa.pa_importance ASC
LIMIT 100;
```

---

## Edge cases

1. **Redirects:** `pa_page_id` always points to the subject page, not a
   redirect. But the subject page itself could be a redirect — filter with
   `p.page_is_redirect = 0`.

2. **Multiple assessments from one WikiProject:** Rare, but possible if a
   WikiProject has sub-projects or if templates were re-evaluated. Use
   `DISTINCT` or `GROUP BY` to deduplicate.

3. **Unassessed articles:** Articles within a WikiProject's scope that don't
   have an assessment banner won't appear in `page_assessments` at all. Use
   `categorylinks` to find all articles in a project's scope.

4. **Non-standard classes:** Some WikiProjects use non-standard classes like
   `"Future"`, `"Current"`, `"Draft"`, or `"SIA"` (Set Index Article). Always
   check for unexpected values when aggregating.

5. **Stale assessments:** The assessment reflects the article state at the time
   of the last review. To find the timestamp, join with the `revision` table:
   `SELECT rev_timestamp FROM revision WHERE rev_id = pa.pa_page_revision`.
