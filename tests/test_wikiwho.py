"""Tests for the wikiwho skill: SKILL.md / reference content and the
who_wrote.py authorship-breakdown script.

The script talks to the live WikiWho API; all network access is mocked at
`urllib.request.urlopen` so the suite runs offline.
"""
import csv
import json
import re
import sys
import urllib.error
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import pytest

from conftest import SKILLS_DIR, read_skill  # noqa: E402

SCRIPT_DIR = SKILLS_DIR / "wikiwho" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import who_wrote as ww  # noqa: E402


def _ususerids(url):
    """Decode the ususerids parameter of an Action API URL."""
    return parse_qs(urlparse(url).query)["ususerids"][0].split("|")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

LATEST_RESPONSE = {
    "article_title": "Wikilambda",
    "page_id": 64444578,
    "success": True,
    "message": None,
    "revisions": [
        {
            "995998767": {
                "editor": "11292982",
                "time": "2020-12-24T00:15:32Z",
                "tokens": [
                    {"str": "#", "editor": "13006032"},
                    {"str": "redirect", "editor": "13006032"},
                    {"str": "Wikilambda", "editor": "11292982"},
                    {"str": "{{", "editor": "13006032"},
                ],
            }
        }
    ],
}

USERS_RESPONSE = {
    "query": {
        "users": [
            {"userid": 13006032, "name": "Fuzheado"},
            {"userid": 11292982, "missing": True},  # deleted account: no name
        ]
    }
}


class FakeResp:
    """Minimal file-like response with context-manager support."""

    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def fake_urlopen(route_map, seen=None):
    """Return a urlopen stand-in that routes by URL substring.

    `seen` (optional list) collects every (url, headers) pair for assertions.
    """
    def _urlopen(req, timeout=120):
        url = req.full_url if hasattr(req, "full_url") else req.get_full_url()
        if seen is not None:
            seen.append((url, dict(req.headers)))
        for fragment, payload in route_map:
            if fragment in url:
                return FakeResp(payload)
        raise AssertionError(f"unexpected URL in test: {url}")
    return _urlopen


WWI_RESPONSES = [
    ("wikiwho-api.wmcloud.org", LATEST_RESPONSE),
    ("/w/api.php", USERS_RESPONSE),
]


# ---------------------------------------------------------------------------
# SKILL.md content
# ---------------------------------------------------------------------------

class TestSkillDocs:
    def test_frontmatter(self):
        text = read_skill("wikiwho")
        assert "name: wikiwho" in text
        assert "description:" in text
        assert "license: MIT" in text
        assert "depends_on: [wikimedia-api-access]" in text
        assert "skill_discovery_hints:" in text
        assert re.search(r"last_verified: \d{4}-\d{2}-\d{2}", text)

    def test_base_url_and_version(self):
        text = read_skill("wikiwho")
        assert "wikiwho-api.wmcloud.org" in text
        assert "v1.0.0-beta" in text
        # canonical host note added after mediawiki.org domain change
        assert "wikiwho.wmcloud.org" in text

    def test_key_endpoints_documented(self):
        text = read_skill("wikiwho")
        for ep in ("rev_ids", "latest_rev_content", "rev_content",
                   "range_rev_content", "all_content", "page_id"):
            assert ep in text, f"missing endpoint: {ep}"

    def test_user_agent_required_in_every_example(self):
        text = read_skill("wikiwho")
        # every curl/requests example must carry a descriptive User-Agent
        examples = text.count("curl -s")
        uas = text.count("User-Agent")
        assert uas >= examples, "not every curl example carries a User-Agent"

    def test_editor_id_guardrail(self):
        text = read_skill("wikiwho")
        # editor is a user ID, not a username — must say so and show resolution
        assert "user ID" in text or "user *ID*" in text
        assert "ususerids" in text
        assert "0|<ip>" in text

    def test_cross_references_resolve(self):
        text = read_skill("wikiwho")
        assert "../wikimedia-api-access/SKILL.md" in text
        assert "../wikipedia-edit-history/SKILL.md" in text
        assert "../wikimedia-diffs/SKILL.md" in text

    def test_reference_doc_covers_endpoint_families_and_errors(self):
        ref = (Path(SKILLS_DIR) / "wikiwho" / "references" / "endpoints.md").read_text()
        for ep in ("/rev_content/", "/latest_rev_content/",
                   "/range_rev_content/", "/all_content/", "/rev_ids/"):
            assert ep in ref
        for code in ("400", "408", "503"):
            assert code in ref
        # worked examples must use the small article for fast demos
        assert "Wikilambda" in ref

    def test_reference_doc_links_open_access_paper(self):
        ref = (Path(SKILLS_DIR) / "wikiwho" / "references" / "endpoints.md").read_text()
        assert "archives.iw3c2.org" in ref  # open-access WWW 2014 PDF


