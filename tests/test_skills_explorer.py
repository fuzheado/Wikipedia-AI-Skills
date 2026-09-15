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
        assert rec["url"].startswith("https://github.com/"), rec
        assert rec["url"].endswith(f"/{rec['name']}/SKILL.md"), rec
        assert rec["domain"] and rec["task"], rec
        assert isinstance(rec["roles"], list), rec
        assert isinstance(rec["depends_on"], list), rec
        assert isinstance(rec["cross_links"], list), rec
        assert rec["degree"] == len(rec["cross_links"]), rec


def test_card_links_are_absolute_so_they_work_on_pages():
    """GitHub Pages serves docs/ as the site root, so a repo-relative href 404s there.

    Card links are built client-side from the embedded records, so this checks the
    template expression and the data rather than a literal href attribute.
    """
    gen = _load_generator()
    records = gen.skill_records()
    committed = COMMITTED_HTML.read_text(encoding="utf-8")
    assert "escapeHtml(s.url)" in committed, "card links must use the absolute url field"
    assert "escapeHtml(s.path)" not in committed, (
        "card links must not use the repo-relative path — those 404 on the published site"
    )
    assert committed.count('"url":"https://github.com/') == len(records), (
        "every embedded record needs an absolute url"
    )


def test_committed_html_is_in_sync_with_the_generator(tmp_path):
    """A skill add/rename that skips regeneration must fail here, not in the browser."""
    gen = _load_generator()
    regenerated = tmp_path / "skills-explorer.html"
    gen.write_html(gen.skill_records(), out=regenerated)
    assert regenerated.read_text(encoding="utf-8") == COMMITTED_HTML.read_text(encoding="utf-8"), (
        "docs/skills-explorer.html is stale — run: python3 scripts/generate-skills-explorer.py"
    )
