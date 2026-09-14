"""Tests for scripts/generate-skills-explorer.py — the static skills directory.

`docs/skills-explorer.html` is committed build output. These tests keep it in
sync with `.claude/skills/*/SKILL.md` (so a new or renamed skill cannot silently
go missing from the explorer) and guard the generator's record shape.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate-skills-explorer.py"
COMMITTED_HTML = ROOT / "docs" / "skills-explorer.html"
SKILLS_DIR = ROOT / ".claude" / "skills"


def _load_generator():
    """Load scripts/generate-skills-explorer.py (hyphenated filename -> importlib)."""
    spec = importlib.util.spec_from_file_location("generate_skills_explorer", GENERATOR)
    assert spec and spec.loader, f"cannot load {GENERATOR}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_generator_emits_one_record_per_skill():
    gen = _load_generator()
    records = gen.skill_records()
    skill_dirs = sorted(p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md"))
    assert [r["name"] for r in records] == skill_dirs
    assert len(records) == len(skill_dirs)


def test_every_record_has_the_fields_the_page_renders():
    gen = _load_generator()
    for rec in gen.skill_records():
        assert rec["name"], rec
        assert rec["description"], rec
        assert rec["path"].startswith("../.claude/skills/"), rec
        assert rec["domain"] and rec["task"], rec
        assert isinstance(rec["roles"], list), rec
        assert isinstance(rec["depends_on"], list), rec
        assert isinstance(rec["cross_links"], list), rec
        assert rec["degree"] == len(rec["cross_links"]), rec


def test_committed_html_is_in_sync_with_the_generator(tmp_path):
    """A skill add/rename that skips regeneration must fail here, not in the browser."""
    gen = _load_generator()
    regenerated = tmp_path / "skills-explorer.html"
    gen.write_html(gen.skill_records(), out=regenerated)
    assert regenerated.read_text(encoding="utf-8") == COMMITTED_HTML.read_text(encoding="utf-8"), (
        "docs/skills-explorer.html is stale — run: python3 scripts/generate-skills-explorer.py"
    )
