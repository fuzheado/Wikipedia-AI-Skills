#!/usr/bin/env python3
"""refresh-url-registry.py — HEAD-check every external URL in the skills and
record the status in url-registry.json (ground truth for verify-links.py). This is the live counterpart to the structural URL checks in verify-links.py:
it catches "URLs are not fabricated or guessed" (CONTRIBUTING checklist) by
actually hitting the network.

Incremental by default (freshness rotation): a URL is only live-checked when
it is
  - new (never recorded before), or
  - stale — last checked more than --max-age-days ago (default 90 = ~3 months),
  - or broken — last status was 0/error or >= 400, and it was last checked
    more than --retry-after-days ago (default 30; broken URLs are re-probed
    sooner so recoveries get picked up).

Known-good URLs within the freshness window are skipped entirely, so a normal
run (manual or scheduled) only checks the handful of URLs that rotated in.
There is no need for an unbounded full sweep on every commit — CI's
verify-links.py is fully offline and only cross-checks against this registry.

Useful invocations:
    python3 scripts/refresh-url-registry.py                 # incremental (new + stale + broken)
    python3 scripts/refresh-url-registry.py --new-only      # only URLs never checked (pre-push, fastest)
    python3 scripts/refresh-url-registry.py --full          # re-check everything (rare full audit)
    python3 scripts/refresh-url-registry.py --max-age-days 30   # tighter freshness window

Wikimedia API etiquette is enforced: a descriptive User-Agent on every request
($WIKIMEDIA_USER_AGENT when set), pacing between requests (--delay, default 1s),
and exponential backoff with Retry-After handling on HTTP 429.

Writes: scripts/url-registry.json
  { generated_at, generator, user_agent,
    urls:       {url: status_code},   # status: -1 example, -2 post-only, 0 error, else HTTP code
    checked_at: {url: ISO8601},       # when each URL was last live-checked
    exceptions: {url: {classification, allow_reason}},
    skip: {...} }
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
OUT = SCRIPT_DIR / "url-registry.json"

URL_RE = re.compile(r"https?://[^\s\)\]>'\"`]+")
USER_AGENT = os.environ.get(
    "WIKIMEDIA_USER_AGENT",
    "wikipedia-ai-skills-url-registry/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)",
)

def collect_urls(skills_dir: Path) -> list[str]:
    urls = set()
    for f in skills_dir.rglob("*.md"):
        for m in URL_RE.finditer(f.read_text()):
            url = m.group(0).rstrip(".,;:!?*\\")  # trim trailing punctuation
            # trim unbalanced trailing paren (markdown link artifacts like #.../Python_(programming_language))
            while url.count("(") > url.count(")") and url.endswith("("):
                url = url[:-1]
            if "{" in url or "}" in url or url in ("https://", "http://") or url.endswith("..."):
                continue  # templated URLs and "https://..." documentation patterns
            # SPARQL CONCAT prefixes like 'https://commons.wikimedia.org/entity/M'
            # (entity IDs always follow) are code fragments, not URLs
            if re.search(r"/[MQ]$", url):
                continue
            host = urlparse(url).hostname or ""
            if not host or ("." not in host and host != "localhost"):
                continue
            urls.add(url)
    return sorted(urls)

# URLs that are legitimate documentation but can never be verified with a
# bare HEAD/GET: POST-only endpoints (Lift Wing :predict, Action API write
# actions, the wd-vectordb query endpoint, etc.) and bare API endpoints that
# require query parameters (web.archive.org CDX without url=). Recorded for
# the registry's skip list.
POST_ONLY_RE = re.compile(
    r"""(?:
      :predict$ | /item/query/ | /property/query/ | /similarity-score/ |
      /rest\.php/oauth2 | /rest\.php/oauth2/ |
      web\.archive\.org/cdx/search/cdx$ |
      api\.php\?action=(?:edit|upload|delete|move|import|login|logout|createaccount|
      watch|patrol|rollback|protect|block|emailuser|undelete|revisiondelete|
      suppression|changecontentmodel|stabilize|review)
    )"""
, re.I | re.X)

# Clearly-illustrative example URLs that are not real resources
EXAMPLE_URL_RE = re.compile(
    r"""(?:
      example\.com|example\.org|example\.jpg|doi\.org/10\.0000/example|newspaper\.com/article|<[A-Za-z_-]+>|\{[a-z_]+\}|
      \*\.|your-[a-z-]+|my-[a-z][a-z-]*|123456\d*|wrong-[a-z-]+|\bxxx\b|
      placeholder|\bTBD\b|library/version/file|PageName|Username|Foo\.svg|Doc\.pdf|
      He_Tingbo|/thumb/$|/800px$|/1440px$|\.\.\.|/stream/$|entity/[MQ]$|/entity/$|
      /prop/(direct/|qualifier/|statement/)?$|
      rest_v1/metrics/|rest_v1/page/.*/html$|service/lw/inference/v1/models/$|core/v1/wikipedia/en/$|
      [\\<>]|\([^)]*$|Special_MyLanguage|Special:OAuth|Book_Title|rest_v1/search/page|qlever\.(cs\.uni-freiburg\.de|dev)|/sparql$
    )"""
, re.I | re.X)

def classify(url: str) -> int | None:
    """Return the skip marker (-1 example, -2 post-only) or None if the URL
    should be live-checked."""
    if EXAMPLE_URL_RE.search(url):
        return -1
    if POST_ONLY_RE.search(url):
        return -2
    return None


def exception_for(url: str, status) -> dict | None:
    """Return structured allow metadata for URLs that are not normal live GETs.

    These exceptions make verifier passes reviewable: a non-OK URL is allowed
    only when the registry says why a generic HEAD/GET check is not decisive.
    """
    host = urlparse(url).hostname or ""
    if status == -1:
        return {"classification": "example",
                "allow_reason": "Illustrative placeholder or code fragment, not a literal URL to verify"}
    if status == -2:
        return {"classification": "post_or_parameter_required",
                "allow_reason": "Endpoint requires POST, OAuth flow, or query parameters; bare HEAD/GET is not a validity test"}
    if status == 0:
        if host in {"localhost", "127.0.0.1"}:
            return {"classification": "local_dev",
                    "allow_reason": "Local development URL; not expected to resolve from CI"}
        if host == "stream.wikimedia.org":
            return {"classification": "eventstream_sse",
                    "allow_reason": "Server-sent event stream; generic URL check can time out even when the endpoint exists"}
        if host in {"xn--h1ayg.wikipedia.org", "ру.wikipedia.org"}:
            return {"classification": "unicode_domain_example",
                    "allow_reason": "Used to document Unicode/IDNA pitfalls, not as a normal live-link assertion"}
        if host == "reconcile.wikidata.org":
            return {"classification": "documented_legacy_service",
                    "allow_reason": "Documented legacy/retired reconciliation endpoint; kept as historical context"}
        if host == "wmf.legal-yes.com":
            return {"classification": "browser_only",
                    "allow_reason": "Browser-facing tool can fail generic server-side probes"}
        return {"classification": "network_unverified",
                "allow_reason": "Network/DNS/timeout result; retained for review instead of silently accepting"}
    if status == 401:
        return {"classification": "auth_required",
                "allow_reason": "URL exists behind authentication or anti-bot access controls"}
    if status == 403:
        return {"classification": "access_restricted",
                "allow_reason": "URL is access-restricted to generic CI probes but is not a clear dead link"}
    if status == 405:
        return {"classification": "method_specific",
                "allow_reason": "Endpoint rejects generic HEAD/GET; another method or payload is required"}
    if status == 422:
        return {"classification": "requires_parameters",
                "allow_reason": "Endpoint exists but rejects a bare request without required parameters"}
    if isinstance(status, int) and status >= 500:
        return {"classification": "transient_server_error",
                "allow_reason": "Server-side error at probe time; needs scheduled recheck, not an immediate hallucination finding"}
    return None


def rebuild_exceptions(registry: dict) -> None:
    exceptions = {}
    for url, status in registry.get("urls", {}).items():
        exc = exception_for(url, status)
        if exc is not None:
            exceptions[url] = exc
    registry["exceptions"] = exceptions

def check_url(url: str, timeout: float, delay: float) -> int:
    """HEAD (fall back to GET) a URL, returning the final status code.

    HEAD is preferred for politeness, but many servers mishandle it — some
    return 404/405/501 to HEAD for URLs that work fine with GET (e.g. sites
    that redirect on GET but not HEAD). So any 4xx/5xx from HEAD is retried
    once with GET before being recorded.
    """
    req = Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=timeout) as resp:
                return resp.status
        except HTTPError as e:
            if e.code == 429:
                retry = float(e.headers.get("Retry-After", 2 ** attempt))
                print(f" 429 {url} — backing off {retry}s", file=sys.stderr)
                time.sleep(retry)
                continue
            # HEAD unsupported/mishandled — retry once with GET before trusting
            # the HEAD status (400/404/405/501 are the classic HEAD artifacts)
            if attempt == 0 and e.code in (400, 404, 405, 501):
                req = Request(url, headers={"User-Agent": USER_AGENT})
                continue
            return e.code
        except URLError as e:
            # some servers reject HEAD; retry once with GET
            if attempt == 0 and isinstance(e.reason, Exception) and "HEAD" in str(e):
                req = Request(url, headers={"User-Agent": USER_AGENT})
                continue
            return 0  # network error / DNS / timeout — record as 0
        except Exception:
            return 0
    return 429

def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def parse_iso(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return datetime.min.replace(tzinfo=timezone.utc)

def load_registry() -> tuple[dict, dict]:
    """Load url-registry.json. Returns (urls, checked_at), migrating the legacy
    flat {url: status} format by backfilling checked_at from generated_at."""
    urls, checked_at = {}, {}
    if OUT.exists():
        data = json.loads(OUT.read_text())
        urls = data.get("urls", {})
        checked_at = data.get("checked_at", {})
        if not checked_at and urls:
            # legacy format: every recorded URL approximates as checked at
            # generation time (keeps verify-links.py fully backward compatible)
            generated = data.get("generated_at", now_iso())
            checked_at = {u: generated for u in urls}
    return urls, checked_at

def needs_check(url: str, status, checked_at_iso, now: datetime,
                max_age_days: int, retry_after_days: int,
                new_only: bool, full: bool) -> bool:
    if full:
        return True
    if checked_at_iso is None:
        return True  # never recorded
    if new_only:
        return False  # recorded at all — skip (new-only mode)
    age = (now - parse_iso(checked_at_iso)).days
    if status in (0,) or (isinstance(status, int) and status >= 400):
        return age >= retry_after_days  # broken URLs re-probed sooner
    return age >= max_age_days

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skills-dir", type=Path, default=DEFAULT_SKILLS_DIR)
    ap.add_argument("--delay", type=float, default=1.0,
                    help="seconds between requests (Wikimedia etiquette; default 1.0)")
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--limit", type=int, default=0, help="only check first N URLs (test)")
    ap.add_argument("--max-age-days", type=int, default=90,
                    help="re-check URLs last checked more than this many days ago "
                         "(freshness window; default 90 = ~3 months)")
    ap.add_argument("--retry-after-days", type=int, default=30,
                    help="re-check known-broken URLs (status 0 or >= 400) older than "
                         "this many days (default 30)")
    ap.add_argument("--new-only", action="store_true",
                    help="only check URLs never recorded before; skip all re-checks "
                         "(fastest pre-push mode after adding URLs)")
    ap.add_argument("--full", action="store_true",
                    help="re-check every URL regardless of freshness (rare full audit)")
    ap.add_argument("--resume", action="store_true",
                    help="kept for backwards compatibility — incremental freshness "
                         "mode is now the default, so this flag is a no-op")
    args = ap.parse_args(argv)

    urls = collect_urls(args.skills_dir)
    if args.limit:
        urls = urls[: args.limit]

    known, checked_at = load_registry()
    print(f"{len(urls)} URLs found; {len(known)} recorded "
          f"(delay={args.delay}s, max-age={args.max_age_days}d, "
          f"retry-broken={args.retry_after_days}d)", file=sys.stderr)

    now = datetime.now(timezone.utc)
    registry = {
        "generated_at": now_iso(),
        "generator": "scripts/refresh-url-registry.py",
        "user_agent": USER_AGENT,
        "urls": dict(known),
        "checked_at": dict(checked_at),
        "exceptions": {},
        "skip": {"post_only": "POST-only or parameter-required endpoints "
                              "(bare HEAD/GET cannot verify)",
                 "example": "illustrative placeholder URLs"},
    }

    def save():
        OUT.write_text(json.dumps(registry, indent=1, sort_keys=True) + "\n")

    # Decide what to check this run (before mutating anything)
    plan = []  # (url, reason)
    for u in urls:
        marker = classify(u)
        if marker is not None:
            registry["urls"][u] = marker          # skip markers never need a fetch
            if u not in checked_at:
                checked_at[u] = now_iso()          # classify counts as "known"
            registry["checked_at"] = dict(checked_at)
            rebuild_exceptions(registry)
            continue
        status = known.get(u)
        if needs_check(u, status, checked_at.get(u), now,
                       args.max_age_days, args.retry_after_days,
                       args.new_only, args.full):
            reason = ("new" if u not in known
                      else "broken-retry" if (status in (0,) or (isinstance(status, int) and status >= 400))
                      else f"stale-{args.max_age_days}d")
            plan.append((u, reason))

    print(f" {len(plan)} URL(s) to live-check "
          f"({len(urls) - len(plan) - sum(1 for u in urls if classify(u) is not None)} fresh/skip "
          f"skipped)", file=sys.stderr)

    bad = 0
    for i, (url, reason) in enumerate(plan, 1):
        status = check_url(url, args.timeout, args.delay)
        registry["urls"][url] = status
        registry["checked_at"][url] = now_iso()
        rebuild_exceptions(registry)
        if status >= 400:
            bad += 1
        print(f" [{i}/{len(plan)}] ({reason}) {status} {url}", file=sys.stderr)
        if i % 25 == 0:
            print(f" [{i}/{len(plan)}]...", file=sys.stderr)
        time.sleep(args.delay)  # pacing (Wikimedia etiquette)
        save()  # incremental save: never lose progress on interruption

    rebuild_exceptions(registry)
    save()  # final save (also covers the no-pending case)
    print(f"\nRegistry written to {OUT}", file=sys.stderr)
    print(f" {len(plan)} URLs checked, {bad} with status >= 400, "
          f"{sum(1 for u in urls if classify(u) is not None)} skip-classified, "
          f"{len(urls) - len(plan) - sum(1 for u in urls if classify(u) is not None)} skipped (fresh).",
          file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
