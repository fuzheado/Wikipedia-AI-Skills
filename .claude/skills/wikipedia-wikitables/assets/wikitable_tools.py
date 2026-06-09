"""Tools for generating, parsing, and styling MediaWiki wikitables.

Provides:
- dicts_to_wikitable — convert data to wikitable markup
- parse_wikitable — extract rows from a wikitable string
- style_cell — apply CSS to a single cell value
- csv_to_wikitable — convert CSV text to wikitable
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any


def dicts_to_wikitable(
    data: list[dict[str, str]],
    *,
    classes: str = "wikitable sortable",
    caption: str = "",
    alignment: str | None = None,
) -> str:
    """Convert a list of dicts to a MediaWiki wikitable string.

    Args:
        data: List of dicts, all with the same keys (preserves insertion order).
        classes: CSS class(es) for the table element.
        caption: Optional table caption (renders above the table).
        alignment: Optional text-align value for the whole table element.

    Returns:
        A wikitable string ready to paste into any wiki page.
    """
    if not data:
        return ""

    headers = list(data[0].keys())
    table_style = f' style="text-align: {alignment};"' if alignment else ""
    lines: list[str] = []
    lines.append(f'{{| class="{classes}"{table_style}')
    if caption:
        lines.append(f"|+ {caption}")
    lines.append("! " + "\n! ".join(f'scope="col" | {h}' for h in headers))
    for row in data:
        lines.append("|-")
        for h in headers:
            val = row.get(h, "")
            cell = _auto_format_cell(val)
            lines.append(cell)
    lines.append("|}")
    return "\n".join(lines)


def csv_to_wikitable(
    csv_text: str,
    *,
    classes: str = "wikitable sortable",
    caption: str = "",
    alignment: str | None = None,
) -> str:
    """Convert CSV text (first row = headers) to a wikitable string."""
    reader = csv.reader(io.StringIO(csv_text.strip()))
    rows = list(reader)
    if not rows:
        return ""
    headers = rows[0]
    dicts = [dict(zip(headers, row)) for row in rows[1:]]
    return dicts_to_wikitable(
        dicts,
        classes=classes,
        caption=caption,
        alignment=alignment,
    )


def parse_wikitable(wikitext: str) -> list[dict[str, str]]:
    """Extract rows from a wikitable string.

    Returns a list of dicts with header keys and cell values.
    Handles basic wikitables only — does not support merged cells
    (colspan/rowspan) or nested tables.

    This is a line-oriented parser that does NOT require mwparserfromhell.
    For AST-based parsing with full tag resolution, use mwparserfromhell
    directly (see the wikimedia-wikitext skill).
    """
    # Locate the first {| ... |} block
    table_match = re.search(r"\{\|(.*?)\|\}", wikitext, re.DOTALL)
    if not table_match:
        return []

    body = table_match.group(1)

    # Remove caption line if present
    body = re.sub(r"^\|\+.*", "", body, flags=re.MULTILINE)

    # ---- Extract headers (all lines starting with ! before first |-) ----
    header_lines: list[str] = []
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("!"):
            header_lines.append(stripped)
        elif stripped.startswith("|-"):
            break

    header_text = "\n".join(header_lines)
    headers = re.split(r"\n!\s*|!!", header_text)
    headers = [_clean_header_value(h) for h in headers if _clean_header_value(h)]

    if not headers:
        return []

    # ---- Extract rows ----
    rows_text = re.split(r"\n\|-\s*\n?", body)
    results: list[dict[str, str]] = []

    for row_text in rows_text[1:]:
        if not row_text.strip():
            continue
        cells = _parse_row_cells(row_text)
        if cells:
            row_dict: dict[str, str] = {}
            for i, h in enumerate(headers):
                row_dict[h] = cells[i] if i < len(cells) else ""
            results.append(row_dict)

    return results


def _clean_header_value(h: str) -> str:
    """Strip style/scope attributes from a raw header cell."""
    h = re.sub(r'scope="[^"]*"\s*\|\s*', "", h)
    h = re.sub(r'style="[^"]*"\s*\|\s*', "", h)
    h = h.strip()
    if h.startswith("!"):
        h = h[1:].strip()
    # Remove trailing pipe leftover from style| syntax
    if "|" in h:
        h = h.rsplit("|", 1)[-1].strip()
    return h.strip()


def _parse_row_cells(row_text: str) -> list[str]:
    """Extract cell values from a single row's wikitext lines."""
    cells: list[str] = []
    for line in row_text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("|-") or stripped.startswith("|}"):
            continue

        if stripped.startswith("||"):
            # Inline double-pipe on a continuation line
            for p in stripped[2:].split("||"):
                cells.append(_clean_cell_value(p))
        elif stripped.startswith("|"):
            cell_text = stripped[1:].strip()
            if "||" in cell_text:
                parts = cell_text.split("||")
                cells.append(_clean_cell_value(parts[0]))
                for p in parts[1:]:
                    cells.append(_clean_cell_value(p))
            else:
                cells.append(_clean_cell_value(cell_text))

    return cells


def _clean_cell_value(cell: str) -> str:
    """Strip style/class/colspan/rowspan attributes from a cell value."""
    cell = re.sub(
        r"^(style|class|rowspan|colspan)=\"[^\"]*\"\s*", "", cell
    )
    cell = cell.strip()
    cell = re.sub(r"\|\s*$", "", cell)
    if "|" in cell:
        cell = cell.rsplit("|", 1)[-1].strip()
    return cell


def style_cell(
    value: str,
    *,
    align: str | None = None,
    bold: bool = False,
    italic: bool = False,
    background: str | None = None,
    color: str | None = None,
    nowrap: bool = False,
    width: str | None = None,
    font_size: str | None = None,
) -> str:
    """Wrap a cell value with style attributes.

    Args:
        value: The raw cell content.
        align: 'left', 'center', 'right', or 'justify'.
        bold: Add font-weight: bold.
        italic: Add font-style: italic.
        background: CSS background-color value (e.g. '#fee', '#d5fdf4').
        color: CSS color value (e.g. 'red', '#333').
        nowrap: Add white-space: nowrap.
        width: CSS width value (e.g. '100px', '20%').
        font_size: CSS font-size value (e.g. '90%', '0.9em').

    Returns:
        A wikitable cell string like: | style="text-align: right;" | 42
    """
    styles: list[str] = []
    if align:
        styles.append(f"text-align: {align};")
    if bold:
        styles.append("font-weight: bold;")
    if italic:
        styles.append("font-style: italic;")
    if background:
        styles.append(f"background-color: {background};")
    if color:
        styles.append(f"color: {color};")
    if nowrap:
        styles.append("white-space: nowrap;")
    if width:
        styles.append(f"width: {width};")
    if font_size:
        styles.append(f"font-size: {font_size};")

    if not styles:
        return f"| {value}"
    style_str = " ".join(styles)
    return f'| style="{style_str}" | {value}'


def _auto_format_cell(val: str) -> str:
    """Auto-format a cell: right-align numbers, leave text left-aligned."""
    cleaned = val.replace(",", "").replace("$", "").replace("%", "").replace(" ", "")
    try:
        float(cleaned)
        return style_cell(val, align="right")
    except ValueError:
        # Check for percentage-like or currency-like with remaining chars
        pass
    return f"| {val}"
