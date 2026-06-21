---
name: mediawiki-translate-extension
description: Work with the Translate extension for multilingual wiki content — marking pages for translation, writing translatable templates, using #timef for locale-aware dates, managing language subpages, and building i18n-aware navigation
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access, wikipedia-templates]
skill_discovery_hints:
  - keywords: ["Translate extension", "page translation", "translatable", "<translate>", "translation unit", "language subpage"]
  - keywords: ["Special:MyLanguage", "#timef", "translation memory", "message group", "fuzzy translation"]
last_verified: 2026-06-10
---

> ⚠️ **User-Agent required:** The API examples below hit Wikimedia endpoints. All requests must include a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.
>
> 📖 **Prerequisites:** For general template syntax and parser functions, see **[wikipedia-templates](../wikipedia-templates/SKILL.md)**. For navigation patterns that use `Special:MyLanguage/`, see **[mediawiki-page-navigation](../mediawiki-page-navigation/SKILL.md)**. For styling translatable templates, see **[wikimedia-page-styling](../wikimedia-page-styling/SKILL.md)**.

---

## Table of Contents

1. [What the Translate Extension Is](#what-the-translate-extension-is)
2. [Two Translation Modes](#two-translation-modes)
3. [Page Translation: Marking Content for Translation](#page-translation-marking-content-for-translation)
4. [Translation Units and `<translate>` Tags](#translation-units-and-translate-tags)
5. [The `<languages/>` Bar](#the-languages-bar)
6. [Language Subpages (`/en`, `/fi`, `/ko`, etc.)](#language-subpages-en-fi-ko-etc)
7. [Translation Variables (`<tvar>`)](#translation-variables-tvar)
8. [`Special:MyLanguage/` — Language-Aware Links](#specialmylanguage--language-aware-links)
9. [`#timef` — Locale-Aware Date Formatting](#timef--locale-aware-date-formatting)
10. [Making Templates Translatable](#making-templates-translatable)
11. [The `{{TRANSLATABLEPAGE}}` Magic Word](#the-translatablepage-magic-word)
12. [Page Translation Workflow](#page-translation-workflow)
13. [Message Groups and Translation Memory](#message-groups-and-translation-memory)
14. [Best Practices](#best-practices)
15. [Troubleshooting](#troubleshooting)
16. [Reference Links](#reference-links)

---

## What the Translate Extension Is

The **Translate extension** is MediaWiki's built-in system for creating **multilingual content**. It is installed on Meta, mediawiki.org, Commons, and many other Wikimedia wikis, but **not on Wikipedia** (which uses interlanguage links instead).

### What It Solves

Without the Translate extension, multilingual wikis faced these problems:

| Problem | Without Translate | With Translate |
|---|---|---|
| **How to display multiple languages** | Manual copy-paste, hard to maintain | Automatic language subpages + `<languages/>` bar |
| **How to track completion** | No visibility | Colored progress indicators per language |
| **What happens when source changes** | Translations go out of sync silently | Marked as "outdated" (fuzzy) until reviewed |
| **How to format dates per locale** | Hard-coded formats | `#timef` — auto-formats to user's language |
| **How to link to translated pages** | Manual per-language links | `Special:MyLanguage/` — follows user's preference |

### Where It's Used

| Wiki | Translate Extension | Purpose |
|---|---|---|
| **meta.wikimedia.org** | ✅ Yes | Cross-project coordination docs, multilingual community pages |
| **commons.wikimedia.org** | ✅ Yes | Multilingual file descriptions |
| **mediawiki.org** | ✅ Yes | Software documentation in dozens of languages |
| **en.wikipedia.org** | ❌ No | Uses interlanguage links instead |
| **translatewiki.net** | ✅ Yes (primary) | Software interface translation (MediaWiki, extensions) |
| **Toolforge** | ✅ Yes | Tool documentation |

---

## Two Translation Modes

The Translate extension has two distinct modes:

### 1. Page Translation

Content is written in one language (usually English) and marked for translation with `<translate>` tags. Translation administrators approve the page, and translators can translate each unit through the Special:Translate interface. This is what AvoinGLAM pages use.

**Best for:** Long-form content, documentation, community pages that need human-quality translation.

### 2. Unstructured Element Translation (Interface Messages)

Individual messages are defined as wiki pages in the MediaWiki namespace and translated via the same interface. Used for site UI and template messages.

**Best for:** Template labels, UI strings, small snippets.

This skill focuses on **Page Translation**, which is what the AvoinGLAM pages use.

---

## Page Translation: Marking Content for Translation

### The Basic Markup

To make a page translatable, wrap translatable content in `<translate>` tags:

```wikitext
<languages />
<translate>
== Introduction == <!--T:1-->
Welcome to the AvoinGLAM project.

== Mission == <!--T:2-->
Our goal is to promote Open Access to cultural heritage.
</translate>
```

### Step-by-Step Process

1. **Write the page** in the base language (usually English), wrapping translatable content in `<translate>... </translate>`

2. **Add `<languages />`** at the top (this shows the language selector bar)

3. **Add translation unit markers** — `<!--T:1-->`, `<!--T:2-->`, etc. — after each heading or paragraph. These can be auto-generated when the page is marked for translation.

4. **Request translation marking** — a translation administrator uses `Special:PageTranslation` to mark the page

5. **Translators translate** via `Special:Translate` — each unit gets translated independently

6. **The system creates language subpages** — `/en`, `/fi`, `/fr`, etc.

### What Gets Wrapped in `<translate>`

Only the **translatable content** goes inside `<translate>` tags. Things that should NOT be translated:

- Template calls (but their **labels** should be translatable — see below)
- File names
- URLs and links (but link **display text** should be translatable)
- Numbers, dates in fixed formats
- Code examples

### Omitting Content from Translation

Content outside `<translate>` tags is **page-global** — it appears on all language variants unchanged:

```wikitext
<languages />
{{Project/Navigation}}

<translate><!--T:1-->
Welcome to our project.
</translate>

[[:Category:Project]]    ← Categories are page-global, outside translate
```

---

## Translation Units and `<translate>` Tags

### Translation Units

A **translation unit** is the smallest piece of content that can be translated independently. Each unit gets a unique identifier (`<!--T:1-->`).

```wikitext
<translate>
== Heading == <!--T:1-->
This is a paragraph. It is one translation unit. <!--T:2-->

This is another paragraph. It is a separate unit. <!--T:3-->
</translate>
```

**Rules for translation units:**
- Each paragraph, heading, or list item is typically one unit
- Units are separated by blank lines
- Every unit should have a `<!--T:N-->` marker after it
- The markers are auto-generated when the page is first marked for translation

### Headings

Headings inside `<translate>` become their own translation units:

```wikitext
<translate>
== Contact us == <!--T:10-->
Reach us at example@example.org. <!--T:11-->
</translate>
```

The heading is unit 10, the paragraph is unit 11.

### Lists

List items can be individual units:

```wikitext
<translate>
Our activities include: <!--T:20-->
* Workshops <!--T:21-->
* Hackathons <!--T:22-->
* Online events <!--T:23-->
</translate>
```

### Mixed Content

Content can be mixed inside and outside `<translate>` tags, but each section must be a complete block:

```wikitext
<translate><!--T:30-->
This paragraph is translatable.
</translate>

{{Some template that should not be translated}}

<translate><!--T:31-->
This paragraph is also translatable.
</translate>
```

---

## The `<languages/>` Bar

### Placement

Place `<languages />` at the **very top** of the page, before any content:

```wikitext
<languages />
{{Project/Navigation}}

<translate>
...
</translate>
```

### Appearance

The bar shows all available translations with colored progress indicators:

```
Languages: English ✅   Finnish ✅   French 🔵   Arabic 🟡   German 🔴
```

| Color | Meaning |
|---|---|
| ✅ Green | 100% translated and up-to-date |
| 🔵 Blue | 100% translated but some units are outdated (fuzzy) |
| 🟡 Yellow/Orange | Partially translated |
| 🔴 Red | Not translated at all |

### No `<languages/>` at the Bottom

You only need one `<languages />` tag at the top — do not add it to the bottom.

### Language Bar for Templates

For templates that are translated (like navigation templates), place `<languages />` inside `<noinclude>` so it only appears on the template page itself, not when transcluded:

```wikitext
<noinclude><languages /></noinclude>
<templatestyles src="Project/style.css" />
<translate>... translatable template content ...</translate>
```

---

## Language Subpages (`/en`, `/fi`, `/ko`, etc.)

### How They Are Created

When a page is marked for translation, the system automatically creates language subpages:

```
AvoinGLAM                          ← Base page (contains the translatable source)
AvoinGLAM/en                       ← English translation
AvoinGLAM/fi                       ← Finnish translation
AvoinGLAM/ko                       ← Korean translation
```

### The Base Page vs. Translated Pages

- The **base page** (no language suffix) contains the **source text** with `<translate>` tags
- Language subpages contain **only the translated text** for that language
- When you view the base page, you see the source language (usually English) by default
- When you view a variant like `/fi`, you see the Finnish translation
- The `<languages />` bar on the base page links to all variants

### Language Template Subpages

Language subpages work for **templates** too. The AvoinGLAM navigation template has:

```
Template:AvoinGLAM/Main navigation          ← Source (with <translate> tags)
Template:AvoinGLAM/Main navigation/en       ← English
Template:AvoinGLAM/Main navigation/fi       ← Finnish
Template:AvoinGLAM/Main navigation/ko       ← Korean
Template:AvoinGLAM/Main navigation/ar       ← Arabic
Template:AvoinGLAM/Main navigation/zh       ← Chinese
```

### How the Translation System Decides Which Language to Show

1. Check if a subpage matching the user's interface language exists
2. If not, check the fallback language chain (e.g., `fi` → `en`)
3. If no translation exists, show the source page

This is why `Special:MyLanguage/` is important — it triggers this fallback chain.

### Working with Language Subpages

**Do NOT manually create language subpages.** They are created and managed by the Translate extension's page translation system. Editing them directly is possible but will be overwritten the next time a translator updates through the interface.

---

## Translation Variables (`<tvar>`)

`<tvar>` variables let you embed **non-translatable content** inside a translation unit while keeping the surrounding text translatable.

### Basic Syntax

```wikitext
<translate><!--T:40-->
Welcome to <tvar name="project">{{SITENAME}}</tvar>. 
Our website is at <tvar name="url">https://example.org</tvar>.
</translate>
```

In the translation interface, translators see:

```
Welcome to $project. Our website is at $url.
```

They translate the sentence but the `$project` and `$url` placeholders stay intact.

### Common Uses for `<tvar>`

| Use | Example |
|---|---|
| **Magic words** | `<tvar name="year">{{CURRENTYEAR}}</tvar>` |
| **Template calls** | `<tvar name="count">{{PAGESINCATEGORY:Events}}</tvar>` |
| **URLs** | `<tvar name="link">https://example.com</tvar>` |
| **Numbers/statistics** | `<tvar name="members">42</tvar>` |
| **Special characters** | `<tvar name="arrow">→</tvar>` |
| **Formulas** | `<tvar name="formula">E=mc²</tvar>` |

### In Templates

For template labels that include parameters:

```wikitext
<translate><!--T:50-->
Join the <tvar name="group">{{{groupname|}}}</tvar> community.
</translate>
```

### Best Practices for `<tvar>`

- **Use descriptive names** — `name="project"` not `name="1"` — so translators understand what they represent
- **Wrap only the dynamic part** — not the entire sentence
- **Avoid `<tvar>` inside links** — use the link text approach instead (see below)

---

## `Special:MyLanguage/` — Language-Aware Links

`Special:MyLanguage/` is a redirect page that follows the user's language preference.

### How It Works

```wikitext
[[Special:MyLanguage/AvoinGLAM/Past activities|Past activities]]
```

1. The user clicks the link
2. Special:MyLanguage checks the user's interface language (e.g., `fi`)
3. It redirects to `AvoinGLAM/Past activities/fi` if that translation exists
4. If not, it falls back to the base page (usually English)

### Why It Matters

Without `Special:MyLanguage/`, a Finnish reader clicking "Past activities" would always go to the English page. With it, they land on the Finnish translation if available.

### Where to Use It

- **Every link in navigation menus** — ensures navigation stays in the user's language
- **Internal links on translatable pages** — keeps users in their language context
- **Links in templates** — especially navigation, infoboxes, and banners

### Using It in Templates

```wikitext
* [[Special:MyLanguage/AvoinGLAM|<translate><!--T:1--> AvoinGLAM</translate>]]
* [[Special:MyLanguage/AvoinGLAM/{{CURRENTYEAR}}|<translate><!--T:2--> This year</translate>]]
```

### What NOT to Use It For

- Links to **Wikipedia** pages — use normal interwiki links like `[[w:en:Page|Page]]`
- Links to **files** on Commons — files are not translated this way
- **Category links** — `Special:MyLanguage/` doesn't work with category syntax

---

## `#timef` — Locale-Aware Date Formatting

`#timef` is a parser function provided by the Translate extension that formats dates according to the **user's interface language**.

### Basic Syntax

```wikitext
{{#timef:2024-05-06|date}}
```

| User Language | Output |
|---|---|
| **en** (English) | 6 May 2024 |
| **fi** (Finnish) | 6. toukokuuta 2024 |
| **fr** (French) | 6 mai 2024 |
| **de** (German) | 6. Mai 2024 |
| **ar** (Arabic) | ٦ مايو ٢٠٢٤ |
| **ko** (Korean) | 2024년 5월 6일 |

### Format Options

| Format | Example (English) | Example (Finnish) |
|---|---|---|
| `date` | 6 May 2024 | 6. toukokuuta 2024 |
| `time` | 14:30 | 14:30 |
| `both` | 6 May 2024 14:30 | 6. toukokuuta 2024 14:30 |
| `dmy` | 6 May 2024 | 6. toukokuuta 2024 |
| `mdy` | May 6, 2024 | toukokuuta 6, 2024 |
| `ymd` | 2024 May 6 | 2024 toukokuuta 6 |
| `iso` | 2024-05-06 | 2024-05-06 (iso is always the same) |

### Using `#timef` with Date Ranges

In the AvoinGLAM navigation template, `#timef` is used to display date ranges:

```wikitext
{{#timef:{{{startdate|}}}|date}}
{{#if: {{{enddate|}}}|–{{#timef:{{{enddate|}}}|date}}}}
```

This produces:
- English: `6 May 2024 – 7 May 2024`
- Finnish: `6. toukokuuta 2024 – 7. toukokuuta 2024`

### Full Date-Time Display Pattern

```wikitext
{{{location|}}} {{#timef:{{{startdate|}}}|date}}
{{#if: {{{starttime|}}}|• {{{starttime|}}}
}}{{#if: {{{enddate|}}}|–
}}{{#if: {{{enddate|}}}|
{{#timef:{{{enddate|}}}|date}}
}}{{#if: {{{endtime|}}}|{{{endtime|}}}
}} {{{timezone|}}}
```

### Important: `#timef` Only Works on Translatable Pages

`#timef` formats dates based on the **language of the (translatable) page** that contains it. On non-translatable pages, it falls back to `#time` behavior. This means:

- ✅ Works in templates that are transcluded on translatable pages
- ✅ Works in navigation templates that are part of a translatable project
- ❌ Does NOT work for raw `#timef` calls on non-translatable pages

### Related: `#dateformat`

`#dateformat` is another parser function from the Translate extension that formats dates according to the wiki's content language:

```wikitext
{{#dateformat:2024-05-06|dmy}}
```

This is less commonly used than `#timef` because it doesn't adapt to the user's language.

### Related: `{{#language:...}}`

The `#language` parser function returns the language name in a given language:

```wikitext
{{#language:fi}}    → "suomi" (in Finnish context)
{{#language:fi|en}} → "Finnish" (in English context)
{{#language:fr|en}} → "French"
```

---

## Making Templates Translatable

Templates can be made translatable so that their labels, navigation text, and UI strings appear in the user's language.

### Wrapping Labels in `<translate>`

```wikitext
<noinclude><languages /></noinclude>
<templatestyles src="Project/style.css" />

<div class="menu">
* [[Special:MyLanguage/AvoinGLAM|<translate><!--T:1--> AvoinGLAM</translate>]]
* [[Special:MyLanguage/AvoinGLAM/{{CURRENTYEAR}}|<translate><!--T:2--> This year</translate>]]
* [[Special:MyLanguage/AvoinGLAM/Past activities|<translate><!--T:4--> Past activities</translate>]]
</div>
```

### Template Parameters with Translatable Labels

When a template parameter expects a label, you can provide it inline:

```wikitext
{{Project/Box
| title = <translate><!--T:5--> Join our community</translate>
| intro = <translate><!--T:6--> We invite you to participate.</translate>
}}
```

Or use parameters with defaults:

```wikitext
{{Project/Box
| title = <translate><!--T:5--> Join our community</translate>
| intro = {{{intro|<translate><!--T:6--> We invite you to participate.</translate>}}}
}}
```

### Best Practice: Separate Label Templates

For complex projects, create a dedicated string template:

```wikitext
<!-- Template:Project/Labels -->
<translate>
<!--T:1--> AvoinGLAM
<!--T:2--> This year
<!--T:4--> Past activities
</translate>
```

And reference it in your navigation template:

```wikitext
{{#if: {{{show_join|}}}
| [[Special:MyLanguage/Project/Join|{{Project/Labels|join}}]]
}}
```

### What NOT to Wrap in `<translate>`

```wikitext
<!-- ❌ WRONG: Wrapping the entire template call -->
<translate>{{Project/Navigation}}</translate>

<!-- ✅ RIGHT: Only wrap the labels inside the template -->
{{Project/Navigation|title=<translate><!--T:1--> Welcome</translate>}}
```

---

## The `{{TRANSLATABLEPAGE}}` Magic Word

`{{TRANSLATABLEPAGE}}` returns the title of the translatable page that contains it. It is useful in templates that are transcluded **on translatable pages**.

### Usage

```wikitext
{{fullurl:{{TRANSLATABLEPAGE}}|veaction=edit}}
```

This generates an edit link for the translatable page, regardless of whether the current view is `/en`, `/fi`, or the base page.

### Common Pattern: Edit Button on Translatable Content

```wikitext
<span class="editbutton">
[[File:OOjs UI icon edit-ltr.svg|12px|link=
  {{fullurl:{{TRANSLATABLEPAGE}}|veaction=edit}}
]]
</span>
```

This is used in the AvoinGLAM log entry template to ensure the edit button always targets the source page, not the translation variant.

### Fallback

If `{{TRANSLATABLEPAGE}}` is used on a non-translatable page, it returns nothing. Always wrap in a conditional:

```wikitext
{{#if: {{TRANSLATABLEPAGE}}
| [[File:edit.svg|link={{fullurl:{{TRANSLATABLEPAGE}}|action=edit}}]]
}}
```

---

## Page Translation Workflow

### For Content Authors (Non-Administrators)

1. **Write the content** in the base language, wrapping content in `<translate>` tags
2. **Add `<languages />`** at the top
3. **Add translation unit markers** — either manually (`<!--T:1-->`) or skip them (the system auto-generates when the page is marked)
4. **Request marking** — add the page to a queue or ask a translation administrator

### For Translation Administrators

1. **Mark the page** at `Special:PageTranslation`
2. **Review the translation units** — the system parses `<translate>` tags and shows each unit
3. **Approve the page** for translation — this creates the unit structure
4. **Monitor translations** — check for outdated (fuzzy) units

Main page: [Help:Extension:Translate/Page translation administration](https://www.mediawiki.org/wiki/Help:Extension:Translate/Page_translation_administration)

### For Translators

1. **Go to `Special:Translate`**
2. **Select the page group** (e.g., "AvoinGLAM")
3. **Choose your language** (e.g., "Finnish")
4. **Translate each unit** — the interface shows the source text and a text box
5. **Save** — the translation is live immediately but marked as "up-to-date"
6. **Repeat for other units** — progress is tracked automatically

### When the Source Changes

1. Author edits a translation unit on the base page
2. That unit is automatically marked as **outdated (fuzzy)** for all translations
3. Translators see the fuzzy unit highlighted in `Special:Translate`
4. They update the translation and save
5. The unit is no longer fuzzy

---

## Message Groups and Translation Memory

### Message Groups

A **message group** is a collection of translation units. For page translation, one page = one message group. They can be organized into **aggregate groups** for larger projects:

```
AvoinGLAM (aggregate group)
├── AvoinGLAM (page group)
├── AvoinGLAM/Past activities (page group)
├── AvoinGLAM/Main navigation (page group)
└── AvoinGLAM/style.css (page group — CSS is NOT translatable)
```

### Translation Memory

The Translate extension uses **translation memory** (TM) to suggest translations:
- When a translator translates a unit, it's stored in TM
- When similar text appears elsewhere, TM suggests the previous translation
- TM suggestions include a match percentage

### Quality Assurance Features

| Feature | Description |
|---|---|
| **Translation review** | Translations can be marked as "reviewed" |
| **Validation** | Checks for missing variables, unbalanced tags |
| **Pre-translation** | Auto-fill from TM for high-match units |
| **Consistency checks** | Flags inconsistent translations of the same source text |

---

## Best Practices

### Writing for Translation

| Do | Don't |
|---|---|
| ✅ Write short, complete sentences | ❌ Write long paragraphs with multiple ideas |
| ✅ Use `<!--T:N-->` markers after each unit | ❌ Put everything in one giant `<translate>` block |
| ✅ Keep sentences self-contained | ❌ Use "As mentioned above" (direction is language-dependent) |
| ✅ Use `<tvar>` for numbers, URLs, magic words | ❌ Embed formatting in translated text |
| ✅ Use `Special:MyLanguage/` for internal links | ❌ Hard-code language-specific links |

### Template Design for Translation

| Pattern | Best Practice |
|---|---|
| **Navigation** | Wrap menu labels in `<translate>`, use `Special:MyLanguage/` for links |
| **Infoboxes** | Make label parameters translatable with defaults |
| **Buttons** | Keep button text short, wrap in `<translate>` |
| **Dates** | Use `{{#timef:...}}` not `{{#time:...}}` |
| **Banners** | Use `<tvar>` for dynamic content like attendee counts |

### Translation Completion Strategy

1. **Always maintain English** as the source language
2. **Prioritize navigation templates** — these affect user experience most
3. **Translate high-visibility pages first** (main page, about page)
4. **Translate templates' UI strings** independently from page content
5. **Use `#timef` for all dates** — it costs nothing and improves UX for all languages

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---|---|---|
| **`<languages />` bar not showing** | Page hasn't been marked for translation | Request marking at `Special:PageTranslation` |
| **`#timef` not formatting dates** | Page is not translatable or not in a translatable context | Ensure the page has `<translate>` tags and is marked |
| **`Special:MyLanguage/` not working** | No translation subpage exists for the target page | Create the translation or check the fallback |
| **Template labels not translating** | Labels not wrapped in `<translate>` | Add `<translate>` tags around labels |
| **Translation units not updating** | Source page was edited without updating the translation | Re-mark the page or ask an admin |
| **`{{TRANSLATABLEPAGE}}` returns nothing** | Page is not translatable | Check that the page has been marked for translation |
| **Broken `<tvar>` in translation** | Variable name doesn't match the source | Check for typos in `name="..."` |
| **Language subpage shows source text** | No translation exists yet | The system falls back to source when no translation is available |

### Debugging Translation Status

```bash
# Check if a page is translatable and get its message group
curl -s "https://meta.wikimedia.org/w/api.php?action=query&prop=translationinfo&titles=AvoinGLAM/Past%20activities&format=json" \
  -H "User-Agent: MyTool/1.0"
```

```bash
# List available translations for a page
curl -s "https://meta.wikimedia.org/w/api.php?action=query&prop=langlinks&titles=AvoinGLAM/Past%20activities&format=json" \
  -H "User-Agent: MyTool/1.0"
```

---

## Reference Links

| Resource | URL |
|---|---|
| Translate extension page | [mediawiki.org/wiki/Extension:Translate](https://www.mediawiki.org/wiki/Extension:Translate) |
| Help:Extension:Translate | [mediawiki.org/wiki/Help:Extension:Translate](https://www.mediawiki.org/wiki/Help:Extension:Translate) |
| Page translation administration | [mediawiki.org/wiki/Help:Extension:Translate/Page_translation_administration](https://www.mediawiki.org/wiki/Help:Extension:Translate/Page_translation_administration) |
| Translation best practices | [mediawiki.org/wiki/Help:Extension:Translate/Translation_best_practices](https://www.mediawiki.org/wiki/Help:Extension:Translate/Translation_best_practices) |
| Unstructured element translation | [mediawiki.org/wiki/Help:Extension:Translate/Unstructured_element_translation](https://www.mediawiki.org/wiki/Help:Extension:Translate/Unstructured_element_translation) |
| `Special:MyLanguage` | [mediawiki.org/wiki/Help:Special_MyLanguage](https://www.mediawiki.org/wiki/Help:Special_MyLanguage) |
| `#timef` parser function | [mediawiki.org/wiki/Help:Extension:Translate/Page_translation_example](https://www.mediawiki.org/wiki/Help:Extension:Translate/Page_translation_example) |
| Translation API | [mediawiki.org/wiki/Help:Extension:Translate/API](https://www.mediawiki.org/wiki/Help:Extension:Translate/API) |
| Special:Translate on Meta | [meta.wikimedia.org/wiki/Special:Translate](https://meta.wikimedia.org/wiki/Special:Translate) |
| Skill: Templates | [wikipedia-templates](../wikipedia-templates/SKILL.md) |
| Skill: Navigation | [mediawiki-page-navigation](../mediawiki-page-navigation/SKILL.md) |
| Skill: Page styling | [wikimedia-page-styling](../wikimedia-page-styling/SKILL.md) |
| Skill: API access | [wikimedia-api-access](../wikimedia-api-access/SKILL.md) |

---

## Tooling

This skill includes helper scripts, reference docs, and template code for working with translated pages.

### 🔧 Translation Status Checker (`scripts/translation-status.sh`)

Check the translation status of a translatable page — available languages, completion percentages, and fuzzy (outdated) units:

```bash
# Show translation status for a page
./scripts/translation-status.sh "AvoinGLAM/Past activities" --wiki meta

# Show all languages with completion percentages
./scripts/translation-status.sh "AvoinGLAM" --languages

# Show only incomplete translations
./scripts/translation-status.sh "Project/Page" --incomplete
```

### 🔧 Extract Translatable Strings (`scripts/extract-translatable-strings.sh`)

Extract all `<translate>` sections and their translation unit IDs from a page or template:

```bash
# Show all translatable strings with their T: markers
./scripts/extract-translatable-strings.sh "AvoinGLAM/Main navigation" --wiki meta

# Show just the string IDs and their source text (no markup)
./scripts/extract-translatable-strings.sh "Template:Project/Navigation" --ids

# Show tvar variables used
./scripts/extract-translatable-strings.sh "Template:Project/Banner" --tvars
```

### 📚 Translate Parser Functions Reference (`references/translate-parser-functions.md`)

Complete reference for Translate extension parser functions:
- `#timef` — locale-aware date formatting (all format options, examples across 10+ languages)
- `#dateformat` — alternative date formatting
- `#language` — language name in any language
- `#direction` — text direction (ltr/rtl)
- `{{TRANSLATABLEPAGE}}` — magic word for translatable page context
- `{{TRANSLATIONLANGUAGE}}` — the language of the current translation

### 📚 Page Translation Workflow Guide (`references/page-translation-workflow.md`)

Step-by-step guide for the complete translation workflow:
1. Writing content for translation (author)
2. Marking a page for translation (admin)
3. Translating units (translator)
4. Reviewing translations (reviewer)
5. Handling source updates (fuzzy matching)
6. Managing translation memory

### 🐍 Translation Checker (`assets/translation_checker.py`)

Comprehensive translation analysis for a page — lists available languages, completion stats, fuzzy units, and identifies common issues:

```bash
# Full translation report
python3 assets/translation_checker.py "AvoinGLAM/Past activities" --wiki meta

# Show only outdated/fuzzy translations
python3 assets/translation_checker.py "Project/Page" --fuzzy

# Export translation status as JSON
python3 assets/translation_checker.py "Project/Page" --json
```

### 🐍 Template Translation Scanner (`assets/template_translation_scanner.py`)

Scan templates for translation compliance — checks that labels use `<translate>`, links use `Special:MyLanguage/`, and dates use `#timef`:

```bash
# Check a template for translation best practices
python3 assets/template_translation_scanner.py "Template:AvoinGLAM/Main navigation" --wiki meta

# Check all templates in a project
python3 assets/template_translation_scanner.py --project "AvoinGLAM" --wiki meta

# Show compliance report
python3 assets/template_translation_scanner.py "Template:Project/Box" --report
```

### 🧪 Test Suite (`tests/`)

Test scripts for verifying translation-related tooling:

```bash
# Run all translation tests
python3 -m pytest tests/

# Test #timef format detection
python3 -m pytest tests/test_timef.py

# Test Special:MyLanguage URL resolution
python3 -m pytest tests/test_mylanguage.py

# Test translatable string extraction
python3 -m pytest tests/test_extraction.py
```
