"""Tests for .githooks/pre-push — tooling references and audit-prompt consistency.

The hook is a Python file without a .py extension, so it is loaded explicitly.
These tests cover both directions: the checks catch drift in a synthetic repo,
and the real repository currently satisfies them.
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / ".githooks" / "pre-push"
SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
AUDIT_PROMPT = REPO_ROOT / "scripts" / "audit-prompt.md"


def _load_hook():
    loader = importlib.machinery.SourceFileLoader("pre_push_hook", str(HOOK_PATH))
    spec = importlib.util.spec_from_loader("pre_push_hook", loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


HOOK = _load_hook()


# ---------------------------------------------------------------------------
# Tooling references in SKILL.md
# ---------------------------------------------------------------------------


def _skill(tmp_path: Path, body: str) -> str:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    return str(skill_dir)


def test_missing_tooling_file_is_flagged(tmp_path):
    skill_dir = _skill(tmp_path, "## Tooling\n\n- `scripts/gone.sh` — helper\n")
    missing = HOOK.find_tooling_references(skill_dir)
    assert [ref for ref, _ in missing] == ["scripts/gone.sh"]


def test_existing_tooling_file_passes(tmp_path):
    skill_dir = _skill(tmp_path, "## Tooling\n\n- `scripts/here.sh` — helper\n")
    (Path(skill_dir) / "scripts").mkdir()
    (Path(skill_dir) / "scripts" / "here.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    assert HOOK.find_tooling_references(skill_dir) == []


def test_planned_stub_section_is_exempt(tmp_path):
    """Sections that declare no files shipped yet are intentional gaps."""
    skill_dir = _skill(
        tmp_path, "## Tooling\n\nNo scripts shipped yet.\n\n- `scripts/future.sh`\n"
    )
    assert HOOK.find_tooling_references(skill_dir) == []


# ---------------------------------------------------------------------------
# scripts/audit-prompt.md batch tables
# ---------------------------------------------------------------------------


def _fake_repo(tmp_path: Path, prompt: str, skills=("alpha", "beta", "gamma")):
    skills_dir = tmp_path / "skills"
    for name in skills:
        (skills_dir / name).mkdir(parents=True)
        (skills_dir / name / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    prompt_path = tmp_path / "audit-prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    return str(skills_dir), str(prompt_path)


TABLE_HEAD = "| Batch | Skills | Output File |\n|-------|--------|-------------|\n"


def test_parse_audit_batches_reads_the_table():
    text = TABLE_HEAD + "| APIs | a-skill, b-skill | `reports/out.json` |\n| Tools | c-skill | `reports/tools.json` |\n"
    assert HOOK.parse_audit_batches(text) == {
        "APIs": ["a-skill", "b-skill"],
        "Tools": ["c-skill"],
    }


def test_consistent_prompt_has_no_errors(tmp_path):
    skills_dir, prompt = _fake_repo(
        tmp_path, TABLE_HEAD + "| One | alpha, beta, gamma | `o.json` |\n"
    )
    assert HOOK.check_audit_prompt(skills_dir, prompt) == ([], [])


def test_name_that_is_not_a_skill_is_an_error(tmp_path):
    """The original bug: a batch named a skill that had been merged away."""
    skills_dir, prompt = _fake_repo(
        tmp_path, TABLE_HEAD + "| One | alpha, ghost, beta, gamma | `o.json` |\n"
    )
    errors, _ = HOOK.check_audit_prompt(skills_dir, prompt)
    assert len(errors) == 1
    assert "ghost" in errors[0] and "One" in errors[0]


def test_skill_missing_from_every_batch_is_an_error(tmp_path):
    """The other half: a skill that no batch covers."""
    skills_dir, prompt = _fake_repo(tmp_path, TABLE_HEAD + "| One | alpha, beta | `o.json` |\n")
    errors, _ = HOOK.check_audit_prompt(skills_dir, prompt)
    assert len(errors) == 1
    assert "gamma" in errors[0]


def test_duplicate_listing_is_a_warning(tmp_path):
    skills_dir, prompt = _fake_repo(
        tmp_path,
        TABLE_HEAD
        + "| One | alpha, beta | `o.json` |\n| Two | alpha, gamma | `p.json` |\n",
    )
    errors, warnings = HOOK.check_audit_prompt(skills_dir, prompt)
    assert errors == []
    assert len(warnings) == 1 and "alpha" in warnings[0]


def test_prompt_without_a_batch_table_is_an_error(tmp_path):
    skills_dir, prompt = _fake_repo(tmp_path, "# Audit\n\nNo table here.\n")
    errors, _ = HOOK.check_audit_prompt(skills_dir, prompt)
    assert errors and "no batch table" in errors[0]


def test_missing_prompt_file_is_not_an_error(tmp_path):
    skills_dir, _ = _fake_repo(tmp_path, "")
    assert HOOK.check_audit_prompt(skills_dir, str(tmp_path / "nope.md")) == ([], [])


# ---------------------------------------------------------------------------
# ROADMAP 'Published skills' and the README headline count
# ---------------------------------------------------------------------------

CLEAN_ROADMAP = (
    "### Published skills\n\n"
    "- **alpha** — Complete. Does a thing.\n"
    "- **beta** — Complete. Does another thing.\n"
    "\n### What's outstanding\n"
)


def _fake_docs(tmp_path: Path, roadmap: str, readme: str, skills=("alpha", "beta")):
    skills_dir = tmp_path / "skills"
    for name in skills:
        (skills_dir / name).mkdir(parents=True)
        (skills_dir / name / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
    roadmap_path = tmp_path / "ROADMAP.md"
    roadmap_path.write_text(roadmap, encoding="utf-8")
    readme_path = tmp_path / "README.md"
    readme_path.write_text(readme, encoding="utf-8")
    return str(skills_dir), str(roadmap_path), str(readme_path)


def test_roadmap_consistent_has_no_errors(tmp_path):
    skills_dir, roadmap, _ = _fake_docs(tmp_path, CLEAN_ROADMAP, "")
    assert HOOK.check_roadmap(skills_dir, roadmap) == ([], [])


def test_roadmap_entry_for_nonexistent_skill_is_an_error(tmp_path):
    """The bug this guards: a merged-away skill left in the inventory."""
    roadmap = CLEAN_ROADMAP.replace(
        "- **beta** — Complete. Does another thing.",
        "- **beta** — Complete. Does another thing.\n- **ghost** — Complete. Does a ghost thing.",
    )
    skills_dir, roadmap_path, _ = _fake_docs(tmp_path, roadmap, "")
    errors, _ = HOOK.check_roadmap(skills_dir, roadmap_path)
    assert len(errors) == 1 and "ghost" in errors[0]


def test_roadmap_skill_missing_from_the_section_is_an_error(tmp_path):
    roadmap = CLEAN_ROADMAP.replace("- **beta** — Complete. Does another thing.\n", "")
    skills_dir, roadmap_path, _ = _fake_docs(tmp_path, roadmap, "")
    errors, _ = HOOK.check_roadmap(skills_dir, roadmap_path)
    assert len(errors) == 1 and "beta" in errors[0]


def test_roadmap_without_the_section_is_an_error(tmp_path):
    skills_dir, roadmap_path, _ = _fake_docs(tmp_path, "- **alpha** — Complete.\n", "")
    errors, _ = HOOK.check_roadmap(skills_dir, roadmap_path)
    assert errors and "Published skills" in errors[0]


def test_absorbed_skill_notes_are_not_treated_as_entries(tmp_path):
    """Absorbed skills are recorded as italic notes, not live bold entries."""
    roadmap = CLEAN_ROADMAP.replace(
        "- **beta** — Complete. Does another thing.",
        "- *Former `beta` — absorbed into `alpha`.*",
    )
    skills_dir, roadmap_path, _ = _fake_docs(tmp_path, roadmap, "")
    errors, _ = HOOK.check_roadmap(skills_dir, roadmap_path)
    # the note is ignored, so the real problem reported is the gap (not a dead entry)
    assert len(errors) == 1 and "beta" in errors[0] and "ghost" not in errors[0]


def test_readme_count_matches(tmp_path):
    skills_dir, _, readme = _fake_docs(tmp_path, "", "contains **2 skills** organized into groups.\n")
    assert HOOK.check_readme_count(skills_dir, readme) == ([], [])


def test_readme_count_drift_is_an_error(tmp_path):
    skills_dir, _, readme = _fake_docs(tmp_path, "", "contains **3 skills** organized into groups.\n")
    errors, _ = HOOK.check_readme_count(skills_dir, readme)
    assert len(errors) == 1 and "3 skills" in errors[0]


def test_readme_without_a_count_is_allowed(tmp_path):
    """CONTRIBUTING prefers 'all skills'; no count means nothing to drift."""
    skills_dir, _, readme = _fake_docs(tmp_path, "", "contains all skills.\n")
    assert HOOK.check_readme_count(skills_dir, readme) == ([], [])


# ---------------------------------------------------------------------------
# The real repository must satisfy the hook
# ---------------------------------------------------------------------------


def test_repo_tooling_references_are_complete():
    offenders = {}
    for name in sorted(os.listdir(SKILLS_DIR)):
        skill_dir = SKILLS_DIR / name
        if skill_dir.is_dir():
            missing = HOOK.find_tooling_references(str(skill_dir))
            if missing:
                offenders[name] = [ref for ref, _ in missing]
    assert offenders == {}


def test_repo_audit_prompt_matches_skills():
    errors, warnings = HOOK.check_audit_prompt(str(SKILLS_DIR), str(AUDIT_PROMPT))
    assert errors == [], errors
    assert warnings == [], warnings


def test_repo_roadmap_published_matches_skills():
    errors, _ = HOOK.check_roadmap(str(SKILLS_DIR), str(REPO_ROOT / "ROADMAP.md"))
    assert errors == [], errors


def test_repo_readme_count_matches_skills():
    errors, _ = HOOK.check_readme_count(str(SKILLS_DIR), str(REPO_ROOT / "README.md"))
    assert errors == [], errors
