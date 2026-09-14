#!/usr/bin/env python3
"""
ws_catalog.py — Client for the Wikisource catalogue API (wsindex).

WHAT IT IS
----------
wsindex is the cross-Wikisource catalogue of **proofread and validated books**,
built from Wikidata (the Books data model) and hosted on Toolforge:

    https://wsindex.toolforge.org/books/

It is the data source behind the Wikisource Reader mobile app, which makes it a
production dependency rather than a demo.

WHAT QUALIFIES A BOOK (read from the tool's own source)
-------------------------------------------------------
A work appears in the catalogue only when its Wikisource sitelink carries a
**status badge** — `proofread` (Q20748092) or `validated` (Q20748093) — and the
item has exactly one `P1957` (Wikisource index page URL):

    ?sitelink schema:isPartOf <https://{lang}.wikisource.org/> ; schema:about ?item .
    { ?sitelink wikibase:badge wd:Q20748092. } UNION { ?sitelink wikibase:badge wd:Q20748093. }
    ?item wdt:P1957 ?indexPage .
    GROUP BY ?item HAVING (COUNT(DISTINCT ?indexPage) = 1)

⚠️ BADGE ADOPTION IS UNEVEN — measured 2026-09-11 (badge-qualified ÷ works with a
sitelink and a recorded P1957):

    ta 99.4%   bn 91.6%   en 80.8%   fr 75.4%   es 35.4%   sv 33.0%
    it 19.4%   ru  6.4%   zh  5.6%   de  1.6%   nl 0.0%

So the catalogue measures **Wikidata curation practice** as much as proofreading
status: de.wikisource (654k content pages) contributes 4 books; nl contributes 0.
Never present a catalogue total as "books finished on Wikisource" without this
caveat.

Usage:
    from ws_catalog import WsIndexClient

    client = WsIndexClient()
    page = client.books(languages="en", page_size=5)
    for book in page["results"]:
        print(book["title"], book["ws_url"], book["epub_url"])

CLI:
    python3 ws_catalog.py --languages en --limit 5
    python3 ws_catalog.py --total
    python3 ws_catalog.py --qid Q19026962
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = (
    "WikisourceCatalogClient/1.0 "
    "(https://en.wikipedia.org/wiki/User:Fuzheado; skill: wikisource) python-urllib"
)

BASE = "https://wsindex.toolforge.org/books/"

# Fields returned per book (documented for callers; the API also returns more).
BOOK_FIELDS = [
    "wikidata_qid", "title", "title_native_language", "languages",
    "date_of_publication", "authors", "editors", "translators", "genre",
    "literary_genres", "type_of_work", "form_of_work", "ws_url",
    "thumbnail_url", "epub_url", "wikisource_index_url", "view_count",
    "main_subjects", "subjects", "places_of_publication", "publishers",
]


class WsIndexClient:
    """Minimal, dependency-free client for the wsindex books API."""

    def __init__(self, base: str = BASE, timeout: int = 30, retries: int = 3):
        self.base = base
        self.timeout = timeout
        self.retries = retries

    # ── internals ────────────────────────────────────────────────────────────
    def _get(self, params: dict | None = None) -> dict:
        url = self.base
        if params:
            url += "?" + urllib.parse.urlencode(params)
        last_err: Exception | None = None
        for attempt in range(self.retries):
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8", "replace"))
            except (urllib.error.HTTPError, urllib.error.URLError, OSError,
                    json.JSONDecodeError) as exc:
                last_err = exc
                if attempt < self.retries - 1:
                    time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"wsindex request failed: {last_err}")

    @staticmethod
    def _clean(params: dict) -> dict:
        """Drop None values — wsindex treats empty params as filters."""
        return {k: v for k, v in params.items() if v not in (None, "")}

    # ── public API ───────────────────────────────────────────────────────────
    def books(self, *, languages: str | None = None, page: int | None = None,
              page_size: int | None = None, extra: dict | None = None) -> dict:
        """One page of the catalogue. Returns the raw envelope:
        {"count": N, "next": url|None, "previous": url|None, "results": [...]}.

        ⚠️ TRAP: only `languages` is a verified filter. Unrecognised parameters
        (e.g. `wikidata_qid`) are **silently ignored** — the API returns the
        unfiltered list with `count` = the global total (10,302 on 2026-09-11),
        not an empty result. A filter that "returns data" has not necessarily
        been applied: always sanity-check `count` against the unfiltered total.
        """
        params = {"languages": languages, "page": page, "page_size": page_size}
        if extra:
            params.update(extra)
        return self._get(self._clean(params))

    def total(self, languages: str | None = None) -> int:
        """Total book count (optionally filtered to one or more languages)."""
        return int(self.books(languages=languages, page_size=1).get("count", 0))

    def find_by_qid(self, qid: str, *, languages: str | None = None,
                    max_scan: int = 2000, pause: float = 1.0) -> dict | None:
        """Locate one book by Wikidata QID, scanning client-side.

        There is no working server-side QID filter (see `books()`), so this
        pages through the catalogue and matches locally. Bounded by `max_scan`
        to avoid unbounded crawling — returns None if not found within the cap.
        """
        target = qid.strip().upper()
        for i, book in enumerate(self.iterate(languages=languages, max_books=max_scan, pause=pause)):
            if str(book.get("wikidata_qid", "")).upper() == target:
                return book
            if i + 1 >= max_scan:
                break
        return None

    def iterate(self, *, languages: str | None = None, max_books: int | None = None,
                pause: float = 1.0):
        """Yield books across pages with etiquette pacing between requests."""
        params = self._clean({"languages": languages, "page_size": 50})
        url_params: dict | None = params
        seen = 0
        while True:
            envelope = self._get(url_params)
            for book in envelope.get("results", []):
                yield book
                seen += 1
                if max_books and seen >= max_books:
                    return
            nxt = envelope.get("next")
            if not nxt:
                return
            # `next` is an absolute URL; re-parse its query for the next call
            query = urllib.parse.urlparse(nxt).query
            url_params = dict(urllib.parse.parse_qsl(query))
            time.sleep(pause)

    def sparql_counts_url(self) -> str:
        """The SPARQL endpoint used to compute per-wiki badge adoption."""
        return "https://query.wikidata.org/sparql"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Query the Wikisource catalogue API (wsindex) for proofread/validated books."
    )
    parser.add_argument("--languages", help="Language code filter, e.g. en (or 'en,fr')")
    parser.add_argument("--qid", help="Find one book by Wikidata QID (client-side scan), e.g. Q19026962")
    parser.add_argument("--scan", type=int, default=300,
                        help="Max catalogue entries to scan for --qid (default 300)")
    parser.add_argument("--limit", type=int, help="Max books to print")
    parser.add_argument("--total", action="store_true", help="Print only the total count")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON")
    args = parser.parse_args(argv)

    client = WsIndexClient()

    if args.total:
        print(client.total(args.languages))
        return 0

    if args.qid:
        book = client.find_by_qid(args.qid, languages=args.languages, max_scan=args.scan)
        if not book:
            print(f"Not found in the first {args.scan} catalogue entries: {args.qid}", file=sys.stderr)
            print("(there is no server-side QID filter — raise --scan to search further)", file=sys.stderr)
            return 1
        books = [book]
    else:
        books = list(client.iterate(languages=args.languages, max_books=args.limit))

    if args.json:
        print(json.dumps(books, indent=2, ensure_ascii=False))
        return 0

    print(f"{len(books)} book(s)")
    for book in books:
        authors = ", ".join(a.get("name", "?") for a in book.get("authors", [])) or "—"
        print(f"\n  {book.get('title')}  [{book.get('wikidata_qid')}]")
        print(f"    lang={','.join(book.get('languages', [])) or '—'}  published={book.get('date_of_publication') or '—'}")
        print(f"    authors: {authors}")
        print(f"    views={book.get('view_count')}")
        print(f"    text:  {book.get('ws_url')}")
        print(f"    epub:  {book.get('epub_url')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
