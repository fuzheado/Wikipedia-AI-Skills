"""Test suite for the reference URL checker.

Covers: raw URLs, citation templates with/without URL, named ref
resolution, shortened footnotes, nested templates, empty pages,
self-closing tags, reused named refs, and infobox detection.

Run:  python3 -m pytest test_ref_checker.py -v
"""

from __future__ import annotations

from ref_url_checker import has_any_url_refs, has_infobox


# =========================================================================
# has_any_url_refs — basic cases
# =========================================================================


def test_bare_url_in_ref():
    """A bare URL inside a ref tag should count as having a URL."""
    wikitext = "Some text.<ref>https://example.com/article</ref>"
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is True
    assert total == 1
    assert url_count == 1


def test_cite_web_with_url():
    """A {{cite web}} with a url= parameter counts as having a URL."""
    wikitext = (
        'Content.<ref>{{cite web |url=https://example.com |'
        'title=Example}}</ref>'
    )
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is True
    assert total == 1
    assert url_count == 1


def test_cite_book_no_url():
    """A {{cite book}} without url= counts as not having a URL."""
    wikitext = (
        "<ref>{{cite book |title=The Book |author=Smith |year=2020}}</ref>"
    )
    has_url, total, url_count, samples = has_any_url_refs(wikitext)
    assert has_url is False
    assert total == 1
    assert url_count == 0
    assert "[cite book]" in samples[0]


def test_mixed_refs():
    """When some refs have URLs and some don't, has_url should be True."""
    wikitext = (
        "First.<ref>{{cite web |url=https://example.com}}</ref>"
        "Second.<ref>{{cite book |title=The Book}}</ref>"
    )
    has_url, total, url_count, samples = has_any_url_refs(wikitext)
    assert has_url is True  # at least one has a URL
    assert total == 2
    assert url_count == 1
    assert len(samples) == 1  # only the one without URL


def test_plain_text_ref():
    """A plain-text ref with no template and no URL."""
    wikitext = "<ref>Smith, J. The Book. Penguin, 2020, p. 42.</ref>"
    has_url, total, url_count, samples = has_any_url_refs(wikitext)
    assert has_url is False
    assert total == 1
    assert url_count == 0
    # Should show the actual text, not "[template]"
    assert "Smith" in samples[0]


def test_empty_ref():
    """An empty ref tag should be ignored."""
    wikitext = "Content.<ref /><ref></ref>"
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert total == 0


def test_no_refs():
    """A page with no ref tags should have zero references."""
    wikitext = "This is a simple page with no references."
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert total == 0
    assert has_url is False


# =========================================================================
# Named refs
# =========================================================================


def test_named_ref_definition_with_url():
    """Named ref definition with URL should count."""
    wikitext = (
        'Content.<ref name="src">{{cite web |url=https://example.com '
        '|title=Ex}}</ref> More text.<ref name="src" />'
    )
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is True
    assert total == 1  # counted once despite 2 occurrences
    assert url_count == 1


def test_named_ref_definition_no_url():
    """Named ref definition without URL should not count."""
    wikitext = (
        'Content.<ref name="book">{{cite book |title=The Book}}</ref>'
        'More text.<ref name="book" />'
    )
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is False
    assert total == 1
    assert url_count == 0


def test_named_ref_reuse_before_definition():
    """Reuse before definition should still resolve correctly."""
    wikitext = (
        'First.<ref name="src" /> More.<ref name="src">'
        '{{cite web |url=https://example.com}}</ref>'
    )
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is True
    assert total == 1
    assert url_count == 1


# =========================================================================
# Shortened footnotes
# =========================================================================


def test_harvsp_no_url():
    """A {{harvsp}} reference should be detected as having no URL."""
    wikitext = "<ref>{{harvsp|Smith|2020|p=42}}</ref>"
    has_url, total, url_count, samples = has_any_url_refs(wikitext)
    assert has_url is False
    assert total == 1
    assert "[harvsp]" in samples[0]


def test_sfn_no_url():
    """An {{sfn}} reference should be detected as having no URL."""
    wikitext = "<ref>{{sfn|Jones|2019|p=100}}</ref>"
    has_url, total, url_count, samples = has_any_url_refs(wikitext)
    assert has_url is False
    assert total == 1
    assert url_count == 0


def test_harvnb_no_url():
    """An {{harvnb}} reference should be detected as having no URL."""
    wikitext = "<ref>{{harvnb|Brown|2018}}</ref>"
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is False
    assert total == 1
    assert url_count == 0


# =========================================================================
# Citation template URL parameter variants
# =========================================================================


def test_archive_url_counts_as_url():
    """archive-url= should count as having a URL."""
    wikitext = (
        "<ref>{{cite web |archive-url=https://archive.org/example "
        "|url=https://original.example.com}}</ref>"
    )
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is True
    assert url_count == 1


