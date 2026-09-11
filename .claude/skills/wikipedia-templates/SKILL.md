---
name: wikipedia-templates
description: Create, design, and understand Wikipedia and MediaWiki templates — template syntax, parser functions, magic words, transclusion vs substitution, Lua modules, template types taxonomy, API detection, and maintenance workflows
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["template", "wikitext template", "parser function", "transclusion", "Lua module"]
  - keywords: ["#if", "#switch", "#invoke", "TemplateData", "infobox template"]
  - keywords: ["limitreport", "ResourceLoader", "Scribunto", "Module namespace", "ns 828"]
  - keywords: ["Related Changes", "RecentChangesLinked", "WhatLinksHere", "link table", "Prefixindex"]
last_verified: 2026-09-11
---

> ⚠️ **User-Agent required:** The API examples below hit Wikimedia endpoints. All requests must include a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.
>
> 📖 **Prerequisites:** For general article structure (infoboxes, categories, navboxes), see **[wikipedia-page-anatomy](../wikipedia-page-anatomy/SKILL.md)**. For AST-based programmatic manipulation of template wikitext, see **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)**. For bulk template operations (mass replacement, harvesting infoboxes into Wikidata), see **[pywikibot](../pywikibot/SKILL.md)**.

---

## SOP: How Templates Work

Templates are reusable wiki pages transcluded via double braces:

```wikitext
{{Template name}}
{{Template name|param1=value1|param2=value2}}
```

They live in the **Template namespace** (NS 10). Shortcuts like `{{cn}}` resolve to `Template:Cn`.

### Transclusion vs. Substitution

| Mechanism | Syntax | Behavior | Use Case |
|-----------|--------|----------|----------|
| **Transclusion** | `{{Template}}` | Content included dynamically — edits to the template update every page using it | Infoboxes, navboxes, maintenance tags |
| **Substitution** | `{{subst:Template}}` | Content copied into the page at save time — no link to template afterward | Signatures (`~~~~`), user talk messages, template documentation |
| **Safe substitution** | `{{safesubst:Template}}` | Works in both transcluded and substituted contexts | Templates that must work correctly when called from other templates |

**Transclusion** (the default) means the template content is not part of the page's raw wikitext. Use `action=parse` or the REST API `/html` endpoint to see the fully rendered page. **Substitution** places the expanded content directly into the page's wikitext — useful for signatures, page moves, and one-time messages.

### Template Parameters

Templates accept parameters in two forms:

```wikitext
{{Template
| named_param    = value          ← Named parameter (preferred for clarity)
| positional     = value          ← Or use bare values without names
}}

<!-- Positional parameters: the first unnamed arg is {{{1}}}, second is {{{2}}}, etc. -->
{{Infobox person|Albert Einstein|14 March 1879}}
```

**Inside the template, parameters are accessed as:**

```wikitext
{{{1}}}                   ← Positional parameter (required — shows {{{1}}} if omitted)
{{{named_param|default}}} ← Named parameter with default value
{{{1|}}}                  ← Positional parameter that defaults to empty string
{{{named_param}}}         ← Named parameter (required — shows {{{named_param}}} if omitted)
{{{named_param|}}}        ← Named parameter that defaults to empty string
```

**Key rules:**
- Named parameters can use spaces, underscores, or mixed case — `{{Template|param name=value}}` works
- Parameter names are case-insensitive after normalization (underscores → spaces, first letter upper-cased)
- A blank parameter (`|param=`) is **different from an omitted parameter** — use `{{{param|}}}` to default blank to empty
- Trailing whitespace in parameter values is stripped
- Pipe characters inside values must be escaped with `{{!}}`

### Inclusion Control Tags

These tags control what part of a template page gets transcluded:

| Tag | Effect |
|-----|--------|
| `<noinclude>...</noinclude>` | Content visible on the template page itself but **not** transcluded into articles |
| `<includeonly>...</includeonly>` | Content hidden on the template page but **included** when transcluded |
| `<onlyinclude>...</onlyinclude>` | **Only** this content is transcluded; everything else is ignored |

**Typical use:**
```wikitext
<noinclude>{{Documentation}}</noinclude>
<includeonly>[[Category:Navigation templates]]</includeonly>
{{Navbox | name = ...
}}
```

- `<noinclude>` wraps documentation, categories for the template page, and interwiki links
- `<includeonly>` wraps categories that should apply to *pages using the template*, not the template itself
- `<onlyinclude>` is for templates whose entire transcluded content is a subset of the page (rare)

