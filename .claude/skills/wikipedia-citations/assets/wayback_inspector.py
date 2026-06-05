#!/usr/bin/env python3
"""Check Wayback Machine for URL archives, save new ones.

Usage:
    python3 wayback_inspector.py https://example.com/article
    python3 wayback_inspector.py https://example.com/article --save
    python3 wayback_inspector.py urls.txt  (one URL per line)
"""

import argparse
import json
import sys
import time
import urllib.parse

import requests


USER_AGENT = "WaybackInspector/1.0 (user@example.com) ContentGapResearch"
IA_AVAILABLE = "https://archive.org/wayback/available"
IA_SAVE = "https://web.archive.org/save/"


def check_archive(url: str) -> dict | None:
    """Check if a URL has an archive on the Wayback Machine."""
    params = {"url": url}
    try:
        resp = requests.get(
            IA_AVAILABLE, params=params,
            headers={"User-Agent": USER_AGENT}, timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        snap = data.get("archived_snapshots", {}).get("closest")
        if snap:
            return {
                "url": url,
                "archive_url": snap.get("url"),
                "timestamp": snap.get("timestamp"),
                "status": snap.get("status"),
            }
        return {"url": url, "archive_url": None}
    except requests.exceptions.RequestException as e:
        return {"url": url, "error": str(e)}


def save_archive(url: str) -> dict:
    """Request the Wayback Machine to save a URL."""
    save_url = f"{IA_SAVE}{url}"
    try:
        resp = requests.post(
            save_url,
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        if resp.status_code == 200:
            return {"url": url, "saved": True, "status": resp.status_code}
        else:
            return {"url": url, "saved": False, "status": resp.status_code}
    except requests.exceptions.RequestException as e:
        return {"url": url, "saved": False, "error": str(e)}


def format_result(result: dict) -> str:
    """Format a check result for display."""
    url = result.get("url", "?")
    if "error" in result:
        return f"  ⚠  {url}: ERROR — {result['error']}"

    archive_url = result.get("archive_url")
    if archive_url:
        ts = result.get("timestamp", "")
        readable = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else ts
        return f"  ✅ {url}\n     Archived: {readable}\n     {archive_url}"
    else:
        return f"  ❌ {url}: No archive found"


def main():
    parser = argparse.ArgumentParser(
        description="Check Wayback Machine for URL archives and optionally save new ones",
    )
    parser.add_argument("target", help="URL or file path (file: prefix or .txt file)")
    parser.add_argument("--save", action="store_true", help="Save pages without archives")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests")

    args = parser.parse_args()

    # Determine if target is a URL or a file
    if args.target.startswith("http"):
        urls = [args.target]
    elif args.target.startswith("file:") or args.target.endswith(".txt"):
        path = args.target[5:] if args.target.startswith("file:") else args.target
        with open(path) as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().startswith("http")]
    else:
        urls = [args.target]

    results = []

    for i, url in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] Checking: {url[:80]}...", file=sys.stderr)

        result = check_archive(url)
        results.append(result)

        if args.save and not result.get("archive_url"):
            print(f"  → Saving to Wayback Machine...", file=sys.stderr)
            save_result = save_archive(url)
            result["save_attempt"] = save_result
            time.sleep(5)  # Be gentle with the save endpoint

        if not args.json:
            print(format_result(result), file=sys.stderr)

        if i < len(urls) - 1:
            time.sleep(args.delay)

    if args.json:
        print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
