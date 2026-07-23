"""
WikiProject discovery tools for English Wikipedia.

Usage:
    from discover_wikiprojects import find_project, list_active

    # Find the most relevant project for a topic
    project = find_project("quantum physics")  # → "WikiProject Physics"

    # List active WikiProjects
    active = list_active()
    print(f"{len(active)} active WikiProjects")

Dependencies: requests (for API calls). Falls back to offline lookup if
requests is unavailable.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from typing import Optional

# ── Cached project index ───────────────────────────────────────────────────
# A curated mapping of topic keywords → WikiProject names. This is used as a
# fallback when the API is unavailable and as a pre-filter before API search.

_TOPIC_MAP = {
    "physics": "WikiProject Physics",
    "quantum": "WikiProject Physics",
    "chemistry": "WikiProject Chemistry",
    "biology": "WikiProject Biology",
    "mathematics": "WikiProject Mathematics",
    "maths": "WikiProject Mathematics",
    "math": "WikiProject Mathematics",
    "computer science": "WikiProject Computing",
    "computing": "WikiProject Computing",
    "programming": "WikiProject Computing",
    "astronomy": "WikiProject Astronomy",
    "medicine": "WikiProject Medicine",
    "medical": "WikiProject Medicine",
    "history": "WikiProject History",
    "military history": "WikiProject Military history",
    "philosophy": "WikiProject Philosophy",
    "literature": "WikiProject Literature",
    "novels": "WikiProject Novels",
    "poetry": "WikiProject Poetry",
    "film": "WikiProject Film",
    "films": "WikiProject Film",
    "movies": "WikiProject Film",
    "music": "WikiProject Music",
    "musician": "WikiProject Biography",
    "visual arts": "WikiProject Visual arts",
    "painting": "WikiProject Visual arts",
    "architecture": "WikiProject Architecture",
    "geography": "WikiProject Geography",
    "rivers": "WikiProject Rivers",
    "mountains": "WikiProject Mountains",
    "cities": "WikiProject Cities",
    "countries": "WikiProject Countries",
    "politics": "WikiProject Politics",
    "government": "WikiProject Politics",
    "law": "WikiProject Law",
    "economics": "WikiProject Economics",
    "business": "WikiProject Business",
    "companies": "WikiProject Companies",
    "sports": "WikiProject Sports",
    "football": "WikiProject Football",
    "soccer": "WikiProject Football",
    "basketball": "WikiProject Basketball",
    "cricket": "WikiProject Cricket",
    "baseball": "WikiProject Baseball",
    "olympics": "WikiProject Olympics",
    "video games": "WikiProject Video games",
    "gaming": "WikiProject Video games",
    "anime": "WikiProject Anime and manga",
    "manga": "WikiProject Anime and manga",
    "comics": "WikiProject Comics",
    "food": "WikiProject Food and drink",
    "drink": "WikiProject Food and drink",
    "wine": "WikiProject Wine",
    "beer": "WikiProject Beer",
    "religion": "WikiProject Religion",
    "christianity": "WikiProject Christianity",
    "islam": "WikiProject Islam",
    "judaism": "WikiProject Judaism",
    "buddhism": "WikiProject Buddhism",
    "transport": "WikiProject Transport",
    "railways": "WikiProject Trains",
    "aviation": "WikiProject Aviation",
    "automobiles": "WikiProject Automobiles",
    "education": "WikiProject Education",
    "universities": "WikiProject Universities",
    "biography": "WikiProject Biography",
    "biographies": "WikiProject Biography",
    "women": "WikiProject Women",
    "lgbt": "WikiProject LGBT studies",
    "feminism": "WikiProject Feminism",
    "ecology": "WikiProject Ecology",
    "environment": "WikiProject Environment",
    "climate": "WikiProject Climate change",
    "space": "WikiProject Spaceflight",
    "nasa": "WikiProject Spaceflight",
}


def _try_import_requests():
    """Import requests, returning None if unavailable."""
    try:
        import requests  # noqa: F811
        return requests
    except ImportError:
        return None


def _api_search(topic: str, requests_mod) -> list[str]:
    """Search Wikipedia: namespace for WikiProjects matching topic.

    Returns list of page titles, best match first.
    """
    headers = {
        "User-Agent": (
            "WikiProjectDiscovery/1.0 "
            "(https://github.com/fuzheado/Wikipedia-AI-Skills; tools@example.com)"
        )
    }
    params = {
        "action": "query",
        "list": "search",
        "srsearch": f"WikiProject {topic}",
        "srnamespace": "4",  # Wikipedia: namespace
        "srlimit": "10",
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
    results = data.get("query", {}).get("search", [])
    return [r["title"] for r in results if "WikiProject" in r["title"]]


def find_project(topic: str) -> Optional[str]:
    """Find the most relevant WikiProject for a topic.

    Searches first against curated keyword map, then falls back to the
    Wikipedia Action API search.

    Args:
        topic: Natural language topic (e.g., "quantum physics", "soccer").

    Returns:
        WikiProject page title (e.g., "WikiProject Physics"), or None.
    """
    # 1. Check curated keyword map (case-insensitive)
    topic_lower = topic.strip().lower()
    if topic_lower in _TOPIC_MAP:
        return _TOPIC_MAP[topic_lower]

    # 2. Substring match against keyword map
    best_match = None
    best_len = 0
    for keyword, project in _TOPIC_MAP.items():
        if keyword in topic_lower and len(keyword) > best_len:
            best_match = project
            best_len = len(keyword)
    if best_match:
        return best_match

    # 3. Try API search
    requests_mod = _try_import_requests()
    if requests_mod:
        try:
            results = _api_search(topic, requests_mod)
            if results:
                return results[0]
        except Exception:
            pass

    return None


def list_active() -> list[str]:
    """List active WikiProjects from the API.

    Returns:
        List of WikiProject page titles that are currently active.
    """
    requests_mod = _try_import_requests()
    if not requests_mod:
        # Fallback: return known active projects from keyword map
        return sorted(set(_TOPIC_MAP.values()))

    headers = {
        "User-Agent": (
            "WikiProjectDiscovery/1.0 "
            "(https://github.com/fuzheado/Wikipedia-AI-Skills; tools@example.com)"
        )
    }
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Category:Active_WikiProjects",
        "cmtype": "page",
        "cmlimit": "max",
        "format": "json",
    }
    projects = []
    try:
        while True:
            resp = requests_mod.get(
                "https://en.wikipedia.org/w/api.php",
                params=params,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            members = data.get("query", {}).get("categorymembers", [])
            projects.extend(m["title"] for m in members)

            if "continue" in data:
                params["cmcontinue"] = data["continue"]["cmcontinue"]
                time.sleep(0.3)
            else:
                break
    except Exception:
        # Fallback to keyword map
        return sorted(set(_TOPIC_MAP.values()))

    return projects
