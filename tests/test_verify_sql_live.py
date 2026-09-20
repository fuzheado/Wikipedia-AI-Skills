"""Offline tests for scripts/verify-sql-live.py.

The checker itself needs Toolforge credentials, but everything that can be wrong
with it — extraction, statement splitting, placeholder skipping, probe building,
error classification — is testable with a fake connection, which is what this
file does. No network, no credentials.
"""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def load():
    spec = importlib.util.spec_from_file_location(
        "verify_sql_live", REPO_ROOT / "scripts" / "verify-sql-live.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sql_live = load()


# ─── fakes ──────────────────────────────────────────────────────────────

class FakeError(Exception):
    """Mirrors pymysql's (code, message) args."""


class FakeCursor:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, statement):
        self.conn.executed.append(statement)
        for needle, code, message in self.conn.failures:
            if needle in statement:
                raise FakeError(code, message)

    def fetchall(self):
        return []

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConnection:
    def __init__(self, failures=()):
        self.failures = list(failures)
        self.executed = []
        self.closed = False

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True


def make_tree(tmp_path: Path, sql_body="", md_body="", sh_body=""):
    root = tmp_path / "skills"
    (root / "demo" / "assets").mkdir(parents=True, exist_ok=True)
    (root / "demo" / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "demo" / "assets" / "queries.sql").write_text(sql_body, encoding="utf-8")
    (root / "demo" / "SKILL.md").write_text(md_body, encoding="utf-8")
    (root / "demo" / "scripts" / "run.sh").write_text(sh_body, encoding="utf-8")
    return root


# ─── extraction ─────────────────────────────────────────────────────────

def test_extracts_sql_files_md_fences_and_shell(tmp_path):
    tree = make_tree(
        tmp_path,
        sql_body="SELECT page_id FROM page WHERE page_title = 'A';\n\n"
                 "-- comment first\nSELECT rev_id FROM revision WHERE rev_page = 736;\n",
        md_body="```sql\nSELECT cl_from FROM categorylinks LIMIT 5;\n```\n\n"
                "```sparql\nSELECT ?item WHERE { ?item wdt:P31 wd:Q5 }\n```\n",
        sh_body='echo "    SELECT p.page_title FROM page p JOIN categorylinks cl ON cl.cl_from = p.page_id"\n',
    )
    statements = sql_live.extract_statements(tree)
    files = [s["file"] for s in statements]
    assert files.count("demo/assets/queries.sql") == 2
    assert files.count("demo/SKILL.md") == 1
    assert files.count("demo/scripts/run.sh") == 1
    # SPARQL is a different engine and must not be extracted
    assert all("wdt:P31" not in s["sql"] for s in statements)


def test_comment_lead_in_is_stripped(tmp_path):
    tree = make_tree(tmp_path, sql_body="-- Get page info\nSELECT page_id FROM page LIMIT 1;\n")
    first = sql_live.extract_statements(tree)[0]
    assert first["sql"].startswith("SELECT"), first["sql"]


def test_generated_eval_workspace_is_skipped(tmp_path):
    tree = make_tree(tmp_path)
    workspace = tree / "demo" / "assessment-workspace"
    workspace.mkdir(parents=True)
    (workspace / "report.md").write_text("```sql\nSELECT cl_to FROM categorylinks;\n```\n")
    assert all("assessment-workspace" not in s["file"] for s in sql_live.extract_statements(tree))


def test_target_db_selection():
    assert sql_live.target_db("SELECT gil_to FROM globalimagelinks") == "commonswiki_p"
    assert sql_live.target_db("SELECT * FROM commonswiki_p.page") == "commonswiki_p"
    assert sql_live.target_db("SELECT page_id FROM page") == "enwiki_p"


def test_normalise_applies_documented_literals():
    assert "{db}_p" not in sql_live.normalise("SELECT * FROM {db}_p.imagelinks")
    assert "'Physics'" in sql_live.normalise("SELECT * FROM page WHERE page_title = 'Category_name'")


def test_probe_appends_limit_or_wraps():
    assert sql_live.probe_sql("SELECT 1 FROM page").endswith("LIMIT 0")
    wrapped = sql_live.probe_sql("SELECT page_id FROM page LIMIT 10")
    assert wrapped.startswith("SELECT * FROM (") and wrapped.endswith("LIMIT 0")


