#!/usr/bin/env python3
"""refresh-command-registry.py — Capture the live Toolforge CLI surface into the
command ground-truth registry used by scripts/verify-commands.py.

This is the "manual testing" step, reduced to one command. Run it whenever the
Toolforge CLI might have changed (new toolforge-* binaries, subcommand renames)
or at least every few months. It SSHs to the bastion and records `--help`
output for the `toolforge` dispatcher and every sub-CLI, plus the pywikibot
script list from the official docs (pwb.py is not installed on the bastion).

Usage:
    python3 scripts/refresh-command-registry.py
    TOOLFORGE_USER=alih python3 scripts/refresh-command-registry.py
    TOOLFORGE_BASTION=alih@login.toolforge.org python3 scripts/refresh-command-registry.py

Writes: scripts/command-registry.json
Output is deterministic (sorted) so diffs are reviewable.
"""

import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
OUT = SCRIPT_DIR / "command-registry.json"

bastion = os.environ.get("TOOLFORGE_BASTION") or (
    f"{os.environ.get('TOOLFORGE_USER') or os.environ.get('USER', '')}@login.toolforge.org"
)

# Binaries that exist on the bastion but take positional args (no subcommands).
# Included for existence verification only.
STANDALONE_BINARIES = ("webservice", "sql", "become")

# Binaries documented from their published manual rather than introspected.
# `mw` (the official Wikimedia CLI, https://a-wikimedia-cli.toolforge.org/) is a
# ~136 MB per-machine download, so it is not installed or introspected here. This
# tree is the documented surface at the pinned version: extend it in the same PR
# that starts documenting a new `mw` path, otherwise verify-commands.py rejects
# that path as an unknown subcommand (which is the point — it catches typos and
# invented verbs). Empty child lists mean "children not enumerated; do not check".
MANUAL_BINARIES = {
    "mw": {
        "version": "0.36.0 (published manual, not introspected)",
        "subcommands": [
            "analytics", "api", "cloudvps", "codesearch", "completion", "config",
            "dev", "enterprise", "events", "gerrit", "gitlab", "help",
            "phabricator", "toolforge", "tools", "update", "version", "wiki",
        ],
        "sub": {
            "analytics": [
                "devices", "editors", "edits", "mediarequests", "new-pages",
                "pageviews", "top-edited", "top-pages",
            ],
            "config": ["get", "profiles", "secrets", "set", "show", "where"],
            "codesearch": ["search"],
            "dev": ["compose", "destroy", "env", "restart", "start", "stop", "update"],
            "enterprise": [
                "api", "articles", "auth", "batches", "codes", "languages",
                "namespaces", "projects",
            ],
            "events": ["info", "list", "tail"],
            "toolforge": [
                "build", "components", "cp", "create", "envvar", "job",
                "kubernetes", "replicas", "shell", "toolsdb",
            ],
            "tools": ["quip", "toolcounter", "toolviews"],
            "wiki": ["api", "auth", "bulk", "ext", "file", "page", "realm", "rest"],
        },
    }
}

# pwb.py is not on the bastion; its script list comes from the pywikibot
# source repo (authoritative filenames) with the docs index as fallback.
PYWIKIBOT_DOCS = "https://doc.wikimedia.org/pywikibot/stable/scripts/index.html"
PYWIKIBOT_GH = "https://api.github.com/repos/wikimedia/pywikibot/contents/scripts"


def ssh(cmd: str) -> str:
    """Run a command on the bastion; return stdout+stderr."""
    r = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", bastion, cmd],
        capture_output=True, text=True, timeout=60,
    )
    return r.stdout + r.stderr


