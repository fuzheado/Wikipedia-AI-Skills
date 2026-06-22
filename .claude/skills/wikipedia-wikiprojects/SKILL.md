---
name: wikipedia-wikiprojects
description: Understand and work with English Wikipedia's WikiProject system — finding relevant projects, interpreting assessment tables, using Popular pages and work lists, and navigating project directories
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access, wikipedia-page-anatomy]
skill_discovery_hints:
  - keywords: ["WikiProject", "WikiProject directory", "WikiProject assessment", "Popular pages"]
  - keywords: ["WikiProject banner", "project template", "task force", "work group"]
  - keywords: ["article alerts", "cleanup listing", "WikiProject Council"]
last_verified: 2026-06-22
---

> ⚠️ **User-Agent required:** The API examples below use the Action API. All
> requests must include a descriptive `User-Agent` header. See the
> **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the
> correct format.
>
> 📖 **This skill covers the English Wikipedia WikiProject system.** English Wikipedia
> has the largest WikiProject infrastructure (2,000+ projects, ~1,000 active).
> German Wikipedia (WikiProjekte/Redaktionen) and French Wikipedia (Projets) have
> active systems with their own conventions. Other language editions use WikiProjects
> to varying degrees. The concepts covered here (assessment tables, project directories,
> banner templates) are applicable across languages, but specific URLs, template names,
> and conventions are enwiki-specific.

---

## SOP: What WikiProjects Are

WikiProjects are **volunteer communities** that organize work around a specific
topic area. They assess article quality, track improvements, coordinate clean-up
drives, and maintain topic-specific guidelines. Every WikiProject is itself a
wiki page (or set of pages) in the `Wikipedia:` namespace.

WikiProjects serve three main functions:

1. **Assessment** — rate articles by quality (Stub→Start→C→B→GA→FA) and
   importance (Low→Mid→High→Top) within their topic area
2. **Coordination** — maintain work lists, article alerts, and cleanup listings
3. **Standards** — define style guides, reliable sources, and notability
   criteria specific to their topic

---

## SOP: Finding WikiProjects

### The Curated Directory

The primary entry point is the manually maintained directory:

```
https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Council/Directory
```

This organizes projects by broad topic area (Culture, Geography, History,
Science, Technology, etc.) with active/inactive status indicators.

### The Bot-Maintained Directory

A complementary list, auto-generated from on-wiki data:

```
https://en.wikipedia.org/wiki/Wikipedia:WikiProject_Directory
```

This is updated by bot and includes subproject/task-force information that may
not appear in the manual directory.

### Category-Based Discovery

All WikiProjects are categorized under `Category:WikiProjects`:

```bash
# List all WikiProjects (paginated, up to 500 pages)
curl -s -H "User-Agent: MyBot/1.0 (user@example.com)" \
  "https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&\
cmtitle=Category:WikiProjects&cmtype=page&cmlimit=max&format=json"
```

Subcategories include:
- `Category:Active WikiProjects` — actively maintained
- `Category:Inactive WikiProjects` — dormant or defunct
- `Category:WikiProject Council` — meta-project about WikiProjects

### Searching by Topic

To find the WikiProject for a specific topic, search the `Wikipedia:` namespace:

```bash
# Search for WikiProjects about "Chemistry"
curl -s -H "User-Agent: MyBot/1.0 (user@example.com)" \
  "https://en.wikipedia.org/w/api.php?action=query&list=search&\
srsearch=WikiProject Chemistry&srnamespace=4&format=json"
```

The naming convention is typically `Wikipedia:WikiProject <Topic>` or
`Wikipedia:WikiProject <Parent>/<Sub-topic>`.

---

## SOP: Understanding WikiProject Pages

Every active WikiProject has a main page (the project home) and may have
several important subpages:

### Common Subpages

| Subpage | Purpose | Example URL |
|---------|---------|-------------|
| `/Assessment` | Quality × importance matrix, statistics | `Wikipedia:WikiProject_Physics/Assessment` |
| `/Popular_pages` | Most-viewed articles in scope (bot-generated) | `Wikipedia:WikiProject_Physics/Popular_pages` |
| `/Article_alerts` | Automated notices: AfDs, PRODs, GANs, etc. | `Wikipedia:WikiProject_Physics/Article_alerts` |
| `/Cleanup_listing` | Articles needing cleanup, by type | `Wikipedia:WikiProject_Physics/Cleanup_listing` |
| `/Members` | List of project participants | `Wikipedia:WikiProject_Physics/Members` |
| `/To_do` | Manual task list maintained by members | `Wikipedia:WikiProject_Physics/To_do` |

Not all projects have all subpages — some are optional or require opt-in to
bot generation.

### The Assessment Table

The `/Assessment` subpage (when present) is the most information-dense page:

