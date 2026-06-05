---
name: wikipedia-citations
description: Master Wikipedia citations — CS1/CS2 templates, Wayback Machine archiving, dead link detection, bare URL expansion, citation maintenance, and reference validation
depends_on: [wikimedia-api-access]
license: MIT
compatibility: opencode
---

> ⚠️ **User-Agent required:** API calls below need a descriptive `User-Agent` header.
> See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.

This skill assumes you already understand the anatomy of a Wikipedia article — see
**[wikipedia-page-anatomy](../wikipedia-page-anatomy/SKILL.md)** for infoboxes,
categories, navboxes, and the basic reference section structure.

---

## Reference: CS1 Citation Templates

CS1 (Citation Style 1) is the standard template family for inline citations on
English Wikipedia. Every template has required, recommended, and optional parameters.

### Core Templates

| Template | For | Minimal Parameters |
|----------|-----|-------------------|
| `{{cite web}}` | Web pages | `url`, `title`, `website`, `access-date` |
| `{{cite news}}` | News articles | `url`, `title`, `newspaper`, `date` |
| `{{cite book}}` | Books | `title`, `author`/`last`, `year`, `isbn` |
| `{{cite journal}}` | Academic papers | `title`, `author`, `journal`, `volume`, `pages`, `doi` |
| `{{cite magazine}}` | Magazines | `url`, `title`, `magazine`, `date` |
| `{{cite encyclopedia}}` | Encyclopedias | `title`, `encyclopedia`, `year` |
| `{{cite report}}` | Reports | `url`, `title`, `institution`, `date` |
| `{{cite arXiv}}` | Preprints | `eprint`, `class`, `date` |
| `{{cite bioRxiv}}` | Biology preprints | `biorxiv`, `date` |
| `{{cite conference}}` | Conference papers | `url`, `title`, `book-title`, `conference`, `date` |
| `{{cite thesis}}` | Theses/dissertations | `title`, `type` (e.g. PhD), `publisher`, `year` |
| `{{cite patent}}` | Patents | `country`, `number`, `title`, `pubdate` |
| `{{cite podcast}}` | Podcast episodes | `url`, `title`, `series`, `date` |
| `{{cite interview}}` | Interviews | `last`, `first`, `subject-link`, `interviewer`, `title`, `date` |
| `{{cite AV media}}` | Videos, films | `url`, `title`, `people`, `date`, `medium` |
| `{{cite episode}}` | TV/radio episodes | `title`, `series`, `network`, `date`, `season`, `number` |
| `{{cite map}}` | Maps | `url`, `title`, `publisher`, `date` |
| `{{cite press release}}` | Press releases | `url`, `title`, `publisher`, `date` |
| `{{cite sign}}` | Signs, plaques | `title`, `medium` (e.g. bronze plaque), `location`, `date` |
| `{{cite speech}}` | Speeches | `url`, `title`, `event`, `location`, `date`, `speaker` |
| `{{cite tech report}}` | Technical reports | `url`, `title`, `institution`, `number`, `date` |
| `{{cite court}}` | Court cases | `litigants`, `vol`, `reporter`, `opinion`, `court`, `date` |
| `{{cite legislation}}` | Laws | `title`, `legislature`, `date` |
| `{{cite web source}}` | Wikisource | `url`, `title`, `wslink` |

### Common Parameters (Across All CS1 Templates)

