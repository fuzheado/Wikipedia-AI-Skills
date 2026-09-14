#!/usr/bin/env python3
"""
Tests for the Wikisource skill assets and documentation.

Tests:
  - ProofreadChecker: work stats computation (mocked), page status, quality labels
  - TextExtractor: markup stripping, page text extraction
  - WsNamespaceResolver: content-model resolution, alias/fallback behaviour,
    the T74525 traps (non-portable IDs and names; Index ID not Page+2)
  - WsIndexClient: catalogue envelope, totals, pagination, QID scan
  - Scripts: help output, no-arg behaviour
  - SKILL.md content verification (including the documented traps)

Run with:
    python3 -m pytest .claude/skills/wikisource/tests/test_wikisource.py -v
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "assets"))

from ws_proofread_checker import ProofreadChecker  # noqa: E402
from ws_text_extractor import TextExtractor  # noqa: E402
import ws_namespace_resolver as nsr  # noqa: E402
import ws_catalog  # noqa: E402


# ── ProofreadChecker Tests ────────────────────────────────────────────────

class TestProofreadChecker(unittest.TestCase):
    """Test proofreading status queries (mocked API)."""

    def setUp(self):
        self.checker = ProofreadChecker("en")

    @patch("ws_proofread_checker.requests.Session.get")
    def test_get_work_stats(self, mock_get):
        """Work stats should compute correct totals."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "query": {
                "pages": {
                    "100": {
                        "pageid": 100,
                        "title": "Index:Test.djvu",
                        "proofreadinfo": {
                            "quality": {"1": 3, "2": 3, "3": 2, "4": 2, "5": 2}
                        },
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        stats = self.checker.get_work_stats("Index:Test.djvu")
        self.assertEqual(stats["total"], 5)
        self.assertEqual(stats["validated"], 2)
        self.assertEqual(stats["proofread"], 3)
        self.assertEqual(stats["problematic"], 0)
        self.assertEqual(stats["without_text"], 0)
        self.assertAlmostEqual(stats["percent_done"], 100.0)

    @patch("ws_proofread_checker.requests.Session.get")
    def test_get_work_stats_empty(self, mock_get):
        """Empty work should return zero stats."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"query": {"pages": {"-1": {}}}}
        mock_get.return_value = mock_resp

        stats = self.checker.get_work_stats("Index:Nonexistent.djvu")
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["percent_done"], 0.0)

    def test_get_page_status_not_found(self):
        """Non-existent page should return 'Not found'."""
        with patch("ws_proofread_checker.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "query": {"pages": {"-1": {"missing": True}}}
            }
            mock_get.return_value = mock_resp
            status = self.checker.get_page_status("Page:Nonexistent/1")
            self.assertEqual(status["quality_label"], "Not found")

    def test_get_progress_summary(self):
        """Progress summary should be a formatted string."""
        with patch.object(self.checker, "get_work_stats") as mock_stats:
            mock_stats.return_value = {
                "total": 100, "without_text": 10, "problematic": 5,
                "proofread": 40, "validated": 45, "percent_done": 85.0,
            }
            summary = self.checker.get_progress_summary("Index:Test.djvu")
            self.assertIn("100 pages", summary)
            self.assertIn("45 validated", summary)
            self.assertIn("85.0%", summary)

    def test_quality_labels(self):
        """Quality labels should be correct for all levels."""
        self.assertEqual(ProofreadChecker.QUALITY_LABELS[0], "Without text")
        self.assertEqual(ProofreadChecker.QUALITY_LABELS[1], "Problematic")
        self.assertEqual(ProofreadChecker.QUALITY_LABELS[2], "Proofread")
        self.assertEqual(ProofreadChecker.QUALITY_LABELS[3], "Validated")


# ── TextExtractor Tests ───────────────────────────────────────────────────

class TestTextExtractor(unittest.TestCase):
    """Test Wikisource text extraction."""

    def setUp(self):
        self.extractor = TextExtractor("en")

    def test_strip_header_footer(self):
        wikitext = "{{header|1=1|2=Title}}\nHello world\n{{footer|1=1}}"
        text = self.extractor._strip_markup(wikitext)
        self.assertNotIn("header", text)
        self.assertNotIn("footer", text)
        self.assertIn("Hello world", text)

    def test_strip_nop(self):
        text = self.extractor._strip_markup("Line 1\n{{nop}}\nLine 2")
        self.assertIn("Line 1", text)
        self.assertIn("Line 2", text)

    def test_strip_pages_tag(self):
        text = self.extractor._strip_markup('<pages index="Test" from=1 to=1 />\nContent')
        self.assertIn("Content", text)

    def test_strip_html_comments(self):
        text = self.extractor._strip_markup("Text<!-- comment -->more")
        self.assertEqual(text.strip(), "Textmore")

    def test_empty_wikitext(self):
        self.assertEqual(self.extractor._strip_markup("").strip(), "")

    def test_strip_templates_generic(self):
        text = self.extractor._strip_markup("{{c|Centered}}\nContent")
        self.assertIn("Content", text)

    def test_normalize_whitespace(self):
        with patch("ws_text_extractor.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "parse": {"title": "Page:Test/1",
                          "wikitext": {"*": "Para 1\n\n\n\nPara 2"}}
            }
            mock_get.return_value = mock_resp
            text = self.extractor.get_page_text("Page:Test/1")
            self.assertIn("Para 1", text)
            self.assertIn("Para 2", text)
            self.assertNotIn("\n\n\n", text)

    def test_page_exists_api_call(self):
        with patch("ws_text_extractor.requests.Session.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "query": {"pages": {"123": {"pageid": 123, "title": "Page:Test/1"}}}
            }
            mock_get.return_value = mock_resp
            self.assertTrue(self.extractor.page_exists("Page:Test/1"))


# ── Namespace Resolver Tests (the T74525 trap) ────────────────────────────

EN_NAMESPACES = {
    "query": {"namespaces": {
        "0": {"id": 0, "*": ""},
        "104": {"id": 104, "*": "Page"},
        "105": {"id": 105, "*": "Page talk"},
        "106": {"id": 106, "*": "Index"},
        "107": {"id": 107, "*": "Index talk"},
    }}
}

# fr-shaped: the Index namespace is called "Livre" (112) and 106 is "Portail"
FR_NAMESPACES = {
    "query": {"namespaces": {
        "104": {"id": 104, "*": "Page"},
        "105": {"id": 105, "*": "Discussion Page"},
        "106": {"id": 106, "*": "Portail"},
        "107": {"id": 107, "*": "Discussion Portail"},
        "112": {"id": 112, "*": "Livre"},
        "113": {"id": 113, "*": "Discussion Livre"},
    }}
}


class TestNamespaceResolver(unittest.TestCase):
    """ProofreadPage namespaces must be resolved by content model, not by name/ID."""

    def test_content_model_constants(self):
        self.assertEqual(nsr.CONTENT_MODEL_PAGE, "proofread-page")
        self.assertEqual(nsr.CONTENT_MODEL_INDEX, "proofread-index")

    def test_alias_tables_include_localisations(self):
        """The alias hints should cover the observed localised names."""
        for name in ("page", "seite", "strona", "pagina", "страница"):
            self.assertIn(name, nsr.PAGE_ALIASES)
        for name in ("index", "indeks", "indice", "индекс", "সূচী"):
            self.assertIn(name, nsr.INDEX_ALIASES)

    def test_never_documents_hardcoded_ids(self):
        """The module must not advertise a fixed 104/106 pair as universal."""
        src = (SKILL_DIR / "assets" / "ws_namespace_resolver.py").read_text()
        self.assertIn("T74525", src)
        self.assertIn("contentmodel", src)

    @patch("ws_namespace_resolver._api")
    @patch("ws_namespace_resolver._content_model_of_namespace")
    def test_resolve_en(self, mock_model, mock_api):
        mock_api.return_value = EN_NAMESPACES
        mock_model.side_effect = lambda lang, ns: {104: "proofread-page",
                                                   106: "proofread-index"}.get(ns)
        result = nsr.resolve_namespaces("en")
        self.assertEqual(result["confidence"], "contentmodel")
        self.assertEqual(result["page"]["id"], 104)
        self.assertEqual(result["index"]["id"], 106)

    @patch("ws_namespace_resolver._api")
    @patch("ws_namespace_resolver._content_model_of_namespace")
    def test_resolve_fr_rejects_portal(self, mock_model, mock_api):
        """fr's Index lives at 112 ('Livre'); 106 is 'Portail' and must be rejected."""
        mock_api.return_value = FR_NAMESPACES
        mock_model.side_effect = lambda lang, ns: {104: "proofread-page",
                                                   106: "wikitext",       # Portail
                                                   112: "proofread-index"}.get(ns)
        result = nsr.resolve_namespaces("fr")
        self.assertEqual(result["confidence"], "contentmodel")
        self.assertEqual(result["index"]["id"], 112)
        self.assertEqual(result["index"]["name"], "Livre")

    @patch("ws_namespace_resolver._api")
    @patch("ws_namespace_resolver._content_model_of_namespace")
    def test_index_can_have_lower_id_than_page(self, mock_model, mock_api):
        """pt/bn/ml shape: the Index namespace ID is LOWER than the Page ID."""
        pt = {"query": {"namespaces": {
            "104": {"id": 104, "*": "Galeria"},
            "106": {"id": 106, "*": "Página"},
        }}}
        mock_api.return_value = pt
        mock_model.side_effect = lambda lang, ns: {104: "proofread-index",
                                                   106: "proofread-page"}.get(ns)
        result = nsr.resolve_namespaces("pt")
        self.assertEqual(result["page"]["id"], 106)
        self.assertEqual(result["index"]["id"], 104)

    @patch("ws_namespace_resolver._api")
    def test_api_failure_reports_error(self, mock_api):
        mock_api.side_effect = RuntimeError("boom")
        result = nsr.resolve_namespaces("xx")
        self.assertEqual(result["confidence"], "error")
        self.assertIsNone(result["page"])

    def test_sampled_wikis_include_divergent_cases(self):
        for lang in ("en", "fr", "de", "pt", "bn", "ml", "ta", "sv"):
            self.assertIn(lang, nsr.SAMPLED)


# ── Wikisource Catalogue (wsindex) Tests ──────────────────────────────────

class TestWsIndexClient(unittest.TestCase):
    """Test the wsindex catalogue client."""

    def setUp(self):
        self.client = ws_catalog.WsIndexClient()

    def test_book_fields_documented(self):
        for field in ("wikidata_qid", "title", "ws_url", "epub_url",
                      "wikisource_index_url", "view_count", "languages"):
            self.assertIn(field, ws_catalog.BOOK_FIELDS)

    @patch.object(ws_catalog.WsIndexClient, "_get")
    def test_total_reads_count(self, mock_get):
        mock_get.return_value = {"count": 2572, "results": []}
        self.assertEqual(self.client.total("en"), 2572)

    @patch.object(ws_catalog.WsIndexClient, "_get")
    def test_books_drops_none_params(self, mock_get):
        """Unset filters must not be sent as empty query params."""
        mock_get.return_value = {"count": 0, "results": []}
        self.client.books(languages="en")
        sent = mock_get.call_args[0][0]
        self.assertEqual(sent, {"languages": "en"})

    @patch.object(ws_catalog.WsIndexClient, "_get")
    def test_iterate_follows_next(self, mock_get):
        mock_get.side_effect = [
            {"count": 3, "next": "https://wsindex.toolforge.org/books/?page=2&page_size=50",
             "results": [{"title": "A"}, {"title": "B"}]},
            {"count": 3, "next": None, "results": [{"title": "C"}]},
        ]
        with patch.object(ws_catalog.time, "sleep"):
            titles = [b["title"] for b in self.client.iterate(max_books=3)]
        self.assertEqual(titles, ["A", "B", "C"])

    @patch.object(ws_catalog.WsIndexClient, "_get")
    def test_find_by_qid_scans_client_side(self, mock_get):
        """There is no server-side QID filter — matching happens locally."""
        mock_get.side_effect = [
            {"count": 2, "next": None,
             "results": [{"wikidata_qid": "Q1"}, {"wikidata_qid": "Q2"}]},
        ]
        with patch.object(ws_catalog.time, "sleep"):
            book = self.client.find_by_qid("Q2", max_scan=10)
        self.assertEqual(book["wikidata_qid"], "Q2")


# ── Script Tests ──────────────────────────────────────────────────────────

class TestScripts(unittest.TestCase):
    """Test that scripts run without errors."""

    def setUp(self):
        self.scripts_dir = SKILL_DIR / "scripts"

    def _run(self, name, *args):
        return subprocess.run(["bash", str(self.scripts_dir / name), *args],
                              capture_output=True, text=True, timeout=15)

    def test_ws_page_status_help(self):
        result = self._run("ws-page-status.sh", "--help")
        self.assertIn("Usage", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_ws_page_status_no_args(self):
        result = self._run("ws-page-status.sh")
        self.assertIn("Usage", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_ws_text_extract_help(self):
        result = self._run("ws-text-extract.sh", "--help")
        self.assertIn("Usage", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_ws_text_extract_no_args(self):
        result = self._run("ws-text-extract.sh")
        self.assertIn("Usage", result.stdout)
        self.assertEqual(result.returncode, 0)


# ── SKILL.md Content Tests ────────────────────────────────────────────────

class TestSkillContent(unittest.TestCase):
    """Verify key claims and documented traps in SKILL.md."""

    def setUp(self):
        self.skill_text = (SKILL_DIR / "SKILL.md").read_text()
        self.reference = (SKILL_DIR / "references" /
                          "wikisource-catalog-and-delivery.md").read_text()

    def test_depends_on_declared(self):
        self.assertIn("wikimedia-api-access", self.skill_text)
        self.assertIn("wikimedia-commons", self.skill_text)
        self.assertIn("wikimedia-wikitext", self.skill_text)

    def test_namespace_trap_documented(self):
        """The namespace-heterogeneity trap must be prominent."""
        self.assertIn("T74525", self.skill_text)
        self.assertIn("content model", self.skill_text)
        self.assertIn("Livre", self.skill_text)       # fr's Index namespace name
        self.assertIn("Galeria", self.skill_text)     # pt's Index namespace name

    def test_quality_levels_documented(self):
        for label in ("Without text", "Problematic", "Proofread", "Validated"):
            self.assertIn(label, self.skill_text)

    def test_badge_caveat_documented(self):
        """The uneven badge adoption must be stated, with the measured figures."""
        self.assertIn("Q20748092", self.skill_text)
        self.assertIn("Q20748093", self.skill_text)
        self.assertIn("99.4", self.skill_text)   # ta, highest adoption
        self.assertIn("0.0", self.skill_text)    # nl, lowest adoption

    def test_catalog_and_export_documented(self):
        self.assertIn("wsindex", self.skill_text)
        self.assertIn("ws-export", self.skill_text)
        self.assertIn("epub", self.skill_text.lower())

    def test_assets_referenced(self):
        for asset in ("ws_namespace_resolver.py", "ws_proofread_checker.py",
                      "ws_text_extractor.py", "ws_catalog.py"):
            self.assertIn(asset, self.skill_text)

    def test_scripts_referenced(self):
        for script in ("ws-page-status.sh", "ws-text-extract.sh"):
            self.assertIn(script, self.skill_text)

    def test_references_referenced(self):
        self.assertIn("wikisource-proofread-workflow.md", self.skill_text)
        self.assertIn("wikisource-catalog-and-delivery.md", self.skill_text)

    def test_guardrails_present(self):
        self.assertIn("Guardrails", self.skill_text)
        self.assertIn("Page:", self.skill_text)

    def test_ai_norms_documented(self):
        """The community's OCR/LLM norms belong in the skill, not just the endpoints."""
        self.assertIn("pagequality", self.skill_text.lower() + self.reference.lower())
        self.assertIn("advisor", self.skill_text.lower() + self.reference.lower())

    def test_reference_has_namespace_table(self):
        self.assertIn("T74525", self.reference)
        for wiki in ("en", "fr", "de", "pt", "bn", "ta"):
            self.assertIn(f"| {wiki} |", self.reference)


if __name__ == "__main__":
    unittest.main()
