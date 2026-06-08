#!/usr/bin/env python3
"""
category-intersect.py — Find pages at the intersection of two or more Wikipedia categories.

Uses the PetScan API (https://petscan.wmflabs.org/) to find pages that belong
to all specified categories simultaneously.

Usage:
    python3 category-intersect.py "Physicists" "German scientists"
    python3 category-intersect.py "Physicists" "German scientists" --limit 20
    python3 category-intersect.py "Physics" "20th-century science" --depth 2
    python3 category-intersect.py "American films" "Comedy films" --format json
    python3 category-intersect.py "Novels by Jane Austen" --format csv
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
import time

USER_AGENT = "WikipediaCategoriesSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills) CategoryIntersect"
PETSCAN_URL = "https://petscan.wmflabs.org/"


def intersect_categories(categories, depth=0, limit=100, lang="en", project="wikipedia"):
    """Find pages at the intersection of all given categories via PetScan.

    PetScan treats multiple categories in the 'categories' parameter as a
    union by default. For intersection, we set 'combination' to 'subset'
    union (pages in ALL categories), or use 'intersection' mode.

    Args:
        categories: List of category names (without "Category:" prefix)
        depth: How deep to recurse into subcategories (0 = no recursion)
        limit: Maximum results
        lang: Language code
        project: Wikimedia project

    Returns:
        List of page dicts with 'title' and optionally 'pageid', 'namespace'
    """
    params = {
        "language": lang,
        "project": project,
        "categories": "|".join(categories),
        "combination": "subset",  # Pages must be in ALL categories
        "ns": [0],                # Main namespace only (articles)
        "edgescroll": "true",     # Infinite scroll
        "depth": depth,
        "doit": "Do it!",
    }

    if limit:
        params["limit"] = limit

    # Build the query string with multiple values for ns
    query_parts = []
    for key, value in params.items():
        if isinstance(value, list):
            for v in value:
                query_parts.append(f"{key}={v}")
        else:
            query_parts.append(f"{key}={urllib.parse.quote(str(value))}")

    query_string = "&".join(query_parts)

    # PetScan returns JSON when format=json is set via the Accept header
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
        print(f"❌ PetScan HTTP Error: {e.code}", file=sys.stderr)
        print(f"   Response: {e.read().decode('utf-8', errors='replace')[:500]}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ PetScan Connection Error: {e.reason}", file=sys.stderr)
        # Fallback: try manual API chaining
        print("   Falling back to manual API-based intersection...", file=sys.stderr)
        return _manual_intersect(categories, depth, limit, lang)

    # PetScan response format: {"*": [results]}
    results = data.get("*", [])
    return results


def _manual_intersect(categories, depth, limit, lang):
    """Fallback: manually find intersection by fetching members of each
    category via the MW Action API and computing set intersection.

    This is slower and less powerful than PetScan but works without
    depending on an external service.
    """
    import urllib.request, urllib.parse, json

    api_url = f"https://{lang}.wikipedia.org/w/api.php"

    def get_members(category):
        """Get all page titles in a category."""
        members = set()
        cmcontinue = None
        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmtype": "page",
                "cmlimit": "max",
                "format": "json",
                "cmnamespace": "0",
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            query = urllib.parse.urlencode(params)
            req = urllib.request.Request(f"{api_url}?{query}", headers={"User-Agent": USER_AGENT})

            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            except Exception:
                break

            for page in data.get("query", {}).get("categorymembers", []):
                members.add(page.get("title", ""))

            cmcontinue = data.get("continue", {}).get("cmcontinue")
            if not cmcontinue:
                break

            time.sleep(0.2)  # Rate limiting

        return members

    # Get members of first category, then intersect with each subsequent one
    if not categories:
        return []

    print(f"   Fetching members of category 1: {categories[0]}...", file=sys.stderr)
    intersection = get_members(categories[0])

    for i, cat in enumerate(categories[1:], 2):
        print(f"   Fetching members of category {i}: {cat}...", file=sys.stderr)
        members = get_members(cat)
        intersection &= members
        if not intersection:
            break

    # Format as PetScan-compatible results
    results = [{"title": title} for title in sorted(intersection)[:limit]]
    return results


def display_table(results, categories):
    """Display results as a formatted table."""
    if not results:
        print(f"ℹ️  No pages found in the intersection of: {', '.join(categories)}")
        return

    print(f"\n{'='*70}")
    print(f"  Intersection of: {' ∩ '.join(categories)}")
    print(f"{'='*70}")
    for i, page in enumerate(results, 1):
        title = page.get("title", page.get("page", ""))
        print(f"  {i:<4} {title}")
    print(f"{'='*70}")
    print(f"  Total: {len(results)} pages")
    print()


def display_json(results):
    """Output as JSON."""
    print(json.dumps(results, indent=2))


def display_csv(results):
    """Output as CSV."""
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["#", "Title"])
    for i, page in enumerate(results, 1):
        title = page.get("title", page.get("page", ""))
        writer.writerow([i, title])
    print(output.getvalue().strip())


def main():
    parser = argparse.ArgumentParser(
        description="Find pages at the intersection of two or more Wikipedia categories"
    )
    parser.add_argument("categories", nargs="+", help="Category names (without Category: prefix)")
    parser.add_argument("--limit", type=int, default=100, help="Max results (default: 100)")
    parser.add_argument("--depth", type=int, default=0, help="Recurse into subcategories (depth, default: 0)")
    parser.add_argument("--lang", default="en", help="Language code (default: en)")
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table", help="Output format")
    parser.add_argument("--no-petscan", action="store_true", help="Skip PetScan, use manual API intersection")

    args = parser.parse_args()

    if len(args.categories) < 1:
        print("❌ At least one category is required. For intersection, use two or more.", file=sys.stderr)
        sys.exit(1)

    if args.no_petscan:
        results = _manual_intersect(args.categories, args.depth, args.limit, args.lang)
    else:
        results = intersect_categories(args.categories, args.depth, args.limit, args.lang)

    if args.format == "json":
        display_json(results)
    elif args.format == "csv":
        display_csv(results)
    else:
        display_table(results, args.categories)


if __name__ == "__main__":
    main()
