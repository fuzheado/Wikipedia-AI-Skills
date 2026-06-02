#!/usr/bin/env python3
"""
04-generate-taskgraph.py — Phase 3: Taskgraph Generator

Reads diagnosis.json + verification.json and produces:
  - taskgraph.json   (validated task DAG)
  - analysis.md      (human-readable report)

Usage:
  python3 scripts/04-generate-taskgraph.py
  python3 scripts/04-generate-taskgraph.py --project-dir /path/to/project
  python3 scripts/04-generate-taskgraph.py --force
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# ── Task category → criticality mapping ────────────────────────────

VERDICT_TO_TASK = {
    "contradicted": {"category": "factual_correction", "criticality": "p0"},
    "npov_or": {"category": "npov_rewrite", "criticality": "p0"},
    "unverifiable": {"category": "citation", "criticality": "p1"},
}

STRUCTURAL_TASKS = {
    "missing_infobox": {"category": "infobox", "criticality": "p1"},
    "missing_sections": {"category": "structural", "criticality": "p1"},
    "under_assessed": {"category": "maintenance", "criticality": "p1"},
    "grammar": {"category": "grammar", "criticality": "p2"},
    "missing_image": {"category": "infobox", "criticality": "p2"},
    "short_description_grammar": {"category": "grammar", "criticality": "p2"},
}


# ── Generate tasks from verdicts ───────────────────────────────────

def generate_verdict_tasks(verification, diagnosis):
    """Generate one task per non-confirmed sentence."""
    tasks = []
    sentences = verification.get("sentences", [])

    for s in sentences:
        verdict = s.get("verdict")
        if not verdict or verdict == "confirmed":
            continue

        task_spec = VERDICT_TO_TASK.get(verdict)
        if not task_spec:
            continue

        text = s.get("text", "")[:80]
        task_id = f"fix_s{s.get('index', 0)}_{verdict}"

        action = {
            "type": "edit_wikitext",
            "page": diagnosis.get("article_title", ""),
            "oldText": text,
            "newText": s.get("correction", f"[NEEDS REWRITE: {text}]"),
            "summary": f"{verdict}: S{s.get('index', 0)} - {s.get('npov_explanation', 'needs rewrite')[:80]}" if verdict == "npov_or" else f"fix disputed claim in S{s.get('index', 0)}",
        }

        if s.get("correction_citation"):
            action["citation"] = s["correction_citation"]

        verify_steps = [
            {"type": "page_contains", "page": diagnosis.get("article_title", ""), "text": s.get("correction", "")[:50]}
        ] if s.get("correction") else []

        tasks.append({
            "id": task_id,
            "summary": f"{verdict}: S{s.get('index', 0)} - {text}",
            "depends_on": ["fetch_and_verify_sources"],
            "category": task_spec["category"],
            "criticality": task_spec["criticality"],
            "tools": ["wikipedia_api"],
            "actions": [action],
            "verify": verify_steps,
        })

    return tasks


def generate_structural_tasks(diagnosis):
    """Generate tasks from structural findings."""
    tasks = []
    findings = diagnosis.get("structural", {})
    title = diagnosis.get("article_title", "")
    article_type = diagnosis.get("article_type", "")

    # Missing infobox
    if not findings.get("has_infobox"):
        tasks.append({
            "id": "add_infobox",
            "summary": f"Add {{Infobox person}} — article type: {article_type}",
            "depends_on": [],
            "category": "infobox",
            "criticality": "p1",
            "tools": ["wikipedia_api"],
            "actions": [{
                "type": "insert_after",
                "page": title,
                "after": "{{Short description",
                "after_type": "string",
                "wikitext": "\n\n{{Infobox person\n| name          = \n| image         = \n| caption       = \n| birth_date    = \n| birth_place   = \n| death_date    = \n| death_place   = \n| occupation    = \n| known_for     = \n}}",
                "summary": "add {{Infobox person}}",
            }],
            "verify": [{"type": "infobox_exists", "page": title, "expected_template": "Infobox person"}],
        })

    # Short description grammar
    for issue in findings.get("short_description_issues", []):
        tasks.append({
            "id": "fix_short_description",
            "summary": f"Fix short description: {issue}",
            "depends_on": [],
            "category": "grammar",
            "criticality": "p2",
            "tools": ["wikipedia_api"],
            "actions": [],
            "verify": [],
        })

    # Missing sections
    missing = findings.get("missing_expected_sections", [])
    if missing:
        tasks.append({
            "id": "add_missing_sections",
            "summary": f"Add missing sections: {', '.join(missing)}",
            "depends_on": ["rewrite_npov_block"] if any("npov" in t.get("id", "") for t in tasks) else [],
            "category": "structural",
            "criticality": "p1",
            "tools": ["wikipedia_api"],
            "actions": [],
            "verify": [{"type": "section_exists", "page": title, "heading": s} for s in missing],
        })

    # Under-assessment
    current = findings.get("current_assessment", "")
    if current in ("Stub", "stub"):
        tasks.append({
            "id": "update_assessment",
            "summary": f"Update assessment from {current} to Start",
            "depends_on": [t["id"] for t in tasks if t["criticality"] in ("p0", "p1")],
            "category": "maintenance",
            "criticality": "p1",
            "tools": ["wikipedia_api"],
            "actions": [{
                "type": "edit_talk_page",
                "page": f"Talk:{title}",
                "oldText": f"class={current}",
                "newText": "class=Start",
                "summary": f"bump assessment from {current} to Start after cleanup",
            }],
            "verify": [{"type": "assessment_equals", "page": f"Talk:{title}", "expected_class": "Start"}],
        })

    return tasks


def generate_sources_task(diagnosis):
    """Generate the initial fetch_and_verify_sources task."""
    return [{
        "id": "fetch_and_verify_sources",
        "summary": "Fetch and cache all cited sources for verification",
        "depends_on": [],
        "category": "verification",
        "criticality": "p0",
        "tools": ["http_get", "file_read"],
        "inputs": [
            {"type": "web_page", "url": f"https://en.wikipedia.org/w/index.php?title={quote(diagnosis.get('article_title', ''))}&action=raw"}
        ],
        "actions": [],
        "verify": [],
    }]


def quote(s):
    """Minimal URL quoting."""
    return s.replace(" ", "_")


# ── Generate analysis.md ────────────────────────────────────────────

def generate_analysis_md(diagnosis, verification, tasks):
    """Produce the human-readable markdown report."""
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    title = diagnosis.get("article_title", "")

    lines = [
        "<!-- AUTO-GENERATED from verification.json + taskgraph.json",
        f"     Do not edit by hand. Generated: {now}",
        f"     Article: {title} -->",
        "",
        f"# Article Audit: {title}",
        "",
        "## Quick Stats",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Article type | {diagnosis.get('article_type', '?')} |",
        f"| Current assessment | {diagnosis.get('structural', {}).get('current_assessment', '?')} |",
        f"| Length | {diagnosis.get('structural', {}).get('length_bytes', 0)} bytes |",
        f"| Infobox | {'✅' if diagnosis.get('structural', {}).get('has_infobox') else '❌'} |",
        f"| Sections | {diagnosis.get('structural', {}).get('section_count', 0)} |",
        f"| Categories | {diagnosis.get('structural', {}).get('category_count', 0)} |",
        f"| References | ~{diagnosis.get('structural', {}).get('reference_count', 0)} |",
        "",
    ]

    # NPOV flags
    npov_flags = diagnosis.get("npov_flags", [])
    if npov_flags:
        lines.append("## NPOV Trigger Words Found\n")
        lines.append("| Sentence | Trigger | Category |")
        lines.append("|---|---|---|")
        for f in npov_flags[:15]:
            lines.append(f"| S{f['sentence_index']} | `{f['trigger']}` | {f['category']} |")
        if len(npov_flags) > 15:
            lines.append(f"| ... and {len(npov_flags) - 15} more | | |")
        lines.append("")

    # Per-sentence verdicts
    sentences = verification.get("sentences", [])
    if sentences:
        lines.append("## Sentence Verdicts\n")
        lines.append("| # | Verdict | Text (truncated) |")
        lines.append("|---|---|---|")
        for s in sentences:
            v = s.get("verdict", "?")
            icon = {"confirmed": "✅", "contradicted": "❌", "npov_or": "⚠️", "unverifiable": "❓", "mixed": "🟡"}.get(v, "➖")
            txt = s.get("text", "")[:100]
            lines.append(f"| {s.get('index', '?')} | {icon} {v} | {txt} |")
        lines.append("")

    # Task summary
    if tasks:
        lines.append("## Task Summary\n")
        lines.append(f"Total tasks: {len(tasks)}\n")
        by_crit = {}
        for t in tasks:
            c = t.get("criticality", "p2")
            by_crit.setdefault(c, []).append(t["id"])
        for c in ["p0", "p1", "p2"]:
            if c in by_crit:
                lines.append(f"- **{c.upper()}** ({len(by_crit[c])}): {', '.join(by_crit[c])}")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated by wikipedia-en-article-audit skill on {now}*")

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────

def main():
    project_dir = Path.cwd()
    force = False

    args = sys.argv[1:]
    while args:
        if args[0] == "--project-dir" and len(args) > 1:
            project_dir = Path(args[1])
            args = args[2:]
        elif args[0] == "--force":
            force = True
            args = args[1:]
        else:
            args = args[1:]

    # Load inputs
    diagnosis_path = project_dir / "diagnosis.json"
    verification_path = project_dir / "verification.json"

    if not diagnosis_path.exists():
        print(f"❌ diagnosis.json not found at {diagnosis_path}")
        print("   Run 01-diagnose.py first.")
        sys.exit(1)

    if not verification_path.exists():
        print(f"❌ verification.json not found at {verification_path}")
        print("   Complete Phase 2 (human review) before generating taskgraph.")
        sys.exit(1)

    diagnosis = json.loads(diagnosis_path.read_text())
    verification = json.loads(verification_path.read_text())

    # Staleness check for analysis.md
    analysis_path = project_dir / "analysis.md"
    if analysis_path.exists() and not force:
        v_mtime = os.path.getmtime(verification_path)
        a_mtime = os.path.getmtime(analysis_path)
        if v_mtime > a_mtime:
            print("⚠️  analysis.md is stale (verification.json changed since last generation).")
            print("   Run with --force to overwrite.")
            if not force:
                pass  # Continue generating taskgraph; just warn about analysis.md

    # Generate tasks
    tasks = []
    tasks.extend(generate_sources_task(diagnosis))
    tasks.extend(generate_verdict_tasks(verification, diagnosis))
    tasks.extend(generate_structural_tasks(diagnosis))

    # Build taskgraph
    taskgraph = {
        "$schema": "taskgraph.schema.json",
        "version": "1.0",
        "project": diagnosis.get("article_title", "").replace(" ", "_").lower(),
        "article_title": diagnosis.get("article_title", ""),
        "article_url": f"https://en.wikipedia.org/wiki/{quote(diagnosis.get('article_title', ''))}",
        "execution": {
            "max_concurrency": 1,
            "fail_fast": True,
            "require_verification": True,
            "status_report_path": "run_status.jsonl",
        },
        "tasks": tasks,
    }

    # Validate before writing (basic check)
    task_ids = {t["id"] for t in tasks}
    for t in tasks:
        for dep in t.get("depends_on", []):
            if dep not in task_ids:
                print(f"⚠️  Task '{t['id']}' depends on '{dep}' which does not exist")

    # Write taskgraph.json
    (project_dir / "taskgraph.json").write_text(json.dumps(taskgraph, indent=2))
    print(f"✅ taskgraph.json written ({len(tasks)} tasks)")

    # Write analysis.md
    analysis_md = generate_analysis_md(diagnosis, verification, tasks)
    (project_dir / "analysis.md").write_text(analysis_md)
    print(f"✅ analysis.md written")


if __name__ == "__main__":
    main()
