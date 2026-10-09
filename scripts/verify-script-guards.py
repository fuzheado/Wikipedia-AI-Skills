#!/usr/bin/env python3
"""verify-script-guards.py — Enforce the zero-argument guard on skill scripts.

`.claude/guidelines/script-audit-guidelines.md` §1 requires every skill script to
print a helpful usage message when invoked with no arguments, and the README
advertises that guarantee ("zero-argument guard — every script prints a helpful
usage message when invoked with no arguments"). Nothing enforced it, so a script
whose every CLI option is optional ran its *default action* when invoked bare.
For a network script that means an unrequested crawl: count-maintainers.py
(2026-10-03) launched a ~4,600-request sweep of toolsadmin.wikimedia.org at 12
threads when run with no arguments.

Why this is an execution check, not a source check
--------------------------------------------------
The first draft of this verifier pattern-matched source, and was wrong in both
directions: it flagged 96 scripts, of which 95 print a perfectly good guard that
simply does not look like the pattern (a `raise SystemExit("No API key: ...")`,
a `usage()` helper that `exit 0`s, a `${1:-default}` default). "Does invoking it
bare do work?" is a *behaviour*, so this check runs the script and looks.

Sandboxing (the scripts under test are not trusted)
--------------------------------------------------
  * the skills tree is copied to a temp dir and scripts run there, so writes
    land in the throwaway copy (one script legitimately writes a preview file);
  * `socket.connect` / `create_connection` are blocked by an injected
    `sitecustomize`, and proxy env vars point at the unroutable port 9, so a
    `curl` inside a shell script fails fast instead of reaching the network;
  * stdin is /dev/null, stdout/stderr are captured, and each script gets a
    process-group timeout it cannot outlive.

Pass criterion, per script invoked with no arguments:
  * exits within --timeout, and
  * either exits nonzero having printed something (a helpful refusal counts:
    `No API key: pass --api-key <KEY>`), or exits zero having printed
    usage-looking text (`usage() { ...; exit 0; }` is a common idiom).

Two ways to fail: it hangs (starts work with no end in sight), or it exits zero
without printing anything usage-looking (silently performs its default action).

A third outcome: NOT EXERCISED (missing optional dependency)
------------------------------------------------------------
A nonzero exit only counts as a guard if the script actually got to make that
decision. A Python script that dies on `import requests` exits nonzero with a
message and therefore *passes* — without its guard ever running. That made the
verdict depend on the interpreter used: the same tree reported 0 violations
under a bare `python3` (no `requests`) and 2 violations under an interpreter
that has `requests` installed, because there the scripts got past the import
and ran their default action (language_explorer.py, api_client.py — both were
fixed, not exempted). So an uncaught `ModuleNotFoundError`/`ImportError`
traceback is now counted and reported as "not exercised" instead of being
silently read as a pass. It is *not* a violation (CI runs an interpreter
without those extras and must stay green), but it is no longer invisible
either: the summary names the missing module(s) so a green run cannot be
mistaken for proof that every guard was executed.

Usage:
    python3 scripts/verify-script-guards.py
    python3 scripts/verify-script-guards.py --json
    python3 scripts/verify-script-guards.py --timeout 10 --max-hangs 5
    python3 scripts/verify-script-guards.py --files path/to/script.py ...
    python3 scripts/verify-script-guards.py --list-exempt

Exit codes: 0 = every in-scope script is guarded, 1 = violation(s) found.
"""

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Text that marks "this is a usage message", accepting the two idioms in the repo:
# argparse's `usage: ...` / `error: the following arguments are required`, and the
# hand-rolled `Usage:` / `no arguments` / `Available ...` forms.
USAGEISH = (
    "usage",
    "no arguments",
    "required",
    "available ",          # e.g. "Available maintenance queries:"
)

BLOCKER_SITECUSTOMIZE = '''
import socket
def _blocked(*a, **k):
    raise OSError("NETWORK BLOCKED (verify-script-guards harness)")
socket.socket.connect = _blocked
socket.create_connection = _blocked
'''

PY_ENTRY_RE = re.compile(r"if\s+__name__\s*==\s*['\"]__main__['\"]")
IMPORTS_ARGPARSE_RE = re.compile(r"^\s*(?:import\s+argparse|from\s+argparse\s+import)", re.M)

