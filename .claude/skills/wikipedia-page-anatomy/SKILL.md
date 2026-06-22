---
name: wikipedia-page-anatomy
description: Navigate and understand the structure of a Wikipedia article — infoboxes, categories, references, templates, navboxes, redirects, disambiguation, and protection levels
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["page structure", "article anatomy", "lead section", "first paragraph", "infobox", "categories", "navbox", "references", "templates"]
  - keywords: ["disambiguation", "disambiguation page", "DAB page", "ambiguous title", "disambig", "page type", "redirect"]
  - keywords: ["protection level", "page status", "edit protection", "semi-protected", "fully protected"]
last_verified: 2026-06-10
---

> ⚠️ **User-Agent required:** The search examples below use the Action API. All requests must include a descriptive `User-Agent` header or they will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.

> 💡 **Related skills for deeper analysis:**
> - **[wikipedia-templates](../wikipedia-templates/SKILL.md)** — Template taxonomy (infobox, navbox, maintenance, hatnote, citation) for classifying the templates found during structural analysis
> - **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** — AST-based wikitext parsing with `mwparserfromhell` for extracting and manipulating page elements programmatically
> - **[wikipedia-citations](../wikipedia-citations/SKILL.md)** — CS1/CS2 citation template reference for analyzing reference sections
> - **[wikipedia-categories](../wikipedia-categories/SKILL.md)** — Category system rules and API patterns for deeper category inspection

## SOP: Understanding Page Anatomy

A standard Wikipedia article follows this vertical layout, top to bottom:

```
┌─────────────────────────────────────┐
│  Lead section (unnamed)             │  ← First paragraph contains bold title and summary
├─────────────────────────────────────┤
│  {{Infobox person}}                 │  ← Right-aligned summary table
├─────────────────────────────────────┤
│  == Early life ==                   │  ← Body sections with `== Level 2 ==` headings
│  === Education ===                  │  ← Sub-sections with `=== Level 3 ===`
│  == Career ==                       │
├─────────────────────────────────────┤
│  == See also ==                     │  ← Bulleted list of related article links
│  == References ==                   │  ← `{{reflist}}` renders footnotes here
│  == Further reading ==              │
│  == External links ==               │
├─────────────────────────────────────┤
│  {{Navbox}}                         │  ← Navigation boxes
├─────────────────────────────────────┤
│  [[Category:Name]]                  │  ← Category bar
└─────────────────────────────────────┘
```

**The lead** is the **unnamed** section before the first `== Heading ==`. The first sentence states the subject in bold: `'''Subject name'''`. The lead summarizes the article in 2–4 paragraphs. No citations are required for facts restated from the body (WP:LEADCITE).

**Body sections** use `== Level 2 ==` for top-level sections and `=== Level 3 ===` for subsections. The table of contents is auto-generated from these headings.

**Appendices** appear after the body, in order: See also → Notes → References → Further reading → External links. Only References is required; the others are optional.

---

## SOP: Working with Infoboxes

An **infobox** is a right-aligned summary table at the top of an article that presents key facts in structured form. It is a template:

```wikitext
{{Infobox person
| name        = Albert Einstein
| birth_date  = {{Birth date|1879|03|14}}
| known_for   = [[General relativity]]
}}
```

**Common infobox types by topic:**

| Article Type | Template |
|-------------|----------|
| Person | `{{Infobox person}}`, `{{Infobox scientist}}` |
| Place | `{{Infobox settlement}}`, `{{Infobox country}}` |
| Event | `{{Infobox event}}`, `{{Infobox military conflict}}` |
| Media | `{{Infobox film}}`, `{{Infobox album}}`, `{{Infobox book}}` |
| Organization | `{{Infobox company}}`, `{{Infobox university}}` |

Some infoboxes are backed by **Lua modules** (e.g., `{{Infobox settlement}}`). They contain `{{#invoke:...}}` in the template source.

**How infoboxes differ from sidebars:** Infoboxes summarize facts about the current page's subject and are right-aligned at the top. Sidebars are navigational — they list related pages within a topic area.

