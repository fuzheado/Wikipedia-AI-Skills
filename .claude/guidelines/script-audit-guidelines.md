# Script Audit & Compatibility Guidelines

Guidelines for auditing and maintaining shell scripts (`.sh`) and Python scripts (`.py`) across the Wikipedia-AI-Skills repository. The goal: scripts that are **descriptive, safe, portable, and gracefully handle invocation with no arguments**.

---

## 1. Zero-Argument Handling (Every Script Must Have This)

**Shell scripts:** Always include an explicit zero-argument guard near the top, before any processing:

```bash
if [ $# -eq 0 ]; then
    echo "Usage: $(basename "$0") <required-arg> [optional-arg]" >&2
    echo "" >&2
    echo "  Describe what this script does." >&2
    echo "  required-arg  What it is" >&2
    echo "  optional-arg  What it is (default: X)" >&2
    echo "" >&2
    echo "Examples:" >&2
    echo "  $(basename "$0") value" >&2
    echo "  $(basename "$0") value --flag" >&2
    exit 1
fi
```

**Counterexample (bad):** Using `"${1:-default}"` without a guard — the script silently proceeds with defaults, leaving the user confused about what happened.

**Exception:** Scripts where *all* arguments have sensible defaults and the script does something useful without args (e.g. a test/demo script). In that case, still print a hint to stderr about how to customize.

**Python scripts:** When all argparse arguments have `default=` values, argparse does **not** print help on bare invocation. Add this guard:

```python
import sys
# ... after creating parser ...
if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)
```

**Exception:** Interactive scripts that prompt the user when no CLI args are given (e.g., `citation_generator.py`). For those, document the interactive mode clearly.

### Current audit status

| Script | Zero-args guard | Status |
|---|---|---|
| `scripts/check-status.sh` | ✅ Yes | Pass |
| `scripts/list-unreviewed.sh` | ✅ Yes (fixed) | Pass |
| `assets/patrol_simulator.py` | ✅ Yes (fixed) | Pass |
| `scripts/test-api.sh` | ✅ Defaults + descriptive header | Pass |
| `scripts/assess-project.sh` | ✅ Yes | Pass |
| `scripts/quality-gaps.sh` | ✅ Yes | Pass |
| `scripts/validate-templatestyles.sh` | ✅ Yes (via `--help` + validation) | Pass |
| `scripts/fetch-templatestyles.sh` | ✅ Yes | Pass |
| `scripts/per-article.sh` | ✅ Yes | Pass |
| `scripts/compare-revisions.sh` | ✅ Yes | Pass |
| `scripts/page-summary.sh` | ✅ Yes | Pass |
| `scripts/extract-infobox.sh` | ✅ Yes | Pass |
| `scripts/expand-navigation.sh` | ✅ Yes | Pass |
| `scripts/navigation-inspector.sh` | ✅ Yes | Pass |
| `scripts/get-assessment.sh` | ✅ Yes | Pass |
| `scripts/template-usage.sh` | ✅ Yes | Pass |
| `scripts/batch-ref-audit.sh` | ✅ Yes (fixed) | Pass |
| `scripts/04-generate-taskgraph.py` | ✅ Yes (fixed) | Pass |
| `scripts/validate.py` | ✅ Yes (fixed) | Pass |
| `scripts/01-diagnose.py` | ✅ Yes | Pass |
| All other Python assets | Mixed — see §5 | — |

---

## 2. Bash Version Portability (macOS default is bash 3.2)

macOS ships bash 3.2 as `/bin/bash`. `#!/usr/bin/env bash` resolves to this on macOS unless the user has installed a newer bash via Homebrew. Features to **avoid**:

| Feature | Problem | Portable replacement |
|---|---|---|
| `declare -A` (associative arrays) | bash 4+ only | `case "$key" in val) ... ;; esac` |
| `[[ $var =~ regex ]]` capture groups with `BASH_REMATCH` | Works on 3.2 but indexing differs on old bash | `grep` + `sed` or Python one-liner |
| `${var,,}` / `${var^^}` (case change) | bash 4+ only | `tr '[:upper:]' '[:lower:]'` or Python |
| `printf -v var` | bash 4+ only | `var=$(printf ...)` |
| `mapfile` / `readarray` | bash 4+ only | `while IFS= read -r line; do ... done` |
| `**` globstar | Needs `shopt -s globstar` (bash 4+) | `find` command |
| `<<<` here-strings | bash 3.2 actually *supports* this | ✅ OK, but test |
| `declare -n` (namerefs) | bash 4+ only | Use explicit variable names |

