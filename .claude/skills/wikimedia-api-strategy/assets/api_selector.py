"""
Wikipedia API Strategy Selector — importable module for agents.

Recommends the best Wikimedia API or tool for a given task, based on
task type, scale, and constraints.

Usage:
    from api_selector import recommend

    # Auto-detect from free-text description
    result = recommend("pageviews for 50 physics articles")
    print(result["method"])       # "sql"
    print(result["reason"])       # "100-1000× faster than API for bulk analytics"

    # Explicit task specification
    result = recommend("read single page")
    print(result["method"])       # "rest"
    print(result["endpoint"])     # "/page/summary/{title}"

    # Compare two approaches
    comparison = compare("api", "sql")
    print(comparison["winner"])   # "sql"
"""

import re
from typing import Optional


def classify_task(description: str) -> str:
    """Classify a task description into a category.
    
    Args:
        description: Free-text description of the task.
    
    Returns:
        One of: 'read', 'batch', 'analytics', 'realtime', 'edit', 'graph', 'patrol', 'unknown'
    """
    desc = description.lower()

    # Priority order matters — check more specific patterns first
    patterns = [
        ("patrol", r'patrol|triage|new.page|unreviewed|pagetriage'),
        ("realtime", r'realtime|real.time|live\b|stream|monitor|watch|recent\s+change|event'),
        ("edit", r'edit|write|create|update|delete|bot\b|save|upload|migrat|replace'),
        ("graph", r'graph|relation|sparql|wikidata|connect|linked|semantic|property|qid\b|query.*item'),
        ("analytics", r'analytics|aggregate|count|stats|statistics|top\b|rank|average|report|correlat|distribut'),
        ("batch", r'batch|bulk|many|multiple|list\b|all\b|categor|template|500|every\s+page|all\s+articles'),
        ("read", r'read|summary|content|page\b|article\b|single|fetch|get\b|lookup|retrieve'),
    ]

    for category, pattern in patterns:
        if re.search(pattern, desc):
            return category

    return "unknown"


