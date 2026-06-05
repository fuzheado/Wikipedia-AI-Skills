"""Tests for the citation tools."""

import sys
from unittest.mock import MagicMock, patch
from pathlib import Path

import requests

import pytest

# Add assets directory to path
_assets = Path(__file__).resolve().parent.parent / \
    '.claude/skills/wikipedia-citations/assets'
sys.path.insert(0, str(_assets))
import wayback_inspector  # noqa: E402
import dead_link_scanner  # noqa: E402
import citation_linter  # noqa: E402
import citation_generator  # noqa: E402


class TestWaybackInspector:
    def test_check_archive_found(self):
        """Should parse Wayback Machine response with an existing archive."""
        with patch("wayback_inspector.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "archived_snapshots": {
                    "closest": {
                        "url": "https://web.archive.org/web/20260605000000/https://example.com",
                        "timestamp": "20260605000000",
                        "status": "200",
                    }
                }
            }
            mock_get.return_value = mock_resp

            result = wayback_inspector.check_archive("https://example.com")
            assert result["archive_url"] == "https://web.archive.org/web/20260605000000/https://example.com"
            assert result["timestamp"] == "20260605000000"

    def test_check_archive_not_found(self):
        """Should return archive_url=None when no archive exists."""
        with patch("wayback_inspector.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"archived_snapshots": {}}
            mock_get.return_value = mock_resp

            result = wayback_inspector.check_archive("https://example.com")
            assert result["archive_url"] is None

    def test_check_archive_error(self):
        """Should return error dict on network failure."""
        with patch("wayback_inspector.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

            result = wayback_inspector.check_archive("https://example.com")
            assert "error" in result

    def test_format_result_with_archive(self):
        result = wayback_inspector.format_result({
            "url": "https://example.com",
            "archive_url": "https://web.archive.org/web/20260605000000/https://example.com",
            "timestamp": "20260605000000",
        })
        assert "Archived" in result
        assert "2026-06-05" in result

    def test_format_result_no_archive(self):
        result = wayback_inspector.format_result({
            "url": "https://example.com",
            "archive_url": None,
        })
        assert "No archive found" in result


class TestDeadLinkScanner:
    def test_fetch_wikitext_success(self):
        with patch("dead_link_scanner.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "parse": {"wikitext": {"*": "Some wikitext with citations"}}
            }
            mock_get.return_value = mock_resp

            result = dead_link_scanner.fetch_wikitext("Test_Page")
            assert result == "Some wikitext with citations"

    def test_fetch_wikitext_error(self):
        with patch("dead_link_scanner.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.HTTPError("HTTP 404")

            result = dead_link_scanner.fetch_wikitext("Missing_Page")
            assert result is None

    def test_extract_citation_urls_template(self):
        wikitext = (
            'Some text.<ref>{{cite web |url=https://example.com/article |title=Test}}</ref>'
        )
        citations = dead_link_scanner.extract_citation_urls(wikitext)
        assert len(citations) == 1
        assert citations[0]["url"] == "https://example.com/article"
        assert citations[0]["type"] == "template"

    def test_extract_citation_urls_bare(self):
        wikitext = 'Some text.<ref>https://example.com/bare</ref>'
        citations = dead_link_scanner.extract_citation_urls(wikitext)
        assert len(citations) == 1
        assert citations[0]["url"] == "https://example.com/bare"
        assert citations[0]["type"] == "bare"

    def test_extract_citation_urls_mixed(self):
        wikitext = (
            '<ref>{{cite news |url=https://news.example.com |title=News}}</ref>'
            '<ref>https://bare.example.com</ref>'
        )
        citations = dead_link_scanner.extract_citation_urls(wikitext)
        assert len(citations) == 2
        types = [c["type"] for c in citations]
        assert "template" in types
        assert "bare" in types

    def test_extract_citation_urls_with_archive(self):
        wikitext = (
            '<ref>{{cite web |url=https://example.com |title=X'
            ' |archive-url=https://web.archive.org/web/2021/example.com'
            ' |archive-date=1 January 2021 |url-status=dead}}</ref>'
        )
        citations = dead_link_scanner.extract_citation_urls(wikitext)
        assert len(citations) == 1
        assert citations[0]["archive_url"] is not None
        assert citations[0]["url_status"] == "dead"

    def test_check_url_live(self):
        with patch("dead_link_scanner.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_get.return_value = mock_resp

            result = dead_link_scanner.check_url("https://example.com")
            assert result["status"] == "live"

    def test_check_url_dead(self):
        with patch("dead_link_scanner.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_get.return_value = mock_resp

            result = dead_link_scanner.check_url("https://example.com/404")
            assert result["status"] == "dead"

    def test_check_url_error(self):
        with patch("dead_link_scanner.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectTimeout("timeout")

            result = dead_link_scanner.check_url("https://example.com")
            assert result["status"] == "error"


class TestCitationGenerator:
    def test_generate_cite_web(self):
        result = citation_generator.generate_cite_web(
            url="https://example.com",
            title="Test Article",
            website="Example News",
            **{"access-date": "5 June 2026"},
        )
        assert "cite web" in result
        assert "https://example.com" in result
        assert "Test Article" in result
        assert "5 June 2026" in result

    def test_generate_cite_web_with_archive(self):
        result = citation_generator.generate_cite_web(
            url="https://example.com",
            title="Test",
            website="Ex",
            **{"access-date": "5 June 2026"},
            **{"archive-url": "https://web.archive.org/web/2021/example.com"},
            **{"archive-date": "1 January 2021"},
            **{"url-status": "dead"},
        )
        assert "archive-url" in result
        assert "url-status=dead" in result

    def test_generate_cite_news(self):
        result = citation_generator.generate_cite_news(
            url="https://news.com",
            title="News Article",
            newspaper="The Times",
            date="5 June 2026",
        )
        assert "cite news" in result
        assert "The Times" in result

    def test_generate_cite_book(self):
        result = citation_generator.generate_cite_book(
            title="My Book",
            author="Jane Smith",
            year="2026",
            publisher="Oxford University Press",
            isbn="978-0-262-52316-5",
        )
        assert "cite book" in result
        assert "Oxford University Press" in result
        assert "978-0-262-52316-5" in result

    def test_generate_cite_journal(self):
        result = citation_generator.generate_cite_journal(
            title="Research Paper",
            author="John Doe",
            journal="Nature Physics",
            volume="42",
            pages="123-145",
            doi="10.1000/xyz123",
        )
        assert "cite journal" in result
        assert "Nature Physics" in result
        assert "10.1000/xyz123" in result


class TestCitationLinter:
    def test_extract_parameters(self):
        params = citation_linter.extract_parameters("|url=https://example.com |title=Test |date=2026")
        assert params["url"] == "https://example.com"
        assert params["title"] == "Test"
        assert params["date"] == "2026"

    def test_extract_parameters_multiline(self):
        params = citation_linter.extract_parameters(
            "|url=https://example.com\n |title=Long\n Title\n |date=2026"
        )
        assert "url" in params
        assert "title" in params
        assert "date" in params

    def test_lint_citation_missing_required(self):
        match_data = ("{{cite web |url=https://example.com}}", "cite web", " |url=https://example.com")
        
        class MockMatch:
            def group(self, n):
                return match_data[n]
            def groupdict(self):
                return {}
        
        result = citation_linter.lint_citation(MockMatch())
        assert result["template"] == "cite web"
        # title is missing, so there should be an issue about it
        assert any("title" in i for i in result["issues"])

    def test_lint_citation_complete(self):
        match_data = (
            "{{cite web |url=https://example.com |title=Test |website=Ex |access-date=2026}}",
            "cite web",
            " |url=https://example.com |title=Test |website=Ex |access-date=2026",
        )
        
        class MockMatch:
            def group(self, n):
                return match_data[n]
        
        result = citation_linter.lint_citation(MockMatch())
        assert result["template"] == "cite web"
        assert result["has_access_date"] is True

    def test_lint_citation_with_archive_no_access_date(self):
        match_data = (
            "{{cite web |url=https://example.com |title=T |archive-url=https://archive.org/web/...}}",
            "cite web",
            " |url=https://example.com |title=T |archive-url=https://archive.org/web/...",
        )
        
        class MockMatch:
            def group(self, n):
                return match_data[n]
        
        result = citation_linter.lint_citation(MockMatch())
        assert any("archive-url" in i and "access-date" in i for i in result["issues"])

    def test_lint_citation_url_status_no_archive(self):
        match_data = (
            "{{cite web |url=https://example.com |title=T |url-status=dead}}",
            "cite web",
            " |url=https://example.com |title=T |url-status=dead",
        )
        
        class MockMatch:
            def group(self, n):
                return match_data[n]
        
        result = citation_linter.lint_citation(MockMatch())
        assert any("url-status" in i and "archive-url" in i for i in result["issues"])
