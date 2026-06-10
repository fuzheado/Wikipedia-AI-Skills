---
name: wikimedia-page-assessment
description: Query Wikipedia article quality (FA/GA/B/C/Start/Stub) and importance ratings from WikiProject assessment banners on any Wikimedia wiki with the PageAssessments extension
license: MIT
compatibility: opencode
last_verified: 2026-06-10
---

Enables the agent to retrieve quality and importance ratings for Wikipedia
articles. This data is derived from WikiProject banners on talk pages and is
stored in the `page_assessments` and `page_assessments_projects` tables in
Wikimedia database replicas.

### Which wikis have PageAssessments?

PageAssessments is **not** deployed on every language Wikipedia. It requires
active opt-in per wiki (via a Phabricator request to WMF). As of 2026, the
following wikis have it enabled, with subproject/task-force support noted:

| Wiki | Subprojects enabled? | Phab ticket |
|---|---|---|
| **English Wikipedia** (`enwiki`) | ✅ | T146679 |
| **English Wikivoyage** (`enwikivoyage`) | ❌ | T142056 |
| **French Wikipedia** (`frwiki`) | ❌ | T153393 |
| **Arabic Wikipedia** (`arwiki`) | ❌ | T185023 |
| **Turkish Wikipedia** (`trwiki`) | ❌ | T184969 |
| **Hungarian Wikipedia** (`huwiki`) | ❌ | T191697 |
| **Chinese Wikipedia** (`zhwiki`) | ✅ | T326387 |
| **Nepali Wikipedia** (`newiki`) | ✅ | T328224 |
| **Test Wikipedia** (`testwiki`) | ✅ | T137918 |

This means the `page_assessments` tables will be **empty** on other language
Wikipedias (dewiki, eswiki, jawiki, ruwiki, etc.). Most queries and examples
in this skill target **English Wikipedia** (`enwiki_p`), which has the most
comprehensive assessment coverage by far.

## **Prerequisites**

* **Database access:** Requires an active SSH tunnel to Toolforge per the
  `wikimedia-database` skill.
* **Credentials:** `TOOLFORGE_USER`, `TOOLFORGE_SQL_USER`, `TOOLFORGE_SQL_PASSWORD`
  in `.env` or environment.
* **SSH keys:** Added to `ssh-agent` for non-interactive tunnel connections.

## **Database Schema: `enwiki_p`**

Three primary tables:

1. **`page_assessments`** — One row per assessment (page × WikiProject pair).
   | Column | Type | Description |
   |---|---|---|
   | `pa_page_id` | int | Page ID of the Subject article (namespace 0) |
   | `pa_project_id` | int | Foreign key to `page_assessments_projects` |
   | `pa_class` | varbinary(20) | Quality grade: `FA`, `GA`, `B`, `C`, `Start`, `Stub`, `List`, `FL`, `A`, `Book`, `Category`, `Disambig`, `File`, `Portal`, `Project`, `Redirect`, `Template`, `NA` |
   | `pa_importance` | varbinary(20) | Priority: `Top`, `High`, `Mid`, `Low`, `NA`, `Unknown` |
   | `pa_page_revision` | int | Revision ID when this assessment was last updated (join with `revision` table for timestamp) |

2. **`page_assessments_projects`** — WikiProject name mapping.
   | Column | Type | Description |
   |---|---|---|
   | `pap_project_id` | int | Primary key |
   | `pap_project_title` | varbinary(255) | WikiProject name, e.g. `"Chemistry"`, `"Medicine"` |
   | `pap_parent_id` | int | Parent project ID for subprojects/task forces (NULL if top-level) |

3. **`page`** — Core page metadata for title resolution.
   | Column | Type | Description |
   |---|---|---|
   | `page_id` | int | Joins to `pa_page_id` |
   | `page_title` | varbinary(255) | Article title (underscores, e.g. `Albert_Einstein`) |
   | `page_namespace` | int | `0` for mainspace articles |

## **Core Data Model**

* **`pa_class`** — Quality grade. Standard values (ascending):
  `Stub` → `Start` → `C` → `B` → `GA` (Good Article) → `FA` (Featured Article)
* **`pa_importance`** — Priority within a WikiProject:
  `Top` → `High` → `Mid` → `Low` → `NA` / `Unknown`

## **Standard Implementation Pattern**

### SQL (via database tunnel)

