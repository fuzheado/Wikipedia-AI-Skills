# Citation Tools & Methods — Decision Guide

There are many ways to work with Wikipedia citations, from fully manual to
fully automated. This guide explains each approach, when to use it, and how
they complement each other.

---

## The Tools Compared

| Method | Approach | Data Source | Best For | Limitations |
|--------|----------|-------------|----------|-------------|
| **Manual templates** | Hand-write `{{cite web}}` etc. | Your own knowledge | Simple citations with known metadata | Slow; error-prone; requires knowing template syntax |
| **`citation_generator.py`** | Interactive prompts | User input | Learning template syntax; one-off citations | Manual; no auto-fetching |
| **Citoid API** (`citoid_fetcher.py`, `citoid-expand.sh`) | Auto-fetches metadata from URL/DOI/ISBN | Zotero translators + Crossref | **Expanding bare URLs**; DOI/ISBN lookups; bulk work | Not all sites have Zotero translators; may return noisy data |
| **reFill** (external tool) | Extracts URLs from a page, auto-expands each | Zotero translators | **Cleaning up many bare URLs** on a page at once | External service; requires Toolforge |
| **Citation Bot** (external tool) | Adds DOIs, identifiers, archive links | Crossref, PubMed, Wayback | **Fleshing out existing citations** (add DOIs, fill gaps) | External service; may overwrite manual edits |
| **Wayback Machine** (`wayback_inspector.py`, `archive-check.sh`) | Checks/saves archives | archive.org | **Verifying link rot**; finding archive URLs | Read-only check is free; `/save` is rate-limited |
| **Dead link scanner** (`dead_link_scanner.py`, `check-dead-links.sh`) | HTTP-checks every URL in a page | The live web | **Auditing a page for dead links** | Network-heavy; slow for large pages |
| **`citation_linter.py`** | Static analysis of wikitext | Page wikitext | **Validating template completeness** | No network checks; only checks template syntax |
| **`citation-inspector.sh`** | Summary statistics | Page wikitext | **Getting an overview** of citation health | Shallow; doesn't check URLs |

---

## Decision Flowchart

```
You have a URL and need a citation?
├─ URL is from a major site (NYT, BBC, DOI, etc.)
│  → Use Citoid (citoid_fetcher.py or citoid-expand.sh)
│  → It auto-detects title, author, date, publisher
│
├─ URL is from an obscure site or you want full control
│  → Use citation_generator.py (interactive prompts)
│  → Or hand-write the template from known metadata
│
└─ URL is already on a Wikipedia page as a bare URL
   → Use reFill (toolforge) for batch expansion
   → Or Citoid for one-at-a-time

You have a DOI/ISBN/PMID and need a citation?
└─ → Use Citoid (citoid_fetcher.py)
   → It returns journal/book metadata with authors, volume, pages

You have an existing citation and want to improve it?
├─ Missing identifiers (DOI, PMID, ISBN)?
│  → Use Citation Bot (toolforge)
│
├─ Missing archive URL?
│  → Use wayback_inspector.py with --save
│  → Then manually add |archive-url= and |archive-date=
│
└─ Missing fields (access-date, publisher, etc.)?
   → Use citation_linter.py first to find what's missing
   → Then re-fetch with Citoid to fill gaps

You want to audit a page's citations?
├─ Quick overview?
│  → citation-inspector.sh (counts, template types)
│
├─ Deep validation?
│  → citation_linter.py (checks each template for missing params)
│
├─ Dead link check?
│  → dead_link_scanner.py (HTTP-checks every URL)
│  → check-dead-links.sh (lighter, CLI-focused version)
│
└─ Full workflow?
   → citation-inspector.sh → citation_linter.py → dead_link_scanner.py
   → Then wayback_inspector.py for dead URLs found

You are writing a new article?
└─ → Start with Citoid for URL-based sources
   → Use citation_generator.py for books/journals you have ISBNs for
   → Run citation_linter.py before saving to check for gaps
```

---

## How the Methods Interoperate

### Pipeline 1: Audit → Fix → Archive

```
citation-inspector.sh  →  Shows what's there
       ↓
citation_linter.py     →  Finds missing fields
       ↓
citoid_fetcher.py      →  Re-fetches metadata to fill gaps
       ↓
dead_link_scanner.py   →  Checks which URLs are still live
       ↓
wayback_inspector.py   →  Finds/saves archives for dead links
```

### Pipeline 2: Bare URL → Full Citation → Verified

