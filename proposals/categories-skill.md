# Proposal: Categories Skill

## Overview

A skill for understanding and working with Wikipedia's category system — how
categories form trees, what makes a valid category, how to assign them to
articles, and how to query them programmatically.

## Why This Skill

Categories are one of the three main navigation systems on Wikipedia alongside
infoboxes and navboxes, and they're the backbone of topic discovery. Despite
being used on almost every page, the current coverage is split thin:

- **`wikipedia-page-anatomy`** has ~20 lines on categories — how to query via
  `prop=categories`, hidden categories, and the Wikipedia-vs-Commons distinction.
  That's it.
- **`pywikibot`** covers the Category object model and generators (`cat.articles()`,
  `cat.subcategories()`, `-cat:`, `-catr:`) and the `category_redirect` script.
  Useful but Pywikibot-specific.

Neither skill covers the *rules* — what makes a valid category, the
defining/verifiable/neutral tests, topic vs. set categories, eponymous
categories, sort keys, overcategorization, category creation workflow, or the
Categories for Discussion process. An agent trying to categorize an article or
evaluate a category structure has to read policy pages directly.

A dedicated skill fills this gap cleanly: it's the policy layer that sits
between the raw API (page-anatomy) and the bulk tooling (pywikibot).

## What It Would Look Like

```
wikipedia-categories/
├── SKILL.md
├── scripts/
│   └── category-tree.sh         # Explore a category hierarchy from CLI
├── references/
│   ├── overcategorization.md    # Condensed rules from WP:OC and WP:NONDEFINING
│   └── naming-conventions.md    # Topic vs set, disambiguation, parentheticals
└── assets/
    ├── category-inspector.py    # Fetch all categories for a page with metadata
    └── category-intersect.py    # Find articles at the intersection of two categories
```

## Proposed SKILL.md Outline

### 1. How Categories Work (the mechanics)

Brief, assumes the agent may have read `page-anatomy` but shouldn't need to.

- Categories are a namespace (`Category:`) — pages in Category namespace are
  themselves categories
- Adding `[[Category:Name]]` to a page adds it to that category
- Categories form a directed acyclic graph (tree), not a tag cloud
- Category pages display: subcategories → pages → files, each sorted by sort
  key, paginated at 200 items
- Category redirects (`{{Category redirect|Target}}`) — soft redirects, not
  `#REDIRECT`

### 2. The Rules: What Makes a Valid Category

This is the core value of the skill — an agent needs to be able to evaluate
whether a category is valid or whether adding a page to a category is correct.

**The three tests** (from WP:CATEGORY):

| Test | Rule | Example fail |
|---|---|---|
| **Verifiable** | Article content must clearly justify the category | Adding "Category:Famous people" with no indication of fame |
| **Neutral** | Categories must be neutral, not judgmental | "Category:Criminals" for someone not convicted |
| **Defining** | Only characteristics that reliable sources consistently mention | "Category:People with blue eyes" (trivial) vs "Category:Italian painters" (defining) |

**Topic vs. Set categories:**

| Type | Name form | Contains | Example |
|---|---|---|---|
| Topic | Singular | Everything related to the topic | `Category:France` (articles *about* France) |
| Set | Plural | Things that *are* the class | `Category:Cities in France` (articles about specific cities) |

**Eponymous categories** — the category named after the article's topic
(e.g. `Category:Albert Einstein`). Rules: only create if enough related pages
exist, don't duplicate the article's own parent categories onto the category.

**What NOT to create** (condensed from WP:Overcategorization):
- Non-defining characteristics (trivial, subjective, arbitrary cutoffs)
- Performers by role/venue/production
- People by opinion, association, or shared name
- Narrow intersections with few members
- Overlapping categories with nearly identical scope

### 3. Assigning Categories to Articles

- Place categories at the end of wikitext, before stub templates (MOS:CATORDER)
- Use the **most specific** category, not the parent AND the child
- Normally 3–8 categories per article
- Eponymous category should appear first among the categories
- Sort keys with `[[Category:Name|Sortkey]]` and `{{DEFAULTSORT:key}}`

**DEFAULTSORT conventions:**
- Biographies: `{{DEFAULTSORT:LastName, FirstName}}`
- Works: `{{DEFAULTSORT:Title, The}}` or `{{DEFAULTSORT:Title (film), The}}`
- Institutions: trailing space sorts before letters
- Lists: strip "List of" prefix in the sort key

**Hidden categories** — `__HIDDENCAT__` or `{{Hidden category}}`, used for
maintenance tracking (e.g., `Category:Articles with unsourced statements`).
Not shown to readers unless they opt in via preferences.

### 4. Finding and Querying Categories

**For a given article** — what categories does it belong to?

```
prop=categories&titles=Albert_Einstein
  → returns categories, sort keys, hidden status
  → use clshow=!hidden to filter
```

**For a given category** — what's in it?

