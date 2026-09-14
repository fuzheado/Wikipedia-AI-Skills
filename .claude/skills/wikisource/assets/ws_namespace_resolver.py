#!/usr/bin/env python3
"""
ws_namespace_resolver.py — Resolve ProofreadPage namespace IDs across Wikisource wikis.

WHY THIS EXISTS
---------------
ProofreadPage needs a `Page:` namespace (scanned image + text layer) and an
`Index:` namespace (work metadata). Neither the numeric ID nor the localised
name is portable:

    en   Page = 104   Index = 106     "Page"    / "Index"
    de   Page = 102   Index = 104     "Seite"   / "Index"
    pl   Page = 100   Index = 102     "Strona"  / "Indeks"
    it   Page = 108   Index = 110     "Pagina"  / "Indice"
    pt   Page = 106   Index = ?       "Página"  / — (108 is "Em Tradução", NOT Index)
    ta   Page = 250   Index = 252     "பக்கம்"   / "அட்டவணை"
    sv   Page = 104   Index = 108     "Sida"    / "Index"   (NOT Page+2)
    fr   Page = 104   Index = ?       "Page"    / — (nr 106 is "Portail", NOT Index)

Hardcoding 104/106 silently returns zero pages on most wikis, and the tempting
"Index = Page + 2" offset rule produces **false positives** — it lands on Portal
namespaces on fr (Portail), bn (প্রবেশদ্বার), pt ("Em Tradução") and ml (കവാടം).

See T74525 — "harmonize Wikisource namespaces used by the ProofreadPage extension",
open since 2014: https://phabricator.wikimedia.org/T74525

STRATEGY (authoritative)
------------------------
ProofreadPage gives its two namespaces dedicated **content models**. Sample one
page from a candidate namespace and read `contentmodel` via `prop=info`:

    proofread-page   -> the Page namespace
    proofread-index  -> the Index namespace

That is the extension's own marker, so it cannot be fooled by a localised name
or a coincidental ID. Verified on en/de/ta/fr/bn/pt (2026-09-11): Portal-style
namespaces return `wikitext` and are correctly rejected.

Inexact modes are retained as fallbacks but always report lower confidence —
callers should treat anything below `contentmodel` as unverified.

Usage:
    from ws_namespace_resolver import resolve_namespaces, namespaces_for_many

    ns = resolve_namespaces("de")
    # {'lang': 'de', 'page': {'id': 102, 'name': 'Seite', 'contentmodel': 'proofread-page'},
    #  'index': {'id': 104, 'name': 'Index', 'contentmodel': 'proofread-index'},
    #  'confidence': 'contentmodel'}

CLI:
    python3 ws_namespace_resolver.py de pl it fr sv ta
    python3 ws_namespace_resolver.py --all-sampled
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
    "WikisourceNamespaceResolver/1.0 "
    "(https://en.wikipedia.org/wiki/User:Fuzheado; skill: wikisource) python-urllib"
)

# Fast-path hints only. These are NOT authoritative — contentmodel decides.
PAGE_ALIASES = {
    "page", "seite", "strona", "pagina", "página", "pàgina", "страница", "страна",
    "sida", "síða", "side", "oldal", "lehekülg", "puslapis", "lapa", "stran",
    "पृष्ठ", "পাতা", "பக்கம்", "పేజీ", "ಪುಟ", "പേജ്", "പേജ്", "صفحہ", "صفحة",
    "דף", "sayfa", "σελίδα", "stranica", "ページ", "페이지", "页面", "頁面", "頁",
}
INDEX_ALIASES = {
    "index", "indeks", "indice", "índice", "индекс", "rejstřík", "rejestr",
    "register", "dizin", "ευρετήριο", "kazalo", "sadržaj", "indeksas", "saraksts",
    "अनुक्रमणिका", "সূচী", "அட்டவணை", "సూచిక", "ಸೂಚಿ", "സൂചിക", "فہرست", "فهرس",
    "מפתח", "索引", "インデックス", "색인",
}

SAMPLED = ["en", "fr", "de", "pl", "it", "sv", "nl", "ru", "zh", "es", "pt", "ta", "bn", "ml"]

CONTENT_MODEL_PAGE = "proofread-page"
CONTENT_MODEL_INDEX = "proofread-index"


def _api(lang: str, params: dict, retries: int = 3, timeout: int = 30) -> dict:
    """One Action API call with backoff (Wikimedia etiquette: retry, don't hammer)."""
    params = dict(params, format="json")
    url = f"https://{lang}.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    last_err: Exception | None = None
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            last_err = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"API request failed for {lang}: {last_err}")


def _norm(name: str) -> str:
    return (name or "").strip().lower()