# ─── checking ───────────────────────────────────────────────────────────

def test_check_reports_unknown_column_with_location(tmp_path):
    tree = make_tree(tmp_path, sql_body="SELECT COUNT(*) FROM pagelinks WHERE pl_title = 'X';\n")
    conn = FakeConnection(failures=[("pl_title", 1054, "Unknown column 'pl_title' in 'WHERE'")])
    problems, warnings, counts, _ = sql_live.check(
        tree, {"enwiki_p": 1, "commonswiki_p": 2}, connect=lambda db, port: conn)
    assert counts["checked"] == 1
    assert len(problems) == 1
    assert "demo/assets/queries.sql" in problems[0]
    assert "[1054]" in problems[0] and "pl_title" in problems[0]


def test_check_passes_clean_statements(tmp_path):
    tree = make_tree(tmp_path, sql_body="SELECT page_id FROM page LIMIT 5;\n")
    conn = FakeConnection()
    problems, warnings, counts, _ = sql_live.check(
        tree, {"enwiki_p": 1, "commonswiki_p": 2}, connect=lambda db, port: conn)
    assert problems == [] and warnings == []
    assert counts == {"statements": 1, "checked": 1, "manual": 0}


def test_check_warns_about_retired_identifier(tmp_path):
    tree = make_tree(
        tmp_path,
        sql_body="SELECT pp_value FROM page_props WHERE pp_propname = 'pageview_daily_average';\n")
    conn = FakeConnection()
    problems, warnings, _, _ = sql_live.check(
        tree, {"enwiki_p": 1, "commonswiki_p": 2}, connect=lambda db, port: conn)
    assert problems == []
    assert any("pageview_daily_average" in w for w in warnings)


def test_check_skips_placeholder_statements(tmp_path):
    tree = make_tree(tmp_path, sql_body="SELECT page_id FROM page WHERE page_title = 'YOUR_PAGE_TITLE';\n")
    conn = FakeConnection()
    problems, warnings, counts, manual = sql_live.check(
        tree, {"enwiki_p": 1, "commonswiki_p": 2}, connect=lambda db, port: conn)
    assert counts["manual"] == 1 and counts["checked"] == 0
    assert manual and problems == []
    assert conn.executed == []  # placeholders are never executed


def test_timeout_is_a_warning_unless_strict(tmp_path):
    tree = make_tree(tmp_path, sql_body="SELECT COUNT(*) FROM revision_userindex WHERE rev_timestamp > '2026';\n")
    failing = FakeConnection(failures=[("revision_userindex", 1969, "max_statement_time exceeded")])
    problems, warnings, _, _ = sql_live.check(
        tree, {"enwiki_p": 1, "commonswiki_p": 2}, connect=lambda db, port: failing)
    assert problems == [] and any("unusable at this scale" in w for w in warnings)

    strict = FakeConnection(failures=[("revision_userindex", 1969, "max_statement_time exceeded")])
    problems, _, _, _ = sql_live.check(
        tree, {"enwiki_p": 1, "commonswiki_p": 2}, connect=lambda db, port: strict,
        strict_slow=True)
    assert len(problems) == 1


def test_unreachable_replica_exits_with_tunnel_hint(tmp_path):
    tree = make_tree(tmp_path, sql_body="SELECT page_id FROM page LIMIT 1;\n")

    def boom(db, port):
        raise OSError("Connection refused")

    with pytest.raises(SystemExit) as excinfo:
        sql_live.check(tree, {"enwiki_p": 1, "commonswiki_p": 2}, connect=boom)
    assert "open the tunnels first" in str(excinfo.value)


# ─── CLI ────────────────────────────────────────────────────────────────

def test_cli_skips_without_credentials(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("TOOLFORGE_SQL_USER", raising=False)
    monkeypatch.delenv("TOOLFORGE_SQL_PASSWORD", raising=False)
    assert sql_live.main(["--skills-dir", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "skipped" in out and "dev.toolforge.org" in out


def test_cli_rejects_missing_skills_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TOOLFORGE_SQL_USER", "u1")
    monkeypatch.setenv("TOOLFORGE_SQL_PASSWORD", "x")
    assert sql_live.main(["--skills-dir", str(tmp_path / "nope")]) == 1