### Key Design Principles

1. **Keep templates simple.** Complex logic belongs in Lua modules (see SOP: Lua Modules below).
2. **Always provide defaults.** Use `{{{param|default}}}` so the template degrades gracefully.
3. **Document your parameters.** Use `<noinclude>` for a `/doc` page or inline comments.
4. **Avoid expensive parser functions.** Each `{{#if:}}`, `{{#ifeq:}}`, `{{#switch:}}`, and `{{#time:}}` counts toward the 500-node limit.
5. **Test in a sandbox.** Create `Template:Templatename/sandbox` and `Template:Templatename/testcases`.

---

## SOP: Parser Functions

Parser functions are wiki-text functions that process arguments and return values. They are called with the `{{#function:}}` syntax.

### Conditional Functions

| Function | Syntax | Description |
|----------|--------|-------------|
| `#if` | `{{#if: {{{param\|}}} | then | else}}` | Returns `then` if parameter is non-empty, `else` otherwise |
| `#ifeq` | `{{#ifeq: a | b | equal | not equal}}` | String comparison (case-sensitive) |
| `#iferror` | `{{#iferror: {{#expr:1/0}} | error | ok}}` | Tests if a parser result produces an error |
| `#ifexpr` | `{{#ifexpr: 1+1=2 | yes | no}}` | Evaluates a mathematical expression |
| `#ifexist` | `{{#ifexist: Page title | exists | not found}}` | Checks if a page exists |
| `#switch` | `{{#switch: {{{type\|}}} \| case1 = value1 \| case2 = value2 \| #default = fallback}}` | Multi-way branch |

**Common patterns:**

```wikitext
{{#if: {{{image|}}}
| [[File:{{{image}}}|thumb]]
| <!-- No image — display nothing -->
}}

{{#switch: {{{type|}}}
| person = {{Infobox person}}
| place  = {{Infobox settlement}}
| book   = {{Infobox book}}
| #default = {{Infobox generic}}
}}

{{#ifeq: {{{url|}}} | {{{archive-url|}}}
| <!-- URL and archive are the same — show one -->
| {{cite web |url={{{url|}}} |archive-url={{{archive-url|}}}
           |archive-date={{{archive-date|}}} }}
}}
```

### Data Functions

| Function | Syntax | Description |
|----------|--------|-------------|
| `#expr` | `{{#expr: 1+1}}` | Evaluates a mathematical expression and returns the result |
| `#time` | `{{#time: Y-m-d}}` | Formats a date/time, defaulting to the current UTC time |
| `#timel` | `{{#timel: Y-m-d}}` | Same as `#time` but in the wiki's local time |

**Common `#time` format strings:**

| Code | Output | Example |
|------|--------|---------|
| `Y` | 4-digit year | `2026` |
| `y` | 2-digit year | `26` |
| `F` | Full month name | `June` |
| `M` | Abbreviated month | `Jun` |
| `m` | 2-digit month | `06` |
| `j` | Day of month (no leading zero) | `8` |
| `d` | 2-digit day of month | `08` |
| `H` | 2-digit hour (00–23) | `14` |
| `i` | 2-digit minute | `30` |
| `s` | 2-digit second | `05` |

### Technical Functions

| Function | Syntax | Description |
|----------|--------|-------------|
| `#tag` | `{{#tag: ref \| citation text \| name=foo}}` | Generates an XML-like tag (`<ref>...</ref>`) |
| `#invoke` | `{{#invoke: ModuleName | functionName | arg1 | arg2}}` | Calls a Lua module function |
| `#property` | `{{#property: P18}}` | Fetches a Wikidata property for the current page's item |
| `#statements` | `{{#statements: P18\|from=Q123}}` | Fetches a Wikidata property for a specific Q-item |
| `#invoke` | *See SOP: Lua Modules below* | |

### String Functions (via `#invoke:String`)

Common string operations are available through `Module:String`:

```wikitext
{{#invoke:String|len|S}}         ← Length
{{#invoke:String|sub|S|start|end}}  ← Substring
{{#invoke:String|match|S|pattern}}  ← Regex match
{{#invoke:String|find|S|target}}    ← Find position
{{#invoke:String|replace|S|old|new}} ← Replace
{{#invoke:String|trim|S}}         ← Strip whitespace
```

### Performance Notes

