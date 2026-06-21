---
name: wikipedia-wikitables
description: Create, parse, style, and fix MediaWiki wikitable syntax — delimiters, header/data cells, CSS classes, inline styling, rowspan/colspan, accessibility attributes, sortable and collapsible tables, and programmatic table generation from data
depends_on: [wikimedia-wikitext]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["wikitable", "table", "sortable", "colspan", "rowspan", "data table", "table syntax"]
  - keywords: ["table generation", "CSV to wikitable", "wikitable styling", "mw-collapsible"]
last_verified: 2026-06-10
---

> ⚠️ **Prerequisite:** This skill assumes basic familiarity with wikitext templates.
> See **[wikipedia-templates](../wikipedia-templates/SKILL.md)** for template syntax,
> and **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** for AST parsing with
> `mwparserfromhell`.
>
> ⚠️ **User-Agent required:** API calls to fetch wikitext or render tables need a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.

---

## Reference: Wikitable Building Blocks

MediaWiki tables use a pipe-based syntax inspired by HTML table markup.
Every table has four structural delimiters:

| Symbol | Meaning | Opens/Closes | HTML equivalent |
|---|---------|------|-----------------|
| `{\|` | Table open | Start of table | `<table>` |
| `\|}` | Table close | End of table | `</table>` |
| `\|-` | Row separator | New row | `<tr>` |
| `\|` | Data cell | Cell content | `<td>` |
| `!` | Header cell | Header content | `<th>` |
| `\|+` | Caption | Table caption | `<caption>` |

### Minimal Complete Table

```wikitext
{| class="wikitable"
|+ Annual revenue
! Year
! Revenue
|-
| 2020
| $1.2M
|-
| 2021
| $1.8M
|}
```

This renders as a single row of headers (`!`) followed by two data rows (`|`).

### Anatomy of a Cell

A cell can have attributes (class, style, scope, colspan, rowspan) before the
content. The pipe separates attributes from the value:

```wikitext
| style="text-align: center;" | centered content
! scope="col" style="text-align: right;" | Header
| rowspan="2" | spans two rows
```

The general pattern is:

```
| [attribute1] [attribute2] ... | cell content
```

Multiple attributes on the same cell are space-separated between the opening
pipe and the final `|` that precedes the content.

---

## SOP: Class-Based Styling

MediaWiki's `common.css` ships with pre-defined table classes. You apply them
on the table-open line:

```wikitext
{| class="wikitable"
```

### Available Classes

| Class | Effect | Notes |
|---|---|---|
| `wikitable` | Standard styling: light gray header, borders, striped rows | The default for most tables |
| `sortable` | Adds clickable column headers for sorting | **Must** be combined with `wikitable` or another base class |
| `mw-collapsible` | Adds a [show]/[hide] toggle | Used in navboxes and data tables |
| `mw-collapsed` | Starts collapsed (requires `mw-collapsible`) | Content hidden by default |
| `mw-datatable` | Alternating row colors, hover highlight | Used by software/database tables |
| `plainlinks` | Removes external link icons inside the table | Useful in infobox-style tables |

### Common Combinations

```wikitext
{| class="wikitable sortable"
! Name
! Score
!
|-
| Alice
| 95
|}
```

```wikitext
{| class="wikitable sortable mw-collapsible mw-collapsed"
! Hidden by default, click to expand
|-
| Revealed content
|}
```

### Row-Level Classes

Classes can also go on the row separator:

```wikitext
|- class="sortbottom"
| Total
| $3.0M
```

`class="sortbottom"` pins a summary row to the bottom of a sortable table,
preventing it from being sorted with the data rows.

---

## SOP: Inline CSS Styling

For fine-grained control beyond what the built-in classes provide, use inline
`style=` attributes at the table, row, or cell level.

### Table-Level Styles

```wikitext
{| class="wikitable" style="width: 100%; background-color: #f8f9fa;"
```

| Style | Effect | When to Use |
|---|---|---|
| `width: 100%;` | Full-width table | Dashboard/report tables |
| `width: auto;` | Shrink to content | Small lookup tables |
| `background-color: #f8f9fa;` | Light gray background | Subtle table backdrop |
| `border-collapse: collapse;` | Single borders instead of double | (Default for `wikitable`) |
| `margin-left: auto; margin-right: auto;` | Center the table on the page | Standalone tables |
| `font-size: 90%;` | Slightly smaller text | Sidebar/compact tables |

