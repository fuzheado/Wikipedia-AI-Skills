"""Tests for the CirrusSearch skill — search client, maintenance queries, and scripts."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Paths
SKILL_DIR = (
    Path(__file__).resolve().parent.parent
    / ".claude" / "skills" / "wikimedia-search-cirrussearch"
)
ASSETS_DIR = SKILL_DIR / "assets"
SCRIPTS_DIR = SKILL_DIR / "scripts"

sys.path.insert(0, str(ASSETS_DIR))

# Sample API response for testing
SAMPLE_SEARCH_RESPONSE = {
    "batchcomplete": "",
    "continue": {"sroffset": 2, "continue": "-||"},
    "query": {
        "searchinfo": {"totalhits": 42},
        "search": [
            {
                "ns": 0,
                "title": "Quantum mechanics",
                "pageid": 12345,
                "size": 50000,
                "wordcount": 7000,
                "snippet": "Quantum mechanics is a <span class='searchmatch'>fundamental</span> theory in physics",
                "timestamp": "2024-01-15T12:00:00Z",
                "score": 12.5,
            },
            {
                "ns": 0,
                "title": "Quantum field theory",
                "pageid": 12346,
                "size": 75000,
                "wordcount": 10000,
                "snippet": "In <span class='searchmatch'>quantum</span> field theory, particles are excitations",
                "timestamp": "2024-02-20T08:30:00Z",
                "score": 9.8,
            },
        ],
    },
}


# =========================================================================
# search_client tests
# =========================================================================


class TestCirrusClient:
    """Tests for the CirrusClient class."""

    def test_init_defaults(self):
        """Test default initialization."""
        from search_client import CirrusClient

        client = CirrusClient()
        assert client.wiki == "en.wikipedia.org"
        assert client.api_url == "https://en.wikipedia.org/w/api.php"
        assert client.timeout == 30
        assert client.retries == 3
        assert "ContentGapResearch" in client.session.headers["User-Agent"]

    def test_init_custom(self):
        """Test custom initialization."""
        from search_client import CirrusClient

        client = CirrusClient(
            wiki="commons.wikimedia.org",
            user_agent="TestBot/1.0 (test@example.com) TestProject",
            timeout=60,
            retries=5,
            backoff_factor=2.0,
        )
        assert client.wiki == "commons.wikimedia.org"
        assert client.api_url == "https://commons.wikimedia.org/w/api.php"
        assert client.timeout == 60
        assert client.retries == 5
        assert client.backoff_factor == 2.0

    @patch("search_client.requests.Session.get")
    def test_search_basic(self, mock_get):
        """Test basic full-text search."""
        from search_client import CirrusClient

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_SEARCH_RESPONSE
        mock_get.return_value = mock_resp

        client = CirrusClient()
        results = client.search("quantum mechanics", limit=10)

        assert len(results) == 2
        assert results[0]["title"] == "Quantum mechanics"
        assert results[1]["title"] == "Quantum field theory"

        # Verify API call parameters
        call_params = mock_get.call_args[1]["params"]
        assert call_params["list"] == "search"
        assert call_params["srsearch"] == "quantum mechanics"
        assert call_params["srwhat"] == "text"
        assert call_params["srlimit"] == 10

    @patch("search_client.requests.Session.get")
    def test_search_with_cirrus_syntax(self, mock_get):
        """Test search with CirrusSearch syntax keywords."""
        from search_client import CirrusClient

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_SEARCH_RESPONSE
        mock_get.return_value = mock_resp

        client = CirrusClient()
        results = client.search(
            'hastemplate:"Infobox scientist" incategory:"Nobel laureates"',
            limit=50,
        )

        call_params = mock_get.call_args[1]["params"]
        assert "hastemplate" in call_params["srsearch"]
        assert "incategory" in call_params["srsearch"]
        assert call_params["srlimit"] == 50

    @patch("search_client.requests.Session.get")
    def test_search_near(self, mock_get):
        """Test near-match title search."""
        from search_client import CirrusClient

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_SEARCH_RESPONSE
        mock_get.return_value = mock_resp

        client = CirrusClient()
        results = client.search_near("Albert Einstein")

        call_params = mock_get.call_args[1]["params"]
        assert call_params["srwhat"] == "near_match"

    @patch("search_client.requests.Session.get")
    def test_search_prefix(self, mock_get):
        """Test title prefix search."""
        from search_client import CirrusClient

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "query": {
                "pages": {
                    "123": {"pageid": 123, "ns": 0, "title": "Albert Einstein"},
                    "456": {"pageid": 456, "ns": 0, "title": "Albert Einstein Award"},
                }
            }
        }
        mock_get.return_value = mock_resp

        client = CirrusClient()
        results = client.search_prefix("Albert_E")

        assert len(results) == 2
        assert results[0]["title"] == "Albert Einstein"
        call_params = mock_get.call_args[1]["params"]
        assert call_params["generator"] == "prefixsearch"

    @patch("search_client.requests.Session.get")
    def test_get_total_hits(self, mock_get):
        """Test total hit count retrieval."""
        from search_client import CirrusClient

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_SEARCH_RESPONSE
        mock_get.return_value = mock_resp

        client = CirrusClient()
        total = client.get_total_hits("quantum mechanics")

        assert total == 42

    @patch("search_client.requests.Session.get")
    def test_search_batch(self, mock_get):
        """Test batch/paginated search."""
        from search_client import CirrusClient

        # First call returns 2 results, second call returns empty (done)
        page1 = dict(SAMPLE_SEARCH_RESPONSE)
        page2 = {
            "batchcomplete": "",
            "query": {"searchinfo": {"totalhits": 42}, "search": []},
        }

        mock_get.side_effect = [
            Mock(status_code=200, json=lambda: page1),
            Mock(status_code=200, json=lambda: page2),
        ]

        client = CirrusClient()
        results = list(client.search_batch("quantum", batch_size=2))

        assert len(results) == 2
        assert results[0]["title"] == "Quantum mechanics"

    @patch("search_client.requests.Session.get")
    def test_search_batch_max_results(self, mock_get):
        """Test batch search with max_results limit."""
        from search_client import CirrusClient

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_SEARCH_RESPONSE
        mock_get.return_value = mock_resp

        client = CirrusClient()
        results = list(client.search_batch("quantum", max_results=1))

        assert len(results) == 1

    @patch("search_client.requests.Session.get")
    def test_429_retry(self, mock_get):
        """Test retry on 429 Too Many Requests."""
        from search_client import CirrusClient

        mock_429 = Mock()
        mock_429.status_code = 429
        mock_429.headers = {"Retry-After": "1"}
        mock_429.raise_for_status.side_effect = (
            __import__("requests").HTTPError()
        )

        mock_ok = Mock()
        mock_ok.status_code = 200
        mock_ok.json.return_value = SAMPLE_SEARCH_RESPONSE

        mock_get.side_effect = [mock_429, mock_429, mock_ok]

        client = CirrusClient(retries=3, backoff_factor=0.01)
        results = client.search("quantum")

        assert len(results) == 2
        assert mock_get.call_count == 3

    @patch("search_client.requests.Session.get")
    def test_search_namespace(self, mock_get):
        """Test namespace filtering."""
        from search_client import CirrusClient

        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = SAMPLE_SEARCH_RESPONSE
        mock_get.return_value = mock_resp

        client = CirrusClient()
        client.search("test", namespace=14)  # Category namespace

        call_params = mock_get.call_args[1]["params"]
        assert call_params["srnamespace"] == 14

    def test_format_results_empty(self):
        """Test formatting empty results."""
        from search_client import CirrusClient

        client = CirrusClient()
        output = client.format_results([])
        assert "Results: 0" in output

    def test_format_results_with_data(self):
        """Test formatting search results."""
        from search_client import CirrusClient

        client = CirrusClient()
        output = client.format_results(
            SAMPLE_SEARCH_RESPONSE["query"]["search"]
        )
        assert "Quantum mechanics" in output
        assert "Quantum field theory" in output
        assert "Results: 2" in output


# =========================================================================
# maintenance_queries tests
# =========================================================================


class TestMaintenanceQueries:
    """Tests for maintenance query generators."""

    def test_unsourced_blp_query(self):
        """Test unsourced BLP query string."""
        from maintenance_queries import unsourced_blp

        q = unsourced_blp()
        assert 'hastemplate:"BLP unsourced"' in q
        assert 'incategory:"Living people"' in q

    def test_missing_image_query(self):
        """Test missing image query string."""
        from maintenance_queries import missing_image

        q = missing_image()
        assert 'hastemplate:"Infobox person"' in q
        assert 'insource:"|image ="' in q

    def test_missing_image_custom_template(self):
        """Test missing image with custom template name."""
        from maintenance_queries import missing_image

        q = missing_image(template="Infobox scientist")
        assert 'hastemplate:"Infobox scientist"' in q

    def test_recently_created_default(self):
        """Test recently created with default days."""
        from maintenance_queries import recently_created

        q = recently_created()
        assert "creationdate:>=today-7d" in q

    def test_recently_created_custom(self):
        """Test recently created with custom days."""
        from maintenance_queries import recently_created

        q = recently_created(days=30)
        assert "creationdate:>=today-30d" in q

    def test_linksto_page(self):
        """Test linksto query string."""
        from maintenance_queries import linksto_page

        q = linksto_page("Albert Einstein")
        assert 'linksto:"Albert Einstein"' in q

    def test_template_usage(self):
        """Test template usage query string."""
        from maintenance_queries import template_usage

        q = template_usage("Infobox scientist")
        assert 'hastemplate:"Infobox scientist"' in q

    def test_recent_in_category(self):
        """Test recent edits in a category."""
        from maintenance_queries import recent_in_category

        q = recent_in_category("Physics", days=3)
        assert 'incategory:"Physics"' in q
        assert "lasteditdate:>=today-3d" in q

    def test_subpages_of(self):
        """Test subpages query."""
        from maintenance_queries import subpages_of

        q = subpages_of("Wikipedia:WikiProject Physics")
        assert 'subpageof:"Wikipedia:WikiProject Physics"' in q

    def test_dead_links(self):
        """Test dead links query."""
        from maintenance_queries import dead_links

        q = dead_links()
        assert 'hastemplate:"Dead link"' in q

    def test_copyedit_needed(self):
        """Test copyedit needed query."""
        from maintenance_queries import copyedit_needed

        q = copyedit_needed()
        assert 'hastemplate:"Copy edit"' in q

    def test_pov_check(self):
        """Test POV check query."""
        from maintenance_queries import pov_check

        q = pov_check()
        assert 'hastemplate:"POV"' in q

    def test_search_by_date_range(self):
        """Test date range search."""
        from maintenance_queries import search_by_date_range

        q = search_by_date_range("2024-01-01", "2024-12-31")
        assert "creationdate:>=2024-01-01" in q
        assert "creationdate:<=2024-12-31" in q

    def test_all_queries_catalog_structure(self):
        """Test that the ALL_QUERIES catalog has the right structure."""
        from maintenance_queries import ALL_QUERIES

        assert len(ALL_QUERIES) > 0
        for key, entry in ALL_QUERIES.items():
            assert "query" in entry, f"{key} missing 'query' key"
            assert "description" in entry, f"{key} missing 'description' key"
            assert callable(entry["query"]), f"{key} query is not callable"

    def test_run_maintenance_query_invalid(self):
        """Test that invalid query type raises ValueError."""
        from maintenance_queries import run_maintenance_query

        with pytest.raises(ValueError, match="Unknown query type"):
            run_maintenance_query(None, "nonexistent-query")

    def test_format_results_empty(self):
        """Test formatting empty results."""
        from maintenance_queries import format_results

        output = format_results([], title="Test")
        assert "=== Test ===" in output
        assert "Results: 0" in output

    def test_format_results_with_data(self):
        """Test formatting results with data."""
        from maintenance_queries import format_results

        output = format_results(
            SAMPLE_SEARCH_RESPONSE["query"]["search"], title="Quantum"
        )
        assert "=== Quantum ===" in output
        assert "Quantum mechanics" in output
        assert "Results: 2" in output


# =========================================================================
# Script tests
# =========================================================================


class TestScripts:
    """Tests for shell scripts."""

    def test_cirrus_search_script_help(self):
        """Test cirrus-search.sh --help."""
        script = SCRIPTS_DIR / "cirrus-search.sh"
        assert script.exists(), f"Script not found: {script}"

        import subprocess
        result = subprocess.run(
            ["bash", str(script), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "CirrusSearch CLI" in result.stdout

    def test_cirrus_search_script_no_query(self):
        """Test cirrus-search.sh without query exits with error."""
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "cirrus-search.sh")],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0
        assert "missing search query" in result.stderr

    def test_maintenance_queries_script_list(self):
        """Test maintenance-queries.sh list."""
        script = SCRIPTS_DIR / "maintenance-queries.sh"
        import subprocess
        result = subprocess.run(
            ["bash", str(script), "list"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "unsourced-blp" in result.stdout
        assert "missing-image" in result.stdout

    def test_maintenance_queries_script_no_args(self):
        """Test maintenance-queries.sh without args."""
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "maintenance-queries.sh")],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0

    def test_maintenance_queries_missing_param(self):
        """Test that missing required param exits with error."""
        import subprocess
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "maintenance-queries.sh"),
             "recent-category"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0
        # Error message goes to stdout via echo in the script
        assert "CAT=" in result.stdout or "CAT=" in result.stderr

    def test_search_client_script_help(self):
        """Test search_client.py --help via python3."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "search_client.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout

    def test_maintenance_py_script_list(self):
        """Test maintenance_queries.py with 'list'."""
        import subprocess
        result = subprocess.run(
            ["python3", str(ASSETS_DIR / "maintenance_queries.py"), "list"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "unsourced-blp" in result.stdout
        assert "missing-image" in result.stdout


# =========================================================================
# Reference docs tests
# =========================================================================


class TestReferences:
    """Tests for reference documentation files."""

    def test_cirrus_syntax_ref_exists(self):
        """Test that the syntax reference exists and has content."""
        path = SKILL_DIR / "references" / "cirrus-syntax.md"
        assert path.exists()
        content = path.read_text()
        assert len(content) > 1000
        assert "intitle:" in content
        assert "insource:" in content
        assert "hastemplate:" in content
        assert "linksto:" in content
        assert "deepcategory:" in content
        assert "haswbstatement:" in content
        assert "prefix:" in content
        assert "subpageof:" in content

    def test_search_scenarios_ref_exists(self):
        """Test that the scenarios reference exists and has content."""
        path = SKILL_DIR / "references" / "search-scenarios.md"
        assert path.exists()
        content = path.read_text()
        assert len(content) > 2000
        assert "Maintenance" in content or "maintenance" in content
        assert "Patrolling" in content or "patrol" in content


# =========================================================================
# SKILL.md tests
# =========================================================================


class TestSkillFile:
    """Tests for the main SKILL.md file."""

    def test_skill_file_exists(self):
        """Test that SKILL.md exists."""
        path = SKILL_DIR / "SKILL.md"
        assert path.exists()

    def test_skill_file_has_yaml_frontmatter(self):
        """Test that SKILL.md has valid YAML frontmatter."""
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert content.startswith("---")
        # Find the closing ---
        second = content.find("---", 3)
        assert second > 3
        frontmatter = content[3:second].strip()
        assert "name:" in frontmatter
        assert "description:" in frontmatter
        assert "license: MIT" in frontmatter
        assert "last_verified:" in frontmatter
        assert "depends_on:" in frontmatter

    def test_skill_file_references_related_skills(self):
        """Test that SKILL.md cross-references related skills."""
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "wikimedia-api-access" in content
        assert "wikipedia-categories" in content
        assert "wikimedia-commons" in content

    def test_skill_file_has_guardrails(self):
        """Test that SKILL.md has a guardrails section."""
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "## Guardrails" in content or "### Guardrails" in content

    def test_skill_file_has_sops(self):
        """Test that SKILL.md has SOP sections."""
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "## SOP:" in content or "### SOP:" in content

    def test_skill_file_mentions_key_keywords(self):
        """Test that SKILL.md covers the core syntax keywords."""
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        for keyword in [
            "insource:", "hastemplate:", "linksto:", "deepcategory:",
            "haswbstatement:", "intitle:", "incategory:", "prefix:",
            "subpageof:", "morelike:",
        ]:
            assert keyword in content, f"Missing keyword in SKILL.md: {keyword}"

    def test_skill_file_has_ranking_caveats(self):
        """Test that SKILL.md has a ranking section."""
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "Ranking" in content

    def test_skill_file_has_maintenance_queries_section(self):
        """Test that SKILL.md has maintenance query examples."""
        path = SKILL_DIR / "SKILL.md"
        content = path.read_text()
        assert "Maintenance" in content or "maintenance" in content
