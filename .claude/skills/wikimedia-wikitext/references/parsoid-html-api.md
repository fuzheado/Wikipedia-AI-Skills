# Parsoid HTML REST API Reference

Parsoid is natively embedded in MediaWiki as a core subsystem (the standalone JavaScript version is obsolete). It converts wikitext to clean HTML5/RDFa on demand.

## Endpoint

```
GET https://{project}/w/rest.php/v1/page/{title}/html
```

### Example

```
GET https://en.wikipedia.org/w/rest.php/v1/page/Python_(programming_language)/html
```

## Parameters

| Parameter | Location | Description |
|-----------|----------|-------------|
| `title` | Path | Page title with underscores (e.g., `Albert_Einstein`) |
| `Accept` | Header | Content type negotiation |

### Content Negotiation

| Accept Header Value | Response |
|---------------------|----------|
| `text/html; charset=utf-8; profile="https://www.mediawiki.org/wiki/Specs/HTML/2.1.0"` | **Recommended** — Parsoid HTML5 with RDFa annotations |
| `text/html` | Plain HTML |
| `application/json` | JSON representation of the page (includes HTML in `body` field) |

```bash
# Fetch with proper Accept header
curl -H "Accept: text/html; charset=utf-8; profile=\"https://www.mediawiki.org/wiki/Specs/HTML/2.1.0\"" \
     -H "User-Agent: MyBot/1.0 (user@example.com)" \
     "https://en.wikipedia.org/w/rest.php/v1/page/Python_(programming_language)/html"
```

## Caching (ETag / If-None-Match)

The API supports HTTP caching:

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com)"}
url = "https://en.wikipedia.org/w/rest.php/v1/page/Python_(programming_language)/html"

# First request — get the ETag
resp = requests.get(url, headers=headers)
etag = resp.headers.get("ETag")  # Store this

# Subsequent requests — conditional
resp = requests.get(url, headers={**headers, "If-None-Match": etag})
if resp.status_code == 304:
    print("Page hasn't changed — use cached version")
elif resp.status_code == 200:
    print("Page has been updated — use new response")
```

## Links in Parsoid HTML

Parsoid HTML uses RDFa annotations and `rel` attributes:

| Link type | HTML pattern |
|-----------|-------------|
| Internal wikilinks | `<a rel="mw:WikiLink" href="/wiki/Python_(programming_language)" title="Python (programming language)">Python</a>` |
| External links | `<a rel="mw:ExtLink" href="https://example.com">example</a>` |
| Category links | `<link rel="mw:PageProp/Category" href="/wiki/Category:Programming_languages">` |
| File links | `<a rel="mw:MediaLink" href="//upload.wikimedia.org/..." data-mw="...">` |
| Template-generated | `<span typeof="mw:Transclusion">...</span>` |

### Extracting Links with BeautifulSoup

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")

# Internal links
internal = [a["href"] for a in soup.select('a[rel="mw:WikiLink"]')]

# External links
external = [a["href"] for a in soup.select('a[rel="mw:ExtLink"]')]

# All links
all_links = [a["href"] for a in soup.find_all("a", href=True)]
```

## Section Structure

Sections in Parsoid HTML use standard HTML headings with `mw:Heading` wrapper divs:

```html
<div class="mw-heading mw-heading2">
  <h2 id="Early_life">Early life</h2>
</div>
```

### Extracting Sections

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")
sections = {}

for heading_div in soup.find_all("div", class_=lambda c: c and "mw-heading" in c):
    h_tag = heading_div.find(["h1", "h2", "h3", "h4", "h5", "h6"])
    section_title = h_tag.get_text(strip=True) if h_tag else "unknown"
    # Content follows until the next mw-heading
    content = []
    for sibling in heading_div.find_next_siblings():
        if sibling.get("class") and any("mw-heading" in (c or "") for c in sibling.get("class", [])):
            break
        content.append(str(sibling))
    sections[section_title] = "\n".join(content)
```

## Table Extraction

Wikitext tables are rendered as standard HTML `<table>` elements. Parsoid preserves most table semantics, including rowspan, colspan, and scope attributes.

```python
import pandas as pd

# pandas.read_html handles Parsoid HTML tables natively
tables = pd.read_html(html)

for i, df in enumerate(tables):
    print(f"Table {i}: {df.shape}")
    df.to_csv(f"table_{i}.csv", index=False)
```

## Infobox Extraction

Infoboxes render as `<table>` elements with class `infobox`:

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, "html.parser")
infobox = soup.find("table", class_="infobox")

if infobox:
    rows = infobox.find_all("tr")
    for row in rows:
        header = row.find("th")
        data = row.find("td")
        if header and data:
            print(f"{header.get_text(strip=True)}: {data.get_text(strip=True)}")
```

## Retrieving Specific Revisions

```
GET https://en.wikipedia.org/w/rest.php/v1/page/{title}/html/{revision_id}
```

```bash
curl -H "User-Agent: MyBot/1.0" \
     "https://en.wikipedia.org/w/rest.php/v1/page/Python_(programming_language)/html/123456789"
```

## Error Responses

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success — HTML body follows |
| 304 | Not modified (used with If-None-Match) |
| 404 | Page does not exist |
| 400 | Bad request (e.g., invalid title) |
| 429 | Rate limited — respect Retry-After header |

## Limitations

- The `/html` endpoint is **read-only**. To edit pages, use the Action API with wikitext.
- Very large pages (>5MB HTML) may be slow to fetch and parse.
- Parsoid HTML format may change across MediaWiki versions. Use the versioned `profile` in the `Accept` header and pin to a specific spec version.
