"""
Reusable Wikimedia API client with retry logic, rate limiting, and error handling.

Provides a drop-in HttpClient class that wraps requests.Session() with:
- Automatic exponential backoff on 429 and 5xx errors
- User-Agent header enforcement
- Connection reuse via Session()
- Timeout handling
- Debug logging

Usage:
    from api_client import HttpClient

    client = HttpClient("MyBot/1.0 (user@example.com) MyProject")
    data = client.get("https://en.wikipedia.org/w/api.php", params={
        "action": "query", "titles": "Albert Einstein", "format": "json",
    })

    # For SPARQL:
    data = client.sparql("SELECT ?item WHERE { wd:Q937 wdt:P106 ?item. }")

    # For Lift Wing ML:
    data = client.post(
        "https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-language-agnostic:predict",
        json_data={"rev_id": 123456789, "lang": "en"},
    )

    # For SSE streams (non-blocking):
    for event in client.events("https://stream.wikimedia.org/v2/stream/recentchange"):
        if event.get("meta", {}).get("domain") == "canary":
            continue  # Skip test events
        print(event.get("title"))
"""

import json
import logging
import time
from typing import Any, Optional

import requests

logger = logging.getLogger("wikimedia-api-client")


class HttpClient:
    """Reusable HTTP client for Wikimedia APIs with retry and rate limiting."""

    def __init__(
        self,
        user_agent: str = "HttpClient/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)",
        max_retries: int = 3,
        base_delay: float = 2.0,
        max_delay: float = 120.0,
        default_timeout: int = 30,
    ):
        """
        Args:
            user_agent: User-Agent header value (required by Wikimedia policy).
            max_retries: Maximum number of retry attempts for 429/5xx.
            base_delay: Initial delay in seconds for exponential backoff.
            max_delay: Maximum delay in seconds for exponential backoff.
            default_timeout: Default request timeout in seconds.
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.default_timeout = default_timeout

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    # ── Core request methods ────────────────────────────────────────────────

    def get(
        self,
        url: str,
        params: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """Make a GET request with retry logic."""
        return self._request("GET", url, params=params, timeout=timeout)

    def post(
        self,
        url: str,
        json_data: Optional[dict] = None,
        params: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """Make a POST request with retry logic."""
        return self._request("POST", url, json_data=json_data, params=params, timeout=timeout)

    def _request(
        self,
        method: str,
        url: str,
        params: Optional[dict] = None,
        json_data: Optional[dict] = None,
        timeout: Optional[int] = None,
    ) -> dict:
        """Internal request method with exponential backoff."""
        timeout = timeout or self.default_timeout

        for attempt in range(self.max_retries):
            try:
                if method == "GET":
                    resp = self.session.get(url, params=params, timeout=timeout)
                else:
                    resp = self.session.post(url, json=json_data, params=params, timeout=timeout)
            except requests.exceptions.Timeout:
                logger.warning("Timeout on %s (attempt %d/%d)", url, attempt + 1, self.max_retries)
                if attempt < self.max_retries - 1:
                    self._backoff(attempt)
                    continue
                raise

            except requests.exceptions.ConnectionError as e:
                logger.warning("Connection error on %s: %s (attempt %d/%d)", url, e, attempt + 1, self.max_retries)
                if attempt < self.max_retries - 1:
                    self._backoff(attempt)
                    continue
                raise

            # Success
            if resp.status_code == 200:
                try:
                    return resp.json()
                except json.JSONDecodeError:
                    logger.error("Invalid JSON response from %s", url)
                    raise ValueError(f"Invalid JSON response (status {resp.status_code})")

            # Rate limited — use Retry-After header
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                wait = min(retry_after * (2 ** attempt), self.max_delay)
                logger.warning("429 rate limited on %s. Waiting %ds (attempt %d/%d)", url, wait, attempt + 1, self.max_retries)
                time.sleep(wait)
                continue

            # Server errors — transient, retry
            if 500 <= resp.status_code < 600:
                wait = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning("%d on %s. Retrying in %ds (attempt %d/%d)", resp.status_code, url, wait, attempt + 1, self.max_retries)
                time.sleep(wait)
                continue

            # Client errors (400, 403, 404, 422) — don't retry
            if resp.status_code == 403:
                raise PermissionError(
                    f"403 Forbidden on {url}. Check your User-Agent header. "
                    "Must be descriptive (not 'python-requests/2.x' or 'curl/8.x')."
                )

            if resp.status_code == 422:
                error_body = resp.text[:500]
                raise ValueError(f"422 Unprocessable Entity on {url}: {error_body}")

            resp.raise_for_status()

        raise RuntimeError(f"Request to {url} failed after {self.max_retries} retries")

    def _backoff(self, attempt: int) -> None:
        """Sleep with exponential backoff."""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        time.sleep(delay)

    # ── Specialized methods ─────────────────────────────────────────────────

    def sparql(
        self,
        query: str,
        endpoint: str = "https://query.wikidata.org/sparql",
        timeout: int = 60,
    ) -> dict:
        """Execute a SPARQL query with Wikidata-specific rate limit handling."""
        headers = {"Accept": "application/sparql-results+json"}

        for attempt in range(self.max_retries):
            try:
                resp = self.session.get(
                    endpoint,
                    params={"format": "json", "query": query},
                    headers=headers,
                    timeout=timeout,
                )
            except requests.exceptions.Timeout:
                logger.warning("SPARQL timeout (attempt %d/%d)", attempt + 1, self.max_retries)
                if attempt < self.max_retries - 1:
                    time.sleep(min(10 * (2 ** attempt), 60))
                    continue
                raise

            if resp.status_code == 200:
                return resp.json()

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 60))
                wait = max(retry_after, 10) * (2 ** attempt)
                logger.warning("SPARQL rate limited — waiting %ds", wait)
                time.sleep(wait)
                continue

            if resp.status_code == 503:
                time.sleep(min(30 * (2 ** attempt), 120))
                continue

            if resp.status_code == 400:
                raise ValueError(f"SPARQL syntax error: {resp.text[:500]}")

            if resp.status_code == 504:
                raise TimeoutError(f"SPARQL query timed out (>{timeout}s). Try adding LIMIT or optimizing.")

            resp.raise_for_status()

        raise RuntimeError(f"SPARQL query failed after {self.max_retries} retries")

    def events(self, url: str, timeout: int = 30):
        """Generator for SSE event streams (EventStreams).
        
        Handles reconnection with backoff. Filters canary events.
        
        Yields:
            dict: Parsed event data.
        """
        import json as _json

        max_reconnects = 5
        for attempt in range(max_reconnects):
            try:
                resp = self.session.get(url, stream=True, timeout=timeout)
                resp.raise_for_status()

                buffer = ""
                for chunk in resp.iter_content(chunk_size=1, decode_unicode=True):
                    if chunk is None:
                        continue
                    buffer += chunk
                    if buffer.endswith("\n\n"):
                        for line in buffer.strip().split("\n"):
                            if line.startswith("data: "):
                                try:
                                    event = _json.loads(line[6:])
                                    # Filter canary events
                                    if event.get("meta", {}).get("domain") == "canary":
                                        continue
                                    yield event
                                except _json.JSONDecodeError:
                                    continue
                        buffer = ""

            except (requests.exceptions.ConnectionError,
                    requests.exceptions.ChunkedEncodingError) as e:
                wait = min(30, 2 ** attempt)
                logger.warning("SSE connection lost: %s. Reconnecting in %ds", e, wait)
                time.sleep(wait)
                continue

    # ── Convenience methods ─────────────────────────────────────────────────

    def action_api(self, wiki: str = "en", params: Optional[dict] = None) -> dict:
        """Call the MediaWiki Action API on a specific wiki."""
        domains = {"en": "en.wikipedia.org", "fr": "fr.wikipedia.org", "de": "de.wikipedia.org",
                    "commons": "commons.wikimedia.org", "wikidata": "www.wikidata.org"}
        domain = domains.get(wiki, f"{wiki}.wikipedia.org")
        url = f"https://{domain}/w/api.php"
        p = params or {}
        p.setdefault("format", "json")
        return self.get(url, params=p)

    def wikidata_entity(self, qid: str, props: str = "labels|descriptions|claims") -> dict:
        """Fetch a Wikidata entity by QID."""
        data = self.get(
            "https://www.wikidata.org/w/api.php",
            params={"action": "wbgetentities", "ids": qid, "props": props, "format": "json"},
        )
        return data.get("entities", {}).get(qid, {})

    def lift_wing(self, model: str, data: dict) -> dict:
        """Call a Lift Wing ML model.
        
        Args:
            model: Model name (e.g., 'revertrisk-language-agnostic', 'articlequality')
            data: Request body dict (e.g., {'rev_id': 123, 'lang': 'en'})
        
        Returns:
            Parsed JSON response.
        
        Raises:
            ValueError: If the model returns 422 (e.g., parent_revision_missing for new pages).
        """
        url = f"https://api.wikimedia.org/service/lw/inference/v1/models/{model}:predict"
        try:
            return self.post(url, json_data=data)
        except ValueError as e:
            if "422" in str(e):
                logger.warning("Model %s returned 422 for input %s. "
                              "Revert-risk models cannot score revision 1 (new pages). "
                              "Fall back to articlequality model.", model, data)
            raise

    def pageviews(self, article: str, days: int = 30, project: str = "en.wikipedia") -> list:
        """Fetch daily pageviews for an article."""
        from datetime import datetime, timezone, timedelta
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        url = (
            f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
            f"{project}/all-access/all-agents/{article}/daily/"
            f"{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
        )
        data = self.get(url)
        return data.get("items", [])


# ── CLI entry point ──────────────────────────────────────────────────────────
def main():
    """CLI: Test connectivity to a Wikimedia API endpoint."""
    import argparse

    parser = argparse.ArgumentParser(description="Test Wikimedia API connectivity")
    parser.add_argument("--endpoint", default="enwiki",
                        choices=["enwiki", "wikidata", "commons", "sparql", "liftwing", "pageviews"],
                        help="API endpoint to test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    client = HttpClient()

    tests = {
        "enwiki": lambda c: c.get("https://en.wikipedia.org/w/api.php",
                                   params={"action": "query", "titles": "Albert Einstein", "format": "json"}),
        "wikidata": lambda c: c.wikidata_entity("Q937"),
        "commons": lambda c: c.get("https://commons.wikimedia.org/w/api.php",
                                    params={"action": "query", "list": "search", "srsearch": "Eiffel Tower",
                                            "srnamespace": "6", "format": "json"}),
        "sparql": lambda c: c.sparql("SELECT ?item WHERE { wd:Q937 wdt:P106 ?item. } LIMIT 5"),
        "liftwing": lambda c: c.lift_wing("revertrisk-language-agnostic", {"rev_id": 123456789, "lang": "en"}),
        "pageviews": lambda c: c.pageviews("Albert_Einstein", days=5),
    }

    if args.endpoint not in tests:
        print(f"Unknown endpoint: {args.endpoint}")
        print(f"Available: {', '.join(tests.keys())}")
        sys.exit(1)

    print(f"Testing {args.endpoint}...")
    try:
        result = tests[args.endpoint](client)
        print(f"✅ Success! Response keys: {list(result.keys())[:5]}")
        if args.verbose:
            print(json.dumps(result, indent=2)[:1000])
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
