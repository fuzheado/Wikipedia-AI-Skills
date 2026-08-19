#!/usr/bin/env python3
"""Validate the WAIS-Bench Phase 0 task registry.

Checks every JSON file in research/benchmarks/tasks/ against the task schema:
required fields, id conventions, enums, verifier check kinds, canary structure,
and that referenced skill names exist in .claude/skills/.

Stdlib only. Usage:
    python3 research/benchmarks/scripts/validate-benchmark-tasks.py [--report]
    python3 research/benchmarks/scripts/validate-benchmark-tasks.py --skills-dir .claude/skills
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA_VERSION = "0.1.0"
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TASKS_DIR = REPO_ROOT / "research" / "benchmarks" / "tasks"
DEFAULT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

REQUIRED_TOP_LEVEL = [
    "schema_version", "id", "title", "round", "complexity", "tier", "dimension",
    "prompt", "skills", "apis", "expected_output", "canaries", "verifier",
    "safety", "time_budget_min", "source", "status", "port_notes",
]
ALLOWED_TIERS = {"live", "gold"}
ALLOWED_SAFETY = {"read-only", "sandbox-write", "live-write"}
ALLOWED_DIMENSIONS = {
    "single-api-read", "multi-step-orchestration", "real-time-streams",
    "framework-usage", "cross-project-orchestration", "writing", "sql",
    "multi-agent", "long-running",
}
ALLOWED_VERIFIER_KINDS = {
    "api_crosscheck", "count_check", "schema_check", "canary_detection",
    "membership_check", "anti_contamination", "ordering_check", "artifact_check",
    "namespace_check", "assertion_check", "safety_check", "sanity_check",
    "sparql_match", "anti_fabrication", "throughput_check",
}
ALLOWED_VERIFIER_TOP_KIND = {"api_crosscheck", "sparql_match", "mixed"}
ALLOWED_STATUS = {"ported", "gold", "draft", "retired"}

ID_RE = re.compile(r"^r(\d+)t(\d+)-[a-z0-9-]+$")


def validate_tasks(tasks_dir: Path, skills_dir: Path) -> list[str]:
    violations: list[str] = []
    task_files = sorted(tasks_dir.glob("*.json"))
    if not task_files:
        return [f"no task JSON files found in {tasks_dir}"]

    seen_ids: dict[str, str] = {}

    for path in task_files:
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            violations.append(f"{path.name}: invalid JSON: {e}")
            continue

        # Schema version
        if data.get("schema_version") != SCHEMA_VERSION:
            violations.append(
                f"{path.name}: schema_version must be {SCHEMA_VERSION}, got {data.get('schema_version')!r}"
            )

        # Required fields
        for field in REQUIRED_TOP_LEVEL:
            if field not in data:
                violations.append(f"{path.name}: missing required field '{field}'")

        # ID conventions
        tid = data.get("id", "")
        id_match = ID_RE.match(tid)
        if not id_match:
            violations.append(f"{path.name}: id {tid!r} must match {ID_RE.pattern}")
        else:
            rnd, tsk = int(id_match.group(1)), int(id_match.group(2))
            if rnd != data.get("round"):
                violations.append(f"{path.name}: round {data.get('round')} != id prefix r{rnd}")
            if not path.name.startswith(tid):
                violations.append(f"{path.name}: filename must start with task id {tid!r}")
        if tid in seen_ids:
            violations.append(f"{path.name}: duplicate id {tid!r} (also {seen_ids[tid]})")
        else:
            seen_ids[tid] = path.name

        # Enums
        if data.get("tier") not in ALLOWED_TIERS:
            violations.append(f"{path.name}: tier {data.get('tier')!r} not in {sorted(ALLOWED_TIERS)}")
        if data.get("safety") not in ALLOWED_SAFETY:
            violations.append(f"{path.name}: safety {data.get('safety')!r} not in {sorted(ALLOWED_SAFETY)}")
        if data.get("dimension") not in ALLOWED_DIMENSIONS:
            violations.append(
                f"{path.name}: dimension {data.get('dimension')!r} not in {sorted(ALLOWED_DIMENSIONS)}"
            )
        if data.get("status") not in ALLOWED_STATUS:
            violations.append(f"{path.name}: status {data.get('status')!r} not in {sorted(ALLOWED_STATUS)}")
        if not isinstance(data.get("time_budget_min"), int) or data.get("time_budget_min") <= 0:
            violations.append(f"{path.name}: time_budget_min must be a positive int")

        # Skills exist in the repo
        for skill in data.get("skills", []):
            if not (skills_dir / skill / "SKILL.md").exists():
                violations.append(f"{path.name}: skill '{skill}' not found at {skills_dir / skill / 'SKILL.md'}")

        # Canaries
        canary_ids = set()
        for c in data.get("canaries", []):
            if not isinstance(c, dict) or not all(k in c for k in ("id", "name", "description", "detection")):
                violations.append(f"{path.name}: canary entries need id/name/description/detection")
                continue
            if c["id"] in canary_ids:
                violations.append(f"{path.name}: duplicate canary id {c['id']!r}")
            canary_ids.add(c["id"])

        # Verifier
        verifier = data.get("verifier", {})
        if not isinstance(verifier, dict):
            violations.append(f"{path.name}: verifier must be an object")
            continue
        if verifier.get("kind") not in ALLOWED_VERIFIER_TOP_KIND:
            violations.append(
                f"{path.name}: verifier.kind {verifier.get('kind')!r} not in {sorted(ALLOWED_VERIFIER_TOP_KIND)}"
            )
        check_ids = set()
        for check in verifier.get("checks", []):
            if not isinstance(check, dict) or not all(k in check for k in ("id", "kind", "detail", "pass_condition")):
                violations.append(f"{path.name}: verifier checks need id/kind/detail/pass_condition")
                continue
            if check["kind"] not in ALLOWED_VERIFIER_KINDS:
                violations.append(
                    f"{path.name}: check kind {check['kind']!r} not in {sorted(ALLOWED_VERIFIER_KINDS)}"
                )
            if check["id"] in check_ids:
                violations.append(f"{path.name}: duplicate verifier check id {check['id']!r}")
            check_ids.add(check["id"])

    return violations


def report(tasks_dir: Path) -> None:
    print(f"{'TASK':<28} {'R':<2} {'TIER':<6} {'DIMENSION':<28} {'CHECKS':<6} {'CANARIES':<8} SKILLS")
    for path in sorted(tasks_dir.glob("*.json")):
        data = json.loads(path.read_text())
        print(
            f"{data['id']:<28} {data['round']:<2} {data['tier']:<6} "
            f"{data['dimension']:<28} {len(data['verifier']['checks']):<6} "
            f"{len(data['canaries']):<8} {', '.join(data['skills'])}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate WAIS-Bench task registry")
    ap.add_argument("--tasks-dir", type=Path, default=DEFAULT_TASKS_DIR)
    ap.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR)
    ap.add_argument("--report", action="store_true", help="print task inventory table")
    args = ap.parse_args()

    if args.report:
        report(args.tasks_dir)

    violations = validate_tasks(args.tasks_dir, args.skills_dir)
    if violations:
        print(f"VALIDATION FAILED: {len(violations)} violation(s)", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    n = len(list(args.tasks_dir.glob("*.json")))
    print(f"OK: {n} task file(s) validated against schema v{SCHEMA_VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
