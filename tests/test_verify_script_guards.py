"""Tests for scripts/verify-script-guards.py — the zero-argument guard verifier.

The verifier guards the bug class that arrived with the Toolforge maintainer audit:
a script whose every CLI option is optional ran its *default action* when invoked
bare, which for a network script means an unrequested crawl (count-maintainers.py,
~4,600 requests at 12 threads to a Wikimedia service).

It is an execution check, not a source check — the first draft pattern-matched and
was wrong in both directions (96 flags, 95 of them false). These tests pin the
criterion against fixtures with known behaviour, so the criterion cannot silently
drift back to a spelling test.

Kept fast and offline: the fixtures are synthetic, and the full-tree run belongs to
CI (`python3 scripts/verify-script-guards.py`), not to the unit suite.
"""

import importlib.util
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

_SPEC = importlib.util.spec_from_file_location(
    "verify_script_guards", REPO_ROOT / "scripts" / "verify-script-guards.py"
)
vsg = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(vsg)

SKILLS_DIR = REPO_ROOT / ".claude" / "skills"


class Args:
    """Stand-in for the parsed CLI namespace scan() reads."""

    def __init__(self, files=None, timeout=1.0, max_hangs=10):
        self.files = files
        self.timeout = timeout
        self.max_hangs = max_hangs


# --- the criterion ------------------------------------------------------------

class TestVerdict:
    """Pass = exits in time AND (nonzero + said something, or zero + usage text)."""

    def test_hanging_is_a_violation(self):
        reason = vsg.verdict("TIMEOUT", "", True, 5.0)
        assert reason and "did not exit" in reason

    def test_quiet_success_is_a_violation(self):
        """Exit 0 having printed no usage-looking text = did its default action."""
        reason = vsg.verdict(0, "Preview saved to file:///tmp/x.html", False, 5.0)
        assert reason and "default action" in reason

    def test_quiet_success_with_no_output_is_a_violation(self):
        reason = vsg.verdict(0, "", False, 5.0)
        assert reason and "no output" in reason

    def test_nonzero_with_a_helpful_refusal_passes(self):
        """`No API key: pass --api-key <KEY>` is a guard, just not a pretty one."""
        assert vsg.verdict(1, "No API key: pass --api-key <KEY> or set FLICKR_API_KEY",
                           False, 5.0) is None

    def test_argparse_usage_passes(self):
        assert vsg.verdict(2, "usage: x.py [-h] --name NAME\nx.py: error: required",
                           False, 5.0) is None

    def test_usage_helper_that_exits_zero_passes(self):
        """`usage() { ...; exit 0; }` is a common shell idiom — not a violation."""
        assert vsg.verdict(0, "Usage: commons-search.sh \"query\"", False, 5.0) is None

    def test_unlaunchable_script_is_not_judged(self):
        """A script that could not be started tells us nothing about its guard."""
        assert vsg.verdict("EXC", "ValueError: bad shebang", False, 5.0) is None


# --- fixtures with known behaviour -------------------------------------------

GUARDED_REFUSAL = '''#!/usr/bin/env python3
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default=None)
    args = ap.parse_args()
    if not args.key:
        raise SystemExit("No API key: pass --key <KEY>")
    print("did work")

if __name__ == "__main__":
    main()
'''

GUARDED_USAGE_ZERO = '''#!/usr/bin/env python3
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", default=None)
    args = ap.parse_args()
    if not args.x:
        print("Usage: tool.py --x VALUE")
        raise SystemExit(0)
    print("did work")

if __name__ == "__main__":
    main()
'''

SILENT_WORK = '''#!/usr/bin/env python3
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", default="all")
    args = ap.parse_args()
    print("crawled everything")

if __name__ == "__main__":
    main()
'''

HANGS = '''#!/usr/bin/env python3
import argparse, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", default=None)
    args = ap.parse_args()
    time.sleep(60)

if __name__ == "__main__":
    main()
'''

SILENT_SH = '''#!/usr/bin/env bash
set -euo pipefail
echo "did the default thing"
'''

GUARDED_SH = '''#!/usr/bin/env bash
set -euo pipefail
if [ $# -eq 0 ]; then
    echo "Usage: $(basename "$0") <arg>" >&2
    exit 1
fi
'''

NOT_AN_ENTRY_POINT = '''#!/usr/bin/env python3
"""A helper module, imported not executed."""
import argparse

def run(args): return args
'''

WRITES_A_FILE = '''#!/usr/bin/env python3
import argparse, pathlib

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", default=None)
    ap.parse_args()
    pathlib.Path(__file__).with_name("side-effect.txt").write_text("wrote here")
    print("Usage: wrote.py --x VALUE")

if __name__ == "__main__":
    main()
'''

NETWORK_PROBE = '''#!/usr/bin/env python3
import argparse, socket

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--x", default=None)
    ap.parse_args()
    try:
        socket.create_connection(("127.0.0.1", 9), timeout=1)
        print("REACHED")
    except OSError as e:
        print(f"blocked: {e}")

if __name__ == "__main__":
    main()
'''


def write_skill_scripts(tmp_path: Path, scripts: dict[str, str]) -> Path:
    """Create a fake skills tree with one script per {relpath: source}."""
    root = tmp_path / "skills"
    for rel, body in scripts.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body)
    return root