- `#if` is cheaper than `#ifeq` (no comparison needed)
- `#switch` is more efficient than nested `#ifeq` chains (uses a hash lookup)
- `#ifexist` is **expensive** — each call hits the database; limit to ~10 per page
- `#expr` is slower than a precomputed value
- `#time` with `#time: Y` (year only) is cached; complex `#time` formats are not
- See **Limits and Quotas** below for hard caps

---

## SOP: Magic Words

Magic words are special strings that return wiki metadata or behavior. They are recognized by MediaWiki's parser.

### Behavior Switches

These control page behavior and are placed anywhere in the wikitext:

| Word | Effect |
|------|--------|
| `__NOTOC__` | Hides the table of contents |
| `__FORCETOC__` | Forces the TOC to appear before the first heading |
| `__TOC__` | Places the TOC at this position |
| `__NOEDITSECTION__` | Hides edit links next to section headings |
| `__HIDDENCAT__` | Hides the category from readers (on category pages) |
| `__EXPECTUNUSEDCATEGORY__` | Suppresses "unused category" warnings |
| `__DISAMBIG__` | Marks the page as a disambiguation page |
| `__NEWSECTIONLINK__` | Adds a "new section" tab on talk pages |
| `__NONEWSECTIONLINK__` | Removes the "new section" tab |
| `__NOGALLERY__` | Displays file links instead of galleries on category pages |
| `__INDEX__` / `__NOINDEX__` | Allows or disallows search engine indexing |

### Variables

Variables return page-specific or wiki-specific data:

| Variable | Returns | Example Output |
|----------|---------|----------------|
| `{{PAGENAME}}` | Current page title (without namespace) | `Albert Einstein` |
| `{{PAGENAMEE}}` | URL-encoded page name | `Albert_Einstein` |
| `{{FULLPAGENAME}}` | Full page title with namespace | `Template:Infobox person` |
| `{{FULLPAGENAMEE}}` | URL-encoded full title | `Template:Infobox_person` |
| `{{NAMESPACE}}` | Namespace name | `Template` |
| `{{NAMESPACEE}}` | URL-encoded namespace | `Template` |
| `{{NAMESPACENUMBER}}` | Namespace number | `10` |
| `{{SITENAME}}` | Wiki site name | `Wikipedia` |
| `{{SERVER}}` | Wiki domain URL | `https://en.wikipedia.org` |
| `{{SERVERNAME}}` | Wiki domain name | `en.wikipedia.org` |
| `{{SCRIPTPATH}}` | Script path | `/w` |
| `{{CURRENTYEAR}}` | Current year | `2026` |
| `{{CURRENTMONTH}}` | Current month (01–12) | `06` |
| `{{CURRENTMONTHNAME}}` | Current month name | `June` |
| `{{CURRENTDAY}}` | Current day of month | `8` |
| `{{CURRENTDAYNAME}}` | Current day name | `Monday` |
| `{{CURRENTTIME}}` | Current time (HH:mm) | `14:30` |
| `{{CURRENTTIMESTAMP}}` | Current ISO timestamp | `20260608143005` |
| `{{REVISIONID}}` | Current revision ID | `123456789` |
| `{{REVISIONDAY}}` | Day of last revision | `8` |
| `{{REVISIONMONTH}}` | Month of last revision | `06` |
| `{{REVISIONYEAR}}` | Year of last revision | `2026` |
| `{{REVISIONTIMESTAMP}}` | Timestamp of last revision | `20260608143005` |
| `{{REVISIONUSER}}` | User who made the last edit | `ExampleUser` |
| `{{SITENAME}}` | Wiki site name | `Wikipedia` |
| `{{CONTENTLANGUAGE}}` | Wiki content language | `en` |
| `{{PAGESINCATEGORY:Category name}}` | Page count in category | `42` |
| `{{PAGESIZE:Page title}}` | Size of a page in bytes | `12345` |
| `{{PROTECTIONLEVEL:action}}` | Protection level for an action | `autoconfirmed`, `sysop`, or empty |
| `{{PROTECTIONEXPIRY:action}}` | Protection expiry timestamp | `infinity` or date |

### Template-Specific Magic Words

| Word | Effect |
|------|--------|
| `{{TALKPAGENAME}}` | Full talk page title | `Talk:Albert Einstein` |
| `{{SUBPAGENAME}}` | Subpage name (after the last `/`) | `sandbox` |
| `{{REVISIONID}}` | Current revision ID (useful in templates for cache busting) |

