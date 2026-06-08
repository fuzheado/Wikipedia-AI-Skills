#!/usr/bin/env python3
"""
category-inspector.py — Fetch all categories for a Wikipedia article with metadata.

Usage:
    python3 category-inspector.py Albert_Einstein
    python3 category-inspector.py "Albert Einstein"
    python3 category-inspector.py Albert_Einstein --show-hidden
    python3 category-inspector.py Albert_Einstein --lang de
    python3 category-inspector.py Albert_Einstein --format json

Outputs a table of categories with: name, sort key, hidden status, namespace.
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

USER_AGENT = "WikipediaCategoriesSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills) CategoryInspector"
API_URL = "https://{lang}.wikipedia.org/w/api.php"


def fetch_categories(title, lang="en", show_hidden=False):
    """Fetch all categories for a given article title."""
    params = {
        "action": "query",
        "prop": "categories",
        "titles": title,
        "format": "json",
        "cllimit": "max",
        "clprop": "sortkey|hidden",
    }

    if not show_hidden:
        params["clshow"] = "!hidden"

    all_categories = []
    cmcontinue = None

    while True:
        if cmcontinue:
            params["clcontinue"] = cmcontinue

        url = API_URL.format(lang=lang)
        query_string = urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{url}?{query_string}", headers={"User-Agent": USER_AGENT})

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error: {e.code} {e.reason}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"❌ Connection Error: {e.reason}", file=sys.stderr)
            sys.exit(1)

        query = data.get("query", {})
        pages = query.get("pages", {})

        for page_id, page_data in pages.items():
            if page_id == "-1":
                print(f"❌ Page not found: {title}", file=sys.stderr)
                sys.exit(1)
            categories = page_data.get("categories", [])
            all_categories.extend(categories)

        if "-1" in pages:
            print(f"❌ Page not found: {title}", file=sys.stderr)
            sys.exit(1)

        cmcontinue = data.get("continue", {}).get("clcontinue")
        if not cmcontinue:
            break

    return all_categories


def display_table(categories, title):
    """Display categories in a formatted table."""
    if not categories:
        print(f"ℹ️  No categories found for '{title}'.")
        return

    print(f"\n{'='*70}")
    print(f"  Categories for: {title}")
    print(f"{'='*70}")
    print(f"{'#':<4} {'Category':<50} {'Sort Key':<15} {'Hidden'}")
    print(f"{'-'*4} {'-'*50} {'-'*15} {'-'*6}")

    for i, cat in enumerate(categories, 1):
        # Extract category name from full title
        title_full = cat.get("title", "")
        cat_name = title_full.replace("Category:", "", 1) if title_full.startswith("Category:") else title_full

        sortkey = cat.get("sortkeyprefix", "")
        hidden = "🔒" if cat.get("hidden", "") else ""

        print(f"{i:<4} {cat_name:<50} {sortkey:<15} {hidden}")

    print(f"{'='*70}")
    print(f"  Total: {len(categories)} categories")
    print()


def display_json(categories):
    """Output categories as JSON."""
    print(json.dumps(categories, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Fetch all categories for a Wikipedia article with metadata"
    )
    parser.add_argument("title", help="Article title (e.g., Albert_Einstein)")
    parser.add_argument("--show-hidden", action="store_true", help="Include hidden categories")
    parser.add_argument("--lang", default="en", help="Language code (default: en)")
    parser.add_argument("--format", choices=["table", "json"], default="table", help="Output format")

    args = parser.parse_args()

    # Normalize title: spaces to underscores
    title = args.title.replace(" ", "_")

    categories = fetch_categories(title, args.lang, args.show_hidden)

    if args.format == "json":
        display_json(categories)
    else:
        display_table(categories, title)


if __name__ == "__main__":
    main()
