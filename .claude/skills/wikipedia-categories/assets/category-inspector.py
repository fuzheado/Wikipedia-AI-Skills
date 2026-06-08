#!/usr/bin/env python3
"""
category-inspector.py — Fetch all categories for a Wikipedia article with metadata.

USAGE:
  python3 category-inspector.py <title> [options]

ARGUMENTS:
  title                  Article title (e.g., "Albert_Einstein" or "Albert Einstein")

OPTIONS:
  --show-hidden          Include hidden maintenance categories
  --lang LANG            Wikipedia language code (default: en)
  --format FORMAT        Output format: table (default) or json

EXAMPLES:
  python3 category-inspector.py Albert_Einstein
  python3 category-inspector.py "Albert Einstein"
  python3 category-inspector.py Albert_Einstein --show-hidden
  python3 category-inspector.py Albert_Einstein --lang de
  python3 category-inspector.py Albert_Einstein --format json

HOW IT WORKS:
  Calls the MediaWiki Action API (prop=categories) which returns a list of
  all categories an article belongs to. Handles pagination automatically
  (up to 500 per page via cllimit=max). The response includes sort keys
  (sortkeyprefix) and hidden status for each category.

OUTPUT (table mode):
  #    Category                                            Sort Key        Hidden
  ---- -------------------------------------------------- --------------- ------
  1    Swiss physicists                                   Einstein, Albert
  2    People from Ulm                                    Einstein, Albert
  3    Articles with unsourced statements                 Einstein, Albert  🔒

  The 🔒 icon marks hidden categories (maintenance tracking, not shown
  to readers by default). In JSON mode, the sortkeyprefix and hidden
  fields are machine-readable.

  See also:
    - scripts/category-tree.sh — explore a category tree
    - assets/category-intersect.py — find pages in multiple categories
"""

import argparse
import json
import sys
import textwrap
import urllib.parse
import urllib.request

USER_AGENT = (
    "WikipediaCategoriesSkill/1.0 "
    "(https://github.com/fuzheado/Wikipedia-AI-Skills) "
    "CategoryInspector"
)
API_URL = "https://{lang}.wikipedia.org/w/api.php"


class RawFormatter(argparse.HelpFormatter):
    """Preserves literal newlines and tabs in help text."""

    def _fill_text(self, text, width, indent):
        return "\n".join(
            textwrap.fill(line, width, subsequent_indent=indent)
            if not line.startswith("  ") and line.strip()
            else line
            for line in text.splitlines()
        )

    def _split_lines(self, text, width):
        return text.splitlines()


def fetch_categories(title, lang="en", show_hidden=False):
    """Fetch all categories for a given article title.

    Uses prop=categories with cllimit=max, handles pagination via
    clcontinue automatically.

    Args:
        title: Article title with underscores (e.g. "Albert_Einstein")
        lang: Wikipedia language code (e.g. "en", "de", "fr")
        show_hidden: If True, include hidden maintenance categories

    Returns:
        List of category dicts with keys: title, sortkeyprefix, hidden

    Raises:
        SystemExit: On HTTP errors or page-not-found
    """
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
    clcontinue = None

    while True:
        if clcontinue:
            params["clcontinue"] = clcontinue

        url = API_URL.format(lang=lang)
        query_string = urllib.parse.urlencode(params)
        req = urllib.request.Request(
            f"{url}?{query_string}", headers={"User-Agent": USER_AGENT}
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"❌ HTTP Error {e.code}: {e.reason}", file=sys.stderr)
            print(f"   URL: {url}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"❌ Connection Error: {e.reason}", file=sys.stderr)
            sys.exit(1)

        pages = data.get("query", {}).get("pages", {})

        for page_id, page_data in pages.items():
            if page_id == "-1":
                print(f"❌ Page not found: {title}", file=sys.stderr)
                print(
                    "   Check the spelling and language code.",
                    file=sys.stderr,
                )
                sys.exit(1)
            all_categories.extend(page_data.get("categories", []))

        clcontinue = data.get("continue", {}).get("clcontinue")
        if not clcontinue:
            break

    return all_categories


def display_table(categories, title):
    """Print categories as a formatted text table."""
    if not categories:
        print(f"ℹ️  No categories found for '{title}'.")
        return

    print()
    print("=" * 78)
    print(f"  Categories for: {title}")
    print("=" * 78)
    print(f"{'#':<4} {'Category':<55} {'Sort Key':<15} {'Hidden'}")
    print("-" * 78)

    for i, cat in enumerate(categories, 1):
        title_full = cat.get("title", "")
        cat_name = (
            title_full.replace("Category:", "", 1)
            if title_full.startswith("Category:")
            else title_full
        )
        sortkey = cat.get("sortkeyprefix", "")
        hidden = "🔒" if cat.get("hidden", "") else ""
        # Truncate long category names for alignment
        display_name = cat_name if len(cat_name) <= 54 else cat_name[:51] + "..."
        print(f"{i:<4} {display_name:<55} {sortkey:<15} {hidden}")

    print("=" * 78)
    print(f"  Total: {len(categories)} categories")
    print()


def display_json(categories):
    """Print categories as formatted JSON."""
    print(json.dumps(categories, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(
        prog="category-inspector.py",
        description=(
            "Fetch all categories for a Wikipedia article with metadata "
            "(sort keys, hidden status). Handles pagination automatically."
        ),
        formatter_class=RawFormatter,
        add_help=False,
    )

    parser.add_argument(
        "title",
        nargs="?",
        help="Article title (e.g., Albert_Einstein)",
    )
    parser.add_argument(
        "--show-hidden",
        action="store_true",
        help="Include hidden maintenance categories (e.g., "
        "Category:Articles with unsourced statements)",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Wikipedia language code (default: en). "
        "Examples: de, fr, es, ja, simple",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format: table with sort keys and hidden icons, "
        "or raw JSON for machine processing (default: table)",
    )
    parser.add_argument(
        "--help",
        action="help",
        default=argparse.SUPPRESS,
        help="Show this help message and exit",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        print()
        print(__doc__.split("HOW IT WORKS")[0])
        sys.exit(0)

    args = parser.parse_args()

    title = args.title.replace(" ", "_")
    categories = fetch_categories(title, args.lang, args.show_hidden)

    if args.format == "json":
        display_json(categories)
    else:
        display_table(categories, title)


if __name__ == "__main__":
    main()
