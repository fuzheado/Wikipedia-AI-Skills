"""Tests for the wikidata-reconciliation skill: SKILL.md and script validation.

No network access — these assert that the documented facts, guardrails, and
cross-references match what was live-verified during skill research
(see proposals/wikidata-reconciliation-skill-memo.md).
"""
import re
import py_compile
from pathlib import Path

from conftest import SKILLS_DIR, read_skill  # noqa: E402

SKILL_DIR = SKILLS_DIR / "wikidata-reconciliation"


class TestSkillDocs:
    def test_frontmatter(self):
        text = read_skill("wikidata-reconciliation")
        assert "name: wikidata-reconciliation" in text
        assert "description:" in text
        assert "license: MIT" in text
        assert "compatibility: opencode" in text
        assert "depends_on: [wikimedia-api-access, wikidata]" in text
        assert "skill_discovery_hints:" in text
        assert re.search(r"last_verified: \d{4}-\d{2}-\d{2}", text)

    def test_description_length(self):
        import yaml
        text = read_skill("wikidata-reconciliation")
        fm = yaml.safe_load(text.split("---")[1])
        assert len(fm["description"]) < 200

    def test_core_endpoints_documented(self):
        text = read_skill("wikidata-reconciliation")
        # primary path + verification
        assert "wbsearchentities" in text
        assert "wbgetentities" in text
        # reconciliation service protocol
        assert "wikidata-reconciliation.wmcloud.org" in text
        assert "suggest/entity" in text
        assert "defaultTypes" in text
        # legacy host called out
        assert "reconcile.wikidata.org" in text

    def test_broken_batch_endpoint_trap_documented(self):
        text = read_skill("wikidata-reconciliation")
        # the verified-broken batch POST must be flagged, not silently omitted
        assert "invalid query" in text
        assert "POST" in text
        assert "currently broken" in text or "broken" in text
        assert "wbsearchentities" in text  # the working fallback is named

    def test_core_principle_and_guardrails(self):
        text = read_skill("wikidata-reconciliation")
        # the "never trust an unverified QID" principle must be explicit
        assert "never trust" in text.lower()
        assert "verify" in text.lower()
        # disambiguation key
        assert "description" in text.lower()
        # graceful failure is a documented valid answer
        assert "UNRESOLVED" in text
        # P31 type check present
        assert "P31" in text
        # disambiguation page QID check present
        assert "Q4167410" in text

    def test_llm_grounding_section(self):
        text = read_skill("wikidata-reconciliation")
        # the AI-harness use case must be first-class
        assert "LLM QID grounding" in text
        assert "hallucinat" in text.lower()
        assert "batch-verify" in text.lower() or "batch verify" in text.lower()

    def test_cross_references_resolve(self):
        text = read_skill("wikidata-reconciliation")
        for ref in ("wikidata", "wikimedia-commons-sdc", "quickstatements",
                    "wikidata-vector-search", "wikimedia-api-access"):
            assert f"../{ref}/SKILL.md" in text

    def test_user_agent_admonition(self):
        text = read_skill("wikidata-reconciliation")
        # every curl example must carry a UA; the skill must say so
        assert "User-Agent" in text
        assert text.count("-A ") >= 4  # each curl example includes -A


class TestScript:
    def test_script_compiles(self):
        script = SKILL_DIR / "scripts" / "reconcile.py"
        py_compile.compile(str(script), doraise=True)

    def test_script_is_stdlib_only(self):
        script = (SKILL_DIR / "scripts" / "reconcile.py").read_text()
        # no third-party imports
        assert "import requests" not in script
        assert "import pandas" not in script
        assert "urllib" in script  # stdlib http client
        assert "argparse" in script

    def test_script_has_ua_and_api(self):
        script = (SKILL_DIR / "scripts" / "reconcile.py").read_text()
        assert "User-Agent" in script or "USER_AGENT" in script
        assert "wikidata.org/w/api.php" in script
        assert "wbsearchentities" in script
        assert "wbgetentities" in script

    def test_script_graceful_unresolved(self):
        script = (SKILL_DIR / "scripts" / "reconcile.py").read_text()
        # must return a "none"/UNRESOLVED verdict rather than forcing a match
        assert "confidence" in script
        assert "none" in script