---

## SOP: Lua Modules

Some complex templates are backed by **Lua modules** through the Scribunto extension. Instead of parser function logic in wikitext, the logic lives in a Lua module in the `Module:` namespace (NS 828).

### How to Identify Lua-Backed Templates

Check the template source for `{{#invoke:}}`:

```wikitext
{{#invoke:Infobox|infobox}}
{{#invoke:Check for unknown parameters|check|unknown={{Main other|_VALUE_{{PAGENAME}}}}}}
{{#invoke:String|replace|source=...|old=...|new=...}}
```

Common Lua-backed templates include:
- `{{Infobox settlement}}` — `Module:Infobox` with `Module:Infobox settlement`
- `{{Cite web}}`, `{{Cite book}}`, etc. — `Module:Citation/CS1`
- `{{sfn}}`, `{{harvnb}}` — `Module:Footnotes`
- `{{Authority control}}` — `Module:Authority control`
- Navigation boxes — `Module:Navbox` (with `Module:Navbox/configuration`)

### Module Structure

```
Module:Name/
├── Module:Name               ← Main module code
├── Module:Name/configuration ← Configuration data
├── Module:Name/data          ← Large data tables
└── Module:Name/i18n          ← Internationalization strings
```

### How `#invoke` Works

```wikitext
{{#invoke:ModuleName|functionName|arg1|arg2|named_param=value}}
```

The Lua function receives a `frame` object:

```lua
local p = {}

function p.functionName(frame)
    local arg1 = frame.args[1]            -- Positional argument
    local named = frame.args["named_param"] -- Named argument
    local parent = frame:getParent()      -- Caller's arguments
    return "result"
end

return p
```

### Detection via API

```
action=query&prop=templates&titles=Infobox_settlement&format=json
```

Look for entries with `ns=828` (Module namespace) to identify Lua dependencies.

### When to Use a Module vs. Wikitext-Only Template

| Situation | Best Approach |
|-----------|---------------|
| Simple parameter display | Wikitext template |
| Conditional formatting with ≤5 branches | `{{#switch}}` |
| Complex data processing, loops, or string manipulation | Lua module |
| Citation formatting (hundreds of edge cases) | Lua module |
| Algorithmic logic with conditional branching | Lua module |
| When template exceeds post-expand include size (2 MB) | Lua module |

> ⚠️ **Editing Lua modules requires `templateeditor` or `sysop` rights** on most wikis. You can view the source, but changes must be suggested on the talk page or made by an authorized editor.

---

## SOP: Template Types Taxonomy

Templates on Wikipedia serve many distinct purposes. Here is the taxonomy with examples:

### Infoboxes
Right-aligned summary tables presenting key facts:

| Template | Purpose | Lua? |
|----------|---------|------|
| `{{Infobox person}}` | People | No |
| `{{Infobox settlement}}` | Cities, towns | Yes |
| `{{Infobox country}}` | Sovereign states | No |
| `{{Infobox film}}` | Movies | No |
| `{{Infobox company}}` | Organizations | No |
| `{{Infobox scientist}}` | Researchers | No |
| `{{Infobox book}}` | Books | No |
| `{{Infobox military conflict}}` | Battles, wars | No |

### Citation Templates
Inline reference formatting (see `wikipedia-citations` skill for details):

| Template | For |
|----------|-----|
| `{{cite web}}` | Web pages |
| `{{cite news}}` | News articles |
| `{{cite book}}` | Books |
| `{{cite journal}}` | Academic papers |
| `{{sfn}}` | Shortened footnote (Lua-backed) |
| `{{harvnb}}` | Harvard-style citation |

### Navigation Templates

| Type | Template | Purpose |
|------|----------|---------|
| **Navbox** | `{{Navbox}}` | Collapsible navigation at bottom of article |
| **Navbox with collapsible groups** | `{{Navbox with collapsible groups}}` | Multi-section navbox |
| **Sidebar** | `{{Sidebar}}` | Right-aligned navigation column |
| **Series box** | `{{Sister project links}}` | Links to related wiki projects |
| **Authority control** | `{{Authority control}}` | Library catalog identifiers |
| **Portal bar** | `{{Portal bar}}` | Links to related portals |

### Maintenance Templates
Tags that signal article issues (see `wikipedia-page-anatomy` for full list):

```wikitext
{{cn}}              {{POV}}
{{dead link}}        {{clarify}}
{{expand section}}   {{stub}}
{{original research}} {{weasel inline}}
{{better source}}    {{failed verification}}
```