def test_chapter_url_counts_as_url():
    """chapter-url= should count as having a URL."""
    wikitext = (
        "<ref>{{cite book |chapter-url=https://example.com/chapter "
        "|title=The Book}}</ref>"
    )
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is True
    assert url_count == 1


# =========================================================================
# Nested templates
# =========================================================================


def test_nested_cite_inside_ref():
    """A {{cite web}} nested inside a ref with URL should detect it."""
    wikitext = "<ref>{{cite web|url=https://example.com|title=Test}}</ref>"
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is True
    assert url_count == 1


def test_nested_template_without_url():
    """A template nested inside a ref without URL should not have URL."""
    wikitext = "<ref>{{cite book|title=X|year=2020}}</ref>"
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is False
    assert url_count == 0


# =========================================================================
# Multiple refs and edge cases
# =========================================================================


def test_multiple_refs_all_no_url():
    """Multiple refs, all without URLs."""
    wikitext = (
        "A.<ref>{{cite book|title=A}}</ref>"
        "B.<ref>{{cite journal|title=B}}</ref>"
        "C.<ref>Plain text ref</ref>"
    )
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is False
    assert total == 3
    assert url_count == 0


def test_different_url_param_capitalization():
    """URL parameter with different capitalization should still match."""
    wikitext = (
        "<ref>{{cite web|URL=https://example.com|title=Test}}</ref>"
    )
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    assert has_url is True
    assert url_count == 1


def test_page_with_bibliography_section():
    """A full page with bibliography section and shortened footnotes."""
    wikitext = (
        "Page text.<ref>{{harvsp|Smith|2020}}</ref>\n\n"
        "== Bibliography ==\n"
        "* {{cite book |last=Smith |title=The Book |year=2020}}"
    )
    has_url, total, url_count, _ = has_any_url_refs(wikitext)
    # The harvsp ref has no URL; the bibliography cite has no URL either.
    # Step 4 catches bibliography cites as inline refs.
    assert has_url is False
    assert total == 2   # 1 from <ref>, 1 from inline bibliograpy
    assert url_count == 0


# =========================================================================
# has_infobox
# =========================================================================


def test_has_infobox():
    """Detect an infobox template."""
    wikitext = "{{Infobox person |name=John Doe}}"
    assert has_infobox(wikitext) is True


def test_has_infobox_case_insensitive():
    """Infobox detection should be case-insensitive."""
    wikitext = "{{INFOBOX settlement|name=City}}"
    assert has_infobox(wikitext) is True


def test_no_infobox():
    """Page without any infobox should return False."""
    wikitext = "{{Some other template}}"
    assert has_infobox(wikitext) is False


def test_infobox_variant_spellings():
    """Various common infobox template names should match."""
    templates = [
        "{{Infobox person}}",
        "{{Infobox settlement}}",
        "{{Infobox film}}",
        "{{Infobox company}}",
        "{{Infobox military conflict}}",
        "{{Infobox book}}",
    ]
    for t in templates:
        assert has_infobox(t) is True, f"Failed for {t}"


def test_empty_string_has_no_infobox():
    """Empty wikitext should not raise errors."""
    assert has_infobox("") is False


# =========================================================================
# Real-world scenarios
# =========================================================================


def test_npp_candidate_pattern():
    """Simulates the exact pattern npp-finder catches."""
    wikitext = (
        "'''Article Name''' is a topic.{{Infobox person|name=John}}\n\n"
        "== Early life ==\n"
        "He was born in 1990.<ref>{{cite news|title=Birth announcement|"
        "newspaper=Local Paper|date=1990}}</ref>\n\n"
        "== Career ==\n"
        "He started working in 2010.<ref>{{cite web|"
        "url=https://example.com/career|title=Career|website=Example}}"
        "</ref>\n\n"
        "== References ==\n"
        "{{reflist}}"
    )
    has_url, total, url_count, samples = has_any_url_refs(wikitext)
    assert has_url is True  # second ref has a URL
    assert total == 2
    assert url_count == 1
    # The first ref should be in the bad_samples
    assert len(samples) == 1


def test_all_bad_npp_pattern():
    """A page where no refs have URLs — the npp-finder target."""
    wikitext = (
        "'''Article''' is a topic.\n\n"
        "== History ==\n"
        "Founded in 1900.<ref>{{cite book|title=History of X|"
        "author=Smith|year=1950}}</ref>\n\n"
        "== Notable people ==\n"
        "John Doe (born 1920).<ref>{{cite journal|title=Biography|"
        "journal=Local Journal|volume=5|pages=10-15}}</ref>\n\n"
        "== References ==\n"
        "{{reflist}}"
    )
    has_url, total, url_count, samples = has_any_url_refs(wikitext)
    assert has_url is False
    assert total == 2
    assert url_count == 0
    assert len(samples) == 2
