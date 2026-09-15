"""Tests for the skill verification suite (verify-freshness, verify-links,
verify-api, verify-snippets). The command verifier has its own test file.

Every verifier must:
  1. pass on the real repo (no false positives), and
  2. flag its target bug class (no false negatives).
"""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / ".claude" / "skills"
SCRIPTS = REPO_ROOT / "scripts"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


freshness = load("verify-freshness")
links = load("verify-links")
api = load("verify-api")
snippets = load("verify-snippets")
mul = load("verify-mul-labels")


def make_skill(tmp_path: Path, content: str) -> Path:
    d = tmp_path / "skills" / "test-skill"
    d.mkdir(parents=True)
    f = d / "SKILL.md"
    f.write_text(content)
    return d


# ---------------------------------------------------------------------------
# verify-freshness
# ---------------------------------------------------------------------------

def test_freshness_ok(tmp_path):
    d = make_skill(tmp_path, "---\nname: test\nlast_verified: 2026-08-08\n---\n")
    assert freshness.check_skill(d / "SKILL.md", 365) == []


def test_freshness_missing(tmp_path):
    d = make_skill(tmp_path, "---\nname: test\n---\n")
    assert freshness.check_skill(d / "SKILL.md", 365)


def test_freshness_stale(tmp_path):
    d = make_skill(tmp_path, "---\nname: test\nlast_verified: 2020-01-01\n---\n")
    assert freshness.check_skill(d / "SKILL.md", 365)


def test_freshness_future(tmp_path):
    d = make_skill(tmp_path, "---\nname: test\nlast_verified: 2099-01-01\n---\n")
    assert freshness.check_skill(d / "SKILL.md", 365)


# ---------------------------------------------------------------------------
# verify-links (structural, no registry)
# ---------------------------------------------------------------------------

def test_links_depends_on_missing(tmp_path):
    d = make_skill(tmp_path, "---\nname: test\ndepends_on: [no-such-skill]\n---\n")
    problems = links.scan_file(d / "SKILL.md", SKILLS, None)
    assert any("depends_on" in p for p in problems)


def test_links_broken_local_ref(tmp_path):
    d = make_skill(tmp_path, "See [ref](references/missing.md)\n")
    problems = links.scan_file(d / "SKILL.md", SKILLS, None)
    assert any("broken local reference" in p for p in problems)


def test_links_repo_is_clean():
    problems = []
    for f in sorted(SKILLS.rglob("*.md")):
        problems.extend(links.scan_file(f, SKILLS, None))
    assert problems == [], "\n".join(problems)


def test_links_url_registry_flags_unlisted(tmp_path):
    d = make_skill(tmp_path, "See https://tools-static.test-registry.org/thing\n")
    problems = links.scan_file(d / "SKILL.md", SKILLS, {})
    assert any("not in url-registry" in p for p in problems)


def test_links_url_registry_flags_http_error(tmp_path):
    d = make_skill(tmp_path, "See https://tools-static.test-registry.org/thing\n")
    problems = links.scan_file(d / "SKILL.md", SKILLS,
                               {"urls": {"https://tools-static.test-registry.org/thing": 404}})
    assert any("status 404" in p for p in problems)


def test_links_url_registry_ok(tmp_path):
    d = make_skill(tmp_path, "See https://tools-static.test-registry.org/thing\n")
    problems = links.scan_file(d / "SKILL.md", SKILLS,
                               {"urls": {"https://tools-static.test-registry.org/thing": 200}})
    assert problems == []


def test_links_templated_urls_skipped(tmp_path):
    d = make_skill(tmp_path, "See https://{lang}.wikipedia.org and https://...\n")
    problems = links.scan_file(d / "SKILL.md", SKILLS, {})
    assert problems == []


# ---------------------------------------------------------------------------
# verify-api
# ---------------------------------------------------------------------------

SURFACE = json.loads((SCRIPTS / "api-surface.json").read_text())


def test_api_repo_is_clean():
    problems = []
    for f in sorted(SKILLS.rglob("*.md")):
        problems.extend(api.scan_file(f, SURFACE))
    assert problems == [], "\n".join(problems)


@pytest.mark.parametrize("url", [
    "https://en.wikipedia.org/w/api.php?action=querry&format=json",
    "https://en.wikipedia.org/w/api.php?action=query&prop=revisons&format=json",
    "https://en.wikipedia.org/w/api.php?action=query&list=allpagges&format=json",
    "https://en.wikipedia.org/w/api.php?action=query&meta=siteifno&format=json",
    "https://en.wikipedia.org/w/api.php?action=templatestyles&modules=x&format=json",
])
def test_api_flags_hallucinations(tmp_path, url):
    d = make_skill(tmp_path, f"```bash\ncurl '{url}'\n```\n")
    assert api.scan_file(d / "SKILL.md", SURFACE), f"should flag: {url}"


@pytest.mark.parametrize("url", [
    "https://en.wikipedia.org/w/api.php?action=query&prop=revisions&format=json",
    "https://en.wikipedia.org/w/api.php?action=query&meta=siteinfo&format=json",
    "https://en.wikipedia.org/w/api.php?action=parse&prop=wikitext&format=json",
    "https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q42&format=json",
    "https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&format=json",
])
def test_api_accepts_real_calls(tmp_path, url):
    d = make_skill(tmp_path, f"```bash\ncurl '{url}'\n```\n")
    assert api.scan_file(d / "SKILL.md", SURFACE) == [], f"should accept: {url}"


