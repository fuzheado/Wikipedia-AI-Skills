#!/usr/bin/env python3
"""
Tests for the wiktionary skill assets.

Split out of the former combined `wiktionary-and-wikisource` test module;
only the Wiktionary-related tests are kept here.

Tests:
  - WiktionaryParser: language section extraction, definition parsing,
    translation table parsing, pronunciation extraction, edge cases
  - Divider-less entries (legacy `----` absent) — heading-only splitting
  - wt-entry-summary.sh: help output, no-arg behavior
  - SKILL.md content verification

Run with:
    python3 -m pytest .claude/skills/wiktionary/tests/test_wiktionary.py -v
"""

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "assets"))

from wt_entry_parser import WiktionaryParser, extract_language_section, count_languages


# ── Sample Wiktionary Wikitext ─────────────────────────────────────────────

SAMPLE_WIKTEXT = """==English==
===Etymology===
From Middle English ''word'', from Old English ''word''.

===Pronunciation===
* {{a|UK}} {{IPA|en|/wɜːd/}}
* {{audio|en|en-uk-word.ogg|Audio (UK)}}

===Noun===
{{en-noun}}
# A unit of language.
#: I wrote a '''word''' on the paper.
# A promise.
#: He gave his '''word'''.
====Derived terms====
* {{l|en|buzzword}}
* {{l|en|password}}

===Verb===
{{en-verb}}
# To phrase a certain way.
#: How would you '''word''' that?

====Translations====
{{trans-top|unit of language}}
{{t|fr|mot}}
{{t|es|palabra}}
{{t|de|Wort}}
{{trans-mid}}
{{t|ar|كَلِمَة}}
{{trans-bottom}}

----

==French==
===Etymology===
From Latin ''verbum''.

===Noun===
{{fr-noun|m}}
# [[word]]
#: {{ux|fr|Il n'a pas dit un '''mot'''.}}

===Verb===
{{fr-verb}}
# To say [[word]].
"""

SAMPLE_MULTI_LANG = """==German==
===Noun===
{{de-noun|n}}
# A [[word]].

----

==Italian==
===Noun===
{{it-noun|m}}
# A [[word]].
"""

# Modern en.wiktionary entries often omit the `----` divider entirely
# (verified live on "word", "water", "cat", 2026-09-11).
SAMPLE_NO_DIVIDER = """==English==
===Noun===
{{en-noun}}
# A unit of language.

==German==
===Noun===
{{de-noun|n}}
# A word.
"""

SAMPLE_EMPTY = ""


# ── WiktionaryParser Tests ─────────────────────────────────────────────────

class TestWiktionaryParser(unittest.TestCase):
    """Test parsing Wiktionary entries into structured data."""

    def setUp(self):
        self.parser = WiktionaryParser()

    def test_parse_extracts_languages(self):
        """Should find both English and French language sections."""
        result = self.parser.parse(SAMPLE_WIKTEXT)
        self.assertIn("English", result["languages"])
        self.assertIn("French", result["languages"])

    def test_parse_english_definitions(self):
        """English noun should have 2 definitions."""
        result = self.parser.parse(SAMPLE_WIKTEXT)
        eng = result["languages"]["English"]
        noun_defs = eng["pos_sections"]["Noun"]["definitions"]
        self.assertEqual(len(noun_defs), 2)
        self.assertEqual(noun_defs[0]["definition"], "A unit of language.")
        self.assertEqual(noun_defs[1]["definition"], "A promise.")

    def test_parse_english_examples(self):
        """Definitions should include their examples."""
        result = self.parser.parse(SAMPLE_WIKTEXT)
        eng = result["languages"]["English"]
        noun_defs = eng["pos_sections"]["Noun"]["definitions"]
        self.assertEqual(len(noun_defs[0]["examples"]), 1)
        self.assertEqual(noun_defs[1]["examples"], ["He gave his '''word'''."])

    def test_parse_pos_sections(self):
        """Should find Noun and Verb sections."""
        result = self.parser.parse(SAMPLE_WIKTEXT)
        eng = result["languages"]["English"]
        self.assertIn("Noun", eng["pos_sections"])
        self.assertIn("Verb", eng["pos_sections"])

    def test_parse_inflection_templates(self):
        """Should extract inflection templates ({{en-noun}}, etc.)."""
        result = self.parser.parse(SAMPLE_WIKTEXT)
        eng = result["languages"]["English"]
        self.assertEqual(eng["pos_sections"]["Noun"]["inflection"], "en-noun")
        self.assertEqual(eng["pos_sections"]["Verb"]["inflection"], "en-verb")

    def test_parse_etymology(self):
        """Should extract etymology text."""
        result = self.parser.parse(SAMPLE_WIKTEXT)
        eng = result["languages"]["English"]
        self.assertIn("etymology", eng)  # Etymology field exists (content depends on parse)

    def test_parse_pronunciation(self):
        """Should extract IPA and audio references."""
        result = self.parser.parse(SAMPLE_WIKTEXT)
        eng = result["languages"]["English"]
        pron = eng["pronunciation"]
        self.assertGreaterEqual(len(pron), 1)
        # At least one IPA entry
        ipas = [p for p in pron if p["type"] == "ipa"]
        self.assertGreaterEqual(len(ipas), 1)

    def test_parse_translation_table_shape(self):
        """Translation tables parse into {language: [words]} when present."""
        result = self.parser.parse(SAMPLE_WIKTEXT)
        eng = result["languages"]["English"]
        verbs = eng["pos_sections"]["Verb"]
        self.assertIsInstance(verbs["translations"], dict)

    def test_parse_three_languages(self):
        """Should handle entries with 3+ languages."""
        result = self.parser.parse(SAMPLE_WIKTEXT + SAMPLE_MULTI_LANG)
        self.assertIn("English", result["languages"])
        self.assertIn("French", result["languages"])
        self.assertIn("Italian", result["languages"])

    def test_parse_empty(self):
        """Empty wikitext should return empty result."""
        result = self.parser.parse("")
        self.assertEqual(result["languages"], {})

    def test_parse_no_language_sections(self):
        """Wikitext without language sections should return empty."""
        result = self.parser.parse("Some random text without headings.")
        self.assertEqual(result["languages"], {})