| Parameter | Description | Example |
|-----------|-------------|---------|
| `url` | Full URL of the source | `https://example.com/article` |
| `title` | Title of the source | `The Great Breakthrough` |
| `trans-title` | English translation of title | `La Grande Percée` |
| `last` / `first` | Author name | `last=Einstein`, `first=Albert` |
| `author-link` | Wikipedia article about the author | `Albert_Einstein` |
| `date` | Publication date | `5 June 2026` or `2026-06-05` |
| `year` | Publication year (when full date unknown) | `2026` |
| `work` / `publisher` / `website` / `journal` / `newspaper` | Publication name | `The New York Times` |
| `series` | Series of which this is part | `Lecture Notes in Physics` |
| `volume` | Journal volume | `42` |
| `issue` | Journal issue number | `3` |
| `pages` | Specific pages | `123–145` |
| `page` | Single page | `42` |
| `at` | Precise location (section, paragraph, etc.) | `para. 5` |
| `doi` | Digital Object Identifier | `10.1000/xyz123` |
| `pmid` | PubMed ID | `12345678` |
| `pmc` | PubMed Central ID | `PMC1234567` |
| `isbn` | International Standard Book Number | `978-0-262-52316-5` |
| `issn` | International Standard Serial Number | `0040-165X` |
| `oclc` | OCLC WorldCat ID | `123456789` |
| `jstor` | JSTOR stable URL ID | `123456` |
| `bibcode` | Bibcode (astrophysics) | `1924PhRv...23..123B` |
| `arxiv` | arXiv ID | `1234.56789` |
| `s2cid` | Semantic Scholar Corpus ID | `12345678` |
| `access-date` | When you accessed the URL | `5 June 2026` |
| `archive-url` | Wayback Machine archive URL | `https://web.archive.org/web/...` |
| `archive-date` | Date of the archive snapshot | `5 June 2026` |
| `url-status` | Status of the original URL | `live`, `dead`, `unfit`, `usurped` |
| `quote` | Relevant excerpt from the source | `"Einstein discovered..."` |
| `language` | Language (if not English) | `fr`, `de`, `es` |
| `format` | File format (if not HTML) | `PDF`, `DOC` |
| `id` | Free-form identifier | `ABC-123` |

### CS2 (Citation Style 2)

CS2 uses a single `{{citation}}` template instead of separate template types.
It accepts the same parameters as CS1:

```wikitext
<ref>{{citation |url= |title= |last= |first= |date= |publisher= |isbn=}}</ref>
```

Use CS2 when all your citations are similar in structure and you want a
uniform look. Use CS1 when citation types vary (web vs book vs journal)
and readers benefit from knowing the format at a glance.

---

## SOP: Named References and Reuse

Always use named references for sources cited more than once:

```wikitext
<ref name="einstein1950">{{cite book |last=Einstein |title=My Theory |year=1950}}</ref>

The same fact later.<ref name="einstein1950" />  ← slash-close reuses the footnote
```

**Auto-generate ref names** from the author surname + year:
- `einstein1950` for Einstein (1950)
- `smith2019a`, `smith2019b` for multiple Smith (2019) sources

---

## SOP: Archive URLs and the Wayback Machine

### Checking for Existing Archives

The Wayback Machine provides a JSON API to check if a URL has been archived:

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://archive.org/wayback/available"
params = {"url": "https://example.com/article"}

resp = requests.get(url, params=params, headers=headers)
data = resp.json()
# data["archived_snapshots"]["closest"]["url"] is the archive URL if one exists
# data["archived_snapshots"]["closest"]["timestamp"] is the snapshot date

if data.get("archived_snapshots"):
    snap = data["archived_snapshots"]["closest"]
    archive_url = snap["url"]
    archive_date = snap["timestamp"]  # Format: YYYYMMDDHHMMSS
else:
    print("No archive found")
```

### Saving a URL to the Wayback Machine

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
save_url = f"https://web.archive.org/save/{target_url}"
resp = requests.post(save_url, headers=headers)

if resp.status_code == 200:
    print("Page archived successfully")
```

**Note:** The save endpoint returns the archived page HTML. Rate limits apply —
be conservative with save requests.

### Adding Archive Parameters to a Citation

Once you have an archive URL, add it to the citation template:

```wikitext
<ref>{{cite web
 |url=https://example.com/original-article
 |title=Original Article
 |website=Example News
 |access-date=5 June 2026
 |archive-url=https://web.archive.org/web/20260605000000/https://example.com/original-article
 |archive-date=5 June 2026
 |url-status=live
}}</ref>
```

The `url-status` parameter controls behavior:
- `live` (default) — original URL is working; show archive as backup
- `dead` — original URL is dead; show archive as primary, original as secondary
- `unfit` — original was never suitable (e.g., low-quality source); suppress it
- `usurped` — domain was taken over; suppress original URL

### Using archive.today

```python
# archive.today does not have a public JSON API.
# To check if a URL is archived on archive.today:
check_url = f"https://archive.is/https://example.com"
resp = requests.head(check_url, headers=headers)
if resp.status_code == 200:
    print("Archived on archive.today")
```

---

## SOP: Detecting and Handling Dead Links