def _content_model_of_namespace(lang: str, ns_id: int) -> str | None:
    """Sample one page in the namespace and return its content model."""
    listing = _api(lang, {"action": "query", "list": "allpages",
                          "apnamespace": str(ns_id), "aplimit": "1"})
    pages = listing.get("query", {}).get("allpages", [])
    if not pages:
        return None
    title = pages[0]["title"]
    info = _api(lang, {"action": "query", "titles": title, "prop": "info"})
    for _pid, page in info.get("query", {}).get("pages", {}).items():
        return page.get("contentmodel")
    return None


def resolve_namespaces(lang: str, probe_limit: int = 12) -> dict:
    """Resolve a Wikisource edition's Page/Index namespaces.

    Returns:
        {"lang", "page": {"id","name","contentmodel"}|None,
         "index": {...}|None, "confidence": one of
         "contentmodel" | "alias" | "none" | "error", "notes": [...]}

    `confidence`:
      contentmodel — confirmed via ProofreadPage's own content model (authoritative)
      alias        — matched a localised name but NOT confirmed; verify before relying
      none         — no ProofreadPage namespaces found
      error        — API failure (e.g. wiki unreachable)
    """
    notes: list[str] = []
    try:
        data = _api(lang, {"action": "query", "meta": "siteinfo", "siprop": "namespaces"})
    except RuntimeError as exc:
        return {"lang": lang, "page": None, "index": None, "confidence": "error", "notes": [str(exc)]}

    raw = data.get("query", {}).get("namespaces", {})
    candidates: dict[int, str] = {}
    for _key, ns in raw.items():
        ns_id = int(ns.get("id", 0))
        if ns_id >= 100 and ns_id % 2 == 0:      # content namespaces only (odd = talk)
            candidates[ns_id] = ns.get("*", "")

    page = index = None

    # ── Authoritative pass: content model ────────────────────────────────────
    # Probe alias-matching namespaces first (cheap, usually right), then the rest.
    ordered = sorted(candidates, key=lambda i: (
        _norm(candidates[i]) not in PAGE_ALIASES | INDEX_ALIASES, i))
    for ns_id in ordered[:probe_limit]:
        try:
            model = _content_model_of_namespace(lang, ns_id)
        except RuntimeError as exc:
            notes.append(f"probe failed for ns{ns_id}: {exc}")
            continue
        if model == CONTENT_MODEL_PAGE and page is None:
            page = {"id": ns_id, "name": candidates[ns_id], "contentmodel": model}
        elif model == CONTENT_MODEL_INDEX and index is None:
            index = {"id": ns_id, "name": candidates[ns_id], "contentmodel": model}
        if page and index:
            break
        time.sleep(0.4)                          # etiquette pacing

    if page and index:
        return {"lang": lang, "page": page, "index": index,
                "confidence": "contentmodel", "notes": notes}

    # ── Fallback: localised-name match, explicitly unverified ────────────────
    for ns_id in sorted(candidates):
        if _norm(candidates[ns_id]) in PAGE_ALIASES and page is None:
            page = {"id": ns_id, "name": candidates[ns_id], "contentmodel": None}
        if _norm(candidates[ns_id]) in INDEX_ALIASES and index is None:
            index = {"id": ns_id, "name": candidates[ns_id], "contentmodel": None}
    if page or index:
        notes.append("name-only match — NOT confirmed via content model")
        return {"lang": lang, "page": page, "index": index,
                "confidence": "alias", "notes": notes}

    return {"lang": lang, "page": None, "index": None, "confidence": "none", "notes": notes}


def namespaces_for_many(langs: list[str], pause: float = 1.0) -> list[dict]:
    """Resolve several wikis sequentially with etiquette pacing."""
    out = []
    for i, lang in enumerate(langs):
        out.append(resolve_namespaces(lang))
        if i < len(langs) - 1:
            time.sleep(pause)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve ProofreadPage Page/Index namespaces across Wikisource editions "
                    "via content models (T74525)."
    )
    parser.add_argument("langs", nargs="*", help="Wikisource language codes, e.g. en de pl")
    parser.add_argument("--all-sampled", action="store_true",
                        help=f"Resolve the {len(SAMPLED)} sampled wikis: {' '.join(SAMPLED)}")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    args = parser.parse_args(argv)

    langs = SAMPLED if args.all_sampled else args.langs
    if not langs:
        parser.print_help()
        return 1

    results = namespaces_for_many(langs)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    print(f"{'wiki':6s} {'Page':>5s} {'name':<13s} {'Index':>6s} {'name':<15s} {'confidence'}")
    print("-" * 62)
    for r in results:
        page = r.get("page") or {}
        index = r.get("index") or {}
        print(
            f"{r['lang']:6s} {str(page.get('id', '-')):>5s} {str(page.get('name', '-')):<13s}"
            f" {str(index.get('id', '-')):>6s} {str(index.get('name', '-')):<15s} {r['confidence']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
