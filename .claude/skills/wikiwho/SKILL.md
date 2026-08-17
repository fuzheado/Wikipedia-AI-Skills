---
name: wikiwho
description: Token-level authorship attribution for Wikipedia articles via the WikiWho API — who wrote, removed, or reinserted each word, with content-persistence and editor attribution analysis
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["who wrote this", "authorship attribution", "wikiwho", "token provenance", "content persistence", "which editor wrote"]
  - keywords: ["blame tool", "Who Wrote That", "whowrotethat", "who authored", "contribution analysis"]
  - keywords: ["edit persistence", "token history", "reverted content", "reintroduced text", "revert detection"]
last_verified: 2026-08-17
---

> ⚠️ **User-Agent required:** All requests below require a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

WikiWho is a service providing **token-level authorship attribution** for Wikipedia articles: for every word (token) it tells you which revision and editor originally wrote it, plus the token's complete add → delete → reintroduce history. It was developed at KIT and GESIS (WWW 2014 paper, 95% accuracy), moved to Wikimedia Cloud Services infrastructure in August 2021 ([Phab T288840](https://phabricator.wikimedia.org/T288840)), and is now maintained by WMF Community Tech and the Wiki Education Foundation. It powers the official "Who Wrote That?" browser extension and the WhoColor userscript.

**When to use WikiWho:** when the question is about *content provenance* — "who wrote this sentence?", "what share of the article did editor X write?", "which of my edits have survived?", "which text keeps getting reverted?" — answers that plain revision history (who edited when) cannot give, because they require matching text across revisions at the token level.

## **API Basics**