**How to read infobox values:**
- **Wikitext** — fetch `action=raw` and parse with `mwparserfromhell` (see `wikimedia-wikitext` skill)
- **Parsoid HTML** — REST API `/v1/page/{title}/html` and extract `<table class="infobox">`
- **Page props** — `action=query&prop=pageprops` for the `wikibase-item` Q ID

> 💡 For programmatic extraction and modification, see the **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** skill.

---

## SOP: Reading and Using Categories

Categories group articles by topic and appear at the bottom of the page.

**Syntax:**
```wikitext
[[Category:Category name]]               ← No sort key (sorted by article title)
[[Category:Category name|Sort key]]      ← With sort key for custom ordering
```

**Sort key conventions:**
- Biographies: `[[Category:American physicists|Einstein, Albert]]` — sorts by last name
- Institutions: `[[Category:MIT| ]]` — space sorts before letters

**Category hierarchy:** Categories form a tree. Each category page has `[[Category:Parent category]]` linking it to its parent. Query via:

```
action=query&prop=categories&titles=Albert_Einstein&format=json
```

To find parent categories of a category, query the category page itself:
```
action=query&prop=categories&titles=Category:American_physicists&format=json
```

**Hidden categories** are marked with `__HIDDENCAT__` and do not appear in the visible category bar. They are used for maintenance tracking (e.g., `Category:Articles with unsourced statements`). Filter via API:

```
# Visible only
action=query&prop=categories&titles=Title&clshow=!hidden&format=json

# Hidden only
action=query&prop=categories&titles=Title&clshow=hidden&format=json
```

**Wikipedia vs. Commons categories:** These are independent systems. Wikipedia categories organize articles; Commons categories organize media files. A Wikipedia article may link to a Commons category via `{{Commons category|Name}}`.

---

## SOP: Understanding References and Citations

**Named references** allow reusing a citation without duplicating content:

```wikitext
Some text.<ref name="smith2020">{{cite book |last=Smith |title=...}}</ref>
Later text.<ref name="smith2020" />    ← Reuses the same footnote
```

The `{{reflist}}` tag renders all `<ref>` tags as a numbered list in the References section:
```wikitext
== References ==
{{reflist|30em}}    ← 30em sets column width
```

**Common citation templates:**

| Template | Best For | Key Parameters |
|----------|----------|----------------|
| `{{cite web}}` | Websites | `url`, `title`, `website`, `date`, `access-date` |
| `{{cite news}}` | Newspapers | `url`, `title`, `newspaper`, `date`, `author` |
| `{{cite book}}` | Books | `title`, `author`, `year`, `publisher`, `isbn` |
| `{{cite journal}}` | Academic papers | `title`, `author`, `journal`, `volume`, `pages`, `doi` |

**Always use template-based citations** over free-form `<ref>text</ref>`. Templates have consistent fields and enable bot-based metadata extraction.

**Bare URLs** (`<ref>https://example.com</ref>`) are discouraged per WP:BAREURL. Use `{{cite web}}` instead.

**Identifiers in citations:**

| ID | Example | Where Found |
|----|---------|-------------|
| DOI | `10.1000/xyz123` | Academic journals |
| PMID | `12345678` | Biomedical literature |
| ISBN | `978-0-262-52316-5` | Books |
| ISSN | `0040-165X` | Journals |

**Dead link detection:** Look for the `{{dead link}}` template in wikitext, or check whether the page is in `Category:All articles with dead external links`.

---

## SOP: Identifying and Reading Templates

Templates are reusable wiki pages transcluded via double braces:

```wikitext
{{Template name}}
{{Template name|param1=value1|param2=value2}}
```

They live in the `Template:` namespace (NS 10). Shortcuts like `{{cn}}` resolve to `Template:Cn`.

**Common maintenance templates:**

| Template | What It Signals | Location |
|----------|----------------|----------|
| `{{cn}}` / `{{citation needed}}` | A claim needs a source | After the statement |
| `{{better source}}` | The source is weak | After the citation |
| `{{POV}}` | Article may not be neutral | Top of article/section |
| `{{expand section}}` | Section is too short | Top of section |
| `{{dead link}}` | Citation URL no longer works | Inside the `<ref>` tag |
| `{{clarify}}` | Text is confusing or ambiguous | After the passage |
| `{{stub}}` | Article is very short | Bottom of article |

