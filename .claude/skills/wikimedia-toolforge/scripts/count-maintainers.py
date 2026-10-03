#!/usr/bin/env python3
"""Audit Toolforge tool maintainers by crawling the Striker (toolsadmin) web UI.

Striker is the authoritative source: its per-tool "Maintainers" list is read from
the LDAP membership that gates `become` access. There is no public API for this
data (LDAP is internal-only; Toolhub's `author` is self-reported toolinfo.json).

Usage:
    python3 count-maintainers.py                 # crawl everything, print stats
    python3 count-maintainers.py --json out.json # also write tool -> [maintainers]
    python3 count-maintainers.py --max-page 3    # debug: stop after page 3

See references/maintainer-audit.md for method notes and pitfalls.
"""
import argparse
import json
import re
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape

UA = "HermesAgent/1.0 (research; https://en.wikipedia.org/wiki/User:Fuzheado) ToolforgeMaintainerAudit/1.0"
BASE = "https://toolsadmin.wikimedia.org"
TOOL_RE = re.compile(r'href="/tools/id/([a-z0-9-]+)"')


def get(url, retries=4, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return e.code, ""
            if attempt == retries - 1:
                return e.code, ""
            time.sleep(1.5 * (attempt + 1))
        except Exception:
            if attempt == retries - 1:
                return -1, ""
            time.sleep(1.5 * (attempt + 1))
    return -1, ""


def extract_maintainers(html):
    i = html.find("<caption>Maintainers</caption>")
    if i < 0:
        return []
    seg = html[i:html.find("</tbody>", i)]
    return [
        unescape(re.sub(r"<[^>]+>", "", td)).strip()
        for td in re.findall(r"<td>(.*?)</td>", seg, re.S)
        if td.strip()
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--json", metavar="FILE", help="write tool -> maintainers JSON")
    ap.add_argument("--max-page", type=int, default=None, help="debug: stop index at page N")
    args = ap.parse_args()

    # Phase 1: collect tool names from paginated index.
    _, html = get(f"{BASE}/tools/?p=1")
    pages = sorted({int(x) for x in re.findall(r'href="\?p=([0-9]+)"', html)})
    total_pages = pages[-1] if pages else 1
    if args.max_page:
        total_pages = min(total_pages, args.max_page)
    print(f"total index pages: {total_pages}", flush=True)

    tools = set()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(get, f"{BASE}/tools/?p={n}"): n for n in range(1, total_pages + 1)}
        for f in as_completed(futs):
            _, h = f.result()
            tools.update(TOOL_RE.findall(h))
    tools = sorted(tools)
    print(f"tools found: {len(tools)}", flush=True)

    # Phase 2: fetch each tool's maintainers.
    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(get, f"{BASE}/tools/id/{t}"): t for t in tools}
        for n, f in enumerate(as_completed(futs), 1):
            t = futs[f]
            st, h = f.result()
            if st not in (404, 410) and h:
                results[t] = extract_maintainers(h)
            if n % 500 == 0:
                print(f"  {n}/{len(tools)}", flush=True)

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False)
        print(f"wrote {args.json}", flush=True)

    total = len(results)
    dist = Counter(len(m) for m in results.values())
    print("\nmaintainer-count distribution (count -> #tools):")
    for k in sorted(dist):
        print(f"  {k}: {dist[k]} ({100 * dist[k] / total:.2f}%)")
    solo = dist[1]
    multi = total - solo - dist[0]
    people = {p for m in results.values() for p in m}
    print(f"\ntotal tools with data:  {total}")
    print(f"solo (1 maintainer):    {solo} ({100 * solo / total:.2f}%)")
    print(f"multi (2+ maintainers): {multi} ({100 * multi / total:.2f}%)")
    print(f"zero maintainers:       {dist[0]}")
    print(f"unique maintainer accounts: {len(people)}")


if __name__ == "__main__":
    main()
