---
name: wikipedia-categories
description: Understand and work with Wikipedia's category system — category trees, the three tests for valid categories (Verifiable/Neutral/Defining), topic vs set categories, sort keys and DEFAULTSORT, querying via API, overcategorization rules, and category maintenance workflows
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access, wikipedia-page-anatomy]
skill_discovery_hints:
  - keywords: ["category", "categorization", "category tree", "WP:CATDEF", "WP:CATV"]
  - keywords: ["sort key", "DEFAULTSORT", "hidden category", "category redirect", "PetScan"]
last_verified: 2026-06-10
---

> ⚠️ **User-Agent required:** The API examples below hit Wikimedia endpoints. All requests must include a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.
>
> 📖 **Prerequisites:** For general page structure (infoboxes, templates, navboxes), see **[wikipedia-page-anatomy](../wikipedia-page-anatomy/SKILL.md)**. For bulk Pywikibot category operations, see **[pywikibot](../pywikibot/SKILL.md)**. This skill covers the **policy rules and query patterns** that sit between those two.

---

## SOP: How Categories Work

Categories are a **namespace** (`Category:`) in MediaWiki. Adding `[[Category:Name]]` to a page's wikitext adds it to that category. Every category has a **category page** that is itself a page in the Category namespace.

### The Category Tree

Categories form a **directed acyclic graph** (a tree, not a tag cloud). Each category page lists `[[Category:ParentCategory]]` to link it upward:

```
Category:Science
  └─ Category:Physics
       ├─ Category:Physicists
       │    ├─ Albert Einstein (article)
       │    ├─ Category:American physicists
       │    └─ ...
       └─ Category:Physical phenomena
            └─ ...
```

**Key rule:** A category is a *container* in a hierarchy, not an arbitrary label. Do not add categories as if they are tags.

### What a Category Page Displays

A category page shows three groups, in this order:

1. **Subcategories** — other categories in this category
2. **Pages** — articles and other pages (excluding subcategories and files)
3. **Files** — images and other media

Each group is **paginated at 200 items**. Use the API for more.

### Category Redirects

A category redirect uses `{{Category redirect|Target}}` — this is **not** a `#REDIRECT` wikitext redirect. It soft-redirects: any page categorized in the old category appears as categorized in the target instead.

```wikitext
{{Category redirect|Physics}}
```

### Hidden Categories

A category marked with `__HIDDENCAT__` or `{{Hidden category}}` does not appear in the visible category bar on articles. Used for maintenance tracking (e.g., `Category:Articles with unsourced statements`). Hidden categories are shown to logged-in users who enable "Show hidden categories" in preferences.

Detect via API:

```
action=query&prop=categories&titles=Albert_Einstein&clshow=hidden&format=json
```

### Wikipedia vs. Commons Categories

These are **independent systems**. Wikipedia categories organize articles; Commons categories organize media files. A Wikipedia article may link to a Commons category via `{{Commons category|Name}}`, but the two trees are separate.

---

## SOP: The Three Tests for Valid Categories

This is the most important section. Before creating a category or adding a page to one, check all three. If any fails, the category is likely invalid.

### 1. Verifiable (WP:CATV)

It must be clear from **verifiable information in the article** why the page belongs in the category. If the article does not contain information that justifies the category, use `{{Unreferenced category}}` or remove the category.

**Check:** Can a reader see, from the article text, why this article is in this category?

### 2. Neutral (WP:CATPOV)

Categories appear on article pages without annotations or citations. They must be **uncontroversial**. If a category's topic is likely to spark controversy, use a list article instead (which can be annotated and referenced).

**Check:** Would a reasonable person disagree that this article belongs here?

**Examples of non-neutral categories:**
- `Category:Criminals` for someone not convicted of a crime
- `Category:Controversial politicians` (subjective judgment)
- `Category:Failed companies` ("failed" is a subjective label)

### 3. Defining (WP:CATDEF)

A **defining characteristic** is one that reliable sources *commonly* and *consistently* refer to when describing the topic. Nationality, occupation, genre, geographic location — these are typically defining. Eye color, favorite food, zodiac sign — these are typically trivial.

**Check:** Would reliable sources consistently describe the topic using this characteristic? Would it be appropriate to mention in the lead section?

**Decision flow:**