### Banners and Assessment
Talk page templates for WikiProject coordination:

```wikitext
{{WikiProject Biography|living=yes|class=B|importance=High}}
{{WikiProject Physics|class=C|importance=Mid}}
{{ArticleHistory}}
{{Annual report}}
```

### Structural Templates
Templates that organize the page itself:

```wikitext
{{About|the physicist}}           ← Hatnote disambiguation
{{For|other uses}}                ← Other uses
{{Distinguish|OtherPerson}}       ← Similar name confusion
{{Redirect|Einstein}}             ← Redirect hatnote
{{TOC left}}                      ← Floating table of contents
{{Clear}}                         ← Clear floating elements
{{-}}                             ← Same as {{clear}}
```

### Media and Linking Templates

```wikitext
{{Commons category}}
{{Wikiquote}}
{{External media}}
{{Superimpose}}                   ← Image overlay
{{Image label}}                   ← Labels on images
{{Listen}}                        ← Audio file player
{{Multiple image}}                ← Gallery layout
```

### Stub Templates

```wikitext
{{stub}}              {{physics-stub}}
{{bio-stub}}          {{film-stub}}
{{geo-stub}}          {{sci-stub}}
```

---

## SOP: Template Detection and API Usage

### Find All Templates on a Page

```
action=query&prop=templates&titles=Albert_Einstein&format=json
```

Returns all templates transcluded on the page, with namespace (ns=10 for templates, ns=828 for modules):

```json
{
  "query": {
    "pages": {
      "123": {
        "templates": [
          { "ns": 10, "title": "Template:Infobox person" },
          { "ns": 10, "title": "Template:Authority control" },
          { "ns": 10, "title": "Template:Navbox" },
          { "ns": 828, "title": "Module:Infobox" },
          { "ns": 10, "title": "Template:Cn" }
        ]
      }
    }
  }
}
```

> ⚠️ **Response shape differs by API.** With `action=query&prop=templates`
> (above), each entry has `ns` + `title`. With `action=parse&prop=templates`,
> entries use `ns` + `exists` + `*` — the template title is under the `*` key,
> **not** `title`. Don't read `.title` off a `parse` response.

### Find All Pages Using a Template

```
action=query&list=embeddedin&eititle=Template:Infobox_person&format=json
```

Pagination via `eicontinue`. Limit with `eilimit`. Filter by namespace with `einamespace`.

### Expand a Template

```
action=expandtemplates&text={{Infobox_person|name=Test}}&format=json
```

Returns the fully expanded wikitext (all templates, parser functions, and magic words resolved). Useful for debugging what a template *actually* produces.

### Get Template Source

```
action=raw&title=Template:Infobox_person
```

Returns the raw wikitext of the template page (no transclusion expansion).

### Get Rendered Template

Use the REST API:

```
GET https://en.wikipedia.org/w/rest.php/v1/page/Template:Infobox_person/html
```

Returns the template page rendered as HTML5 via Parsoid. For templates that produce visible output, this shows what the template looks like.

---

## SOP: Template Protection and Limits

### Protection Levels

| Level | Required Right | Who Can Edit |
|-------|---------------|--------------|
| None | — | Any autoconfirmed user |
| `autoconfirmed` | `editsemiprotected` | Users 4+ days and 10+ edits |
| `templateeditor` | `templateeditor` | Trusted template editors |
| `sysop` (full) | `editprotected` | Administrators |

High-use templates (transcluded on 500,000+ pages) are typically protected at `templateeditor` or `sysop` level. Check protection:

```
action=query&prop=info&inprop=protection&titles=Template:Infobox_person&format=json
```

### Template Limits

| Limit | Cap | What Happens When Exceeded |
|-------|-----|---------------------------|
| **Post-expand include size** | 2,048,000 bytes | Templates beyond the limit are not expanded — raw `{{...}}` shown |
| **Template argument size** | 2,048,000 bytes | Same — template call is preserved unexpanded |
| **Expensive parser function calls** | 500 per page | `#ifexist` calls beyond 500 produce errors |
| **Nodes in AST** | ~10,000,000 soft limit | Pages exceeding this may fail to render |
| **Template inclusion depth** | 40 levels | Deeply nested templates will fail to expand |

### How to Check Limits

```
action=parse&page=Albert_Einstein&prop=limitreportdata&format=json
```

