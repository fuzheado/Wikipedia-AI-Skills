#!/usr/bin/env python3
"""Simulate patrolling the latest edit to a Wikipedia page.

Fetches the most recent revision to a page, scores it with revert-risk,
goodfaith, and damaging models, then produces a patrol verdict.

This is the closest thing to a real production use case for Lift Wing
that you can run interactively.

Usage:
    python3 patrol_simulator.py Albert_Einstein
    python3 patrol_simulator.py "Donald Trump" --lang en --threshold 0.3
    python3 patrol_simulator.py --random     # pick a random popular page
"""

import argparse
import json
import os
import sys
import time
import urllib.parse

import requests


BASE_URL = "https://api.wikimedia.org/service/lw/inference/v1/models"
USER_AGENT = "PatrolSimulator/1.0 (user@example.com) ContentGapResearch"
REST_API = "https://en.wikipedia.org/api/rest_v1"
ACTION_API = "https://en.wikipedia.org/w/api.php"


def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Content-Type": "application/json"})
    return s


def fetch_latest_revision(page_title: str, lang: str = "en") -> dict | None:
    """Fetch the latest revision of a page."""
    domain = f"{lang}.wikipedia.org"
    url = f"https://{domain}/api/rest_v1/page/summary/{urllib.parse.quote(page_title, safe='')}"
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"⚠  Could not fetch page: {e}", file=sys.stderr)
        return None