```
Is the characteristic mentioned in reliable sources?
  ├─ No  → ❌ Not verifiable, do not categorize
  └─ Yes → Is it central to how sources describe the topic?
       ├─ Yes → ✅ Defining — likely valid category
       └─ No  → Is it completely trivial (eye color, favorite food)?
            ├─ Yes → ❌ Trivial, do not categorize (WP:TRIVIALCAT)
            └─ No  → May be acceptable as non-defining supplementary category
                      (e.g., "Deaths from sepsis" for a painter)
```

---

## SOP: Topic vs. Set Categories

### Topic Categories (Singular)

Named after the topic itself. Contains articles **about** the topic and its subtopics.

| Name | Example members |
|---|---|
| `Category:France` | France (main article), History of France, Geography of France, French cuisine |
| `Category:Opera` | Opera (main article), History of opera, Opera houses, List of operas |

### Set Categories (Plural)

Named after a class of things. Contains articles that **are** members of that class.

| Name | Example members |
|---|---|
| `Category:Cities in France` | Paris, Lyon, Marseille (each *is a* city in France) |
| `Category:Operas` | The Magic Flute, Carmen, La Traviata (each *is an* opera) |

**Important:** Some topics have both a topic category (singular) and a set category (plural) with similar names. Be careful which one to use when categorizing an article.

### Eponymous Categories

An **eponymous category** is named after its main article (e.g., `Category:Albert Einstein` for the article Albert Einstein).

Rules:
- Only create if enough directly related articles or subcategories exist
- The eponymous category should appear **first** in the article's category list
- The eponymous category should have **only the article's categories that are relevant to the category's content** — do NOT copy all of the article's categories onto the category page
- The article itself is placed in the eponymous category (yes, it categorizes itself)

---

## SOP: Assigning Categories to Articles

### Placement

Per MOS:CATEGORY and MOS:ORDER, categories go at the **end of the wikitext**, before any stub templates:

```wikitext
== References ==
{{reflist}}

[[Category:1879 births]]
[[Category:People from Ulm]]
{{Germany-scientist-stub}}
```

### The "Most Specific" Rule

Place articles in the **most specific** category that applies, not both the parent and the child.

| ❌ Wrong | ✅ Correct |
|---|---|
| Albert Einstein in both `Category:Physicists` AND `Category:German physicists` | Albert Einstein in `Category:German physicists` only |
| Paris in both `Category:Cities in France` AND `Category:Capitals in Europe` | Paris in `Category:Capitals in Europe` (more specific) |

### How Many Categories?

Normally **3–8 categories per article**. More than 10 is unusual.

### Sort Keys

Sort keys control where the page appears in the category listing:

```wikitext
[[Category:Category name|Sort key]]
```

The sort key is **not visible** to readers — it only affects ordering.

**Common conventions:**

| Article type | Sort key | Example |
|---|---|---|
| Biography | `{{DEFAULTSORT:LastName, FirstName}}` | `{{DEFAULTSORT:Einstein, Albert}}` |
| Work (book, film, song) | `{{DEFAULTSORT:Title, The}}` | `{{DEFAULTSORT:Matrix, The}}` |
| Institution | Trailing space sorts before letters | `[[Category:MIT| ]]` |
| List | Strip "List of" prefix | `[[Category:Lists of countries|Rugby union]]` |

Use `{{DEFAULTSORT:key}}` to set a **default** sort key for all categories on the page. Individual `[[Category:Name|key]]` overrides the default for that specific category.

```wikitext
{{DEFAULTSORT:Einstein, Albert}}
[[Category:1879 births]]             ← sorted as "Einstein, Albert"
[[Category:People from Ulm]]         ← sorted as "Einstein, Albert"
[[Category:Swiss physicists]]        ← sorted as "Einstein, Albert"
[[Category:20th-century physicists]] ← sorted as "Einstein, Albert"
```

**DEFAULTSORT conflicts:** If multiple `{{DEFAULTSORT}}` tags appear on the rendered page, the *last one wins* — but they are tracked in `Category:Pages with DEFAULTSORT conflicts`. A DEFAULTSORT from a template is overridden by any DEFAULTSORT later on the page.

### Category Descriptions

A category page should, at minimum, make clear what belongs in it. For ambiguous or large categories, add a description:

