"""Content-anchor tests for the WAIS-Bench Phase 0 task registry.

No network. Verifies the task JSON files parse, carry the required schema
fields, have unique ids, and pass the schema validator script.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = REPO_ROOT / "research" / "benchmarks" / "tasks"
VALIDATOR = REPO_ROOT / "research" / "benchmarks" / "scripts" / "validate-benchmark-tasks.py"

REQUIRED_FIELDS = [
    "schema_version", "id", "title", "round", "complexity", "tier", "dimension",
    "prompt", "skills", "apis", "expected_output", "canaries", "verifier",
    "safety", "time_budget_min", "source", "status", "port_notes",
]


def task_files():
    return sorted(TASKS_DIR.glob("*.json"))


def test_twelve_tasks_present():
    assert len(task_files()) == 12, f"expected 12 ported AB tasks, found {len(task_files())}"


def test_all_task_files_parse_as_json():
    for path in task_files():
        data = json.loads(path.read_text())
        assert isinstance(data, dict), f"{path.name} is not a JSON object"


def test_required_fields_present():
    for path in task_files():
        data = json.loads(path.read_text())
        missing = [f for f in REQUIRED_FIELDS if f not in data]
        assert not missing, f"{path.name} missing: {missing}"


def test_task_ids_unique_and_match_filename():
    ids = []
    for path in task_files():
        data = json.loads(path.read_text())
        assert data["id"], f"{path.name} has empty id"
        assert path.name.startswith(data["id"]), (
            f"{path.name} filename must start with task id {data['id']!r}"
        )
        ids.append(data["id"])
    assert len(ids) == len(set(ids)), "duplicate task ids"


def test_all_rounds_covered():
    data = [json.loads(p.read_text()) for p in task_files()]
    rounds = {d["round"] for d in data}
    assert rounds == {1, 2, 3}, f"expected rounds 1-3, got {sorted(rounds)}"


def test_every_task_has_verifier_and_canaries():
    for path in task_files():
        data = json.loads(path.read_text())
        assert data["verifier"]["checks"], f"{path.name} has no verifier checks"
        assert data["canaries"], f"{path.name} has no canaries"


def test_validator_script_runs_clean():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0, f"validator failed:\n{result.stdout}\n{result.stderr}"
    assert "OK:" in result.stdout


def test_validator_report_mentions_all_tasks():
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "--report"], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode == 0
    for path in task_files():
        data = json.loads(path.read_text())
        assert data["id"] in result.stdout, f"{data['id']} missing from validator report"