### Row-Level Styles

```wikitext
|- style="background-color: #efe;"
| Highlighted row
```

Useful for section breaks, totals, or status indicators (e.g. green for
"approved", red for "fails").

### Cell-Level Styles

```wikitext
| style="text-align: center;" | Centered
| style="text-align: right; font-weight: bold;" | Right-aligned bold
! style="text-align: left; background-color: #eaecf0;" | Left header
```

### Text Alignment

| Style | Effect |
|---|---|
| `text-align: left;` | Left-align content |
| `text-align: center;` | Center content |
| `text-align: right;` | Right-align content |
| `text-align: justify;` | Justified text |
| `vertical-align: top;` | Align to top of cell |
| `vertical-align: middle;` | Vertically center |
| `vertical-align: bottom;` | Align to bottom of cell |

### Background Colors

```wikitext
! scope="col" style="background-color: #cfe3ff;" | Blue header
|- style="background-color: #ffffcc;"
| Yellow row
| style="background-color: #fee;" | Pink cell
```

### Borders and Spacing

```wikitext
{| style="border: 2px solid #a3bfb1;"
|- style="border-bottom: 3px solid #a3bfb1;"
| style="border-right: 1px dashed #ccc;" | Content
|}

{| style="cellpadding: 10px;"
|- style="padding: 8px;"
| Spacious cell
|}
```

### Legacy HTML Attributes (avoid in new tables)

Older tables use HTML attributes like `align=`, `valign=`, `bgcolor=`.
These still render but are **deprecated in HTML5**. Prefer CSS `style=`:

| Legacy | Modern CSS equivalent |
|---|--------------------|
| `align="center"` | `style="text-align: center;"` |
| `valign="top"` | `style="vertical-align: top;"` |
| `bgcolor="#eee"` | `style="background-color: #eee;"` |
| `width="500"` | `style="width: 500px;"` |
| `border="1"` | `style="border: 1px solid #a2a9b1;"` |

### Shorthand Multi-Value Attributes

You can combine multiple styles on one cell:

```wikitext
| style="text-align: right; background-color: #fdd; white-space: nowrap; font-size: 90%;" | 42
```

---

## SOP: Accessibility with `scope`

For screen readers, header cells must specify which cells they govern:

```wikitext
! scope="col" | Column header
! scope="col" | Another header
! scope="row" | Row header
```

| `scope` value | Meaning |
|---|---|
| `scope="col"` | Header applies to the column below it |
| `scope="row"` | Header applies to the row beside it |
| `scope="colgroup"` | Header applies to a group of columns |
| `scope="rowgroup"` | Header applies to a group of rows |

A table with `class="wikitable"` and proper `scope` attributes passes
WCAG accessibility requirements. A table with no `scope` does not.

---

## SOP: Column Spans and Row Spans

```wikitext
! colspan="2" | Merged header spanning two columns
| rowspan="3" | Content spans three rows
| colspan="2" rowspan="2" | Spans both
```

- `colspan="N"` — merge N columns horizontally
- `rowspan="N"` — merge N rows vertically
- Can be combined on the same cell
- Cells covered by a span are omitted (not written with empty `| |`)

### Common Patterns

```wikitext
{| class="wikitable"
! colspan="2" | Merged header
! scope="col" | Single
|-
! scope="row" | Row header
| Data 1
| Data 2
|-
| rowspan="2" | Vertical span
| A
| B
|-
| C
| D
|}
```

---

## SOP: Inline Cell Content

Cell values support any wikitext — templates, links, images, lists, even
nested tables:

```wikitext
| [[Albert Einstein]] (born 1879)
| {{flag|France}}
| [[File:Example.jpg|50px]]
|
* Item one
* Item two
|
{| class="wikitable"
| Nested table
|}
```

---

## SOP: Parsing Tables with `mwparserfromhell`

```python
import mwparserfromhell

wikitext = """{| class="wikitable sortable"
! Name
! Score
! scope="col" | Rank
|-
| Alice
| 95
| style="text-align: center;" | 1st
|}"""

parsed = mwparserfromhell.parse(wikitext)
tables = parsed.filter_tags(matches=lambda t: str(t.tag) == "table")

for table in tables:
    print("Table:", table)
    # Extract attributes
    if table.has("class"):
        print("  Classes:", table.get("class").value)
```