Returns the `limitreport` with current usage vs. limits (key `0` = current
value, `1` = limit):

```json
{
 "parse": {
   "limitreportdata": [
     { "name": "limitreport-ppvisitednodes", "0": 11174, "1": 1000000 },
     { "name": "limitreport-postexpandincludesize", "0": 478489, "1": 2097152 },
     { "name": "limitreport-expensivefunctioncount", "0": 2, "1": 500 }
   ]
 }
}
```

> ⚠️ **Do NOT use `prop=modules` for this.** `prop=modules` returns the page's
> **ResourceLoader JS/CSS modules** (`ext.cite.ux-enhancements`, `mediawiki.page.media`, …),
> not Lua modules and not the limit report. Lua (Scribunto) module dependencies
> come from `prop=templates` filtered to `ns=828` (see SOP: Lua Modules above).
> The human-readable variant is `prop=limitreport`.

---

## SOP: Template Maintenance

### Creating a New Template

1. Create the page `Template:YourTemplateName`
2. Add the template code with parameter defaults
3. Add `<noinclude>{{Documentation}}</noinclude>` at the end
4. Create `Template:YourTemplateName/doc` with usage examples
5. Add categories to the doc page (`<includeonly>[[Category:Your template category]]</includeonly>`)
6. Create `Template:YourTemplateName/sandbox` for testing
7. Create `Template:YourTemplateName/testcases` for automated test cases

### Template Documentation (Doc Pages)

Every template should have a `/doc` subpage:

```wikitext
<!-- Template:YourTemplateName/doc -->
{{Documentation subpage}}
<!-- Description goes here -->
This template displays [purpose].

== Usage ==
{{YourTemplateName |param1= |param2= }}

== Example ==
{{YourTemplateName |param1=Hello |param2=World}}

== TemplateData ==
<templatedata>
{
  "description": "Template purpose",
  "params": {
    "param1": {
      "label": "Parameter 1",
      "description": "What this parameter does",
      "type": "string",
      "required": true
    },
    "param2": {
      "label": "Parameter 2",
      "description": "Another parameter",
      "type": "string",
      "required": false
    }
  }
}
</templatedata>

<includeonly>{{Sandbox other||
<!-- Categories below this line -->
[[Category:Your template category]]
}}</includeonly>
```

### Tracking Categories

Templates often use `<includeonly>` to add pages to maintenance categories:

```wikitext
<includeonly>{{#if:{{{url|}}}|<!-- OK -->|[[Category:Pages with missing URL]]}}</includeonly>
```

Common tracking categories:
- `Category:Pages with missing parameters` — required parameter omitted
- `Category:Pages using duplicate arguments in template calls` — same param used twice
- `Category:Pages with template errors` — template fails to render
- `Category:Wikipedia template protection` — protected templates

### Testing Templates

- **Sandbox:** `Template:Name/sandbox` — experimental changes without affecting production
- **Test cases:** `Template:Name/testcases` — parameter combinations with expected output
- **What links here:** `Special:WhatLinksHere/Template:Name` — pages using the template
- **Transclusion count:** `Special:PageInfo/Template:Name` — shows usage count
- **TemplateData:** Structured parameter documentation used by the Visual Editor

---

## SOP: Link Tracking for Template-Generated Content

`Special:RecentChangesLinked`, `Special:WhatLinksHere`, and `prop=links` read the
wiki's **link tables**, never the rendered HTML. A page can therefore *visibly*
list 20 pages that the change feeds believe do not exist.

**Symptom:** a dashboard or index page lists pages (via `{{Special:Prefixindex}}`,
a module, a template, or another dynamic construct), but "Related changes" on that
page returns nothing — or only changes to the few pages that also appear as
literal links.

### What gets recorded, and attributed to whom

| Construct | In a link table? | Attributed to |
|---|---|---|
| `[[Wikilink]]` in the page's own wikitext | ✅ `pagelinks` | that page |
| Link emitted by a parser tag/function placed **directly on the page** (e.g. `<dynamicpagelist>` on the page) | ✅ `pagelinks` | that page |
| Link inside a **transcluded template or Lua module** | ✅ — but | the **template/module**, not the including page (the includer only gets a `templatelinks` row) |
| **Transcluded special page** (`{{Special:Prefixindex}}`, `{{Special:RecentChanges}}`, `{{Special:CategoryTree}}`) | ❌ nowhere | — |
| Raw HTML `<a href>` built by an extension or JavaScript | ❌ | — |
| Links inside `<nowiki>`, HTML comments, or `<pre>` | ❌ | — |
| `[[Category:X]]` — **including when emitted by a transcluded template** | ✅ `categorylinks` | the **including page** (the opposite rule to plain links) |
| `[https://example.org …]` external link | ✅ `externallinks` (separate table; not usable for internal feeds) | that page |

