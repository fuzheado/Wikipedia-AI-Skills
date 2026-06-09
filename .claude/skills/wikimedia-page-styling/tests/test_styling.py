#!/usr/bin/env python3
"""
Tests for wikimedia-page-styling tools.
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


# --- Test CSS Validation ------------------------------------------------

class TestCSSPropertyValidation(unittest.TestCase):
    
    def setUp(self):
        # Import the validation logic
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    
    def test_allowed_property_detection(self):
        """Test that allowed CSS properties are correctly identified."""
        from assets.templatestyles_inspector import (
            ALLOWED_CSS_PROPERTIES, extract_css_properties, lint_css_properties
        )
        
        # Test allowed property
        css = ".my-class { display: grid; color: red; }"
        props = extract_css_properties(css)
        issues = lint_css_properties(props)
        self.assertEqual(len(issues), 0, "Allowed properties should not produce issues")
    
    def test_disallowed_property_detection(self):
        """Test that disallowed CSS properties are flagged."""
        from assets.templatestyles_inspector import (
            ALLOWED_CSS_PROPERTIES, extract_css_properties, lint_css_properties
        )
        
        # "foo-bar" is not a real CSS property and should be flagged
        css = ".x { foo-bar: baz; }"
        props = extract_css_properties(css)
        issues = lint_css_properties(props)
        self.assertGreater(len(issues), 0, "Disallowed property should produce an issue")
    
    def test_background_image_url_restricted(self):
        """Test that background-image: url() is flagged."""
        from assets.templatestyles_inspector import (
            extract_css_properties, lint_css_properties
        )
        
        css = ".x { background-image: url('http://evil.com/hack.png'); }"
        props = extract_css_properties(css)
        issues = lint_css_properties(props)
        url_issues = [i for i in issues if 'background-image' in i['property']]
        self.assertEqual(len(url_issues), 1, "background-image: url() should be flagged")
    
    def test_gradient_background_allowed(self):
        """Test that background-image with gradients is allowed."""
        from assets.templatestyles_inspector import (
            extract_css_properties, lint_css_properties
        )
        
        css = ".x { background-image: linear-gradient(red, blue); }"
        props = extract_css_properties(css)
        issues = lint_css_properties(props)
        grad_issues = [i for i in issues if i['property'] == 'background-image']
        self.assertEqual(len(grad_issues), 0, "Gradient backgrounds should be allowed")


class TestCSSPropertyExtraction(unittest.TestCase):
    
    def test_simple_properties(self):
        """Test extracting simple CSS properties."""
        from assets.templatestyles_inspector import extract_css_properties
        
        css = """
        .foo {
            color: red;
            font-size: 1.2em;
            display: flex;
        }
        """
        props = extract_css_properties(css)
        # Should find 3 properties
        prop_names = [p[0] for p in props]
        self.assertIn("color", prop_names)
        self.assertIn("font-size", prop_names)
        self.assertIn("display", prop_names)
    
    def test_commented_properties(self):
        """Test that commented-out CSS is not extracted."""
        from assets.templatestyles_inspector import extract_css_properties
        
        css = """
        .foo {
            color: red;
            /* display: none; */
            font-size: 1em;
        }
        """
        props = extract_css_properties(css)
        prop_names = [p[0] for p in props]
        self.assertIn("color", prop_names)
        self.assertNotIn("display", prop_names, "Commented property should not be extracted")
        self.assertIn("font-size", prop_names)


class TestGridLayoutPreview(unittest.TestCase):
    
    def test_grid_css_generation(self):
        """Test CSS grid code generation."""
        from assets.grid_layout_preview import generate_grid_css
        
        css = generate_grid_css("150px", "219px", "1.5rem", ".my-grid")
        self.assertIn("display: grid", css)
        self.assertIn("grid-template-columns: repeat(auto-fit, minmax(150px, 219px))", css)
        self.assertIn("gap: 1.5rem", css)
        self.assertIn(".my-grid", css)
    
    def test_estimate_columns(self):
        """Test column count estimation."""
        from assets.grid_layout_preview import estimate_columns
        
        # At 800px viewport, min 150px columns with 24px gap
        cols = estimate_columns(800, 150, 24)
        self.assertGreater(cols, 0)
        # At 360px viewport, should be at least 1
        cols = estimate_columns(360, 200, 24)
        self.assertGreaterEqual(cols, 1)


if __name__ == "__main__":
    unittest.main()