**Best practice:** If you need bash 4+ features, add an explicit version check:

```bash
if [ "${BASH_VERSINFO:-0}" -lt 4 ]; then
    echo "Error: This script requires bash 4+. Current: ${BASH_VERSION}" >&2
    echo "On macOS: brew install bash" >&2
    exit 1
fi
```

Otherwise, prefer POSIX sh syntax where practical, or delegate complex logic to Python.

---

## 3. Portability Beyond macOS (Windows/Linux)

### Shebang lines

| Target | Shebang |
|---|---|
| Shell scripts | `#!/usr/bin/env bash` (portable across Unix-like systems) |
| Python scripts (CLI) | `#!/usr/bin/env python3` |
| Python library modules | No shebang needed — omit it |

### What breaks on Windows (Git Bash / WSL)

- `mktemp` — available on Git Bash, but temp dir patterns may need adjustment
- `nc` (netcat) — not available on Git Bash; use `timeout` or Python instead
- `date -v-3d` (macOS syntax) vs `date -d '3 days ago'` (GNU syntax) — use both with fallback

**Portable date arithmetic pattern:**

```bash
DATE=$(date -v-30d +%Y%m%d 2>/dev/null || date -d '30 days ago' +%Y%m%d 2>/dev/null || echo "")
```

### File system

- Avoid pathnames with colons, trailing spaces, or other Windows-reserved characters
- Use `/tmp` for temp files (Git Bash maps this to `%TMP%`)
- Test with both forward slashes (Unix) and handle backslash conversion if the script takes file paths as arguments

---

## 4. Usage Message Best Practices

Every usage string should answer three questions:

1. **What does it do?** — One-line description
2. **What arguments does it take?** — Listed with types/defaults
3. **Show examples** — 1–3 realistic invocations

### Shell script pattern

```bash
if [ $# -eq 0 ] || [ "$1" = "--help" ]; then
    echo "Usage: $(basename "$0") <article> [limit]" >&2
    echo "" >&2
    echo "Fetch assessment data for a WikiProject." >&2
    echo "" >&2
    echo "Arguments:" >&2
    echo "  article  Article title (required)" >&2
    echo "  limit    Max results (default: 50)" >&2
    echo "" >&2
    echo "Examples:" >&2
    echo "  $(basename "$0") Albert_Einstein" >&2
    echo "  $(basename "$0") Python_(language) 100 --json" >&2
    exit 0
fi
```

For complex scripts with many options, the `validate-templatestyles.sh` pattern of a dedicated `show_help()` function with a full `cat <<EOF` block is recommended.

---

## 5. Python CLI Audit Summary

