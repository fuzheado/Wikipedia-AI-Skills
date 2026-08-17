"""Tests for the xtools skill: SKILL.md and reference content validation.

No network access — these assert that the documented facts, guardrails, and
cross-references match what was live-verified during skill research
(see proposals/xtools-skill-memo.md).
"""
import re
from pathlib import Path

from conftest import SKILLS_DIR, read_skill  # noqa: E402


class TestSkillDocs:
    def test_frontmatter(self):
        text = read_skill("xtools")
        assert "name: xtools" in text
        assert "description:" in text
        assert "license: MIT" in text
        assert "compatibility: opencode" in text
        assert "depends_on: [wikimedia-api-access]" in text
        assert "skill_discovery_hints:" in text
        assert re.search(r"last_verified: \d{4}-\d{2}-\d{2}", text)

    def test_description_length(self):
        import yaml
        text = read_skill("xtools")
        fm = yaml.safe_load(text.split("---")[1])
        assert len(fm["description"]) < 200

    def test_base_url_and_core_facts(self):
        text = read_skill("xtools")
        assert "xtools.wmcloud.org/api" in text
        assert "not versioned" in text.lower()
        assert "elapsed_time" in text
        assert "RFC 7807" in text
        assert "warning" in text  # deprecation announcements must be logged

    def test_uses_pageinfo_not_articleinfo(self):
        text = read_skill("xtools")
        # the renamed endpoint must be documented under its new name...
        assert "/api/page/pageinfo" in text
        # ...with the legacy name called out as a trap
        assert "articleinfo" in text

    def test_error_handling_documented(self):
        text = read_skill("xtools")
        for code in ("501", "503", "504"):
            assert code in text
        assert "600,000" in text or "600000" in text
        assert "900" in text  # 900s query timeout

    def test_user_agent_required_in_examples(self):
        text = read_skill("xtools")
        examples = text.count("curl -s")
        uas = text.count("User-Agent")
        assert uas >= examples, "not every curl example carries a User-Agent"

    def test_action_api_precedence_guardrail(self):
        text = read_skill("xtools")
        assert "Action API" in text
        # the skill must encode the official "Action API is faster" guidance
        assert "faster" in text.lower() or "considerably faster" in text.lower()

    def test_cross_references_resolve(self):
        text = read_skill("xtools")
        for dep in ("../wikimedia-api-access/SKILL.md",
                    "../wikipedia-edit-history/SKILL.md",
                    "../wikimedia-pageviews/SKILL.md",
                    "../wikiwho/SKILL.md",
                    "../wikimedia-page-assessment/SKILL.md",
                    "../wikimedia-api-strategy/SKILL.md"):
            assert dep in text, f"missing cross-reference: {dep}"

    def test_synchronous_requests_guardrail(self):
        text = read_skill("xtools")
        assert "synchronously" in text.lower() or "synchronous" in text.lower()


class TestReferenceDocs:
    def _ref(self, name):
        return (Path(SKILLS_DIR) / "xtools" / "references" / name).read_text()

    def test_page_api_covered(self):
        ref = self._ref("page-api.md")
        for ep in ("pageinfo", "top_editors", "prose", "links",
                   "assessments", "bot_data", "automated_edits"):
            assert ep in ref, f"missing endpoint: {ep}"
        assert "limit" in ref and "nobots" in ref

    def test_user_project_api_covered(self):
        ref = self._ref("user-project-api.md")
        for ep in ("simple_editcount", "pages_count", "pages", "automated_editcount",
                   "edit_summaries", "top_edits", "category_editcount",
                   "log_counts", "month_counts", "timecard", "globalcontribs",
                   "admin_stats", "patroller_stats", "steward_stats",
                   "largest_pages", "normalize", "namespaces"):
            assert ep in ref, f"missing endpoint: {ep}"

    def test_user_reference_documents_limits(self):
        ref = self._ref("user-project-api.md")
        assert "501" in ref
        assert "600,000" in ref or "600000" in ref
        assert "CIDR" in ref  # IP/CIDR usernames supported

    def test_page_reference_documents_rename(self):
        ref = self._ref("page-api.md")
        assert "articleinfo" in ref  # legacy name documented as a trap
