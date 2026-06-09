---
name: wikipedia-reference-verifiability
description: Analyze whether a Wikipedia page's references contain URLs — detect bare plain-text citations, template-based citations without url= parameters, shortened footnotes, and named ref reuse. Useful for article quality assessment, NPP triage, and citation maintenance
depends_on: [wikimedia-api-access, wikimedia-wikitext]
license: MIT
compatibility: opencode
---

> ⚠️ **User-Agent required:** The API calls in this skill need a descriptive `User-Agent`
> header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for
> the correct format.

> ⚠️ **Prerequisite:** This skill assumes you can parse wikitext with `mwparserfromhell`.
> See the **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** skill for AST parsing
> patterns.

---

## Reference: Why Reference URLs Matter for Verifiability

Wikipedia's core policy, **Verifiability** (WP:V), requires that readers can
verify that content is backed by reliable sources. A reference that provides
a **clickable URL** is immediately verifiable by any reader. A reference
without a URL requires the reader to:

- Own the cited book or journal
- Have access to a library with the cited work
- Trust the author's claim about the source

This is one of the most common red flags during New Page Patrol (NPP) review,
and a frequent target for citation maintenance.

### Reference Types and Verifiability

| Type | Wikitext Example | Has URL? | Verifiable Online? |
|---|---|---|---|
| Citation template with URL | `{{cite web\|url=https://...}}` | ✅ | ✅ Yes |
| Citation template without URL | `{{cite book\|title=X\|year=2020}}` | ❌ | ❌ (print only) |
| Plain-text ref | `<ref>Smith, 2020, p.42</ref>` | ❌ | ❌ (no link) |
| Shortened footnote | `<ref>{{harvsp\|Smith\|2020}}</ref>` | ❌ | ❌ (may resolve in bibliography) |
| Named ref (reuse) | `<ref name="x" />` | resolves to definition | depends on definition |

---

## SOP: URL Detection Strategy

The analysis proceeds in several passes:

### Pass 1 — Collect all `<ref>` tags

```python
import mwparserfromhell

parsed = mwparserfromhell.parse(wikitext)
ref_tags = parsed.filter_tags(
    matches=lambda t: str(t.tag).strip().lower() == "ref"
)
```

### Pass 2 — Index named ref definitions

Named refs can be defined anywhere on the page, even after their first use.
Index all definitions before evaluating individual refs:

```python
named_defs: dict[str, str] = {}
for tag in ref_tags:
    name = _named_ref_name(tag)
    content = _tag_content(tag)
    if name and content and name not in named_defs:
        named_defs[name] = content
```

### Pass 3 — Evaluate each reference

For each ref tag:

1. If it has content, use that. If it's a named ref reuse (no content but
   has a name attribute), resolve from the index.
2. Count it only once per name group (avoid double-counting reused named refs).
3. Check for URLs in the content via two strategies (see below).

### Pass 4 — Check inline citation templates outside `<ref>` tags

Some pages use citation templates directly in the text (old-style inline
citations). Check for `{{cite ...}}` templates that aren't nested inside
any `<ref>` tag:

```python
for template in parsed.filter_templates():
    name = str(template.name).strip().lower()
    if name.startswith("cite "):
        if not _is_inside_ref(template, ref_tags):
            # Check this template for URL presence
```

---

## SOP: URL Detection — Two Strategies

### Strategy A — Raw URL in text

A simple regex check catches bare URLs and links inside plain text:

```python
import re

URL_RE = re.compile(r"https?://", re.IGNORECASE)

def _contains_raw_url(text: str) -> bool:
    return bool(URL_RE.search(text))
```

This catches:
- `<ref>https://example.com/article</ref>` (bare URL)
- `<ref>Available at https://example.com</ref>` (URL in prose)
- `<ref>{{cite web|url=https://...|title=...}}</ref>` (URL inside template)
- `<ref>[https://example.com Article]</ref>` (external link syntax)

### Strategy B — Citation template URL parameters

When a reference uses a CS1/CS2 citation template, the URL may be in a
named parameter, not in the raw text. Check for the following parameter names:

```python
URL_PARAM_NAMES = frozenset({
    "url",
    "chapter-url",
    "conference-url",
    "contribution-url",
    "transcript-url",
    "archive-url",
    # camelCase legacy variants
    "chapterurl",
    "conferenceurl",
    "contributionurl",
    "transcripturl",
    "archiveurl",
    # Deprecated but still in use
    "accessdate",  # not a URL, but check its value
})
```

Implementation:

```python
def _template_has_url_param(template: mwparserfromhell.nodes.Template) -> bool:
    for param in template.params:
        name = str(param.name).strip().lower()
        if name in URL_PARAM_NAMES:
            value = str(param.value).strip()
            if value:  # non-empty value = URL present
                return True
        # Also check unnamed params for raw URLs
        if not name and _contains_raw_url(str(param.value)):
            return True
    return False
```

Known citation template families that accept URL parameters:

| Template Family | URL Parameter | Notes |
|---|---|---|
| `{{cite web}}` | `url` | Primary parameter |
| `{{cite news}}` | `url` | |
| `{{cite journal}}` | `url` | Often has DOI instead |
| `{{cite book}}` | `url` | Rarely used (print sources) |
| `{{cite magazine}}` | `url` | |
| `{{cite encyclopedia}}` | `url` | |
| `{{cite report}}` | `url` | |
| `{{cite thesis}}` | `url` | |
| `{{cite conference}}` | `url` | |
| `{{cite podcast}}` | `url` | |
| `{{cite episode}}` | `url` | |
| `{{cite map}}` | `url` | |
| `{{citation}}` | `url` | Generic citation template |

