#!/usr/bin/env python3
"""
ws_proofread_checker.py — Query Wikisource proofreading status.

Provides:
  - ProofreadChecker: query proofreading stats for an Index, list pages by
    quality, and get individual page status

Usage:
    from ws_proofread_checker import ProofreadChecker

    checker = ProofreadChecker("en")
    stats = checker.get_work_stats("Index:Pride and Prejudice")
    # stats == {"total": 400, "without_text": 10, "problematic": 5,
    #           "proofread": 200, "validated": 185, "percent_done": 96.25}

    pages = checker.get_pages_by_quality("Index:Pride and Prejudice", quality=2)
    # pages == [{"title": "Page:Pride and Prejudice/1", "quality": 2}, ...]

    status = checker.get_page_status("Page:Pride and Prejudice/1")
    # status == {"title": "Page:Pride and Prejudice/1",
    #            "quality": 2, "quality_label": "Proofread"}
"""

from typing import Optional
import requests


class ProofreadChecker:
    """Query Wikisource proofreading status via the API."""

    QUALITY_LABELS = {
        0: "Without text",
        1: "Problematic",
        2: "Proofread",
        3: "Validated",
    }

    def __init__(self, wiki: str = "en", user_agent: str = ""):
        """
        Args:
            wiki: Language code (e.g., 'en', 'fr', 'de')
            user_agent: Custom User-Agent string
        """
        self.api = f"https://{wiki}.wikisource.org/w/api.php"
        default_ua = "ProofreadChecker/1.0 (https://example.com; user@example.com)"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or default_ua,
        })

    def get_work_stats(self, index_title: str) -> dict:
        """
        Get proofreading statistics for a work.
        
        Args:
            index_title: Index page title (e.g., 'Index:Example Book.pdf')
        
        Returns:
            {"total": N, "without_text": N, "problematic": N,
             "proofread": N, "validated": N, "percent_done": float}
        """
        resp = self.session.get(self.api, params={
            "action": "query",
            "titles": index_title,
            "prop": "proofreadinfo",
            "piprop": "quality",
            "format": "json",
        })
        resp.raise_for_status()
        data = resp.json()

        stats = {
            "without_text": 0,
            "problematic": 0,
            "proofread": 0,
            "validated": 0,
            "total": 0,
            "percent_done": 0.0,
        }

        pages = data.get("query", {}).get("pages", {})
        for page_id, page_data in pages.items():
            if page_id == "-1":
                continue

            pr_data = page_data.get("proofreadinfo", {})
            if "quality" in pr_data:
                for q in pr_data["quality"].values():
                    quality = int(q)
                    mapping = {0: "without_text", 1: "problematic",
                               2: "proofread", 3: "validated"}
                    key = mapping.get(quality)
                    if key:
                        stats[key] += 1
                    stats["total"] += 1

        if stats["total"] > 0:
            done = stats["proofread"] + stats["validated"]
            stats["percent_done"] = round(done / stats["total"] * 100, 1)

        return stats

    def get_page_status(self, page_title: str) -> dict:
        """
        Get the proofread status of a single Page: page.
        
        Args:
            page_title: Page title (e.g., 'Page:Example/1')
        
        Returns:
            {"title": str, "quality": int, "quality_label": str}
        """
        resp = self.session.get(self.api, params={
            "action": "query",
            "titles": page_title,
            "prop": "proofread",
            "format": "json",
        })
        resp.raise_for_status()
        data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        for pid, pdata in pages.items():
            if pid != "-1":
                quality = pdata.get("pagequality", 0)
                return {
                    "title": pdata.get("title", page_title),
                    "quality": quality,
                    "quality_label": self.QUALITY_LABELS.get(quality, "Unknown"),
                }
        return {"title": page_title, "quality": None, "quality_label": "Not found"}

    def get_pages_by_quality(self, index_title: str, quality: int) -> list[dict]:
        """
        List all pages in an Index at a specific quality level.
        
        Args:
            index_title: Index page title
            quality: Quality level (0-3)
        
        Returns:
            List of {"title": str, "quality": int}
        """
        resp = self.session.get(self.api, params={
            "action": "query",
            "list": "proofreadpages",
            "pipqual": quality,
            "pipindex": index_title,
            "pilimit": "max",
            "format": "json",
        })
        resp.raise_for_status()
        data = resp.json()

        pages = []
        for page in data.get("query", {}).get("proofreadpages", []):
            pages.append({
                "title": page.get("title", ""),
                "quality": page.get("quality", quality),
            })
        return pages

    def get_progress_summary(self, index_title: str) -> str:
        """Return a human-readable progress summary string."""
        stats = self.get_work_stats(index_title)
        if stats["total"] == 0:
            return f"No pages found for {index_title}"
        return (
            f"{stats['total']} pages • "
            f"{stats['validated']} validated • "
            f"{stats['proofread']} proofread • "
            f"{stats['problematic']} problematic • "
            f"{stats['without_text']} without text • "
            f"{stats['percent_done']}% complete"
        )