```
list=categorymembers&cmtitle=Category:Physics
  → cmtype=page|subcat|file to filter
  → cmprop=title|sortkey|timestamp|ids
  → paginated at 500, use cmcontinue for next page
  → cmnamespace to restrict to a specific namespace
```

**Category tree navigation:**

```
action=categorytree&category=Physics&options={mode:"categories",depth:3}
  → Subtree of subcategories only
  → mode: "categories" (default), "pages", "all", "parents"
```

**Special pages:**
- `Special:Categories` — list of all categories with member counts
- `Special:CategoryTree` — interactive tree browser
- `incategory:"Foo"` search operator

**PetScan** — external tool for category intersection, namespace filtering,
and template-based queries. API at `https://petscan.wmflabs.org/`.

Use cases:
```
"Find all FA-class articles in Category:Physics"
  → PetScan: category=Physics, template=WikiProject Physics, quality=FA

"Find all pages in Category:Physics but not in any of its subcategories"
  → categorymembers with cmtype=page, filter manually
```

### 5. Category Maintenance

- **Creating a new category:** Put `[[Category:Parent]]` on the category page,
  add `{{Category main article|Article}}` if it has a main article, consider a
  `{{Category TOC}}` for large categories
- **Renaming/moving:** Use the CfD process, leave behind `{{Category redirect}}`
- **Populating via template:** Use `<includeonly>[[Category:Name]]</includeonly>`
  in templates for maintenance categories (with caveats about job queue delay)
- **Overpopulated categories:** Diffuse into subcategories when >200 members
- **Category description:** Should state clear inclusion criteria, can use
  `{{Set category}}` to mark set categories explicitly

### 6. API Reference (compact)

A one-page quick reference for the three main query patterns:

```
# What categories does page X belong to?
GET https://en.wikipedia.org/w/api.php?action=query&prop=categories&titles=X&format=json

# What pages are in category Y?
GET https://en.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:Y&format=json

# What subcategories does category Z have (recursive)?
GET https://en.wikipedia.org/w/api.php?action=categorytree&category=Z&options={"mode":"categories","depth":3}
```

### Optional: Category intersection via PetScan

```
https://petscan.wmflabs.org/?language=en&project=wikipedia&categories=Foo|Bar&interface_language=en
```

## Scope Guardrails (what this skill will NOT cover)

Decisions to keep the skill focused and avoid bloat:

| Will NOT cover | Reason | Falls to |
|---|---|---|
| Pywikibot category generators | Already in pywikibot skill | `pywikibot` |
| Infobox vs category distinction | Already in page-anatomy | `wikipedia-page-anatomy` |
| Commons categories (organizing media files) | Entirely different system | `wikimedia-commons` |
| HotCat gadget usage | Browser UI, not agent-relevant | Reference only |
| Full WP:CFD process documentation | Too deep; reference link is enough | WP:CFD |
| Wikidata category items (QIDs for categories) | Out of scope unless queried | `wikidata` |
| Stub category sorting | Niche, well-covered by WP:SS | Wikipedia policy |

## Size Estimate

Target: **400–600 lines** in SKILL.md (comparable to `wikimedia-diffs` or
`wikipedia-edit-history`), plus:

- `scripts/category-tree.sh` (~60 lines)
- `assets/category-inspector.py` (~120 lines)
- `assets/category-intersect.py` (~100 lines)
- `references/overcategorization.md` (~80 lines)
- `references/naming-conventions.md` (~60 lines)

Total: roughly 3/4 the size of the largest skills (wikidata, pywikibot),
intentionally scoped to stay lean.

## Downsides & Risks

| Risk | Mitigation |
|---|---|
| **Overlap with page-anatomy** could confuse an agent about which skill to load | Make the categories SKILL.md's description explicit: *"Use when you need to evaluate, assign, or query Wikipedia categories — not for general page structure (see wikipedia-page-anatomy)"* |
| **WP:Overcategorization is huge** — 20+ sub-rules | Condense to a reference doc, give the agent a decision tree ("check these 6 things") instead of full text |
| **Category rules change** (CfD creates new precedent) | Keep overcategorization reference as the point of truth; link to live WP:OC page as the canonical source |
| **PetScan API changes** | Version the PetScan URL example; the web UI is more stable than the raw API |
| **Too niche** — categories are everywhere but an agent rarely needs deep category policy | The 80/20 is the three tests (V/N/D), sort keys, and `list=categorymembers`. Those three things justify the skill. The rest is progressive disclosure via references. |

## Success Criteria

An agent using this skill should be able to:

1. Evaluate whether a proposed category for an article is valid (passes V/N/D)
2. Add categories to an article with correct sort keys and DEFAULTSORT
3. Query all pages in a category hierarchy via the Action API
4. Determine whether a category should be topic or set (singular vs plural)
5. Identify overcategorization violations and suggest alternatives
6. Find the intersection of two categories (via PetScan or manual API chaining)
7. Inspect an article's existing categories and flag any that violate policy