def parse_commands(help_text: str) -> list[str]:
    """Extract subcommand tokens from CLI help.

    Handles both click-style ('Commands:' section) and argparse-style
    (usage line with {sub1,sub2,...}) help output.
    """
    tokens = []

    # argparse style: Usage: toolforge jobs [-h] {images,run,...}...
    for line in help_text.splitlines():
        m = re.search(r"\{([a-z][a-z-,]*)\}\s*\.\.\.", line)
        if m:
            tokens.extend(t for t in m.group(1).split(",") if re.fullmatch(r"[a-z][a-z-]*", t))

    # click style: a 'Commands:' section with indented entries
    in_cmds = False
    for line in help_text.splitlines():
        if line.startswith("Commands:"):
            in_cmds = True
            continue
        if in_cmds:
            if line.startswith("  ") and line.strip():
                tok = line.strip().split()[0]
                if re.fullmatch(r"[a-z][a-z-]*", tok):
                    tokens.append(tok)
            elif line and not line.startswith("  "):
                break
    return sorted(set(tokens))


def get_version(binary: str) -> str:
    out = ssh(f"{binary} --version 2>&1")
    return out.strip().splitlines()[0][:80] if out.strip() else ""


def get_pywikibot_scripts() -> list[str]:
    """Scrape the official docs page for pwb.py script names.

    The docs index lists the bot scripts but not the core helper scripts
    (login, shell, version), which live in pywikibot/scripts/ and are invoked
    the same way — add those explicitly.
    """
    ua = ("wikipedia-ai-skills-command-registry/1.0 "
          "(https://github.com/fuzheado/Wikipedia-AI-Skills)")
    names = []
    try:
        req = Request(PYWIKIBOT_GH, headers={"User-Agent": ua})
        with urlopen(req, timeout=30) as resp:
            files = json.loads(resp.read().decode("utf-8", "replace"))
        names = [f["name"][:-3] for f in files if f.get("name", "").endswith(".py")]
        print(f"  pywikibot: {len(names)} scripts from GitHub repo", file=sys.stderr)
    except Exception as e:
        print(f"  GitHub fetch failed ({e}); falling back to docs", file=sys.stderr)
        req = Request(PYWIKIBOT_DOCS, headers={"User-Agent": ua})
        with urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
        names = [n[:-3] for n in sorted(set(re.findall(r">([a-z][a-z0-9_-]+\.py)<", html)))]
    # core helper scripts invoked via pwb.py but not bot scripts
    names.extend(["login", "shell", "version", "generate_user_files",
                  "generate_family_file", "wrapper"])
    return sorted(set(names))


def main() -> int:
    print(f"Capturing Toolforge CLI surface from {bastion} ...", file=sys.stderr)

    tf_version = get_version("toolforge")
    tf_help = ssh("toolforge --help")
    tf_commands = parse_commands(tf_help)
    if not tf_commands:
        print(f"ERROR: could not capture 'toolforge --help' from {bastion}. "
              f"Is SSH access configured?", file=sys.stderr)
        return 1

    sub = {}
    for sub_name in tf_commands:
        sub[sub_name] = parse_commands(ssh(f"toolforge {sub_name} --help 2>&1"))

    pwb_scripts = get_pywikibot_scripts()
    print(f"  pywikibot: {len(pwb_scripts)} scripts from {PYWIKIBOT_DOCS}", file=sys.stderr)

    registry = {
        "schema_version": 1,
        "generator": "scripts/refresh-command-registry.py",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": f"ssh {bastion} + {PYWIKIBOT_DOCS}",
        "note": ("Ground-truth command surface. Do not edit by hand; regenerate "
                 "with scripts/refresh-command-registry.py. The `mw` entry comes "
                 "from its published manual (MANUAL_BINARIES), not introspection."),
        "binaries": {
            "toolforge": {
                "version": tf_version,
                "subcommands": tf_commands,
                "sub": sub,
            },
            "pwb.py": {
                "version": "pywikibot (script list from official docs)",
                "subcommands": pwb_scripts,
                "sub": {},
            },
        },
    }
    for name in STANDALONE_BINARIES:
        registry["binaries"][name] = {"version": get_version(name), "subcommands": []}

    registry["binaries"].update(MANUAL_BINARIES)

    OUT.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")

    print(f"Registry written to {OUT}", file=sys.stderr)
    print(f"  toolforge: {tf_version}", file=sys.stderr)
    for sub_name in tf_commands:
        kids = ", ".join(sub[sub_name]) or "(positional args only)"
        print(f"    {sub_name}: {kids}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
