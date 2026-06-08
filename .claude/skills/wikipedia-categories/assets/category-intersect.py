#!/usr/bin/env python3
"""
category-intersect.py — Find pages that belong to ALL specified Wikipedia categories.

USAGE:
  python3 category-intersect.py <category> [<category> ...] [options]

ARGUMENTS:
  category               One or more category names (without "Category:" prefix).
                         Only pages in ALL specified categories are returned.

OPTIONS:
  --limit N              Maximum results (default: 100)
  --depth N              Recurse into subcategories N levels deep (default: 0)
  --lang LANG            Wikipedia language code (default: en)
  --format FORMAT        Output format: table (default), json, or csv
  --no-petscan           Skip PetScan, use manual MW API intersection (slower)

EXAMPLES:
  # Basic intersection (pages in BOTH categories)
  python3 category-intersect.py Physicists "German scientists"

  # Three-way intersection
  python3 category-intersect.py Physicists "German scientists" "Nobel laureates"

  # With subcategory recursion
  python3 category-intersect.py Physics "20th-century science" --depth 2

  # Machine-readable output
  python3 category-intersect.py "American films" "Comedy films" --format json

  # CSV for spreadsheet import
  python3 category-intersect.py "Novels by Jane Austen" --format csv

  # Manual fallback (no external service dependency)
  python3 category-intersect.py "1879 births" --no-petscan

HOW IT WORKS:
  Primary path: Uses PetScan (https://petscan.wmflabs.org/), an external tool
  that can query Wikipedia categories with intersection, template filters,
  and namespace constraints. PetScan handles all the API work server-side.

  Fallback path (--no-petscan): Calls list=categorymembers on each category,
  computes set intersection locally. Slower (N sequential round-trips) but
  works without depending on an external service.

  In all cases, pages must be in EVERY specified category (AND logic).
  For union (OR logic) or complement (NOT), use the PetScan web UI directly.

OUTPUT (table mode):
  ======================================================================
    Intersection of: Physicists ∩ German scientists
  ======================================================================
    1     Albert Einstein
    2     Max Planck
    3     Werner Heisenberg
  ======================================================================
    Total: 18 pages
  ======================================================================

  See also:
    - scripts/category-tree.sh — explore a category tree
    - assets/category-inspector.py — inspect categories on a single article
"""

import argparse
import csv
import io
import json
import sys
import textwrap
import time
import urllib.parse
import urllib.request

USER_AGENT = (
    "WikipediaCategoriesSkill/1.0 "
    "(https://github.com/fuzheado/Wikipedia-AI-Skills) "
    "CategoryIntersect"
)
PETSCAN_URL = "https://petscan.wmflabs.org/"


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


