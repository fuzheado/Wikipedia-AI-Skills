"""Tests for the wikimedia-media-usage-metrics skill: SKILL.md content + scripts."""

import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from conftest import SKILLS_DIR, read_skill  # noqa: E402

SKILL = SKILLS_DIR / "wikimedia-media-usage-metrics"
SCRIPT = SKILL / "scripts" / "media-usage-report.py"

sys.path.insert(0, str(SKILL / "scripts"))
import media_usage_report as mur  # noqa: E402


class TestSkillContent:
    """Key assertions about the SKILL.md."""

    def test_four_meanings_of_use(self):
        text = read_skill("wikimedia-media-usage-metrics")
        assert "Transfers" in text and "Usage (embeds)" in text
        assert "Reach" in text and "External reuse" in text

    def test_depends_on(self):
        text = read_skill("wikimedia-media-usage-metrics")
        assert "wikimedia-api-access" in text
        assert "wikimedia-pageviews" in text
        assert "wikimedia-commons" in text
        assert "wikimedia-commons-sparql" in text

    def test_verified_gotchas_present(self):
        text = read_skill("wikimedia-media-usage-metrics")
        # leading-slash encoding for mediarequests per-file
        assert "leading slash" in text
        # utm tracking-param strip
        assert "utm_source" in text and "Strip everything from" in text
        # pageviews 404 = zero data
        assert "404 as 0 views" in text
        # CIM snapshot has no pageviews field
        assert "no pageviews" in text and "pageviews-per-category-monthly" in text

    def test_no_stale_perfile_removal_claim(self):
        text = read_skill("wikimedia-media-usage-metrics")
        assert "is removed" not in text

    def test_sightglass_section(self):
        text = read_skill("wikimedia-media-usage-metrics")
        assert "Sightglass" in text
        assert "api/media/stats" in text and "api/category/stats" in text
        assert "300,000" in text  # category query cap
        assert "OAuth" in text  # login requirement documented

    def test_petscan_role(self):
        text = read_skill("wikimedia-media-usage-metrics")
        assert "population selection" in text
        assert "does **not** emit usage counts" in text
        assert "file_type=bitmap" in text

    def test_cim_not_on_demand_callout(self):
        text = read_skill("wikimedia-media-usage-metrics")
        assert "NOT on-demand" in text
        assert "allow-listed" in text and "pre-computed" in text
        assert "Views from category" in text and "Phabricator" in text
        assert "does **not** register" in text
        assert "no retroactive backfill" in text


class TestResolvePath:
    """Title -> upload path resolution, including the utm tracking-param strip."""

    def test_strips_tracking_params(self):
        url = "https://upload.wikimedia.org/wikipedia/commons/0/00/Crab_Nebula.jpg?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original"
        resp = {"query": {"pages": {"1": {"imageinfo": [{"url": url}]}}}}
        with mock.patch.object(mur, "_get", return_value=resp):
            assert mur.resolve_path("File:Crab Nebula.jpg") == "/wikipedia/commons/0/00/Crab_Nebula.jpg"

    def test_missing_file_raises(self):
        resp = {"query": {"pages": {"1": {"missing": ""}}}}
        with mock.patch.object(mur, "_get", return_value=resp):
            with pytest.raises(SystemExit):
                mur.resolve_path("File:No Such File.jpg")


class TestGlobalUsage:
    """prop=globalusage enumeration with pagination and truncation."""

    def test_paginates(self):
        page1 = {"query": {"pages": {"1": {"globalusage": [{"wiki": "en.wikipedia", "title": "A"}]}}},
                 "continue": {"gucontinue": "0|A", "continue": "||"}}
        page2 = {"query": {"pages": {"1": {"globalusage": [{"wiki": "fr.wikipedia", "title": "B"}]}}}}
        with mock.patch.object(mur, "_get", side_effect=[page1, page2]):
            usage, truncated = mur.global_usage("File:X.jpg", max_usage=5000)
        assert usage == [("en.wikipedia", "A"), ("fr.wikipedia", "B")]
        assert truncated is False

    def test_truncates_at_cap(self):
        many = {"query": {"pages": {"1": {"globalusage": [{"wiki": "en.wikipedia", "title": f"P{i}"} for i in range(10)]}}}}
        with mock.patch.object(mur, "_get", return_value=many):
            usage, truncated = mur.global_usage("File:X.jpg", max_usage=5)
        assert len(usage) == 5
        assert truncated is True


class TestMediarequests:
    """per-file transfer counts: leading-slash encoding + 404-as-no-data."""

    def test_encodes_leading_slash(self):
        captured = {}

        def fake_get(url):
            captured["url"] = url
            return {"items": [{"requests": 100}, {"requests": 50}]}

        with mock.patch.object(mur, "_get_or_none", side_effect=fake_get):
            total, days = mur.mediarequests("/wikipedia/commons/0/00/Crab_Nebula.jpg", "20240101", "20240201")
        assert total == 150 and days == 2
        assert "%2Fwikipedia%2Fcommons%2F0%2F00%2FCrab_Nebula.jpg" in captured["url"]

    def test_404_returns_zero(self):
        with mock.patch.object(mur, "_get_or_none", return_value=None):
            total, days = mur.mediarequests("/wikipedia/commons/0/00/X.jpg", "20240101", "20240201")
        assert (total, days) == (0, 0)


class TestPageviews:
    """per-article reach: 404 (no data) -> None, sums views otherwise."""

    def test_404_returns_none(self):
        with mock.patch.object(mur, "_get_or_none", return_value=None):
            assert mur.pageviews("en.wikipedia", "Albert Einstein", "20240101", "20240108") is None

    def test_sums_views(self):
        resp = {"items": [{"views": 10}, {"views": 20}]}
        with mock.patch.object(mur, "_get_or_none", return_value=resp):
            assert mur.pageviews("en.wikipedia", "Albert Einstein", "20240101", "20240108") == 30


class TestScriptCompiles:
    def test_compiles(self):
        import py_compile
        py_compile.compile(str(SKILL / "scripts" / "media_usage_report.py"), doraise=True)