# Scripts whose bare invocation IS the intended use, so printing usage instead
# would break them. Each needs a reason: an exemption is a decision, not a silencer.
EXEMPT: dict[str, str] = {
    "wikimedia-api-access/scripts/test-api.sh":
        "Connectivity smoke test: running with no arguments is the whole point "
        "(`$1` is an optional User-Agent override).",
    "wikipedia-error-handling/scripts/check-api-status.sh":
        "API status check: bare invocation is the documented use; it takes no "
        "required arguments by design.",
    "wikimedia-database/scripts/close-tunnel.sh":
        "Idempotent cleanup helper: bare invocation closes the default tunnel "
        "(`${1:-${TOOLFORGE_DB_PORT:-3307}}`), which is bounded and reversible.",
    "wikipedia-wikitables/scripts/wikitable-to-html.sh":
        "Stdin filter: reads the wikitable from stdin or the clipboard, so bare "
        "invocation with empty stdin is a no-op, not a default action.",
    "wikimedia-toolforge/assets/deploy-config.sh":
        "Sourceable config template (`source deploy-config.sh`), not an entry "
        "point; it only assigns variables and prints nothing.",
}


def is_candidate(path: Path, text: str) -> bool:
    """True if this file is an in-scope entry-point script worth running"""
    if path.suffix == ".sh":
        return True
    if path.suffix != ".py":
        return False
    return bool(PY_ENTRY_RE.search(text) and IMPORTS_ARGPARSE_RE.search(text))


def build_sandbox(skills_dir: Path) -> tuple[Path, Path]:
    """Copy the skills tree and an injection dir; return (workdir, harness_dir)."""
    work = Path(tempfile.mkdtemp(prefix="verify-script-guards-"))
    shutil.copytree(skills_dir, work / "skills")
    harness = work / "harness"
    harness.mkdir()
    (harness / "sitecustomize.py").write_text(BLOCKER_SITECUSTOMIZE)
    return work, harness


