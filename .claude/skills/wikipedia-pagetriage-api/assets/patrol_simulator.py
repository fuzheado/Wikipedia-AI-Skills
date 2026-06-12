#!/usr/bin/env python3
"""Patrol Simulator — demonstrates the two-pass NPP pipeline.

Fetches new pages, analyzes references for URL presence, then enriches
only the matching pages with metadata.  This is the same architecture
used by the npp-finder tool, packaged here as a reusable demo.

Usage:
    python3 assets/patrol_simulator.py --days 3 --limit 50
    python3 assets/patrol_simulator.py --days 7 --limit 100 --no-quality
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import requests

from pagetriage_client import PageTriageClient


def main() -> None:
    args = _parse_args()
    client = PageTriageClient(args.wiki)

    # ---- Phase 1: Fetch new pages ----
    pages = client.fetch_new_pages(days=args.days, limit=args.limit)
    print(f"[1] {len(pages)} new pages fetched", file=sys.stderr)

    # ---- Phase 1b: Get wikitext for ref analysis ----
    wikitexts = _fetch_wikitexts(client, [p["pageid"] for p in pages])

    # ---- Phase 1c: Run reference analysis ----
    matches = []
    for p in pages:
        raw = wikitexts.get(p["pageid"], "")
        if not raw:
            continue
        has_url, total_refs, url_refs, _ = has_any_url_refs(raw)
        is_match = total_refs > 0 and not has_url
        if is_match:
            matches.append(
                {
                    "pageid": p["pageid"],
                    "title": p["title"],
                    "user": p["user"],
                    "revid": p.get("revid"),
                }
            )

    print(f"[2] {len(matches)} no-URL-ref pages found", file=sys.stderr)

    if not matches:
        print("No matches — skipping enrichment phase.", file=sys.stderr)
        return

    # ---- Phase 2: Enrich matches only ----
    print(f"[3] Enriching {len(matches)} matches...", file=sys.stderr)

    # Page metadata (size, categories)
    meta = _fetch_page_meta(client, [m["pageid"] for m in matches])
    for m in matches:
        m["size"] = meta.get(m["pageid"], {}).get("size")
        m["categories"] = meta.get(m["pageid"], {}).get("categories", [])

    # Edit counts
    users = sorted({m["user"] for m in matches})
    edit_counts = _fetch_edit_counts(client, users)
    for m in matches:
        m["editcount"] = edit_counts.get(m["user"])

    # Quality scores
    if not args.no_quality:
        rev_ids = [m["revid"] for m in matches if m.get("revid")]
        quality = _fetch_quality_scores(rev_ids)
        for m in matches:
            m["quality"] = quality.get(m["revid"])
    else:
        for m in matches:
            m["quality"] = None

    # ---- Output ----
    print()
    for m in matches:
        ec = f"{m.get('editcount'):,d}" if m.get("editcount") else "—"
        sz = f"{m.get('size'):,d}" if m.get("size") else "—"
        ql = m.get("quality") or "—"
        nc = len(m.get("categories", []))
        print(f"  {m['title']:<45} edits={ec:<8} size={sz:<8} cats={nc:<3} quality={ql}")


# ---------------------------------------------------------------------------
# Helper functions (standalone to avoid external dependencies beyond requests)
# ---------------------------------------------------------------------------


def _fetch_wikitexts(
    client: PageTriageClient, page_ids: list[int]
) -> dict[int, str]:
    """Batch fetch wikitext for a list of page IDs."""
    result: dict[int, str] = {}
    for i in range(0, len(page_ids), 50):
        chunk = page_ids[i : i + 50]
        data = client._get(
            {
                "action": "query",
                "prop": "revisions",
                "rvprop": "content",
                "rvslots": "main",
                "pageids": "|".join(str(pid) for pid in chunk),
                "format": "json",
            }
        )
        for info in data.get("query", {}).get("pages", {}).values():
            pid = info.get("pageid")
            revs = info.get("revisions", [])
            if pid is not None and revs:
                result[int(pid)] = (
                    revs[0].get("slots", {}).get("main", {}).get("*", "")
                )
        time.sleep(0.3)
    return result


def _fetch_page_meta(
    client: PageTriageClient, page_ids: list[int]
) -> dict[int, dict[str, Any]]:
    """Batch fetch page size and categories."""
    result: dict[int, dict[str, Any]] = {}
    for i in range(0, len(page_ids), 50):
        chunk = page_ids[i : i + 50]
        data = client._get(
            {
                "action": "query",
                "prop": "info|categories",
                "cllimit": "max",
                "pageids": "|".join(str(pid) for pid in chunk),
                "format": "json",
            }
        )
        for info in data.get("query", {}).get("pages", {}).values():
            pid = info.get("pageid")
            if pid is not None:
                cats = info.get("categories", [])
                result[int(pid)] = {
                    "size": info.get("length"),
                    "categories": sorted(
                        c["title"] for c in cats if "title" in c
                    ),
                }
        time.sleep(0.3)
    return result


def _fetch_edit_counts(
    client: PageTriageClient, usernames: list[str]
) -> dict[str, int | None]:
    """Batch fetch edit counts for a list of usernames."""
    result: dict[str, int | None] = {}
    for i in range(0, len(usernames), 50):
        chunk = usernames[i : i + 50]
        data = client._get(
            {
                "action": "query",
                "list": "users",
                "ususers": "|".join(chunk),
                "usprop": "editcount",
                "format": "json",
            }
        )
        for u in data.get("query", {}).get("users", []):
            name = u.get("name", "")
            if "missing" in u or "invalid" in u:
                result[name] = None
            else:
                ec = u.get("editcount")
                result[name] = int(ec) if ec is not None else None
        time.sleep(0.1)
    return result


def _fetch_quality_scores(rev_ids: list[int]) -> dict[int, str]:
    """Fetch Lift Wing article quality predictions."""
    result: dict[int, str] = {}
    for rid in rev_ids:
        try:
            resp = requests.post(
                "https://api.wikimedia.org/service/lw/inference/v1/models"
                "/enwiki-articlequality:predict",
                json={"rev_id": rid},
                timeout=30,
            )
            if resp.status_code == 200:
                payload = resp.json()
                prediction = (
                    payload.get("enwiki", {})
                    .get("scores", {})
                    .get(str(rid), {})
                    .get("articlequality", {})
                    .get("score", {})
                    .get("prediction")
                )
                if prediction:
                    result[rid] = prediction
        except (requests.RequestException, ValueError, TypeError):
            pass
        time.sleep(0.15)
    return result


def has_any_url_refs(
    wikitext: str,
) -> tuple[bool, int, int, list[str]]:
    """Minimal inline implementation of reference URL detection.

    Full version with named-ref resolution and all template variants
    is in the wikipedia-reference-verifiability skill.
    """
    import re

    total = 0
    url_count = 0
    bad_samples: list[str] = []

    # Find all <ref>...</ref> tags (simple regex version)
    refs = re.findall(r"<ref[^>]*>(.*?)</ref>", wikitext, re.DOTALL)
    for ref_text in refs:
        total += 1
        if re.search(r"https?://", ref_text, re.IGNORECASE):
            url_count += 1
        elif "{{" in ref_text and "}}" in ref_text:
            # Check for url= in templates
            if re.search(r"\|?\s*url\s*=", ref_text, re.IGNORECASE):
                url_count += 1
            elif len(bad_samples) < 3:
                m = re.search(r"\{\{([^|}]+)", ref_text)
                bad_samples.append(
                    f"[{m.group(1).strip()}]" if m else "(template)"
                )
        else:
            if len(bad_samples) < 3:
                cleaned = ref_text.strip()[:50]
                bad_samples.append(cleaned or "(empty)")

    return (url_count > 0, total, url_count, bad_samples)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Patrol Simulator — two-pass NPP pipeline demo"
    )
    p.add_argument("--wiki", default="enwiki", help="Wiki to scan")
    p.add_argument("--days", type=int, default=3, help="Days back")
    p.add_argument("--limit", type=int, default=50, help="Max pages")
    p.add_argument("--no-quality", action="store_true", help="Skip ML predictions")

    # Show help when invoked with no arguments (all have defaults, so
    # argparse won't do this automatically)
    if len(sys.argv) == 1:
        p.print_help()
        sys.exit(1)

    return p.parse_args()


if __name__ == "__main__":
    main()
