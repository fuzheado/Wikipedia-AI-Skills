#!/usr/bin/env python3
"""verify-sql-live.py — run the repo's SQL assets against the live Toolforge replicas.

Why this is not a CI check: replica access needs Toolforge credentials and an SSH
tunnel, neither of which a GitHub runner has. It exists because the offline
verifiers check URLs, snippet syntax, CLI commands and API names but **never
execute SQL**, so a column or property that no longer exists is invisible until a
human runs a query. That is how `categorylinks.cl_to` (fixed 2026-09-19,
PR #62) and then `pagelinks.pl_title` / `templatelinks.tl_namespace` survived
here, and how the retired `page_props.pageview_daily_average` property kept
returning empty result sets without an error.

Setup (one-time, two tunnels — enwiki is the default target of the assets):

    ssh -N -L 13306:enwiki.analytics.db.svc.wikimedia.cloud:3306 <user>@dev.toolforge.org &
    ssh -N -L 13307:commonswiki.analytics.db.svc.wikimedia.cloud:3306 <user>@dev.toolforge.org &

Then (credentials are the ones from your Toolforge `replica.my.cnf`):

    TOOLFORGE_SQL_USER=u12345 TOOLFORGE_SQL_PASSWORD=... \\
        python3 scripts/verify-sql-live.py

What it does:

  1. Extracts every SQL statement from the skills tree — `*.sql` assets, ```sql
     fences in markdown, and SQL embedded in shell scripts.
  2. Validates each one against the live schema by executing it as a zero-row
     probe (`<stmt> LIMIT 0`, or wrapped in a derived table when it already has a
     top-level LIMIT). No rows are read, but MySQL/MariaDB resolve every table and
     column, so `ERROR 1054 Unknown column` / `ERROR 1146 Table doesn't exist`
     fail the run. A server-side `max_statement_time` caps anything unexpected.
  3. Warns about curated "retired but still parseable" identifiers — a property
     with no rows is a silent wrong answer, not an error.

Without credentials it prints the setup above and exits 0, so it is safe to run
from CI or a pre-push hook. With credentials but no reachable tunnel it exits 1
(you clearly meant to run it).

Usage:
    python3 scripts/verify-sql-live.py
    python3 scripts/verify-sql-live.py --skills-dir .claude/skills
    python3 scripts/verify-sql-live.py --strict-slow

Exit codes: 0 = clean (or skipped for lack of credentials), 1 = violations.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

# Generated eval output is not skill content.
SKIP_PATH_PARTS = ("assessment-workspace", "__pycache__", "node_modules")
SCAN_SUFFIXES = (".sql", ".md", ".sh")

# ``sql`` and ``mysql`` fences only: ```sparql is a different engine.
SQL_FENCE_RE = re.compile(r"^```(sql|mysql)\s*$", re.I)
STATEMENT_START_RE = re.compile(r"^(SELECT|WITH)\b", re.I)
LIMIT_RE = re.compile(r"\bLIMIT\b", re.I)

# Statements whose literals are placeholders cannot be run as-is.
PLACEHOLDER_RE = re.compile(
    r"\{\{|%s|%\(|<\w+>|YOUR_|your_|_goes_here|INSERT_YOUR|ExampleUser|Category_name",
    re.I,
)

# Identifiers that no longer exist on the replicas but whose queries still parse,
# so a schema check alone cannot catch them. Keep the evidence date with each.
RETIRED_IDENTIFIERS = {
    "pageview_daily_average": (
        "retired property: 0 rows on enwiki, commons, dewiki, frwiki, nlwiki and "
        "wikidatawiki (verified 2026-09-20) — queries return empty result sets; "
        "see the wikimedia-pageviews skill"
    ),
}

# Literal substitutions that make documented examples runnable.
LITERAL_FIXES = {
    "'Category_name_goes_here'": "'Physics'",
    "'Category_name'": "'Physics'",
    "'<category>'": "'Physics'",
    "'<your category>'": "'Physics'",
    "'Category:Example'": "'Physics'",
    "{db}_p": "enwiki_p",
}

# Which replica each statement targets. The assets are enwiki-centric; the
# Commons links tables only exist on commonswiki.
COMMONSWIKI_MARKERS = ("commonswiki", "globalimagelinks")


def target_db(sql: str) -> str:
    """Return the replica database a statement should run against."""
    lowered = sql.lower()
    if any(marker in lowered for marker in COMMONSWIKI_MARKERS):
        return "commonswiki_p"
    return "enwiki_p"


def normalise(sql: str) -> str:
    """Apply the documented literal substitutions."""
    out = sql
    for old, new in LITERAL_FIXES.items():
        out = out.replace(old, new)
    return out


def split_statements(text: str):
    """Split a SQL blob on statement-terminating semicolons."""
    return [part for part in re.split(r";\s*\n", text)]


def strip_comments(sql: str) -> str:
    """Drop ``--`` comment lines so a fence can start with a comment block."""
    kept = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    return "\n".join(kept).strip().rstrip(";").strip()


def extract_statements(skills_dir: Path):
    """Yield {file, line, db, sql, first} for every SQL statement in the tree."""
    found = []

    def emit(path: Path, line: int, raw: str, source: str):
        sql = normalise(strip_comments(raw))
        if len(sql) < 15:
            return
        found.append({
            "file": str(path.relative_to(skills_dir)),
            "line": line,
            "source": source,
            "db": target_db(sql),
            "sql": sql,
            "first": " ".join(sql.split())[:90],
        })

    for path in sorted(skills_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in SKIP_PATH_PARTS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")

        if path.suffix.lower() == ".sql":
            line = 1
            for part in split_statements(text):
                emit(path, line, part, "sql-file")
                line += part.count("\n") + 1
            continue

        if path.suffix.lower() == ".md":
            inside = False
            buf, start = [], 0
            for i, raw_line in enumerate(text.splitlines(), 1):
                if SQL_FENCE_RE.match(raw_line.strip()) and not inside:
                    inside, buf, start = True, [], i + 1
                elif inside and raw_line.strip().startswith("```"):
                    line = start
                    for part in split_statements("\n".join(buf)):
                        emit(path, line, part, "md-fence")
                        line += part.count("\n") + 1
                    inside = False
                elif inside:
                    buf.append(raw_line)
            continue

        # shell scripts: SQL echoed into help output or query wrappers
        for i, raw_line in enumerate(text.splitlines(), 1):
            if re.search(r"\b(SELECT|WITH)\b.*\bFROM\b", raw_line, re.I):
                emit(path, i, raw_line.strip(), "shell")

    unique, seen = [], set()
    for item in found:
        key = (item["file"], item["line"], item["sql"][:120])
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _pymysql_connector(host):
    """Return a connector for the replica databases (deferred import)."""
    import pymysql  # deferred: the skip path must not require the driver

    def connector(db, port):
        return pymysql.connect(
            host=host, port=port,
            user=os.environ["TOOLFORGE_SQL_USER"],
            password=os.environ["TOOLFORGE_SQL_PASSWORD"],
            database=db, ssl={"ssl": {}}, connect_timeout=10, read_timeout=60,
        )

    return connector


def probe_sql(sql: str) -> str:
    """Build a zero-row probe for *sql* (LIMIT 0, wrapped if it has its own LIMIT)."""
    if LIMIT_RE.search(sql):
        return f"SELECT * FROM ({sql}) AS audit_q LIMIT 0"
    return f"{sql} LIMIT 0"


def check(skills_dir: Path, ports, host="127.0.0.1", statement_timeout=15,
          strict_slow=False, connect=None, log=print):
    """Validate every statement; return (problems, warnings, counts)."""
    statements = extract_statements(skills_dir)
    problems, warnings, manual = [], [], []

    runnable = []
    for item in statements:
        if not STATEMENT_START_RE.match(item["sql"]) or PLACEHOLDER_RE.search(item["sql"]):
            manual.append(item)
        else:
            runnable.append(item)

    if connect is None:
        connector = _pymysql_connector(host)
    else:
        connector = connect

    connections = {}
    for item in runnable:
        db = item["db"]
        if db in connections:
            continue
        try:
            conn = connector(db, ports[db])
            with conn.cursor() as cur:
                cur.execute(f"SET SESSION max_statement_time={statement_timeout}")
            connections[db] = conn
        except Exception as exc:  # unreachable tunnel / bad credentials
            raise SystemExit(
                f"error: cannot connect to {db} on {host}:{ports[db]} — "
                f"{type(exc).__name__}: {str(exc)[:120]}\n"
                f"       open the tunnels first (see --help)"
            )

    for item in runnable:
        cursor = connections[item["db"]].cursor()
        try:
            cursor.execute(probe_sql(item["sql"]))
            cursor.fetchall()
            for identifier, note in RETIRED_IDENTIFIERS.items():
                if identifier in item["sql"]:
                    warnings.append(f"{item['file']}:{item['line']}: uses {identifier} — {note}")
        except Exception as exc:
            code = exc.args[0] if exc.args else "?"
            message = str(exc.args[1] if len(exc.args) > 1 else exc)[:120]
            if code == 1969:  # max_statement_time exceeded
                text = (f"{item['file']}:{item['line']}: exceeds {statement_timeout}s — "
                        f"valid SQL, unusable at this scale ({item['first'][:60]}...)")
                (problems if strict_slow else warnings).append(text)
            else:
                problems.append(f"{item['file']}:{item['line']}: [{code}] {message}\n"
                                f"      {item['first']}")
        finally:
            cursor.close()

    for conn in connections.values():
        try:
            conn.close()
        except Exception:
            pass

    counts = {"statements": len(statements), "checked": len(runnable),
              "manual": len(manual)}
    return problems, warnings, counts, manual


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR,
                    help="skills tree to scan (default: .claude/skills)")
    ap.add_argument("--host", default=os.environ.get("SQL_AUDIT_HOST", "127.0.0.1"),
                    help="SSH tunnel host (default 127.0.0.1)")
    ap.add_argument("--port-enwiki", type=int,
                    default=int(os.environ.get("SQL_AUDIT_PORT_ENWIKI", 13306)),
                    help="local port tunnelled to enwiki_p (default 13306)")
    ap.add_argument("--port-commonswiki", type=int,
                    default=int(os.environ.get("SQL_AUDIT_PORT_COMMONSWIKI", 13307)),
                    help="local port tunnelled to commonswiki_p (default 13307)")
    ap.add_argument("--statement-timeout", type=int, default=15,
                    help="server-side cap per statement, seconds (default 15)")
    ap.add_argument("--strict-slow", action="store_true",
                    help="treat statements that hit the timeout as failures, not warnings")
    ap.add_argument("--json", dest="json_out", type=Path,
                    help="also write the full result set to this file")
    args = ap.parse_args(argv)

    if not args.skills_dir.is_dir():
        print(f"error: no such skills directory: {args.skills_dir}", file=sys.stderr)
        return 1

    if not os.environ.get("TOOLFORGE_SQL_USER") or not os.environ.get("TOOLFORGE_SQL_PASSWORD"):
        print("verify-sql-live: skipped — TOOLFORGE_SQL_USER / TOOLFORGE_SQL_PASSWORD are not set.")
        print("  This is an opt-in live check (CI has no replica access). To run it:")
        print("    ssh -N -L 13306:enwiki.analytics.db.svc.wikimedia.cloud:3306 <user>@dev.toolforge.org &")
        print("    ssh -N -L 13307:commonswiki.analytics.db.svc.wikimedia.cloud:3306 <user>@dev.toolforge.org &")
        print("    TOOLFORGE_SQL_USER=uXXXXX TOOLFORGE_SQL_PASSWORD=... python3 scripts/verify-sql-live.py")
        return 0

    problems, warnings, counts, manual = check(
        args.skills_dir,
        {"enwiki_p": args.port_enwiki, "commonswiki_p": args.port_commonswiki},
        host=args.host, statement_timeout=args.statement_timeout,
        strict_slow=args.strict_slow,
    )

    for problem in problems:
        print(f"  x {problem}")
    for warning in warnings:
        print(f"  (warn) {warning}")
    print(f"\n{counts['statements']} statement(s) extracted, {counts['checked']} executed as "
          f"zero-row probes, {counts['manual']} skipped as placeholders, "
          f"{len(problems)} violation(s), {len(warnings)} warning(s).")

    if args.json_out:
        args.json_out.write_text(json.dumps(
            {"counts": counts, "problems": problems, "warnings": warnings,
             "manual": [f"{m['file']}:{m['line']}" for m in manual]}, indent=1),
            encoding="utf-8")
        print(f"  (json written to {args.json_out})")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