# ---------------------------------------------------------------------------
# verify-snippets
# ---------------------------------------------------------------------------

def test_snippets_repo_is_clean():
    problems = []
    for f in sorted(SKILLS.rglob("*.md")):
        problems.extend(snippets.scan_file(f))
    assert problems == [], "\n".join(str(p) for p in problems)


def test_snippets_flags_broken_python(tmp_path):
    d = make_skill(tmp_path, "```python\ndef main():\n  print('x'\n```\n")
    assert snippets.scan_file(d / "SKILL.md")


def test_snippets_flags_broken_bash(tmp_path):
    d = make_skill(tmp_path, "```bash\necho 'unclosed\n```\n")
    assert snippets.scan_file(d / "SKILL.md")


def test_snippets_flags_broken_json(tmp_path):
    d = make_skill(tmp_path, "```json\n{\"a\": 1,}\n```\n")
    assert snippets.scan_file(d / "SKILL.md")


def test_snippets_skips_placeholders(tmp_path):
    d = make_skill(tmp_path, "```bash\nssh <user>@login.toolforge.org\n```\n")
    assert snippets.scan_file(d / "SKILL.md") == []


def test_snippets_skips_annotated_json(tmp_path):
    d = make_skill(tmp_path, "```json\n{ \"a\": 1,  # annotated\n}\n```\n")
    assert snippets.scan_file(d / "SKILL.md") == []


# ---------------------------------------------------------------------------
# verify-mul-labels
# ---------------------------------------------------------------------------

def test_mul_flags_label_service_without_mul(tmp_path):
    d = make_skill(
        tmp_path,
        'SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }\n',
    )
    problems, _ = mul.scan_file(d / "SKILL.md", tmp_path / "skills")
    assert any("SPARQL label service without mul" in p for p in problems)


def test_mul_accepts_label_service_with_mul(tmp_path):
    d = make_skill(
        tmp_path,
        'bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en".\n',
    )
    problems, _ = mul.scan_file(d / "SKILL.md", tmp_path / "skills")
    assert problems == []


def test_mul_decodes_url_encoded_sparql(tmp_path):
    """The shell-script status check embeds a percent-encoded SPARQL query."""
    d = make_skill(tmp_path, 'query=...wikibase:language%20%22en%22...\n')
    problems, _ = mul.scan_file(d / "SKILL.md", tmp_path / "skills")
    assert any("SPARQL label service without mul" in p for p in problems)


def test_mul_flags_piped_languages_without_mul(tmp_path):
    d = make_skill(tmp_path, '"languages": "en|fr|de",\n')
    problems, _ = mul.scan_file(d / "SKILL.md", tmp_path / "skills")
    assert any("multi-language label request without mul" in p for p in problems)


def test_mul_ignores_bare_separator_literal(tmp_path):
    """`"|".join(langs)` is a separator, not a language list."""
    d = make_skill(tmp_path, '"languages": "|".join(langs),\n')
    problems, _ = mul.scan_file(d / "SKILL.md", tmp_path / "skills")
    assert problems == []


def test_mul_allow_marker_suppresses_negative_example(tmp_path):
    d = make_skill(
        tmp_path,
        'bd:serviceParam wikibase:language "en".  # verify-mul-labels: allow (demo)\n',
    )
    problems, marked = mul.scan_file(d / "SKILL.md", tmp_path / "skills")
    assert problems == []
    assert marked


def test_mul_repo_is_clean():
    problems = []
    for path in mul._iter_files(SKILLS):
        file_problems, _ = mul.scan_file(path, SKILLS)
        problems.extend(file_problems)
    problems.extend(mul.scan_label_readers(SKILLS))
    assert problems == [], "\n".join(problems)


def test_mul_flags_pinned_reader_without_default_handling(tmp_path):
    skills = tmp_path / "skills"
    for rel in mul.LABEL_READERS:
        p = skills / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("label = labels.get('en')\n")
    assert len(mul.scan_label_readers(skills)) == len(mul.LABEL_READERS)


def test_mul_accepts_pinned_reader_with_default_handling(tmp_path):
    skills = tmp_path / "skills"
    for rel in mul.LABEL_READERS:
        p = skills / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("label = labels.get('en') or labels.get('mul')\n")
    assert mul.scan_label_readers(skills) == []


def test_mul_pinned_readers_exist():
    assert mul.scan_label_readers(SKILLS) == []


# ---------------------------------------------------------------------------
# registry sanity
# ---------------------------------------------------------------------------

def test_command_registry_rejects_known_hallucinations():
    reg = json.loads((SCRIPTS / "command-registry.json").read_text())
    tf = reg["binaries"]["toolforge"]["subcommands"]
    assert "tools" not in tf and "env" not in tf and "db" not in tf
    assert "envvars" in tf and "build" in tf and "jobs" in tf
    assert {"create", "delete", "list", "quota", "show"} <= set(reg["binaries"]["toolforge"]["sub"]["envvars"])


def test_api_surface_rejects_known_hallucinations():
    assert "querry" not in SURFACE["action"]
    assert "templatestyles" not in SURFACE["action"]
    assert "revisons" not in SURFACE["query"]["prop"]
    assert "revisions" in SURFACE["query"]["prop"]
    assert "siteinfo" in SURFACE["query"]["meta"]
    assert "wikitext" in SURFACE["action_props"]["parse"]
