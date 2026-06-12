"""Lightweight Python client for the PageTriage extension API.

Provides methods for listing unreviewed pages, checking review status,
and marking pages as reviewed/unreviewed (with appropriate permissions).

Usage:
    from assets.pagetriage_client import PageTriageClient

    client = PageTriageClient("enwiki")
    pages = client.list_unreviewed(limit=50)
    status = client.get_review_status("Albert Einstein")
"""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urljoin

import requests

# Wiki short name → API endpoint
WIKI_DOMAINS = {
    "enwiki": "https://en.wikipedia.org/w/api.php",
    "testwiki": "https://test.wikipedia.org/w/api.php",
    "ruwiki": "https://ru.wikipedia.org/w/api.php",
}

DEFAULT_UA = (
    "PageTriageClient/0.1 (https://github.com/fuzheado/npp-finder; "
    "npp-finder@example.com) PageTriageSkill"
)


class PageTriageClient:
    """Client for PageTriage-related MediaWiki API operations."""

    def __init__(
        self,
        wiki: str = "enwiki",
        user_agent: str | None = None,
    ):
        domain = WIKI_DOMAINS.get(wiki)
        if not domain:
            raise ValueError(
                f"Unknown wiki '{wiki}'. Known: {list(WIKI_DOMAINS.keys())}. "
                "PageTriage is primarily deployed on enwiki and testwiki."
            )
        self.api_url = domain
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent or DEFAULT_UA

    def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make a GET request to the Action API with retry-on-429."""
        backoff = 1.0
        for attempt in range(5):
            resp = self.session.get(self.api_url, params=params, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                retry = int(resp.headers.get("Retry-After", backoff))
                time.sleep(retry)
                backoff = min(backoff * 2, 60)
                continue
            if resp.status_code == 403:
                raise PermissionError(
                    f"403 Forbidden — check User-Agent. "
                    f"If you need patrol-level data, authenticate."
                )
            resp.raise_for_status()
        raise RuntimeError("Too many 429s — aborting")

    # ------------------------------------------------------------------
    # Listing unreviewed pages (requires patrol right)
    # ------------------------------------------------------------------

    def list_unreviewed(
        self, limit: int = 100, namespace: int = 0
    ) -> list[dict[str, Any]]:
        """Return list of unreviewed pages in the given namespace.

        Each entry contains keys: pageid, title, metadata (created_at,
        user_name, length, etc.).

        Requires the ``patrol`` user right.  Without it the API returns
        an empty result or a permission error.
        """
        params: dict[str, Any] = {
            "action": "pagetriagelist",
            "showunreviewed": 1,
            "noredirects": 1,
            "namespace": namespace,
            "limit": min(limit, 500),
            "format": "json",
        }
        data = self._get(params)

        if "error" in data:
            err = data["error"].get("info", "unknown error")
            if "permissiondenied" in data["error"].get("code", ""):
                raise PermissionError(
                    f"Permission denied: {err}. "
                    f"The pagetriagelist endpoint requires the patrol user right."
                )
            raise RuntimeError(f"API error: {err}")

        return data.get("query", {}).get("pagetriagelist", [])

    # ------------------------------------------------------------------
    # Checking review status (works without authentication)
    # ------------------------------------------------------------------

    def get_review_status(
        self, title: str
    ) -> dict[str, Any]:
        """Check page existence, length, and protection level.

        Returns::

            {
                "pageid": int,
                "exists": bool,
                "length": int,
                "protection": [{"type": str, "level": str, ...}]
            }

        This does **not** return the PageTriage review status (the
        ``ptrp_reviewed`` flag) because that field requires SQL replica
        access or the patrol right via ``pagetriagelist``.
        """
        data = self._get(
            {
                "action": "query",
                "titles": title,
                "prop": "info",
                "inprop": "protection",
                "format": "json",
            }
        )
        pages = data.get("query", {}).get("pages", {})
        for pid, p in pages.items():
            if pid == "-1":
                return {"pageid": None, "exists": False, "length": 0, "protection": []}
            return {
                "pageid": p.get("pageid"),
                "exists": "missing" not in p,
                "length": p.get("length", 0),
                "protection": p.get("protection", []),
            }
        return {"pageid": None, "exists": False, "length": 0, "protection": []}

    # ------------------------------------------------------------------
    # Finding new pages via recentchanges (no auth needed)
    # ------------------------------------------------------------------

    def fetch_new_pages(
        self, days: int = 7, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Return recently created mainspace pages.

        Each entry contains: pageid, revid, title, timestamp, user.

        Works for unauthenticated users but does **not** include patrol
        status (use the ``patrolmarks`` right via ``rcprop=patrolled`` to
        get that).
        """
        params: dict[str, Any] = {
            "action": "query",
            "list": "recentchanges",
            "rctype": "new",
            "rcnamespace": 0,
            "rcshow": "!redirect",
            "rclimit": min(limit, 500),
            "rcprop": "title|timestamp|ids|user",
            "format": "json",
        }
        data = self._get(params)
        pages: list[dict[str, Any]] = []
        for rc in data.get("query", {}).get("recentchanges", []):
            pages.append(
                {
                    "pageid": rc.get("pageid"),
                    "revid": rc.get("revid"),
                    "title": rc.get("title"),
                    "timestamp": rc.get("timestamp"),
                    "user": rc.get("user", "Unknown"),
                }
            )
        return pages
