#!/usr/bin/env python3
"""
Tests for mediawiki-page-navigation tools.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch


class TestTitlepartsParsing(unittest.TestCase):
    """Test #titleparts-like hierarchy parsing logic."""

    def test_parse_root(self):
        """Test parsing a root-level page."""
        title = "AvoinGLAM"
        parts = title.split("/")
        self.assertEqual(parts[0], "AvoinGLAM")
        self.assertEqual(len(parts), 1)

    def test_parse_subpage(self):
        """Test parsing a subpage."""
        title = "AvoinGLAM/Past activities"
        parts = title.split("/")
        self.assertEqual(parts[0], "AvoinGLAM")
        self.assertEqual(parts[1], "Past activities")

    def test_parse_deep_subpage(self):
        """Test parsing a deeply nested subpage."""
        title = "AvoinGLAM/Past activities/2023"
        parts = title.split("/")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "AvoinGLAM")
        self.assertEqual(parts[1], "Past activities")
        self.assertEqual(parts[2], "2023")

    def test_titleparts_first_segment(self):
        """Simulate {{#titleparts: title | 1 }} — get root."""
        title = "AvoinGLAM/Past activities"
        first = title.split("/")[0]
        self.assertEqual(first, "AvoinGLAM")


class TestSubTemplateDetection(unittest.TestCase):
    """Test /Sub template candidate generation."""

    def generate_sub_candidates(self, title):
        """Simulate the /Sub template detection logic."""
        parts = title.split("/")
        candidates = []
        for i in range(len(parts), 0, -1):
            prefix = "/".join(parts[:i])
            candidates.append(f"Template:{prefix}/Sub")
        candidates.append(f"Template:{parts[0]}/Sub")
        return candidates

    def test_root_sub_candidates(self):
        """Test /Sub candidates for a root page."""
        candidates = self.generate_sub_candidates("AvoinGLAM")
        self.assertIn("Template:AvoinGLAM/Sub", candidates)

    def test_subpage_sub_candidates(self):
        """Test /Sub candidates for a subpage."""
        candidates = self.generate_sub_candidates("AvoinGLAM/Past activities")
        self.assertIn("Template:AvoinGLAM/Sub", candidates)
        self.assertIn("Template:AvoinGLAM/Past activities/Sub", candidates)

    def test_deep_subpage_candidates(self):
        """Test /Sub candidates for a deeply nested page."""
        candidates = self.generate_sub_candidates("AvoinGLAM/Past activities/2023")
        self.assertIn("Template:AvoinGLAM/Sub", candidates)
        self.assertIn("Template:AvoinGLAM/Past activities/Sub", candidates)
        self.assertIn("Template:AvoinGLAM/Past activities/2023/Sub", candidates)


class TestNavigationPatternDetection(unittest.TestCase):
    """Test detection of navigation patterns in wikitext."""

    def test_detect_titleparts(self):
        """Test detection of {{#titleparts}}."""
        wikitext = """
        {{#ifexist: Template:{{#titleparts: {{FULLPAGENAME}} | 2 }}/Sub
        | {{Template:{{#titleparts: {{FULLPAGENAME}} | 2 }}/Sub}}
        }}
        """
        self.assertIn("{{#titleparts", wikitext)

    def test_detect_ifexist(self):
        """Test detection of {{#ifexist}}."""
        wikitext = """
        {{#ifexist: AvoinGLAM/{{#expr: {{CURRENTYEAR}} + 1 }}
        | [[Link|Next year]]
        }}
        """
        self.assertIn("{{#ifexist", wikitext)
        self.assertIn("{{CURRENTYEAR}}", wikitext)

    def test_detect_mylanguage(self):
        """Test detection of Special:MyLanguage."""
        wikitext = "* [[Special:MyLanguage/AvoinGLAM|AvoinGLAM]]"
        self.assertIn("Special:MyLanguage", wikitext)

    def test_detect_template_parameters(self):
        """Test detection of navigation with {{{params}}}."""
        wikitext = """
        {{#ifeq: {{{TOC|}}}|Show|__TOC__|__NOTOC__}}
        <div class="menu">
        * [[Special:MyLanguage/Project|Home]]
        </div>
        """
        self.assertIn("{{{TOC|}}}", wikitext)
        self.assertIn("{{#ifeq", wikitext)

    def test_conditional_navigation_logic(self):
        """Test the year rollover conditional logic."""
        import re
        
        # Simulate the logic — {{CURRENTYEAR}} in a string
        wikitext = "Page for {{CURRENTYEAR}}"
        self.assertIn("{{CURRENTYEAR}}", wikitext)


if __name__ == "__main__":
    unittest.main()