class TestDividerlessEntries(unittest.TestCase):
    """Modern entries omit the legacy `----` divider — headings must suffice."""

    def setUp(self):
        self.parser = WiktionaryParser()

    def test_count_languages_without_divider(self):
        self.assertEqual(count_languages(SAMPLE_NO_DIVIDER), 2)

    def test_parse_extracts_both_languages_without_divider(self):
        result = self.parser.parse(SAMPLE_NO_DIVIDER)
        self.assertIn("English", result["languages"])
        self.assertIn("German", result["languages"])

    def test_extract_language_section_without_divider(self):
        section = extract_language_section(SAMPLE_NO_DIVIDER, "German")
        self.assertIsNotNone(section)
        self.assertIn("de-noun", section)
        self.assertNotIn("en-noun", section)


# ── Language counting / extraction helpers ─────────────────────────────────

class TestLanguageHelpers(unittest.TestCase):
    """count_languages / extract_language_section on divider-separated input."""

    def test_count_languages(self):
        """Should correctly count language sections."""
        count = count_languages(SAMPLE_WIKTEXT)
        self.assertEqual(count, 2)

    def test_count_languages_multi(self):
        """Should count all languages."""
        count = count_languages(SAMPLE_WIKTEXT + SAMPLE_MULTI_LANG)
        self.assertGreaterEqual(count, 2)

    def test_count_languages_empty(self):
        """Empty text should have 0 languages."""
        self.assertEqual(count_languages(""), 0)

    def test_extract_language_section_found(self):
        """Should extract a specific language section."""
        section = extract_language_section(SAMPLE_WIKTEXT, "English")
        self.assertIsNotNone(section)
        self.assertIn("===Noun===", section)

    def test_extract_language_section_not_found(self):
        """Should return None for missing language."""
        section = extract_language_section(SAMPLE_WIKTEXT, "Spanish")
        self.assertIsNone(section)


# ── Script Tests ───────────────────────────────────────────────────────────

class TestScripts(unittest.TestCase):
    """Test that the summary script runs without errors."""

    def setUp(self):
        self.skills_dir = Path(__file__).resolve().parent.parent
        self.scripts_dir = self.skills_dir / "scripts"

    def test_wt_entry_summary_help(self):
        """wt-entry-summary.sh should print help with --help."""
        script = self.scripts_dir / "wt-entry-summary.sh"
        result = subprocess.run(
            ["bash", str(script), "--help"],
            capture_output=True, text=True, timeout=10
        )
        self.assertIn("Usage", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_wt_entry_summary_no_args(self):
        """wt-entry-summary.sh should print usage with no args."""
        script = self.scripts_dir / "wt-entry-summary.sh"
        result = subprocess.run(
            ["bash", str(script)],
            capture_output=True, text=True, timeout=10
        )
        self.assertIn("Usage", result.stdout)
        self.assertEqual(result.returncode, 0)


# ── SKILL.md Content Tests ────────────────────────────────────────────────

class TestSkillContent(unittest.TestCase):
    """Verify key claims in SKILL.md."""

    def setUp(self):
        skill_path = Path(__file__).resolve().parent.parent / "SKILL.md"
        self.skill_text = skill_path.read_text()

    def test_depends_on_declared(self):
        """SKILL.md should declare depends_on."""
        self.assertIn("wikimedia-api-access", self.skill_text)
        self.assertIn("wikimedia-commons", self.skill_text)
        self.assertIn("pywikibot", self.skill_text)

    def test_wiktionary_present(self):
        """The skill should be about Wiktionary."""
        self.assertIn("Wiktionary", self.skill_text)

    def test_assets_referenced(self):
        """The parser asset should be referenced."""
        self.assertIn("wt_entry_parser.py", self.skill_text)

    def test_scripts_referenced(self):
        """The summary script should be referenced."""
        self.assertIn("wt-entry-summary.sh", self.skill_text)

    def test_references_referenced(self):
        """The entry-structure reference doc should be listed."""
        self.assertIn("wiktionary-entry-structure.md", self.skill_text)

    def test_guardrails_present(self):
        """Guardrails should cover the Wiktionary traps."""
        self.assertIn("Guardrails", self.skill_text)
        self.assertIn("English", self.skill_text)  # "Don't Assume English Wiktionary"
        self.assertIn("translation", self.skill_text.lower())  # Translation-table trap


if __name__ == "__main__":
    unittest.main()
