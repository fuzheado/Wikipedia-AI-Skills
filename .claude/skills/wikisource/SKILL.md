---
name: wikisource
description: "Work with Wikisource - ProofreadPage workflow, page quality levels, cross-wiki namespace resolution, completed-book catalogues, EPUB export, and the OCR/AI layer."
license: MIT
compatibility: opencode
last_verified: 2026-09-11
depends_on: [wikimedia-api-access, wikimedia-commons, wikimedia-wikitext]
skill_discovery_hints:
  - keywords: ["Wikisource", "ProofreadPage", "proofread", "Index namespace", "validated text"]
  - keywords: ["wsindex", "completed books", "WSExport", "EPUB", "Wikisource Reader app"]
  - keywords: ["page quality", "OCR", "bulk OCR", "Tesseract", "Google OCR", "transcription"]
---

> ⚠️ **Prerequisites:** This skill assumes the MediaWiki Action API conventions —
> User-Agent, retry/backoff, and rate-limit etiquette — from **wikimedia-api-access**.
> Scans live on Commons (**wikimedia-commons**); parsing the wikitext of pages uses
> **wikimedia-wikitext**.

---

## Overview

Wikisource is Wikimedia's free digital library: 84 language editions holding millions of
proofread pages. It differs from every other Wikimedia project in one structural way —
**the source of truth is a scanned image, and the text is a transcription of it**. That
transcription happens in two dedicated namespaces (`Page:` and `Index:`) created by the
**ProofreadPage** extension, and every page carries an explicit quality level.

This skill covers both halves of the pipeline:

| Half | You need it when… | Covered in |
|------|-------------------|-----------|
| **Production** | checking proofreading progress, reading/validating page text, author pages | SOPs 1–5 |
| **Catalogue & delivery** | finding finished books across wikis, exporting EPUBs, counting completions | SOPs 0, 6–8 |

**When to use:**

- Measuring or reporting proofreading progress for a work or a wiki.
- Extracting the text layer of a page, or the compiled text of a work.
- Finding **finished** (proofread/validated) books across Wikisource editions.
- Generating EPUB/PDF files, or building on the Wikisource Reader app's data.
- Anything touching OCR, bulk OCR, or AI-assisted transcription — see §9, which encodes
  the community's rules, not just the endpoints.

**Out of scope:** uploading scans (use **wikimedia-commons**), general wikitext parsing
(**wikimedia-wikitext**), and Wikipedia article work.

---

## API basics

Site pattern: `https://{lang}.wikisource.org/w/api.php` (84 language editions; `www` for
multilingual/old Wikisource).

| Module | Purpose |
|--------|---------|
| `prop=proofread` | quality level of a single `Page:` page |
| `prop=proofreadinfo` | per-page quality for an `Index:` page |
| `list=proofreadpages` | list pages in an Index filtered by quality |
| `prop=pageprops` | Index-level properties (authors, publisher, year) |
| `meta=siteinfo&siprop=namespaces` | **resolve the Page/Index namespace IDs** (SOP 0) |
| `meta=siteinfo&siprop=statistics` | per-wiki scale (pages, active users) |
| `list=search` | full-text search; use the resolved numeric namespace for scope |

Docs: `MediaWiki:Extension:ProofreadPage` · `Wikisource:ProofreadPage` ·
`Help:Proofread` (en.wikisource).

