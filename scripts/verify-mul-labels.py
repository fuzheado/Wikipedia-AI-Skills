#!/usr/bin/env python3
"""verify-mul-labels.py — Enforce the `mul` (multiple languages) default-value rule.

Wikidata stores language-independent labels and aliases as *default values*
under the language code `mul` ("multiple languages") — see
https://www.wikidata.org/wiki/Help:Default_values_for_labels_and_aliases.
A label request that asks for a reader language plus `en` does **not** receive
them, and the failure is silent: the caller renders the bare QID ("Q7186")
where a reader expects "Marie Curie". Documented in the wikidata skill
("Getting Labels: `mul` Is Not Optional", measured 2026-09-14).

Three offline checks (no network):

  1. SPARQL label service — every `wikibase:language "..."` list must contain
     `mul`. The label service does not fall back to defaults on its own: a
     query with only "en" returns the QID as the label.
  2. Pinned label readers — shipped scripts that read Wikidata/Wikibase terms
     must reference `mul`, `languagefallback`, or `resolve_fallback()` (the
     three ways to resolve defaults), so no reader silently reads a single
     language and prints "(no label)" for a mul-only entity.
  3. Multi-language requests — a piped `languages=` value (dict form
     `"languages": "en|fr"` or URL form `&languages=en|fr`) must contain `mul`.
     A multi-language label fetch that omits defaults is incomplete.

Escape hatch: append the marker `verify-mul-labels: allow` to a line that
deliberately shows the wrong form (e.g. the negative example in the wikidata
skill's comparison table). Marked lines are counted and reported, so the
escape hatch cannot hide silently.

Usage:
    python3 scripts/verify-mul-labels.py
    python3 scripts/verify-mul-labels.py --skills-dir .claude/skills

Exit codes: 0 = clean, 1 = violations found.
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

ALLOW_MARKER = "verify-mul-labels: allow"

# Rule 2: shipped term readers. Every entry must mention one of MUL_TOKENS.
# Keep this list to files that actually fetch labels/aliases/captions — it is a
# regression pin for known-good readers, not a general "must use mul" rule.
LABEL_READERS = {
    "wikidata/scripts/wikidata-lookup.sh":
        "core skill's QID lookup tool (props=labels|descriptions|aliases)",
    "wikidata/assets/wikidata-entity-fetcher.py":
        "core skill's entity/inspector tool (props=labels)",
    "wikimedia-i18n-l10n-for-tools/scripts/fetch-multilingual-labels.sh":
        "batch label fetch CLI",
    "wikimedia-i18n-l10n-for-tools/assets/wikidata_labels.py":
        "batch label fetch library",
    "wikidata-reconciliation/scripts/reconcile.py":
        "QID verification guardrail (label match check)",
}
MUL_TOKENS = ("mul", "languagefallback", "resolve_fallback")

SERVICE_RE = re.compile(r'wikibase:language\s*"([^"]*)"')
# "languages": "en|fr", languages='en|fr', languages=en|fr (inside a mapping/params dict)
PIPED_DICT_RE = re.compile(r"""languages["']?\s*[:=]\s*["']([^"']*\|[^"']*)["']""")
# ...?languages=en|fr and ...&languages=en|fr (query-string form)
PIPED_URL_RE = re.compile(r"[?&]languages=([^\s\"'&#]*\|[^\s\"'&#]*)")

SCAN_SUFFIXES = {".md", ".py", ".sh", ".json"}
SKIP_DIR_NAMES = {"__pycache__", ".git", "node_modules"}


def _iter_files(skills_dir: Path):
    for path in sorted(skills_dir.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        yield path


def _split_mul(raw: str):
    r"""Return (tokens, matched) for a piped/space language list.

    Normalizes markdown escapes and quoting: the skills write the same value
    as `languages=en\|mul` (table cell), "en|mul" (JSON), `{lang}|mul|en`
    (template).
    """
    cleaned = raw.replace("\\|", "|").replace("`", "").replace('"', "").replace("'", "")
    return [tok.strip() for tok in re.split(r"[|,]", cleaned) if tok.strip()]


def scan_file(path: Path, skills_dir: Path) -> tuple[list[str], list[str]]:
    """Return (violations, allow_marked) for one skill file."""
    rel = path.relative_to(skills_dir)
    violations: list[str] = []
    allow_marked: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return violations, allow_marked

    for lineno, line in enumerate(text.splitlines(), start=1):
        decoded = unquote(line)  # URL-encoded SPARQL in shell scripts
        marker = ALLOW_MARKER in line
        if marker:
            allow_marked.append(f"{rel}:{lineno}")

        for raw in SERVICE_RE.findall(decoded):
            tokens = _split_mul(raw)
            if "mul" in tokens:
                continue
            if marker:
                continue
            violations.append(
                f"{rel}:{lineno}: SPARQL label service without mul — "
                f'wikibase:language "{raw}" renders QIDs for mul-only items; '
                f'use "[AUTO_LANGUAGE],mul,en"'
            )

        for pattern in (PIPED_DICT_RE, PIPED_URL_RE):
            for raw in pattern.findall(line):
                # Skip code like `"|".join(langs)` — a separator literal, not a list.
                if not any(ch.isalnum() for ch in raw):
                    continue
                tokens = _split_mul(raw)
                if "mul" in tokens or marker:
                    continue
                violations.append(
                    f"{rel}:{lineno}: multi-language label request without mul — "
                    f'languages="{raw}" drops default values; add mul '
                    f'(or use languagefallback=1)'
                )

    return violations, allow_marked


def scan_label_readers(skills_dir: Path) -> list[str]:
    """Rule 2: pinned readers must reference a default-value resolution path."""
    problems: list[str] = []
    for rel, why in sorted(LABEL_READERS.items()):
        path = skills_dir / rel
        if not path.exists():
            problems.append(f"{rel}: pinned label reader is missing ({why})")
            continue
        text = path.read_text(encoding="utf-8")
        if not any(token in text for token in MUL_TOKENS):
            problems.append(
                f"{rel}: label reader references none of {MUL_TOKENS} — "
                f"{why}; it will report mul-only entities as label-less "
                f"(add `<lang>|mul` + a mul fallback, languagefallback=1, or "
                f"resolve_fallback())"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR,
                    help="skills directory to scan (default: .claude/skills)")
    args = ap.parse_args(argv)

    if not args.skills_dir.is_dir():
        print(f"error: no such skills directory: {args.skills_dir}", file=sys.stderr)
        return 1

    files = list(_iter_files(args.skills_dir))
    problems: list[str] = []
    marked: list[str] = []
    for path in files:
        file_problems, file_marked = scan_file(path, args.skills_dir)
        problems.extend(file_problems)
        marked.extend(file_marked)
    problems.extend(scan_label_readers(args.skills_dir))

    for p in problems:
        print(f"  x {p}")
    for m in marked:
        print(f"  (allow) {m} carries the '{ALLOW_MARKER}' marker")
    print(f"\n{len(files)} files scanned, {len(problems)} mul default-value "
          f"violation(s), {len(marked)} allow-marked line(s).")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
