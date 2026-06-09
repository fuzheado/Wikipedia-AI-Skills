# Translate Parser Functions Reference

Complete reference for parser functions provided by the Translate extension.

---

## `#timef` — Locale-Aware Date Formatting

Formats a date according to the user's interface language. This is the **primary date formatting function** for translatable pages.

### Syntax
```
{{#timef:date|format}}
```

| Parameter | Required | Description |
|---|---|---|
| `date` | Yes | Date string in ISO format (`YYYY-MM-DD`) or any format `#time` accepts |
| `format` | Yes | Output format (see below) |

### Format Options

| Format | English | Finnish | French | Arabic |
|---|---|---|---|---|
| `date` (default-like) | 6 May 2024 | 6. toukokuuta 2024 | 6 mai 2024 | ٦ مايو ٢٠٢٤ |
| `time` | 14:30 | 14:30 | 14:30 | ١٤:٣٠ |
| `both` | 6 May 2024 14:30 | 6. toukokuuta 2024 14:30 | 6 mai 2024 14:30 | ٦ مايو ٢٠٢٤ ١٤:٣٠ |
| `dmy` | 6 May 2024 | 6. toukokuuta 2024 | 6 mai 2024 | ٦ مايو ٢٠٢٤ |
| `mdy` | May 6, 2024 | toukokuuta 6, 2024 | mai 6, 2024 | مايو ٦، ٢٠٢٤ |
| `ymd` | 2024 May 6 | 2024 toukokuuta 6 | 2024 mai 6 | ٢٠٢٤ مايو ٦ |
| `iso` | 2024-05-06 | 2024-05-06 | 2024-05-06 | ٢٠٢٤-٠٥-٠٦ |

### Common Patterns

**Single date:**
```wikitext
{{#timef:2024-10-23|date}}
```

**Date with day of week:**
```wikitext
{{#time:l|2024-10-23}} {{#timef:2024-10-23|date}}
```
→ "Wednesday 23 October 2024" (day name is via #time, date is via #timef)

**Date range:**
```wikitext
{{#timef:{{{startdate|}}}|date}} – {{#timef:{{{enddate|}}}|date}}
```

**With time:**
```wikitext
{{#timef:2024-10-23|date}} • 14:00
```

**With timezone:**
```wikitext
{{#timef:2024-10-23 14:00|both}} EET
```

### Using with Template Parameters

```wikitext
<div class="bannertime">
{{#timef:{{{startdate|}}}|date}}
{{#if: {{{starttime|}}}|• {{{starttime|}}} }}
{{#if: {{{enddate|}}}|– {{#timef:{{{enddate|}}}|date}} }}
</div>
```

### Important Notes

- `#timef` only works correctly on **translatable pages** or pages that are part of the translation system
- On non-translatable pages, it falls back to `#time` behavior (always outputs English/UTC format)
- The format string `date` is the most commonly used — it produces the most natural output per locale
- Unlike `#time`, `#timef` does **not** accept PHP date format characters — only the named formats listed above

---

## `#dateformat` — Content-Language Date Formatting

Formats a date according to the wiki's default content language (not the user's language).

### Syntax
```
{{#dateformat:date|format}}
```

| Format | Example |
|---|---|
| `dmy` | 6 May 2024 |
| `mdy` | May 6, 2024 |
| `ymd` | 2024 May 6 |
| `iso` | 2024-05-06 |

### When to Use

- Use `#timef` for user-facing dates on translatable pages
- Use `#dateformat` when you specifically want the wiki's language, not the user's
- Use `#time` for fixed-format dates that should not change per locale

---

## `#language` — Language Name

Returns the name of a language in a specified language.

### Syntax
```
{{#language:langcode}}
{{#language:langcode|inlangcode}}
```

### Examples

| Call | Returns |
|---|---|
| `{{#language:fi}}` | "suomi" (in the wiki's language) |
| `{{#language:fi|en}}` | "Finnish" |
| `{{#language:en|fi}}` | "englanti" |
| `{{#language:fr|de}}` | "Französisch" |
| `{{#language:ar}}` | "العربية" |

### Common Use

```wikitext
[[Special:MyLanguage/AvoinGLAM/{{#language:fi}}|{{#language:fi|en}}]]
```

---

## `#direction` — Text Direction

Returns the writing direction for a language.

### Syntax
```
{{#direction:langcode}}
```

### Examples

| Call | Returns |
|---|---|
| `{{#direction:en}}` | `ltr` |
| `{{#direction:ar}}` | `rtl` |
| `{{#direction:he}}` | `rtl` |
| `{{#direction:fi}}` | `ltr` |

### Use in Templates

```wikitext
<div dir="{{#direction:{{{lang|en}}}}}">
Content that adapts to writing direction
</div>
```

---

## `{{TRANSLATABLEPAGE}}` — Magic Word

Returns the title of the translatable page that contains this template.

### Syntax
```
{{TRANSLATABLEPAGE}}
```

### Examples

| Context | Returns |
|---|---|
| On `AvoinGLAM/en` | `AvoinGLAM` |
| On `AvoinGLAM/Past activities` | `AvoinGLAM/Past activities` |
| On a non-translatable page | (empty string) |

### Common Use

Generate an edit link to the source page, regardless of translation variant:

```wikitext
{{fullurl:{{TRANSLATABLEPAGE}}|action=edit}}
```

### Conditional Check

```wikitext
{{#if: {{TRANSLATABLEPAGE}}
| This page IS translatable
| This page is NOT translatable
}}
```

---

## `{{TRANSLATIONLANGUAGE}}` — Magic Word

Returns the language code of the current translation page view.

### Syntax
```
{{TRANSLATIONLANGUAGE}}
```

### Examples

| Context | Returns |
|---|---|
| On `AvoinGLAM/en` | `en` |
| On `AvoinGLAM/fi` | `fi` |
| On a non-translatable page | (empty string) |

### Use

```wikitext
{{#if: {{TRANSLATIONLANGUAGE}}
| You are viewing {{TRANSLATIONLANGUAGE}} translation
| You are viewing the source page
}}
```
