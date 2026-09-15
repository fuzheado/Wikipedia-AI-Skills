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
