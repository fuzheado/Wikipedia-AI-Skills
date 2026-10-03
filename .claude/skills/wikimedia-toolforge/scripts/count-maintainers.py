#!/usr/bin/env python3
"""Audit Toolforge tool maintainers by crawling the Striker (toolsadmin) web UI.

Striker is the authoritative source: its per-tool "Maintainers" list is read from
the LDAP membership that gates `become` access. There is no public API for this
data (LDAP is internal-only; Toolhub's `author` is self-reported toolinfo.json).

The crawl is ~4,600 requests (≈420 index pages at 10 tools/page + ~4,200 tool
pages), so it is deliberate, not a default: you must pass --all. Pacing follows
the Wikimedia Robot policy for non-wiki resources — at most 1 concurrent request
and at least 1 second between requests by default. At --delay 1.0, --workers 1
expect roughly 80 minutes.

Usage:
    python3 count-maintainers.py --all                    # full crawl, print stats
    python3 count-maintainers.py --all --json out.json    # also write tool -> [maintainers]
    python3 count-maintainers.py --max-page 3             # debug: stop after page 3
    python3 count-maintainers.py --all --delay 0.5        # faster: know why first

User-Agent: taken from $WIKIMEDIA_USER_AGENT when set (recommended); see the
repo README for the extension-provided default.

See references/maintainer-audit.md for method notes and pitfalls.
"""
import argparse
import email.utils
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape

UA = os.environ.get(
    "WIKIMEDIA_USER_AGENT",
    "wikipedia-ai-skills-toolforge-maintainer-audit/1.0 "
    "(https://github.com/fuzheado/Wikipedia-AI-Skills)",
)
BASE = "https://toolsadmin.wikimedia.org"
TOOL_RE = re.compile(r'href="/tools/id/([a-z0-9-]+)"')

# Robot policy (non-wiki Wikimedia resources): >= 1s between requests, and give up
# rather than keep hammering after repeated rate limiting.
DEFAULT_DELAY = 1.0
MAX_CONSECUTIVE_429 = 2
BACKOFF_START = 10.0


class RateLimited(RuntimeError):
    """Raised when the server throttles us hard enough that the run must stop."""


class ServiceUnavailable(RuntimeError):
    """Raised when the server keeps returning 5xx; the policy asks us to pause."""


class Pacer:
    """Enforce a global minimum interval between request starts.

    The interval is enforced across threads, so raising --workers cannot raise
    the average request rate — it only removes idle time between paced requests.
    """

    def __init__(self, delay: float):
        self.delay = delay
        self._lock = threading.Lock()
        self._next_at = 0.0

    def wait(self) -> None:
        if self.delay <= 0:
            return
        with self._lock:
            now = time.monotonic()
            sleep_for = self._next_at - now
            self._next_at = max(now, self._next_at) + self.delay
        if sleep_for > 0:
            time.sleep(sleep_for)


def parse_retry_after(value: str | None) -> float | None:
    """Retry-After is either delta-seconds or an HTTP-date; return seconds."""
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


def get(url, pacer, retries=4, timeout=30):
    """Fetch url politely. Returns (status, text); status -1 on unrecoverable error."""
    throttled = 0
    wait = BACKOFF_START
    for attempt in range(retries):
        pacer.wait()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code in (404, 410):
                return e.code, ""
            if e.code == 429:
                throttled += 1
                if throttled >= MAX_CONSECUTIVE_429:
                    raise RateLimited(
                        f"throttled {throttled}x in a row on {url} — stopping the run. "
                        f"Honour Retry-After, wait a while, and re-run (see the Robot "
                        f"policy in the wikimedia-api-access skill)."
                    ) from e
                pause = parse_retry_after(e.headers.get("Retry-After") if e.headers else None)
                if pause is None:
                    pause = wait
                print(f"  429 on {url} — pausing {pause:.0f}s", file=sys.stderr)
                time.sleep(pause)
                wait *= 2
                continue
            if 500 <= e.code < 600:
                if attempt == retries - 1:
                    raise ServiceUnavailable(
                        f"{e.code} from {url} after {retries} attempts — stopping the "
                        f"run; the policy asks for a 15-minute pause after a 5xx "
                        f"before trying again."
                    ) from e
                print(f"  {e.code} on {url} — pausing {wait:.0f}s", file=sys.stderr)
                time.sleep(wait)
                wait *= 2
                continue
            if attempt == retries - 1:
                return e.code, ""
            time.sleep(1.5 * (attempt + 1))
        except RateLimited:
            raise
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