Consequence worth remembering: a navbox template's links belong to the *template's*
link table, so one template edit reaches thousands of pages for **categories**
(cascade to the includer) but not for **links**. This is also why `WhatLinksHere`
on a target often lists the template rather than the articles that display the link.

### Diagnose in three calls

```bash
TITLE="Wikimedia Futures Lab/Dashboard/Experiment Tracker"
UA="MyTool/1.0 (https://example.org/me)"

# 1. What IS recorded for the page? (empty/minimal result = not link-tracked)
curl -s -H "User-Agent: $UA" \
  "https://meta.wikimedia.org/w/api.php?action=query&titles=${TITLE}&prop=links|categories|templates&pllimit=max&format=json"

# 2. Reproduce the symptom: count rendered change rows on Related changes
curl -s -H "User-Agent: $UA" \
  "https://meta.wikimedia.org/wiki/Special:RecentChangesLinked?target=${TITLE}&days=30&limit=50" | grep -c mw-changeslist-line
```

Compare (1) and (2) against the page's rendered output. If the visible list is far
larger than `prop=links`, the list comes from a construct in the table above that is
not tracked. Note that a **non-existent target returns HTTP 404**, not an empty
list — do not read that as "no changes".

### Recipe 1 — category anchor (general fix, self-maintaining)

1. Put `[[Category:Name]]` on every page in the list. For generated pages, add it to
   the **preload template** so future pages self-categorize; backfill existing pages
   with a bot run or JWB/AWB.
2. Point Related Changes at the category instead of the page:
   `https://{wiki}/wiki/Special:RecentChangesLinked?target=Category:Name&days=30&limit=100`
3. Verify membership landed (category links are applied by **deferred jobs**, so a
   new category can lag — a null edit on the page forces it):
   `https://{wiki}/w/api.php?action=query&list=categorymembers&cmtitle=Category:Name&format=json`

This works regardless of how the list is generated (prefixindex, DPL, module, bot),
which is why it is the general answer when "Related changes" must keep working.

### Recipe 2 — hidden DynamicPageList block (Related changes on the page itself)

Meta and the Wikinews projects run the legacy **DynamicPageList (Intersection)**;
its tag output *is* link-tracked. Keep the pretty display and add a hidden block
whose only job is to populate the page's link table:

```text
<div style="display:none">
<dynamicpagelist>
category=Name
count=100
mode=unordered
suppresserrors=true
</dynamicpagelist>
</div>
```

Constraints: category-driven only (no prefix/titlematch), output is cached, and it
will not be installed on further WMF wikis. Put it **on the page itself** — inside a
template, the links would be attributed to the template.

### Recipe 3 — feed from the API (no wiki edits at all)

Enumerate the list yourself, then ask for the changes per page and merge:

```python
import json, time, urllib.parse, urllib.request

UA = "MyTool/1.0 (https://example.org/me)"  # descriptive User-Agent is required
API = "https://meta.wikimedia.org/w/api.php"

def get(params):
    url = API + "?" + urllib.parse.urlencode(dict(params, format="json"))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read())

prefix = "Wikimedia Futures Lab/Dashboard/Experiment Tracker/"
pages, cont = [], {}
while True:
    data = get({"action": "query", "list": "allpages", "apprefix": prefix,
                "apnamespace": "0", "aplimit": "500", **cont})
    pages += [p["title"] for p in data["query"]["allpages"]]
    if "continue" not in data:
        break
    cont = data["continue"]

events = []
for title in pages:
    data = get({"action": "query", "list": "recentchanges", "rctitle": title,
                "rcprop": "title|timestamp|user|comment|sizes", "rclimit": "10",
                "rcdir": "older", "rcend": "2026-08-12T00:00:00Z"})
    events += data["query"]["recentchanges"]
    time.sleep(1)  # >=1s pacing outside Toolforge/WMCS

for event in sorted(events, key=lambda e: e["timestamp"], reverse=True)[:20]:
    print(event["timestamp"], event["title"], event["user"], event["comment"])
```