For extracting structured data from tables, use the `style` and `class`
attributes to identify header rows and data cells.

---

## SOP: Generating Tables from Data (Python)

```python
def dicts_to_wikitable(
    data: list[dict[str, str]],
    *,
    classes: str = "wikitable sortable",
    caption: str = "",
    alignment: str | None = None,
) -> str:
    """Convert a list of dicts to a MediaWiki wikitable string."""
    if not data:
        return ""

    headers = list(data[0].keys())
    style = f' style="text-align: {alignment};"' if alignment else ""
    lines: list[str] = []
    lines.append(f'{{| class="{classes}"{style}')
    if caption:
        lines.append(f"|+ {caption}")
    lines.append("! " + "\n! ".join(f'scope="col" | {h}' for h in headers))
    for row in data:
        lines.append("|-")
        for h in headers:
            val = row.get(h, "")
            # Auto-align numeric values to the right
            try:
                float(val.replace(",", "").replace("$", "").replace("%", ""))
                cell = f' style="text-align: right;" | {val}'
            except ValueError:
                cell = f"| {val}"
            lines.append(cell)
    lines.append("|}")
    return "\n".join(lines)


# Example
data = [
    {"Name": "Alice", "Score": "95"},
    {"Name": "Bob", "Score": "87"},
]
print(dicts_to_wikitable(data, caption="Scores"))
```

---

## Reference: Styling Quick Reference

### Color Palette (Wikimedia Standard)

These are the colors used by `class="wikitable"` and common in Wikipedia tables:

| Color | Hex | Use |
|---|---|---|
| Table header background | `#eaecf0` | Default `wikitable` header |
| Table body background | `#f8f9fa` | Default `wikitable` body |
| Alternating row highlight | `#fafafa` | Hover/alternate shade |
| Border | `#a2a9b1` | Default table border |
| Green row (pass) | `#d5fdf4` | Positive signal |
| Yellow row (warning) | `#fef6e7` | Needs attention |
| Red row (fail/error) | `#fee7e6` | Negative signal |
| Blue header | `#cfe3ff` | Custom header color |

### Alignment Summary

| Target | Inline Style | Class Alternative |
|---|---|---|
| Center the table on page | `style="margin:0 auto;"` | Not available as class |
| Left-align a column | `style="text-align: left;"` | Not available as class |
| Center a column | `style="text-align: center;"` | Not available as class |
| Right-align numeric column | `style="text-align: right;"` | Not available as class |
| Vertically center cells | `style="vertical-align: middle;"` | Not available as class |
| Pin a row to bottom | — | `class="sortbottom"` |

---

## Reference: When to Use Which Approach

| Situation | Approach | Example |
|---|---|---|
| Standard data table | Class only | `class="wikitable sortable"` |
| Report with a color-coded row | Class + inline | `class="wikitable"`, `\|- style="background: #fee;"` |
| One-off alignment override | Inline cell style | `\| style="text-align: center;" \| 42` |
| Table for user scripts/gadgets | Class + accessible | `class="wikitable"` + `scope="col"` on all headers |
| Compact sidebar table | Inline table style | `style="font-size: 90%; width: auto;"` |

---

## Tooling

### 🔧 Wikitable to HTML Preview (`scripts/wikitable-to-html.sh`)

Convert a wikitable to rough HTML for visual verification:

```bash
echo '{| class="wikitable"|! A|! B|-|1|2|}' | ./scripts/wikitable-to-html.sh
```

### 🔧 Generate Table from CSV (`scripts/generate-table.sh`)

```bash
cat data.csv | ./scripts/generate-table.sh --caption "Scores" --classes "wikitable sortable"
```

### 🐍 Wikitable Tools (`assets/wikitable_tools.py`)

```python
from assets.wikitable_tools import (
    dicts_to_wikitable,
    parse_wikitable,
    style_cell,
)

# Generate
table = dicts_to_wikitable(data, caption="Results", alignment="center")

# Parse
rows = parse_wikitable(wikitext)

# Style a single cell
styled = style_cell("42", align="right", bold=True, background="#efe")
```

### 🐍 Test Suite (`assets/test_wikitable_tools.py`)

```bash
python3 -m pytest assets/test_wikitable_tools.py -v
```

Tests cover: generation from dicts, parsing, styling, edge cases (empty
tables, colspan, rowspan, nested tables, multi-word headers, numeric
auto-alignment).