### Find Pages with Dead Links

The Action API can find pages tagged with dead link templates:

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
params = {
    "action": "query",
    "list": "categorymembers",
    "cmtitle": "Category:All articles with dead external links",
    "cmlimit": "max",       # Up to 500 per request
    "format": "json",
}

resp = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=headers)
data = resp.json()
pages = [p["title"] for p in data["query"]["categorymembers"]]
```

### Check Links Programmatically

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}

def check_url(url: str, timeout: int = 10) -> dict:
    """Check if a URL is live and returns useful content.
    
    Returns:
        {"status": "live", "code": 200}
        {"status": "dead", "code": 404}
        {"status": "redirect", "code": 301, "location": "..."}
        {"status": "error", "error": "connection refused"}
    """
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=False,  # Check redirects separately
        )
        if resp.status_code in (200, 304):
            return {"status": "live", "code": resp.status_code}
        elif resp.status_code in (301, 302, 303, 307, 308):
            return {
                "status": "redirect",
                "code": resp.status_code,
                "location": resp.headers.get("Location", "?"),
            }
        else:
            return {"status": "dead", "code": resp.status_code}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": str(e)}
```

### Dead Link Detection Workflow

For a full dead-link audit of a page:

1. Parse the wikitext and extract all `<ref>` tags with `url=` parameters
2. Check each URL with `check_url()` above
3. For dead URLs, query the Wayback Machine for an existing archive
4. If no archive exists, request one via the save endpoint
5. Report results: live, dead+archived, dead+noarchive, redirect

---

## SOP: Bare URL Expansion

Bare URLs (`<ref>https://example.com</ref>`) are strongly discouraged per
WP:BAREURL. Convert them to proper citations:

### Manual Expansion: Common Patterns

```wikitext
<!-- Bare URL -->
<ref>https://www.nytimes.com/2026/06/05/science.html</ref>

<!-- Converted -->
<ref>{{cite news
 |url=https://www.nytimes.com/2026/06/05/science.html
 |title=New Scientific Discovery
 |last=Johnson
 |first=Mark
 |date=5 June 2026
 |work=The New York Times
 |access-date=5 June 2026
}}</ref>
```

### Automated Tools

