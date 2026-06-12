"""
Notability report templates and output formatters.

Usage:
    from notability_templates import (
        format_report,
        format_short,
        generate_afd_summary,
    )

    # Full formatted report
    print(format_report(report))

    # One-line summary
    print(format_short(report))

    # AfD nomination summary
    summary = generate_afd_summary(report)
"""

from typing import Any, Dict, List, Optional

from notability_checker import NotabilityReport, GNGResult, SNGResult


def format_report(report: NotabilityReport) -> str:
    """Format a full notability assessment report as human-readable text."""
    lines = []
    lines.append("=" * 50)
    lines.append("NOTABILITY ASSESSMENT REPORT")
    lines.append("=" * 50)
    lines.append("")

    # Subject info
    lines.append(f"Subject: {report.subject_name}")
    lines.append(f"Type:    {report.subject_type}")
    if report.description:
        lines.append(f"Desc:    {report.description}")
    lines.append("")

    # Verdict
    verdict_char = {
        "notable": "✅",
        "not_notable": "❌",
        "unclear": "❓",
    }.get(report.overall_verdict, "❓")

    lines.append(f"{verdict_char}  Verdict: {report.overall_verdict.upper()}")
    lines.append(f"   Confidence: {report.confidence.upper()}")
    lines.append("")

    # Exclusion flags
    if report.exclusion_flags:
        lines.append("⚠ EXCLUSION FLAGS:")
        for flag in report.exclusion_flags:
            lines.append(f"   • {flag}")
        lines.append("")

    # SNG results
    sng_hits = [s for s in report.sng_results if s.criteria_met]
    if sng_hits:
        lines.append("📋 SUBJECT-SPECIFIC GUIDELINES (SNGs):")
        for s in sng_hits:
            bullet = "✅" if s.criteria_met else "  "
            lines.append(f"   {bullet} {s.sng}: {s.details}")
        lines.append("")

    sng_misses = [s for s in report.sng_results if not s.criteria_met and s.confidence != "low"]
    if sng_misses:
        for s in sng_misses:
            lines.append(f"      {s.sng}: {s.details}")
        lines.append("")

    # GNG assessment
    g = report.gng
    lines.append("📊 GENERAL NOTABILITY GUIDELINE (GNG):")
    lines.append(f"   {'✅' if g.passed else '❌'} Overall: {'PASS' if g.passed else 'FAIL'}")
    lines.append(f"   {'✅' if g.significant_coverage else '❌'} Significant coverage")
    lines.append(f"   {'✅' if g.reliable_sources else '❌'} Reliable sources")
    lines.append(f"   {'✅' if g.independent_sources else '❌'} Independent sources")
    lines.append(f"   {'✅' if g.multiple_sources else '❌'} Multiple sources")
    lines.append(f"   Sources evaluated: {g.source_count}")
    if g.notes:
        lines.append(f"   Notes: {g.notes}")
    lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("💡 RECOMMENDATIONS:")
        for rec in report.recommendations:
            lines.append(f"   → {rec}")

    return "\n".join(lines)


def format_short(report: NotabilityReport) -> str:
    """Format a one-line notability summary."""
    verdict = report.overall_verdict.upper()
    confidence = report.confidence.upper()
    sngs = ", ".join(
        s.sng for s in report.sng_results if s.criteria_met
    )
    gng = "GNG:✓" if report.gng.passed else "GNG:✗"

    parts = [f"[{verdict}] {report.subject_name}"]
    if sngs:
        parts.append(f"({sngs})")
    parts.append(f"[{gng}]")
    parts.append(f"[confidence:{confidence}]")

    return " ".join(parts)


def generate_afd_summary(
    report: NotabilityReport,
    include_sources: bool = True,
) -> str:
    """
    Generate a notability summary suitable for an AfD discussion.

    Args:
        report: NotabilityReport from the checker
        include_sources: Whether to include source details

    Returns:
        AfD-ready summary text
    """
    lines = []

    if report.overall_verdict == "notable":
        lines.append(f"'''Keep''' — Subject appears to meet notability guidelines.")
    elif report.overall_verdict == "not_notable":
        lines.append(f"'''Delete''' — Subject does not appear to meet notability guidelines.")
    else:
        lines.append(f"Notability is unclear. Needs further source evaluation.")

    # SNG justification
    sng_hits = [s for s in report.sng_results if s.criteria_met]
    if sng_hits:
        for s in sng_hits:
            lines.append(f"* Meets [[WP:{s.sng}]]: {s.details}")

    # GNG justification
    if report.gng.passed:
        lines.append(
            f"* Meets [[WP:GNG]]: {report.gng.source_count} "
            f"independent reliable sources with significant coverage found."
        )
    else:
        g = report.gng
        failures = []
        if not g.significant_coverage:
            failures.append("no source provides significant coverage")
        if not g.reliable_sources:
            failures.append("sources are not reliable")
        if not g.independent_sources:
            failures.append("sources are not independent")
        if not g.multiple_sources:
            failures.append("only one source found")
        if failures:
            lines.append(f"* Fails [[WP:GNG]]: {', '.join(failures)}.")

    # Exclusion flags
    for flag in report.exclusion_flags:
        lines.append(f"* ⚠ {flag}")

    return "\n".join(lines)


def generate_notability_tag(report: NotabilityReport) -> str:
    """
    Generate the appropriate maintenance template tag for a page.

    Returns:
        Wiki template string (e.g., {{notability|date=June 2026}})
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%B %Y")

    if report.overall_verdict == "notable":
        return ""  # No tag needed

    if report.overall_verdict == "not_notable":
        # Not truly notable — may need CSD or AfD instead
        return ""

    # Unclear — add notability tag
    return "{{notability|date=" + date_str + "}}"


# ---- CLI ----
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Format notability assessment reports"
    )
    parser.add_argument("--name", required=True, help="Subject name")
    parser.add_argument("--verdict", default="unclear",
                        choices=["notable", "not_notable", "unclear"])
    parser.add_argument("--format", default="full",
                        choices=["full", "short", "afd", "tag"])
    parser.add_argument("--type", default="person")
    parser.add_argument("--description", default="")

    args = parser.parse_args()

    # Create a minimal report for formatting demo
    report = NotabilityReport(
        subject_name=args.name,
        subject_type=args.type,
        description=args.description,
        overall_verdict=args.verdict,
    )

    if args.format == "full":
        print(format_report(report))
    elif args.format == "short":
        print(format_short(report))
    elif args.format == "afd":
        print(generate_afd_summary(report))
    elif args.format == "tag":
        tag = generate_notability_tag(report)
        print(tag if tag else "(no tag needed)")
