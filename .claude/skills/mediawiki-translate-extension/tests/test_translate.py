#!/usr/bin/env python3
"""
Tests for mediawiki-translate-extension tools.
"""

import os
import sys
import unittest


class TestTranslateUnitExtraction(unittest.TestCase):
    """Test extraction of translation units from wikitext."""

    def setUp(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    def test_extract_simple_translate_blocks(self):
        """Test extracting simple <translate> sections."""
        from assets.translation_checker import extract_translate_units

        wikitext = """
        <languages />
        <translate>
        == Hello == <!--T:1-->
        Welcome to our page. <!--T:2-->
        </translate>
        """
        units = extract_translate_units(wikitext)
        self.assertEqual(len(units), 2)

    def test_extract_translate_unit_ids(self):
        """Test that translation unit IDs are correctly extracted."""
        from assets.translation_checker import extract_translate_units

        wikitext = """
        <translate>
        First unit <!--T:1-->
        Second unit <!--T:5-->
        Third unit <!--T:10-->
        </translate>
        """
        units = extract_translate_units(wikitext)
        unit_ids = sorted([u["id"] for u in units])
        self.assertIn(1, unit_ids)
        self.assertIn(5, unit_ids)
        self.assertIn(10, unit_ids)

    def test_extract_multiple_translate_sections(self):
        """Test extracting units from multiple <translate> sections."""
        from assets.translation_checker import extract_translate_units

        wikitext = """
        <translate>First section <!--T:1--></translate>
        Some non-translatable content.
        <translate>Second section <!--T:2--></translate>
        """
        units = extract_translate_units(wikitext)
        self.assertEqual(len(units), 2)

    def test_detect_tvar(self):
        """Test detection of <tvar> variables."""
        from assets.translation_checker import extract_translate_units

        wikitext = """
        <translate>
        Text with <tvar name="url">https://example.org</tvar> variable. <!--T:1-->
        Plain text. <!--T:2-->
        </translate>
        """
        units = extract_translate_units(wikitext)
        units_with_tvar = [u for u in units if u["has_tvar"]]
        self.assertEqual(len(units_with_tvar), 1)

    def test_extract_tvar_names(self):
        """Test extraction of <tvar> variable names."""
        from assets.translation_checker import extract_tvar_variables

        wikitext = """
        <translate>
        <tvar name="url">https://x.org</tvar>
        <tvar name="count">42</tvar>
        <tvar name="project">{{SITENAME}}</tvar>
        </translate>
        """
        tvars = extract_tvar_variables(wikitext)
        self.assertIn("url", tvars)
        self.assertIn("count", tvars)
        self.assertIn("project", tvars)

    def test_no_translate_blocks(self):
        """Test behavior when there are no <translate> blocks."""
        from assets.translation_checker import extract_translate_units

        wikitext = "This page has no translate tags."
        units = extract_translate_units(wikitext)
        self.assertEqual(len(units), 0)


class TestTemplateTranslationScanner(unittest.TestCase):
    """Test template translation compliance checking."""

    def setUp(self):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    def test_detect_translate_tags(self):
        """Test detection of <translate> tags."""
        from assets.template_translation_scanner import check_translate_coverage

        wikitext_with = "<translate>Some translatable text here.</translate>"
        wikitext_without = "Some text without translate tags."

        cov_with = check_translate_coverage(wikitext_with)
        cov_without = check_translate_coverage(wikitext_without)

        self.assertGreater(cov_with, 0)
        # Without any translate tags, coverage should be 0
        self.assertEqual(cov_without, 0.0)

    def test_detect_bare_labels(self):
        """Test detection of hardcoded labels not in <translate>."""
        from assets.template_translation_scanner import check_bare_labels

        # Labels NOT wrapped in translate
        wikitext = """
        <translate>Good label</translate>
        * [[Project/Page|Bad label]]
        """
        issues = check_bare_labels(wikitext)
        self.assertIn("Bad label", issues)

        # All labels wrapped in translate
        wikitext = """
        <translate>
        * [[Project/Page|Good label]]
        </translate>
        """
        issues = check_bare_labels(wikitext)
        self.assertEqual(len(issues), 0)

    def test_mylanguage_detection(self):
        """Test detection of Special:MyLanguage."""
        from assets.translation_checker import check_special_mylanguage_usage

        wikitext = "* [[Special:MyLanguage/Project|Home]]"
        count = check_special_mylanguage_usage(wikitext)
        self.assertEqual(count, 1)

        wikitext = "* [[Project|Home]]"
        count = check_special_mylanguage_usage(wikitext)
        self.assertEqual(count, 0)

    def test_timef_detection(self):
        """Test detection of #timef usage."""
        from assets.translation_checker import check_timef_usage

        wikitext = "{{#timef:2024-05-06|date}}"
        count = check_timef_usage(wikitext)
        self.assertEqual(count, 1)

        wikitext = "{{#time:Y-m-d|2024-05-06}}"
        count = check_timef_usage(wikitext)
        self.assertEqual(count, 0)


class TestRulesEngine(unittest.TestCase):
    """Test the compliance rules engine."""

    def test_rule_matching(self):
        """Test that individual rules match correctly."""
        from assets.template_translation_scanner import RULES

        rules_dict = {r["id"]: r for r in RULES}

        # Test translate-labels rule
        self.assertTrue(rules_dict["translate-labels"]["check"](
            "<translate>Hello</translate>"
        ))
        self.assertFalse(rules_dict["translate-labels"]["check"](
            "Hello"
        ))

        # Test mylanguage-links rule
        self.assertTrue(rules_dict["mylanguage-links"]["check"](
            "[[Special:MyLanguage/Project|Link]]"
        ))
        self.assertFalse(rules_dict["mylanguage-links"]["check"](
            "[[Project|Link]]"
        ))

        # Test languages-bar rule
        self.assertTrue(rules_dict["languages-bar"]["check"](
            "<languages />"
        ))
        self.assertTrue(rules_dict["languages-bar"]["check"](
            "<languages/>"
        ))
        self.assertFalse(rules_dict["languages-bar"]["check"](
            "No languages bar"
        ))


if __name__ == "__main__":
    unittest.main()