- **[reFill](https://refill.toolforge.org/)** — Expands bare URLs to full citations
  by fetching page metadata. Runs on Toolforge.
- **[Citation Bot](https://citation-bot.toolforge.org/)** — Adds DOI metadata,
  archive links, and fills in missing fields automatically.
- **[WP:REFLINKS](https://en.wikipedia.org/wiki/Wikipedia:REFLINKS)** —
  Browser-based tool for expanding bare references.

```bash
# reFill can be called programmatically (Toolforge required):
curl -s 'https://refill.toolforge.org/ng/api/en.wikipedia.org/Article_Title' \
  -H 'User-Agent: MyBot/1.0 (user@example.com) ContentGapResearch'
```

---

## SOP: Citation Maintenance Templates

These templates flag citation issues for human review:

| Template | When to Use | Placement |
|----------|-------------|-----------|
| `{{dead link}}` | URL returns 404 or connection error | Inside `<ref>`, at end: `<ref>...{{dead link}}</ref>` |
| `{{failed verification}}` | Source exists but does not support the claim | After the `<ref>` |
| `{{full citation needed}}` | Citation is missing key details (page, date, publisher) | After the `<ref>` |
| `{{page needed}}` | Source is cited but no specific page number given | After the `<ref>` |
| `{{bare URL}}` / `{{bare URL inline}}` | URL is not wrapped in a citation template | After the bare URL |
| `{{better source needed}}` | Source is weak, unreliable, or primary | After the `<ref>` |
| `{{verification needed}}` | Claim may not be verifiable from the cited source | After the claim |
| `{{self-published source}}` | Source is self-published | After the `<ref>` |
| `{{primary source inline}}` | Source is primary, secondary preferred | After the `<ref>` |
| `{{medical citation needed}}` | Medical claim needs a reliable medical source | After the claim |
| `{{third-party inline}}` | Source is too close to the subject | After the `<ref>` |

**When to add vs. when to fix:** If you can immediately fix the issue (add a
missing parameter, find an archive), do it. If you cannot, add the maintenance
template so a human editor knows what's wrong.

---

## SOP: Extracting and Analyzing Citations from a Page

### Parse All Citation URLs from Wikitext

```python
import re, requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}

def extract_citations(page_title: str, lang: str = "en") -> list[dict]:
    """Fetch page wikitext and extract all citation URLs and templates."""
    domain = f"{lang}.wikipedia.org"
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json",
    }
    resp = requests.get(f"https://{domain}/w/api.php", params=params, headers=headers)
    data = resp.json()
    wikitext = data["parse"]["wikitext"]["*"]

    citations = []

    # Pattern 1: Template-based citations
    for match in re.finditer(r"\{\{(cite \w+)([^}]*)\}\}", wikitext, re.IGNORECASE):
        template = match.group(1)
        params_text = match.group(2)

        # Extract url parameter
        url_match = re.search(r"\|?\s*url\s*=\s*([^|\n}]+)", params_text)
        url = url_match.group(1).strip() if url_match else None

        # Extract archive-url
        archive_match = re.search(r"\|?\s*archive-url\s*=\s*([^|\n}]+)", params_text)
        archive_url = archive_match.group(1).strip() if archive_match else None

        citations.append({
            "template": template,
            "url": url,
            "archive_url": archive_url,
            "raw": match.group(0)[:200],  # Truncated for display
        })

    # Pattern 2: Bare URLs inside <ref> tags
    for match in re.finditer(r"<ref>(https?://[^\s<]+)</ref>", wikitext):
        citations.append({
            "template": "bare URL",
            "url": match.group(1),
            "archive_url": None,
            "raw": match.group(0)[:200],
        })

    return citations
```

---

## SOP: Citoid Auto-Citation (REST API)

The [Citoid](https://www.mediawiki.org/wiki/Citoid) service, deployed on all WMF wikis,
automatically fetches citation metadata from a URL, DOI, ISBN, PMID, PMCID, or QID.
It powers VisualEditor's auto-cite feature and is accessible via the REST API.

### API Endpoint

```
GET https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/{url|doi|isbn|pmid}
GET https://en.wikipedia.org/api/rest_v1/data/citation/zotero/{url|doi|isbn|pmid}
```

- `/mediawiki` format returns data structured for wiki citation templates
- `/zotero` format returns raw Zotero JSON (more structured, better for automation)

### Fetch Citation Metadata from a URL

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/https://example.com/article"

resp = requests.get(url, headers=headers)
citations = resp.json()  # Returns array of citation objects

if citations:
    c = citations[0]  # Best match
    print(f"Type: {c.get('itemType')}")       # webpage, journalArticle, book, etc.
    print(f"Title: {c.get('title')}")
    print(f"Authors: {c.get('author', [])}")   # List of [last, first] pairs
    print(f"Date: {c.get('date')}")
    print(f"Publisher: {c.get('publisher')}")
    print(f"URL: {c.get('url')}")
```

### Fetch from a DOI

```python
resp = requests.get(
    "https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/10.7554/eLife.32259",
    headers=headers,
)
citations = resp.json()
c = citations[0]
# Returns: itemType=journalArticle, title, volume, publicationTitle,
#          date, author, DOI, ISSN, url, accessDate
```

### Converting Citoid Data to a Citation Template

```python
def citoid_to_template(citation: dict) -> str:
    """Convert a Citoid citation object to a CS1 template string."""
    item_type = citation.get("itemType", "webpage")
    url = citation.get("url", "")
    title = citation.get("title", "")
    date = citation.get("date", "")
    access_date = citation.get("accessDate", "")

    # Map Citoid item types to CS1 templates
    type_map = {
        "journalArticle": "cite journal",
        "book": "cite book",
        "bookSection": "cite book",
        "newspaperArticle": "cite news",
        "magazineArticle": "cite magazine",
        "webpage": "cite web",
        "report": "cite report",
        "thesis": "cite thesis",
        "conferencePaper": "cite conference",
        "patent": "cite patent",
        "film": "cite AV media",
        "podcast": "cite podcast",
        "interview": "cite interview",
        "map": "cite map",
    }
    template = type_map.get(item_type, "cite web")

    parts = [f"{{{{{template}}}"]

    if url:
        parts.append(f" |url={url}")
    if title:
        parts.append(f" |title={title}")
    if date:
        parts.append(f" |date={date}")
    if access_date:
        parts.append(f" |access-date={access_date}")

    # Authors
    authors = citation.get("author", [])
    for i, (last, first) in enumerate(authors, 1):
        if i == 1:
            parts.append(f" |last={last} |first={first}")
        else:
            parts.append(f" |last{i}={last} |first{i}={first}")

    # Type-specific fields
    if template == "cite journal":
        journal = citation.get("publicationTitle") or citation.get("journalTitle", "")
        if journal:
            parts.append(f" |journal={journal}")
        volume = citation.get("volume", "")
        if volume:
            parts.append(f" |volume={volume}")
        issue = citation.get("issue", "")
        if issue:
            parts.append(f" |issue={issue}")
        pages = citation.get("pages", "")
        if pages:
            parts.append(f" |pages={pages}")
        doi = citation.get("DOI", "")
        if doi:
            parts.append(f" |doi={doi}")

    if template == "cite news":
        newspaper = citation.get("publicationTitle", "")
        if newspaper:
            parts.append(f" |newspaper={newspaper}")

    if template == "cite book":
        publisher = citation.get("publisher", "")
        if publisher:
            parts.append(f" |publisher={publisher}")
        isbn = citation.get("ISBN", [""])[0]
        if isbn:
            parts.append(f" |isbn={isbn}")

    # Publisher field (for cite web when available)
    publisher = citation.get("publisher", "")
    if publisher and template == "cite web":
        parts.append(f" |publisher={publisher}")
    elif publisher and template not in ("cite book", "cite news"):
        parts.append(f" |publisher={publisher}")

    parts.append("}}")
    return "\n".join(parts)


# Usage:
citation = citoid_to_template(c)
print(citation)
```

### CLI with Citoid

```bash
# Fetch citation metadata for a URL and output as wiki template
curl -s 'https://en.wikipedia.org/api/rest_v1/data/citation/mediawiki/https://example.com' \
  -H 'User-Agent: MyBot/1.0 ContentGapResearch'
```

---

## SOP: Generating Citation Templates Programmatically

When you have source metadata (from a DOI API, ISBN lookup, or user input),
you can generate the wikitext citation template:

```python
def generate_cite_web(url: str, title: str, website: str, access_date: str,
                      last: str = "", first: str = "", archive_url: str = "",
                      archive_date: str = "", url_status: str = "live") -> str:
    """Generate a {{cite web}} template string."""
    parts = ["{{cite web"]
    parts.append(f" |url={url}")
    if last and first:
        parts.append(f" |last={last} |first={first}")
    parts.append(f" |title={title}")
    parts.append(f" |website={website}")
    parts.append(f" |access-date={access_date}")
    if archive_url and archive_date:
        parts.append(f" |archive-url={archive_url}")
        parts.append(f" |archive-date={archive_date}")
        parts.append(f" |url-status={url_status}")
    parts.append("}}")
    return "\n".join(parts)


def generate_cite_book(title: str, author: str, year: str,
                       publisher: str, isbn: str = "",
                       pages: str = "") -> str:
    """Generate a {{cite book}} template string."""
    parts = ["{{cite book"]
    parts.append(f" |title={title}")
    parts.append(f" |author={author}")
    parts.append(f" |year={year}")
    parts.append(f" |publisher={publisher}")
    if isbn:
        parts.append(f" |isbn={isbn}")
    if pages:
        parts.append(f" |pages={pages}")
    parts.append("}}")
    return "\n".join(parts)


def generate_cite_journal(title: str, author: str, journal: str,
                          volume: str, pages: str, doi: str = "",
                          year: str = "") -> str:
    """Generate a {{cite journal}} template string."""
    parts = ["{{cite journal"]
    parts.append(f" |title={title}")
    parts.append(f" |author={author}")
    parts.append(f" |journal={journal}")
    if year:
        parts.append(f" |year={year}")
    parts.append(f" |volume={volume}")
    parts.append(f" |pages={pages}")
    if doi:
        parts.append(f" |doi={doi}")
    parts.append("}}")
    return "\n".join(parts)
```

---

## Guardrails

### ❌ Never fabricate a citation
Every `<ref>` must point to a real, verifiable source. If you lack a source,
use `{{citation needed}}` instead. **No exceptions.**

### ❌ Never guess a URL
Do not construct URLs from assumed patterns (e.g., `https://nytimes.com/...`).
If you cannot verify a URL exists, do not include it.

### ❌ Never strip existing archive data
If a citation already has `archive-url` and `archive-date`, preserve them.
Adding a new archive is fine; removing one is not.

### ❌ Don't confuse `work`, `publisher`, `website`, and `journal`
These are not interchangeable. Using the wrong field can break automated
metadata extraction:
- `website` → For `{{cite web}}` — the site name (e.g., `BBC News`)
- `newspaper` → For `{{cite news}}` — the publication name
- `journal` → For `{{cite journal}}` — the academic journal name
- `publisher` → For `{{cite book}}` — the publishing house

### ⚠️ Respect Wayback Machine rate limits
The `/save` endpoint is resource-intensive. Limit to 1–2 save requests
per minute. Use the `/available` endpoint (read-only) freely.

### ⚠️ Don't archive every URL
Not every URL needs an archive. Prioritize:
1. URLs from news sites that remove articles behind paywalls
2. Government pages that may disappear after administration changes
3. Academic preprints that may move to final published versions
4. Personal websites and blogs (most ephemeral)

### ⚠️ Verify archives actually work
The Wayback Machine may return a "captured" status for a page that is
mostly empty (JavaScript errors, redirect loops). Spot-check the archive
URL in a browser before relying on it.

---

## Tooling

### 🔧 CLI Scripts

| Script | Purpose | Usage Example |
|--------|---------|---------------|
| [`scripts/expand-bare-url.sh`](./scripts/expand-bare-url.sh) | Expand a bare URL into a cite web template | `./expand-bare-url.sh https://example.com/article` |
| [`scripts/archive-check.sh`](./scripts/archive-check.sh) | Check if a URL is archived on the Wayback Machine | `./archive-check.sh https://example.com/article` |
| [`scripts/citoid-expand.sh`](./scripts/citoid-expand.sh) | Auto-generate a full citation template from URL/DOI/ISBN using Citoid | `./citoid-expand.sh 10.7554/eLife.32259` |
| [`scripts/check-dead-links.sh`](./scripts/check-dead-links.sh) | Extract URLs from a Wikipedia page and check each one | `./check-dead-links.sh Albert_Einstein` |
| [`scripts/citation-inspector.sh`](./scripts/citation-inspector.sh) | Show a summary of all citations on a page | `./citation-inspector.sh Albert_Einstein` |

### 🐍 Python Assets

| Script | Purpose | Usage Example |
|--------|---------|---------------|
| [`assets/wayback_inspector.py`](./assets/wayback_inspector.py) | Check Wayback Machine for URL archives, save new ones | `python3 wayback_inspector.py https://example.com` |
| [`assets/citoid_fetcher.py`](./assets/citoid_fetcher.py) | Auto-generate citations from URL/DOI/ISBN/PMID via the Citoid API | `python3 citoid_fetcher.py 10.7554/eLife.32259` |
| [`assets/dead_link_scanner.py`](./assets/dead_link_scanner.py) | Scan a Wikipedia page for dead links and suggest archives | `python3 dead_link_scanner.py Albert_Einstein` |
| [`assets/citation_linter.py`](./assets/citation_linter.py) | Parse and validate all citation templates in a page | `python3 citation_linter.py Albert_Einstein` |
| [`assets/citation_generator.py`](./assets/citation_generator.py) | Interactive CLI to generate citation templates | `python3 citation_generator.py` |

### 📚 Reference Docs

| Document | Contents |
|----------|----------|
| [`references/cs1-parameters.md`](./references/cs1-parameters.md) | Complete parameter reference for all CS1/CS2 templates |
| [`references/maintenance-templates.md`](./references/maintenance-templates.md) | Full catalog of citation-related maintenance templates with usage guidance |
| [`references/tools-decision-guide.md`](./references/tools-decision-guide.md) | When to use each tool — flowchart, pipelines, strengths/weaknesses of all 10+ methods |
| [`references/fetch-contexts.md`](./references/fetch-contexts.md) | Where metadata fetching happens (your machine vs WMF servers vs Toolforge vs IA) and how it affects success rates |
