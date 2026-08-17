"""Tests for the mint skill: SKILL.md and script validation.

No network access — these assert that the documented facts, traps, and
cross-references match what was live-verified during skill research
(see proposals/mint-skill-memo.md).
"""
import re
import py_compile
from pathlib import Path

from conftest import SKILLS_DIR, read_skill  # noqa: E402


class TestSkillDocs:
    def test_frontmatter(self):
        text = read_skill("mint")
        assert "name: mint" in text
        assert "description:" in text
        assert "license: MIT" in text
        assert "compatibility: opencode" in text
        assert "depends_on: [wikimedia-api-access]" in text
        assert "skill_discovery_hints:" in text
        assert re.search(r"last_verified: \d{4}-\d{2}-\d{2}", text)

    def test_description_length(self):
        import yaml
        text = read_skill("mint")
        fm = yaml.safe_load(text.split("---")[1])
        assert len(fm["description"]) < 200

    def test_base_url_and_endpoints(self):
        text = read_skill("mint")
        assert "translate.wmcloud.org" in text
        assert "/api/translate" in text
        assert "/api/languages" in text
        assert "/healthz" in text
        assert "openapi.json" in text  # machine-readable spec referenced

    def test_request_field_names(self):
        text = read_skill("mint")
        for field in ("content", "source_language", "target_language", "provider", "format"):
            assert field in text, f"missing request field: {field}"

    def test_formats_documented(self):
        text = read_skill("mint")
        for fmt in ("html", "json", "markdown", "text", "svg", "webpage"):
            assert fmt in text, f"missing format: {fmt}"

    def test_response_fields(self):
        text = read_skill("mint")
        for field in ("translation", "translationtime", "model"):
            assert field in text, f"missing response field: {field}"

    def test_api_404_trap_documented(self):
        text = read_skill("mint")
        assert "404" in text
        # the bare /api path must be called out as not-an-endpoint
        assert "/api` alone returns 404" in text or "`/api` alone returns 404" in text

    def test_field_name_trap_documented(self):
        text = read_skill("mint")
        # wrong field names must be called out as a 422 trap
        assert "422" in text
        assert "text" in text and "from" in text and "to" in text

    def test_provider_selection_documented(self):
        text = read_skill("mint")
        assert "nllb200-600M" in text
        assert "indictrans2" in text.lower()

    def test_user_agent_required_in_examples(self):
        text = read_skill("mint")
        examples = text.count("curl -s")
        uas = text.count("User-Agent")
        assert uas >= examples, "not every curl example carries a User-Agent"

    def test_etiquette_guardrails(self):
        text = read_skill("mint")
        assert "synchronous" in text.lower()
        assert "pacing" in text.lower() or "1s" in text.lower()

    def test_cross_references_resolve(self):
        text = read_skill("mint")
        for dep in ("../wikimedia-api-access/SKILL.md",
                    "../wikimedia-api-strategy/SKILL.md",
                    "../wikimedia-ml-services/SKILL.md",
                    "../wikimedia-i18n-l10n-for-tools/SKILL.md"):
            assert dep in text, f"missing cross-reference: {dep}"

    def test_licensing_noted(self):
        text = read_skill("mint")
        assert "CC-BY-SA" in text


class TestScript:
    def test_script_compiles(self):
        script = Path(SKILLS_DIR) / "mint" / "scripts" / "translate.py"
        assert script.exists()
        py_compile.compile(str(script), doraise=True)

    def test_script_has_key_arguments(self):
        text = (Path(SKILLS_DIR) / "mint" / "scripts" / "translate.py").read_text()
        for arg in ("--format", "--provider", "--list-languages", "--file"):
            assert arg in text, f"missing CLI argument: {arg}"
        assert "translate.wmcloud.org" in text
