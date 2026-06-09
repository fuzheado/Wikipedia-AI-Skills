"""Test suite for wikitable generation, parsing, and styling.

Run:  python3 -m pytest test_wikitable_tools.py -v
"""

from __future__ import annotations

from wikitable_tools import (
    dicts_to_wikitable,
    csv_to_wikitable,
    parse_wikitable,
    style_cell,
)


# =========================================================================
# Generation — dicts_to_wikitable
# =========================================================================


def test_basic_dicts():
    """Simple two-row table should produce valid markup."""
    data = [{"Name": "Alice", "Score": "95"}, {"Name": "Bob", "Score": "87"}]
    result = dicts_to_wikitable(data)
    assert result.startswith('{| class="wikitable sortable"')
    assert result.endswith("|}")
    assert "! scope=\"col\" | Name" in result
    assert "| Alice" in result
    assert "| Bob" in result
    # Numeric auto-alignment
    assert 'style="text-align: right;" | 95' in result
    assert 'style="text-align: right;" | 87' in result


def test_with_caption():
    """Caption should appear as |+ ... right after the table open."""
    data = [{"X": "1"}]
    result = dicts_to_wikitable(data, caption="Test Table")
    assert "|+ Test Table" in result


def test_with_custom_classes():
    """Custom classes should replace the default."""
    data = [{"X": "1"}]
    result = dicts_to_wikitable(data, classes="wikitable mw-collapsible")
    assert 'class="wikitable mw-collapsible"' in result
    assert 'class="wikitable sortable"' not in result


def test_with_alignment():
    """Table-wide alignment should produce a style on the opening tag."""
    data = [{"X": "1"}]
    result = dicts_to_wikitable(data, alignment="center")
    assert 'style="text-align: center;"' in result


def test_empty_data():
    """Empty data should produce an empty string."""
    assert dicts_to_wikitable([]) == ""


def test_single_row():
    """Single-row table should still produce valid markup."""
    data = [{"Name": "Alice", "Age": "30"}]
    result = dicts_to_wikitable(data)
    assert "! " in result  # header row
    assert "| Alice" in result
    assert "|-" in result  # row separator


def test_multi_word_headers():
    """Headers with spaces should work."""
    data = [{"Full Name": "Alice Smith", "Test Score": "95"}]
    result = dicts_to_wikitable(data)
    assert 'scope="col" | Full Name' in result
    assert 'scope="col" | Test Score' in result


# =========================================================================
# Generation — csv_to_wikitable
# =========================================================================


def test_basic_csv():
    csv_text = "Name,Score\nAlice,95\nBob,87"
    result = csv_to_wikitable(csv_text)
    assert 'scope="col" | Name' in result
    assert "| Alice" in result
    assert "| Bob" in result


def test_csv_with_commas_in_values():
    csv_text = 'Name,Description\nAlice,"High, medium, low"\nBob,"Simple"'
    result = csv_to_wikitable(csv_text)
    assert "| Alice" in result
    assert "High, medium, low" in result


# =========================================================================
# Styling — style_cell
# =========================================================================


def test_style_align_right():
    result = style_cell("42", align="right")
    assert 'style="text-align: right;"' in result
    assert "| 42" in result


def test_style_center():
    result = style_cell("Hello", align="center")
    assert 'style="text-align: center;"' in result


def test_style_bold():
    result = style_cell("Important", bold=True)
    assert "font-weight: bold;" in result


def test_style_background():
    result = style_cell("Warn", background="#fee")
    assert 'background-color: #fee;' in result


def test_style_multiple():
    result = style_cell("42", align="right", bold=True, background="#efe")
    assert "text-align: right;" in result
    assert "font-weight: bold;" in result
    assert "background-color: #efe;" in result


def test_style_no_args():
    """No style args should produce a plain cell."""
    result = style_cell("plain")
    assert result == "| plain"


def test_style_color_and_nowrap():
    result = style_cell("Text", color="#333", nowrap=True)
    assert "color: #333;" in result
    assert "white-space: nowrap;" in result


# =========================================================================
# Parsing — parse_wikitable
# =========================================================================


def test_parse_basic():
    wikitext = """{| class="wikitable"
! Name
! Score
|-
| Alice
| 95
|-
| Bob
| 87
|}"""
    rows = parse_wikitable(wikitext)
    assert len(rows) == 2
    assert rows[0]["Name"] == "Alice"
    assert rows[0]["Score"] == "95"
    assert rows[1]["Name"] == "Bob"
    assert rows[1]["Score"] == "87"


def test_parse_with_inline_style():
    wikitext = """{| class="wikitable sortable"
! scope="col" | Name
! scope="col" | Score
|-
| style="text-align: right;" | 42
| Alice
|}"""
    rows = parse_wikitable(wikitext)
    assert len(rows) == 1
    # Style text should be stripped from the value
    assert "text-align" not in rows[0]["Name"]
    assert rows[0]["Name"] != ""


def test_parse_empty():
    assert parse_wikitable("") == []
    assert parse_wikitable("No table here") == []


def test_parse_no_header():
    """A table without a header row should return []."""
    wikitext = """{| class="wikitable"
|-
| just
| data
|}"""
    rows = parse_wikitable(wikitext)
    assert rows == []


def test_parse_single_row():
    wikitext = """{| class="wikitable"
! X
|-
| 1
|}"""
    rows = parse_wikitable(wikitext)
    assert len(rows) == 1
    assert rows[0]["X"] == "1"


def test_parse_with_caption():
    wikitext = """{| class="wikitable"
|+ Scores
! Name
! Score
|-
| Alice
| 95
|}"""
    rows = parse_wikitable(wikitext)
    assert len(rows) == 1
    assert rows[0]["Name"] == "Alice"


# =========================================================================
# Round-trip: generate → parse
# =========================================================================


def test_round_trip():
    data = [{"Name": "Alice", "Score": "95"}, {"Name": "Bob", "Score": "87"}]
    wikitext = dicts_to_wikitable(data)
    parsed = parse_wikitable(wikitext)
    assert parsed == data


def test_round_trip_single():
    data = [{"X": "hello"}]
    wikitext = dicts_to_wikitable(data, caption="Test")
    parsed = parse_wikitable(wikitext)
    assert parsed == data


# =========================================================================
# Real-world pattern: NPP patrol report
# =========================================================================


def test_patrol_report_table():
    """Simulate the kind of table npp-finder produces."""
    data = [
        {"Title": "[[LOL: Slutty Bass]]", "Creator": "Vvenom974",
         "Edits": "148", "Size": "4,364", "Refs": "3", "URL": "0"},
        {"Title": "[[Betka Ait Mokran]]", "Creator": "Naslechat",
         "Edits": "402", "Size": "2,175", "Refs": "2", "URL": "0"},
    ]
    result = dicts_to_wikitable(data, caption="NPP Report")
    assert "|+ NPP Report" in result
    assert "[[LOL: Slutty Bass]]" in result
    assert "[[Betka Ait Mokran]]" in result
    # Edits column should be right-aligned (numeric)
    assert 'style="text-align: right;" | 148' in result
    assert 'style="text-align: right;" | 4,364' in result
