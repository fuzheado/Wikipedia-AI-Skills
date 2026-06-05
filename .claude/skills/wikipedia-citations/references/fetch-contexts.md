# Citation Fetching: Where Metadata Comes From

When a tool fetches citation metadata from a URL, *where* the fetch happens
determines whether it succeeds or fails. This document explains the different
execution contexts and their implications.

---

## The Fetch Paths

```
                    ┌─────────────────────────┐
                    │  You (user's machine)   │
                    │  Home/office IP         │
                    │  `dead_link_scanner.py`  │
                    │  `expand-bare-url.sh`    │
                    │  `wayback_inspector.py`  │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │  The Target Website     │
                    │  (nytimes.com, doi.org, │
                    │   example.org, etc.)    │
                    └──────────┬──────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼─────────┐ ┌───────▼───────┐ ┌──────────▼─────────┐
│  WMF Servers      │ │  Toolforge    │ │  Wayback Machine   │
│  Citoid API       │ │  reFill,      │ │  archive.org       │
│  api.wikimedia.org│ │  Citation Bot │ │  (their own infra) │
│  WMF IP ranges    │ │  WMF IPs      │ │  Internet Archive  │
└───────────────────┘ └───────────────┘ └────────────────────┘
```

There are **five distinct execution contexts**, each with different network
characteristics:

| Context | Who Runs It | IP Range | Typical UA | Examples |
|---------|------------|----------|------------|----------|
| **Your machine** | You | Your ISP/home IP | Custom agent string | `dead_link_scanner.py`, `curl`, browser |
| **WMF servers** | Wikimedia Foundation | WMF production IPs | `Citoid/...` | Citoid API, REST API |
| **Toolforge** | Community tool maintainers | WMF cloud IPs | `reFill/...`, `CitationBot/...` | reFill, Citation Bot |
| **Internet Archive** | archive.org | IA IPs | `Mozilla/5.0...` (archive bot) | Wayback `/save` |
| **Browser (VE)** | You, in browser | Your ISP, + cookies | Full browser UA | VisualEditor's auto-cite |

---

## How Each Context Affects Success

### 1. Your Machine (Client-Side)

**When you run:** `python3 dead_link_scanner.py Albert_Einstein`
**or:** `python3 citoid_fetcher.py https://example.com`

| Factor | Effect |
|--------|--------|
| IP diversity | Your home/office IP. If it's a residential IP, fewer sites block it. If a datacenter/VPS IP, more sites may challenge it. |
| Cloudflare | If you run from a residential IP behind a normal ISP, most Cloudflare-protected sites will pass the check. From a cloud/VPS IP, you may get CAPTCHAs. |
| Geolocation | A site may return different content (or block) based on your country. From inside the EU, GDPR consent pages may interfere. From the US, some European sites may block. |
| Rate limits | Per-IP rate limits apply to *your* IP. If you scan 200 URLs from a page, the target site sees 200 requests from your IP — may trigger rate limiting. |
| Academic access | If you're on a university network, you may have access to paywalled journal content. From home, the same URLs may redirect to a login page. |
| VPN/proxy | May bypass geoblocks but may also trigger Cloudflare challenges. |

**Best for:** URLs that work for normal web browsing. Residential IPs generally
have the widest access. Worst for: high-volume scraping (rate limits).

### 2. WMF Servers (Citoid)

**When you call:** `https://en.wikipedia.org/api/rest_v1/data/citation/zotero/{URL}`

| Factor | Effect |
|--------|--------|
| IP reputation | WMF IPs are well-known. Some sites **whitelist** them (academic databases, government sites). Others **block** them (some news sites, forums). |
| Zotero translators | Citoid uses Zotero's translator library — 500+ site-specific scrapers that know how to extract metadata from each site's HTML structure. This is its superpower. |
| Structured data | Citoid also reads JSON-LD, microdata, and Open Graph metadata embedded in pages. |
| Cloudflare | WMF IPs may trigger Cloudflare challenges on some sites — but Zotero translators often have workarounds. |
| Rate limits | WMF servers have dedicated relationships with some providers. Crossref, for example, gives Wikimedia priority access. |
| DOI/ISBN resolution | WMF servers resolve DOIs and ISBNs through Crossref and other databases that may not be accessible from your machine. |

**Best for:** Major news sites, academic journals (via DOI), books (via ISBN),
and any site with a Zotero translator. Worst for: obscure blogs, sites behind
login walls, sites that block WMF IPs.

### 3. Toolforge (reFill, Citation Bot)

**When you use:** `https://refill.toolforge.org/ng/api/en.wikipedia.org/Article`

| Factor | Effect |
|--------|--------|
| IP range | Toolforge shares WMF cloud infrastructure. Same IP considerations as Citoid, but different subranges. |
| reFill's approach | reFill fetches each URL from Toolforge servers and runs it through Zotero translators (same engine as Citoid). It then generates a diff showing the expanded citations. |
| Citation Bot's approach | Citation Bot adds DOIs from Crossref, PMIDs from PubMed, and archive URLs. It does NOT re-fetch URLs — it adds identifiers to existing templates. |
| Rate limits | Toolforge has generous outbound access but shares bandwidth with other tools. Long-running batch jobs may be throttled. |

**Best for:** Bulk operations on existing Wikipedia pages. Worst for: real-time
single-URL lookups (use Citoid directly instead).

### 4. Internet Archive (Wayback Machine)

**When you call:** `https://archive.org/wayback/available?url=...`