**How to detect templates via API:**
```
action=query&prop=templates&titles=Albert_Einstein&format=json
```

Returns all templates transcluded on the page, including infoboxes, navboxes, and maintenance templates.

**Transclusion** means the template content is not part of the page's raw wikitext — edits to the template update all pages that use it. Use `action=parse` or the REST API `/html` endpoint to see the fully rendered page.

> 💡 For safe, AST-based template manipulation, see the **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** skill.

---

## SOP: Recognizing Navigation Boxes

Navboxes are collapsible navigation templates at the very bottom of an article, below the appendices and above the categories:

```
┌─────────────────────────────────────────────────┐
│ ▼ [collapse] Part of a series on Physics         │
├─────────────────────────────────────────────────┤
│ Classical mechanics · Electromagnetism ·         │
│ Thermodynamics · Quantum mechanics · Relativity  │
└─────────────────────────────────────────────────┘
```

**How they differ from other components:**

| Component | Purpose | Location |
|-----------|---------|----------|
| **Infobox** | Key facts about THIS article | Top-right |
| **Navbox** | Links to RELATED articles in the same topic | Bottom |
| **Category** | Automatic grouping by topic | Bottom (after navboxes) |

**Detect navboxes via API:** `action=query&prop=templates&titles=Title` — filter for templates with "navbox" in the name, or look for the `navbox` CSS class in rendered HTML.

---

## SOP: Handling Redirects and Disambiguation

### Redirects

A redirect page sends the reader to another article:

```wikitext
#REDIRECT [[Target page]]
```

**API resolution:**
```
action=query&titles=Einstein&redirects=1&format=json
```
The response includes a `redirects` array mapping the source title to the target. The `pages` section contains the final destination.

### Disambiguation Pages

A disambiguation page lists multiple articles sharing the same or similar title. Identified by the `{{disambiguation}}` template (or variants like `{{geodis}}`, `{{hndis}}`, `{{schooldis}}`).

**API detection (preferred — REST API):**
```
https://en.wikipedia.org/api/rest_v1/page/summary/Title
```
Check the `type` field in the JSON response: `"type": "disambiguation"` indicates a disambiguation page, `"type": "standard"` indicates a regular article. This is simpler than parsing categories and works across all language editions.

**API detection (fallback — Action API):**
```
action=query&prop=categories&titles=Title&format=json
```
Check if any category matches `*disambiguation*` (e.g., `Category:Disambiguation pages`).

**Cross-lingual detection (when you only have the page title):**

If you're working with interlanguage links from the Action API and don't want to make additional API calls, disambiguation pages can often be identified by known suffixes in the page title. This is useful for filtering language editions before fetching their content:

```python
_DISAMBIG_PATTERNS = (
    '(disambiguation)',            # English
    '(egyértelműsítő lap)',        # Hungarian
    '(desambiguación)',            # Spanish
    '(Begriffsklärung)',           # German
    '(homonymie)',                 # French
    '(disambigua)',                # Italian
    '(消歧義)', '(消歧义)',         # Chinese
    '(曖昧さ回避)',                  # Japanese
    '(동음이의)', '(동음이의어)',      # Korean
    '(anlam ayrımı)',              # Turkish
    '(неоднозначность)',           # Russian
    '(توضيح)',                     # Arabic
    '(ابهام‌زدایی)',               # Persian
)

def is_disambiguation_title(title):
    return any(p in title for p in _DISAMBIG_PATTERNS)
```

**When to follow vs. stop:**

| Scenario | Action |
|----------|--------|
| User provided a redirect title | Follow to the canonical page |
| User provided a disambiguation page | Ask which specific meaning, or list the options |
| Searching across redirects | Use `redirects=1` in the API call |

---

## SOP: Checking Protection Levels and Page Status

Wikipedia uses padlock icons to indicate protection:

| Icon | Level | Who Can Edit | Typical Reason |
|------|-------|-------------|----------------|
| None | Open | All users | Default |
| 🛡️ Grey | Semi-protected | Autoconfirmed (4 days, 500 edits) | Persistent vandalism |
| 🔵 Blue | Extended confirmed | 30 days, 500 edits | Disputes, BLP concerns |
| 🔴 Red | Full | Administrators only | Legal, edit wars |