```wikitext
{{Category main article|Physicist}}

This category is for articles about notable physicists, including 
subcategories for physicists by nationality, century, and specialization.

[[Category:Science]]
[[Category:People by occupation]]
```

Useful templates:
- `{{Category main article|Article}}` — links to the main article
- `{{Category see also|Other category}}` — links to related categories
- `{{Set category}}` — marks a category as a set category (not a topic category)
- `{{Category TOC}}` — adds A–Z table of contents for large categories
- `{{Large category TOC}}` — 5-band per-letter TOC for very large categories
- `{{Automatic category TOC}}` — auto-selects TOC based on member count

---

## SOP: Finding and Querying Categories

### What Categories Does an Article Belong To?

```
GET https://en.wikipedia.org/w/api.php?action=query&prop=categories&titles=Albert_Einstein&format=json
```

Key parameters:

| Parameter | Purpose |
|---|---|
| `cllimit` | Max results (default 10, max 500) |
| `clshow=!hidden` | Visible categories only |
| `clshow=hidden` | Hidden categories only |
| `clprop=sortkey` | Include sort key information |

### What's in a Category?

Use `list=categorymembers`:

```
GET https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Physics&format=json
```

Key parameters:

| Parameter | Purpose |
|---|---|
| `cmtitle` | Category name (required, must include `Category:` prefix) |
| `cmtype=page` | Articles only |
| `cmtype=subcat` | Subcategories only |
| `cmtype=file` | Files only (default: all three) |
| `cmtype=page|subcat` | Articles and subcategories (no files) |
| `cmlimit` | Max results (default 10, max 500) |
| `cmprop=title` | Page title only |
| `cmprop=title|sortkey|timestamp|ids` | Full metadata |
| `cmnamespace=0` | Main namespace only |
| `cmcontinue` | Pagination token for next page |

**Pagination:** Results include a `cmcontinue` token when there are more pages. Append it to get the next batch:

```
GET https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Physics&cmlimit=500&cmcontinue=page|1234|NextPageTitle&format=json
```

### Category Hierarchy (Recursive Tree)

Use the CategoryTree extension:

```
GET https://en.wikipedia.org/w/api.php?action=categorytree&category=Physics&format=json
```

The response is in `$.categorytree["*"]` and contains **HTML** (not JSON-structured data).
The HTML uses `<div>` elements with these classes:

| Class | Purpose |
|---|---|
| `CategoryTreeSection` | Wraps one category and its children |
| `CategoryTreeItem` | The category name/link itself |
| `CategoryTreeChildren` | Wraps nested subcategories (may be collapsed) |
| `CategoryTreeBullet` | Expand/collapse toggle icon |

> ⚠️ **Parsing gotcha:** This is `<div>`-based HTML, not `<li>`/`<ul>` lists.
> Nested sections are sibling `<div class="CategoryTreeSection">` elements
> inside `<div class="CategoryTreeChildren">`. Collapsed children use
> `style="display:none"` on the children div. Any parser must track
> **all** `<div>` tags for correct nesting — omitting unrelated divs
> (like `CategoryTreeItem`) will break `</div>` balancing.
> See `scripts/category-tree.sh` for a working parser.

> **Trade-off vs. `list=categorymembers`:** `action=categorytree` makes a single
> API call regardless of depth (fast, one round-trip) but returns pre-rendered
> HTML rather than structured JSON. The HTML classes (`CategoryTreeSection`,
> `CategoryTreeItem`, etc.) are CSS hooks for the extension's own UI, not a
> stable public API — they could change across MediaWiki versions.
>
> For more data-rich access (page IDs, namespaces, sort keys, timestamps),
> use `list=categorymembers` with `cmtype=subcat` recursively. This returns
> clean JSON at the cost of N sequential API calls for depth N.
>
> | Approach | Calls | Response format | Data per node |
> |---|---|---|---|
> | `action=categorytree` | 1 | Pre-rendered HTML | Link text only |
> | `list=categorymembers` (recursive) | N | Structured JSON | ID, title, ns, sortkey, timestamp |

The `options` parameter is a JSON object:

| Option | Values | Default | Description |
|---|---|---|---|
| `mode` | `"categories"`, `"pages"`, `"all"`, `"parents"` | `"categories"` | What to show: just subcats, pages+subcats, everything, or parent categories |
| `depth` | integer | `1` | How many levels deep to recurse |
| `namespaces` | array of integers | `[]` | Restrict to specific namespaces (mode must not be `categories`) |

