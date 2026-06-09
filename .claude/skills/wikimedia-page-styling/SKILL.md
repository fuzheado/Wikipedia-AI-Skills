---
name: wikimedia-page-styling
description: Use TemplateStyles to load custom CSS on wiki pages, then build responsive grid/flexbox layouts, card-based tile systems, color themes, button systems, and full visual design systems — transforming plain MediaWiki pages into rich, interactive-looking interfaces
license: MIT
compatibility: opencode
---

> ⚠️ **User-Agent required:** The API examples below hit Wikimedia endpoints. All requests must include a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.
>
> 📖 **Prerequisites:** For general template syntax and parser functions, see **[wikipedia-templates](../wikipedia-templates/SKILL.md)**. For navigating subpage hierarchies and building menu navigation, see **[mediawiki-page-navigation](../mediawiki-page-navigation/SKILL.md)**. For the Translate extension and multilingual content, see **[mediawiki-translate-extension](../mediawiki-translate-extension/SKILL.md)**.

---

## Table of Contents

1. [What TemplateStyles Is](#what-templatestyles-is)
2. [How TemplateStyles Works](#how-templatestyles-works)
3. [Creating a CSS Template](#creating-a-css-template)
4. [Allowed CSS Properties (The Sanitizer)](#allowed-css-properties-the-sanitizer)
5. [CSS Grid Layouts](#css-grid-layouts)
6. [Flexbox Layouts](#flexbox-layouts)
7. [Card / Tile Design Patterns](#card--tile-design-patterns)
8. [Color Theme System](#color-theme-system)
9. [Button Design System](#button-design-system)
10. [Typography](#typography)
11. [Responsive Breakpoints](#responsive-breakpoints)
12. [Skin Targeting (Vector / Minerva)](#skin-targeting-vector--minerva)
13. [Image Positioning & Object-Fit](#image-positioning--object-fit)
14. [Hover Overlays and Transitions](#hover-overlays-and-transitions)
15. [Lua + TemplateStyles Integration](#lua--templatestyles-integration)
16. [Anti-Abuse Features and Scoping](#anti-abuse-features-and-scoping)
17. [Cascading Order & Specificity](#cascading-order--specificity)
18. [Debugging TemplateStyles](#debugging-templatestyles)
19. [Reference Links](#reference-links)

---

## What TemplateStyles Is

**TemplateStyles** is a MediaWiki extension (available since MW 1.31, 2018) that allows templates to ship **their own CSS** without needing site-wide stylesheet edits (`MediaWiki:Common.css`). It is the **single most important feature** for creating visually rich wiki pages.

**Before TemplateStyles:** All custom CSS had to go in `MediaWiki:Common.css`, which required `interface-admin` rights and affected every page on the wiki. Template authors could only use inline styles (`style="..."`), which are repetitive, unmaintainable, and cannot use media queries.

**After TemplateStyles:** Any template can load its own CSS from any page in the Template namespace ending in `.css`:

```wikitext
<templatestyles src="AvoinGLAM/style.css" />
```

This CSS only applies to the page where the template is transcluded — it does **not** leak to other pages.

### What TemplateStyles Enables

| Capability | Without TemplateStyles | With TemplateStyles |
|---|---|---|
| Custom fonts (e.g. Montserrat) | Impossible (can't ship font assets) | ✅ Declare in CSS |
| CSS Grid layouts | Inline `style` on every element | ✅ Full CSS Grid |
| Responsive breakpoints | Impossible | ✅ `@media` queries |
| Hover effects | Inline `onmouseover` (not possible in wikitext) | ✅ `:hover` pseudo-classes |
| Color themes (`.bluebox`, `.whitebox`) | Manual on every element | ✅ Class-based theming |
| Layout classes (`.grid`, `.boxes`) | Impossible | ✅ Reusable CSS classes |
| Mobile/desktop adaptivity | Impossible | ✅ Responsive design |

---

## How TemplateStyles Works

### Basic Syntax

```wikitext
<templatestyles src="YourTemplate/style.css" />
```

The `src` parameter is a page title in the **Template namespace** (NS 10). The page must end in `.css`. You can omit the `Template:` prefix:

```wikitext
<!-- These are equivalent: -->
<templatestyles src="AvoinGLAM/style.css" />
<templatestyles src="Template:AvoinGLAM/style.css" />
```

### Placement

Place `<templatestyles>` near the **top** of your template, before any HTML that uses the styles:

```wikitext
<templatestyles src="Project/colors.css" />
<div class="project-box">...</div>
```

### Multiple Stylesheets

You can load multiple stylesheets — they cascade in order:

```wikitext
<templatestyles src="Project/colors.css" />
<templatestyles src="Project/layout.css" />
<templatestyles src="Project/buttons.css" />
```

### Loading from a Template Call

A template can let its caller specify an additional stylesheet:

```wikitext
{{#if: {{{style|}}}|<templatestyles src="{{{style|}}}" />}}
```

### What Gets Loaded

TemplateStyles generates a `<link rel="stylesheet">` element in the page `<head>` with a **randomized, unique URL** that includes a hash of the CSS content for cache busting:

```html
<link rel="stylesheet" href="/w/load.php?lang=en&amp;modules=ext.templatestyles;ext.templatestyles.assets&amp;skin=vector&amp;target=AvoinGLAM/style.css&amp;*">
```

This means changes to the CSS template are reflected near-instantly (subject to CDN cache).

---

## Creating a CSS Template

### Step 1: Create the Page

Create a page at `Template:YourProject/style.css` with any standard CSS:

```css
/* Template:YourProject/style.css */
.my-box {
    background: #f1f4f6;
    border-radius: 8px;
    padding: 1.5rem;
    margin: 1rem 0;
}

.my-box h3 {
    font-family: "Montserrat", sans-serif;
    font-weight: bold;
    font-size: 1.4rem;
    margin-top: 0;
}

.my-grid {
    display: grid;
    gap: 1.5rem;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}
```

### Step 2: Create a Template that Loads It

```wikitext
<templatestyles src="YourProject/style.css" />
<div class="my-grid">
  <div class="my-box">
    <h3>Card title</h3>
    <p>Card content here.</p>
  </div>
</div>
```

### Step 3: Create a Wrapper Template for Reuse

```wikitext
<!-- Template:YourProject/Box -->
<templatestyles src="YourProject/style.css" />
{{#tag:div
|{{#if:{{{title|}}}|<h3>{{{title|}}}</h3>}}
{{{content|}}}
|class=my-box
}}
```

**Key insight:** TemplateStyles is loaded every time the template is transcluded, but it's deduplicated per page — the CSS is only fetched once regardless of how many times the template appears.

### Naming Conventions

| Convention | Example | Purpose |
|---|---|---|
| `Project/style.css` | `AvoinGLAM/style.css` | Main stylesheet for a project |
| `Project/colors.css` | `GLAM/colors.css` | Color variables/themes |
| `Project/layout.css` | `GLAM/layout.css` | Grid and flexbox rules |
| `Project/buttons.css` | `GLAM/buttons.css` | Button component styles |

---

## Allowed CSS Properties (The Sanitizer)

TemplateStyles **sanitizes CSS** for security — only certain CSS properties and values are allowed. This prevents CSS-based attacks (data exfiltration via `background-image: url(...)`, XSS via `expression()`, etc.).

### Allowed Properties (Complete List)

The sanitizer allows most common layout, typography, and visual properties. Key categories:

| Category | Allowed Properties |
|---|---|
| **Box model** | `width`, `height`, `min-width`, `max-width`, `min-height`, `max-height`, `padding` (and `-top`, `-right`, `-bottom`, `-left`), `margin` (and directional variants), `box-sizing` |
| **Display & layout** | `display`, `flex`, `flex-direction`, `flex-wrap`, `flex-flow`, `flex-grow`, `flex-shrink`, `flex-basis`, `grid`, `grid-template` (columns, rows, areas), `grid-column`, `grid-row`, `grid-area`, `grid-gap`, `gap`, `order`, `align-items`, `align-content`, `align-self`, `justify-items`, `justify-content`, `justify-self`, `place-items`, `place-content`, `place-self` |
| **Positioning** | `position`, `top`, `right`, `bottom`, `left`, `overflow`, `overflow-x`, `overflow-y`, `z-index`, `float`, `clear` |
| **Typography** | `font`, `font-family`, `font-size`, `font-weight`, `font-style`, `font-variant`, `line-height`, `text-align`, `text-decoration`, `text-transform`, `text-overflow`, `text-shadow`, `letter-spacing`, `word-spacing`, `white-space`, `word-break`, `overflow-wrap`, `hyphens`, `direction`, `unicode-bidi`, `column-count`, `column-gap`, `column-width`, `columns` |
| **Color & background** | `color`, `background`, `background-color`, `background-image` (⚠️ restricted — see below), `background-repeat`, `background-size`, `background-position`, `background-attachment`, `background-clip`, `background-origin`, `opacity` |
| **Border & outline** | `border`, `border-collapse`, `border-color`, `border-style`, `border-width`, `border-radius` (and directional variants), `outline`, `outline-color`, `outline-style`, `outline-width` |
| **Visual effects** | `box-shadow`, `filter`, `backdrop-filter`, `transform`, `transition`, `transition-property`, `transition-duration`, `transition-timing-function`, `transition-delay`, `animation`, `animation-name`, `animation-duration`, `animation-timing-function`, `animation-delay`, `animation-iteration-count`, `animation-direction`, `animation-fill-mode`, `animation-play-state` |
| **Lists** | `list-style`, `list-style-type`, `list-style-image`, `list-style-position` |
| **Tables** | `table-layout`, `empty-cells`, `caption-side`, `vertical-align` |
| **Content** | `content`, `counter-increment`, `counter-reset`, `quotes` |
| **UI** | `cursor`, `visibility`, `clip`, `clip-path`, `pointer-events`, `resize`, `user-select`, `caret-color` |

### ⚠️ Restricted Properties

| Property | Restriction |
|---|---|
| `background-image` | Only `linear-gradient()`, `radial-gradient()`, `repeating-linear-gradient()`, `repeating-radial-gradient()`, `conic-gradient()`, `repeating-conic-gradient()` — **no `url()`** for external images or `data:` URIs |
| `font-family` | Only generic families (`sans-serif`, `serif`, `monospace`, `cursive`, `fantasy`, `system-ui`) and **locally-loaded** web fonts via `@font-face` (must be hosted on Wikimedia servers) |
| `@font-face` | Allowed but the `src` URL must point to a Wikimedia-hosted file (Commons or extension) |
| `filter` | All filter functions allowed except `filter: url()` (external references) |
| `clip-path` | All values allowed except `clip-path: url()` |
| `cursor` | Only standard CSS keywords — no custom `url()` cursors |

### CSS At-Rules Allowed

| At-rule | Allowed? | Notes |
|---|---|---|
| `@media` | ✅ Yes | All media queries (screen, print, min-width, max-width, prefers-color-scheme, etc.) |
| `@supports` | ✅ Yes | Feature queries |
| `@font-face` | ✅ Yes | Font URLs must be Wikimedia-hosted |
| `@keyframes` | ✅ Yes | For CSS animations |
| `@page` | ✅ No | Not supported |
| `@import` | ❌ No | Use separate `<templatestyles>` tags instead |
| `@namespace` | ❌ No | Not supported |

### Checking the Sanitizer

To see the exact allowlist for your wiki:

```
GET https://meta.wikimedia.org/w/api.php?action=templatestyles&modules=ext.templatestyles&format=json
```

Or check the [extension.json source](https://github.com/wikimedia/mediawiki-extensions-TemplateStyles/blob/master/src/TemplateStylesMatcherFactory.php).

---

## CSS Grid Layouts

CSS Grid is the foundation of the tile/card layout seen on AvoinGLAM pages.

### Basic Grid Container

```css
.grid {
    display: grid;
    gap: 1.5rem;
    margin: 1.5rem 0;
    grid-template-columns: repeat(auto-fit, minmax(150px, 219px));
}
```

This creates a responsive grid where:
- Each column is between **150px** (minimum) and **219px** (maximum)
- `auto-fit` creates **as many columns as fit** in the viewport
- Items auto-wrap to new rows as the viewport narrows
- Gap between items is `1.5rem`

### Grid Variants

```css
/* Two-column grid for wider content */
.grid-wide {
    display: grid;
    gap: 2rem;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

/* Three-column grid for dense layouts */
.grid-dense {
    display: grid;
    gap: 1rem;
    grid-template-columns: repeat(3, 1fr);
}

/* Mixed — first item spans full width */
.blog-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
}
.blog-grid > div:first-child {
    grid-column: 1 / -1;  /* Spans all columns */
}
.blog-grid > div:last-child {
    display: none;         /* Hides a sentinel/listeria element */
}
```

### Using Grid in Wikitext

```wikitext
<div class="grid">
{{Card|title=Item 1|...}}
{{Card|title=Item 2|...}}
{{Card|title=Item 3|...}}
</div>
```

**CSS Grid + #tag pattern** (for template authors who prefer parser functions):

```wikitext
{{#tag:div
|{{Card|title=Item 1}}
{{Card|title=Item 2}}
|class=grid
}}
```

### The "Listeria" Pattern

Many grid templates hide the last child div — this works with API-driven listers that emit a trailing sentinel:

```css
.grid.listeria > div:last-child {
    display: none;
}
```

---

## Flexbox Layouts

Flexbox is used for navigation bars, button groups, horizontal metadata rows, and alignment tasks.

### Horizontal Menu Bar

```css
.menu {
    margin: 0 0 1rem 0;
    font-family: "Montserrat", sans-serif;
}
.menu ul {
    display: flex;
    list-style: none;
    margin: 0;
}
.menu ul li {
    font-weight: bold;
    padding: 1rem 0;
    margin-right: 1.5rem;
    margin-bottom: 0;
    color: black;
    transition: 0.3s;
}
.menu ul li:hover {
    box-shadow: inset 0 -2px 0 #0E65C0;
}
.menu ul li a {
    text-decoration: none;
    color: black;
}
```

### Flexible Box Groups

```css
.boxes {
    display: flex;
    flex-wrap: wrap;
    column-gap: 1.5rem;
    row-gap: 1.5rem;
    margin: 2rem 0;
}
```

### Horizontal Metadata Rows

```css
.logrow {
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    column-gap: 0.5em;
}

.someicons {
    display: flex;
    gap: 0.4em;
    flex-flow: wrap;
}

.inventorydata {
    display: flex;
    gap: 2em;
    margin: 1em 0 2em;
}
.inventorydata div {
    flex: 1 1 50%;
}
```

### Alignment Helpers

```css
.bi {
    display: flex;
    gap: 1.5em;
    align-items: center;
}

.logcontent {
    display: flex;
    flex-direction: row;
    gap: 1em;
    align-items: flex-start;
}
```

---

## Card / Tile Design Patterns

The "card" or "tile" is the fundamental building block of rich Meta pages.

### Small Box (Tile) Pattern

This is the pattern used in the `{{Wiki Loves Living Heritage/Box}}` template with `color=smallbox`:

```css
.smallbox {
    padding: 0;
    flex: 1 1 200px;
    min-width: 150px;
    max-width: 300px;
}

.smallbox img {
    border-radius: 8px;
    width: 100%;
    height: 150px;
    object-fit: cover;
}

.smallbox h3 {
    line-height: 1.2em;
    font-size: 1.3em;
    margin-top: 0.6em;
    margin-bottom: 0;
}
```

### Generic Box Pattern

```css
.box {
    border-radius: 8px;
    padding: 1.5rem;
}
```

### Box Sizes

```css
.quarter {
    flex: 1 1 26%;
    min-width: 250px;
}

.third {
    min-width: 200px;
    max-width: 300px;
    padding: 0;
    flex: 1 1 240px;
}

.half {
    flex: 1 1 40%;
    min-width: 250px;
}

.full {
    flex: 1 1 100%;
    flex-direction: row;
    display: flex;
    gap: 1em;
}
```

### Image-Containing Box

```css
.boximg {
    position: relative;
    margin-bottom: 1em;
}

.boximg img {
    width: 100%;
    height: 150px;
    object-fit: cover;
    border-radius: 8px;
}
```

### Content Box Layout

```css
.blocks {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: flex-start;
}

.blocks p {
    margin: 0.5em 0 0 0;
}
```

---

## Color Theme System

A color theme system lets pages switch between visual themes by applying a CSS class to a container.

### Theme Classes

```css
/* Blue theme — for primary/hero content */
.bluebox {
    background: #0E65C0;
    color: white;
}

.bluebox h2, .bluebox h3, .bluebox h4 {
    color: white;
}

/* White/light theme — for secondary content */
.whitebox {
    background: #F1F4F6;
}

/* Alert / notice theme */
.alertbox {
    background: #f8eb79;
}

/* Colored columns for tables/programs */
.col1 { background: #f6b264; }
.col2 { background: #bb5e2d; }
.col3 { background: #b6d0c0; }
.col4 { background: #25a3ac; }
.col5 { background: #045a70; }
.col6 { background: #e98036; }
.col7 { background: #f0d4aa; }
.col8 { background: #4eacb7; }
```

### Using Themes in a Template

```wikitext
{{#tag:div
|content
|class=box {{{color|whitebox}}} {{{size|half}}}
}}
```

The caller picks a color:

```wikitext
{{Box|color=bluebox|title=Welcome|...}}
{{Box|color=whitebox|title=Details|...}}
```

### Decorative Logo Backgrounds

Randomized color backgrounds for visual variety (via a `#switch` in the template):

```wikitext
{{#switch: {{#expr: {{#time: xNU}} mod 11 }}
 | 0 = #71D1B3
 | 1 = #970302
 | 2 = #E679A6
 | 3 = #EE8019
 | 4 = #F0BC00
 | 5 = #5748B5
 ...
}}
```

Applied as `background` style on a logo container.

---

## Button Design System

Buttons use pill-shaped (`border-radius: 2rem`) design with outline hover states.

### Base Button

```css
.btn {
    padding: 0.7rem 1.3rem;
    border-radius: 2rem;
    margin-top: 1rem;
    font-weight: bold;
    display: inline-block;
    font-family: 'Montserrat', sans-serif;
    white-space: nowrap;
}

/* Compact variant */
.tight {
    padding: 0.2rem 0.6rem;
    border-radius: 2rem;
    margin: 0.3em 0.1em;
    font-size: 0.9em;
}
```

### Button Color Variants

```css
/* Blue box → white button */
.bluebox .btn, .whitebtn {
    color: #0E65C0;
    background: white;
}

/* White box → blue button */
.whitebox .btn, .bluebtn, .negbtn:hover {
    color: white;
    background: #0E65C0;
}
```

### Button Hover States (Outline Style)

```css
/* Blue box — hover outline on white */
.bluebox .btn:hover, .whitebtn:hover {
    background: none;
    outline: 2px solid white;
    outline-offset: -2px;
}

/* White box — hover outline on blue */
.whitebox .btn:hover, .negbtn, .bluebtn:hover {
    background: none;
    outline: 2px solid #0E65C0;
    outline-offset: -2px;
    color: #0E65C0;
}
```

### Button Link Colors

```css
.bluebox .btn a, .whitebtn a {
    color: #0E65C0;
    text-decoration: none;
}

.whitebox .btn a, .bluebtn a {
    color: white;
    text-decoration: none;
}
```

### Using Buttons in a Template

```wikitext
{{#tag:div
| {{{linktitle|}}}
|class=btn {{{btnstyle|}}}
}}
```

The `btnstyle` parameter accepts: `bluebtn`, `whitebtn`, `negbtn`, `tight`, or combinations.

---

## Typography

### Font Family Declaration

```css
h1, .mw-heading1, h2, .mw-heading2, h3, .mw-heading3,
h4, h5 {
    font-family: "Montserrat", sans-serif;
    font-weight: bold;
    border-bottom: none;
}
```

Note: Montserrat is a **Google Font** not pre-loaded on Wikimedia wikis. For it to work, the wiki must load the font. On Meta, the font is loaded through the site-wide CSS. For custom projects, you have two options:

1. **Use system fonts** — `font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;`
2. **Use a web font hosted on Commons** — via `@font-face` pointing to a `.woff2` file on Commons

### Heading Sizes

```css
h1 { font-size: 2rem !important; margin-top: 0; padding-top: 0; }
h2 { font-size: 1.7rem; }
h3 { font-size: 1.4rem !important; line-height: 1; }
h4 { font-size: 1.1rem; }
```

### Banner Typography (Hero Section)

```css
.bannertitle {
    font-weight: bold;
    font-size: 4rem;
}

.bannerbody {
    font-size: 2rem;
    line-height: 1.3;
}

.bannertime {
    font-size: 1rem;
    background: black;
    color: white;
    border-radius: 1em;
    padding: 0.1em 1em;
    width: max-content;
}

.bannersubtitle {
    font-weight: bold;
}
```

### Article Metadata

```css
.articlemeta {
    font-weight: bold;
    margin: 2em 0 1em;
    font-family: 'Montserrat', sans-serif;
    line-height: normal;
}
```

### Capitalization

```css
h1:first-letter, h2:first-letter, h3:first-letter,
h4:first-letter, h5:first-letter {
    text-transform: capitalize;
}
```

This ensures headings always start with a capital letter regardless of wikitext.

---

## Responsive Breakpoints

### Standard Breakpoints

| Breakpoint | Target | Common Changes |
|---|---|---|
| `max-width: 1000px` | Small desktops / tablets | Menu collapses to vertical |
| `max-width: 800px` | Tablets | Two-column becomes single |
| `max-width: 600px` | Mobile phones | Full stacking, smaller fonts |

### Menu Collapse (1000px)

```css
@media only screen and (max-width: 1000px) {
    .menu ul li {
        padding: 0.2rem 0;
        margin-right: 0;
    }
    .menu ul {
        flex-direction: column;
    }
    .menu {
        margin: 1rem 0;
    }
}
```

### Header Adapt (800px)

```css
@media only screen and (max-width: 800px) {
    .headertitle {
        font-size: 4vw;
    }
}
```

### Mobile Stack (600px)

```css
@media only screen and (max-width: 600px) {
    .activity {
        position: relative;
        width: 100%;
        line-height: 1.4;
    }
    .activity .mainimage img.mw-file-element {
        height: 200px !important;
    }
    .articlerowinfo {
        flex-direction: column;
        align-items: start;
    }
    .full {
        flex-direction: column;
    }
    .bannerbackground {
        display: flex;
        flex-direction: column;
        padding: 2rem;
    }
    .bannertitle {
        font-size: 2rem;
    }
    .bannertexts {
        width: 100%;
    }
    .bannerbody {
        font-size: 1rem;
        padding-top: 0.5em;
    }
    .bannerimage {
        width: 100%;
        height: 70%;
    }
}
```

### Pattern: Prefer `em`/`rem` over `px` for Breakpoints

```css
/* Good — accessible: respects user font-size preferences */
@media only screen and (max-width: 62.5em) { ... }

/* Also fine for wiki pages where simplicity matters */
@media only screen and (max-width: 600px) { ... }
```

---

## Skin Targeting (Vector / Minerva)

TemplateStyles supports skin-specific styling via the `media` attribute on `<templatestyles>`:

```wikitext
<templatestyles src="Project/style.css" />
<templatestyles src="Project/mobile.css" media="screen and (max-width: 720px)" />
```

But a better approach is to use **class overrides** within the same CSS file:

```css
/* Desktop Vector */
.my-card { padding: 2rem; }

/* Mobile Minerva */
.skin-minerva .my-card { padding: 1rem; }

/* Vector 2022 (new Vector) has its own skin class */
.skin-vector-2022 .my-card { border-radius: 4px; }
```

Common skin class names:

| Skin | CSS Class |
|---|---|
| Vector (legacy) | `.skin-vector` |
| Vector (2022) | `.skin-vector-2022` |
| Minerva (mobile) | `.skin-minerva` |
| Monobook | `.skin-monobook` |
| Timeless | `.skin-timeless` |

---

## Image Positioning & Object-Fit

When images are used as card thumbnails or hero banners, controlling how they fill their container is critical.

### Object-Fit Classes

```css
.mainimage img.mw-file-element {
    width: 100%;
    object-fit: cover;
    max-height: 450px;
}

/* Position the image to show the top portion (useful for portraits) */
.mainimage.top img.mw-file-element {
    object-position: top;
}

/* Position to bottom (useful for landscapes) */
.mainimage.bottom img.mw-file-element {
    object-position: bottom;
}

/* Don't crop — show the whole image with letterboxing */
.mainimage.contain img.mw-file-element {
    object-fit: contain;
}

/* Position at 25% from top (good for person photos — eyes centered) */
.person img {
    object-position: 50% 25%;
}
```

These classes are passed via the `class` parameter in templates:

```wikitext
{{AvoinGLAM/Main navigation
  |image=File:Photo.jpg
  |class=person
}}
```

### Card Image Sizing

```css
.smallbox img {
    border-radius: 8px;
    width: 100%;
    height: 150px;
    object-fit: cover;
}

.boximg img {
    width: 100%;
    height: 150px;
    object-fit: cover;
    border-radius: 8px;
}
```

### Table Image Sizing

```css
.tableimg img {
    width: 150px;
    height: 150px;
    border-radius: 8px;
    object-fit: cover;
}
```

---

## Hover Overlays and Transitions

The hover overlay pattern used on gallery items creates a "reveal info on hover" effect.

### Overlay Pattern (White Semi-Transparent)

```css
.work {
    flex: auto;
    border-radius: 8px;
    position: relative;
    overflow: hidden;
    text-align: center;
}

/* Invisible overlay that fades in on hover */
.work::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(255, 255, 255, 0.85);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.work:hover::before {
    opacity: 1;
}

/* Hidden content that appears on hover */
.workdata {
    display: none;
}

.work:hover .workdata {
    display: flex;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    justify-content: center;
    align-items: center;
    color: #333;
    padding: 1em;
    text-align: center;
    flex-direction: column;
    width: 100%;
    z-index: 2;
    word-break: break-word;
    box-sizing: border-box;
}
```

### Simple Hover Effects

```css
/* Underline reveal on menu items */
.menu ul li {
    transition: 0.3s;
}
.menu ul li:hover {
    box-shadow: inset 0 -2px 0 #0E65C0;
}

/* Color change on hover */
.menu ul li:hover a {
    color: #0E65C0;
}

/* Grayscale to color */
.createarticle img {
    opacity: 0.5;
    filter: grayscale(1);
    transition: 0.3s;
}
.createarticle:hover img {
    opacity: 1;
    filter: grayscale(0);
}
```

---

## Lua + TemplateStyles Integration

Lua modules (via Scribunto) can generate `<templatestyles>` calls programmatically.

### From Lua: Emitting a Stylesheet Link

```lua
local p = {}

function p.render(frame)
    -- Emit the stylesheet tag
    local css = '<templatestyles src="Project/style.css" />'
    -- Build content
    local html = css .. '<div class="my-box">Content</div>'
    return html
end

return p
```

### From Lua: Adding a Class Name

```lua
function p.card(frame)
    local color = frame.args["color"] or "whitebox"
    -- The CSS class is chosen dynamically
    local html = mw.html.create('div')
        :addClass('box')
        :addClass(color)
        :wikitext(frame.args["content"])
    return tostring(html)
end
```

### Checking TemplateStyles from Lua

Use `frame:extensionTag()` to generate the templatestyles tag properly:

```lua
function p.withStyles(frame)
    return frame:extensionTag('templatestyles', '', { src = 'Project/style.css' })
        .. '<div class="styled-content">' .. frame.args[1] .. '</div>'
end
```

---

## Anti-Abuse Features and Scoping

### CSS Scoping

TemplateStyles CSS is **automatically scoped** — each stylesheet is prefixed with a unique `mw-parser-output` ancestor selector. This means:

```css
/* Your CSS */
.my-class { color: red; }

/* Gets transformed to: */
.mw-parser-output .my-class { color: red; }
```

This prevents TemplateStyles from affecting content outside the parser output area (e.g., site navigation, footer).

### Sanitization Errors

If you use a disallowed property or value, the CSS rule is **silently dropped** — the page still renders, but your style won't apply. To debug:

1. Open browser DevTools → Network tab → Find the `load.php` request for `templatestyles`
2. Check the Response tab — invalid rules are omitted
3. Alternatively, check the wiki's `action=templatestyles&modules=ext.templatestyles` API response for warnings

### Flagged Properties

Some properties are allowed but **flagged** for review:
- `background-image` with gradients is allowed; `url()` is blocked
- `position: fixed` and `position: absolute` are allowed but may be flagged for accessibility review

### Template Protection

High-use CSS templates should be protected at `templateeditor` or `sysop` level, just like high-use templates:

```
action=query&prop=info&inprop=protection&titles=Template:Project/style.css&format=json
```

---

## Cascading Order & Specificity

Order of CSS application on a wiki page:

1. **Site-wide CSS** (`MediaWiki:Common.css`, skin CSS)
2. **TemplateStyles CSS** (in order of `<templatestyles>` tags on the page)
3. **Page-specific CSS** (if any `<style>` tags exist — these are stripped on Wikimedia wikis for security)

**Specificity:** TemplateStyles has **normal CSS specificity** — it follows standard CSS cascade rules. Use more specific selectors to override:

```css
/* Base style from TemplateStyles */
.smallbox h3 { font-size: 1.3em; }

/* Override on a specific page via another TemplateStyles inclusion */
.special-page .smallbox h3 { font-size: 1.5em; }
```

**Multiple TemplateStyles:** If two templates load different stylesheets that target the same element, the **last one loaded** wins at equal specificity.

TemplateStyles also **deduplicates** — if the same stylesheet is loaded twice (same hash), it's only included once.

---

## Debugging TemplateStyles

### Quick Checklist

| Issue | Likely Cause |
|---|---|
| Style doesn't apply | Property not in allowlist, or selector specificity too low |
| Style applies on template page but not in articles | `<noinclude>` wrapping the `<templatestyles>` tag |
| Only some rules work | Disallowed properties are silently dropped |
| Looks different on mobile | Minerva skin has different defaults — use `.skin-minerva` overrides |
| Cache issues | Append `?action=purge` to the page, or wait for CDN purge |

### Checking if TemplateStyles is Loading

```bash
# Does the page load any templatestyles?
curl -s "https://meta.wikimedia.org/w/api.php?action=parse&page=PageTitle&prop=modules&format=json" \
  -H "User-Agent: MyTool/1.0" | python3 -c "
import json, sys
data = json.load(sys.stdin)
modules = data.get('parse', {}).get('modules', [])
ts = [m for m in modules if 'templatestyles' in m]
print(f'TemplateStyles modules: {ts}' if ts else 'No TemplateStyles found')
"
```

### Validating a CSS File

Use the templatestyles Action API module (if available on the wiki):

```bash
curl -s "https://meta.wikimedia.org/w/api.php?action=templatestyles&modules=ext.templatestyles&format=json&text=.my-class%20%7B%20color%3A%20red%3B%20%7D" \
  -H "User-Agent: MyTool/1.0" | python3 -m json.tool
```

### Visual Debugging

Use your browser's **Inspect Element** on the rendered page. TemplateStyles classes (`.mw-parser-output .my-class`) should appear in the Computed Styles panel.

---

## Reference Links

| Resource | URL |
|---|---|
| TemplateStyles extension page | [mediawiki.org/wiki/Extension:TemplateStyles](https://www.mediawiki.org/wiki/Extension:TemplateStyles) |
| Help:TemplateStyles | [mediawiki.org/wiki/Help:TemplateStyles](https://www.mediawiki.org/wiki/Help:TemplateStyles) |
| Allowed CSS properties (source) | [github.com/wikimedia/mediawiki-extensions-TemplateStyles](https://github.com/wikimedia/mediawiki-extensions-TemplateStyles) |
| CSS sanitizer source | [github.com/wikimedia/mediawiki-extensions-TemplateStyles/blob/master/src/TemplateStylesMatcherFactory.php](https://github.com/wikimedia/mediawiki-extensions-TemplateStyles/blob/master/src/TemplateStylesMatcherFactory.php) |
| TemplateStyles usage on Meta | [meta.wikimedia.org/wiki/Category:Templates_with_TemplateStyles](https://meta.wikimedia.org/wiki/Category:Templates_with_TemplateStyles) |
| Skill: Templates | [wikipedia-templates](../wikipedia-templates/SKILL.md) |
| Skill: Navigation | [mediawiki-page-navigation](../mediawiki-page-navigation/SKILL.md) |
| Skill: Translate extension | [mediawiki-translate-extension](../mediawiki-translate-extension/SKILL.md) |
| Skill: API access | [wikimedia-api-access](../wikimedia-api-access/SKILL.md) |

---

## Tooling

This skill includes helper scripts, reference docs, and template code.

### 🔧 Validate TemplateStyles CSS (`scripts/validate-templatestyles.sh`)

Check a CSS file or template against the TemplateStyles allowed-property allowlist:

```bash
# Validate a local CSS file
./scripts/validate-templatestyles.sh path/to/style.css

# Validate directly from a wiki template
./scripts/validate-templatestyles.sh --wiki meta "AvoinGLAM/style.css"

# Show only warnings for disallowed properties
./scripts/validate-templatestyles.sh style.css --strict
```

### 🔧 Fetch Rendered TemplateStyles (`scripts/fetch-templatestyles.sh`)

Download the compiled, sanitized CSS from a TemplateStyles template page (what the browser actually receives):

```bash
# Fetch the rendered CSS for inspection
./scripts/fetch-templatestyles.sh "AvoinGLAM/style.css" --wiki meta

# Compare source vs. rendered (spot what got stripped)
./scripts/fetch-templatestyles.sh "Project/style.css" --diff
```

### 📚 Allowed CSS Properties Reference (`references/allowed-properties.md`)

Complete categorized reference of all CSS properties, at-rules, and values allowed by TemplateStyles sanitizer.

### 📚 Layout Pattern Catalog (`references/layout-patterns.md`)

Reusable CSS Grid and Flexbox patterns with wikitext usage examples and responsive variants:
- Single-column responsive
- Multi-column card grids
- Hero banner layouts
- Sidebar + content layouts
- Dashboard/dataviz layouts

### 📚 Design Theme Examples (`references/design-themes.md`)

Color palette suggestions, typography pairings, and complete theme CSS examples:
- Blue/white professional theme
- Warm/earthy community theme
- Dark/accent theme for dashboards
- High-contrast accessibility theme

### 🐍 TemplateStyles Inspector (`assets/templatestyles_inspector.py`)

Analyze a page for all TemplateStyles usage — which CSS templates are loaded, what CSS properties they define, and whether any disallowed properties are present:

```bash
# Inspect TemplateStyles on a page
python3 assets/templatestyles_inspector.py "AvoinGLAM/Past activities" --wiki meta

# Show all CSS rules grouped by selector
python3 assets/templatestyles_inspector.py "Page" --rules

# Check for unsupported properties
python3 assets/templatestyles_inspector.py "Page" --lint
```

### 🐍 Grid Layout Preview (`assets/grid_layout_preview.py`)

Generate a visualization of how a CSS Grid configuration will look, given column min/max widths and gap:

```bash
# Preview a grid layout
python3 assets/grid_layout_preview.py --min 150 --max 219 --gap 24

# Export grid CSS for a given number of items
python3 assets/grid_layout_preview.py --items 12 --columns 3 --gap 16 --output-css
```

### 🧪 Test Suite (`tests/`)

Test scripts for verifying tool functionality:

```bash
# Run all tests
python3 -m pytest tests/

# Test the inspector against known pages
python3 -m pytest tests/test_inspector.py

# Test CSS validation rules
python3 -m pytest tests/test_validation.py
```
