#!/usr/bin/env python3
"""Scan a Wikipedia page for dead links and suggest archive replacements.

Usage:
    python3 dead_link_scanner.py Albert_Einstein
    python3 dead_link_scanner.py "Albert Einstein" --lang fr
    python3 dead_link_scanner.py Albert_Einstein --action report
    python3 dead_link_scanner.py Albert_Einstein --action fix     (generates corrected wikitext)
    python3 dead_link_scanner.py Albert_Einstein --output json
"""

import argparse
import json
import re
import sys
import time
import urllib.parse

import requests


USER_AGENT = "DeadLinkScanner/1.0 (user@example.com) ContentGapResearch"
ACTION_API = "https://{lang}.wikipedia.org/w/api.php"
IA_AVAILABLE = "https://archive.org/wayback/available"


def fetch_wikitext(page_title: str, lang: str = "en") -> str | None:
    """Fetch the raw wikitext of a page."""
    url = ACTION_API.format(lang=lang)
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json",
    }
    try:
        resp = requests.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data["parse"]["wikitext"]["*"]
    except (KeyError, requests.exceptions.RequestException) as e:
        print(f"⚠  Could not fetch page: {e}", file=sys.stderr)
        return None


def extract_citation_urls(wikitext: str) -> list[dict]:
    """Extract all citation URLs with their context from wikitext."""
    citations = []

    # Template-based citations with url= parameter
    for m in re.finditer(
        r"(\{\{(cite\s+\w+)([^}]*)\}\})", wikitext, re.IGNORECASE
    ):
        full_template = m.group(1)
        params_text = m.group(3)

        url_m = re.search(r"\|?\s*url\s*=\s*([^|\n}]+)", params_text, re.IGNORECASE)
        archive_m = re.search(r"\|?\s*archive-url\s*=\s*([^|\n}]+)", params_text, re.IGNORECASE)
        status_m = re.search(r"\|?\s*url-status\s*=\s*(\w+)", params_text, re.IGNORECASE)

        if url_m:
            url = url_m.group(1).strip()
            if url.startswith("http"):
                citations.append({
                    "type": "template",
                    "url": url,
                    "archive_url": archive_m.group(1).strip() if archive_m else None,
                    "url_status": status_m.group(1).strip() if status_m else "live",
                    "template": full_template,
                })

    # Bare URLs in ref tags
    for m in re.finditer(r"<ref>(https?://[^\s<]+)</ref>", wikitext):
        citations.append({
            "type": "bare",
            "url": m.group(1),
            "archive_url": None,
            "url_status": "unknown",
            "template": m.group(0),
        })

    return citations


