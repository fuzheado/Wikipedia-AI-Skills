---
name: wikimedia-diffs
description: Fetch, compare, and interpret diffs between Wikipedia page revisions — wikitext changes, visual differences, and diff statistics via the Action API and REST API
license: MIT
compatibility: opencode
---

## SOP: Understanding Wikipedia Diffs

Wikipedia records every edit as a **revision** with a unique ID. A **diff** shows what changed between two revisions. There are two ways to get diffs:

| Approach | When to use | Endpoint |
|----------|-------------|----------|
| **Action API** | You need raw wikitext diff (markup changes) or diff metadata | `action=compare` |
| **REST API** | You need rendered HTML comparison (visual diff) | `/compare` |
| **Browser URL** | You want to view or share a diff in a web browser | `index.php?diff=...&oldid=...` |

### Sharing a Diff Link

To share a link to a diff between two specific revisions:

```
https://en.wikipedia.org/w/index.php?title=PAGE_TITLE&diff=NEW_REV_ID&oldid=OLD_REV_ID
```

For example:

```
https://en.wikipedia.org/w/index.php?title=Talk:Geothermal_energy&diff=1352498037&oldid=1323528943
```

This works for any Wikimedia project — just change the hostname and provide the page title and two revision IDs. No API key or User-Agent is needed since this is a standard web URL.

---

## SOP: Fetching Diffs via the Action API

The Action API's `compare` module returns an HTML table diff plus revision metadata.

### Basic Diff Between Two Revisions (Absolute IDs Required)

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com)"}
params = {
    "action": "compare",
    "fromrev": 123456789,   # Old revision ID
    "torev": 123456790,     # New revision ID
    "prop": "diff|diffsize|ids|title|size",
    "format": "json",
}
resp = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=headers)
data = resp.json()
```

### Two-Step: Latest Edit to a Page

Since the API requires absolute revision IDs, first fetch the latest two:

```python
import requests

s = requests.Session()
s.headers.update({"User-Agent": "MyBot/1.0 (user@example.com)"})
API = "https://en.wikipedia.org/w/api.php"

# Step 1: Get revision IDs
rv = s.get(API, params={
    "action": "query", "prop": "revisions",
    "titles": "Python (programming language)",
    "rvlimit": "2", "rvprop": "ids", "format": "json",
}).json()
page = list(rv["query"]["pages"].values())[0]
revs = page["revisions"]
from_rev, to_rev = revs[1]["revid"], revs[0]["revid"]

