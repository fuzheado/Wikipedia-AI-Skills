# Diff API Reference

Two APIs can return diffs between Wikipedia revisions: the **Action API** (HTML table diff + metadata) and the **REST API** (rendered HTML comparison).

---

## Action API: `action=compare`

### Endpoint

```
GET https://{project}/w/api.php
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `action` | yes | `compare` |
| `fromrev` | yes | Source revision ID (integer) |
| `torev` | yes | Target revision ID (integer) |
| `prop` | no | What to return: `diff`, `ids`, `title`, `size` |
| `slots` | no | Content slots to compare (e.g., `main`) |
| `format` | no | `json` (recommended) |

**Note:** The `torelative` feature (`prev`, `cur`, etc.) is **not available** in the current MediaWiki API. You must use absolute revision IDs. To compare the latest two revisions of a page, first fetch revision IDs via `action=query&prop=revisions&rvlimit=2` then pass them to `compare`.

### Response Format

```json
{
  "compare": {
    "fromid": 736,
    "fromrevid": 1355112534,
    "fromns": 0,
    "fromtitle": "Albert Einstein",
    "fromsize": 234579,
    "toid": 736,
    "torevid": 1355663707,
    "tons": 0,
    "totitle": "Albert Einstein",
    "tosize": 234583,
    "prev": 1355044810,
    "next": 1355884292,
    "diffsize": 13400,
    "*": "<tr>\n  <td class=\"diff-marker\"></td>\n  ... HTML table of changes ...\n</tr>"
  }
}
```

### Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `fromid` | int | Page ID (not revision ID!) of the source page |
| `fromrevid` | int | Source revision ID |
| `fromsize` | int | Size of the source revision in bytes |
| `toid` | int | Page ID of the target page |
| `torevid` | int | Target revision ID |
| `tosize` | int | Size of the target revision in bytes |
| `prev` | int | Previous revision ID (before `fromrevid`) |
| `next` | int | Next revision ID (after `torevid`) |
| `diffsize` | int | Total number of bytes changed (not net — this is add+remove churn) |
| `*` | string | HTML table of the diff, with `diff-marker`, `diff-deletedline`, `diff-addedline` classes |

### Diff HTML Classes

The diff HTML (`*` field) uses these CSS classes for styling:

| Class | Meaning |
|-------|---------|
| `diff-marker` | Cell with +/- marker |
| `diff-deletedline` | Old (removed) line content |
| `diff-addedline` | New (added) line content |
| `diff-context` | Unchanged line (shown for context) |
| `diffchange` | Inline highlight of changed text |
| `diff-lineno` | Line number header |
| `diff-side-deleted` | Left column (old) |
| `diff-side-added` | Right column (new) |

### Estimating Added/Removed Bytes

Since `diffsize` is total churn and you only have `fromsize`/`tosize`:

```python
net_change = tosize - fromsize
if net_change >= 0:
    added = net_change
    removed = diffsize - net_change
else:
    removed = -net_change
    added = diffsize + net_change
```

This is an approximation — exact line-level counts require parsing the HTML diff.

### Error Responses

| Error | Meaning |
|-------|---------|
| `nosuchrevid` | One or both revision IDs don't exist |
| `readapidenied` | Insufficient read permissions |

---

## REST API: `/compare`

### Endpoint

```
GET https://{project}/w/rest.php/v1/revision/{from}/compare/{to}
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `from` | Source revision ID (integer, required) |
| `to` | Target revision ID (integer, required) |
| `slot` | Content slot to compare (e.g., `main`) |

### Response

```json
{
  "from": {
    "id": 1355112534,
    "page": { "id": 736, "title": "Albert Einstein" }
  },
  "to": {
    "id": 1355663707,
    "page": { "id": 736, "title": "Albert Einstein" }
  },
  "diff": [
    {
      "type": "add",
      "leftText": null,
      "rightText": "<p>New paragraph HTML</p>"
    }
  ]
}
```

### Key Differences from Action API

| Aspect | Action API | REST API |
|--------|------------|----------|
| **Output** | HTML table string in `"*"` | Array of structured diff objects |
| **Content** | Raw wikitext shown in table | Rendered HTML fragments |
| **Templates** | Not expanded | Expanded in output |
| **Use case** | Quick metadata, bot analysis | Visual comparison, human review |
| **Relative revs** | Not supported | Not supported |

---

## Workflow: Compare Latest Two Revisions

Since neither API supports relative revision references, use this two-step workflow:

```python
import requests

s = requests.Session()
s.headers.update({"User-Agent": "MyBot/1.0 (user@example.com)"})
API = "https://en.wikipedia.org/w/api.php"

# Step 1: Get the two most recent revision IDs
rv = s.get(API, params={
    "action": "query", "prop": "revisions",
    "titles": "Albert Einstein", "rvlimit": "2",
    "rvprop": "ids", "format": "json",
}).json()
page = list(rv["query"]["pages"].values())[0]
revs = page["revisions"]
from_rev, to_rev = revs[1]["revid"], revs[0]["revid"]

# Step 2: Compare
diff = s.get(API, params={
    "action": "compare",
    "fromrev": from_rev, "torev": to_rev,
    "prop": "diff|ids|title|size", "format": "json",
}).json()
```
