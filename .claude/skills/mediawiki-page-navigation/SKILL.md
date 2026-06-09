---
name: mediawiki-page-navigation
description: Build navigation systems in MediaWiki — menu bars, subpage hierarchies, breadcrumbs, tabs, and the template logic that powers them. Covers #titleparts, #ifexist, dynamic sub-navigation loading, menu bars, and page-hierarchy-aware link generation
license: MIT
compatibility: opencode
---

> ⚠️ **User-Agent required:** The API examples below hit Wikimedia endpoints. All requests must include a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.
>
> 📖 **Prerequisites:** For general template syntax, parser functions, and magic words, see **[wikipedia-templates](../wikipedia-templates/SKILL.md)**. For styling navigation elements (menus, tabs, buttons), see **[wikimedia-page-styling](../wikimedia-page-styling/SKILL.md)**. For language-aware navigation links, see **[mediawiki-translate-extension](../mediawiki-translate-extension/SKILL.md)**.

---

## Table of Contents

1. [Navigation Patterns Overview](#navigation-patterns-overview)
2. [Page Hierarchy with Subpages](#page-hierarchy-with-subpages)
3. [The `/Sub` Template Pattern](#the-sub-template-pattern)
4. [Menu Bars](#menu-bars)
5. [Dynamic Sub-Navigation with `#titleparts`](#dynamic-sub-navigation-with-titleparts)
6. [Temporal Navigation (This Year / Next Year)](#temporal-navigation-this-year--next-year)
7. [Breadcrumbs](#breadcrumbs)
8. [Tab Navigation](#tab-navigation)
9. [Highlighting the Current Page](#highlighting-the-current-page)
10. [Table of Contents Control](#table-of-contents-control)
11. [Combined Navigation + Hero Banner Pattern](#combined-navigation--hero-banner-pattern)
12. [Testing and Debugging Navigation](#testing-and-debugging-navigation)
13. [Reference Links](#reference-links)

---

## Navigation Patterns Overview

MediaWiki's subpage feature (`/` in page titles) enables powerful hierarchical navigation patterns. Combined with template logic and parser functions, you can build:

| Pattern | Description | Example |
|---|---|---|
| **Horizontal menu bar** | Top-of-page navigation links | `AvoinGLAM/Main navigation` |
| **Subpage navigation** | Auto-generated links to parent/sibling/child pages | `{{#titleparts: {{FULLPAGENAME}} | 2 }}` |
| **Dynamic sub-nav** | Conditionally loaded sub-menus per page | `/Sub` template pattern |
| **Temporal nav** | Year-based navigation that auto-advances | `{{CURRENTYEAR}}` + `#ifexist` |
| **Breadcrumbs** | Hierarchical "You are here" trail | `AvoinGLAM > Past activities` |
| **Tab navigation** | Horizontal tab bar for sub-pages | Common on Commons |
| **Inline TOC control** | Show/hide table of contents | `__TOC__` / `__NOTOC__` |

### How Navigation Templates Work

A navigation template is typically a **single template** that every page in a project transcludes at the top. It:

1. Generates a **consistent navigation bar** across all project pages
2. Knows what page it's on via `{{FULLPAGENAME}}`, `{{SUBPAGENAME}}`, etc.
3. Highlights the **current active page** in the menu
4. Can load **additional sub-navigation** specific to each page or section
5. Optionally includes a **hero banner** behind the navigation

---

## Page Hierarchy with Subpages

MediaWiki allows hierarchical page organization using the **subpage feature** (forward slash in titles):

```
AvoinGLAM                         ← Parent page
AvoinGLAM/Past activities         ← Child page (subpage)
AvoinGLAM/Past activities/2023    ← Grandchild page (sub-subpage)
```

### Magic Words for Subpage Hierarchy

| Magic Word | Returns | Example |
|---|---|---|
| `{{FULLPAGENAME}}` | Full page title with namespace | `AvoinGLAM/Past activities` |
| `{{FULLPAGENAMEE}}` | URL-encoded full title | `AvoinGLAM/Past_activities` |
| `{{PAGENAME}}` | Page title without namespace | `AvoinGLAM/Past activities` |
| `{{PAGENAMEE}}` | URL-encoded page name | `AvoinGLAM/Past_activities` |
| `{{SUBPAGENAME}}` | Last segment after `/` | `Past activities` |
| `{{NAMESPACE}}` | Namespace name | `(Main)` or `Template` |
| `{{NAMESPACENUMBER}}` | Namespace number | `0` for main |

### Parsing the Hierarchy with `#titleparts`

The `#titleparts` parser function splits a title by `/` and returns specific segments:

```
{{#titleparts: AvoinGLAM/Past activities | 1 }}    → AvoinGLAM
{{#titleparts: AvoinGLAM/Past activities | 2 }}    → AvoinGLAM/Past activities
{{#titleparts: AvoinGLAM/Past activities | -1 }}   → AvoinGLAM  (last segment removed)
{{#titleparts: AvoinGLAM/Past activities | 2 | 2 }} → Past activities
```

**Common pattern — get the project root:**

```wikitext
{{#titleparts: {{FULLPAGENAME}} | 1 }}
```

This extracts the top-level project name from any subpage.

**Pattern — get the parent of the current page:**

```wikitext
{{#titleparts: {{FULLPAGENAME}} | -1 }}
```

This strips the last segment, giving you the parent page.

---

## The `/Sub` Template Pattern

The `/Sub` pattern is a powerful extensibility mechanism. It lets **sub-pages of a project inject additional navigation items** without modifying the main navigation template.

### How It Works

The main navigation template checks if a template named `Project/Sub` exists and transcludes it if so:

```wikitext
{{#ifexist: Template:{{#titleparts: {{FULLPAGENAME}} | 2 }}/Sub
| {{ Template:{{#titleparts: {{FULLPAGENAME}} | 2 }}/Sub }}
}}
```

For a page at `AvoinGLAM/Past activities`, this evaluates to:

```wikitext
{{#ifexist: Template:AvoinGLAM/Sub
| {{ Template:AvoinGLAM/Sub }}
}}
```

### Example `/Sub` Template

```wikitext
<!-- Template:AvoinGLAM/Past_activities/Sub -->
* [[Special:MyLanguage/AvoinGLAM/Past activities/2023|2023]]
* [[Special:MyLanguage/AvoinGLAM/Past activities/2022|2022]]
* [[Special:MyLanguage/AvoinGLAM/Past activities/2021|2021]]
```

This would add year-specific links to the navigation bar only when viewing pages under `AvoinGLAM/Past activities/`.

### Context-Aware Sub Navigation

You can also check for a **sub-navigation specific to the current menu section**:

```wikitext
{{#ifexist: Template:Wiki Loves Living Heritage/{{{1}}}/Sub
| {{Template:Wiki Loves Living Heritage/{{{1}}}/Sub}}
}}
```

Where `{{{1}}}` is a parameter passed to the navigation template indicating which menu section is active.

### Full Pattern from AvoinGLAM

```wikitext
{{#ifexist: Template:{{#titleparts: {{FULLPAGENAME}} | 2 }}/Sub
| {{ Template:{{#titleparts: {{FULLPAGENAME}} | 2 }}/Sub}}
}}{{#ifexist: Template:Wiki Loves Living Heritage/{{{1}}}/Sub
| {{Template:Wiki Loves Living Heritage/{{{1}}}/Sub}}
}}
```

This loads **two levels** of sub-navigation:
1. Project-level sub-nav (`AvoinGLAM/Sub`, `AvoinGLAM/Past activities/Sub`, etc.)
2. Section-level sub-nav (Wiki Loves Living Heritage sub-menus)

---

## Menu Bars

### Basic Menu Bar Structure (Wikitext)

A horizontal menu is simply a list with a CSS class:

```wikitext
<div class="menu">
* [[Special:MyLanguage/Project|Home]]
* [[Special:MyLanguage/Project/This year|This year]]
* [[Special:MyLanguage/Project/Past activities|Past activities]]
* [[Special:MyLanguage/Project/Community|Community]]
</div>
```

The CSS (loaded via TemplateStyles) converts the bullet list into a horizontal flexbox (see `wikimedia-page-styling` skill).

### Menu with Dynamic Items

```wikitext
<div class="menu">
* [[Special:MyLanguage/AvoinGLAM|AvoinGLAM]]
* [[Special:MyLanguage/AvoinGLAM/{{CURRENTYEAR}}|This year]]
{{#ifexist: AvoinGLAM/{{#expr: {{CURRENTYEAR}} + 1 }}
| * [[Special:MyLanguage/AvoinGLAM/{{#expr: {{CURRENTYEAR}} + 1 }}|Next year]]
}}
* [[Special:MyLanguage/AvoinGLAM/Past activities|Past activities]]
</div>
```

### Menu with Active Page Highlighting

MediaWiki automatically adds the `mw-selflink` class to links pointing to the current page:

```css
.menu a.mw-selflink {
    color: #0E65C0;  /* Highlight color for active page */
}
```

### Using `Special:MyLanguage/` for i18n Menus

`Special:MyLanguage/` is a redirect that follows the user's interface language preference:

```wikitext
* [[Special:MyLanguage/AvoinGLAM|AvoinGLAM]]
* [[Special:MyLanguage/AvoinGLAM/Past activities|Past activities]]
```

This ensures users are directed to the translated version of the page if it exists.

### Nested Menu Items (Sub-Menus)

Sub-menus can be handled via the `/Sub` template pattern or by nesting lists in the menu itself:

```wikitext
<div class="menu">
* Main section
** [[Project/Subpage 1|Item 1]]
** [[Project/Subpage 2|Item 2]]
</div>
```

The CSS can style nested lists as dropdowns or expandable sub-menus.

### Menu Parameters in Templates

A navigation template can accept parameters to customize the menu:

```wikitext
{{Project/Navigation
  |menu     = activities    ← Which menu section is active
  |image    = File:hero.jpg
  |subtitle = Past events
}}
```

---

## Dynamic Sub-Navigation with `#titleparts`

### How `#titleparts` Works on the Current Page

```wikitext
{{FULLPAGENAME}}                              → "AvoinGLAM/Past activities"
{{#titleparts: {{FULLPAGENAME}} | 1 }}         → "AvoinGLAM"           (root)
{{#titleparts: {{FULLPAGENAME}} | -1 }}        → "AvoinGLAM"           (parent, stripped last segment)
{{#titleparts: {{FULLPAGENAME}} | 2 | 2 }}     → "Past activities"     (second segment)
```

### Pattern: Build a Link to the Parent Page

```wikitext
[[{{#titleparts: {{FULLPAGENAME}} | -1 }}|Up to parent]]
```

### Pattern: Build Links to Sibling Pages

```wikitext
[[{{#titleparts: {{FULLPAGENAME}} | -1 }}/Page1|Page 1]]
[[{{#titleparts: {{FULLPAGENAME}} | -1 }}/Page2|Page 2]]
```

### Pattern: Detect and Link to Sub-Pages

```wikitext
{{#ifexist: {{FULLPAGENAME}}/Detail
| [[{{FULLPAGENAME}}/Detail|Detailed view]]
}}
```

### Pattern: Recursive Parent Link Chain (Breadcrumbs)

```wikitext
{{#if: {{#titleparts: {{FULLPAGENAME}} | -1 }}  ← Only show if there IS a parent
| [[{{#titleparts: {{FULLPAGENAME}} | -1 }}|← Back to {{#titleparts: {{FULLPAGENAME}} | -1 }}]]
}}
```

---

## Temporal Navigation (This Year / Next Year)

A common pattern on Meta project pages is **auto-advancing year-based navigation**.

### This Year Link

```wikitext
[[Special:MyLanguage/AvoinGLAM/{{CURRENTYEAR}}|This year]]
```

This always points to the current year's subpage.

### Next Year Link (Conditional)

```wikitext
{{#ifexist: AvoinGLAM/{{#expr: {{CURRENTYEAR}} + 1 }}
| * [[Special:MyLanguage/AvoinGLAM/{{#expr: {{CURRENTYEAR}} + 1 }}|Next year]]
}}
```

This only shows a "Next year" link if that page already exists (planning ahead).

### Year Range Pattern

For activity indexes spanning multiple years:

```wikitext
{{#ifexist: AvoinGLAM/{{CURRENTYEAR}}
| [[AvoinGLAM/{{CURRENTYEAR}}|{{CURRENTYEAR}}]]
}}{{#ifexist: AvoinGLAM/{{#expr: {{CURRENTYEAR}} - 1 }}
| · [[AvoinGLAM/{{#expr: {{CURRENTYEAR}} - 1 }}|{{#expr: {{CURRENTYEAR}} - 1 }}]]
}}
```

---

## Breadcrumbs

Breadcrumbs show the user's place in the page hierarchy.

### Simple Breadcrumb Template

```wikitext
<!-- Template:Project/Breadcrumb -->
<div class="breadcrumb">
[[{{#titleparts: {{FULLPAGENAME}} | 1 }}|{{#titleparts: {{FULLPAGENAME}} | 1 }}]]
{{#if:{{#titleparts: {{FULLPAGENAME}} | 2 | 2 }}|
  › [[{{#titleparts: {{FULLPAGENAME}} | 2 }}|{{#titleparts: {{FULLPAGENAME}} | 2 | 2 }}]]
}}
{{#if:{{#titleparts: {{FULLPAGENAME}} | 3 | 3 }}|
  › {{#titleparts: {{FULLPAGENAME}} | 3 | 3 }}
}}
</div>
```

For `AvoinGLAM/Past activities/2023`, this renders:

```
AvoinGLAM › Past activities › 2023
```

### CSS for Breadcrumbs

```css
.breadcrumb {
    font-family: "Montserrat", sans-serif;
    font-size: 0.9rem;
    color: #666;
    margin: 0.5em 0;
    padding: 0;
}
.breadcrumb a {
    color: #0E65C0;
    text-decoration: none;
}
```

---

## Tab Navigation

Tab navigation creates a horizontal bar of tabs for switching between sub-pages.

### Wikitext Structure

```wikitext
<div class="tabs">
{{#ifeq: {{SUBPAGENAME}} | Overview
  | <span class="tab active">Overview</span>
  | [[Project/{{BASEPAGENAME}}/Overview|<span class="tab">Overview</span>]]
}}
{{#ifeq: {{SUBPAGENAME}} | Details
  | <span class="tab active">Details</span>
  | [[Project/{{BASEPAGENAME}}/Details|<span class="tab">Details</span>]]
}}
{{#ifeq: {{SUBPAGENAME}} | History
  | <span class="tab active">History</span>
  | [[Project/{{BASEPAGENAME}}/History|<span class="tab">History</span>]]
}}
</div>
```

### CSS for Tabs

```css
.tabs {
    display: flex;
    gap: 0;
    border-bottom: 2px solid #0E65C0;
    margin: 1rem 0;
}

.tab {
    padding: 0.5rem 1.5rem;
    font-family: "Montserrat", sans-serif;
    font-weight: bold;
    color: #666;
    text-decoration: none;
    border-radius: 8px 8px 0 0;
    transition: 0.2s;
}

.tab.active {
    background: #0E65C0;
    color: white;
}

.tab:hover:not(.active) {
    background: #f1f4f6;
}
```

---

## Highlighting the Current Page

MediaWiki automatically adds `mw-selflink` to the link pointing to the current page. This can be styled:

```css
.menu a.mw-selflink {
    color: #0E65C0;
    font-weight: bold;
}
```

For custom navigation not using wiki links, use `#ifeq` to check the page name:

```wikitext
{{#ifeq: {{FULLPAGENAME}} | AvoinGLAM/Past activities
  | <strong>Past activities</strong>
  | [[AvoinGLAM/Past activities|Past activities]]
}}
```

Or check the subpage name:

```wikitext
{{#ifeq: {{SUBPAGENAME}} | Past activities
  | <span class="active">Past activities</span>
  | [[Project/Past activities|Past activities]]
}}
```

---

## Table of Contents Control

### TOC Magic Words

| Word | Effect |
|------|--------|
| `__TOC__` | Insert TOC at this exact position |
| `__NOTOC__` | Hide the TOC entirely |
| `__FORCETOC__` | Force TOC to appear before first heading |

### Toggle TOC via Template Parameter

The AvoinGLAM navigation template lets pages decide whether to show the TOC:

```wikitext
{{#ifeq: {{{TOC|}}}|Show|__TOC__|__NOTOC__}}
```

Usage on the page:

```wikitext
{{Project/Navigation|TOC=Show}}
```

This defaults to hiding the TOC (cleaner look for visually rich pages) but allows individual pages to opt-in.

---

## Combined Navigation + Hero Banner Pattern

The most advanced pattern combines a **hero banner** (full-width image with overlaid text) with a **navigation menu bar** below it. This is what `{{AvoinGLAM/Main navigation}}` does.

### Template Structure

```wikitext
<templatestyles src="Project/style.css" />

{{#tag:div
|<!-- Full-width hero image -->
{{#tag:div
|[[{{{image|File:default.jpg}}}|1500px]]
|class=mainimage
}}
<!-- Title and metadata overlaid on the image -->
<div class="header">
  <div class="bannertitle">{{{title|}}}</div>
  <div class="bannerbody">{{{subtitle|}}}</div>
  <div class="bannertime">{{{startdate|}}} {{{location|}}}</div>
</div>
<!-- Invisible clickable link over the whole banner -->
{{#tag:span|[[File:Pix.gif|link={{{eventpage|}}}]]|class=emptylink}}
|class=banner
}}

<!-- Navigation menu below the banner -->
<div class="menu">
* [[Special:MyLanguage/Project|Home]]
* [[Special:MyLanguage/Project/Past activities|Past activities]]
{{#ifexist: Template:{{#titleparts: {{FULLPAGENAME}} | 2 }}/Sub
| {{Template:{{#titleparts: {{FULLPAGENAME}} | 2 }}/Sub}}
}}
</div>
```

### Parameters for the Combined Template

| Parameter | Purpose | Example |
|---|---|---|
| `image` | Hero background image | `File:banner.jpg` |
| `title` | Large overlay title | `AvoinGLAM` |
| `subtitle` | Smaller subtitle | `Past activities` |
| `startdate` / `enddate` | Date badge display | `2024-05-06` |
| `location` | Event location | `Helsinki` |
| `eventpage` | Link target of the banner | `Project/Event` |
| `class` | Image position class | `top`, `person` |
| `TOC` | Show TOC toggle | `Show` |
| `1` (positional) | Active menu section name | `activities` |

---

## Testing and Debugging Navigation

### Manual Tests

| Test | What to Check |
|---|---|
| **Root page** | Does the menu show all top-level items? Is the current page highlighted? |
| **Subpage** | Does the subpage inherit the same menu? Is `/Sub` template loaded if it exists? |
| **Non-existent page** | Does `#ifexist` correctly hide conditional links? |
| **Year rollover** | Does `{{CURRENTYEAR}}` + 1 link only show when the page exists? |
| **Language variant** | Do `Special:MyLanguage/` links resolve correctly? |

### Debugging with Parse API

```bash
# See what the fully expanded navigation template produces
curl -s "https://meta.wikimedia.org/w/api.php?action=expandtemplates&text={{:AvoinGLAM/Past_activities}}&prop=wikitext&format=json" \
  -H "User-Agent: MyTool/1.0"
```

### Checking Template Transclusion

```bash
# Verify all templates used on the page (including sub-nav templates)
curl -s "https://meta.wikimedia.org/w/api.php?action=query&prop=templates&titles=AvoinGLAM/Past%20activities&format=json" \
  -H "User-Agent: MyTool/1.0"
```

---

## Reference Links

| Resource | URL |
|---|---|
| MediaWiki subpages | [mediawiki.org/wiki/Help:Subpages](https://www.mediawiki.org/wiki/Help:Subpages) |
| `#titleparts` parser function | [mediawiki.org/wiki/Help:Magic_words#titleparts](https://www.mediawiki.org/wiki/Help:Magic_words#titleparts) |
| `Special:MyLanguage` | [mediawiki.org/wiki/Help:Special_MyLanguage](https://www.mediawiki.org/wiki/Help:Special_MyLanguage) |
| `{{CURRENTYEAR}}` and other variables | [mediawiki.org/wiki/Help:Magic_words#Date_and_time](https://www.mediawiki.org/wiki/Help:Magic_words#Date_and_time) |
| Template transclusion API | [mediawiki.org/wiki/API:Properties#templates](https://www.mediawiki.org/wiki/API:Properties#templates) |
| Skill: Templates | [wikipedia-templates](../wikipedia-templates/SKILL.md) |
| Skill: Page styling | [wikimedia-page-styling](../wikimedia-page-styling/SKILL.md) |
| Skill: Translate extension | [mediawiki-translate-extension](../mediawiki-translate-extension/SKILL.md) |
| Skill: API access | [wikimedia-api-access](../wikimedia-api-access/SKILL.md) |

---

## Tooling

This skill includes helper scripts, reference docs, and template code.

### 🔧 Navigation Inspector (`scripts/navigation-inspector.sh`)

Analyze the navigation structure of a page — menu templates, subpage hierarchy, `/Sub` templates, link tree:

```bash
# Show navigation structure for a page
./scripts/navigation-inspector.sh "AvoinGLAM/Past activities" --wiki meta

# Show full link tree (all linked pages)
./scripts/navigation-inspector.sh "Project/Page" --links

# Show subpage hierarchy
./scripts/navigation-inspector.sh "Project/Page/Subpage" --hierarchy
```

### 🔧 Expand Navigation Template (`scripts/expand-navigation.sh`)

Expand a navigation template call to see the fully rendered wikitext output:

```bash
# Expand with parameters
./scripts/expand-navigation.sh "Project/Navigation" "image=File:hero.jpg|title=My Project"

# Expand with the current page context
./scripts/expand-navigation.sh "Project/Navigation" --page "Project/Subpage"
```

### 📚 Navigation Pattern Catalog (`references/navigation-patterns.md`)

Complete catalog of navigation patterns with ready-to-use wikitext:
- Horizontal menu bar (with active state)
- Vertical sidebar menu
- Tab navigation
- Dropdown sub-menus
- Breadcrumb trails
- Year-based temporal navigation
- Language-switching menu
- Pagination (page numbers)
- Search + filter navigation
- Multi-level accordion

### 🐍 Navigation Analyzer (`assets/navigation_analyzer.py`)

Given a page, trace its navigation template hierarchy, subpage structure, and link tree:

```bash
# Full analysis of a page's navigation
python3 assets/navigation_analyzer.py "AvoinGLAM/Past activities" --wiki meta

# Visualize the page hierarchy tree
python3 assets/navigation_analyzer.py "Project" --tree

# Show conditional navigation (what #ifexist would match)
python3 assets/navigation_analyzer.py "Project/Subpage" --conditionals
```

### 🧪 Test Suite (`tests/`)

Test scripts for verifying navigation template logic:

```bash
# Run all navigation tests
python3 -m pytest tests/

# Test #titleparts parsing patterns
python3 -m pytest tests/test_titleparts.py

# Test temporal navigation patterns
python3 -m pytest tests/test_temporal_nav.py
```