def fetch_recent_edit(page_title: str, lang: str = "en") -> dict | None:
    """Fetch the most recent edit event for a page (user, timestamp, comment)."""
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": page_title.replace(" ", "_"),
        "rvlimit": 1,
        "rvprop": "ids|user|timestamp|comment|size|flags",
        "format": "json",
    }
    try:
        resp = requests.get(
            ACTION_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        for page in data.get("query", {}).get("pages", {}).values():
            if "revisions" in page and page["revisions"]:
                rev = page["revisions"][0]
                rev["page_title"] = page.get("title", page_title)
                return rev
        return None
    except requests.exceptions.RequestException as e:
        print(f"⚠  Could not fetch edit: {e}", file=sys.stderr)
        return None


def fetch_random_page() -> str | None:
    """Fetch a random Wikipedia article title."""
    params = {
        "action": "query",
        "list": "random",
        "rnnamespace": 0,
        "rnlimit": 1,
        "format": "json",
    }
    try:
        resp = requests.get(
            ACTION_API,
            params=params,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["query"]["random"][0]["title"].replace(" ", "_")
    except Exception as e:
        print(f"⚠  Could not fetch random page: {e}", file=sys.stderr)
        return None


def call_liftwing(session, model: str, payload: dict) -> dict | None:
    """Call a Lift Wing model."""
    url = f"{BASE_URL}/{model}:predict"
    try:
        resp = session.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"  ⚠  {model}: {e}", file=sys.stderr)
        return None


def get_verdict(revert_prediction: bool, revert_prob: float, threshold: float) -> str:
    """Determine a patrol verdict."""
    if revert_prediction and revert_prob > threshold:
        return "🔴 FLAG FOR REVIEW"
    elif revert_prediction:
        return "🟡 WEAK FLAG"
    elif revert_prob > threshold:
        return "🟡 WEAK FLAG (low confidence but elevated risk)"
    else:
        return "🟢 PASS"


def get_edit_emoji(comment: str) -> str:
    """Add an emoji based on edit summary."""
    c = comment.lower() if comment else ""
    if any(w in c for w in ["revert", "rv", "undo", "rollback"]):
        return "↩️"
    if any(w in c for w in ["vandal", "spam", "test"]):
        return "🚨"
    if "/*" in c:
        return "📝"
    return "✏️"


def main():
    parser = argparse.ArgumentParser(
        description="Simulate patrolling the latest edit to a Wikipedia page",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("page_title", nargs="?", help="Wikipedia page title")
    parser.add_argument("--lang", default="en", help="Language code (default: en)")
    parser.add_argument(
        "--threshold", type=float, default=0.3,
        help="Revert risk threshold for flagging (default: 0.3)"
    )
    parser.add_argument("--random", action="store_true", help="Pick a random page")
    parser.add_argument("--rev-id", type=int, help="Use a specific revision ID")

    args = parser.parse_args()

    if args.random:
        title = fetch_random_page()
        if not title:
            sys.exit(1)
        print(f"🎲 Random page: {title.replace('_', ' ')}\n")
    elif args.page_title:
        title = args.page_title.replace(" ", "_")
    else:
        parser.print_help()
        sys.exit(1)

    session = get_session()

    # ── Fetch page info and latest edit ──────────────────────────────────────
    print(f"📄 Fetching page info for '{title.replace('_', ' ')}'...")
    page = fetch_latest_revision(title, args.lang)
    if not page:
        sys.exit(1)

    rev_id = args.rev_id or page.get("revision")
    if not rev_id:
        print("❌ No revision ID found.", file=sys.stderr)
        sys.exit(1)

    print(f"   Revision: {rev_id}")
    print(f"   Extract:  {page.get('extract', '')[:120]}...")
    print()

    # Fetch the edit metadata
    edit = fetch_recent_edit(title, args.lang)
    if edit:
        emoji = get_edit_emoji(edit.get("comment", ""))
        print(f"{emoji} Latest edit by {edit.get('user', 'unknown')}")
        print(f"   Timestamp: {edit.get('timestamp', '?')}")
        print(f"   Comment:   {edit.get('comment', '(none)')}")
        print(f"   Size:      {edit.get('size', '?')} bytes")
        print()

    # ── Score with revert-risk ──────────────────────────────────────────────
    print("🧠 Scoring edit quality...")

    # Model 1: Revert risk (modern)
    print("  [1/3] revertrisk-language-agnostic...", end=" ", flush=True)
    rr = call_liftwing(
        session, "revertrisk-language-agnostic",
        {"rev_id": rev_id, "lang": args.lang}
    )
    if rr:
        rr_pred = rr["output"]["prediction"]
        rr_prob = rr["output"]["probabilities"]["true"]
        print(f"{'RISKY' if rr_pred else 'SAFE'} (p={rr_prob:.1%})")
    else:
        rr_pred, rr_prob = False, 0.0
        print("FAILED")
    time.sleep(0.15)

    # Model 2: Goodfaith (Revscoring, frozen)
    print("  [2/3] enwiki-goodfaith...", end=" ", flush=True)
    gf = call_liftwing(
        session, "enwiki-goodfaith",
        {"rev_id": rev_id}
    )
    if gf:
        try:
            gf_pred = gf["enwiki"]["scores"][str(rev_id)]["goodfaith"]["score"]["prediction"]
            gf_conf = gf["enwiki"]["scores"][str(rev_id)]["goodfaith"]["score"]["probability"]["true"]
            print(f"{'GOODFAITH' if gf_pred else 'BADFAITH'} (conf={gf_conf:.1%})")
        except (KeyError, TypeError):
            print("PARSE ERROR")
            gf_pred, gf_conf = True, 0.0
    else:
        gf_pred, gf_conf = True, 0.0
        print("FAILED")
    time.sleep(0.15)

    # Model 3: Damaging (Revscoring, frozen)
    print("  [3/3] enwiki-damaging...", end=" ", flush=True)
    dm = call_liftwing(
        session, "enwiki-damaging",
        {"rev_id": rev_id}
    )
    if dm:
        try:
            dm_pred = dm["enwiki"]["scores"][str(rev_id)]["damaging"]["score"]["prediction"]
            dm_conf = dm["enwiki"]["scores"][str(rev_id)]["damaging"]["score"]["probability"]["false"]
            print(f"{'DAMAGING' if dm_pred else 'NOT_DAMAGING'} (safe_conf={dm_conf:.1%})")
        except (KeyError, TypeError):
            print("PARSE ERROR")
            dm_pred, dm_conf = False, 0.0
    else:
        dm_pred, dm_conf = False, 0.0
        print("FAILED")

    # ── Verdict ──────────────────────────────────────────────────────────────
    print()
    print("═" * 55)
    verdict = get_verdict(rr_pred, rr_prob, args.threshold)
    print(f"   PATROL VERDICT: {verdict}")
    print("═" * 55)
    print()
    print(f"   Revert risk:     {rr_prob:.1%} {'🔴' if rr_pred else '🟢'}")
    print(f"   Goodfaith:       {gf_conf:.1%} {'🟢' if gf_pred else '🔴'}")
    print(f"   Damaging:        {1-dm_conf:.1%} {'🔴' if dm_pred else '🟢'}")
    print(f"   Threshold:       {args.threshold:.0%}")
    print()

    # ── Summary ──────────────────────────────────────────────────────────────
    if rr_pred:
        print("⚠️  This edit may need human review.")
        print(f"   Visit: https://en.wikipedia.org/w/index.php?diff={rev_id}")
    else:
        print("✅ This edit looks safe. No action needed.")


if __name__ == "__main__":
    main()
