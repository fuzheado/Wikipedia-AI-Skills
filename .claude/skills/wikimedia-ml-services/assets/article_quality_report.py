#!/usr/bin/env python3
"""Generate a comprehensive article quality report by chaining multiple Lift Wing models.

Takes a page title and language, fetches the latest revision ID, then scores:
  1. Article quality (Revscoring model)
  2. Readability (modern model)
  3. Topic classification (outlink topic model)
  4. Reference risk (modern model)

Usage:
    python3 article_quality_report.py Albert_Einstein en
    python3 article_quality_report.py "Douglas_Adams" en --output json
    python3 article_quality_report.py 123456789 en --rev-id  (skip page lookup)

Output:
    Text report by default, or JSON with --output json.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import requests


# ── API configuration ────────────────────────────────────────────────────────
BASE_URL = "https://api.wikimedia.org/service/lw/inference/v1/models"
REST_API = "https://en.wikipedia.org/api/rest_v1"
USER_AGENT = "ArticleQualityReport/1.0 (user@example.com) ContentGapResearch"
MIN_INTERVAL = 0.15  # ~7 req/s — conservative for anonymous users


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    })
    token = os.environ.get("ACCESS_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def fetch_latest_revision(page_title: str, lang: str = "en") -> int | None:
    """Get the latest revision ID for a page title via the REST API."""
    domain = f"{lang}.wikipedia.org"
    url = f"https://{domain}/api/rest_v1/page/summary/{page_title}"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        return resp.json().get("revision")
    except requests.exceptions.RequestException as e:
        print(f"  ⚠  Could not fetch revision for '{page_title}': {e}", file=sys.stderr)
        return None


def call_liftwing(
    session: requests.Session, model: str, payload: dict
) -> dict | None:
    """Call a Lift Wing model and return the parsed response."""
    url = f"{BASE_URL}/{model}:predict"
    try:
        resp = session.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  ⚠  {model}: {e}", file=sys.stderr)
        return None


# ── Model-specific extraction functions ──────────────────────────────────────

def extract_quality(rev_id: int, result: dict | None) -> dict:
    """Extract article quality grade from Revscoring model response."""
    if result is None:
        return {"grade": "ERROR"}
    for wiki_key, wiki_data in result.items():
        if isinstance(wiki_data, dict) and "scores" in wiki_data:
            try:
                score = wiki_data["scores"][str(rev_id)]["articlequality"]["score"]
                return {
                    "grade": score.get("prediction", "N/A"),
                    "probabilities": score.get("probability", {}),
                }
            except (KeyError, TypeError):
                pass
    return {"grade": "PARSE_ERROR", "raw": str(result)[:200]}


def extract_readability(result: dict | None) -> dict:
    """Extract readability metrics."""
    if result is None:
        return {"error": "No response"}
    output = result.get("output", {})
    return {
        "score": output.get("score"),
        "fk_score_proxy": output.get("fk_score_proxy"),
    }


def extract_outlink_topics(result: dict | None, top_n: int = 5) -> dict:
    """Extract top topic predictions from outlink-topic-model."""
    if result is None:
        return {"error": "No response"}
    try:
        results = result["prediction"]["results"]
    except (KeyError, TypeError):
        return {"error": "Unexpected response format", "raw": str(result)[:200]}

    # Get top N topics
    top = results[:top_n]

    # Group by top-level category
    categories = {}
    for r in results:
        cat = r["topic"].split(".")[0] if "." in r["topic"] else "Other"
        categories[cat] = categories.get(cat, 0) + r["score"]

    top_cats = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))

    return {
        "top_topics": [{"topic": r["topic"], "score": round(r["score"], 4)} for r in top],
        "category_breakdown": top_cats,
    }


def extract_reference_risk(result: dict | None) -> dict:
    """Extract reference quality risk."""
    if result is None:
        return {"error": "No response"}
    return {
        "risk_score": result.get("reference_risk_score"),
        "ref_count": result.get("reference_count"),
        "survival_ratio": result.get("survival_ratio"),
    }


def format_quality_bar(probs: dict, grade: str) -> str:
    """Format a quality probability bar."""
    lines = [f"   Predicted grade: {grade}"]
    sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    for g, p in sorted_probs:
        filled = int(p * 20)
        bar = "█" * filled + "░" * (20 - filled)
        marker = " ←" if g == grade else ""
        lines.append(f"   {g:>6}: {p:>5.1%} {bar}{marker}")
    return "\n".join(lines)


def format_readability(r: dict) -> str:
    """Format readability results."""
    score = r.get("score")
    grade = r.get("fk_score_proxy")
    if score is None:
        return "   (unavailable)"

    level = (
        "Very Easy" if score > 0.8
        else "Easy" if score > 0.6
        else "Fairly Difficult" if score > 0.4
        else "Difficult" if score > 0.2
        else "Very Confusing"
    )
    lines = [f"   Readability score: {score:.3f} ({level})"]
    if grade is not None:
        audience = (
            "Children" if grade < 6
            else "General Adult" if grade < 10
            else "College" if grade < 14
            else "Academic"
        )
        lines.append(f"   Grade level: {grade:.1f} (target: {audience})")
    return "\n".join(lines)


def format_topics(t: dict) -> str:
    """Format topic results."""
    if "error" in t:
        return f"   {t['error']}"

    lines = []
    for cat, score in t.get("category_breakdown", {}).items():
        lines.append(f"   {cat}: {score:.1%}")

    for topic in t.get("top_topics", []):
        lines.append(f"     • {topic['topic']}: {topic['score']:.1%}")

    return "\n".join(lines)


def format_reference_risk(r: dict) -> str:
    """Format reference risk results."""
    if "error" in r:
        return f"   {r['error']}"
    risk = r.get("risk_score")
    count = r.get("ref_count")
    survival = r.get("survival_ratio", {})

    lines = []
    if risk is not None:
        lines.append(f"   Reference risk score: {risk:.1%}")
    if count is not None:
        lines.append(f"   Reference count: {count}")
    if survival:
        lines.append(f"   Survival ratio: mean={survival.get('mean', '?'):.1%}, "
                      f"median={survival.get('median', '?'):.1%}")
    return "\n".join(lines)


def generate_report(page_title: str, lang: str, rev_id: int | None = None) -> dict:
    """Fetch all ML scores and return a structured report dict."""
    session = get_session()

    # If rev_id not provided, fetch the latest revision
    if rev_id is None:
        rev_id = fetch_latest_revision(page_title, lang)
        if rev_id is None:
            return {"error": f"Could not determine revision ID for '{page_title}'"}
    else:
        # Use the provided rev_id; page_title is still needed for topic model
        pass

    results = {}

    # Model 1: Article quality (Revscoring, uses rev_id)
    print(f"  [1/4] Article quality...", file=sys.stderr)
    quality_result = call_liftwing(
        session, f"{lang}wiki-articlequality", {"rev_id": rev_id}
    )
    results["quality"] = extract_quality(rev_id, quality_result)
    time.sleep(MIN_INTERVAL)

    # Model 2: Readability (modern, uses rev_id + lang)
    print(f"  [2/4] Readability...", file=sys.stderr)
    readability_result = call_liftwing(
        session, "readability", {"rev_id": rev_id, "lang": lang}
    )
    results["readability"] = extract_readability(readability_result)
    time.sleep(MIN_INTERVAL)

    # Model 3: Topic classification (uses page_title + lang)
    print(f"  [3/4] Topic classification...", file=sys.stderr)
    topic_result = call_liftwing(
        session, "outlink-topic-model", {"page_title": page_title, "lang": lang}
    )
    results["topics"] = extract_outlink_topics(topic_result)
    time.sleep(MIN_INTERVAL)

    # Model 4: Reference risk (uses rev_id + lang)
    print(f"  [4/4] Reference risk...", file=sys.stderr)
    ref_result = call_liftwing(
        session, "reference-risk", {"rev_id": rev_id, "lang": lang}
    )
    results["reference_risk"] = extract_reference_risk(ref_result)

    return results


def format_text_report(page_title: str, lang: str, rev_id: int, report: dict) -> str:
    """Format the report as human-readable text."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"📋 Article Quality Report")
    lines.append(f"   Title: {page_title}")
    lines.append(f"   Language: {lang}")
    lines.append(f"   Revision: {rev_id}")
    lines.append(f"   Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("=" * 60)

    # Quality
    q = report.get("quality", {"grade": "N/A"})
    if "error" not in q:
        lines.append(f"\n🏆 Article Quality")
        lines.append(format_quality_bar(q.get("probabilities", {}), q.get("grade", "N/A")))
    else:
        lines.append(f"\n🏆 Article Quality: {q['error']}")

    # Readability
    r = report.get("readability", {})
    if "error" not in r:
        lines.append(f"\n📖 Readability")
        lines.append(format_readability(r))
    else:
        lines.append(f"\n📖 Readability: {r['error']}")

    # Topics
    t = report.get("topics", {})
    if "error" not in t:
        lines.append(f"\n🏷️  Topic Classification")
        lines.append(format_topics(t))
    else:
        lines.append(f"\n🏷️  Topic Classification: {t['error']}")

    # Reference risk
    ref = report.get("reference_risk", {})
    if "error" not in ref:
        lines.append(f"\n🔗 Reference Quality")
        lines.append(format_reference_risk(ref))
    else:
        lines.append(f"\n🔗 Reference Quality: {ref['error']}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate a comprehensive article quality report using Lift Wing ML models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("page_or_rev", help="Wikipedia page title (underscores) or revision ID if --rev-id")
    parser.add_argument("lang", nargs="?", default="en", help="Language code (default: en)")
    parser.add_argument("--rev-id", action="store_true", help="First argument is a revision ID, not a page title")
    parser.add_argument("--output", choices=["text", "json"], default="text")

    args = parser.parse_args()

    if args.rev_id:
        # User provided a revision ID directly
        rev_id = int(args.page_or_rev)
        page_title = f"rev_id={rev_id}"
        print(f"\n🔍 Generating quality report for revision {rev_id} ({args.lang})...\n", file=sys.stderr)
    else:
        rev_id = None
        page_title = args.page_or_rev
        print(f"\n🔍 Generating quality report for '{page_title}' ({args.lang})...\n", file=sys.stderr)

    report = generate_report(page_title, args.lang, rev_id)

    if "error" in report:
        print(f"❌ {report['error']}", file=sys.stderr)
        sys.exit(1)

    # Determine actual rev_id used
    actual_rev_id = rev_id
    if actual_rev_id is None:
        # Try to extract from report or fetch again
        pass

    if args.output == "json":
        print(json.dumps(report, indent=2, default=str))
    else:
        print(format_text_report(page_title, args.lang, rev_id or 0, report))


if __name__ == "__main__":
    main()
