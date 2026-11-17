#!/usr/bin/env python3
"""verify-commands.py — Check every CLI invocation in the skills against the
ground-truth command registry (scripts/command-registry.json).

Catches the "hallucinated command" bug class: `toolforge tools create`,
`toolforge env set`, `toolforge db list`, etc. — commands that look plausible
but do not exist in the real CLI. The registry is generated from live `--help`
output on the Toolforge bastion (scripts/refresh-command-registry.py), so this
also catches CLI drift whenever the registry is refreshed.

Usage:
    python3 scripts/verify-commands.py
    python3 scripts/verify-commands.py --json          # machine-readable output
    python3 scripts/verify-commands.py --max-age-days 0   # disable staleness warning

Exit codes: 0 = clean, 1 = command violations found.

Scope: verifies invocations of binaries listed in the registry (toolforge,
webservice, sql, become). Prose that *documents* removed commands is skipped
when the surrounding line is a removal/error context (e.g. "the `toolforge
tools` family was removed", "Error: No such command").
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_REGISTRY = SCRIPT_DIR / "command-registry.json"
DEFAULT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Binaries the verifier knows about; invocations of anything else are ignored.
# Extend here + in the registry when new tooling is documented.
# `mw` is the official Wikimedia CLI; its registry entry is curated from the
# published manual rather than introspected (see MANUAL_BINARIES in
# refresh-command-registry.py), so a documented `mw <verb>` is still checked.
BINARIES = ("mw", "toolforge", "webservice", "sql", "become", "pwb.py")

BIN_RE = re.compile(r"\b(" + "|".join(BINARIES) + r")\s+([a-z][a-z0-9_-]*)")

# Lines in these contexts document *removals/failures*, not instructions.
REMOVAL_CONTEXT = re.compile(
    r"\b(removed|removal|no longer|does not exist|doesn't exist|"
    r"no CLI equivalent|no cli path|not available)\b",
    re.I,
)
ERROR_CONTEXT = re.compile(
    r"\b(Error:|No such command|command not found|unknown command|not found)\b",
    re.I,
)


def load_registry(path: Path) -> dict:
    return json.loads(path.read_text())


def registry_age_days(registry: dict) -> int | None:
    try:
        ts = datetime.strptime(registry["generated_at"], "%Y-%m-%dT%H:%M:%SZ")
    except (KeyError, ValueError):
        return None
    return (datetime.now(timezone.utc) - ts.replace(tzinfo=timezone.utc)).days


def scan_file(path: Path, registry: dict) -> list[dict]:
    """Return violations: [{file, line, command, reason}]."""
    violations = []
    lines = path.read_text().splitlines()
    n = len(lines)

    # ctx_skip[i]: line i documents a removal/failure rather than instructing.
    # A +-1-line window around any marker line covers wrapped prose ("the
    # `toolforge tools...` family was\nremoved from the CLI"), and whole
    # blockquote blocks are marked when any line inside carries a marker
    # (e.g. the "Removed in CLI 0.3.x" table in toolforge-cli.md).
    marker = lambda s: bool(REMOVAL_CONTEXT.search(s) or ERROR_CONTEXT.search(s))
    ctx_skip = [False] * n
    for i, line in enumerate(lines):
        if marker(line):
            for j in (i - 1, i, i + 1):
                if 0 <= j < n:
                    ctx_skip[j] = True
    i = 0
    while i < n:
        if lines[i].lstrip().startswith(">"):
            j = i
            while j < n and lines[j].lstrip().startswith(">"):
                j += 1
            if any(marker(l) for l in lines[i:j]):
                for k in range(i, j):
                    ctx_skip[k] = True
            i = j
        else:
            i += 1

    in_fence = False
    for i, line in enumerate(lines):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if ctx_skip[i]:
            continue
        if not in_fence:
            # Inline code spans only (outside fences).
            for m in re.finditer(r"`([^`]+)`", line):
                check_invocation(m.group(1), path, i + 1, violations, registry)
        else:
            # Whole fenced line is an instruction context.
            check_invocation(line, path, i + 1, violations, registry)

    return violations


def check_invocation(text: str, path: Path, lineno: int,
                     violations: list, registry: dict) -> None:
    binaries = registry["binaries"]
    for m in BIN_RE.finditer(text):
        binary, t1 = m.group(1), m.group(2)
        # second token (sub-subcommand), if any
        rest = text[m.end():]
        t2m = re.match(r"\s+([a-z][a-z-]*)", rest)
        t2 = t2m.group(1) if t2m else None

        cmd = f"{binary} {t1}" + (f" {t2}" if t2 else "")

        bin_cfg = binaries.get(binary)
        if bin_cfg is None:
            violations.append({"file": str(path), "line": lineno,
                               "command": binary,
                               "reason": "unknown binary (not in registry)"})
            continue
        if not bin_cfg.get("subcommands"):
            continue  # positional-args binary (webservice/sql/become)

        if t1.startswith("-"):
            continue
        if t1 not in bin_cfg["subcommands"]:
            violations.append({"file": str(path), "line": lineno, "command": cmd,
                               "reason": f"unknown subcommand of {binary} "
                                         f"(registry: {', '.join(bin_cfg['subcommands'])})"})
            continue

        sub_kids = bin_cfg.get("sub", {}).get(t1, [])
        if t2 and not t2.startswith("-") and sub_kids and t2 not in sub_kids:
            violations.append({"file": str(path), "line": lineno, "command": cmd,
                               "reason": f"unknown sub-subcommand of {binary} {t1} "
                                         f"(registry: {', '.join(sub_kids)})"})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--max-age-days", type=int, default=120,
                    help="warn when registry is older than N days (0 = disable)")
    args = ap.parse_args(argv)

    registry = load_registry(args.registry)
    age = registry_age_days(registry)
    if args.max_age_days and age is not None and age > args.max_age_days:
        print(f"WARNING: command registry is {age} days old — run "
              f"scripts/refresh-command-registry.py to re-verify the CLI "
              f"surface (last: {registry['generated_at']})", file=sys.stderr)

    all_violations = []
    md_files = sorted(args.skills_dir.rglob("*.md"))
    for md in md_files:
        all_violations.extend(scan_file(md, registry))

    if args.json:
        print(json.dumps(all_violations, indent=2))
    else:
        for v in all_violations:
            print(f"  x {v['file']}:{v['line']}  {v['command']}  ({v['reason']})")
        print(f"\n{len(md_files)} skill files scanned, {len(all_violations)} violation(s) found.")

    return 1 if all_violations else 0


if __name__ == "__main__":
    sys.exit(main())
