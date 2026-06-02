#!/usr/bin/env python3
"""
Talk Archive Search — search across a Wikipedia talk page and all its archives
for a keyword or phrase.

Searches the main talk page and each archive subpage, reporting which pages
contain matches and showing matching snippets.

Usage:
    python3 talk-archive-search.py "Albert Einstein" "birth date"
    python3 talk-archive-search.py "Talk:Albert Einstein" "Nobel"
    python3 talk-archive-search.py "Python (programming language)" "indentation" --json
"""

import sys
import re
import json
import urllib.request
import urllib.parse
import argparse

USER_AGENT = "TalkArchiveSearch/1.0 (https://en.wikipedia.org; demo@example.com) WikiSkills"
API = "https://en.wikipedia.org/w/api.php"


def api_request(params):
    """Make an API request and return parsed JSON."""
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_archives(talk_page):
    """Find all archive subpages for a talk page via prefixsearch API."""
    prefix = f"{talk_page}/Archive"
    data = api_request({
        "action": "query",
        "list": "prefixsearch",
        "pssearch": prefix,
        "pslimit": 100,
        "format": "json",
    })
    results = data.get("query", {}).get("prefixsearch", [])
    return [r["title"] for r in results if r["title"] != talk_page]


def fetch_page_content(page_title):
    """Fetch raw wikitext content of a page."""
    data = api_request({
        "action": "query",
        "prop": "revisions",
        "titles": page_title,
        "rvslots": "*",
        "rvprop": "content",
        "format": "json",
    })
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if "missing" not in page:
            revs = page.get("revisions", [])
            if revs:
                return revs[0].get("slots", {}).get("main", {}).get("*", "")
    return ""


def search_content(content, keyword, case_sensitive=False):
    """Search content for a keyword and return matching lines with context."""
    if not content:
        return []
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(re.escape(keyword), flags)
    lines = content.split("\n")
    matches = []
    for i, line in enumerate(lines):
        if pattern.search(line):
            # Get context: up to 3 lines before and after
            start = max(0, i - 3)
            end = min(len(lines), i + 4)
            snippet = "\n".join(lines[start:end])
            # Truncate long lines
            if len(snippet) > 500:
                snippet = snippet[:500] + "..."
            matches.append({
                "line": i + 1,
                "snippet": snippet.strip(),
            })
    return matches


def main():
    parser = argparse.ArgumentParser(description="Search Wikipedia talk pages and archives")
    parser.add_argument("title", help="Article title or talk page to search")
    parser.add_argument("keyword", help="Word or phrase to search for")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--case-sensitive", action="store_true",
                        help="Case-sensitive search")
    args = parser.parse_args()

    # Normalize to talk page
    talk_page = args.title
    if not talk_page.startswith("Talk:"):
        talk_page = f"Talk:{talk_page}"

    # Find archives
    archives = find_archives(talk_page)

    # Pages to search: main talk page + all archives
    pages_to_search = [talk_page] + archives

    results = []
    for page in pages_to_search:
        content = fetch_page_content(page)
        if not content:
            continue
        matches = search_content(content, args.keyword, args.case_sensitive)
        if matches:
            results.append({
                "page": page,
                "match_count": len(matches),
                "matches": matches,
            })

    if args.json:
        print(json.dumps({
            "keyword": args.keyword,
            "talk_page": talk_page,
            "archives_found": len(archives),
            "pages_searched": len(pages_to_search),
            "pages_with_matches": len(results),
            "results": results,
        }, indent=2))
    else:
        print(f"Keyword: \"{args.keyword}\"")
        print(f"Talk page: {talk_page}")
        if archives:
            print(f"Archives: {len(archives)} found")
        else:
            print("Archives: none found")
        print(f"Pages with matches: {len(results)} of {len(pages_to_search)} searched")
        print()

        if not results:
            print("No matches found.")
            return

        for r in results:
            print(f"── {r['page']} ({r['match_count']} match(es)) ──")
            print()
            for m in r["matches"][:5]:
                # Show snippet with keyword highlighted
                snippet = m["snippet"]
                highlighted = re.sub(
                    re.escape(args.keyword),
                    lambda m: f"\033[1;33m{m.group(0)}\033[0m",
                    snippet,
                    flags=0 if args.case_sensitive else re.IGNORECASE
                )
                print(f"  Line {m['line']}:")
                for sl in highlighted.split("\n"):
                    print(f"    {sl}")
                print()
            if len(r["matches"]) > 5:
                print(f"  ... and {len(r['matches']) - 5} more matches")
            print()


if __name__ == "__main__":
    main()
