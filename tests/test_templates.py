"""Tests for the wikipedia-templates skill scripts and assets."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from conftest import REPO_ROOT

TMPL_SKILL = REPO_ROOT / '.claude' / 'skills' / 'wikipedia-templates'
TMPL_EXPAND = TMPL_SKILL / 'scripts' / 'expand-template.sh'
TMPL_USAGE = TMPL_SKILL / 'scripts' / 'template-usage.sh'
TMPL_INSPECT = TMPL_SKILL / 'scripts' / 'inspect-template.sh'
TMPL_INSPECTOR = TMPL_SKILL / 'assets' / 'template-inspector.py'
TMPL_SCANNER = TMPL_SKILL / 'assets' / 'template-scanner.py'


# ─── expand-template.sh ──────────────────────────────────────────────────


class TestExpandTemplateScript:
    """Tests for the expand-template.sh CLI script."""

    def test_script_exists(self):
        """The script file must exist and be executable."""
        assert TMPL_EXPAND.exists(), f"Script not found: {TMPL_EXPAND}"
        assert (TMPL_EXPAND.stat().st_mode & 0o111), "Script is not executable"

    def test_script_requires_template(self):
        """Running without arguments should print usage and exit non-zero."""
        result = subprocess.run(
            ['bash', str(TMPL_EXPAND)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0
        assert 'Error:' in result.stdout or 'Error:' in result.stderr
        assert 'Usage:' in result.stdout or 'Usage:' in result.stderr

    def test_script_accepts_help(self):
        """--help should show usage and exit zero."""
        result = subprocess.run(
            ['bash', str(TMPL_EXPAND), '--help'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert 'Usage:' in result.stdout

    def test_script_accepts_stdin_mode(self):
        """The - argument should be accepted for stdin mode."""
        result = subprocess.run(
            ['bash', str(TMPL_EXPAND), '-'],
            capture_output=True, text=True, timeout=10,
            input='{{Test}}',
        )
        # Should at least not crash on the curl call (will fail at API, but
        # shouldn't error out before trying)
        assert result.returncode in (0, 1)

    @pytest.mark.slow
    def test_expand_simple_template(self):
        """Expanding a simple template should return wikitext output."""
        result = subprocess.run(
            ['bash', str(TMPL_EXPAND), 'CURRENTYEAR'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        # CURRENTYEAR should expand to a 4-digit year
        assert any(c.isdigit() for c in result.stdout)

    @pytest.mark.slow
    def test_expand_with_parameters(self):
        """Expanding with parameters should work."""
        result = subprocess.run(
            ['bash', str(TMPL_EXPAND), 'Abbr', '1=etc|2=et cetera'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert 'et cetera' in result.stdout or '<abbr' in result.stdout

    @pytest.mark.slow
    def test_expand_non_existent_template(self):
        """A non-existent template should still return some output."""
        result = subprocess.run(
            ['bash', str(TMPL_EXPAND), 'NoSuchTemplateXyzzy12345'],
            capture_output=True, text=True, timeout=30,
        )
        # Should produce output regardless (templates don't error on
        # the API level, they just fail to expand)
        assert result.returncode == 0, f"Exit {result.returncode}: {result.stderr}"


# ─── template-usage.sh ──────────────────────────────────────────────────


class TestTemplateUsageScript:
    """Tests for the template-usage.sh CLI script."""

    def test_script_exists(self):
        """The script file must exist and be executable."""
        assert TMPL_USAGE.exists(), f"Script not found: {TMPL_USAGE}"
        assert (TMPL_USAGE.stat().st_mode & 0o111), "Script is not executable"

    def test_script_requires_template(self):
        """Running without arguments should print usage and exit non-zero."""
        result = subprocess.run(
            ['bash', str(TMPL_USAGE)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0
        assert 'Error:' in result.stdout or 'Error:' in result.stderr

    def test_script_accepts_help(self):
        """--help should show usage and exit zero."""
        result = subprocess.run(
            ['bash', str(TMPL_USAGE), '--help'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert 'Usage:' in result.stdout

    @pytest.mark.slow
    def test_usage_common_template(self):
        """Checking usage of a common template should find pages."""
        result = subprocess.run(
            ['bash', str(TMPL_USAGE), 'Cn', '--limit', '5'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        # Should show at least some results
        assert 'Template:Cn' in result.stdout or '|' in result.stdout

    @pytest.mark.slow
    def test_usage_with_count(self):
        """--count should show a total."""
        result = subprocess.run(
            ['bash', str(TMPL_USAGE), 'Stub', '--count', '--limit', '3'],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert 'Total' in result.stdout


# ─── inspect-template.sh ────────────────────────────────────────────────


class TestInspectTemplateScript:
    """Tests for the inspect-template.sh CLI script."""

    def test_script_exists(self):
        """The script file must exist and be executable."""
        assert TMPL_INSPECT.exists(), f"Script not found: {TMPL_INSPECT}"
        assert (TMPL_INSPECT.stat().st_mode & 0o111), "Script is not executable"

    def test_script_requires_template(self):
        """Running without arguments should print usage and exit non-zero."""
        result = subprocess.run(
            ['bash', str(TMPL_INSPECT)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0
        assert 'Error:' in result.stdout or 'Error:' in result.stderr

    def test_script_accepts_help(self):
        """--help should show usage and exit zero."""
        result = subprocess.run(
            ['bash', str(TMPL_INSPECT), '--help'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert 'Usage:' in result.stdout

    @pytest.mark.slow
    def test_inspect_known_template(self):
        """Inspecting a known template should return protection info."""
        result = subprocess.run(
            ['bash', str(TMPL_INSPECT), 'Infobox person', '--protection'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert 'Protection' in result.stdout or 'protection' in result.stdout

    @pytest.mark.slow
    def test_inspect_with_modules(self):
        """--modules should show Lua dependencies for a Lua-backed template."""
        result = subprocess.run(
            ['bash', str(TMPL_INSPECT), 'Infobox settlement', '--modules'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        # This template IS Lua-backed, should show module deps
        assert 'Lua' in result.stdout or 'Module' in result.stdout

    @pytest.mark.slow
    def test_inspect_non_existent_template(self):
        """A non-existent template should produce an error."""
        result = subprocess.run(
            ['bash', str(TMPL_INSPECT), 'NoSuchTemplateXyzzy12345'],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode != 0
        assert 'not found' in result.stderr.lower()


# ─── template-inspector.py ──────────────────────────────────────────────


class TestTemplateInspector:
    """Tests for the template-inspector.py asset."""

    def test_inspector_exists(self):
        """The Python asset must exist."""
        assert TMPL_INSPECTOR.exists()

    def test_inspector_requires_title(self):
        """Running without arguments should show usage."""
        result = subprocess.run(
            [sys.executable, str(TMPL_INSPECTOR)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0
        assert 'usage:' in result.stderr.lower() or 'Usage:' in result.stderr

    def test_inspector_accepts_help(self):
        """--help should show usage and exit zero."""
        result = subprocess.run(
            [sys.executable, str(TMPL_INSPECTOR), '--help'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert 'usage:' in result.stdout.lower()

    def test_parameters_extraction_simple(self):
        """Test that parameter extraction works on sample source."""
        # Use import to test the function directly
        sys.path.insert(0, str(TMPL_SKILL / 'assets'))
        try:
            import template_inspector as ti
        except ImportError:
            # Try alternative import
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "template_inspector", str(TMPL_INSPECTOR))
            ti = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ti)

        source = "{{{1}}} {{{2|default}}} {{{name|}}} {{{required_param}}}"
        params = ti.extract_parameters(source)
        assert len(params["positional"]) >= 1
        assert len(params["named"]) >= 1
        assert "2" in params["with_defaults"]
        assert params["with_defaults"]["2"] == "default"

    def test_lua_call_extraction(self):
        """Test that Lua #invoke calls are correctly extracted."""
        sys.path.insert(0, str(TMPL_SKILL / 'assets'))
        try:
            import template_inspector as ti
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "template_inspector", str(TMPL_INSPECTOR))
            ti = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ti)

        source = "{{#invoke:Infobox|infobox}} {{#invoke:String|replace|source=test}}"
        calls = ti.extract_lua_calls(source)
        assert len(calls) == 2
        assert calls[0]["module"] == "Infobox"
        assert calls[0]["function"] == "infobox"
        assert calls[1]["module"] == "String"
        assert calls[1]["function"] == "replace"

    def test_include_tag_extraction(self):
        """Test that include tags are correctly counted."""
        sys.path.insert(0, str(TMPL_SKILL / 'assets'))
        try:
            import template_inspector as ti
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "template_inspector", str(TMPL_INSPECTOR))
            ti = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ti)

        source = ("<noinclude>{{Documentation}}</noinclude>\n"
                  "<includeonly>[[Category:Test]]</includeonly>\n"
                  "<onlyinclude>Content</onlyinclude>\n")
        tags = ti.extract_include_tags(source)
        assert tags["noinclude"] == 1
        assert tags["includeonly"] == 1
        assert tags["onlyinclude"] == 1

    def test_classify_template(self):
        """Test template classification by source."""
        sys.path.insert(0, str(TMPL_SKILL / 'assets'))
        try:
            import template_inspector as ti
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "template_inspector", str(TMPL_INSPECTOR))
            ti = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ti)

        assert ti.classify_template("{{Navbox|name=Test}}", "Template:Test") == "navigation"
        assert ti.classify_template("{{Infobox|title=Test}}", "Template:Infobox person") == "infobox"
        assert ti.classify_template("{{cite web|url=...}}", "Template:Cite web") == "citation"
        assert ti.classify_template("#REDIRECT [[Other]]", "Template:Redirect") == "redirect"

    def test_normalize_title(self):
        """Test title normalization."""
        sys.path.insert(0, str(TMPL_SKILL / 'assets'))
        try:
            import template_inspector as ti
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "template_inspector", str(TMPL_INSPECTOR))
            ti = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ti)

        assert ti.normalize_title("Infobox person") == "Template:Infobox person"
        assert ti.normalize_title("Template:Cn") == "Template:Cn"
        assert ti.normalize_title("Module:Infobox") == "Module:Infobox"

    def test_json_output_format(self):
        """JSON output should be parseable (using mock to avoid API call)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "template_inspector", str(TMPL_INSPECTOR))
        ti = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ti)

        # Mock the fetch_basic_info to return a non-existent result
        with patch.object(ti, 'fetch_basic_info', return_value={
            'exists': True,
            'title': 'Template:Infobox person',
            'pageid': 12345,
            'protection': [{'type': 'edit', 'level': 'templateeditor', 'expiry': 'infinity'}],
            'pageprops': {'noeditsection': ''}
        }):
            with patch.object(ti, 'fetch_source', return_value=(
                '<noinclude>{{Documentation}}</noinclude>\n'
                '<includeonly>[[Category:Infobox templates]]</includeonly>\n'
                '{{Infobox\n| name = {{{name|}}}\n| birth_date = {{{birth_date|}}}\n}}'
            )):
                with patch.object(ti, 'fetch_templates', return_value=[
                    {'ns': 10, 'title': 'Template:Infobox'},
                    {'ns': 10, 'title': 'Template:Documentation'},
                ]):
                    result = ti.analyze_template("TestTemplate")
                    assert isinstance(result, dict)
                    assert "title" in result
                    assert result['exists'] is True
                    assert result['classification'] == 'infobox'
                    assert len(result['parameters']['named']) == 2

    @pytest.mark.slow
    @pytest.mark.slow
    def test_inspector_real_template(self):
        """Inspecting a real template should work."""
        result = subprocess.run(
            [sys.executable, str(TMPL_INSPECTOR), "Infobox person", "--format", "json"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert data.get("exists") is True
        # Classification may vary by API response; just check it exists
        assert "classification" in data

    @pytest.mark.slow
    @pytest.mark.slow
    def test_inspector_non_existent(self):
        """A non-existent template should report does not exist."""
        result = subprocess.run(
            [sys.executable, str(TMPL_INSPECTOR), "NoSuchTemplateXyzzy12345"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Expected exit 0, got: {result.stderr}"
        assert 'does not exist' in result.stdout.lower()


# ─── template-scanner.py ────────────────────────────────────────────────


class TestTemplateScanner:
    """Tests for the template-scanner.py asset."""

    def test_scanner_exists(self):
        """The Python asset must exist."""
        assert TMPL_SCANNER.exists()

    def test_scanner_requires_title(self):
        """Running without arguments should show usage."""
        result = subprocess.run(
            [sys.executable, str(TMPL_SCANNER)],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0
        assert 'usage:' in result.stderr.lower() or 'Usage:' in result.stderr

    def test_scanner_accepts_help(self):
        """--help should show usage and exit zero."""
        result = subprocess.run(
            [sys.executable, str(TMPL_SCANNER), '--help'],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert 'usage:' in result.stdout.lower()

    def test_classify_template_name(self):
        """Test template name classification logic directly."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "template_scanner", str(TMPL_SCANNER))
        ts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ts)

        assert ts.classify_template_name("Infobox person") == "infobox"
        assert ts.classify_template_name("Cite web") == "citation"
        assert ts.classify_template_name("Navbox") == "navbox"
        assert ts.classify_template_name("Cn") == "maintenance"
        assert ts.classify_template_name("About") == "hatnote"
        assert ts.classify_template_name("physics-stub") == "stub"
        assert ts.classify_template_name("WikiProject Physics") == "banner"
        assert ts.classify_template_name("Start date") == "date_and_format"
        assert ts.classify_template_name("Convert") == "date_and_format"
        assert ts.classify_template_name("TOC left") == "structural"
        assert ts.classify_template_name("Listen") == "media"
        assert ts.classify_template_name("Welcome") == "user_talk"
        assert ts.classify_template_name("Documentation") == "template_doc"
        assert ts.classify_template_name("SomeCustomTemplate") == "other"

    def test_lua_backed_detection(self):
        """Test Lua-backed template detection."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "template_scanner", str(TMPL_SCANNER))
        ts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ts)

        assert ts.is_lua_backed("Template:Infobox settlement") is True
        assert ts.is_lua_backed("Infobox video game") is True
        assert ts.is_lua_backed("Navbox") is True
        assert ts.is_lua_backed("Infobox person") is False
        assert ts.is_lua_backed("Template:Cn") is False

    def test_json_output_format(self):
        """JSON output should be valid."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "template_scanner", str(TMPL_SCANNER))
        ts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ts)

        # Test with mock data
        page_info = {"title": "Test", "pageid": 1}
        by_type = {"infobox": [{"title": "Template:Infobox person", "ns": 10, "type": "infobox", "lua_backed": False}]}
        modules = []
        others = []
        js = ts.format_json_result(page_info, by_type, modules, others)
        data = json.loads(js)
        assert data["page"] == "Test"
        assert data["total_templates"] == 1

    @pytest.mark.slow
    @pytest.mark.slow
    def test_scanner_real_page(self):
        """Scanning a real page should produce output."""
        result = subprocess.run(
            [sys.executable, str(TMPL_SCANNER), "Albert Einstein", "--flat"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert result.stdout.strip(), "Expected non-empty output"
        assert 'Page:' in result.stdout or 'page:' in result.stdout.lower()

    @pytest.mark.slow
    @pytest.mark.slow
    def test_scanner_with_modules(self):
        """--modules should show Lua dependencies."""
        result = subprocess.run(
            [sys.executable, str(TMPL_SCANNER), "Berlin", "--modules"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Should produce some output about modules
        assert result.stdout.strip(), "Expected non-empty output"

    @pytest.mark.slow
    @pytest.mark.slow
    def test_scanner_json_format(self):
        """JSON output should be valid JSON."""
        result = subprocess.run(
            [sys.executable, str(TMPL_SCANNER), "Albert Einstein", "--format", "json"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert "page" in data
        assert "total_templates" in data


# ─── References ──────────────────────────────────────────────────────────


class TestTemplateReferences:
    """Reference documents exist and are non-empty."""

    def test_parser_functions_ref_exists(self):
        path = TMPL_SKILL / 'references' / 'parser-functions.md'
        assert path.exists()
        assert len(path.read_text()) > 200

    def test_magic_words_ref_exists(self):
        path = TMPL_SKILL / 'references' / 'magic-words.md'
        assert path.exists()
        assert len(path.read_text()) > 200

    def test_template_types_ref_exists(self):
        path = TMPL_SKILL / 'references' / 'template-types.md'
        assert path.exists()
        assert len(path.read_text()) > 200

    def test_all_references_have_content(self):
        """All references should be substantial documents."""
        ref_dir = TMPL_SKILL / 'references'
        for f in ref_dir.iterdir():
            if f.suffix == '.md':
                content = f.read_text()
                assert len(content) > 500, (
                    f"Reference {f.name} is too short ({len(content)} chars)"
                )