Examples:

```
# Subcategory tree, 3 levels deep
action=categorytree&category=Physics&options={"mode":"categories","depth":3}

# All pages in the tree (articles + subcategories), 2 levels deep
action=categorytree&category=Physics&options={"mode":"pages","depth":2}

# Parent categories of Physics (go upward, not downward)
action=categorytree&category=Physics&options={"mode":"parents"}
```

### Search Operator: `incategory:`

The search box supports `incategory:"CategoryName"` to find articles in a specific category. Pipe-separated categories are union queries:

```
incategory:"Suspension bridges|Bridges in New York City"
```

This returns all articles in EITHER category. Note: does **not** include subcategories.

### External Tools

**PetScan** (`https://petscan.wmflabs.org/`) — category intersection and data extraction tool. Useful for:

| Use case | How |
|---|---|
| Find articles in multiple categories simultaneously | Set multiple category sources with intersection mode |
| Find pages in one category but NOT in another | Set negative category filter |
| Filter by template presence | Add a template filter (e.g., only pages with `{{WikiProject Physics}}`) |
| Filter by namespace, page size, redirect status | Built-in filters |
| Export as CSV, JSON, or Wiki table | Output format selector |

Web UI: `https://petscan.wmflabs.org/`

### Special Pages

| Page | Purpose |
|---|---|
| `Special:Categories` | Alphabetical list of all categories with member counts |
| `Special:AllPages/Category:` | List all existing category pages (even empty ones) |
| `Special:CategoryTree` | Interactive tree browser |
| `Special:TrackingCategories` | Built-in MediaWiki tracking categories |

---

## SOP: Category Maintenance

### Creating a New Category

1. Add `[[Category:ParentCategory]]` to the category page to place it in the tree
2. Add a category description (see "Category Descriptions" above)
3. Add a TOC template if the category will be large
4. For eponymous categories, add `{{Category main article|ArticleName}}`

### Finding the Right Place in the Tree

Before creating a category, verify one doesn't already exist with the same or overlapping scope:
- Check categories on similar articles
- Search existing category names
- Navigate the parent tree: e.g., for "Mexican painters", check `Category:People by nationality` → `Category:Mexican people` → `Category:Mexican artists` → `Category:Mexican painters`

### Renaming / Moving Categories

Do NOT move categories with a simple `#REDIRECT`. Use **Wikipedia:Categories for discussion** (CFD) for contested renames, which leaves behind a `{{Category redirect}}`:

```wikitext
{{Category redirect|NewCategoryName}}
```

The `category_redirect` template ensures that any page categorized in the old name appears as if categorized in the target. The Pywikibot script `category_redirect` can then fix the underlying category tags.

### Populating Categories via Templates

For maintenance categories (e.g., `Category:Articles with unsourced statements`), use `<includeonly>` tags in a template:

```wikitext
<includeonly>[[Category:Articles with unsourced statements]]</includeonly>
```

**Caveat:** Template-based categorization is delayed — changes only appear after the job queue processes affected pages (can be hours in busy periods). A null edit to a specific page forces immediate recaching.

### Diffusing Overpopulated Categories

When a category exceeds roughly **200 members**, consider diffusing into subcategories:

```
Before:                       After:
Category:Writers (1,200)      Category:Writers
                                ├─ Category:Writers by nationality
                                │    ├─ Category:American writers
                                │    ├─ Category:French writers
                                │    └─ ...
                                └─ Category:Writers by genre
                                     ├─ Category:Novelists
                                     ├─ Category:Poets
                                     └─ ...
```

Diffusion should follow **defining characteristics** — nationality and genre are typical, eye color is not. See the [overcategorization reference](references/overcategorization.md) for what NOT to do.

---

## SOP: Evaluating a Category or Categorization

When asked to evaluate whether a category is valid or whether an article belongs in a category, follow this checklist:

