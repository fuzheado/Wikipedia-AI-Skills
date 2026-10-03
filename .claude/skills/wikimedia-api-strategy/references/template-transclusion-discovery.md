# Template Transclusion Discovery

## When to Use

When you need to find **all pages currently involved in a structured discussion process** (RFCs, AfDs, RMs, merges, etc.), do NOT scrape the manually-curated listing pages. They lag, miss entries, and have inconsistent formatting. Instead, query the **template transclusion** — the bot-tracked source of truth.

## The Pattern

Every structured process on Wikipedia uses a template that gets placed on the page when the process starts and removed when it ends. Query `list=embeddedin` to find all pages currently transcluding that template:

```
action=query&list=embeddedin&eititle=Template:Rfc&einamespace=1|5&eilimit=500
```

### Key parameters

| Parameter | Purpose |
|-----------|---------|
| `eititle` | The template name, with `Template:` prefix (e.g. `Template:Rfc`, `Template:Afd`) |
| `einamespace` | Restrict to specific namespaces (pipe-separated). For discussions: `1` = Talk, `5` = Wikipedia talk |
| `eilimit` | Max 500 per call. Use `eicontinue` for pagination |

### Common templates to query

| Process | Template | Typical namespaces |
|---------|----------|-------------------|
| Requests for Comment | `Template:Rfc` | 1, 4, 5 |
| Articles for Deletion | `Template:Afd` | 4 (Wikipedia:) |
| Requested Moves | `Template:Requested move` | 1 (Talk:) |
| Merge proposals | `Template:Merge` | 1 (Talk:) |

## RFC-Specific Example

Finding all active English Wikipedia RFCs:

```python
params = {
    "action": "query",
    "list": "embeddedin",
    "eititle": "Template:Rfc",
    "einamespace": "1|5",  # Talk + Wikipedia talk
    "eilimit": "500",
    "format": "json",
}
# Paginate with eicontinue from the 'continue' block
```

This returned 52 unique RFC pages (August 2026) — compared to ~45 from the category listing pages, and some RFCs appeared in both but the template list was more complete.

## Multi-Title Content Fetching: Pitfalls

When you need the **content** of the pages found via `embeddedin`, batch-fetch them efficiently. These pitfalls were discovered during RFC analysis:

### 1. `rvlimit` breaks multi-title queries

```bash
# ❌ BROKEN — returns 400 error
curl "...&titles=Page1|Page2|Page3&rvlimit=1&prop=revisions&rvprop=content"

# ✅ CORRECT — omit rvlimit, default gets 1 revision
curl "...&titles=Page1|Page2|Page3&prop=revisions&rvprop=content"
```

The API rejects `rvlimit` when multiple pages are supplied. Error: *"rvlimit may only be used on a single page."*

### 2. Pipe characters in shell

Use `--data-urlencode` with `-G` to properly encode pipe-separated titles:

```bash
curl -s -G \
  --data-urlencode "action=query" \
  --data-urlencode "titles=Talk:Page A|Talk:Page B|Talk:Page C" \
  --data-urlencode "prop=revisions" \
  --data-urlencode "rvprop=content" \
  --data-urlencode "rvslots=main" \
  --data-urlencode "format=json" \
  "https://en.wikipedia.org/w/api.php"
```

### 3. Stdout caps on large responses

Talk pages can be 50K–250K chars. When fetching 10+ pages at once, the total response can exceed terminal-based tool output caps (~50KB). The response is silently truncated — JSON parsing fails on incomplete data with no clear indicator.

**Solution:** Fetch pages individually or in batches of 2–3. For talk page analysis, one-at-a-time with a small delay (0.3s) is reliable and stays well under rate limits.

## Signature Extraction from Talk Page Wikitext

When counting participants in a discussion, extract user signatures from wikitext sections:

```python
import re

BOTS = {'SineBot', 'Legobot', 'ClueBot III', ...}

def extract_users(wikitext):
    users = set()
    # Standard: [[User:Name|Name]] ([[User talk:Name|talk]])
    for m in re.finditer(r'\[\[User:([^\]|/#<>]+?)(?:\|[^\]]*?)?\]\]', wikitext):
        user = m.group(1).strip()
        if user not in BOTS and '/' not in user:
            users.add(user)
    # Unsigned template fallback: Special:Contributions/Name
    for m in re.finditer(r'Special:Contributions?/([^\]|#<>]+?)\]\]', wikitext):
        user = m.group(1).strip()
        if user not in BOTS:
            users.add(user)
    return users
```

To isolate the RFC section, split the page by `==` section headings and keep sections containing `{{rfc}}` or `{{Rfc}}`. This avoids counting signatures from unrelated discussions on the same page.
