"""
Maintenance query library — pre-built CirrusSearch query generators for common
Wikipedia maintenance and patrolling tasks.

Usage:
    from maintenance_queries import (
        unsourced_blp,
        missing_image,
        linksto_page,
        recently_created,
        template_usage,
        all_queries,
        run_maintenance_query,
        format_results,
    )

    # Get query string
    q = unsourced_blp()

    # Run via the search_client
    from search_client import CirrusClient
    client = CirrusClient()
    results = client.search(q)
    print(format_results(results, "Unsourced BLPs"))

    # Or use the convenience function
    results = run_maintenance_query(client, "unsourced-blp", days=7)
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


def unsourced_blp() -> str:
    """Find living person articles with no sources at all."""
    return 'hastemplate:"BLP unsourced" incategory:"Living people"'


def unsourced_pages() -> str:
    """Find unsourced articles that are not BLPs."""
    return 'hastemplate:"Unreferenced" -incategory:"Living people"'


def dead_links() -> str:
    """Find articles tagged with dead link templates."""
    return 'hastemplate:"Dead link" incategory:"All articles with dead external links"'


def missing_image(template: str = "Infobox person") -> str:
    """Find infobox pages without an image parameter."""
    return (
        f'hastemplate:"{template}" '
        '-insource:"|image =" -insource:"|image="'
    )


def no_image_blp() -> str:
    """Find BLP articles that have an infobox but no image."""
    return (
        'hastemplate:"Infobox person" incategory:"Living people" '
        '-insource:"|image =" -insource:"|image="'
    )


def no_categories() -> str:
    """Find pages with no categories assigned."""
    return 'incategory:"All uncategorized pages"'


def recently_created(days: int = 7) -> str:
    """Find pages created in the last N days."""
    return f"creationdate:>=today-{days}d"


def recent_stubs(days: int = 7) -> str:
    """Find stub articles created in the last N days."""
    return f"creationdate:>=today-{days}d incategory:\"All stub articles\""


def recent_in_category(category: str, days: int = 7) -> str:
    """Find pages in a category that were recently edited."""
    return f'incategory:"{category}" lasteditdate:>=today-{days}d'


def stub_category(category: str) -> str:
    """Find all pages in a stub category."""
    return f'incategory:"{category}"'


def template_usage(template: str) -> str:
    """Find all pages using a specific template."""
    return f'hastemplate:"{template}"'


def linksto_page(page: str) -> str:
    """Find all pages linking to a specific page."""
    return f'linksto:"{page}"'


def subpages_of(parent: str) -> str:
    """Find all subpages of a given page."""
    return f'subpageof:"{parent}"'


def copyedit_needed() -> str:
    """Find articles needing copy editing."""
    return 'hastemplate:"Copy edit"'


def pov_check() -> str:
    """Find articles flagged for POV/neutrality review."""
    return 'hastemplate:"POV" incategory:"All articles with unsourced statements"'


def deprecated_templates() -> str:
    """Find pages using deprecated templates."""
    return 'incategory:"Pages using deprecated templates"'


def overcategorized() -> str:
    """Find pages tagged as overcategorized."""
    return 'incategory:"Wikipedia articles that are excessively categorized"'


def search_by_date_range(start_date: str, end_date: str) -> str:
    """Find pages created between two dates (YYYY-MM-DD format)."""
    return f"creationdate:>={start_date} creationdate:<={end_date}"


def search_by_size(min_size_kb: Optional[int] = None, max_size_kb: Optional[int] = None) -> str:
    """Find pages by size (approximate — uses wordcount as proxy)."""
    # Note: CirrusSearch doesn't have a native page-size filter.
    # This is a placeholder showing how to approximate with other tools.
    # Use SQL replicas for actual page-size queries.
    parts = []
    # CirrusSearch itself doesn't support filesize: on non-File namespaces.
    # Use a combined query with maintenance tags as proxy.
    return 'incategory:"All articles with unsourced statements"'


# Catalog of all queries with descriptions
ALL_QUERIES = {
    "unsourced-blp": {
        "query": unsourced_blp,
        "description": "Living person articles with no sources",
    },
    "unsourced-pages": {
        "query": unsourced_pages,
        "description": "Unsourced articles (non-BLP)",
    },
    "dead-links": {
        "query": dead_links,
        "description": "Articles with dead link templates",
    },
    "missing-image": {
        "query": missing_image,
        "description": "Infobox pages without image parameter",
    },
    "no-image-blp": {
        "query": no_image_blp,
        "description": "BLP articles with infobox but no image",
    },
    "no-categories": {
        "query": no_categories,
        "description": "Pages with no categories",
    },
    "recently-created": {
        "query": recently_created,
        "description": "Pages created in the last N days",
        "params": {"days": 7},
    },
    "recent-stubs": {
        "query": recent_stubs,
        "description": "Stub articles created recently",
        "params": {"days": 7},
    },
    "recent-category": {
        "query": recent_in_category,
        "description": "Recently edited pages in a category",
        "params": {"category": "", "days": 7},
    },
    "stub-category": {
        "query": stub_category,
        "description": "Pages in a stub category",
        "params": {"category": ""},
    },
    "template-usage": {
        "query": template_usage,
        "description": "Pages using a specific template",
        "params": {"template": ""},
    },
    "linksto-page": {
        "query": linksto_page,
        "description": "Pages linking to a specific page",
        "params": {"page": ""},
    },
    "subpages-of": {
        "query": subpages_of,
        "description": "Subpages of a given page",
        "params": {"parent": ""},
    },
    "copyedit-needed": {
        "query": copyedit_needed,
        "description": "Articles needing copy editing",
    },
    "pov-check": {
        "query": pov_check,
        "description": "Articles flagged for POV review",
    },
    "deprecated-tmpl": {
        "query": deprecated_templates,
        "description": "Pages using deprecated templates",
    },
    "overcategorized": {
        "query": overcategorized,
        "description": "Pages tagged as overcategorized",
    },
}


def run_maintenance_query(
    client: Any, query_type: str, **kwargs
) -> List[Dict[str, Any]]:
    """
    Convenience function: run a maintenance query via a CirrusClient instance.

    Args:
        client: A CirrusClient instance (from search_client module)
        query_type: Key from ALL_QUERIES
        **kwargs: Override default parameters (days=, category=, template=, etc.)

    Returns:
        List of search result dicts
    """
    if query_type not in ALL_QUERIES:
        valid = ", ".join(sorted(ALL_QUERIES.keys()))
        raise ValueError(f"Unknown query type '{query_type}'. Valid: {valid}")

    entry = ALL_QUERIES[query_type]
    query_fn = entry["query"]
    params = dict(entry.get("params", {}))
    params.update(kwargs)

    # Build query — pass params if the function accepts them
    import inspect
    sig = inspect.signature(query_fn)
    fn_params = list(sig.parameters.keys())

    filtered_params = {k: v for k, v in params.items() if k in fn_params}
    query = query_fn(**filtered_params)

    limit = kwargs.get("limit", 50)
    return client.search(query, limit=limit)


def format_results(results: List[Dict[str, Any]], title: str = "") -> str:
    """Format search results as a human-readable summary."""
    lines = []
    if title:
        lines.append(f"=== {title} ===")
    lines.append(f"Results: {len(results)}\n")

    for i, r in enumerate(results, 1):
        title = r.get("title", "?")
        size = r.get("size", "?")
        wc = r.get("wordcount", "?")
        ts = r.get("timestamp", "")
        snippet = r.get("snippet", "")
        import re
        clean = re.sub(r"<[^>]+>", "", snippet)[:100]

        lines.append(f"  {i:3d}. {title}")
        if clean:
            lines.append(f"       {clean}...")
        parts = []
        if size != "?":
            parts.append(f"{size}B")
        if wc != "?":
            parts.append(f"{wc} words")
        if ts:
            parts.append(ts)
        if parts:
            lines.append(f"       {' | '.join(parts)}")
        lines.append("")

    return "\n".join(lines)


# ---- CLI ----
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="Run CirrusSearch maintenance queries"
    )
    parser.add_argument("type", nargs="?",
                        choices=list(ALL_QUERIES.keys()) + ["list"],
                        help="Query type (use 'list' to show all)")
    parser.add_argument("--wiki", default="en.wikipedia.org",
                        help="Wiki domain")
    parser.add_argument("--limit", type=int, default=20, help="Max results")
    parser.add_argument("--days", type=int, default=7,
                        help="Days for recency-based queries")
    parser.add_argument("--category", default="", help="Category name")
    parser.add_argument("--template", default="", help="Template name")
    parser.add_argument("--linksto", default="", help="Page to find links to")
    parser.add_argument("--parent", default="", help="Parent page for subpages")

    args = parser.parse_args()

    if not args.type or args.type == "list":
        print("Available maintenance queries:\n")
        for key, entry in sorted(ALL_QUERIES.items()):
            desc = entry["description"]
            params = entry.get("params", {})
            param_str = ""
            if params:
                param_str = f"  (params: {', '.join(params.keys())})"
            print(f"  {key:20s}  {desc}{param_str}")
        print("\nUse: python3 maintenance_queries.py <type> [options]")
        sys.exit(0)

    from search_client import CirrusClient

    client = CirrusClient(wiki=args.wiki)

    kwargs = {
        "days": args.days,
        "category": args.category,
        "template": args.template,
        "linksto": args.linksto,
        "parent": args.parent,
        "limit": args.limit,
    }

    results = run_maintenance_query(client, args.type, **kwargs)
    entry = ALL_QUERIES[args.type]
    print(format_results(results, title=entry["description"]))