```
□ Verify: Does the article content justify the category?
   (If not → flag as unverifiable)

□ Neutral: Is the category name neutral and uncontroversial?
   (If not → suggest a list article instead)

□ Defining: Is this a characteristic that reliable sources consistently mention?
   (If not → check WP:TRIVIALCAT, flag as non-defining)

□ Specific: Is this the most specific category available?
   (If not → suggest the more specific one, don't double-categorize)

□ Type: Is it the right type (topic=singular, set=plural)?
   (If wrong → suggest correct name form)

□ Overcategorization: Does the category violate any OC rules?
   (Check: subjective, arbitrary, narrow, by opinion, by performance)
```

---

## Comparison: All Category Access Methods

This table covers every way to access category data, from lightweight API calls
through Pywikibot and external tools. Use it to pick the right approach for
your task.

### Quick Decision Guide

| Task | Best method | Why |
|---|---|---|
| Quick CLI tree of subcategories | `action=categorytree` | 1 call, built-in recursion |
| Get all articles in a category with metadata | `list=categorymembers` | Clean JSON, page IDs, sort keys |
| Traverse deep category hierarchy programmatically | Pywikibot `cat.subcategories(recurse=True)` | Handles pagination + recursion automatically |
| Intersection of multiple categories | PetScan | Built-in AND/OR/NOT, filter by template/namespace |
| Category member counts only | `prop=categoryinfo` | 1 call, no pagination needed |
| Find what categories an article belongs to | `prop=categories` | Inverse direction |
| Find all categories matching a prefix | `list=allcategories` | Discover categories by name |
| Bulk edit/move/redirect categories | Pywikibot `category.py` script | Built for mass operations |
| Cross-wiki category analysis | WDQS (SPARQL) | Recursive across all Wikimedia wikis |
| Manual browsing | Special:CategoryTree | Interactive, no coding |

### Detailed Comparison

#### Action API — query modules

| Module | Direction | Returns | Recursive? | Calls for depth N |
|---|---|---|---|---|
| `list=categorymembers` | Category → members | JSON: page IDs, titles, ns, sort keys, timestamp, type | Manual | N |
| `prop=categories` | Article → categories | JSON: category titles, sort keys, hidden status | No | 1 |
| `prop=categoryinfo` | Category → counts | JSON: page count, subcat count, file count, size | No | 1 |
| `list=allcategories` | Whole wiki → categories | JSON: category names, member counts | No | 1 (paginated) |
| `action=categorytree` | Category → tree (HTML) | Pre-rendered HTML with `<div>` elements | Built-in (depth param) | 1 |

**`list=categorymembers` key parameters:**

| Parameter | Purpose |
|---|---|
| `cmtype=page|subcat|file` | Filter by member type |
| `cmnamespace=0` | Filter by namespace |
| `cmprop=title|sortkey|timestamp|ids|type` | What data to return |
| `cmsort=sortkey|timestamp` | Sort order |
| `cmdir=asc|desc` | Sort direction |
| `cmstart` / `cmend` | Timestamp range (requires `cmsort=timestamp`) |
| `cmcontinue` | Pagination token (next 500) |
| `generator=categorymembers` | Use as generator to feed other query props |

**Generator pattern** (fetch members + page content in one call):

```
GET /w/api.php?action=query&generator=categorymembers&gcmtitle=Category:Physics
  &prop=extracts|info&exintro&inprop=url&format=json
```

This is more efficient than fetching members first, then fetching each page's
content separately.

#### Pywikibot

Pywikibot wraps the Action API with automatic pagination, rate limiting, and
recursion. Its page generators are the recommended way to do anything beyond
one-shot API calls.

| Generator | CLI flag | Python method | Recursive? |
|---|---|---|---|
| Pages in a category | `-cat:Physics` | `pagegenerators.CategorizedPageGenerator(cat)` | `recurse=True` |
| Pages including subcategories | `-catr:Physics` | Same with `recurse=True` | Yes (int for depth) |
| Subcategories only | `-subcats:Physics` | `cat.subcategories()` | `recurse=True` |
| Subcategories recursively | `-subcatsr:Physics` | Same with `recurse=True` | Yes (int for depth) |
| All members (pages + subcats + files) | `-cat:Physics` (includes all) | `cat.members()` | `recurse=True` |

**Programmatic usage:**