```
expand-bare-url.sh     →  Quick {{cite web}} from URL
       ↓           OR
citoid-expand.sh       →  Smarter: auto-detects type (web/news/journal)
       ↓
citoid_to_template()   →  Converts to proper CS1 template
       ↓
dead_link_scanner.py   →  Verifies URL still works
       ↓
wayback_inspector.py   →  Archives the source if not already
```

### Pipeline 3: New Article → Citations Complete

```
For each source:
  citoid_fetcher.py <url|doi|isbn>  →  Generates template
  wayback_inspector.py <url>        →  Checks for archive

After all citations are assembled:
  citation_linter.py <page_title>   →  Validates all templates

Final check:
  citation-inspector.sh <page_title> →  Summary report
```

---

## Strengths & Weaknesses Per Method

### Citoid (citoid_fetcher.py / citoid-expand.sh)

**Strengths:**
- Fully automatic — no manual data entry
- Handles URLs, DOIs, ISBNs, PMIDs, QIDs
- Returns structured data with authors, dates, publishers
- Deployed on all WMF wikis — no auth needed
- Fast: ~1 second per lookup

**Weaknesses:**
- Quality depends on Zotero translators. Major sites (NYT, BBC, DOI) work well.
  Obscure blogs or PDF-only sites may return minimal or no data.
- May return multiple results (disambiguation), requiring manual selection
- Does not handle paywalled content that blocks crawlers
- Returns access-date as today's date — may not match when you actually accessed it

### Wayback Machine (wayback_inspector.py)

**Strengths:**
- `/available` endpoint is fast and has no rate limits
- Can verify if an archive exists before linking to it
- `/save` can create archives on demand

**Weaknesses:**
- `/save` is heavily rate-limited (1–2 req/min recommended)
- Not all URLs are saved — the Wayback Machine has gaps
- Some archived pages are broken (JS-heavy sites, redirect loops)
- No public API for archive.today

### Dead Link Detection (dead_link_scanner.py)

**Strengths:**
- Actually checks each URL by making an HTTP request
- Detects 404s, connection errors, redirects
- Suggests archives for dead links automatically

**Weaknesses:**
- Slow for pages with many citations (each URL = one HTTP request)
- Some sites block automated requests (returns false positives)
- Cannot check pages behind login/paywall
- Respecting rate limits means a full audit can take minutes

### Citation Linter (citation_linter.py)

**Strengths:**
- Instant — no network calls (pure wikitext analysis)
- Catches missing required parameters, malformed templates
- Detects `url-status` without `archive-url` (common mistake)

**Weaknesses:**
- Cannot verify URLs — purely syntactic analysis
- Does not check if citation metadata is factually correct
- May flag false positives for unusual but valid template usage

### Manual Template Generation (citation_generator.py)

**Strengths:**
- Full control over every parameter
- Works for any source, no matter how obscure
- No API dependencies

**Weaknesses:**
- Manual — requires knowing the metadata
- Slow for bulk work
- Prone to human error (typos, wrong fields)

---

## When to Use External Tools

### reFill (toolforge)

Use reFill when a page has **many bare URLs** and you want to expand them all at once.
It processes an entire page in one go, running each URL through Zotero translators.
The result is a diff you can review before saving.

**Limitation:** Only works on pages that already exist on Wikipedia. Not for new citations.

### Citation Bot (toolforge)

Use Citation Bot when you have **existing citations that are incomplete** — it adds
DOIs from Crossref, PMIDs from PubMed, and archive URLs from the Wayback Machine.
It fills in missing fields without changing what's already there.

**Limitation:** May add data you don't want (e.g., a DOI for a print article). Always
review the diff before saving.

---

## How Modern Is Each Method?

| Method | Technology | Age | Maintenance |
|--------|-----------|-----|-------------|
| Manual templates | Wikitext | As old as Wikipedia | Always current |
| `citation_generator.py` | Python CLI | 2026 (this project) | Active |
| Citoid | Node.js REST API | 2014–present | **Active** — WMF-maintained |
| reFill | PHP + Toolforge | 2010–present | **Active** — community-maintained |
| Citation Bot | Python + Toolforge | 2008–present | **Active** — community-maintained |
| Wayback Machine | REST API | 2001–present | **Active** — Internet Archive |
| Zotero translators | JavaScript | 2006–present | **Active** — community-maintained |

All major services are actively maintained. The bottlenecks are:
- **Zotero translator quality** — determines how well Citoid and reFill work for a given site
- **Wayback Machine coverage** — determines whether archives are available
- **Crossref/PubMed data** — determines how well DOI/PMID lookups work
