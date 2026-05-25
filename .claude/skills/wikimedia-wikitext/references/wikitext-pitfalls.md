# Wikitext Parsing Pitfalls

This document catalogs documented edge cases and traps in MediaWiki wikitext that break naive parsing approaches.

---

## 1. Template Argument Separation

The pipe (`|`) character separates template arguments — **except** when it appears inside:

- **Wikilinks:** `{{Template|link=[[Page|display text]]}}` — the `|` between `Page` and `display text` is part of the wikilink, not a new template argument
- **Image captions:** `{{Template|file=[[File:Example.jpg|thumb|caption]]}}`
- **Parser functions:** `{{Template|text={{#if:cond|true|false}} }}`
- **HTML entities:** `{{Template|text={{!}}}}` — `{{!}}` is a magic word that produces `|`

**Regex `/\|/` splitting fails** on all the above. Use `mwparserfromhell` which correctly tracks nesting depth.

## 2. Nested Templates

Templates can be nested arbitrarily deep:

```wikitext
{{Infobox
  | name = {{PAGENAME}}
  | image = {{#if:{{{image|}}}|[[File:{{{image}}}|thumb]]|{{No image}}}}
  | data = {{#invoke:DataModule|getData|{{#time:Y}} }}
}}
```

`mwparserfromhell` correctly handles this — each template node in the AST is independent, including templates found inside the parameter values of other templates.

## 3. Table Syntax Gotchas

### Implicit Row/Colspan
Wikitext tables can have implicit row spans and multi-line cells:

```wikitext
{|
| row 1, cell 1 || row 1, cell 2
|-
| row 2, cell 1
| row 2, cell 2 (multi-line content
continues here)
|}
```

### CSS in Cell Markers
CSS styling can be embedded directly in cell markers:

```wikitext
! scope="col" style="background:#eee;" | Header
| style="text-align:center;" | Centered data
|-
| colspan="2" style="color:red;" | Merged cell
```

### Pipes Inside Table Content
A pipe inside `[[wikilink|display]]` or `{{template}}` inside a table cell is NOT a cell separator. Naive line splitting breaks.

### Nested Tables
Tables can be nested inside other table cells. Tracking `{|`/`|}` depth is necessary for correct parsing.

**Solution for all table issues:** Fetch via Parsoid `/html` endpoint and use `pandas.read_html()` or BeautifulSoup on the clean HTML output.

## 4. Tag Extension Boundaries

MediaWiki has tag extensions that consume raw content:

```wikitext
<nowiki>[[This is not a link]]</nowiki>

<pre>
{{This is not a template}}
</pre>

<syntaxhighlight lang="python">
# {{not a template call}}
print("hello")
</syntaxhighlight>
```

Inside `<nowiki>`, `<pre>`, and `<syntaxhighlight>`, all wiki markup is treated as literal text. Regex patterns that don't understand these boundaries will falsely detect templates/links inside them.

`mwparserfromhell.filter_tags()` correctly handles these, but be aware that the tag's `contents` are text, not parseable wikitext.

## 5. Parser Function Intricacies

Parser functions use `{{#...:}}` syntax and have complex argument separation:

```wikitext
{{#if: condition | then text | else text }}
{{#ifeq: {{{parameter}}} | value | then | else }}
{{#switch: {{{var}}}
 | case1 = result1
 | case2 = result2
 | #default = default result
}}
```

`mwparserfromhell` treats parser functions as `Template` nodes — they can be filtered with `code.filter_templates()`. Check with:

```python
for t in code.filter_templates():
    if t.name.startswith("#"):
        print("Parser function:", t.name)
```

## 6. Comment Placement

HTML comments can appear almost anywhere and affect parsing:

```wikitext
{{Template|<!-- comment -->param=value}}   <!-- Valid -->
{|
<!-- comment before table -->
| cell
|}
```

Comments inside template parameters are preserved by `mwparserfromhell` but not by regex. Always use the parser.

## 7. Magic Words and Variables

MediaWiki has magic words that look like templates but aren't:

```wikitext
{{PAGENAME}}         <!-- Expands to current page name -->
{{CURRENTTIME}}      <!-- Expands to current UTC time -->
{{SITENAME}}         <!-- Expands to "Wikipedia" -->
{{SERVER}}           <!-- Expands to "https://en.wikipedia.org" -->
{{DEFAULTSORT:Smith, John}}  <!-- Affects page sorting -->
__NOTOC__            <!-- Behavior switch (not a template at all) -->
```

These are parsed as `Template` nodes by `mwparserfromhell`. To distinguish them, check if the name matches known magic words.

## 8. strip_code() Behavior Quirks

```python
code = mwparserfromhell.parse(wikitext)
plain = code.strip_code()
```

`strip_code()` has specific behaviors to be aware of:

| Input | strip_code() Output | Notes |
|-------|---------------------|-------|
| `Hello <!-- comment --> world` | `Hello world` | Comments removed |
| `{{Template}} text` | ` text` | Template removed (no expansion) |
| `<ref>citation</ref> text` | ` text` | Ref tags removed |
| `[[Page]] text` | `Page text` | Wikilink replaced with title |
| `[[Page|display]] text` | `display text` | Wikilink replaced with display text |
| `[https://example.com] text` | `[1] text` | External links become `[n]` |
| `'''bold''' text` | `bold text` | Formatting stripped |
| `{{!}}` | (empty) | Magic word stripped |

## 9. Unicode and Character Encoding

- Page titles use underscores for spaces (`Albert_Einstein`, not `Albert Einstein` in URLs)
- Page titles can contain non-ASCII characters: `São Paulo`, `München`, `中国`
- HTML entities (`&amp;`, `&lt;`, `&gt;`, `&nbsp;`) may appear in wikitext
- Some characters trigger normalization: `İ` → `i` (Turkish dotless I), `ß` → `ss` (German)
- Zero-width characters (U+200B, U+200C) may appear in page titles

`mwparserfromhell` preserves the original text. If you need normalized output, apply Unicode normalization (NFC) yourself.

## 10. Transclusion vs. Raw Content

`{{Template}}` in source wikitext is a template *transclusion* — the parser sees the template call, not the expanded result. `mwparserfromhell` does NOT expand templates. To get expanded output:

- **Parsoid HTML route:** Fetch the page via the `/html` REST endpoint (templates are fully expanded in the HTML)
- **Action API route:** Use `action=parse&page=Title&prop=text` to get pre-rendered HTML

Never try to manually expand templates — you'd need to replicate the full MediaWiki parser, which is impractical.