def usage_note() -> str:
    return (
        "A full crawl is ~4,600 requests (~420 index pages + ~4,200 tool pages).\n"
        "At the default --delay 1.0 with --workers 1 that takes roughly 80 minutes.\n"
        "Pacing follows the Wikimedia Robot policy for non-wiki resources\n"
        "(<= 1 concurrent request, >= 1s between requests).\n"
        "\n"
        "Examples:\n"
        "  count-maintainers.py --all                     # full crawl, print stats\n"
        "  count-maintainers.py --all --json out.json     # also write tool -> maintainers\n"
        "  count-maintainers.py --max-page 3              # debug: stop after index page 3\n"
    )


def main():
    ap = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Audit Toolforge tool maintainers via the Striker web UI.",
        epilog=usage_note(),
    )
    ap.add_argument("--all", action="store_true",
                    help="run the full crawl (required; the crawl is ~4,600 requests)")
    ap.add_argument("--workers", type=int, default=1,
                    help="concurrent requests (default 1: the policy expects <= 1 for "
                         "non-wiki Wikimedia resources; --delay is enforced globally "
                         "either way)")
    ap.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                    help=f"minimum seconds between request starts (default {DEFAULT_DELAY})")
    ap.add_argument("--json", metavar="FILE", help="write tool -> maintainers JSON")
    ap.add_argument("--max-page", type=int, default=None, help="debug: stop index at page N")
    args = ap.parse_args()

    # Zero-argument guard: bare invocation explains itself and stops.
    if len(sys.argv) == 1:
        print(usage_note(), file=sys.stderr)
        print("error: refusing to start a full crawl without --all", file=sys.stderr)
        return 2
    if not args.all and not args.max_page:
        ap.error("pass --all to run the full crawl, or --max-page N to bound it")

    workers = max(1, args.workers)
    if workers > 1:
        print(f"note: --workers {workers} exceeds the Robot policy's concurrency limit "
              f"for non-wiki Wikimedia resources; requests are still paced to one every "
              f"{args.delay:g}s on average.", file=sys.stderr)
    pacer = Pacer(args.delay)

    try:
        # Phase 1: collect tool names from paginated index.
        _, html = get(f"{BASE}/tools/?p=1", pacer)
        pages = sorted({int(x) for x in re.findall(r'href="\?p=([0-9]+)"', html)})
        total_pages = pages[-1] if pages else 1
        if args.max_page:
            total_pages = min(total_pages, args.max_page)
        print(f"total index pages: {total_pages}", flush=True)

        tools = set()
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(get, f"{BASE}/tools/?p={n}", pacer): n
                    for n in range(1, total_pages + 1)}
            for f in as_completed(futs):
                _, h = f.result()
                tools.update(TOOL_RE.findall(h))
        tools = sorted(tools)
        print(f"tools found: {len(tools)}", flush=True)

        # Phase 2: fetch each tool's maintainers.
        results = {}
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(get, f"{BASE}/tools/id/{t}", pacer): t for t in tools}
            for n, f in enumerate(as_completed(futs), 1):
                t = futs[f]
                st, h = f.result()
                if st not in (404, 410) and h:
                    results[t] = extract_maintainers(h)
                if n % 500 == 0:
                    print(f"  {n}/{len(tools)}", flush=True)
    except (RateLimited, ServiceUnavailable) as exc:
        print(f"aborted: {exc}", file=sys.stderr)
        return 1

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False)
        print(f"wrote {args.json}", flush=True)

    total = len(results)
    if not total:
        print("no tool data collected", file=sys.stderr)
        return 1
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
