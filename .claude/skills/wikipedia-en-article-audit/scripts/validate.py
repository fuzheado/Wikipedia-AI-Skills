#!/usr/bin/env python3
"""
validate.py — Validate a taskgraph.json against its schema.

Usage:
    python3 validate.py                         # validate the default taskgraph.json
    python3 validate.py path/to/taskgraph.json  # validate a specific file
"""

import json
import sys
import os
from pathlib import Path

HERE = Path(__file__).parent

def load_json(path):
    with open(path) as f:
        return json.load(f)

def validate_dag(tasks):
    """Check that dependency references are valid and the graph is acyclic."""
    task_ids = {t["id"] for t in tasks}
    errors = []

    for t in tasks:
        tid = t["id"]
        for dep in t.get("depends_on", []):
            if dep not in task_ids:
                errors.append(f"  Task '{tid}' depends on '{dep}' which does not exist")

    # Topological sort to detect cycles (Kahn's algorithm)
    in_degree = {t["id"]: 0 for t in tasks}
    adj = {t["id"]: [] for t in tasks}
    for t in tasks:
        for dep in t.get("depends_on", []):
            adj[dep].append(t["id"])
            in_degree[t["id"]] += 1

    queue = [tid for tid, deg in in_degree.items() if deg == 0]
    sorted_count = 0
    while queue:
        tid = queue.pop(0)
        sorted_count += 1
        for neighbor in adj[tid]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if sorted_count != len(tasks):
        errors.append(f"  Cycle detected! Only {sorted_count}/{len(tasks)} tasks can be ordered.")

    return errors

def check_verify_steps(tasks):
    """Flag verification steps that might be impossible to satisfy."""
    warnings = []
    for t in tasks:
        for v in t.get("verify", []):
            vtype = v.get("type", "")
            if vtype == "page_contains" or vtype == "page_not_contains":
                if not v.get("text"):
                    warnings.append(f"  Task '{t['id']}': verify step has empty 'text' field")
            if vtype == "infobox_exists":
                if not v.get("page"):
                    warnings.append(f"  Task '{t['id']}': infobox_exists verify has no 'page'")
    return warnings

def main():
    if len(sys.argv) > 1:
        graph_path = Path(sys.argv[1])
    else:
        graph_path = HERE / "taskgraph.json"
    schema_path = HERE / "taskgraph.schema.json"

    if not graph_path.exists():
        print(f"❌ Not found: {graph_path}")
        sys.exit(1)
    if not schema_path.exists():
        print(f"❌ Not found: {schema_path}")
        sys.exit(1)

    graph = load_json(graph_path)
    schema = load_json(schema_path)

    # 1. Validate against JSON Schema
    try:
        import jsonschema
        jsonschema.validate(graph, schema)
        print("✅ JSON Schema validation: PASSED")
    except ImportError:
        print("⚠️  jsonschema not installed — skipping JSON Schema validation")
        print("   Install: pip install jsonschema")
    except jsonschema.ValidationError as e:
        print(f"❌ JSON Schema validation: FAILED")
        print(f"   {e.message}")
        sys.exit(1)

    # 2. Validate DAG
    tasks = graph.get("tasks", [])
    dag_errors = validate_dag(tasks)
    if dag_errors:
        print("❌ DAG validation: FAILED")
        for e in dag_errors:
            print(f"  {e}")
        sys.exit(1)
    else:
        print(f"✅ DAG validation: PASSED ({len(tasks)} tasks, acyclic)")

    # 3. Check verify steps
    warnings = check_verify_steps(tasks)
    if warnings:
        print("⚠️  Verify step warnings:")
        for w in warnings:
            print(f"  {w}")
    else:
        print("✅ Verify steps: all well-formed")

    # 4. Print execution order
    print(f"\n📋 Recommended execution order (topological sort):")
    in_degree = {t["id"]: len(t.get("depends_on", [])) for t in tasks}
    adj = {t["id"]: [] for t in tasks}
    for t in tasks:
        for dep in t.get("depends_on", []):
            adj[dep].append(t["id"])

    queue = [t["id"] for t in tasks if in_degree[t["id"]] == 0]
    criticality_order = {"p0": 0, "p1": 1, "p2": 2}
    task_map = {t["id"]: t for t in tasks}
    queue.sort(key=lambda tid: (criticality_order.get(task_map[tid].get("criticality", "p2"), 99), tid))

    order = []
    visited = set()
    while queue:
        tid = queue.pop(0)
        if tid in visited:
            continue
        visited.add(tid)
        order.append(tid)
        for neighbor in adj.get(tid, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
        queue.sort(key=lambda tid: (criticality_order.get(task_map[tid].get("criticality", "p2"), 99), tid))

    for i, tid in enumerate(order, 1):
        t = task_map[tid]
        crit = t.get("criticality", "p2")
        cat = t.get("category", "?")
        summary = t.get("summary", "")[:80]
        deps = t.get("depends_on", [])
        dep_str = f" (after: {', '.join(deps)})" if deps else ""
        print(f"  {i:2d}. [{crit}] {tid}{dep_str}")
        print(f"      {summary}")
        print()

    print(f"\n{'='*60}")
    print(f"✅ All checks passed. Taskgraph is ready for execution.")


if __name__ == "__main__":
    main()
