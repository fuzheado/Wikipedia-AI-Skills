#!/usr/bin/env python3
"""Wikimedia API Client Template.

A reusable, production-ready client for accessing Wikimedia APIs
with proper User-Agent headers, rate limiting, and error handling.

USAGE:
  1. Copy this file:  cp user-agent-template.py my_bot.py
  2. Edit the USER_AGENT string below with YOUR contact info
  3. Run it:          python3 my_bot.py

REQUIREMENTS:
  pip install requests
"""

import json
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import requests

# ═══════════════════════════════════════════════════════════
# ✏️  EDIT THIS: Replace with your own contact information
# ═══════════════════════════════════════════════════════════
USER_AGENT = (
    "MyBot/1.0 "                     # Your bot/tool name and version
    "(https://example.com; "         # Your website or contact page
    "user@example.com) "             # Your email address
    "MyProjectName/1.0"              # Your project identifier
)

# ═══════════════════════════════════════════════════════════
# ⚙️  Configuration
# ═══════════════════════════════════════════════════════════

# Rate limiting: minimum seconds between requests
REQUEST_DELAY = 0.5  # 500ms — be respectful!

# Max retries for transient errors
MAX_RETRIES = 3

# Base URLs
WIKIPEDIA_ACTION_API = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_REST_API = "https://en.wikipedia.org/api/rest_v1"
WIKIMEDIA_API_GATEWAY = "https://api.wikimedia.org/core/v1"
PAGEVIEWS_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("wikimedia_client")


# ═══════════════════════════════════════════════════════════
# 🧰  Client
# ═══════════════════════════════════════════════════════════

