#!/usr/bin/env python3
"""Wikipedia Pageview Analysis Tool.

Fetches and analyzes pageview data from the Wikimedia REST API.

USAGE:
  python3 analysis-template.py <article_title> [days]

EXAMPLES:
  python3 analysis-template.py Albert_Einstein 30
  python3 analysis-template.py "Python_(programming_language)" 90
  python3 analysis-template.py "Barack_Obama" 365 --compare

REQUIREMENTS:
  pip install requests matplotlib (optional, for charts)
"""

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests


# ────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────

USER_AGENT = os.environ.get(
    "WIKIMEDIA_UA",
    "PageviewsAnalyzer/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; "
    "test@wikimedia.org) PageviewAnalysis",
)

API_BASE = "https://wikimedia.org/api/rest_v1/metrics/pageviews"

# How long to wait between API requests (seconds)
REQUEST_DELAY = 0.5


# ────────────────────────────────────────────────────
# Client
# ────────────────────────────────────────────────────

class PageviewsClient:
    """Client for the Wikimedia Pageviews API."""

    def __init__(self, user_agent: str = USER_AGENT):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self._last_request = 0.0

    def _rate_limit(self):
        elapsed = time.time() - self._last_request
        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)

    def _request(self, url: str) -> Dict[str, Any]:
        self._rate_limit()
        resp = self.session.get(url, timeout=30)
        self._last_request = time.time()
        if resp.status_code == 404:
            return {"items": []}
        resp.raise_for_status()
        return resp.json()

    def per_article(
        self,
        article: str,
        start: str,
        end: str,
        project: str = "en.wikipedia",
        access: str = "all-access",
        agent: str = "all-agents",
    ) -> List[Dict[str, Any]]:
        """Daily pageviews for a single article."""
        url = (
            f"{API_BASE}/per-article/{project}/{access}/{agent}/"
            f"{article}/daily/{start}/{end}"
        )
        data = self._request(url)
        return data.get("items", [])

    def top_articles(
        self,
        date: str,
        project: str = "en.wikipedia",
        access: str = "all-access",
    ) -> List[Dict[str, Any]]:
        """Top articles for a project on a given date."""
        url = f"{API_BASE}/top/{project}/{access}/{date}"
        data = self._request(url)
        items = data.get("items", [])
        if items:
            return items[0].get("articles", [])
        return []

    def multi_article(
        self,
        articles: List[str],
        start: str,
        end: str,
        project: str = "en.wikipedia",
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch pageviews for multiple articles (with rate limiting)."""
        results = {}
        for article in articles:
            print(f"  Fetching: {article}")
            results[article] = self.per_article(article, start, end, project)
        return results


# ────────────────────────────────────────────────────
# Analysis Functions
# ────────────────────────────────────────────────────

def analyze_trend(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute trend statistics from a list of daily pageview items."""
    if not items:
        return {"error": "No data"}

    views = [item.get("views", 0) for item in items]
    dates = [item["timestamp"][:8] for item in items]

    total = sum(views)
    days = len(views)
    avg = total / days if days > 0 else 0
    peak_idx = views.index(max(views))
    min_idx = views.index(min(views))

    # Day-over-day change
    changes = []
    for i in range(1, len(views)):
        if views[i - 1] > 0:
            pct = ((views[i] - views[i - 1]) / views[i - 1]) * 100
            changes.append(pct)

    avg_change = sum(changes) / len(changes) if changes else 0

    return {
        "total": total,
        "days": days,
        "average": round(avg, 1),
        "peak": {"date": dates[peak_idx], "views": views[peak_idx]},
        "low": {"date": dates[min_idx], "views": views[min_idx]},
        "trend": "up" if avg_change > 1 else ("down" if avg_change < -1 else "stable"),
        "avg_daily_change_pct": round(avg_change, 1),
    }


def print_report(article: str, items: List[Dict[str, Any]], detailed: bool = False):
    """Print a formatted analysis report."""
    if not items:
        print(f"\n  No data for '{article}' in this period.")
        return

    stats = analyze_trend(items)
    print(f"\n{'=' * 55}")
    print(f"  📊 Pageview Report: {article}")
    print(f"{'=' * 55}")
    print(f"  Period:  {items[0]['timestamp'][:8]} to {items[-1]['timestamp'][:8]}")
    print(f"  Days:    {stats['days']}")
    print(f"  Total:   {stats['total']:,} views")
    print(f"  Avg:     {stats['average']:,.0f} views/day")
    print(f"  Peak:    {stats['peak']['views']:,} views on {stats['peak']['date']}")
    print(f"  Low:     {stats['low']['views']:,} views on {stats['low']['date']}")
    print(f"  Trend:   {stats['trend']} ({stats['avg_daily_change_pct']:+.1f}%/day)")

    if detailed:
        print(f"\n  {'Date':<12} {'Views':>10} {'Change':>8}")
        print(f"  {'-' * 32}")
        prev = None
        for item in items:
            date = item["timestamp"][:8]
            views = item.get("views", 0)
            if prev:
                pct = ((views - prev) / prev) * 100
                change = f"{pct:+.1f}%"
            else:
                change = "—"
            print(f"  {date:<12} {views:>10,} {change:>8}")
            prev = views


# ────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fetch and analyze Wikipedia pageview data."
    )
    parser.add_argument(
        "article", nargs="?", help="Article title (underscores, e.g., Albert_Einstein)"
    )
    parser.add_argument(
        "days", nargs="?", type=int, default=30, help="Number of days to analyze"
    )
    parser.add_argument(
        "--project", default="en.wikipedia", help="Wikimedia project (default: en.wikipedia)"
    )
    parser.add_argument(
        "--top", type=int, metavar="N", help="Show top N articles instead"
    )
    parser.add_argument(
        "--compare", action="store_true", help="Compare desktop vs mobile"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output raw JSON"
    )
    parser.add_argument(
        "--detailed", action="store_true", help="Show daily breakdown"
    )

    args = parser.parse_args()
    client = PageviewsClient()

    end_date = datetime.now() - timedelta(days=2)  # Data lag
    start_date = end_date - timedelta(days=args.days)

    end_compact = end_date.strftime("%Y%m%d")
    start_compact = start_date.strftime("%Y%m%d")
    end_slash = end_date.strftime("%Y/%m/%d")

    if args.top:
        # Fetch top articles
        print(f"📊 Top {args.top} articles on {args.project} ({end_slash})")
        articles = client.top_articles(end_slash, project=args.project)[: args.top]
        if not articles:
            print("  No data available (data may be delayed ~48h)")
            return

        if args.json:
            print(json.dumps(articles, indent=2))
            return

        print(f"\n  {'Rank':<6} {'Article':<50} {'Views':>10}")
        print(f"  {'-' * 68}")
        for a in articles:
            print(f"  #{a['rank']:<4} {a['article']:<50} {a['views']:>10,}")
        return

    if not args.article:
        parser.print_help()
        sys.exit(1)

    # Single article analysis
    article = args.article

    if args.compare:
        # Compare access methods
        print(f"📊 Comparing access methods for '{article}'")
        print(f"   Period: {start_compact} to {end_compact}\n")
        for access in ["all-access", "desktop", "mobile-web", "mobile-app"]:
            items = client.per_article(
                article, start_compact, end_compact,
                project=args.project, access=access
            )
            total = sum(i.get("views", 0) for i in items)
            print(f"  {access:<15} {total:>10,} total views")
        return

    # Standard analysis
    items = client.per_article(article, start_compact, end_compact, project=args.project)

    if args.json:
        print(json.dumps(items, indent=2))
        return

    print_report(article, items, detailed=args.detailed)


if __name__ == "__main__":
    main()