def intersect_via_petscan(categories, depth=0, limit=100, lang="en", project="wikipedia"):
    """Find pages at the intersection of all given categories via PetScan.

    PetScan is an external Wikimedia query tool that supports category
    intersection, template filters, namespace constraints, and more.

    Args:
        categories: List of category names (without "Category:" prefix)
        depth: How deep to recurse into subcategories (0 = no recursion)
        limit: Maximum results
        lang: Language code (e.g., "en", "de", "fr")
        project: Wikimedia project (default: "wikipedia")

    Returns:
        List of page dicts with 'title' key
    """
    params = {
        "language": lang,
        "project": project,
        "categories": "|".join(categories),
        "combination": "subset",  # AND logic — pages in ALL categories
        "ns": [0],                # Main namespace only (articles)
        "edgescroll": "true",     # Infinite scroll mode
        "depth": depth,
        "doit": "Do it!",
    }

    if limit:
        params["limit"] = limit

    query_parts = []
    for key, value in params.items():
        if isinstance(value, list):
            for v in value:
                query_parts.append(f"{key}={v}")
        else:
            query_parts.append(f"{key}={urllib.parse.quote(str(value))}")

    query_string = "&".join(query_parts)

    req = urllib.request.Request(
        f"{PETSCAN_URL}?{query_string}",
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")[:500]
        print(f"❌ PetScan HTTP Error {e.code}", file=sys.stderr)
        print(f"   Response: {error_body}", file=sys.stderr)
        print(
            "   Falling back to manual API-based intersection...",
            file=sys.stderr,
        )
        return _manual_intersect(categories, depth, limit, lang)
    except urllib.error.URLError as e:
        print(f"❌ PetScan Connection Error: {e.reason}", file=sys.stderr)
        print(
            "   Falling back to manual API-based intersection...",
            file=sys.stderr,
        )
        return _manual_intersect(categories, depth, limit, lang)

    return data.get("*", [])


def _manual_intersect(categories, depth, limit, lang):
    """Fallback: compute intersection via direct MW API calls.

    Calls list=categorymembers for each category separately, then computes
    the set intersection locally. Slower (N sequential round-trips) but
    works without PetScan.

    Args:
        categories: List of category names
        depth: Ignored in fallback (always non-recursive)
        limit: Maximum results
        lang: Language code

    Returns:
        List of page dicts with 'title' key
    """
    if not categories:
        return []

    api_url = f"https://{lang}.wikipedia.org/w/api.php"

    def get_members(category_name):
        """Get all page titles in a single category."""
        members = set()
        cmcontinue = None
        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category_name}",
                "cmtype": "page",
                "cmlimit": "max",
                "format": "json",
                "cmnamespace": "0",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            query = urllib.parse.urlencode(params)
            req = urllib.request.Request(
                f"{api_url}?{query}", headers={"User-Agent": USER_AGENT}
            )

            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                print(
                    f"   ⚠️  HTTP {e.code} fetching '{category_name}', "
                    f"stopping",
                    file=sys.stderr,
                )
                break
            except urllib.error.URLError as e:
                print(
                    f"   ⚠️  Connection error fetching '{category_name}': "
                    f"{e.reason}",
                    file=sys.stderr,
                )
                break

            for page in data.get("query", {}).get("categorymembers", []):
                members.add(page.get("title", ""))

            cmcontinue = data.get("continue", {}).get("cmcontinue")
            if not cmcontinue:
                break

            time.sleep(0.2)  # Rate limiting between batches

        return members

    print(
        f"   Fetching members of category 1: {categories[0]}...",
        file=sys.stderr,
    )
    intersection = get_members(categories[0])

    for i, cat in enumerate(categories[1:], 2):
        print(
            f"   Fetching members of category {i}: {cat}...",
            file=sys.stderr,
        )
        members = get_members(cat)
        intersection &= members
        if not intersection:
            print("   No overlap found — intersection is empty.", file=sys.stderr)
            break

    return [{"title": t} for t in sorted(intersection)][:limit]


def display_table(results, categories):
    """Print results as a formatted text table."""
    if not results:
        intersection_label = " ∩ ".join(categories)
        print(f"ℹ️  No pages found in the intersection of: {intersection_label}")
        return

    print()
    print("=" * 78)
    print(f"  Intersection of: {' ∩ '.join(categories)}")
    print("=" * 78)
    for i, page in enumerate(results, 1):
        title = page.get("title", page.get("page", ""))
        print(f"  {i:<4} {title}")
    print("=" * 78)
    print(f"  Total: {len(results)} pages")
    print()


def display_json(results):
    """Print results as formatted JSON."""
    print(json.dumps(results, indent=2, ensure_ascii=False))


def display_csv(results):
    """Print results as CSV."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["#", "Title"])
    for i, page in enumerate(results, 1):
        title = page.get("title", page.get("page", ""))
        writer.writerow([i, title])
    print(output.getvalue().strip())


def main():
    parser = argparse.ArgumentParser(
        prog="category-intersect.py",
        description=(
            "Find pages that belong to ALL specified Wikipedia categories "
            "(set intersection). Uses PetScan by default with automatic "
            "fallback to the MW Action API."
        ),
        formatter_class=RawFormatter,
        add_help=False,
    )

    parser.add_argument(
        "categories",
        nargs="*",
        metavar="category",
        help="Category names (without Category: prefix). "
        "Supply 2+ for intersection, or 1 to list all pages in one category.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum results (default: 100)",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=0,
        help="Recurse into subcategories N levels deep (default: 0 = no recursion)",
    )
    parser.add_argument(
        "--lang",
        default="en",
        help="Wikipedia language code (default: en). "
        "Examples: de, fr, es, ja, simple",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Output format (default: table). "
        "json for machine processing, csv for spreadsheets",
    )
    parser.add_argument(
        "--no-petscan",
        action="store_true",
        help="Skip PetScan, use direct MW Action API calls. "
        "Slower but no external service dependency",
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

    if len(args.categories) < 1:
        print(
            "❌ At least one category is required.",
            file=sys.stderr,
        )
        print(
            "   For intersection, supply two or more: "
            "python3 category-intersect.py Physicists Germans",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.no_petscan:
        results = _manual_intersect(
            args.categories, args.depth, args.limit, args.lang
        )
    else:
        results = intersect_via_petscan(
            args.categories, args.depth, args.limit, args.lang
        )

    if args.format == "json":
        display_json(results)
    elif args.format == "csv":
        display_csv(results)
    else:
        display_table(results, args.categories)


if __name__ == "__main__":
    main()