```
┌──────────┬───────┬──────┬────┬─────┬──────┬──────┬───────┐
│          │  Top  │ High │Mid │ Low │ None │Total │       │
├──────────┼───────┼──────┼────┼─────┼──────┼──────┼───────┤
│ FA       │   12  │  45  │ 89 │ 134 │   0  │  280 │       │
│ GA       │   23  │  67  │156 │ 289 │   0  │  535 │       │
│ B        │   45  │ 234  │567 │1234 │   0  │ 2080 │       │
│ C        │   34  │ 456  │890 │2345 │   0  │ 3725 │       │
│ Start    │   12  │ 345  │678 │4567 │   0  │ 5602 │       │
│ Stub     │    3  │  89  │234 │1890 │   0  │ 2216 │       │
│ List     │    5  │  23  │ 45 │ 123 │   0  │  196 │       │
│ Unassess │    0  │   0  │  0 │   0 │ 450  │  450 │       │
│ Total    │  134  │1259  │2659│10582│ 450  │15084 │       │
└──────────┴───────┴──────┴────┴─────┴──────┴──────┴───────┘
```

**How to read it:**
- **Top/High importance** + **Stub/Start quality** = highest-priority
  improvement targets
- **High importance + B/C quality** = good articles that could be improved to GA
- **Unassessed** articles haven't been rated yet — evaluate them first

### The Popular Pages Table

The `/Popular_pages` subpage is **bot-generated** from pageview data and shows
the most-read articles within the project's scope:

| Rank | Page | Views | Quality | Importance |
|------|------|-------|---------|------------|
| 1 | Physics | 1,234,567 | B | Top |
| 2 | Albert Einstein | 987,654 | FA | Top |
| 3 | Quantum mechanics | 876,543 | B | Top |
| ... | ... | ... | ... | ... |

The data is pre-sorted by pageviews descending. The bot (`Community_Tech_bot`)
updates these ~monthly.

**Master index of all Popular_pages reports:**
```
https://en.wikipedia.org/wiki/User:Community_Tech_bot/Popular_pages
```

This page indexes every WikiProject that has opted into the bot, organized by
topic category. Browse it to discover which projects have traffic data.

---

## SOP: Interpreting WikiProject Banners on Talk Pages

WikiProjects add **banner templates** to article talk pages. A single article
can be tagged by multiple WikiProjects. Example:

```wikitext
{{WikiProject Physics|class=B|importance=Top}}
{{WikiProject Biography|class=B|importance=Mid|s&a-work-group=yes}}
{{WikiProject Chemistry|class=C|importance=Low}}
```

### What the Banner Tells You

| Parameter | Meaning | Values |
|-----------|---------|--------|
| `class` | Quality rating | `FA`, `GA`, `B`, `C`, `Start`, `Stub`, `List`, `NA` |
| `importance` | Priority within project | `Top`, `High`, `Mid`, `Low`, `NA` |
| Work group flags | Task force membership | Varies by project (e.g., `s&a-work-group`) |

### Checking Programmatically

```python
import requests

def get_wikiproject_banners(title):
    """Fetch WikiProject banner templates from a talk page."""
    headers = {'User-Agent': 'MyBot/1.0 (user@example.com)'}
    # Get the talk page wikitext
    params = {
        'action': 'parse', 'page': f'Talk:{title}',
        'prop': 'wikitext', 'format': 'json',
    }
    resp = requests.get(
        'https://en.wikipedia.org/w/api.php',
        params=params, headers=headers, timeout=30
    )
    resp.raise_for_status()
    wikitext = resp.json()['parse']['wikitext']['*']
    
    # Extract WikiProject templates
    import re
    projects = []
    for match in re.finditer(r'\{\{(WikiProject[^}|]+)\}\}', wikitext):
        banner = match.group(1)
        # Parse class and importance
        class_match = re.search(r'\|class=(\w+)', banner)
        imp_match = re.search(r'\|importance=(\w+)', banner)
        name_match = re.match(r'WikiProject[_ ](\w+)', banner)
        if name_match:
            projects.append({
                'project': name_match.group(1),
                'class': class_match.group(1) if class_match else None,
                'importance': imp_match.group(1) if imp_match else None,
            })
    return projects


# Example
for p in get_wikiproject_banners('Albert Einstein'):
    print(f"{p['project']}: {p['class']} / {p['importance']}")
```

### Check if a Project Exists

```python
def has_project(project_name):
    """Check if a WikiProject page exists."""
    headers = {'User-Agent': 'MyBot/1.0 (user@example.com)'}
    params = {
        'action': 'query',
        'titles': f'Wikipedia:WikiProject_{project_name}',
        'format': 'json',
    }
    resp = requests.get(
        'https://en.wikipedia.org/w/api.php',
        params=params, headers=headers, timeout=10
    )
    pages = resp.json()['query']['pages']
    return '-1' not in pages  # '-1' means page doesn't exist


# Check common projects
for project in ['Physics', 'Medicine', 'Chemistry', 'Mathematics']:
    exists = has_project(project)
    print(f"WikiProject {project}: {'✓ exists' if exists else '✗ not found'}")
```