def recommend(description: str, has_db_access: Optional[bool] = None,
              num_items: Optional[int] = None) -> dict:
    """Recommend the best API/tool for a given task.
    
    Args:
        description: Free-text task description.
        has_db_access: Whether Toolforge database access is available.
                       If None, recommendations that require DB will note this.
        num_items: Number of items involved (if known).
                   If None, inferred from description keywords.
    
    Returns:
        dict with keys: method, endpoint, reason, alternatives, category
    """
    category = classify_task(description)
    desc_lower = description.lower()

    # Infer item count from description
    if num_items is None:
        if re.search(r'\b(one|single|a\s+|this\s+)\b', desc_lower):
            num_items = 1
        elif re.search(r'\b(ten|few|several|dozen)\b', desc_lower):
            num_items = 10
        elif re.search(r'\b(hundred|100|200|300|400)\b', desc_lower):
            num_items = 100
        elif re.search(r'\b(500|thousand|1000)\b', desc_lower):
            num_items = 500
        elif re.search(r'\b(bulk|all|every|entire|massive)\b', desc_lower):
            num_items = 5000
        else:
            num_items = 1  # default: assume single

    result = {
        "category": category,
        "description": description,
        "num_items": num_items,
        "has_db_access": has_db_access,
    }

    if category == "read" or (category == "unknown" and num_items == 1):
        if re.search(r'wikitext|raw\s+source|markup|wiki\s+text|template\s+code', desc_lower):
            result["method"] = "action_api"
            result["endpoint"] = "action=parse&prop=wikitext"
            result["url"] = "https://en.wikipedia.org/w/api.php"
            result["reason"] = "REST API does not expose raw wikitext. Action API is the only option."
            result["alternatives"] = []
        else:
            result["method"] = "rest"
            result["endpoint"] = "/page/summary/{title}"
            result["url"] = "https://en.wikipedia.org/api/rest_v1/"
            result["reason"] = "Fastest and simplest for single page reads. Returns clean JSON."
            result["alternatives"] = [
                {"method": "action_api", "why": "If you need raw wikitext instead of rendered content"}
            ]

    elif category == "batch":
        if num_items and num_items > 500:
            result["method"] = "sql"
            result["endpoint"] = "SSH tunnel to enwiki.analytics.db.svc.wikimedia.cloud"
            result["reason"] = f"{num_items} items is too many for efficient API calls. SQL is 100-1000× faster."
            result["requires_db"] = True
            result["alternatives"] = [
                {"method": "action_api", "why": "If database access is unavailable. Expect slow pagination."}
            ]
        else:
            result["method"] = "action_api"
            result["endpoint"] = "list=categorymembers | list=embeddedin | list=search"
            result["url"] = "https://en.wikipedia.org/w/api.php"
            result["reason"] = f"Best for {num_items if num_items else 'moderate'} items with simple filters."
            result["alternatives"] = [
                {"method": "sql", "why": "For >500 items, SQL replicas are dramatically faster"}
            ]

    elif category == "analytics":
        if has_db_access or has_db_access is None:
            result["method"] = "sql"
            result["endpoint"] = "SSH tunnel to enwiki.analytics.db.svc.wikimedia.cloud"
            result["reason"] = "Single SQL query with JOINs replaces hundreds of API calls."
            result["requires_db"] = True
            result["alternatives"] = [
                {"method": "sparql", "why": "If the analysis is about Wikidata entities rather than Wikipedia pages"},
                {"method": "action_api", "why": "For small sets (<50 items), if database access is unavailable"}
            ]
            if has_db_access is None:
                result["note"] = "Requires Toolforge SSH tunnel and database credentials. See wikimedia-database skill."
        else:
            result["method"] = "sparql"
            result["endpoint"] = "https://query.wikidata.org/sparql"
            result["reason"] = "Best alternative when SQL replicas are unavailable."
            result["alternatives"] = [
                {"method": "action_api", "why": "For very small datasets (<50 items)"}
            ]

    elif category == "realtime":
        result["method"] = "eventstreams"
        result["endpoint"] = "https://stream.wikimedia.org/v2/stream/recentchange"
        result["reason"] = "Only way to get sub-second push-based notifications. No rate limits."
        result["alternatives"] = [
            {"method": "action_api", "why": "For occasional checks rather than continuous monitoring"}
        ]
        if re.search(r'patrol|new\s*page|review', desc_lower):
            result["endpoint"] = "https://stream.wikimedia.org/v2/stream/recentchange (filter: type==new)"
            result["note"] = "Combine with PageTriage API for patrol status checks."

    elif category == "edit":
        if num_items and num_items > 10:
            result["method"] = "pywikibot"
            result["endpoint"] = "Site('en', 'wikipedia') + page generator"
            result["reason"] = f"For {num_items} edits, Pywikibot's built-in throttling and conflict detection are essential."
            result["script_hint"] = "Use replace.py or harvest_template.py from Pywikibot's built-in scripts."
            result["alternatives"] = [
                {"method": "action_api", "why": "For a single one-off edit"}
            ]
        else:
            result["method"] = "action_api"
            result["endpoint"] = "action=edit"
            result["url"] = "https://en.wikipedia.org/w/api.php"
            result["reason"] = "Simplest approach for a single edit. Requires bot password."
            result["alternatives"] = [
                {"method": "pywikibot", "why": "For >10 edits, switch to Pywikibot for safety"}
            ]
        result["requires_auth"] = True

    elif category == "graph":
        result["method"] = "sparql"
        result["endpoint"] = "https://query.wikidata.org/sparql"
        result["reason"] = "SPARQL is the only way to do complex graph traversal across Wikidata entities."
        result["alternatives"] = [
            {"method": "action_api", "why": "For single-entity lookups (wbgetentities is faster for one QID)"}
        ]
        if re.search(r'single|one\s+item|one\s+entity|lookup', desc_lower):
            result["method"] = "action_api"
            result["endpoint"] = "action=wbgetentities&ids=Q..."
            result["url"] = "https://www.wikidata.org/w/api.php"
            result["reason"] = "For a single entity lookup, wbgetentities is 10-100× faster than SPARQL."
            result["alternatives"] = [
                {"method": "sparql", "why": "For complex relational queries across multiple entities"}
            ]

    elif category == "patrol":
        result["method"] = "pagetriage"
        result["endpoint"] = "action=pagetriagelist"
        result["url"] = "https://en.wikipedia.org/w/api.php"
        result["reason"] = "PageTriage is the dedicated extension for new page patrol."
        result["requires_auth"] = True
        result["note"] = "Requires patrol user right. Primarily deployed on enwiki."
        result["alternatives"] = [
            {"method": "action_api", "why": "Use list=recentchanges&rctype=new if you don't have patrol rights"}
        ]

    else:  # unknown
        result["method"] = "rest"
        result["endpoint"] = "/page/summary/{title}"
        result["url"] = "https://en.wikipedia.org/api/rest_v1/"
        result["reason"] = "Default: REST API is the simplest starting point."
        result["note"] = "Could not auto-detect task. Try a more specific description."
        result["alternatives"] = [
            {"method": "action_api", "why": "For multiple pages or filtered queries"},
            {"method": "sparql", "why": "For complex relational queries"},
            {"method": "sql", "why": "For bulk analytics"},
            {"method": "eventstreams", "why": "For real-time monitoring"},
            {"method": "pywikibot", "why": "For editing and bot operations"},
        ]

    return result