# ---------------------------------------------------------------------------
# resolve_users
# ---------------------------------------------------------------------------

class TestResolveUsers:
    def test_skips_anonymous_ids(self):
        responses = [("/w/api.php", {"query": {"users": [
            {"userid": 13006032, "name": "Fuzheado"}]}})]
        seen = []
        with patch("urllib.request.urlopen", fake_urlopen(responses, seen)):
            names = ww.resolve_users(["13006032", "0", "0|152.163.195.8"], "en.wikipedia.org")
        assert names == {"13006032": "Fuzheado"}
        # only the registered ID may be sent to the Action API
        assert _ususerids(seen[0][0]) == ["13006032"]

    def test_batches_by_50(self):
        ids = [str(i) for i in range(1, 76)]  # 75 ids -> 2 requests
        responses = [
            ("ususerids=1%7C", {"query": {"users": [
                {"userid": i, "name": f"User{i}"} for i in range(1, 51)]}}),
            ("ususerids=51%7C", {"query": {"users": [
                {"userid": i, "name": f"User{i}"} for i in range(51, 76)]}}),
        ]
        seen = []
        with patch("urllib.request.urlopen", fake_urlopen(responses, seen)):
            names = ww.resolve_users(ids, "en.wikipedia.org")
        assert len(seen) == 2
        assert len(_ususerids(seen[0][0])) == 50
        assert len(_ususerids(seen[1][0])) == 25
        assert len(names) == 75

    def test_missing_users_become_deleted_label(self):
        responses = [("/w/api.php", {"query": {"users": [
            {"userid": 11292982, "missing": True}]}})]
        with patch("urllib.request.urlopen", fake_urlopen(responses)):
            names = ww.resolve_users(["11292982"], "en.wikipedia.org")
        assert names == {"11292982": "(deleted)"}

    def test_sends_descriptive_user_agent(self):
        seen = []
        with patch("urllib.request.urlopen", fake_urlopen(WWI_RESPONSES, seen)):
            ww.resolve_users(["13006032"], "en.wikipedia.org")
        ua = seen[0][1].get("User-Agent") or seen[0][1].get("User-agent")
        assert ua == ww.UA
        assert "wikiwho-skill" in ua


# ---------------------------------------------------------------------------
# fetch_tokens
# ---------------------------------------------------------------------------

class TestFetchTokens:
    def test_latest_revision_path(self):
        seen = []
        with patch("urllib.request.urlopen", fake_urlopen(WWI_RESPONSES, seen)):
            data, tokens = ww.fetch_tokens("Wikilambda", None, "en")
        assert len(tokens) == 4
        assert "/latest_rev_content/Wikilambda/?editor=true" in seen[0][0]
        assert data["article_title"] == "Wikilambda"

    def test_specific_revision_path(self):
        seen = []
        with patch("urllib.request.urlopen", fake_urlopen(WWI_RESPONSES, seen)):
            _, tokens = ww.fetch_tokens("Wikilambda", 995998767, "en")
        assert len(tokens) == 4
        assert "/rev_content/Wikilambda/995998767/?editor=true" in seen[0][0]

    def test_language_code_in_base_url(self):
        seen = []
        with patch("urllib.request.urlopen", fake_urlopen(WWI_RESPONSES, seen)):
            ww.fetch_tokens("Wikilambda", None, "de")
        assert "https://wikiwho-api.wmcloud.org/de/api/v1.0.0-beta/" in seen[0][0]


