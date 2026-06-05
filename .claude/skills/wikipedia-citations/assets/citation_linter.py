#!/usr/bin/env python3
"""Parse and validate all citation templates in a Wikipedia page.

Reports:
  - Which citation templates are used (cite web, cite news, etc.)
  - Missing required parameters
  - Common issues (bare URLs, missing access-dates, no archives)
  - Template validity

Usage:
    python3 citation_linter.py Albert_Einstein
    python3 citation_linter.py Albert_Einstein --lang fr
    python3 citation_linter.py Albert_Einstein --fix      (generates suggested fixes)
    python3 citation_linter.py Albert_Einstein --output json
"""

import argparse
import json
import re
import sys
from collections import Counter

import requests


USER_AGENT = "CitationLinter/1.0 (user@example.com) ContentGapResearch"

# Required/mandatory parameters per template type
REQUIRED_PARAMS = {
    "cite web": ["url", "title"],
    "cite news": ["url", "title"],
    "cite book": ["title", "author"],
    "cite journal": ["title", "journal"],
    "cite magazine": ["url", "title"],
    "cite encyclopedia": ["title", "encyclopedia"],
    "cite arXiv": ["eprint"],
    "cite bioRxiv": ["biorxiv"],
    "cite conference": ["title", "book-title"],
    "cite thesis": ["title", "type", "publisher"],
    "cite report": ["title"],
    "cite patent": ["country", "number", "title"],
    "cite AV media": ["title"],
    "cite episode": ["title", "series"],
    "cite podcast": ["title", "series"],
    "cite interview": ["title"],
    "cite map": ["title"],
    "cite press release": ["title"],
    "cite speech": ["title"],
    "cite tech report": ["title"],
    "cite court": ["litigants", "court", "date"],
}

RECOMMENDED_PARAMS = {
    "cite web": ["access-date", "website", "date"],
    "cite news": ["access-date", "date", "newspaper"],
    "cite book": ["year", "publisher", "isbn"],
    "cite journal": ["volume", "pages", "doi", "year"],
    "cite magazine": ["access-date", "date"],
    "cite encyclopedia": ["year", "publisher"],
}


def fetch_wikitext(page_title: str, lang: str = "en") -> str | None:
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {"action": "parse", "page": page_title, "prop": "wikitext", "format": "json"}
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
        return resp.json()["parse"]["wikitext"]["*"]
    except (KeyError, requests.exceptions.RequestException):
        return None


def extract_parameters(params_text: str) -> dict[str, str]:
    """Extract key=value pairs from a template's parameter block."""
    params = {}
    # Match |key=value patterns (value can span multiple lines if no | or }})
    for m in re.finditer(r"\|\s*(\w[\w-]*)\s*=\s*([^|\n}]+(?:\n[^|\n}]+)*)", params_text):
        key = m.group(1).strip().lower()
        value = m.group(2).strip()
        params[key] = value
    return params


def lint_citation(match) -> dict:
    """Lint a single citation template match."""
    full = match.group(0)
    tmpl_raw = match.group(1)
    params_text = match.group(2)

    tmpl_name = tmpl_raw.strip().lower()

    params = extract_parameters(params_text)

    issues = []

    # Check required parameters
    if tmpl_name in REQUIRED_PARAMS:
        for req in REQUIRED_PARAMS[tmpl_name]:
            if req not in params:
                issues.append(f"missing required: {req}")

    # Check recommended parameters
    if tmpl_name in RECOMMENDED_PARAMS:
        for rec in RECOMMENDED_PARAMS[tmpl_name]:
            if rec not in params:
                issues.append(f"missing recommended: {rec}")

    # Check URL validity if url parameter present
    url = params.get("url", "")
    if url and not url.startswith("http"):
        issues.append(f"suspicious URL: {url[:60]}")

    # Check for archive without access-date
    if "archive-url" in params and "access-date" not in params:
        issues.append("has archive-url but no access-date")

    # Check url-status without archive-url
    if "url-status" in params and "archive-url" not in params:
        issues.append("has url-status but no archive-url")

    # Check for bare DOI (doi without cite journal)
    if "doi" in params and tmpl_name not in ("cite journal", "cite conference"):
        issues.append(f"doi in {tmpl_name} (usually belongs in cite journal)")

    return {
        "template": tmpl_name,
        "url": params.get("url", ""),
        "has_doi": "doi" in params,
        "has_archive": "archive-url" in params,
        "has_access_date": "access-date" in params,
        "param_count": len(params),
        "issues": issues,
        "raw": full[:150],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Parse and validate all citation templates in a Wikipedia page",
    )
    parser.add_argument("page_title", help="Wikipedia page title")
    parser.add_argument("--lang", default="en")
    parser.add_argument("--fix", action="store_true", help="Generate fix suggestions")
    parser.add_argument("--output", choices=["text", "json"], default="text")

    args = parser.parse_args()
    page_title = args.page_title.replace(" ", "_")

    wikitext = fetch_wikitext(page_title, args.lang)
    if not wikitext:
        print("❌ Could not fetch page.", file=sys.stderr)
        sys.exit(1)

    # Find all citation templates
    matches = list(re.finditer(r"\{\{(cite\s+\w+)([^}]*)\}\}", wikitext, re.IGNORECASE))
    bare_urls = re.findall(r"<ref>(https?://[^\s<]+)</ref>", wikitext)

    if not matches and not bare_urls:
        print("No citations found.")
        return

    results = [lint_citation(m) for m in matches]

    # Count stats
    tmpl_counts = Counter(r["template"] for r in results)
    total_issues = sum(len(r["issues"]) for r in results)
    with_archive = sum(1 for r in results if r["has_archive"])
    with_doi = sum(1 for r in results if r["has_doi"])
    with_access_date = sum(1 for r in results if r["has_access_date"])

    if args.output == "json":
        print(json.dumps({
            "page": page_title,
            "lang": args.lang,
            "citation_count": len(results),
            "bare_url_count": len(bare_urls),
            "total_issues": total_issues,
            "templates": dict(tmpl_counts.most_common()),
            "with_archive": with_archive,
            "with_doi": with_doi,
            "with_access_date": with_access_date,
            "citations": results,
            "bare_urls": bare_urls,
        }, indent=2, default=str))
    else:
        print(f"📋 Citation Lint Report: {page_title}")
        print(f"{'═' * 55}")
        print(f"  Template citations: {len(results)}")
        print(f"  Bare URLs:          {len(bare_urls)}")
        print(f"  Total issues:       {total_issues}")
        print(f"  With archive:       {with_archive}")
        print(f"  With DOI:           {with_doi}")
        print(f"  With access-date:   {with_access_date}")
        print()
        print("  Template breakdown:")
        for tmpl, count in tmpl_counts.most_common():
            print(f"    {tmpl}: {count}")

        if bare_urls:
            print(f"\n  ⚠️  Bare URLs ({len(bare_urls)}):")
            for bu in bare_urls[:5]:
                print(f"    • {bu[:100]}")
            if len(bare_urls) > 5:
                print(f"    ... and {len(bare_urls) - 5} more")

        issues_with = [r for r in results if r["issues"]]
        if issues_with:
            print(f"\n  ❌ Citations with issues ({len(issues_with)}):")
            for r in issues_with[:10]:
                url = r["url"][:60] if r["url"] else "(no URL)"
                print(f"    • [{r['template']}] {url}")
                for issue in r["issues"][:3]:
                    print(f"      - {issue}")
            if len(issues_with) > 10:
                print(f"    ... and {len(issues_with) - 10} more")


if __name__ == "__main__":
    main()
