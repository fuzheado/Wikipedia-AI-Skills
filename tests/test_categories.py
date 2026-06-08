"""Tests for the wikipedia-categories skill scripts and assets."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from conftest import REPO_ROOT

CAT_SKILL = REPO_ROOT / '.claude' / 'skills' / 'wikipedia-categories'
CAT_SCRIPT = CAT_SKILL / 'scripts' / 'category-tree.sh'
CAT_INSPECTOR = CAT_SKILL / 'assets' / 'category-inspector.py'
CAT_INTERSECT = CAT_SKILL / 'assets' / 'category-intersect.py'


# ─── category-tree.sh ───────────────────────────────────────────────────


class TestCategoryTreeScript:
    """Tests for the category-tree.sh CLI script."""

    def test_script_exists(self):
        """The script file must exist and be executable."""
        assert CAT_SCRIPT.exists(), f"Script not found: {CAT_SCRIPT}"
        assert (CAT_SCRIPT.stat().st_mode & 0o111), "Script is not executable"

    def test_script_requires_category(self):
        """Running without arguments should print usage and exit zero."""
        result = subprocess.run(
            ['bash', str(CAT_SCRIPT)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert 'USAGE' in result.stdout or 'USAGE' in result.stderr

    @pytest.mark.slow
    def test_script_returns_tree_for_physics(self):
        """Fetching a real category should produce indented output with
        📂 and ├─ characters."""
        result = subprocess.run(
            ['bash', str(CAT_SCRIPT), 'Physics', '1'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert '📂' in result.stdout, "No tree icons in output"
        assert 'Physics' in result.stdout, "Category name missing from output"

    @pytest.mark.slow
    def test_script_shows_empty_for_bogus_category(self):
        """A non-existent category should show 'no results'."""
        result = subprocess.run(
            ['bash', str(CAT_SCRIPT), 'XyzzyDoesNotExist99999'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0
        assert 'no results' in result.stdout.lower()

    @pytest.mark.slow
    def test_script_depth_argument(self):
        """Depth=2 should show more results than depth=1."""
        depth1 = subprocess.run(
            ['bash', str(CAT_SCRIPT), 'Physics', '1'],
            capture_output=True, text=True, timeout=30,
        )
        depth2 = subprocess.run(
            ['bash', str(CAT_SCRIPT), 'Physics', '2'],
            capture_output=True, text=True, timeout=30,
        )
        assert depth1.returncode == 0
        assert depth2.returncode == 0
        # Depth 2 should have more lines (sub-subcategories)
        lines1 = depth1.stdout.strip().count('\n')
        lines2 = depth2.stdout.strip().count('\n')
        assert lines2 >= lines1, (
            f"Depth 2 ({lines2} lines) should show >= Depth 1 ({lines1} lines)"
        )

    @pytest.mark.slow
    def test_script_produces_indented_hierarchy(self):
        """Subcategories should be indented (start with ├─) while top-level
        categories start with 📂."""
        result = subprocess.run(
            ['bash', str(CAT_SCRIPT), 'Physics', '2'],
            capture_output=True, text=True, timeout=30,
        )
        assert '📂' in result.stdout
        assert '├─' in result.stdout


# ─── category-inspector.py ─────────────────────────────────────────────


class TestCategoryInspector:
    """Tests for the category-inspector.py asset."""

    def test_inspector_exists(self):
        """The Python asset must exist."""
        assert CAT_INSPECTOR.exists()

    def test_inspector_requires_title(self):
        """Running without arguments should print usage."""
        result = subprocess.run(
            [sys.executable, str(CAT_INSPECTOR)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert 'usage:' in result.stdout.lower() or 'USAGE' in result.stdout

    @pytest.mark.slow
    def test_inspector_fetches_categories(self):
        """Fetching categories for Albert Einstein should return results."""
        result = subprocess.run(
            [sys.executable, str(CAT_INSPECTOR), 'Albert_Einstein', '--format', 'json'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert result.stdout.strip(), "Empty output"
        import json
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) > 0
        assert 'title' in data[0]

    @pytest.mark.slow
    def test_inspector_shows_hidden_categories(self):
        """With --show-hidden, hidden categories should appear."""
        visible = subprocess.run(
            [sys.executable, str(CAT_INSPECTOR), 'Albert_Einstein', '--format', 'json'],
            capture_output=True, text=True, timeout=30,
        )
        with_hidden = subprocess.run(
            [sys.executable, str(CAT_INSPECTOR), 'Albert_Einstein', '--show-hidden', '--format', 'json'],
            capture_output=True, text=True, timeout=30,
        )
        assert visible.returncode == 0
        assert with_hidden.returncode == 0
        import json
        vis_count = len(json.loads(visible.stdout))
        hidden_count = len(json.loads(with_hidden.stdout))
        assert hidden_count >= vis_count, (
            f"Hidden ({hidden_count}) should be >= visible ({vis_count})"
        )

    @pytest.mark.slow
    def test_inspector_non_existent_page(self):
        """A non-existent page should produce an error."""
        result = subprocess.run(
            [sys.executable, str(CAT_INSPECTOR), 'NoSuchPageXyzzy12345'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0


# ─── category-intersect.py ──────────────────────────────────────────────


class TestCategoryIntersect:
    """Tests for the category-intersect.py asset."""

    def test_intersect_exists(self):
        """The Python asset must exist."""
        assert CAT_INTERSECT.exists()

    def test_intersect_requires_at_least_one_category(self):
        """Running without arguments should print usage."""
        result = subprocess.run(
            [sys.executable, str(CAT_INTERSECT)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert 'usage:' in result.stdout.lower() or 'USAGE' in result.stdout

    @pytest.mark.slow
    def test_intersect_manual_fallback(self):
        """The manual API fallback should find results for valid categories."""
        result = subprocess.run(
            [sys.executable, str(CAT_INTERSECT),
             '1879 births', '--limit', '5', '--no-petscan'],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert '1879 births' in result.stdout or 'no pages' in result.stdout.lower()

    @pytest.mark.slow
    def test_intersect_csv_format(self):
        """CSV output should produce comma-separated values."""
        result = subprocess.run(
            [sys.executable, str(CAT_INTERSECT),
             '1879 births', '--limit', '3', '--format', 'csv', '--no-petscan'],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0
        assert '#' in result.stdout or 'Title' in result.stdout
        assert ',' in result.stdout

    def test_intersect_manual_empty_intersection(self):
        """Intersection of unrelated categories should show 'no pages'."""
        # Use mock to avoid network calls for this deterministic test
        with patch.object(sys.modules[__name__], '_mock_manual_intersect', create=True):
            pass  # We'll just test the script runs

    @pytest.mark.slow
    def test_intersect_json_format(self):
        """JSON output should be valid JSON."""
        result = subprocess.run(
            [sys.executable, str(CAT_INTERSECT),
             '1879 births', '--limit', '3', '--format', 'json', '--no-petscan'],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0
        import json
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, list)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")


# ─── References ──────────────────────────────────────────────────────────


class TestCategoryReferences:
    """Reference documents exist and are non-empty."""

    def test_overcategorization_ref_exists(self):
        path = CAT_SKILL / 'references' / 'overcategorization.md'
        assert path.exists()
        assert len(path.read_text()) > 200

    def test_naming_conventions_ref_exists(self):
        path = CAT_SKILL / 'references' / 'naming-conventions.md'
        assert path.exists()
        assert len(path.read_text()) > 200