```sql
-- Basic lookup: get assessment for a specific article
SELECT 
    p.page_title, 
    pap.pap_project_title AS wikiproject,
    pa.pa_class, 
    pa.pa_importance
FROM page_assessments pa
JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
JOIN page p ON pa.pa_page_id = p.page_id
WHERE p.page_title = 'YOUR_PAGE_TITLE'  -- Replace spaces with underscores
  AND p.page_namespace = 0;
```

### Python (for programmatic use)

```python
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

conn = pymysql.connect(
    host='127.0.0.1',
    port=int(os.getenv('TOOLFORGE_DB_PORT', '3307')),
    user=os.getenv('TOOLFORGE_SQL_USER'),
    password=os.getenv('TOOLFORGE_SQL_PASSWORD'),
    database='enwiki_p',
    cursorclass=pymysql.cursors.DictCursor,
    charset='utf8mb4'
)

with conn.cursor() as cursor:
    cursor.execute("""
        SELECT pap.pap_project_title AS wikiproject,
               pa.pa_class, pa.pa_importance
        FROM page_assessments pa
        JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
        JOIN page p ON pa.pa_page_id = p.page_id
        WHERE p.page_title = 'Albert_Einstein'
          AND p.page_namespace = 0
    """)
    for row in cursor.fetchall():
        print(f"[{row['wikiproject']}] Class={row['pa_class']}, Importance={row['pa_importance']}")
conn.close()
```

### MySQL 9+ compatibility

If you get `ERROR 2059: Authentication plugin 'mysql_native_password' cannot be loaded`
when using the `mysql` CLI, this is because **MySQL 9.x removed the
`mysql_native_password` plugin entirely** from the client — both as a loadable
`.so` and as a compiled-in implementation. Neither `--default-auth` nor any
other flag can work around this.

**The fix is to use `pymysql`** (pure Python). It implements the MySQL protocol
natively and handles `mysql_native_password` authentication without any
external plugins:

```bash
pip install pymysql python-dotenv
```

The scripts in this skill (`assess-project.sh`, `quality-gaps.sh`) will
automatically use `pymysql` if available, falling back to the `mysql` CLI only
if Python dependencies are missing.

## **Constraint & Guardrails**

1. **Talk Page Paradox:** Assessment templates exist on **Talk pages** (Namespace 1),
   but `pa_page_id` refers to the **Subject page** (Namespace 0). Always join with
   the Subject page ID for title resolution.

2. **Duplicate Titles:** A single page will have multiple rows if it is assessed by
   multiple WikiProjects. Use `GROUP_CONCAT` or your application-level grouping.

3. **Normalization:** Ratings are strings. Some projects use non-standard classes
   (e.g., `"Future"`, `"Current"`, `"Draft"`). The standard ordinal scale is:
   `Stub` → `Start` → `C` → `B` → `GA` → `FA`.

4. **Case Sensitivity:** WikiProject titles in `pap_project_title` are case-sensitive.
   `"medicine"` will fail; `"Medicine"` will succeed.

5. **Safety Limits:** Every exploratory query **must** include a `LIMIT` (default 10-50).

## **Example Use Cases for Agent**

* "Find all 'Featured Articles' in the 'Computing' WikiProject."
* "Identify high-importance stubs that need immediate expansion."
* "Compare the average quality of articles in 'WikiProject Maryland' versus 'WikiProject Virginia'."
* "List every WikiProject that assesses articles about 'Chemistry'."
* "For the 'Physics' WikiProject, find all B-class articles with Top importance that haven't been assessed in over 5 years."

---

## **Tooling**

This skill includes helper scripts, reference docs, and templates:

### 🔧 Assess Project (`scripts/assess-project.sh`)

Get quality and importance distribution for any WikiProject.

```bash
./scripts/assess-project.sh "Chemistry" [limit]
./scripts/assess-project.sh "Medicine" 100
```

### 🔧 Quality Gaps (`scripts/quality-gaps.sh`)

Find high-importance articles with low quality — the highest-ROI improvement targets.

```bash
./scripts/quality-gaps.sh "Physics" [limit]
./scripts/quality-gaps.sh "Biology" 50
```

### 📚 Schema Reference (`references/assessments-schema.md`)

Full reference of the `page_assessments` and `page_assessments_projects` tables
with column descriptions, join patterns, and edge cases.

### 🧩 Sample SQL Queries (`assets/sample-queries.sql`)

20+ pre-built SQL queries for assessments organized by category:
project-level summaries, article lookups, quality gaps, importance distributions,
multi-project intersections, and maintenance workflows.

### 🧩 Environment Template (`assets/.env.example`)

```bash
cp assets/.env.example .env
# Edit .env with your credentials
```
