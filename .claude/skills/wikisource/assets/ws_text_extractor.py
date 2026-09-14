#!/usr/bin/env python3
"""
ws_text_extractor.py — Extract text from Wikisource pages.

Provides:
  - TextExtractor: fetch and clean Wikisource text layers, stripping
    header/footer templates and formatting

Usage:
    from ws_text_extractor import TextExtractor

    extractor = TextExtractor("en")
    text = extractor.get_page_text("Page:Pride and Prejudice/1")
    # text == "It is a truth universally acknowledged..."

    all_text = extractor.get_work_text("Index:Pride and Prejudice",
                                       from_page=1, to_page=10)
    # all_text == "..." (concatenated, with page boundaries)
"""

from typing import Optional
import re
import requests


class TextExtractor:
    """Extract and clean text from Wikisource pages."""

    HEADER_FOOTER_PATTERNS = [
        (r'\{\{header[^}]*\}\}', ''),
        (r'\{\{footer[^}]*\}\}', ''),
        (r'\{\{nop\}\}', ''),
        (r'\{\{c\|[^}]*\}\}', ''),
        (r'\{\{larger\|[^}]*\}\}', ''),
        (r'\{\{smaller\|[^}]*\}\}', ''),
        (r'\{\{gap\}\}', ' '),
        (r'<pages[^>]*/>', ''),
        (r'\{\{—\}\}', '—'),
        (r'\{\{—\}\}', '—'),
        (r'\{\{hws\|([^}]*)\|([^}]*)\}\}', r'\1'),  # {{hws|start|end}}
        (r'\{\{hwe\|([^}]*)\|([^}]*)\}\}', r'\1'),  # {{hwe|start|end}}
        (r'\{\{—\<\!\-\-rh\-\-\>', '—'),
        (r'\<\!\-\-rh\-\-\>\}\}', ''),
    ]

    def __init__(self, wiki: str = "en", user_agent: str = ""):
        """
        Args:
            wiki: Language code (e.g., 'en', 'fr', 'de')
            user_agent: Custom User-Agent string
        """
        self.api = f"https://{wiki}.wikisource.org/w/api.php"
        default_ua = "TextExtractor/1.0 (https://example.com; user@example.com)"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or default_ua,
        })

    def get_page_text(self, page_title: str, strip_markup: bool = True) -> Optional[str]:
        """
        Get the cleaned text from a Wikisource Page: page.
        
        Args:
            page_title: Full page title (e.g., 'Page:Pride and Prejudice/1')
            strip_markup: If True, strip header/footer and formatting templates
        
        Returns:
            Cleaned text, or None if the page doesn't exist.
        """
        resp = self.session.get(self.api, params={
            "action": "parse",
            "page": page_title,
            "prop": "wikitext",
            "format": "json",
        })
        resp.raise_for_status()
        data = resp.json()

        if "parse" not in data or "wikitext" not in data["parse"]:
            return None

        wikitext = data["parse"]["wikitext"]["*"]

        if strip_markup:
            text = self._strip_markup(wikitext)
        else:
            text = wikitext

        # Normalize whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def get_work_text(
        self,
        index_title: str,
        from_page: Optional[int] = None,
        to_page: Optional[int] = None,
    ) -> str:
        """
        Get the compiled text for a range of pages in a work.
        
        This reconstructs what the main namespace page shows by fetching
        individual Page: pages.
        
        Args:
            index_title: Index page title
            from_page: First page number (1-indexed)
            to_page: Last page number (inclusive)
        
        Returns:
            Concatenated text from all pages in the range.
        """
        if from_page is None:
            from_page = 1
        if to_page is None:
            to_page = from_page

        all_text = []
        for page_num in range(from_page, to_page + 1):
            # Extract base work name from index title
            work_name = re.sub(r'^Index:', '', index_title)
            work_name = re.sub(r'\.(djvu|pdf)$', '', work_name, flags=re.IGNORECASE)

            page_title = f"Page:{work_name}/{page_num}"
            text = self.get_page_text(page_title)
            if text:
                all_text.append(f"--- Page {page_num} ---\n{text}")

        return "\n\n".join(all_text)

    def _strip_markup(self, wikitext: str) -> str:
        """Remove Wikisource formatting templates from wikitext."""
        text = wikitext
        for pattern, replacement in self.HEADER_FOOTER_PATTERNS:
            text = re.sub(pattern, replacement, text)
        # Remove remaining template invocations
        text = re.sub(r'\{\{[^}]*\}\}', '', text)
        # Remove HTML comments
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        return text

    def page_exists(self, page_title: str) -> bool:
        """Check if a Page: page exists."""
        resp = self.session.get(self.api, params={
            "action": "query",
            "titles": page_title,
            "format": "json",
        })
        resp.raise_for_status()
        data = resp.json()
        for pid in data.get("query", {}).get("pages", {}):
            if pid != "-1":
                return True
        return False
