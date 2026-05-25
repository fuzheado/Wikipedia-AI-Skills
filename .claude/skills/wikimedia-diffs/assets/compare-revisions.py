#!/usr/bin/env python3
"""
Revision Comparator — fetch and analyze diffs between Wikipedia page revisions.

Usage:
    python3 compare-revisions.py --from-rev 123456789 --to-rev 123456790
    python3 compare-revisions.py --page "Python (programming language)"
    python3 compare-revisions.py --page "Albert Einstein" --stats
    python3 compare-revisions.py --page "Marie Curie" --report
    python3 compare-revisions.py --page "Paris" --project fr.wikipedia

Dependencies: pip install requests beautifulsoup4
"""

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ requests not installed. Install: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    print("⚠️  beautifulsoup4 not installed. HTML diff parsing disabled.", file=sys.stderr)
    print("   Install: pip install beautifulsoup4 lxml", file=sys.stderr)


USER_AGENT = "DiffSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)"


def get_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def fetch_revision_ids(page: str, project: str = "en.wikipedia.org") -> tuple[int, int]:
    """Fetch the two most recent revision IDs for a page."""
    api_url = f"https://{project}/w/api.php"
    s = get_session()
    rv = s.get(api_url, params={
        "action": "query", "prop": "revisions",
        "titles": page, "rvlimit": "2",
        "rvprop": "ids", "format": "json",
    }).json()

    pages = list(rv.get("query", {}).get("pages", {}).values())
    if not pages:
        raise ValueError(f"Page '{page}' not found")
    revs = pages[0].get("revisions", [])
    if len(revs) < 2:
        raise ValueError(f"Page '{page}' has fewer than 2 revisions")
    return revs[1]["revid"], revs[0]["revid"]


def fetch_diff(from_rev: int = None, to_rev: int = None, page: str = None,
               project: str = "en.wikipedia.org") -> dict:
    """Fetch a diff via the Action API."""
    api_url = f"https://{project}/w/api.php"
    s = get_session()

    if from_rev is not None and to_rev is not None:
        pass
    elif page:
        from_rev, to_rev = fetch_revision_ids(page, project)
    else:
        raise ValueError("Provide --from-rev + --to-rev, or --page")

    diff = s.get(api_url, params={
        "action": "compare",
        "fromrev": from_rev,
        "torev": to_rev,
        "prop": "diff|diffsize|ids|title|size",
        "format": "json",
    }).json()

    if "error" in diff:
        raise ValueError(f"API error: {diff['error'].get('info', 'unknown')}")

    result = diff.get("compare", {})
    result["_from_rev"] = from_rev
    result["_to_rev"] = to_rev
    result["_project"] = project
    return result


def print_stats(cmp: dict):
    """Print structured diff statistics."""
    fromsize = cmp.get("fromsize", 0)
    tosize = cmp.get("tosize", 0)
    diffsize = cmp.get("diffsize", 0)
    diff_html = cmp.get("*", "")

    net = tosize - fromsize

    print("📊 Diff Statistics")
    print(f"   Title:      {cmp.get('fromtitle', '?')}")
    print(f"   From rev:   {cmp.get('fromrevid', '?')}")
    print(f"   To rev:     {cmp.get('torevid', '?')}")
    print()
    print(f"   ┌─ Size")
    print(f"   ├  Page was:    {fromsize:>8,} bytes")
    print(f"   ├  Page is now: {tosize:>8,} bytes")
    print(f"   ├  Net change:  {net:>+8,} bytes")
    print(f"   └  Total churn: {diffsize:>8,} bytes (added + removed)")
    print()

    # Parse HTML diff for additional stats
    if BeautifulSoup and diff_html:
        soup = BeautifulSoup(diff_html, "html.parser")
        insertions = len(soup.find_all("td", class_="diff-addedline"))
        deletions = len(soup.find_all("td", class_="diff-deletedline"))
        changes = len(soup.find_all("span", class_="diffchange"))
        context = len(soup.find_all("td", class_="diff-context"))

        print(f"   ┌─ HTML diff elements")
        print(f"   ├  Insertions:  {insertions}")
        print(f"   ├  Deletions:   {deletions}")
        print(f"   ├  Changes:     {changes}")
        print(f"   └  Context:     {context}")
        print()

    # Risk assessment
    flags = []
    if diffsize > 50000:
        flags.append(("🔴", f"Large churn ({diffsize:,} bytes)"))
    if net < -20000:
        flags.append(("🔴", f"Significant net removal ({-net:,} bytes)"))
    if net > 100000:
        flags.append(("🟡", f"Large addition ({net:,} bytes)"))
    if diffsize > 0 and diffsize < 100:
        flags.append(("✅", "Tiny edit"))
    elif diffsize == 0:
        flags.append(("✅", "No content change"))

    print(f"   ┌─ Assessment")
    for icon, msg in flags:
        print(f"   {icon}  {msg}")
    print()