def sandbox_env(harness: Path) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(harness)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for var in ("http_proxy", "https_proxy", "all_proxy",
                "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        env[var] = "http://127.0.0.1:9"   # unroutable: fail fast, no network
    for var in ("NO_PROXY", "no_proxy"):
        env.pop(var, None)
    return env


def run_bare(cmd: list[str], cwd: Path, env: dict, timeout: float) -> tuple[int | str, str, bool]:
    """Run cmd with no args. Return (rc, output, hung). Kills the whole group on timeout."""
    p = subprocess.Popen(cmd, cwd=str(cwd), env=env, stdin=subprocess.DEVNULL,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         start_new_session=True)
    try:
        out = p.communicate(timeout=timeout)[0]
        return p.returncode, out.decode("utf-8", "replace"), False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            p.kill()
        p.communicate()
        partial = b""
        return "TIMEOUT", partial.decode("utf-8", "replace"), True
    except Exception as exc:                                   # pragma: no cover
        return "EXC", f"{type(exc).__name__}: {exc}", False


def looks_usageish(out: str) -> bool:
    low = out.lower()
    return bool(out.strip()) and any(m in low for m in USAGEISH)


# An *uncaught* import failure means the bare run never reached the script's own
# argument handling, so the pass/nonzero verdict says nothing about its guard.
TRACEBACK_MARKER = "Traceback (most recent call last):"
MISSING_DEP_RE = re.compile(
    r"^(?:ModuleNotFoundError|ImportError): No module named ['\"]([A-Za-z0-9_.]+)['\"]",
    re.M,
)


def missing_dependency(rc: int | str, out: str, hung: bool) -> str | None:
    """Return the missing module name if the bare run died on an import.

    Requires BOTH a real traceback and an uncaught ModuleNotFoundError/ImportError
    line, so a script that *catches* the error and prints a helpful refusal
    ("install X: pip install foo") keeps counting as guarded.
    """
    if hung or rc in ("EXC", "TIMEOUT") or rc == 0:
        return None
    if TRACEBACK_MARKER not in out:
        return None
    m = MISSING_DEP_RE.search(out)
    return m.group(1) if m else None


def verdict(rc: int | str, out: str, hung: bool, timeout: float) -> str | None:
    """Return a violation reason, or None if the script is guarded."""
    if hung:
        return (f"no zero-argument guard: invoking it bare started work and did not "
                f"exit within {timeout:g}s")
    if rc == "EXC":
        return None                       # could not be launched; not a guard question
    if rc == 0 and not looks_usageish(out):
        detail = out.strip().splitlines()[0][:80] if out.strip() else "(no output)"
        return (f"no zero-argument guard: invoking it bare performed its default action "
                f"and exited 0 — {detail}")
    return None                            # nonzero + a message, or zero + usage text


def scan(skills_dir: Path, args) -> tuple[list[dict], int, bool, list[dict]]:
    work, harness = build_sandbox(skills_dir)
    try:
        env = sandbox_env(harness)
        root = work / "skills"
        # Paths from --files are re-pointed into the sandbox, so even a targeted run
        # cannot write to the real tree.
        targets: list[tuple[Path, Path]] = []
        if args.files:
            for f in args.files:
                try:
                    rel = f.resolve().relative_to(skills_dir.resolve())
                except ValueError:
                    targets.append((f, Path(f.name)))
                    continue
                targets.append((root / rel, rel))
        else:
            targets = [(p, p.relative_to(root)) for p in sorted(root.rglob("*"))]

        violations: list[dict] = []
        unexercised: list[dict] = []
        examined = 0
        stopped = False
        for path, rel in targets:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if not is_candidate(path, text):
                continue
            if rel.as_posix() in EXEMPT:
                continue
            examined += 1
            cmd = [sys.executable, str(path)] if path.suffix == ".py" else ["bash", str(path)]
            rc, out, hung = run_bare(cmd, work, env, args.timeout)
            dep = missing_dependency(rc, out, hung) if path.suffix == ".py" else None
            if dep:
                # Died on `import X`: the verdict would be an artefact of this
                # interpreter, not a statement about the script's guard.
                unexercised.append({"file": str(rel), "module": dep, "exit_code": rc})
                continue
            reason = verdict(rc, out, hung, args.timeout)
            if reason:
                violations.append({"file": str(rel), "reason": reason,
                                   "exit_code": rc})
                if len(violations) >= args.max_hangs:
                    stopped = True
                    break
        return violations, examined, stopped, unexercised
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR)
    ap.add_argument("--files", nargs="*", type=Path, help="only check these script paths")
    ap.add_argument("--timeout", type=float, default=5.0,
                    help="seconds a bare invocation may take before it counts as a hang")
    ap.add_argument("--max-hangs", type=int, default=3,
                    help="stop after finding this many violations (default 3)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--list-exempt", action="store_true",
                    help="show the exemption list and exit")
    args = ap.parse_args(argv)

    if args.list_exempt:
        if not EXEMPT:
            print("no exemptions")
        for name, reason in sorted(EXEMPT.items()):
            print(f"{name}\n    {reason}")
        return 0

    if not args.skills_dir.is_dir():
        print(f"error: skills dir not found: {args.skills_dir}", file=sys.stderr)
        return 1

    violations, examined, stopped, unexercised = scan(args.skills_dir, args)

    if args.json:
        print(json.dumps({"violations": violations, "examined": examined,
                          "stopped_early": stopped, "unexercised": unexercised,
                          "exempt": sorted(EXEMPT)}, indent=2))
        return 1 if violations else 0

    for v in violations:
        print(f"{v['file']}: {v['reason']}", file=sys.stderr)
    if unexercised:
        modules = sorted({u["module"] for u in unexercised})
        print(f"\nnote: {len(unexercised)} script(s) not exercised — they exit nonzero on "
              f"an uncaught import error, so their guard was never run. "
              f"Missing module(s): {', '.join(modules)}. Install the dependency to check "
              f"them, or run this verifier with an interpreter that has it.", file=sys.stderr)
        for u in unexercised:
            print(f"  ? {u['file']} (import {u['module']})", file=sys.stderr)
    if violations:
        print(f"\n{len(violations)} script guard violation(s).", file=sys.stderr)
        if stopped:
            print("stopped early: enough violations to fail the check.", file=sys.stderr)
        return 1
    tail = (f"; {len(unexercised)} not exercised (missing: "
            f"{', '.join(sorted({u['module'] for u in unexercised}))})"
            if unexercised else "")
    print(f"{examined} script(s) run with no arguments, "
          f"0 zero-argument guard violation(s){tail}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