```python
import pywikibot
from pywikibot import pagegenerators

site = pywikibot.Site("en", "wikipedia")
cat = pywikibot.Category(site, "Physics")

# Member counts
print(cat.categoryinfo)  # {"size": 68, "pages": 22, "files": 0, "subcats": 46}

# Articles (non-recursive)
for page in cat.articles():
    print(page.title())

# Subcategories, 2 levels deep
for subcat in cat.subcategories(recurse=2):
    print(subcat.title())

# All members recursively (pages + subcategories + files)
for member in cat.members(recurse=True):
    print(member.title())
```

**Built-in scripts for category maintenance:**

| Script | Purpose | Example |
|---|---|---|
| `category.py` | Add/remove/move/tidy/clean/tree/listify | `pwb.py category move -from:"Old" -to:"New"` |
| `category_redirect` | Fix redirected categories | `pwb.py category_redirect -cat:"Category:Redirects"` |
| `category_graph` | Visualize hierarchy as DOT/SVG/HTML | `pwb.py category_graph -from Physics -depth 3` |
| `commonscat` | Add `{{commonscat}}` to category pages | `pwb.py commonscat -start:Category:!` |

#### External Tools

| Tool | Best for | How |
|---|---|---|
| **PetScan** | Category intersection + filtering | Web UI at `https://petscan.wmflabs.org/` or URL API |
| **WDQS (SPARQL)** | Cross-wiki recursive category queries | `https://query.wikidata.org/sparql` |
| **Special:CategoryTree** | Interactive manual browsing | Browser-based, expand/collapse |
| **Special:Categories** | Discover all categories on a wiki | Alphabetical with member counts |

**PetScan example URL** — find FA-class articles in Category:Physics:

```
https://petscan.wmflabs.org/?language=en&project=wikipedia&categories=Physics
  &ns[0]=1&interface_language=en&wikidata_item=yes&templates_yes=WikiProject_Physics
```

**WDQS example** — find all subcategories recursively:

```sparql
SELECT ?category ?categoryLabel WHERE {
  wd:Q413 wdt:P910 ?category .                        # Main topic's category
  ?category wdt:P279* ?subcategory .                   # Recursive subcategories
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

#### Trade-off Summary

```
Speed (fewer calls):
  action=categorytree (1)  >  prop=categoryinfo (1)  >  list=categorymembers (N)  >  Pywikibot (N + overhead)

Data richness:
  Pywikibot (full objects)  >  list=categorymembers (IDs + metadata)  >  action=categorytree (link text only)

Ease of use:
  PetScan (web UI)  >  Pywikibot CLI (-catr)  >  Action API direct  >  action=categorytree (needs HTML parser)

Stability:
  list=categorymembers (stable, documented)  >  Pywikibot (stable, wraps API)  >  action=categorytree (unstable HTML)
```

---

## Quick Reference: API Patterns

```
# Categories of an article (visible only):
GET /w/api.php?action=query&prop=categories&titles=Albert_Einstein&clshow=!hidden&format=json

# Categories of an article (all, including hidden):
GET /w/api.php?action=query&prop=categories&titles=Albert_Einstein&format=json

# Members of a category (articles only):
GET /w/api.php?action=query&list=categorymembers&cmtitle=Category:Physics&cmtype=page&format=json

# Members of a category (subcategories only):
GET /w/api.php?action=query&list=categorymembers&cmtitle=Category:Physics&cmtype=subcat&format=json

# Category tree (subcategories, 3 levels):
GET /w/api.php?action=categorytree&category=Physics&options={"mode":"categories","depth":3}&format=json

# Category tree (all pages, 2 levels):
GET /w/api.php?action=categorytree&category=Physics&options={"mode":"pages","depth":2}&format=json

# Category info (member counts):
GET /w/api.php?action=query&prop=categoryinfo&titles=Category:Physics&format=json
```

See `scripts/category-tree.sh` for an interactive CLI explorer, and `assets/` for Python utilities.

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent and API patterns for category queries |
| **[wikipedia-page-anatomy](../wikipedia-page-anatomy/SKILL.md)** | Article structure — categories as page elements |
| **[wikipedia-citations](../wikipedia-citations/SKILL.md)** | Citation-related tracking categories (e.g., Articles with unsourced statements) |
| **[pywikibot](../pywikibot/SKILL.md)** | Bulk category operations via Pywikibot generators |
| **[wikimedia-search-cirrussearch](../wikimedia-search-cirrussearch/SKILL.md)** | `incategory:` and `deepcategory:` search operators |