def print_report(cmp: dict):
    """Print a human-readable diff report from the HTML table."""
    diff_html = cmp.get("*", "")
    if not diff_html:
        print("   (no diff content)")
        return

    if not BeautifulSoup:
        print("   (install beautifulsoup4 for HTML diff parsing)")
        return

    soup = BeautifulSoup(diff_html, "html.parser")

    # Find all rows in the diff table
    rows = soup.find_all("tr")
    if not rows:
        print("   (no rows in diff table)")
        return

    print("📋 Diff Report")
    print(f"   {'=' * 60}")

    for row in rows:
        # Line number headers
        lineno = row.find("td", class_="diff-lineno")
        if lineno:
            print(f"\n  ── Line {lineno.get_text(strip=True)} ──")
            continue

        # Deleted line
        deleted = row.find("td", class_="diff-deletedline")
        added = row.find("td", class_="diff-addedline")

        if deleted and added:
            old_text = deleted.get_text(separator=" ", strip=True)
            new_text = added.get_text(separator=" ", strip=True)
            if old_text != new_text:
                print(f"  \033[31m- {old_text[:200]}\033[0m")
                print(f"  \033[32m+ {new_text[:200]}\033[0m")
            else:
                print(f"    {old_text[:200]}")
        elif deleted:
            text = deleted.get_text(separator=" ", strip=True)
            print(f"  \033[31m- {text[:200]}\033[0m")
        elif added:
            text = added.get_text(separator=" ", strip=True)
            print(f"  \033[32m+ {text[:200]}\033[0m")
        else:
            # Context or other row
            context = row.find("td", class_="diff-context")
            if context:
                text = context.get_text(separator=" ", strip=True)
                if text:
                    print(f"    {text[:200]}")

    print()


def print_json(cmp: dict):
    """Output summary as JSON."""
    output = {
        "title": cmp.get("fromtitle"),
        "from_revid": cmp.get("fromrevid"),
        "to_revid": cmp.get("torevid"),
        "fromsize": cmp.get("fromsize"),
        "tosize": cmp.get("tosize"),
        "diffsize": cmp.get("diffsize"),
        "net_change": cmp.get("tosize", 0) - cmp.get("fromsize", 0),
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Fetch and analyze Wikipedia diffs")
    parser.add_argument("--from-rev", type=int, help="Source revision ID")
    parser.add_argument("--to-rev", type=int, help="Target revision ID")
    parser.add_argument("--page", help="Page title (compares latest two revisions)")
    parser.add_argument("--project", default="en.wikipedia.org")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--report", action="store_true", help="Show diff report")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--save-html", help="Save raw HTML diff to file")

    args = parser.parse_args()

    if not args.from_rev and not args.page:
        parser.error("Provide --from-rev + --to-rev, or --page")
    if not args.stats and not args.report and not args.json and not args.save_html:
        args.stats = True
        args.report = True

    fetch_kwargs = {"page": args.page, "project": args.project}
    if args.from_rev:
        fetch_kwargs["from_rev"] = args.from_rev
        fetch_kwargs["to_rev"] = args.to_rev

    print(f"📄 Fetching diff from {args.project}...", file=sys.stderr)
    cmp = fetch_diff(**fetch_kwargs)

    if args.json:
        print_json(cmp)
    if args.stats:
        print_stats(cmp)
    if args.report:
        print_report(cmp)
    if args.save_html:
        html = cmp.get("*", "")
        Path(args.save_html).write_text(html, encoding="utf-8")
        print(f"💾 HTML diff saved to: {args.save_html}", file=sys.stderr)


if __name__ == "__main__":
    main()