class TestScanCriterion:
    """End-to-end scan of fixtures whose no-arg behaviour is known by construction."""

    def test_flags_exactly_the_unguarded_scripts(self, tmp_path):
        root = write_skill_scripts(tmp_path, {
            "demo-skill/scripts/guarded_refusal.py": GUARDED_REFUSAL,
            "demo-skill/scripts/guarded_usage_zero.py": GUARDED_USAGE_ZERO,
            "demo-skill/scripts/guarded.sh": GUARDED_SH,
            "demo-skill/scripts/silent_work.py": SILENT_WORK,
            "demo-skill/scripts/silent.sh": SILENT_SH,
            "demo-skill/scripts/hangs.py": HANGS,
        })
        violations, examined, _ = vsg.scan(root, Args(timeout=1.5))
        flagged = {v["file"] for v in violations}
        assert flagged == {"demo-skill/scripts/silent_work.py",
                           "demo-skill/scripts/silent.sh",
                           "demo-skill/scripts/hangs.py"}
        assert examined == 6

    def test_module_without_main_is_skipped(self, tmp_path):
        """An importable helper is not an entry point and has nothing to guard."""
        root = write_skill_scripts(tmp_path, {
            "demo-skill/assets/helper.py": NOT_AN_ENTRY_POINT,
        })
        violations, examined, _ = vsg.scan(root, Args())
        assert violations == [] and examined == 0

    def test_exempt_scripts_are_not_run(self, tmp_path):
        root = write_skill_scripts(tmp_path, {
            "demo-skill/scripts/silent_work.py": SILENT_WORK,
        })
        vsg.EXEMPT["demo-skill/scripts/silent_work.py"] = "test fixture"
        try:
            violations, examined, _ = vsg.scan(root, Args())
        finally:
            del vsg.EXEMPT["demo-skill/scripts/silent_work.py"]
        assert violations == [] and examined == 0

    def test_max_hangs_stops_early(self, tmp_path):
        root = write_skill_scripts(tmp_path, {
            "demo-skill/scripts/silent_a.py": SILENT_WORK,
            "demo-skill/scripts/silent_b.py": SILENT_WORK,
            "demo-skill/scripts/silent_c.py": SILENT_WORK,
        })
        violations, examined, stopped = vsg.scan(root, Args(max_hangs=2))
        assert len(violations) == 2 and stopped and examined == 2


class TestSandbox:
    """The scripts under test are not trusted: writes and network are contained."""

    def test_writes_land_in_the_throwaway_copy(self, tmp_path):
        root = write_skill_scripts(tmp_path, {
            "demo-skill/scripts/writer.py": WRITES_A_FILE,
        })
        vsg.scan(root, Args())
        assert not (root / "demo-skill" / "scripts" / "side-effect.txt").exists(), \
            "a scanned script wrote into the real tree"

    def test_network_is_blocked(self, tmp_path):
        """Sockets are blocked by the injected sitecustomize, not merely unrouted."""
        root = write_skill_scripts(tmp_path, {
            "demo-skill/scripts/probe.py": NETWORK_PROBE,
        })
        work, harness = vsg.build_sandbox(root)
        try:
            env = vsg.sandbox_env(harness)
            probe = work / "skills" / "demo-skill" / "scripts" / "probe.py"
            _, out, hung = vsg.run_bare([sys.executable, str(probe)], work, env, 10)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        assert not hung
        assert "NETWORK BLOCKED" in out, f"socket was not blocked; got: {out!r}"

    def test_proxy_env_points_somewhere_unroutable(self, tmp_path):
        """Shell scripts calling curl/wget must fail fast, not reach the network."""
        env = vsg.sandbox_env(tmp_path)
        for var in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"):
            assert "127.0.0.1:9" in env[var]
        assert "NO_PROXY" not in env and "no_proxy" not in env


class TestExemptions:
    """EXEMPT is how bare invocation is declared intentional — with a reason."""

    def test_every_exemption_states_why(self):
        for name, reason in vsg.EXEMPT.items():
            assert reason.strip(), f"{name} is exempt with no reason"
            assert len(reason) > 30, f"{name} needs a real reason, not a stub"

    def test_every_exempt_file_exists(self):
        for name in vsg.EXEMPT:
            assert (SKILLS_DIR / name).is_file(), f"{name} is exempt but does not exist"

    def test_exemptions_are_script_paths(self):
        for name in vsg.EXEMPT:
            assert name.endswith((".py", ".sh")), f"{name} is not a script"


class TestRealTree:
    """The shipped tree must be clean — this is what CI enforces."""

    def test_scope_covers_the_scripts_the_readme_advertises(self):
        """Guard against a scope that quietly stops looking at anything."""
        count = sum(1 for p in SKILLS_DIR.rglob("*")
                    if p.is_file() and p.suffix in (".py", ".sh"))
        assert count > 100, f"only {count} scripts in scope; scope is too narrow"

    def test_count_maintainers_is_guarded(self):
        """The regression that motivated this verifier: it must stay refused."""
        script = SKILLS_DIR / "wikimedia-toolforge" / "scripts" / "count-maintainers.py"
        violations, examined, _ = vsg.scan(SKILLS_DIR, Args(files=[script], timeout=10))
        assert examined == 1
        assert violations == [], "count-maintainers.py lost its zero-argument guard"