| Factor | Effect |
|--------|--------|
| `/available` | Read-only. Checks if a URL has been archived. No rate limit issues. Fast. |
| `/save` | **Writes** a new archive. Heavily rate-limited. The save request comes from IA's own crawlers, not from your machine. |
| Coverage | IA may have archives that no other service has — including pages that are now gone. Conversely, some sites block IA's crawlers. |
| IP | The check comes from your machine (client-side). The save is IA's infrastructure. |

**Best for:** `/available` — always use it. It's free, fast, and unblocked.
`/save` — use sparingly (1–2/minute).

### 5. Your Browser (VisualEditor)

**When you use:** VisualEditor's "Cite" button

| Factor | Effect |
|--------|--------|
| Cookies | Your browser sends your login cookies. Some sites return different content to logged-in users. |
| JavaScript | The page executes in your browser. JS-rendered content is visible. Citoid and CLI tools see the raw HTML before JS runs. |
| User-Agent | Full browser UA string. Many sites treat browser traffic differently from script traffic. |
| geolocation | Same as your machine, but with the addition of browser-based geolocation APIs. |

**Best for:** Interactive use. The browser can render JavaScript and send
authenticated cookies. Worst for: automation (obviously).

---

## Concrete Examples: When Each Context Succeeds or Fails

| Target URL | Your Machine | Citoid (WMF) | Toolforge | Browser |
|-----------|-------------|--------------|-----------|---------|
| `nytimes.com/article` | ✅ Works | ✅ Zotero translator | ✅ | ✅ |
| `twitter.com/user/status` | ✅ Works | ⚠️ Sometimes blocked | ⚠️ | ✅ (if logged in) |
| `10.1038/nature12373` (DOI) | ⚠️ May redirect to paywall | ✅ Crossref metadata | ✅ | ⚠️ Paywall |
| `academic.journal.edu/article` | ⚠️ May need institutional login | ⚠️ May need subscription | ⚠️ | ⚠️ (unless on campus) |
| `obscure-blog.blogspot.com` | ✅ Works | ⚠️ No Zotero translator | ⚠️ | ✅ |
| `archive.org/details/book` | ✅ Works | ⚠️ May be blocked | ⚠️ | ✅ |
| `web.archive.org/web/...` | ✅ Works | ⚠️ Sometimes blocked | ⚠️ | ✅ |
| `cloudflare-protected-site.com` | ⚠️ May get challenge | ❌ Usually blocked | ❌ | ✅ (browser passes) |
| `facebook.com/post` | ⚠️ Login required | ❌ Blocked | ❌ | ⚠️ (if logged in) |
| `wikipedia.org/wiki/Article` | ✅ Works | ✅ (trivial) | ✅ | ✅ |

---

## Strategy: How to Choose

### Rule of thumb: Try Citoid first, fall back to client-side

```python
def fetch_citation_metadata(url: str) -> dict | None:
    """Try Citoid first, then fall back to direct fetch."""
    # Attempt 1: Citoid (WMF server-side, Zotero translators)
    citoid_result = try_citoid(url)
    if citoid_result and has_meaningful_data(citoid_result):
        return citoid_result

    # Attempt 2: Direct fetch from your machine
    # (works for sites that block WMF IPs but allow client IPs)
    page = fetch_page_directly(url)
    metadata = extract_metadata_from_html(page)
    return metadata
```

### Context-specific strategies

| Scenario | Best Strategy |
|----------|--------------|
| **Single URL, major site** | Citoid. Fast, accurate, Zotero knows the structure. |
| **Single URL, unknown site** | Citoid first. If no data, fetch directly and parse `<title>`, JSON-LD, OG tags. |
| **Bulk URLs from a Wikipedia page** | reFill (Toolforge). Designed for this. |
| **DOI/ISBN lookup** | Citoid always. Crossref metadata is the authoritative source. |
| **Dead link check on a page** | Client-side (`dead_link_scanner.py`). You need to actually hit each URL, and WMF IPs may be blocked. |
| **Archive check** | Wayback `/available` from client-side. Free and fast. |
| **Academic paywalled article** | Citoid for metadata (DOI → Crossref). You won't get full text from any automated tool. |
| **Cloudflare-protected site** | Browser only. None of the automated tools will reliably get through. |

### The hybrid approach: `citoid_fetcher.py`

The `citoid_fetcher.py` script in this skill calls the Citoid API, which runs
on WMF servers. This means it gets:
- ✅ Zotero translator metadata for well-known sites
- ✅ Crossref metadata for DOIs
- ✅ ISBN resolution
- ❌ None of the client-side benefits (no bypass for WMF IP blocks)

If Citoid returns no data, try fetching the page directly from your machine.
The `dead_link_scanner.py` script does this and extracts metadata from common
HTML patterns.

---

## Summary

| Tool | Where fetch happens | Best when... | Worst when... |
|------|-------------------|-------------|---------------|
| Citoid API | WMF servers | Target has Zotero translator or is a DOI/ISBN | Target blocks WMF IPs |
| reFill | Toolforge | Bulk expansion of bare URLs on a page | Target blocks WMF IPs |
| Citation Bot | Toolforge | Adding DOIs/archives to existing citations | Citations are complete |
| `dead_link_scanner.py` | Your machine | Checking URL liveness, obscure sites | You're on a blocked IP |
| `wayback_inspector.py` | Your machine for check, IA for save | Archive discovery | `/save` rate limits |
| Browser (VE) | Your browser + cookies | JS-heavy sites, logged-in content | Automation |

No single method works for every URL. The best approach is to try multiple
contexts in order and use the first one that returns useful data.