# ---------------------------------------------------------------------------
# main() end-to-end (mocked network)
# ---------------------------------------------------------------------------

class TestMain:
    def _run(self, *args, route_map=WWI_RESPONSES):
        """Invoke main() with a fake argv, network mocked."""
        ctx = patch("urllib.request.urlopen", fake_urlopen(route_map))
        with ctx, patch.object(sys, "argv", ["who_wrote.py", *args]):
            ww.main()

    def test_breakdown_output(self, capsys):
        self._run("Wikilambda")
        out = capsys.readouterr().out
        # 3 tokens by 13006032 (Fuzheado) = 75%; 1 token by 11292982 = 25%;
        # the missing-account ID displays as "(deleted)" without crashing
        assert "Fuzheado" in out
        assert "(deleted)" in out
        assert "75.0%" in out
        assert "25.0%" in out
        assert "tokens: 4" in out

    def test_top_limit(self, capsys):
        self._run("Wikilambda", "--top", "1")
        out = capsys.readouterr().out
        assert "Fuzheado" in out
        assert "(deleted)" not in out  # top-1 cuts the second editor

    def test_csv_output(self, tmp_path, capsys):
        csv_path = tmp_path / "out.csv"
        self._run("Wikilambda", "--csv", str(csv_path))
        rows = list(csv.reader(open(csv_path)))
        assert rows[0] == ["editor", "tokens", "pct"]
        assert ["Fuzheado", "3", "75.0"] in rows
        assert ["(deleted)", "1", "25.0"] in rows

    def test_lang_flag_uses_correct_wiki_domain_for_resolution(self, capsys):
        seen = []
        ctx = patch("urllib.request.urlopen", fake_urlopen(WWI_RESPONSES, seen))
        with ctx, patch.object(sys, "argv", ["who_wrote.py", "Wikilambda", "--lang", "de"]):
            ww.main()
        wikiwho_urls = [u for u, _ in seen if "wikiwho-api" in u]
        api_urls = [u for u, _ in seen if "/w/api.php" in u]
        assert "/de/api/v1.0.0-beta/" in wikiwho_urls[0]
        # username resolution defaults to the matching Wikipedia edition
        assert "https://de.wikipedia.org/w/api.php" in api_urls[0]

    def test_domain_override(self, capsys):
        seen = []
        ctx = patch("urllib.request.urlopen", fake_urlopen(WWI_RESPONSES, seen))
        with ctx, patch.object(sys, "argv", ["who_wrote.py", "Wikilambda", "--lang", "en", "--domain", "fr.wikipedia.org"]):
            ww.main()
        api_urls = [u for u, _ in seen if "/w/api.php" in u]
        assert "https://fr.wikipedia.org/w/api.php" in api_urls[0]

    def test_http_error_exits_with_helpful_message(self, capsys):
        """A 400 (e.g. article missing in that wiki) must not dump a traceback."""
        def boom(req, timeout=120):
            raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {}, None)
        ctx = patch("urllib.request.urlopen", side_effect=boom)
        with ctx, patch.object(sys, "argv", ["who_wrote.py", "Wikilambda", "--lang", "de"]):
            with pytest.raises(SystemExit) as exc:
                ww.main()
        # sys.exit(message) carries the message as the exit code, not on stderr
        assert exc.value.code not in (0, None)
        msg = str(exc.value.code)
        assert "400" in msg
        assert "article title" in msg.lower()