def compare(method_a: str, method_b: str) -> dict:
    """Compare two approaches head-to-head.
    
    Args:
        method_a: First method (api, rest, sparql, sql, eventstreams, pywikibot)
        method_b: Second method
    
    Returns:
        dict with winner, reason, and comparison table
    """
    methods = {
        "rest": {"name": "REST API", "read": True, "write": False, "latency": "Low (~200ms)",
                 "auth": "No", "best_for": "Single page reads, summaries"},
        "api": {"name": "Action API", "read": True, "write": True, "latency": "Low (~200ms)",
                "auth": "For edits", "best_for": "Multi-page queries, metadata, edits"},
        "sparql": {"name": "SPARQL", "read": True, "write": False, "latency": "Medium (1-30s)",
                   "auth": "No", "best_for": "Complex graph queries"},
        "sql": {"name": "SQL Replicas", "read": True, "write": False, "latency": "Medium (~1s)",
                "auth": "SSH + DB creds", "best_for": "Bulk analytics, JOINs"},
        "eventstreams": {"name": "EventStreams", "read": True, "write": False, "latency": "Real-time",
                         "auth": "No", "best_for": "Live monitoring"},
        "pywikibot": {"name": "Pywikibot", "read": True, "write": True, "latency": "Varies",
                      "auth": "Bot password", "best_for": "Bot operations, bulk edits"},
    }

    a = methods.get(method_a)
    b = methods.get(method_b)

    if not a or not b:
        return {"error": f"Unknown method(s). Valid: {', '.join(methods.keys())}"}

    return {
        "methods": [a, b],
        "comparison": [
            {"attribute": "Read", f"method_a": a["read"], f"method_b": b["read"]},
            {"attribute": "Write", f"method_a": a["write"], f"method_b": b["write"]},
            {"attribute": "Latency", f"method_a": a["latency"], f"method_b": b["latency"]},
            {"attribute": "Authentication", f"method_a": a["auth"], f"method_b": b["auth"]},
        ],
        "winner": method_a if a["read"] and not b["read"] else method_b,
        "tie": True,
    }


def format_recommendation(result: dict) -> str:
    """Format a recommendation dict as a human-readable string."""
    lines = []
    lines.append(f"Category: {result['category']}")
    lines.append(f"Recommended: {result.get('method', '?')}")
    lines.append(f"Endpoint: {result.get('endpoint', '?')}")
    if result.get('url'):
        lines.append(f"URL: {result['url']}")
    lines.append(f"Reason: {result.get('reason', '?')}")
    if result.get('note'):
        lines.append(f"Note: {result['note']}")
    if result.get('requires_auth'):
        lines.append("⚠️ Requires authentication")
    if result.get('requires_db'):
        lines.append("⚠️ Requires Toolforge database access")
    if result.get('script_hint'):
        lines.append(f"Script: {result['script_hint']}")
    if result.get('alternatives'):
        lines.append("Alternatives:")
        for alt in result['alternatives']:
            lines.append(f"  - {alt['method']}: {alt['why']}")
    return "\n".join(lines)


# ── CLI entry point ──────────────────────────────────────────────────────────
def main():
    """CLI: recommend the best API for a task description."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Recommend the best Wikimedia API for a task")
    parser.add_argument("description", nargs="?", help="Task description (e.g., 'pageviews for 50 articles')")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--items", type=int, default=None, help="Number of items involved")
    parser.add_argument("--compare", nargs=2, metavar=("METHOD_A", "METHOD_B"),
                        help="Compare two approaches: api, rest, sparql, sql, eventstreams, pywikibot")
    parser.add_argument("--has-db", action="store_true", default=None,
                        help="Whether Toolforge database access is available")
    args = parser.parse_args()

    if args.compare:
        result = compare(args.compare[0], args.compare[1])
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(format_recommendation(result))
        return

    if not args.description:
        parser.print_help()
        print("\nExamples:")
        print("  python3 api_selector.py 'pageviews for 50 physics articles'")
        print("  python3 api_selector.py 'read single page' --json")
        print("  python3 api_selector.py --compare api sql")
        return

    result = recommend(args.description, has_db_access=args.has_db, num_items=args.items)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_recommendation(result))


if __name__ == "__main__":
    main()