def check_url(url: str, timeout: int = 10) -> dict:
    """Check if a URL is live."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
            allow_redirects=False,
        )
        if resp.status_code in (200, 304):
            return {"status": "live", "code": resp.status_code}
        elif resp.status_code in (301, 302, 303, 307, 308):
            return {"status": "redirect", "code": resp.status_code,
                    "location": resp.headers.get("Location", "?")}
        else:
            return {"status": "dead", "code": resp.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}


def check_wayback(url: str) -> dict | None:
    """Check Wayback Machine for an existing archive."""
    try:
        resp = requests.get(
            IA_AVAILABLE,
            params={"url": url},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        snap = data.get("archived_snapshots", {}).get("closest")
        if snap:
            return {"archive_url": snap["url"], "timestamp": snap["timestamp"]}
        return None
    except requests.exceptions.RequestException:
        return None


def build_fix_suggestion(citation: dict, wayback_result: dict | None) -> str | None:
    """Build a corrected citation template with archive URL added."""
    if citation["type"] == "bare":
        return None  # Too complex to auto-fix bare URLs

    if citation["url_status"] == "dead" and wayback_result:
        # Add archive-url and archive-date to the template
        template = citation["template"]
        archive_url = wayback_result["archive_url"]
        ts = wayback_result["timestamp"]
        archive_date = f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}" if len(ts) >= 8 else ts[:8]

        # Insert archive-url and archive-date before the closing }}
        fixed = template.rstrip("}")
        fixed += f" |archive-url={archive_url}\n |archive-date={archive_date}\n |url-status=dead\n}}"
        return fixed

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Scan a Wikipedia page for dead links and suggest archive replacements",
    )
    parser.add_argument("page_title", help="Wikipedia page title")
    parser.add_argument("--lang", default="en", help="Language code (default: en)")
    parser.add_argument("--action", choices=["report", "fix"], default="report",
                       help="'report' to show dead links, 'fix' to generate corrected wikitext")
    parser.add_argument("--output", choices=["text", "json"], default="text")

    args = parser.parse_args()
    page_title = args.page_title.replace(" ", "_")

    print(f"🔍 Scanning: {page_title} ({args.lang})", file=sys.stderr)

    wikitext = fetch_wikitext(page_title, args.lang)
    if not wikitext:
        sys.exit(1)

    citations = extract_citation_urls(wikitext)
    print(f"📊 Found {len(citations)} citation URLs", file=sys.stderr)
    print(file=sys.stderr)

    results = []

    for i, cite in enumerate(citations):
        print(f"  [{i+1}/{len(citations)}] Checking: {cite['url'][:80]}...", file=sys.stderr)

        check = check_url(cite["url"])
        wayback = check_wayback(cite["url"]) if check["status"] != "live" else None
        fix = build_fix_suggestion(cite, wayback) if args.action == "fix" else None

        result = {
            "url": cite["url"],
            "type": cite["type"],
            "status": check["status"],
            "http_code": check.get("code"),
            "has_archive": wayback is not None,
            "archive_url": wayback["archive_url"] if wayback else None,
            "fix_suggestion": fix,
        }
        results.append(result)

        if check["status"] == "live":
            print(f"     ✅ Live (HTTP {check['code']})", file=sys.stderr)
        elif check["status"] == "redirect":
            print(f"     🔀 Redirect to {check.get('location', '?')[:60]}", file=sys.stderr)
        elif check["status"] == "dead":
            msg = f"     ❌ Dead (HTTP {check['code']})"
            if wayback:
                msg += f" — Archived at {wayback['archive_url']}"
            print(msg, file=sys.stderr)
        else:
            print(f"     ⚠  Error: {check.get('error', '?')}", file=sys.stderr)

        time.sleep(0.2)  # Rate limiting

    if args.output == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        dead = [r for r in results if r["status"] == "dead"]
        errors = [r for r in results if r["status"] == "error"]
        redirects = [r for r in results if r["status"] == "redirect"]

        print(f"\n{'═' * 55}")
        print(f"📋 Report for {page_title}")
        print(f"{'═' * 55}")
        print(f"  Total citations: {len(results)}")
        print(f"  ✅ Live:          {len(results) - len(dead) - len(errors) - len(redirects)}")
        print(f"  🔀 Redirects:     {len(redirects)}")
        print(f"  ❌ Dead:          {len(dead)}")
        print(f"  ⚠  Errors:        {len(errors)}")
        archived = sum(1 for r in dead if r["has_archive"])
        print(f"  📦 Archived:      {archived}/{len(dead)}")
        print()

        if dead:
            print("❌ Dead links needing attention:")
            for r in dead:
                print(f"  • {r['url'][:100]}")
                if r["has_archive"]:
                    print(f"    Archive: {r['archive_url']}")

        if args.action == "fix":
            fixes = [r for r in results if r.get("fix_suggestion")]
            if fixes:
                print(f"\n🔧 Generated fixes for {len(fixes)} citations:")
                for r in fixes:
                    print(f"\n  From: {r['url'][:80]}")
                    print(f"  To:   {r['fix_suggestion'][:200]}...")


if __name__ == "__main__":
    main()