**API check:**
```
action=query&prop=info&inprop=protection&titles=Title&format=json
```

Response includes a `protection` array with `type`, `level`, and `expiry`.

**Page existence check:**
```
action=query&titles=Title&format=json
```
- Exists: numeric `pageid` in the response
- Missing: `"missing": ""` with negative `pageid`
- Invalid: `"invalid": ""`

---

## SOP: Accessing Page Data via API

| Task | API Method | Example |
|------|-----------|---------|
| Get raw wikitext | `action=raw` | `https://en.wikipedia.org/w/index.php?title=Albert_Einstein&action=raw` |
| Get parsed HTML | `action=parse` | `action=parse&page=Albert_Einstein&prop=text&format=json` |
| Get page info (protection, length, redirect status) | `prop=info` | `action=query&prop=info&titles=Albert_Einstein&format=json` |
| Get categories | `prop=categories` | `action=query&prop=categories&titles=Albert_Einstein&format=json` |
| Get templates used | `prop=templates` | `action=query&prop=templates&titles=Albert_Einstein&format=json` |
| Get links on page | `prop=links` | `action=query&prop=links&titles=Albert_Einstein&format=json` |
| Resolve redirect | `redirects=1` | `action=query&titles=Einstein&redirects=1&format=json` |
| Get rendered HTML (REST) | `GET /v1/page/{title}/html` | `https://en.wikipedia.org/api/rest_v1/page/Albert_Einstein/html` |

---

## Relationship to Other Skills

- **wikipedia-en-biography-writing** — This skill is a prerequisite: understanding page anatomy is necessary before drafting, editing, or auditing a biography.
- **wikipedia-talk-page** — Complements this skill by covering the discussion side of a page.
- **wikipedia-edit-history** — Complements this skill by covering the revision history side of a page.
- **wikimedia-wikitext** — For programmatic parsing and manipulation of infoboxes, templates, and other page components.
- **wikimedia-api-access** — The page anatomy operations rely on the Action API; defer to this skill for User-Agent, rate limiting, and error handling.
- **[wikipedia-wikiprojects](../wikipedia-wikiprojects/SKILL.md)** — WikiProjects assess articles and organize topic-area work; their banners appear on talk pages.

---

## Tooling

### 🔧 Infobox Extractor (`scripts/extract-infobox.sh`)

Extract infobox field names and values from any Wikipedia article. Handles nested templates and multi-line parameters via brace-depth tracking.

```bash
./scripts/extract-infobox.sh "Albert Einstein"
./scripts/extract-infobox.sh "Python (programming language)" --project fr.wikipedia
./scripts/extract-infobox.sh "Berlin" --json
```

### 🔧 Page Summary (`scripts/page-summary.sh`)

Fetches a compact structural overview of any article — infobox type, protection level, redirect/disambiguation status, visible and hidden categories, template count, and WikiProject assessment banners from the talk page.

```bash
./scripts/page-summary.sh "Albert Einstein"
./scripts/page-summary.sh "Python (programming language)" --json
```

### 📚 Template Reference (`references/template-reference.md`)

Quick reference for common infobox templates (person, scientist, settlement, film, company, etc.), citation templates (`cite web`, `cite book`, `cite journal`), and maintenance templates (`{{cn}}`, `{{POV}}`, `{{stub}}`, etc.).

### 🐍 Wikitext Utilities (`assets/wikitext_utils.py`)

Python library used by the shell scripts. Provides `fetch_wikitext()` and `extract_infobox()` functions with proper brace-depth tracking.

### 🐍 Page Auditor (`assets/page-audit.py`)

Fetch a Wikipedia article and report on all its structural components: infobox type and parameters, visible and hidden categories, templates by category (infobox, navbox, maintenance), protection level, redirect/disambiguation status, WikiProject banners from the talk page, reference/citation count, and section outline.

```bash
pip install requests   # required for this tool
python3 assets/page-audit.py "Albert Einstein"
python3 assets/page-audit.py "Python (programming language)" --project fr.wikipedia --json
```

> **Note:** The shell scripts (`extract-infobox.sh`, `page-summary.sh`) and `wikitext_utils.py` use only Python standard library — no pip install needed. The `page-audit.py` requires `requests`.