**Quality levels** (ProofreadPage's `pagequality`):

| Code | Label | Meaning |
|-----:|-------|---------|
| 0 | Without text | image only — needs OCR or typing |
| 1 | Problematic | text present but flagged |
| 2 | Proofread | read once |
| 3 | Validated | read twice |
| 4 | **Without text (blank page)** | intentionally empty — exclude from progress maths |

> ⚠️ Level **4** is easy to miss: a blank leaf is not unfinished work. Counting it as
> "not done" understates progress.

---

## Quick smoke test

```bash
UA="MyTool/1.0 (https://example.org/me; me@example.org)"

# Scale of a wiki
curl -s -H "User-Agent: $UA" \
  "https://en.wikisource.org/w/api.php?action=query&meta=siteinfo&siprop=statistics&format=json"

# Quality of one page (returns pagequality)
curl -s -H "User-Agent: $UA" \
  "https://en.wikisource.org/w/api.php?action=query&titles=Page:Example/1&prop=proofread&format=json"

# The cross-wiki catalogue of finished books
curl -s -H "User-Agent: $UA" "https://wsindex.toolforge.org/books/?languages=en&page_size=2"
```

---

## SOP 0 — Resolve Page/Index namespaces (do this first, every time)

**This is the #1 source of silently-empty results on Wikisource.** The ProofreadPage
namespace IDs are **not portable** across editions, and neither are the names:

| Wiki | Page | Index |
|------|------|-------|
| en | 104 `Page` | 106 `Index` |
| fr | 104 `Page` | 112 **`Livre`** |
| de | 102 `Seite` | 104 `Index` |
| pl | 100 `Strona` | 102 `Indeks` |
| it | 108 `Pagina` | 110 `Indice` |
| pt | 106 `Página` | **104** `Galeria` |
| bn | 104 `পাতা` | **102** `নির্ঘণ্ট` |
| ml | 106 `താൾ` | **104** `സൂചിക` |
| sv | 104 `Sida` | 108 `Index` |
| ta | **250** `பக்கம்` | **252** `அட்டவணை` |

Do **not** hardcode 104/106, and do **not** apply an "Index = Page + 2" offset — it is
false on sv (104/108), and on pt/bn/ml the Index ID is *lower* than the Page ID. The
offset rule also lands on *Portal* namespaces: fr `Portail`, bn `প্রবেশদ্বার`,
pt `Em Tradução`, ml `കവാടം`.

**The reliable method is the content model** — ProofreadPage's own marker:

```python
import json, urllib.parse, urllib.request

UA = "MyTool/1.0 (https://example.org/me; me@example.org)"

def _api(lang, params):
    params = dict(params, format="json")
    url = f"https://{lang}.wikisource.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def content_model(lang, ns_id):
    """Sample one page in a namespace and return its content model."""
    listing = _api(lang, {"action": "query", "list": "allpages",
                          "apnamespace": str(ns_id), "aplimit": "1"})
    pages = listing.get("query", {}).get("allpages", [])
    if not pages:
        return None
    info = _api(lang, {"action": "query", "titles": pages[0]["title"], "prop": "info"})
    for _pid, page in info.get("query", {}).get("pages", {}).items():
        return page.get("contentmodel")
    return None

# proofread-page  -> Page namespace
# proofread-index -> Index namespace
# (a Portal namespace returns plain "wikitext" — the trap above)
```

For a ready-made cross-wiki resolver with confidence reporting, use
`assets/ws_namespace_resolver.py`:

```bash
python3 assets/ws_namespace_resolver.py de pl it sv ta   # or --all-sampled, --json
```

---

## SOP 1 — Proofreading progress for a work

```python
def work_stats(lang: str, index_title: str) -> dict:
    """Quality distribution for an Index: page.

    Returns {"total","without_text","problematic","proofread","validated",
             "blank","percent_done"}.
    """
    data = _api(lang, {"action": "query", "titles": index_title,
                       "prop": "proofreadinfo", "piprop": "quality"})
    stats = {"without_text": 0, "problematic": 0, "proofread": 0,
             "validated": 0, "blank": 0, "total": 0}
    for pid, page in data.get("query", {}).get("pages", {}).items():
        if pid == "-1":
            continue
        q = page.get("pagequality", 0)
        stats[{0: "without_text", 1: "problematic", 2: "proofread",
               3: "validated", 4: "blank"}.get(q, "without_text")] += 1
        if q != 4:                      # blank leaves are not work in progress
            stats["total"] += 1
    if stats["total"]:
        done = stats["proofread"] + stats["validated"]
        stats["percent_done"] = round(done / stats["total"] * 100, 1)
    return stats
```

`assets/ws_proofread_checker.py` implements this (plus per-page status and
quality-filtered page lists) as an importable class; `scripts/ws-page-status.sh` is the CLI.

---

## SOP 2 — Read the text layer of a page

```python
import re

def page_text(lang: str, page_title: str) -> str | None:
    """Raw text layer of a Page: page, with header/footer markup stripped."""
    data = _api(lang, {"action": "parse", "page": page_title, "prop": "wikitext"})
    if "parse" not in data:
        return None
    wt = data["parse"]["wikitext"]["*"]
    for pat in (r"\{\{header\|.*?\}\}", r"\{\{footer\|.*?\}\}",
                r"\{\{c\|.*?\}\}", r"\{\{nop\}\}", r"<!--.*?-->"):
        wt = re.sub(pat, "", wt, flags=re.S)
    return wt.strip()
```

`assets/ws_text_extractor.py` / `scripts/ws-text-extract.sh` do this with more markup cases.

> An empty text layer or a lone `{{blank}}` means **no transcription yet** — do not
> record that as an empty page of content.

---

## SOP 3 — Compiled work text and author pages

```python
def work_text(lang: str, title: str) -> str | None:
    """The transcluded text of a compiled work (main namespace)."""
    data = _api(lang, {"action": "parse", "page": title, "prop": "wikitext"})
    return data.get("parse", {}).get("wikitext", {}).get("*")

def author_works(lang: str, author: str) -> list[str]:
    """Pages that transclude an Author: page (its work list)."""
    data = _api(lang, {"action": "query", "list": "embeddedin",
                       "eititle": f"Author:{author}", "eilimit": "max"})
    return [p["title"] for p in data.get("query", {}).get("embeddedin", [])]
```

Compiled text is assembled by the `<pages index="…" from=1 to=100 header=1 />` tag, so
`action=parse` on the main-namespace title returns the assembled text, while parsing a
`Page:` title returns only that page's layer.

---

## SOP 4 — Cross-wiki scale

```python
def wiki_scale(lang: str) -> dict:
    d = _api(lang, {"action": "query", "meta": "siteinfo", "siprop": "statistics"})
    s = d["query"]["statistics"]
    return {k: s[k] for k in ("pages", "articles", "edits", "users", "activeusers")}
```

Useful context: Wikisource editions have **huge corpora and tiny editor bases**
(measured 2026-09-11 — en: 4,867,641 pages / 1,128,923 content pages / **616** active
users; fr: 4,814,221 / 710,753 / **293**; de: 712,923 / 654,049 / **146**;
pl: 1,368,365 / 1,327,109 / **70**). Tooling that amplifies a handful of proofreaders
matters more here than on Wikipedia.

---

## SOP 5 — Asking whether a work is "done" (the honest answer)

Combine two signals, and state which you used:

1. **Wikidata sitelink badge** (cross-wiki, curated): `proofread` `Q20748092` /
   `validated` `Q20748093` — see SOP 6 and the bias warning below.
2. **Index-level quality distribution** (authoritative for one work): SOP 1.

```sparql
# SPARQL: works on a given Wikisource carrying a completion badge
SELECT ?item ?itemLabel WHERE {
  ?sitelink schema:isPartOf <https://en.wikisource.org/> ; schema:about ?item .
  { ?sitelink wikibase:badge wd:Q20748092. } UNION { ?sitelink wikibase:badge wd:Q20748093. }
  ?item wdt:P1957 ?indexPage .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

> ⚠️ **Badge adoption is wildly uneven** (measured 2026-09-11): ta 99.4 %, bn 91.6 %,
> en 80.8 %, fr 75.4 %, es 35.4 %, sv 33.0 %, it 19.4 %, ru 6.4 %, zh 5.6 %,
> **de 1.6 %, nl 0.0 %**. The badge measures *curation practice* as much as
> proofreading: de.wikisource (≈654k content pages) contributes 4 badged books.
> Never present badge-derived totals as "books finished on Wikisource" without this caveat.

---

## SOP 6 — The catalogue of finished books (wsindex)

`https://wsindex.toolforge.org/books/` — JSON, paginated, built from Wikidata, and the
data source behind the **Wikisource Reader** Android app.

```bash
UA="MyTool/1.0 (https://example.org/me; me@example.org)"
curl -s -H "User-Agent: $UA" "https://wsindex.toolforge.org/books/?languages=en&page_size=2"
```

Envelope: `{"count": N, "next": url|null, "previous": url|null, "results": [...]}`.
Per-book fields include `wikidata_qid`, `title`, `languages`, `authors`, `publishers`,
`date_of_publication`, `ws_url`, `wikisource_index_url`, **`epub_url`**, `view_count`.

```python
from ws_catalog import WsIndexClient      # assets/ws_catalog.py

client = WsIndexClient()
client.total()                 # 10302  (global, 2026-09-11)
client.total(languages="en")   #  2572
for book in client.iterate(languages="en", max_books=5):
    print(book["title"], book["epub_url"])
```

> ⚠️ **Parameter trap:** `languages` is a real filter; **unrecognised parameters are
> silently ignored**. `?wikidata_qid=Q…` returns the *unfiltered* list rather than an
> error. After adding any filter, sanity-check `count` (global total 10,302; `en` 2,572) —
> a "working" filter that returns data may not have been applied at all.

Selection rule (from the tool's source): the work's Wikisource sitelink must carry a
`proofread` or `validated` **badge**, have a `P1957` (index page URL), and have **exactly
one** such index page.

---

## SOP 7 — EPUB / PDF export

| Endpoint | Use |
|----------|-----|
| `https://ws-export.wmcloud.org/` | interactive UI (all languages) |
| `https://ws-export-app.wmcloud.org/?format=epub-3&lang=en&page=Constitution_of_the_United_States_of_America` | direct download — returns `application/epub+zip` (swap `lang`/`page` for any catalogue entry) |

`epub_url` in wsindex records is exactly this second form, so you can hand a reader an
EPUB without touching the API. Per-wiki output (fonts, credits, templates) is configured
via `Wikisource:WS Export`; some of that configuration requires admin rights.

---

## SOP 8 — Consumers to build on

| Project | What | Interface |
|---------|------|-----------|
| **Wikisource Reader** (Android) | Reader for proofread/validated works; 22 languages; offline + TTS | consumes **wsindex**; repo `cis-india/Wikisource-Reader` |
| **Sangkalak** | Cross-Wikisource library catalogue (Toolforge) | web UI only — **no public API** (`/api/` → 404) |

---

## SOP 9 — OCR and AI-assisted transcription

**Endpoints:** `https://ocr.wmcloud.org/` (Google Cloud Vision for scripts Tesseract
can't handle, Tesseract otherwise; **images only, no PDF**) ·
`https://ws-google-ocr.toolforge.org/` (standalone, any Commons image URL) ·
`https://wsstats.toolforge.org/` (ProofreadPage usage statistics).

DjVu/PDF **text layers** (often vendor OCR) are injected into the edit window on a page's
first edit — so inherited text quality is part of the pipeline, not just on-demand OCR.

Bulk OCR is an **active, unfinished** area: GSoC 2026 **T420680** ("Bulk OCR
Improvements", umbrella **T415145**) exists precisely because the extension's bulk OCR
lacks access control, a **review step**, and progress reporting.

**Community norms — encode these as guardrails, not suggestions:**

1. **Never programmatically promote quality levels.** Machine OCR fills level 0/1;
   only human proofreading sets 2/3. A June 2026 bot approval on en.wikisource was
   explicitly limited to uploading at level 1.
2. **Don't pre-empt the proofreader.** The stated position: *"OCR dump ⇒ no one works
   on it immediately ⇒ discourages further work"* — add OCR where someone will proofread
   it soon, not as bulk volume.
3. **Fidelity beats plausibility.** Never "correct" a spelling, hyphen or pagination that
   is present in the scan; that is a proofreading judgement. (The same bot lost support
   for rewriting local transcriptions and dropping visible hyphens.)
4. **AI is an advisor, not a validator.** Any AI-assisted validation must be labelled —
   see the Scriptorium discussion and `User:Mathmitch7/…using AI to edit Wikisource`
   (Apr 2026): "validate with an asterisk".
5. **Do not transclude unproofread text into the main namespace** to "make progress".

---

## Guardrails

1. ❌ **Never hardcode namespace IDs (104/106) or assume `Index = Page + 2`.** Resolve via
   content model (SOP 0) — sv, pt, bn, ml and ta all break the offset convention, and the
   offset lands on Portal namespaces on fr/bn/pt/ml.
2. ❌ **Never filter by a localised namespace name alone.** fr calls its Index namespace
   `Livre`; pt calls it `Galeria`.
3. ❌ **Don't treat quality level 4 (blank) as unfinished.**
4. ❌ **Don't count a text layer as content when it's empty or `{{blank}}`.**
5. ❌ **Don't present badge-derived catalogues as complete completion statistics** —
   see SOP 5's adoption table.
6. ❌ **Don't assume a filter was applied** because results came back — the catalogue API
   ignores unknown parameters (SOP 6).
7. ❌ **Never auto-promote proofreading quality or auto-validate with AI** (SOP 9).
8. ❌ **Don't assume English conventions** — 84 editions, localised template families and
   layouts; `en` is not the default for anything except examples.
9. ⚠️ **Etiquette:** descriptive User-Agent on every request; handle 429 with backoff;
   pace requests ≥1 s apart outside Toolforge/WMCS. Multi-wiki sweeps
   (e.g. the namespace resolver over many editions) multiply that cost — pace them.

---

## Tooling

### 🔧 Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| [`scripts/ws-page-status.sh`](./scripts/ws-page-status.sh) | Proofreading progress for a work | `./ws-page-status.sh en "Index:Example.pdf"` |
| [`scripts/ws-text-extract.sh`](./scripts/ws-text-extract.sh) | Cleaned text of a `Page:` page | `./ws-text-extract.sh en "Page:Example/1"` |

### 🐍 Python Assets

| Asset | Purpose | Usage |
|-------|---------|-------|
| [`assets/ws_namespace_resolver.py`](./assets/ws_namespace_resolver.py) | Resolve Page/Index namespaces across wikis via content models (T74525) | `python3 ws_namespace_resolver.py de pl` |
| [`assets/ws_proofread_checker.py`](./assets/ws_proofread_checker.py) | Work stats, per-page status, quality-filtered page lists | `from ws_proofread_checker import ProofreadChecker` |
| [`assets/ws_text_extractor.py`](./assets/ws_text_extractor.py) | Page text layer with header/footer stripping | `from ws_text_extractor import TextExtractor` |
| [`assets/ws_catalog.py`](./assets/ws_catalog.py) | wsindex client: totals, paging, per-language filtering | `python3 ws_catalog.py --languages en --limit 5` |

### 📚 Reference Docs

| Document | Contents |
|----------|----------|
| [`references/wikisource-proofread-workflow.md`](./references/wikisource-proofread-workflow.md) | Three-namespace system, quality levels, lifecycle, API modules |
| [`references/wikisource-catalog-and-delivery.md`](./references/wikisource-catalog-and-delivery.md) | Wikidata Books model, wsindex, badge-adoption bias, WSExport, consumers, OCR/AI norms, namespace table |

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent, retries, rate-limit etiquette for every call here |
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | The scans (DjVu/PDF) that ProofreadPage transcribes |
| **[wikimedia-commons-pdf](../wikimedia-commons-pdf/SKILL.md)** | PDF/DjVu file handling behind the page images |
| **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** | Parsing the wikitext of Page:/main-namespace content |
| **[wikidata](../wikidata/SKILL.md)** | The Books data model, `P1957`, and sitelink badges |
| **[wikimedia-pageviews](../wikimedia-pageviews/SKILL.md)** | Measuring readership of exported/compiled works |
| **[pywikibot](../pywikibot/SKILL.md)** | Batch operations across Wikisource editions |
| **[wiktionary](../wiktionary/SKILL.md)** | The sister dictionary project (separate skill) |
