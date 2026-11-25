"""Tests for the commons-face-identification skill: docs, references, and script contract.

No network access: these assert that the documented facts, traps and cross-references match
what was live-verified during the calibration run (see
references/calibration-measurements.md), and that the bundled script refuses bad input.
"""
import re
import subprocess
import sys
from pathlib import Path

import py_compile
import yaml

from conftest import SKILLS_DIR, read_skill  # noqa: E402

SKILL = "commons-face-identification"
SKILL_DIR = SKILLS_DIR / SKILL


def norm(text):
    return " ".join(text.split())


class TestFrontmatter:
    def test_required_fields(self):
        text = read_skill(SKILL)
        assert "name: commons-face-identification" in text
        assert "description:" in text
        assert "license: MIT" in text
        assert "compatibility: opencode" in text
        assert "depends_on: [wikimedia-api-access, wikimedia-commons-sdc]" in text
        assert "skill_discovery_hints:" in text
        assert re.search(r"last_verified: \d{4}-\d{2}-\d{2}", text)

    def test_description_length_and_no_colon_space(self):
        fm = yaml.safe_load(read_skill(SKILL).split("---")[1])
        assert len(fm["description"]) < 200
        assert ": " not in fm["description"], "colon-space breaks YAML frontmatter"

    def test_description_is_a_trigger(self):
        fm = yaml.safe_load(read_skill(SKILL).split("---")[1])
        desc = fm["description"].lower()
        assert "face" in desc
        assert any(w in desc for w in ("identify", "recognition"))


class TestDocumentedFacts:
    def test_ground_truth_resolution_traps(self):
        text = norm(read_skill(SKILL))
        assert "P301" in text
        assert "Q4167836" in text
        assert "wikibase_item" in text

    def test_measured_thresholds(self):
        text = norm(read_skill(SKILL))
        assert "0.55–0.60" in text or "0.55-0.60" in text
        assert "1,537" in text
        assert "282" in text

    def test_active_learning_gain(self):
        cal = norm((SKILL_DIR / "references" / "calibration-measurements.md").read_text())
        assert "78%" in cal and "49%" in cal
        assert "269 photos" in cal

    def test_live_traps_recorded(self):
        text = norm(read_skill(SKILL))
        for trap in ("414", "429", "Retry-After", "maxlag"):
            assert trap in text, f"missing live-verified trap: {trap}"

    def test_polluted_tree_measurement(self):
        text = norm(read_skill(SKILL) + (SKILL_DIR / "references" /
                                       "commons-person-category-ground-truth.md").read_text())
        assert "7,589" in text

    def test_licence_and_ethics(self):
        text = norm(read_skill(SKILL))
        assert "non-commercial" in text
        assert "biometric" in text
        assert "Photographs of identifiable people" in text

    def test_write_back_qualifier(self):
        assert "P2677" in read_skill(SKILL)

    def test_tooling_is_named_with_alternatives(self):
        text = read_skill(SKILL)
        assert "wikivisage.toolforge.org" in text
        assert "reframe.toolforge.org" in text
        assert "commons-metadata-suggester.toolforge.org" in text


class TestCrossReferences:
    def test_relative_links_resolve(self):
        text = read_skill(SKILL)
        links = re.findall(r"\]\(\.\./([a-z0-9-]+)/SKILL\.md\)", text)
        assert links, "expected cross-references to sibling skills"
        for name in links:
            assert (SKILLS_DIR / name / "SKILL.md").exists(), f"broken cross-reference: {name}"

    def test_reference_files_exist_and_are_linked(self):
        text = read_skill(SKILL)
        for ref in ("commons-person-category-ground-truth.md", "calibration-measurements.md"):
            assert (SKILL_DIR / "references" / ref).exists()
            assert ref in text, f"{ref} exists but is not linked from SKILL.md"

    def test_every_shell_example_carries_a_user_agent(self):
        text = read_skill(SKILL)
        for block in re.findall(r"```bash\n(.*?)```", text, re.S):
            if "curl" in block:
                assert "-A " in block, "curl example without a User-Agent"


class TestScriptContract:
    def test_compiles(self):
        py_compile.compile(str(SKILL_DIR / "scripts" / "person_ground_truth.py"), doraise=True)

    def test_refuses_without_arguments(self):
        p = subprocess.run([sys.executable, str(SKILL_DIR / "scripts" / "person_ground_truth.py")],
                           capture_output=True, text=True, timeout=60)
        assert p.returncode == 2
        assert "category" in (p.stderr or "").lower()

    def test_refuses_non_category_title(self):
        p = subprocess.run([sys.executable, str(SKILL_DIR / "scripts" / "person_ground_truth.py"),
                            "Erasmus Prize 2015"],
                           capture_output=True, text=True, timeout=60)
        assert p.returncode == 2
        assert "Category:" in (p.stderr or "")

    def test_stdlib_only(self):
        src = (SKILL_DIR / "scripts" / "person_ground_truth.py").read_text()
        assert "import requests" not in src
        assert "urllib.request" in src

    def test_batch_helper_caps_count_and_length(self):
        src = (SKILL_DIR / "scripts" / "person_ground_truth.py").read_text()
        assert "maxcount=50" in src, "the API rejects more than 50 titles per request"
        assert "maxlen=3500" in src, "long Commons titles overflow the URL (HTTP 414)"