| Python script | Has `__main__`? | Required args | No-args behavior | Status |
|---|---|---|---|---|
| `assets/citation_generator.py` | ✅ Yes | None (interactive) | Interactive prompt | ✅ Good |
| `assets/dead_link_scanner.py` | ✅ Yes | `page_title` | `argparse` prints error | ✅ Good |
| `assets/citation_linter.py` | ✅ Yes | `page_title` | `argparse` prints error | ✅ Good |
| `assets/citoid_fetcher.py` | ✅ Yes | `input` | `argparse` prints error | ✅ Good |
| `assets/wayback_inspector.py` | ✅ Yes | `target` | `argparse` prints error | ✅ Good |
| `assets/user-agent-template.py` | ✅ Yes | None | Runs demo | ✅ Intentional |
| `assets/analysis-template.py` | ✅ Yes | `article` | `parser.print_help()` | ✅ Good |
| `assets/category-inspector.py` | ✅ Yes | `title` | `parser.print_help()` | ✅ Good |
| `assets/commons-file-inspector.py` | ✅ Yes | `query` | `argparse` prints error | ✅ Good |
| `assets/patrol_simulator.py` | ✅ Yes | None (fixed) | Shows help now | ✅ Fixed |
| `assets/talk-archive-search.py` | ✅ Yes | `title`, `keyword` | `argparse` prints error | ✅ Good |
| `assets/history-audit.py` | ✅ Yes | `title` | `argparse` prints error | ✅ Good |
| `assets/page-audit.py` | ✅ Yes | `title` | `argparse` prints error | ✅ Good |
| `assets/wikitext_utils.py` | ✅ Yes | `command`, `title` | `argparse` prints error | ✅ Good |
| `assets/navigation_analyzer.py` | ✅ Yes | `title` | `argparse` prints error | ✅ Good |
| `assets/templatestyles_inspector.py` | ✅ Yes | `title` | `argparse` prints error | ✅ Good |
| `assets/grid_layout_preview.py` | ✅ No default | None | Shows help (fixed) | ✅ Fixed |
| `assets/translation_checker.py` | ✅ Yes | `title` | `argparse` prints error | ✅ Good |
| `assets/template_translation_scanner.py` | ✅ Yes | `template` or `--project` | Early validation (fixed) | ✅ Fixed |
| `assets/wikidata-entity-fetcher.py` | ✅ Yes | `query` | `parser.print_help()` | ✅ Good |
| `assets/liftwing_multi_model.py` | ✅ Yes | `title` | `argparse` prints error | ✅ Good |
| `assets/patrol_simulator.py` (ML) | ✅ Yes | None needed | `parser.print_help()` | ✅ Good |
| `assets/article_quality_report.py` | ✅ Yes | `title` or `--rev-id` | `argparse` prints error | ✅ Good |
| `assets/eventstreams-consumer.py` | ✅ Yes | None | Shows help (fixed) | ✅ Fixed |
| `assets/template-inspector.py` | ✅ Yes | `title` | `argparse` prints error | ✅ Good |
| `scripts/04-generate-taskgraph.py` | ✅ Yes | `--project-dir` | Shows help (fixed) | ✅ Fixed |
| `scripts/01-diagnose.py` | ✅ Yes | `title` | Manual check ✅ | ✅ Good |
| `scripts/validate.py` | ✅ Yes | `graph_path` (optional) | Shows help if default not found (fixed) | ✅ Fixed |

**All previously flagged scripts have been fixed. ✅** No scripts currently fail the audit.

---

## 6. Additional Compatibility Recommendations

### Error messages to stderr

All error messages, diagnostic info, and progress messages should go to **stderr** (`>&2`). Only the script's primary output (data results) should go to **stdout** — this allows piping output to other commands.

### Shell script idioms

- Use `set -euo pipefail` at the top of every bash script
- Use `trap 'rm -f "$TMPFILE"' EXIT` for temp file cleanup
- Prefer `$(...)` over backticks for command substitution
- Quote all variable expansions: `"$var"` not `$var`
- Use `printf` instead of `echo` for consistent behavior with special characters
- For user-facing color codes, use `tput` instead of raw ANSI escape sequences for better cross-terminal compatibility:

```bash
RED=$(tput setaf 1 2>/dev/null || printf '\033[0;31m')
NC=$(tput sgr0 2>/dev/null || printf '\033[0m')
```

### Python script idioms

- Use `argparse.ArgumentParser` (not `optparse` or manual `sys.argv`)
- Always set `description=` on the parser
- For file paths, use `pathlib.Path` instead of `os.path`
- Import `__future__` annotations for type hints
- Catch specific exceptions, not bare `except:`
- Rate-limit API calls with `time.sleep()` between requests
- Support `--json` flag for machine-readable output alongside human-readable text output

### Cross-platform Python

- Use `os.name` or `platform.system()` only when necessary (e.g., Windows tempdir differences)
- `urllib.request` works everywhere; `requests` library requires `pip install`
- For date arithmetic, prefer `datetime` from stdlib over shell `date` hacks

### Temp file management

- Shell: `mktemp` with cleanup via `trap`
- Python: `tempfile.NamedTemporaryFile` or `tempfile.mkdtemp`
- Always clean up — leaked temp files are a security issue

---

## 7. Checklist for New Scripts

- [ ] `set -euo pipefail` (shell) or `argparse` (Python)
- [ ] Zero-argument guard shows usage and exits nonzero
- [ ] `--help` shows comprehensive usage
- [ ] Shebang is `#!/usr/bin/env bash` or `#!/usr/bin/env python3`
- [ ] No bash 4+ features unless explicitly checked
- [ ] All errors go to stderr
- [ ] Temp files cleaned up via `trap`/`try-finally`
- [ ] Example invocations included in comments or `--help`
- [ ] Rate limiting for API calls
- [ ] Proper `User-Agent` header (per Wikimedia policy)
- [ ] Link to relevant skill's SKILL.md in script header comments

