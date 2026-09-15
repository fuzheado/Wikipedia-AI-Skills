"""Tests for the flickr-wayback-recovery skill: SKILL.md content + scripts."""

import json
import py_compile
import sys
import textwrap
from pathlib import Path

import pytest

from conftest import SKILLS_DIR, read_skill  # noqa: E402

SKILL = SKILLS_DIR / "flickr-wayback-recovery"
ASSET_DIR = SKILL / "assets"
SCRIPT_DIR = SKILL / "scripts"


class TestSkillContent:
    """Key assertions about the flickr-wayback-recovery SKILL.md."""

    def test_depends_on(self):
        text = read_skill("flickr-wayback-recovery")
        assert "flickr" in text and "pattypan" in text
        assert "wikimedia-api-access" in text

    def test_cdx_both_url_forms(self):
        text = read_skill("flickr-wayback-recovery")
        assert "NSID" in text and "alias" in text
        assert "Query **both**" in text or "Query both" in text

    def test_trailing_slash_pitfall(self):
        text = read_skill("flickr-wayback-recovery")
        assert "209" in text
        assert "trailing slash" in text.lower()

    def test_license_filter(self):
        """The free-license rule lives in SKILL.md; the id → Commons template
        map lives in the case-study reference (it was moved out of SKILL.md)."""
        text = read_skill("flickr-wayback-recovery")
        assert "free set" in text.lower()
        assert "4, 5, 7, 8, 9, 10, 11, 12" in text
        assert "license 2" in text  # CC BY-NC — explicitly skipped
        case_study = (SKILL / "references" / "internetstiftelsen-case-study.md").read_text()
        assert "{{cc-by-2.0}}" in case_study
        assert "{{cc-by-sa-2.0}}" in case_study

    def test_match_by_id(self):
        text = read_skill("flickr-wayback-recovery")
        assert "Flickr ID" in text
        assert "not by filename" in text or "never by filename" in text

    def test_model_export(self):
        text = read_skill("flickr-wayback-recovery")
        assert "modelExport" in text
        assert "script class=\"modelExport\"" in text

    def test_mojibake_latin1(self):
        text = read_skill("flickr-wayback-recovery")
        assert "latin-1" in text
        assert "unquote_to_bytes" in text

    def test_pruned_exclusion_list(self):
        text = read_skill("flickr-wayback-recovery")
        assert "skip_photos.txt" in text
        assert "archived URL" in text  # the trap: URL keeps the row alive

    def test_magic_bytes_validation(self):
        text = read_skill("flickr-wayback-recovery")
        assert "magic bytes" in text or "looks_like_image" in text

    def test_no_dead_people_page_link(self):
        text = read_skill("flickr-wayback-recovery")
        assert "people page" in text
        assert "plain username" in text

    def test_person_categories_are_subjects(self):
        text = read_skill("flickr-wayback-recovery")
        assert "photographed people" in text
        assert "not the photographers" in text

    def test_tooling_referenced(self):
        text = read_skill("flickr-wayback-recovery")
        for f in ("cdx-photo-ids.py", "check-commons.py", "fetch-photo-metadata.py",
                  "download-images.py", "build-manifest.py", "validate-manifest.py",
                  "inspect_model.py", "wayback-cdx-notes.md",
                  "internetstiftelsen-case-study.md"):
            assert f in text


class TestScriptsCompile:
    """Every shipped script must be syntactically valid."""

    @pytest.mark.parametrize("rel", [
        "scripts/cdx-photo-ids.py",
        "scripts/check-commons.py",
        "scripts/fetch-photo-metadata.py",
        "scripts/download-images.py",
        "scripts/build-manifest.py",
        "scripts/validate-manifest.py",
        "assets/inspect_model.py",
    ])
    def test_compiles(self, rel):
        py_compile.compile(str(SKILL / rel), doraise=True)


class TestInspectModel:
    """Unit-test the modelExport extractor/resolver on a synthetic page."""

    def _html(self):
        # cyclical JSON: ~N strings reference data["legend"] paths into main.
        blob = {
            "main": {
                "strings": ["Hello", "World"],
                "photo-models": [{"title": "~0", "description": "~1", "license": 4}],
                "photo-stats-models": [{"dateTaken": "2024-05-12 15:07:00"}],
                "photo-head-meta-models": [{"keywords": "se%2C%20hack%2C%20musik"}],
                "person-models": [{"id": "44783532@N07", "pathAlias": "stiftelsen",
                                   "username": "Stiftelsen"}],
            },
            "legend": [["strings", "0"], ["strings", "1"]],
        }
        return ('<html><body><script class="modelExport" type="application/json">'
                'modelExport: ' + json.dumps(blob) + '</script></body></html>')

    def test_extract_and_resolve(self):
        sys.path.insert(0, str(ASSET_DIR))
        import inspect_model
        html = self._html()
        data = inspect_model.extract_model(html)
        assert data is not None
        meta = inspect_model.photo_metadata(data)
        assert meta is not None
        assert meta["title"] == "Hello"      # "~0" -> legend[0] -> strings[0]
        assert meta["description"] == "World"  # "~1" -> legend[1] -> strings[1]
        assert meta["license"] == 4
        assert meta["owner"]["path_alias"] == "stiftelsen"
        assert meta["tags"] == ["se", "hack", "musik"]

    def test_no_model_export(self):
        sys.path.insert(0, str(ASSET_DIR))
        import inspect_model
        assert inspect_model.extract_model("<html>no blob here</html>") is None
