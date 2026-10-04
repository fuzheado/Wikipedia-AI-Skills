"""Tests for scripts/verify-rest-enums.py — the AQS endpoint/parameter verifier.

The verifier guards two bug classes the existing suite could not see:

  * a documented endpoint that does not exist (`/metrics/pageviews/top-by-ec/…`)
  * a parameter value the live service rejects, presented as usable
    (`agent_type=automated` -> HTTP 400 on mediarequests, while `agent=automated`
    is a perfectly good value on pageviews)

These tests keep the verifier itself honest: it must pass on the real repo, must
flag known-bad lines, and must stay quiet on the loudest false-positive classes
(base URLs, elided paths, spec links, and lines that *warn about* a bad value).

Offline throughout — the surface file is checked in and no request is made here.
"""

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SURFACE = REPO_ROOT / "scripts" / "rest-surface.json"

# verify-rest-enums.py has hyphens, so load it as a module via importlib.
_SPEC = importlib.util.spec_from_file_location(
    "verify_rest_enums", REPO_ROOT / "scripts" / "verify-rest-enums.py"
)
verify_rest_enums = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(verify_rest_enums)


def run(skills_dir: Path, surface: Path = SURFACE, capsys=None) -> tuple[int, str]:
    """Invoke the verifier's CLI against a skills directory; return (exit, stdout)."""
    argv = ["verify-rest-enums.py", "--skills-dir", str(skills_dir), "--surface", str(surface)]
    old = sys.argv
    sys.argv = argv
    try:
        code = verify_rest_enums.main()
    finally:
        sys.argv = old
    out = capsys.readouterr().out if capsys is not None else ""
    return code, out


def make_skill(tmp_path: Path, body: str) -> Path:
    root = tmp_path / "skills"
    skill = root / "wikimedia-pageviews"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(body)
    return root


# ---------------------------------------------------------------------------
# The verifier must PASS on the real repo.
# ---------------------------------------------------------------------------

def test_repo_is_clean():
    code, _ = run(REPO_ROOT / ".claude" / "skills")
    assert code == 0, "verify-rest-enums reports violations against the committed skills"


def test_surface_file_is_populated():
    """A stale or emptied surface must not silently pass everything."""
    surface = json.loads(SURFACE.read_text())
    paths = [p for p in surface["paths"] if p.startswith("/metrics/")]
    assert len(paths) >= 30, f"only {len(paths)} AQS path templates recorded"
    params = surface.get("params") or {}
    assert params, "no probed parameters recorded"
    # The probe that matters most: the same word is valid on one API, a 400 on another.
    assert params["mediarequests:agent_type"]["invalid"].get("automated") == 400
    assert "automated" in params["pageviews:agent"]["valid"]
    assert "user" in params["pageviews:agent"]["valid"]


# ---------------------------------------------------------------------------
# Known-bad lines must be flagged.
# ---------------------------------------------------------------------------

def test_flags_nonexistent_endpoint(tmp_path, capsys):
    root = make_skill(tmp_path, "```\nGET /top-by-ec/{project}/{access}/{year}/{month}\n```\n")
    code, out = run(root, capsys=capsys)
    assert code == 1
    assert "top-by-ec" in out


def test_flags_nonexistent_endpoint_in_full_url(tmp_path, capsys):
    url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/top-by-ec/de.wikipedia/all-access/2026/08"
    root = make_skill(tmp_path, f"See {url}\n")
    code, out = run(root, capsys=capsys)
    assert code == 1
    assert "top-by-ec" in out


def test_flags_rejected_parameter_value(tmp_path, capsys):
    root = make_skill(
        tmp_path, "Filters: `agent_type` (user/spider/automated/all-agents), and `granularity`.\n"
    )
    code, out = run(root, capsys=capsys)
    assert code == 1
    assert "automated" in out


# ---------------------------------------------------------------------------
# The loudest false-positive classes must stay quiet.
# ---------------------------------------------------------------------------

def test_allows_valid_endpoint_and_base_url(tmp_path, capsys):
    body = (
        "Base: `https://wikimedia.org/api/rest_v1/metrics/pageviews/`\n"
        "```\nGET /top/{project}/{access}/{year}/{month}/{day}\n```\n"
        "GET /per-article/{project}/{access}/{agent}/{article}/{daily}/{start}/{end}\n"
    )
    root = make_skill(tmp_path, body)
    code, out = run(root, capsys=capsys)
    assert code == 0, out


def test_skips_elided_paths_and_spec_links(tmp_path, capsys):
    body = (
        "`https://wikimedia.org/api/rest_v1/metrics/pageviews/...`\n"
        "Spec: https://wikimedia.org/api/rest_v1/metrics/commons-analytics/api-spec.json\n"
    )
    root = make_skill(tmp_path, body)
    code, out = run(root, capsys=capsys)
    assert code == 0, out


def test_warning_lines_are_not_flagged(tmp_path, capsys):
    """A skill that correctly warns about `automated` must not be punished for it."""
    body = (
        "`agent_type` (spider | user — **no `automated`**; the value returns HTTP 400)\n"
        "`agent_type` (user/spider only — no automated value exists in webrequest)\n"
    )
    root = make_skill(tmp_path, body)
    code, out = run(root, capsys=capsys)
    assert code == 0, out


def test_core_rest_paths_are_out_of_scope(tmp_path, capsys):
    """`/page/…` belongs to a different surface and must not be resolved against AQS."""
    root = make_skill(
        tmp_path,
        "Base: https://wikimedia.org/api/rest_v1/metrics/pageviews/\n"
        "| `GET /page/with-edits/{title}` | edit metadata |\n",
    )
    code, out = run(root, capsys=capsys)
    assert code == 0, out