class WikimediaClient:
    """Reusable HTTP client for Wikimedia APIs."""

    def __init__(self, user_agent: str = USER_AGENT):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.last_request_time: Optional[datetime] = None

    # ─────────────────────────────────────────────────────
    # Core request method with rate limiting & retries
    # ─────────────────────────────────────────────────────

    def request(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET",
        max_retries: int = MAX_RETRIES,
    ) -> requests.Response:
        """Make a rate-limited, retry-enabled HTTP request.

        Automatically:
        - Waits REQUEST_DELAY seconds between requests
        - Retries on 429 (rate limit) with Retry-After header
        - Raises on 403 (bad User-Agent) with a helpful message
        - Raises on other HTTP errors
        """
        self._rate_limit()

        for attempt in range(max_retries):
            try:
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    params=params,
                    timeout=30,
                )
            except requests.exceptions.Timeout:
                log.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise

            self.last_request_time = datetime.now()

            if response.status_code == 200:
                return response

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                log.warning(
                    f"Rate limited (429). Waiting {retry_after}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_after)
                continue

            if response.status_code == 403:
                raise PermissionError(
                    "403 Forbidden — likely a missing or invalid User-Agent.\n"
                    "See: https://foundation.wikimedia.org/wiki/"
                    "Policy:Wikimedia_Foundation_User-Agent_Policy\n"
                    f"Current User-Agent: {self.session.headers.get('User-Agent')}"
                )

            if response.status_code == 404:
                raise FileNotFoundError(
                    f"404 Not Found: {url}\n"
                    f"  Params: {params}\n"
                    "  Check that the URL and parameters are correct."
                )

            response.raise_for_status()

        raise RuntimeError(f"Request failed after {max_retries} retries: {url}")

    def _rate_limit(self) -> None:
        """Ensure minimum delay between requests."""
        if self.last_request_time is not None:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            if elapsed < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - elapsed)

    # ─────────────────────────────────────────────────────
    # Convenience: close session (use as context manager)
    # ─────────────────────────────────────────────────────

    def close(self) -> None:
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    # ─────────────────────────────────────────────────────
    # Action API helpers
    # ─────────────────────────────────────────────────────

    def action_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call the Action API and return parsed JSON."""
        defaults = {"action": "query", "format": "json", "formatversion": "2"}
        merged = {**defaults, **params}
        return self.request(WIKIPEDIA_ACTION_API, params=merged).json()

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search Wikipedia pages."""
        data = self.action_query({
            "list": "search",
            "srsearch": query,
            "srlimit": min(limit, 50),
        })
        return data.get("query", {}).get("search", [])

    def get_page_extract(self, title: str) -> Optional[str]:
        """Get the plain text extract of a page (lead section)."""
        data = self.action_query({
            "prop": "extracts",
            "titles": title,
            "exintro": True,
            "explaintext": True,
        })
        pages = data.get("query", {}).get("pages", [])
        if pages:
            return pages[0].get("extract")
        return None

    def get_category_members(
        self, category: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get pages in a category."""
        data = self.action_query({
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmlimit": min(limit, 500),
        })
        return data.get("query", {}).get("categorymembers", [])

    # ─────────────────────────────────────────────────────
    # REST API helpers
    # ─────────────────────────────────────────────────────

    def page_summary(self, title: str) -> Dict[str, Any]:
        """Get a short page summary via the REST API."""
        url = f"{WIKIPEDIA_REST_API}/page/summary/{requests.utils.quote(title)}"
        return self.request(url).json()

    # ─────────────────────────────────────────────────────
    # SPARQL / Wikidata helpers
    # ─────────────────────────────────────────────────────

    def sparql_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SPARQL query against Wikidata."""
        response = self.request(
            SPARQL_ENDPOINT,
            params={"format": "json", "query": query},
        )
        data = response.json()
        return data.get("results", {}).get("bindings", [])

    def get_entity(self, qid: str) -> Dict[str, Any]:
        """Get full Wikidata entity data."""
        url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        return self.request(url).json()

    # ─────────────────────────────────────────────────────
    # Pageviews helpers
    # ─────────────────────────────────────────────────────

    def top_pageviews(
        self, project: str = "en.wikipedia", date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get top pageviews for a project on a given date.

        Args:
            project: e.g. 'en.wikipedia', 'commons.wikimedia'
            date: YYYY/MM/DD format (defaults to 3 days ago)
        """
        if date is None:
            three_days_ago = datetime.now() - timedelta(days=3)
            date = three_days_ago.strftime("%Y/%m/%d")
        url = f"{PAGEVIEWS_API}/top/{project}/all-access/{date}"
        data = self.request(url).json()
        items = data.get("items", [])
        if items:
            return items[0].get("articles", [])
        return []


# ═══════════════════════════════════════════════════════════
# 🚀  Demo / Test
# ═══════════════════════════════════════════════════════════

def main():
    """Run a quick demo to verify the client works."""
    print(f"⚡ Wikimedia API Client Demo")
    print(f"   User-Agent: {USER_AGENT}")
    print()

    with WikimediaClient() as client:
        # 1. Search
        print("🔍 Searching for 'Albert Einstein'...")
        results = client.search("Albert Einstein", limit=3)
        for r in results:
            print(f"   - {r['title']} (page_id: {r['pageid']})")
        print()

        # 2. Page summary
        print("📄 Getting page summary for 'Python (programming language)'...")
        summary = client.page_summary("Python (programming language)")
        print(f"   Title: {summary.get('title', 'N/A')}")
        print(f"   Description: {summary.get('description', 'N/A')}")
        extract = summary.get("extract", "")
        if extract:
            print(f"   Extract: {extract[:150]}...")
        print()

        # 3. SPARQL test
        print("🔗 Testing SPARQL endpoint...")
        sparql_results = client.sparql_query(
            'SELECT ?item ?itemLabel WHERE { '
            '  VALUES ?item { wd:Q937 wd:Q42 } '
            '  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }'
            '}'
        )
        for r in sparql_results:
            print(f"   - {r.get('item', {}).get('value', 'N/A')}: "
                  f"{r.get('itemLabel', {}).get('value', 'N/A')}")
        print()

        # 4. Pageviews test
        print("📊 Testing pageviews endpoint...")
        top = client.top_pageviews("en.wikipedia")
        print(f"   Got top {len(top)} articles for today")
        if top:
            for a in top[:5]:
                print(f"   - {a.get('article', 'N/A')}: "
                      f"{a.get('views', 'N/A')} views")

    print()
    print("✅ All API tests passed!")


if __name__ == "__main__":
    main()