---

## SOP: Finding High-Impact Work

### Most Active WikiProjects

Projects with large assessment tables and frequent edits signal active
communities. To gauge activity:

1. **Check the Assessment table** — a large table with recent updates indicates
   active assessment
2. **Check the Popular_pages page** — if it exists and is current, the project
   opted into automated tooling
3. **Check Recent Changes** — search for recent edits tagged with the project's
   banner template

### Finding Top-Priority Work

The highest-ROI improvement targets for any project:

1. **Top/High importance + Stub/Start quality** — these are the most-read
   articles in the worst shape. Prioritize them.
2. **Popular pages with low quality** — cross-reference the Popular_pages table
   with the Assessment table to find widely-read articles that need improvement
3. **Unassessed articles** — pages that haven't been rated at all. Assess them
   first before any other action.

### Using the Database for Bulk Analysis

For deep analysis, the `page_assessments` table provides programmatic access.
See the **[wikimedia-page-assessment](../wikimedia-page-assessment/SKILL.md)**
skill for SQL queries, schema documentation, and pre-built reports.

---

## SOP: Task Forces and Work Groups

Large WikiProjects often have **task forces** (or work groups) — sub-projects
focused on a narrower topic within the parent project.

Examples:
- `WikiProject Physics` → `Task Force: Biographies`, `Task Force: Relativity`
- `WikiProject Medicine` → `Task Force: Cardiology`, `Task Force: Pharmacology`

Task forces are listed on the parent project's main page, typically in a
sidebar or infobox. The naming convention is:
```
Wikipedia:WikiProject <Parent>/<Task Force>
```

---

## Guardrails

### ❌ Don't Assume All Projects Are Active
Many WikiProjects are dormant. Check the `/Assessment` subpage — if it exists
and has recent data, the project is likely active. If not, the project may be
defunct.

### ❌ Don't Create New WikiProjects Lightly
Creating a new WikiProject requires significant community buy-in. Propose at
`Wikipedia:WikiProject_Council/Proposals` first. Most topic areas are already
covered by existing projects or task forces.

### ❌ Don't Edit Assessment Tables Manually
Assessment data is generated by bots from talk page banners. Don't edit the
`/Assessment` subpage directly — update the banner on the article's talk page
instead.

### ❌ Don't Confuse WikiProjects with Portals
WikiProjects are workspaces for editors. Portals (`Portal:`) are reader-facing
entry points to a topic. They are different namespaces with different purposes.

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent and API patterns for WikiProject queries |
| **[wikipedia-page-anatomy](../wikipedia-page-anatomy/SKILL.md)** | Article structure — where WikiProject banners appear on talk pages |
| **[wikipedia-talk-page](../wikipedia-talk-page/SKILL.md)** | Talk pages — WikiProject banners are placed here |
| **[wikimedia-page-assessment](../wikimedia-page-assessment/SKILL.md)** | SQL queries for page_assessments table — bulk analysis of project data |
| **[wikimedia-pageviews](../wikimedia-pageviews/SKILL.md)** | Pageview data — Popular_pages combines views with assessments |
| **[wikipedia-categories](../wikipedia-categories/SKILL.md)** | Category system — WikiProjects often maintain topic-specific categories |

---

## Tooling

### 🔧 List WikiProjects (`scripts/list-wikiprojects.sh`)

List active WikiProjects by category:

```bash
./scripts/list-wikiprojects.sh          # All WikiProjects
./scripts/list-wikiprojects.sh active   # Active only
./scripts/list-wikiprojects.sh science  # Science category
```

### 🔧 Check Project (`scripts/check-project.sh`)

Check whether a WikiProject exists and show its metadata:

```bash
./scripts/check-project.sh Physics
./scripts/check-project.sh "United States History"
```

### 🐍 WikiProject Discovery (`assets/discover-wikiprojects.py`)

Python tool for discovering WikiProjects by topic:

```python
from assets.discover_wikiprojects import find_project, list_active

# Find the most relevant project for a topic
project = find_project("quantum physics")
print(project)  # → WikiProject Physics

# List all active projects
active = list_active()
print(f"{len(active)} active WikiProjects")
```

### 🐍 Banner Parser (`assets/banner-parser.py`)

Parse WikiProject banners from talk pages:

```python
from assets.banner_parser import parse_banners

banners = parse_banners("Albert Einstein")
# → [{'project': 'Physics', 'class': 'B', 'importance': 'Top'}, ...]
```

### 📚 WikiProject Reference (`references/wikiproject-directory.md`)

Reference guide covering:
- Complete list of major active WikiProjects by topic area
- Common banner parameters and their meanings
- Subpage naming conventions
- Task force and work group patterns
- Bot-maintained pages and their update schedules
