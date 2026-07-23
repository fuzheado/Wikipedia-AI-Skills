"""
WikiProject banner parser for English Wikipedia talk pages.

Usage:
    from banner_parser import parse_banners

    banners = parse_banners("Albert Einstein")
    # → [
    #     {'project': 'WikiProject Physics', 'class': 'B', 'importance': 'Top'},
    #     {'project': 'WikiProject Biography', 'class': 'B', 'importance': 'Mid'},
    #     ...
    #   ]

Dependencies: requests. Parses the wikitext of Talk: pages to extract
WikiProject banner templates and their parameters.
"""

from __future__ import annotations

import re
from typing import Any


def _try_import_requests():
    """Import requests, returning None if unavailable."""
    try:
        import requests  # noqa: F811
        return requests
    except ImportError:
        return None


def _fetch_talk_wikitext(title: str, requests_mod) -> str:
    """Fetch wikitext of a Talk: page via the Action API."""
    headers = {
        "User-Agent": (
            "BannerParser/1.0 "
            "(https://github.com/fuzheado/Wikipedia-AI-Skills; tools@example.com)"
        )
    }
    params = {
        "action": "parse",
        "page": f"Talk:{title}",
        "prop": "wikitext",
        "format": "json",
    }
    resp = requests_mod.get(
        "https://en.wikipedia.org/w/api.php",
        params=params,
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    if "error" in data:
        error = data["error"]
        raise RuntimeError(
            f"API error: {error.get('code', 'unknown')} - {error.get('info', '')}"
        )

    wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
    return wikitext


def _parse_banner_template(banner_text: str) -> dict[str, str] | None:
    """Parse a single WikiProject banner template string.

    Example input:
        'WikiProject Physics|class=B|importance=Top'
    Returns:
        {'project': 'WikiProject Physics', 'class': 'B', 'importance': 'Top'}
    """
    # Split on | but not inside [[...]] or {{...}}
    parts = []
    current = ""
    depth_square = 0
    depth_curly = 0

    for ch in banner_text:
        if ch == "[":
            depth_square += 1
        elif ch == "]":
            depth_square -= 1
        elif ch == "{":
            depth_curly += 1
        elif ch == "}":
            depth_curly -= 1
        elif ch == "|" and depth_square == 0 and depth_curly == 0:
            parts.append(current.strip())
            current = ""
            continue
        current += ch
    parts.append(current.strip())

    if not parts:
        return None

    result: dict[str, str] = {"project": parts[0].strip()}

    for part in parts[1:]:
        if "=" in part:
            key, _, value = part.partition("=")
            key = key.strip().lower()
            value = value.strip()
            # Keep common parameters
            if key in (
                "class", "importance", "listas", "attention",
                "needs-infobox", "needs-photo", "needs-image",
                "small", "category", "auto",
            ):
                result[key] = value
            # Work group flags (e.g., s&a-work-group=yes)
            elif key.endswith("work-group") or key.endswith("task-force"):
                result[key] = value

    return result


def _extract_banners_from_wikitext(wikitext: str) -> list[dict[str, str]]:
    """Extract WikiProject banner templates from talk page wikitext."""
    banners: list[dict[str, str]] = []

    # Match {{WikiProject ...}} templates with balanced braces
    # Pattern: find {{WikiProject at top level, track brace depth
    pattern = re.compile(r'\{\{(WikiProject[^{}|]+)')
    for m in pattern.finditer(wikitext):
        start = m.start()
        inner_start = m.group(1)  # content after {{
        # Track brace depth from the opening {{
        depth = 1
        pos = m.end()
        content = inner_start
        while pos < len(wikitext) and depth > 0:
            if wikitext[pos:pos+2] == "{{":
                depth += 1
                content += "{{"
                pos += 2
            elif wikitext[pos:pos+2] == "}}":
                depth -= 1
                if depth == 0:
                    break
                content += "}}"
                pos += 2
            else:
                content += wikitext[pos]
                pos += 1

        parsed = _parse_banner_template(content)
        if parsed:
            banners.append(parsed)

    return banners


def parse_banners(title_or_wikitext: str) -> list[dict[str, str]]:
    """Parse WikiProject banners from a Wikipedia article or raw wikitext.

    Args:
        title_or_wikitext: Either a Wikipedia article title (e.g.,
            "Albert Einstein") or raw talk page wikitext starting with "{{".
            If the text starts with "{{", it's treated as wikitext.
            Otherwise, it's treated as a page title and fetched via API.

    Returns:
        List of dicts with keys: project, class, importance, and any
        work-group flags found in the banner.
    """
    if title_or_wikitext.strip().startswith("{{"):
        # Treat as raw wikitext
        return _extract_banners_from_wikitext(title_or_wikitext)

    # Treat as page title — fetch from API
    requests_mod = _try_import_requests()
    if not requests_mod:
        raise ImportError(
            "requests is required for API-based banner parsing. "
            "Install with: pip install requests"
        )

    wikitext = _fetch_talk_wikitext(title_or_wikitext, requests_mod)
    return _extract_banners_from_wikitext(wikitext)
