"""
CirrusSearch client — Python library for searching Wikimedia wikis via the Action API.

Provides search in three modes (full-text, near-match, prefix) with full support for
CirrusSearch syntax, pagination, error handling, and formatted output.

Usage:
    from search_client import CirrusClient

    client = CirrusClient(user_agent="MyBot/1.0 (contact) ContentGapResearch")

    # Full-text search with CirrusSearch syntax
    results = client.search('hastemplate:"Infobox scientist" incategory:"Nobel laureates"')

    # Near-match title search
    results = client.search_near("Albert Einstein")

    # Prefix search
    results = client.search_prefix("Albert_E")

    # Iterate through paginated results
    for page in client.search_batch("incategory:Physics"):
        print(page["title"])
"""

import json
import re
import sys
import time
from typing import Any, Dict, Generator, List, Optional
from urllib.parse import urlencode

import requests


class CirrusClient:
    """Client for searching Wikimedia wikis via CirrusSearch (Action API)."""

    BASE_URL = "https://{wiki}/w/api.php"
    DEFAULT_UA = "CirrusClient/1.0 (contact) ContentGapResearch"

    # Namespace IDs to human-readable names
    NS_NAMES = {
        0: "Article", 1: "Talk", 2: "User", 3: "User talk",
        4: "Wikipedia", 5: "Wikipedia talk", 6: "File", 7: "File talk",
        8: "MediaWiki", 9: "MediaWiki talk", 10: "Template", 11: "Template talk",
        12: "Help", 13: "Help talk", 14: "Category", 15: "Category talk",
    }

    def __init__(
        self,
        wiki: str = "en.wikipedia.org",
        user_agent: Optional[str] = None,
        timeout: int = 30,
        retries: int = 3,
        backoff_factor: float = 1.5,
    ):
        """
        Initialize the search client.

        Args:
            wiki: Wiki domain (e.g., 'en.wikipedia.org', 'commons.wikimedia.org')
            user_agent: User-Agent header value
            timeout: Request timeout in seconds
            retries: Number of retries on 429/5xx errors
            backoff_factor: Multiplicative backoff factor between retries
        """
        self.wiki = wiki
        self.api_url = self.BASE_URL.format(wiki=wiki)
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or self.DEFAULT_UA,
            "Accept-Encoding": "gzip, deflate",
        })

    def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make an API request with retry logic."""
        params.setdefault("format", "json")
        params.setdefault("action", "query")

        last_error = None
        for attempt in range(self.retries):
            try:
                resp = self.session.get(
                    self.api_url,
                    params=params,
                    timeout=self.timeout,
                )

                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", 5))
                    wait = retry_after * self.backoff_factor ** attempt
                    time.sleep(wait)
                    continue

                resp.raise_for_status()
                return resp.json()

            except (requests.RequestException, json.JSONDecodeError) as e:
                last_error = e
                if attempt < self.retries - 1:
                    time.sleep(self.backoff_factor ** attempt)
                    continue

                raise RuntimeError(
                    f"API request failed after {self.retries} attempts: {last_error}"
                ) from last_error

        raise RuntimeError(f"API request failed: {last_error}")

    def search(
        self,
        query: str,
        namespace: int = 0,
        limit: int = 50,
        offset: int = 0,
        sort: str = "relevance",
        prop: str = "size|wordcount|timestamp|snippet|score",
    ) -> List[Dict[str, Any]]:
        """
        Full-text search with CirrusSearch syntax support.

        Args:
            query: CirrusSearch query string (supports intitle:, incategory:, etc.)
            namespace: Namespace ID to search (0 = main, use 14 for categories)
            limit: Number of results (max 50 unauthenticated, 500 for bots)
            offset: Pagination offset
            sort: Sort order (relevance, last_edit_desc, create_timestamp_desc, etc.)
            prop: What metadata to return

        Returns:
            List of search result dicts with keys: title, pageid, size, wordcount,
            timestamp, snippet, score, ns
        """
        params = {
            "list": "search",
            "srsearch": query,
            "srnamespace": namespace,
            "srwhat": "text",
            "srlimit": min(limit, 500),
            "srsort": sort,
            "srprop": prop,
        }
        if offset:
            params["sroffset"] = offset

        data = self._request(params)
        return data.get("query", {}).get("search", [])

    def search_near(
        self, query: str, namespace: int = 0, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Near-match title search (the 'Go' feature).

        Finds pages whose title nearly perfectly matches the query.
        """
        params = {
            "list": "search",
            "srsearch": query,
            "srnamespace": namespace,
            "srwhat": "near_match",
            "srlimit": limit,
            "srprop": "size|timestamp",
        }
        data = self._request(params)
        return data.get("query", {}).get("search", [])

    def search_prefix(
        self, prefix: str, namespace: int = 0, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Title prefix search.

        Finds pages whose title starts with the given string.
        """
        params = {
            "generator": "prefixsearch",
            "gpssearch": prefix,
            "gpsnamespace": namespace,
            "gpslimit": min(limit, 500),
            "prop": "info",
        }
        data = self._request(params)
        pages = data.get("query", {}).get("pages", {})
        results = []
        for page_id, page_data in sorted(
            pages.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0
        ):
            if page_id == "-1":
                continue
            results.append(page_data)
        return results

    def search_batch(
        self,
        query: str,
        namespace: int = 0,
        batch_size: int = 500,
        max_results: Optional[int] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Iterate through all search results (handles pagination automatically).

        Args:
            query: CirrusSearch query string
            namespace: Namespace ID
            batch_size: Results per API call (max 500)
            max_results: Stop after this many results (None = all available, up to 10k)

        Yields:
            Search result dicts
        """
        offset = 0
        total_yielded = 0
        while True:
            results = self.search(
                query=query,
                namespace=namespace,
                limit=min(batch_size, 500),
                offset=offset,
            )

            if not results:
                break

            for result in results:
                yield result
                total_yielded += 1
                if max_results and total_yielded >= max_results:
                    return

            if len(results) < min(batch_size, 500):
                break
            offset += len(results)

    def maintenance_query(
        self, query_type: str, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Run a pre-built maintenance query.

        Args:
            query_type: One of: 'unsourced-blp', 'missing-image', 'dead-links',
                       'recently-created', 'template-usage', 'linksto-page',
                       'no-categories', 'copyedit-needed', 'pov-check',
                       'subpages-of', 'stub-category', 'recent-category'
            **kwargs: Query-specific parameters (days=, category=, template=,
                     linksto=, parent=)

        Returns:
            List of search result dicts
        """
        query = self._build_maintenance_query(query_type, **kwargs)
        limit = kwargs.get("limit", 50)
        return self.search(query, limit=limit)

    def _build_maintenance_query(self, query_type: str, **kwargs) -> str:
        """Build a CirrusSearch query string for a maintenance task."""
        days = kwargs.get("days", 7)
        category = kwargs.get("category", "")
        template = kwargs.get("template", "")
        linksto = kwargs.get("linksto", "")
        parent = kwargs.get("parent", "")

        queries = {
            "unsourced-blp": 'hastemplate:"BLP unsourced" incategory:"Living people"',
            "unsourced-pages": 'hastemplate:"Unreferenced" -incategory:"Living people"',
            "dead-links": 'hastemplate:"Dead link" incategory:"All articles with dead external links"',
            "missing-image": 'hastemplate:"Infobox person" -insource:"|image =" -insource:"|image="',
            "no-categories": 'incategory:"All uncategorized pages"',
            "no-image-blp": 'hastemplate:"Infobox person" incategory:"Living people" -insource:"|image =" -insource:"|image="',
            "copyedit-needed": 'hastemplate:"Copy edit"',
            "pov-check": 'hastemplate:"POV" incategory:"All articles with unsourced statements"',
            "deprecated-tmpl": 'incategory:"Pages using deprecated templates"',
            "overcategorized": 'incategory:"Wikipedia articles that are excessively categorized"',
        }

        if query_type in queries:
            return queries[query_type]

        if query_type == "recently-created":
            return f"creationdate:>=today-{days}d"
        elif query_type == "recent-stubs":
            return f"creationdate:>=today-{days}d incategory:\"All stub articles\""
        elif query_type == "recent-category":
            return f'incategory:"{category}" lasteditdate:>=today-{days}d'
        elif query_type == "stub-category":
            return f'incategory:"{category}"'
        elif query_type == "template-usage":
            return f'hastemplate:"{template}"'
        elif query_type == "linksto-page":
            return f'linksto:"{linksto}"'
        elif query_type == "subpages-of":
            return f'subpageof:"{parent}"'
        else:
            raise ValueError(f"Unknown maintenance query type: {query_type}")

    def get_total_hits(self, query: str, namespace: int = 0) -> int:
        """Get the total number of hits without fetching result details."""
        params = {
            "list": "search",
            "srsearch": query,
            "srnamespace": namespace,
            "srwhat": "text",
            "srlimit": 1,
            "srprop": "",
        }
        data = self._request(params)
        return data.get("query", {}).get("searchinfo", {}).get("totalhits", 0)

    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format search results as a human-readable string."""
        lines = [f"Results: {len(results)}"]
        for i, r in enumerate(results, 1):
            title = r.get("title", "?")
            ns = r.get("ns", 0)
            ns_label = self.NS_NAMES.get(ns, f"NS{ns}")
            snippet = re.sub(r"<[^>]+>", "", r.get("snippet", ""))[:120]
            size = r.get("size", "?")
            wc = r.get("wordcount", "?")
            ts = r.get("timestamp", "")
            score = r.get("score", "")

            lines.append(f"\n  {i:3d}. {title}  [{ns_label}]")
            if snippet:
                lines.append(f"       {snippet}...")
            parts = []
            if size != "?":
                parts.append(f"{size}B")
            if wc != "?":
                parts.append(f"{wc} words")
            if ts:
                parts.append(ts)
            if score:
                parts.append(f"score={score}")
            if parts:
                lines.append(f"       {' | '.join(parts)}")

        return "\n".join(lines)


# ---- CLI ----
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Search Wikimedia wikis using CirrusSearch"
    )
    parser.add_argument("query", help="CirrusSearch query string")
    parser.add_argument("--wiki", default="en.wikipedia.org", help="Wiki domain")
    parser.add_argument("--ns", type=int, default=0, help="Namespace ID")
    parser.add_argument("--limit", type=int, default=20, help="Max results")
    parser.add_argument("--near", action="store_true", help="Near-match title search")
    parser.add_argument("--prefix", action="store_true", help="Title prefix search")
    parser.add_argument("--sort", default="relevance",
                        choices=["relevance", "last_edit_desc", "last_edit_asc",
                                 "create_timestamp_desc", "create_timestamp_asc",
                                 "incoming_links_desc", "incoming_links_asc",
                                 "title_natural_asc", "title_natural_desc",
                                 "random", "just_match", "none"],
                        help="Sort order")
    parser.add_argument("--json", action="store_true", help="Raw JSON output")
    parser.add_argument("--total", action="store_true", help="Just show total hit count")
    parser.add_argument("--batch", action="store_true", help="Iterate through all results")

    args = parser.parse_args()

    client = CirrusClient(wiki=args.wiki)

    if args.total:
        total = client.get_total_hits(args.query, namespace=args.ns)
        print(f"Total hits: {total}")
        sys.exit(0)

    if args.json:
        if args.near:
            results = client.search_near(args.query, namespace=args.ns, limit=args.limit)
        elif args.prefix:
            results = client.search_prefix(args.query, namespace=args.ns, limit=args.limit)
        else:
            results = client.search(args.query, namespace=args.ns, limit=args.limit, sort=args.sort)
        print(json.dumps(results, indent=2))
        sys.exit(0)

    if args.batch:
        count = 0
        for result in client.search_batch(args.query, namespace=args.ns):
            title = result.get("title", "?")
            print(title)
            count += 1
            if args.limit and count >= args.limit:
                break
        print(f"\nTotal: {count}")
        sys.exit(0)

    if args.near:
        results = client.search_near(args.query, namespace=args.ns, limit=args.limit)
    elif args.prefix:
        results = client.search_prefix(args.query, namespace=args.ns, limit=args.limit)
    else:
        results = client.search(args.query, namespace=args.ns, limit=args.limit, sort=args.sort)

    print(client.format_results(results))