Personal variant needing no code: watch the pages and use `Special:Watchlist`
(30-day window) plus its RSS/Atom feed. Real-time variant: EventStreams filtered
client-side (see [wikimedia-eventstreams](../wikimedia-eventstreams/SKILL.md)).

### Pitfalls

- **Category lag.** `categorylinks` rows are written by deferred jobs; a freshly
  added category may not appear in Related changes for a moment. Force with a null
  edit, or wait for the job queue.
- **404 ≠ empty.** A Related changes target that does not exist returns 404 — check
  the target spelling before concluding there are no changes.
- **30-day horizon.** The UI defaults to 30 days; RSS/Atom feeds serve short windows
  only, so "all changes ever" needs the API or a database replica.
- **Template attribution surprise.** Links rendered by a transcluded template are
  recorded against the *template*: point Related changes at the template page only
  when every page in the list transcludes it.
- **Cached parser output.** DPL and other extension output is cached; changes to the
  underlying category may not re-render the page immediately.

---

## Tooling

This skill includes helper scripts, reference docs, and templates:

### 🔧 Expand Template (`scripts/expand-template.sh`)

Expand a template with parameters via the Action API, showing the fully rendered wikitext:

```bash
# Expand a simple template call
./scripts/expand-template.sh "Infobox_person" "name=Albert Einstein|birth_date=14 March 1879"

# Read template call from stdin
echo "{{Infobox_person|name=Test}}" | ./scripts/expand-template.sh -
```

### 🔧 Template Usage Lookup (`scripts/template-usage.sh`)

Find all pages using a template, with count and pagination:

```bash
# Show all pages using Template:Cn
./scripts/template-usage.sh "Cn"

# Show with namespaces and total count
./scripts/template-usage.sh "Infobox person" --count

# Limit results
./scripts/template-usage.sh "Stub" --limit 20
```

### 🔧 Inspect Template (`scripts/inspect-template.sh`)

Get comprehensive information about a template: source, protection, Lua dependencies, transclusion count, and tracking categories:

```bash
# Full inspection
./scripts/inspect-template.sh "Infobox person"

# Just check protection level
./scripts/inspect-template.sh "Infobox person" --protection

# Show source code only
./scripts/inspect-template.sh "Cite web" --source
```

### 📚 Parser Functions Reference (`references/parser-functions.md`)

Complete reference covering all parser functions with examples, performance notes, and common pitfalls.

### 📚 Magic Words Reference (`references/magic-words.md`)

Complete catalog of all magic words organized by category (behavior switches, variables, template-specific).

### 📚 Template Types Reference (`references/template-types.md`)

Full taxonomy of template types with examples, usage patterns, and Lua-backing information.

### 🐍 Template Inspector (`assets/template-inspector.py`)

Python script that fetches and analyzes a template's structure:

```bash
# Full analysis
python3 assets/template-inspector.py "Infobox person"

# Get parameters only
python3 assets/template-inspector.py "Infobox person" --parameters

# Show Lua module dependencies
python3 assets/template-inspector.py "Infobox settlement" --modules

# JSON output for programmatic use
python3 assets/template-inspector.py "Cite web" --format json
```

### 🐍 Template Scanner (`assets/template-scanner.py`)

Python script that scans a page for all template usage, classifying each template by type:

```bash
# Scan a Wikipedia article
python3 assets/template-scanner.py "Albert Einstein"

# Group by template type (infobox, citation, navbox, maintenance, etc.)
python3 assets/template-scanner.py "Berlin" --by-type

# Output as JSON
python3 assets/template-scanner.py "Python (programming language)" --format json

# Show Lua module usage
python3 assets/template-scanner.py "Berlin" --modules
```

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent and API patterns for template detection |
| **[wikipedia-page-anatomy](../wikipedia-page-anatomy/SKILL.md)** | Article structure — where templates appear (infoboxes, navboxes, citations) |
| **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** | AST-based template parsing with `mwparserfromhell` |
| **[wikipedia-citations](../wikipedia-citations/SKILL.md)** | Citation templates — the most common template type on Wikipedia |
| **[wikipedia-talk-page](../wikipedia-talk-page/SKILL.md)** | WikiProject banners on talk pages are templates |
| **[wikipedia-wikitables](../wikipedia-wikitables/SKILL.md)** | Table templates and wikitable generation |
| **[pywikibot](../pywikibot/SKILL.md)** | Bulk template operations (mass replacement, infobox harvesting) |