- **Base URL:** `https://wikiwho-api.wmcloud.org/<lang>/api/v1.0.0-beta/` where `<lang>` is a Wikipedia language code (`en`, `de`, `fr`, `zh`, …). ~72 languages supported — see the [current list](https://www.mediawiki.org/wiki/WikiWho#Currently_supported_wikis). The canonical host on MediaWiki.org is now `wikiwho.wmcloud.org` (same path); both hosts serve the API.
- **Docs:** a Swagger 2.0 spec is served at the API root itself (e.g. `…/en/api/v1.0.0-beta/`).
- **Auth:** none (read-only). **Data license:** CC-BY-SA 4.0; the underlying revision data remains under Wikimedia's reuse terms.
- **Version:** `v1.0.0-beta` — stable in practice but perpetually beta; **rate limits are undocumented** (be polite).
- **Python wrapper caveat:** the `wikiwho-wrapper` package on PyPI is stale (last release 2019) — use the raw API.

**Quick smoke test:**

```bash
curl -s "https://wikiwho-api.wmcloud.org/en/api/v1.0.0-beta/rev_ids/Wikilambda/?editor=true&timestamp=true" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
# {"article_title":"Wikilambda","page_id":64444578,"success":true,"message":null,
#  "revisions":[{"id":965686479,"editor":"13006032","timestamp":"2020-07-02T20:15:49Z"}, ...]}
```

## **Key Endpoints**

| Endpoint | Returns |
|---|---|
| `/rev_ids/{article_title}/` (`?editor=true&timestamp=true`) | All revision IDs of an article as processed by WikiWho, with editor and timestamp |
| `/latest_rev_content/{article_title}/` | Token-level content of the most recent revision |
| `/rev_content/{article_title}/{rev_id}/` | Token-level content of a specific revision |
| `/range_rev_content/{article_title}/{start_rev_id}/{end_rev_id}/` | Tokens of revisions in the range (ordered by **timestamp**, not rev-id numeric order) |
| `/all_content/{article_title}/` (`?threshold=N`) | Every token that has ever existed in the article, with its full change history |
| `/…/page_id/{page_id}/` variants | Same endpoints by page ID instead of article title |

Plus **WhoColor** (HTML color-markup for inline authorship display) and **Edit Persistence** services on the same base URL.

**Query flags** (`rev_content`, `latest_rev_content`, `all_content`): `o_rev_id=true`, `editor=true`, `token_id=true`, `in=true`, `out=true`. Request only what you need — responses are large.

## **Token Metadata Semantics** ⚠️

Each token object looks like:

```json
{"str": "redirect", "token_id": 1, "o_rev_id": 965686479, "editor": "13006032", "in": [], "out": []}
```

| Field | Meaning |
|---|---|
| `str` | The token text. Words, punctuation, and wiki markup (`[[`, `]]`, `|`, …) are **separate tokens** |
| `token_id` | WikiWho's internal ID, **unique per article**, assigned increasing from 0 |
| `o_rev_id` | **Origin revision** — the revision where this token was first added |
| `editor` | **User ID** (integer). `0` = all unregistered accounts; anonymous IPs appear as `"0|<ip>"`. ⚠️ This is a user *ID*, not a username — resolve it via the Action API |
| `out` | Revisions where the token was **deleted**, in time order (empty = never deleted) |
| `in` | Revisions where the token was **reinserted** after a deletion (each `in` follows an `out`) |

## **SOP: Resolve Editor IDs to Usernames**

```python
import requests

def resolve_users(user_ids, wiki_domain='en.wikipedia.org'):
    """Resolve WikiWho editor IDs to usernames via the Action API (batches of 50)."""
    ids = [u for u in user_ids if str(u).isdigit() and int(u) > 0]  # skip 0 and "0|<ip>"
    names = {}
    for i in range(0, len(ids), 50):
        r = requests.get(
            f"https://{wiki_domain}/w/api.php",
            params={'action': 'query', 'list': 'users',
                    'ususerids': '|'.join(map(str, ids[i:i+50])), 'format': 'json'},
            headers={'User-Agent': 'MyBot/1.0 (me@example.com) ProjectName'}, timeout=30)
        for u in r.json()['query']['users']:
            names[str(u['userid'])] = u.get('name', '(deleted)')
    return names
```

## **SOP: "Who Wrote This?" — Authorship Breakdown of an Article**

```python
import requests, collections

def authorship(article, lang='en', wiki_domain='en.wikipedia.org'):
    base = f"https://wikiwho-api.wmcloud.org/{lang}/api/v1.0.0-beta"
    r = requests.get(f"{base}/latest_rev_content/{article}/", params={'editor': 'true'},
                     headers={'User-Agent': 'MyBot/1.0 (me@example.com) ProjectName'}, timeout=60)
    revs = r.json()['revisions']
    tokens = revs[0][list(revs[0].keys())[0]]['tokens']
    counts = collections.Counter(t.get('editor', '?') for t in tokens)
    names = resolve_users(list(counts), wiki_domain)
    total = len(tokens)
    for editor, n in counts.most_common():
        print(f"{names.get(editor, editor):20s} {n:5d} tokens ({100*n/total:.1f}%)")
```

Notes:
- Tokens include wiki markup — for "human-readable" shares, filter out `str` values that are pure markup (`[[`, `]]`, `|`, `#`, etc.) or weight by character length instead of raw token count.
- For a historical snapshot, call `rev_content/{article}/{rev_id}/` with the same flags.

## **SOP: Content Persistence — Which Edits Survive?**

Question: "Of what editor X added to this article, how much is still there today?"

1. `latest_rev_content` → tokens currently present, each carrying its `o_rev_id`.
2. `rev_ids` → map revision IDs to the editors who made them.
3. Attribute each surviving token to the editor of its `o_rev_id`.
4. Baseline: `rev_content` at a past revision (or `all_content` with `threshold`) to see what X contributed historically, then compare survival.

## **SOP: Find Reverted or Disputed Text (in/out)**

Tokens with long `in`/`out` chains have been deleted and reinserted repeatedly — a proxy for conflict:

```python
def contentious_tokens(article, lang='en', min_events=2):
    base = f"https://wikiwho-api.wmcloud.org/{lang}/api/v1.0.0-beta"
    r = requests.get(f"{base}/all_content/{article}/",
                     params={'editor': 'true', 'o_rev_id': 'true', 'in': 'true', 'out': 'true'},
                     headers={'User-Agent': 'MyBot/1.0 (me@example.com) ProjectName'}, timeout=120)
    for t in r.json()['all_tokens']:
        if len(t.get('in', [])) + len(t.get('out', [])) >= min_events:
            yield t
```

## **Constraint & Guardrails**

1. **Per-article, not bulk.** WikiWho answers article-by-article; there is no cross-article or query-by-username endpoint. Loop with a small delay for multi-article analyses.
2. **Token reconstruction ≠ verbatim text.** Tokens split wiki markup and punctuation into separate units; joining `str` with spaces approximates the text but is not byte-identical to the wikitext. Use `prop=revisions` (see [wikipedia-edit-history](../wikipedia-edit-history/SKILL.md)) when you need exact revision text.
3. **`editor` is a user ID.** Never present IDs as usernames; resolve with `list=users&ususerids=` (anonymous = `0` or `0|<ip>`). Note user IDs can be reused after account renames — cross-check names for precise identity work.
4. **Data freshness.** The service is built by processing complete revision histories, so "latest" content can lag live Wikipedia slightly. For time-critical research, compare the returned latest `rev_id` against the live `prop=revisions` for the article.
5. **Be polite.** Rate limits are undocumented; reuse a session, batch user-ID lookups, and add small delays between articles.
6. **Errors:** `400` bad request, `408` timeout (retry), `503` service unavailable (back off). Stable on Wikimedia Cloud since 2021, but research-grade — the API code repo (`wikimedia/wikiwho_api`) is archived, so treat behavior as frozen.

## **Example Use Cases**

* "Who wrote the current lead section of this article, and what share did each editor contribute?"
* "Which editor's contributions to this article have survived the longest?"
* "Find the most reverted sentences on a controversial article" (tokens with long `out`/`in` chains).
* "What fraction of this article was written by anonymous editors?"
* AI-era research: "Measure human-authored vs. bot/reverted content over time" — combine `all_content` with the editor IDs of known bots (see [wikipedia-edit-history](../wikipedia-edit-history/SKILL.md) for bot identification).

## **Tooling**

This skill includes helper scripts and reference docs:

### 🔧 Authorship Breakdown (`scripts/who_wrote.py`)

Fetch the token-level authorship distribution of an article and resolve editor IDs to usernames.

```bash
./scripts/who_wrote.py "Albert Einstein"              # current revision, enwiki
./scripts/who_wrote.py "Albert Einstein" 123456789    # specific revision
./scripts/who_wrote.py "Albert Einstein" --lang de    # German Wikipedia
./scripts/who_wrote.py "Albert Einstein" --top 10 --csv out.csv
```

### 📚 Endpoint Reference (`references/endpoints.md`)

Complete endpoint list with parameters, response schemas, error codes, and worked examples.

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent header and API request patterns for all calls |
| **[wikipedia-edit-history](../wikipedia-edit-history/SKILL.md)** | Revision-level history (who edited when) — complementary to token-level attribution |
| **[wikimedia-diffs](../wikimedia-diffs/SKILL.md)** | Per-revision diff content — pairs with WikiWho's token provenance for "what changed" analysis |
| **[wikimedia-api-strategy](../wikimedia-api-strategy/SKILL.md)** | Deciding between APIs when WikiWho is overkill (e.g. simple revision counts) |
| **[wikimedia-pageviews](../wikimedia-pageviews/SKILL.md)** | Popularity context for authorship analyses |