# Step 2: Compare
diff = s.get(API, params={
    "action": "compare",
    "fromrev": from_rev, "torev": to_rev,
    "prop": "diff|diffsize|ids|title|size", "format": "json",
}).json()
```

### Response Fields

```json
{
  "compare": {
    "fromtitle": "Python (programming language)",
    "fromrevid": 123456789,
    "fromsize": 24500,
    "torevid": 123456790,
    "tosize": 24620,
    "diffsize": 150,   ← total bytes changed (churn, not net)
    "*": "...HTML diff table..."
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `fromrevid` / `torevid` | int | Revision IDs |
| `fromsize` / `tosize` | int | Page sizes in bytes |
| `diffsize` | int | Total bytes changed (added + removed churn) |
| `*` | string | HTML table of the diff |

---

## SOP: Fetching Diffs via the REST API

The REST API provides a rendered HTML comparison that shows how the content *looks* different, not just the markup.

### Endpoint

```
GET https://en.wikipedia.org/w/rest.php/v1/revision/{from}/compare/{to}
```

### Example

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com)"}
url = "https://en.wikipedia.org/w/rest.php/v1/revision/123456789/compare/123456790"

resp = requests.get(url, headers=headers)
data = resp.json()
```

### Response Format

The response includes:
- **`from`** — source revision ID and page info
- **`to`** — target revision ID and page info
- **`diff`** — array of change objects with `type` (`add`, `remove`, `change`, `context`), `leftText` (HTML), and `rightText` (HTML)

The HTML in `leftText`/`rightText` is rendered — templates are expanded, images shown, etc. This is useful for **visual comparison**.

### Comparing by Slot

```python
# Compare a specific content slot (e.g., "main" for article body)
url = "https://en.wikipedia.org/w/rest.php/v1/revision/123456789/compare/123456790?slot=main"
```

---

## SOP: Interpreting Diff Results

### Detecting Edit Magnitude

```python
cmp = data["compare"]
diffsize = cmp.get("diffsize", 0)    # Total bytes changed
fromsize = cmp.get("fromsize", 0)
tosize = cmp.get("tosize", 0)
net = tosize - fromsize             # Net byte change

# Estimate additions and removals
if net >= 0:
    approx_added = net
    approx_removed = diffsize - net
else:
    approx_removed = -net
    approx_added = diffsize + net

# Red flags
if diffsize > 50000:
    print("⚠️ Large-scale change — review needed")
if net < -20000:
    print("⚠️ Significant net removal — possible blanking")
```

### Parsing the HTML Diff

The diff HTML (`"*"` field) is a table with standard CSS classes. You can extract meaningful statistics from it:

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(cmp["*"], "html.parser")

# Count insertions and deletions
insertions = len(soup.find_all("td", class_="diff-addedline"))
deletions = len(soup.find_all("td", class_="diff-deletedline"))
changed_spans = len(soup.find_all("span", class_="diffchange"))
context_lines = len(soup.find_all("td", class_="diff-context"))

print(f"{insertions} insertions, {deletions} deletions")
print(f"{changed_spans} inline changes across {context_lines} context lines")
```

### Extracting Changed Content

```python
soup = BeautifulSoup(cmp["*"], "html.parser")

# Get all added lines (new version)
for td in soup.find_all("td", class_="diff-addedline"):
    # The <div> inside contains the actual content
    div = td.find("div")
    if div:
        print(f"+ {div.get_text()}")

# Get all deleted lines (old version)
for td in soup.find_all("td", class_="diff-deletedline"):
    div = td.find("div")
    if div:
        print(f"- {div.get_text()}")

# Get inline changes (diffchange spans mark changed words)
for span in soup.find_all("span", class_="diffchange"):
    print(f"~ {span.get_text()}")
```

---

## SOP: Anti-Patterns to Avoid

| ❌ Anti-Pattern | Why | ✅ Correct |
|---|---|---|
| Using `fromrev=prev` or `torev=cur` (relative refs) | The API rejects non-integer revision IDs | Fetch absolute revision IDs first with `action=query&prop=revisions` |
| Expecting a structured `diff` array | The API returns an HTML table in `"*"`, not a structured array | Parse the HTML table with BeautifulSoup, or use the REST API for structured diffs |
| Using `diffsize` as net bytes changed | `diffsize` is total churn (additions + removals), not net | Calculate net from `fromsize` / `tosize` |
| Parsing diff HTML with regex | The table structure is well-formed HTML | Use BeautifulSoup with CSS class selectors |
| Fetching diff for every revision in a page history | Rate limited | Fetch diffs selectively or with delays between requests |

---

## Tooling

This skill includes helper scripts, reference docs, and templates:

### 🔧 Diff Fetcher (`scripts/fetch-diff.sh`)

Fetch a diff between two revisions or the latest change to a page.

```bash
# Diff between two known revision IDs
./scripts/fetch-diff.sh --from-rev 123456789 --to-rev 123456790

# Latest edit to a page
./scripts/fetch-diff.sh --page "Python (programming language)"

# Diff with statistics
./scripts/fetch-diff.sh --page "Albert Einstein" --stats

# Output as JSON
./scripts/fetch-diff.sh --page "Marie Curie" --json
```

### 🔧 Diff Stats (`scripts/diff-stats.sh`)

Analyze a diff and report statistics: lines/bytes added and removed, sections affected, templates changed, and potential issues (large deletions, blanking).

```bash
# Analyze a diff between two revisions
./scripts/diff-stats.sh --from-rev 123456789 --to-rev 123456790

# Analyze the latest edit to a page
./scripts/diff-stats.sh --page "Python (programming language)"
```

### 📚 Diff API Reference (`references/diff-api.md`)

Full reference for both the Action API `compare` module and the REST API `/compare` endpoint:
- Complete parameter list with `torelative` and slot options
- All action types (add, remove, change, move, context)
- Diff table format documentation
- Comparison of Action API vs REST API approaches
- Error response guide (invalid revisions, protected pages)
- Rate limiting considerations

### 🐍 Revision Comparator (`assets/compare-revisions.py`)

Python script for fetching and analyzing diffs:

```bash
# Fetch diff between two revisions
python3 assets/compare-revisions.py --from-rev 123456789 --to-rev 123456790

# Fetch latest diff for a page
python3 assets/compare-revisions.py --page "Python (programming language)"

# Show structured diff with stats
python3 assets/compare-revisions.py --page "Albert Einstein" --stats

# Output as formatted report
python3 assets/compare-revisions.py --page "Marie Curie" --report

# Compare across different projects
python3 assets/compare-revisions.py --page "Paris" --project fr.wikipedia
```