---

## SOP: Handling Edge Cases

### Named Ref Reuse

```python
seen_named: set[str] = set()

for tag in ref_tags:
    name = _named_ref_name(tag)
    content = _tag_content(tag)

    # Resolve reuse
    if not content and name:
        content = named_defs.get(name, "")
    elif not content:
        continue  # self-closing with no name

    # Deduplicate per name
    if name:
        if name in seen_named:
            continue
        seen_named.add(name)

    # Now evaluate content for URL presence
    ...
```

### Shortened Footnotes (`{{harvsp}}`, `{{sfn}}`, `{{harvnb}}`)

These author-date templates point to a bibliography entry elsewhere on the
page. The inline ref has no URL, but the bibliography entry might. To check
the bibliography:

1. Scan the page for a `== Bibliography ==` or `== References ==` section.
2. Look for full `{{cite ...}}` templates in that section.
3. Check if the author/year from the shortened footnote matches a biblio entry.
4. Determine if that entry has a URL.

This is heuristic — a simplified approach is to flag the inline ref and
report the bibliography entries separately:

```python
SHORTENED_FOOTNOTE_TEMPLATES = frozenset({
    "harvsp", "harvnb", "harv", "sfn", "harvard citation",
})

def _is_shortened_footnote(name: str) -> bool:
    return name in SHORTENED_FOOTNOTE_TEMPLATES or \
           name.startswith("harv") or name.startswith("sfn")
```

### Nested Templates

A citation template may be nested inside another template inside a `<ref>`:

```
<ref>{{citation|title=X|url=https://...}}</ref>         ← simple nest
<ref>{{harvsp|Smith|2020}}                              ← shortened footnote
```

The inner `{{citation|url=...}}` must still be detected. After extracting
the ref content, parse it recursively:

```python
for template in parsed.filter_templates():
    if _template_has_url_param(template):
        return True
    # Recurse: check nested templates in params
    for param in template.params:
        inner = mwparserfromhell.parse(str(param.value))
        for nt in inner.filter_templates():
            if _template_has_url_param(nt):
                return True
```

### Infobox Presence

Infoboxes are templates whose name starts with `Infobox`:

```python
def has_infobox(wikitext: str) -> bool:
    parsed = mwparserfromhell.parse(wikitext)
    for template in parsed.filter_templates():
        name = str(template.name).strip()
        if name.lower().startswith("infobox"):
            return True
    return False
```

---

## Reference: Summarizing References for Display

When displaying a URL-free reference to a reviewer, produce a human-readable
snippet that identifies the type of reference:

```python
def _summarize_ref(content: str) -> str:
    # Extract template name for template-based refs
    cleaned = re.sub(
        r"\{\{(\s*[Cc]ite\s+\w+|\s*[Hh]arv[np]?\w*|\s*[Ss]fn)\b[^}]*\}\}",
        lambda m: "[" + m.group(1).strip() + "]",
        content,
    )
    # Generic fallback for unrecognized templates
    cleaned = re.sub(r"\{\{[^}]*\}\}", "[template]", cleaned)
    # Simplify wikilinks
    cleaned = re.sub(r"\[\[([^\]|\]]+)\|([^\]]+)\]\]", r"\2", cleaned)
    cleaned = re.sub(r"\[\[([^\]|]+)\]\]", r"\1", cleaned)
    cleaned = re.sub(r"'''''|'''|''", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > 80:
        cleaned = cleaned[:77] + "..."
    return cleaned or "(empty ref)"
```

This produces readable labels like:
- `[harvsp]` — shortened footnote
- `[Cite journal]` — cite journal template without URL
- `[cite Instagram]` — Instagram citation
- `Smith, J. The Book...` — plain text

---

## Tooling

### 🔧 Check References for a Single Page (`scripts/check-ref-urls.sh`)

```bash
./scripts/check-ref-urls.sh "Betka Ait Mokran"
./scripts/check-ref-urls.sh "LOL: Slutty Bass"
```

Outputs a per-reference summary showing whether each ref has a URL.

### 🔧 Batch Scan New Pages (`scripts/batch-ref-audit.sh`)

```bash
./scripts/batch-ref-audit.sh --days 7 --limit 100
./scripts/batch-ref-audit.sh --days 1 --limit 50 --no-quality
```

Combines the PageTriage two-pass pipeline with reference analysis. Equivalent
to the npp-finder tool.

### 🐍 Reference URL Checker Library (`assets/ref_url_checker.py`)

The full reference analysis library — importable, with all edge cases handled:

```python
from assets.ref_url_checker import has_any_url_refs, has_infobox

# Check a page's references
has_url, total, url_count, samples = has_any_url_refs(wikitext)

# Check infobox presence
has_box = has_infobox(wikitext)
```

### 🐍 Test Suite (`assets/test_ref_checker.py`)

```bash
python3 -m pytest assets/test_ref_checker.py -v
```

Tests cover: raw URLs, citation templates with/without URL, named ref
resolution, shortened footnotes, nested templates, empty pages, self-closing
tags, and reused named refs.