---

## 8. Preventing Compliance Drift: CI & Process Integration

### Option A: Ad-hoc check (recommended first step)

Before merging any PR that adds or modifies scripts, run the audit checklist:

```bash
# Quick scan for new scripts in a branch
git diff --name-only main | grep -E '\.(sh|py)$' | while read f; do
    echo "=== $f ==="
    head -3 "$f"
done
```

The reviewer should check the §7 checklist for every new or modified script.

### Option B: ~~SKILL.md manifest~~ (use `# Scripts` section instead)

Each SKILL.md can include a `## Scripts` section that documents every script
in the skill and its invocation pattern. This is already standard practice for
most skills in this repo. When adding a new script, get into the habit of:

1. Adding the script file
2. Updating the skill's SKILL.md `## Scripts` section with the usage example

Example SKILL.md `## Scripts` entry:

```markdown
## Scripts

### `scripts/my-tool.sh`

Audit recently-created pages.

Usage:
  ./scripts/my-tool.sh --days 3 --limit 50
```

### Option C: Git hook (manual enforcement)

A pre-commit hook can catch the most obvious violations:

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit — checks for script compliance

violations=0

while IFS= read -r file; do
    # Check shell scripts for zero-arg guard
    if [[ "$file" == *.sh ]]; then
        if ! grep -qE 'if \[ \$# -eq 0 \]' "$file" && ! grep -qE '--help\)|show_help|usage\(\)' "$file"; then
            echo "⚠️  Missing zero-arg guard: $file"
            ((violations++))
        fi
        if grep -q 'declare -A' "$file"; then
            echo "⚠️  Uses bash 4+ 'declare -A': $file"
            ((violations++))
        fi
    fi
    # Check Python CLI scripts for argparse and no-arg guard
    if [[ "$file" == *.py ]] && grep -q 'if __name__ == "__main__"' "$file"; then
        if ! grep -q 'ArgumentParser' "$file"; then
            echo "⚠️  CLI script missing argparse: $file"
            ((violations++))
        fi
        if grep -q "parser\.parse_args\(\)" "$file" && ! grep -qE "len\(sys\.argv\) == 1|parser\.print_help" "$file"; then
            # Only flag if ALL args have defaults
            if ! grep -qE 'add_argument\("[^"-]' "$file"; then
                echo "⚠️  Missing no-arg guard (all args have defaults): $file"
                ((violations++))
            fi
        fi
    fi
done < <(git diff --cached --name-only --diff-filter=ACM)

if (( violations > 0 )); then
    echo "❌ $violations compliance violation(s) found. See guidelines/script-audit-guidelines.md"
    exit 1
fi
```

Install with:
```bash
cp .git/hooks/pre-commit.sample .git/hooks/pre-commit
# (then paste the script above)
chmod +x .git/hooks/pre-commit
```

### Option D: GitHub Actions CI (automated enforcement)

A CI workflow can validate every PR. Create `.github/workflows/script-audit.yml`:

```yaml
name: Script Compliance Audit
on: [pull_request, push]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Check scripts for zero-arg guards
        run: |
          violations=0
          git diff --name-only HEAD~1 | grep '\.sh$' | while read f; do
            if ! grep -qE 'if \[ \$# -eq 0 \]' "$f" 2>/dev/null && \
               ! grep -qE '--help\).*show_help|show_help\(\)|usage\(\)' "$f" 2>/dev/null; then
              echo "::warning file=$f::Missing zero-arg guard"
              ((violations++))
            fi
          done
          # ... similar checks for Python, bash 4+ features ...
          exit $violations
```

### Recommended approach

| Stage | Action | Who |
|---|---|---|
| **Creation** | Follow §7 checklist, document in SKILL.md | Skill author |
| **Code review** | Reviewer runs the quick scan + §7 as review criteria | Reviewer |
| **Periodic** | Run the full audit from these guidelines every 6 months | Maintainer |
| **Automation** | Pre-commit hook (optional) + GitHub Actions CI (ideal) | Maintainer |
