---
name: wikidata-vector-search
description: Query Wikidata by meaning, concept, or natural-language description — not just by exact label match. Uses semantic embeddings to find items (QIDs) and properties (PIDs) via vector similarity, keyword search, and Reciprocal Rank Fusion. Covers fuzzy semantic search, concept matching, similarity lookups, cross-lingual queries, and "find like this" when you do not know the exact QID or label
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access, wikidata]
skill_discovery_hints:
  - keywords: ["vector search", "semantic search", "embedding", "similarity score", "find QID", "fuzzy match"]
  - keywords: ["wd-vectordb", "concept search", "meaning search", "RRF", "cross-lingual search"]
last_verified: 2026-06-10
---

> ⚠️ **User-Agent required:** All calls to the Vector Database API require a descriptive `User-Agent` header. Requests without one are blocked with HTTP 403. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.

> ⚠️ **Alpha-quality service:** The Vector Database is in early testing (v0.2.1). Results may be incomplete or inaccurate. Queries are sent to JinaAI for embedding and logged for up to 90 days. The `instanceof` filter is non-functional in the current release.

The **Wikidata Vector Database** ([wd-vectordb.wmcloud.org](https://wd-vectordb.wmcloud.org/)), part of the [Wikidata Embedding Project](https://www.wikidata.org/wiki/Wikidata:Embedding_Project) led by Wikimedia Deutschland, stores semantic embeddings of every Wikidata entity. It enables **context-aware search** — finding items by *what they mean* rather than by exact string matching.

**When to reach for this instead of SPARQL:**

| You want to... | Use this | Use SPARQL if... |
|---|---|---|
| Find items "related to maritime exploration in the 1600s" | **Vector search** — understands concept, not just keywords | You need exact structured filters like `?item wdt:P31 wd:Q5` |
| Discover the QID for something when you don't know the label | **Vector search** — fuzzy match by description | You know the exact English label |
| Compare how "similar" two entities are semantically | **Similarity score** — vector dot product | You need graph distance (shortest path between items) |
| Search across languages without specifying which one | **Vector search** with `lang=all` | You need results in one specific language only |
| Get every human born in 1900 with a Nobel Prize | ✗ Vector search can't do this | **SPARQL** — exact filters, joins, aggregation |

The Vector Database **complements** SPARQL: use vector search for discovery and fuzzy matching, then use SPARQL or the Wikibase REST API for structured follow-up. See the **[wikidata](../wikidata/SKILL.md)** skill for SPARQL and structured queries.

---

## How It Works

Every Wikidata item (QID) and property (PID) is pre-computed into a high-dimensional vector embedding using JinaAI's multilingual model (100+ languages, 8192 token limit). When you submit a query:

1. **Your query text** is embedded into the same vector space
2. Two searches run in parallel:
   - **Vector Search** — dot-product similarity against all entity vectors (captures meaning)
   - **Keyword Search** — BM25-style text match over labels and aliases (captures exact terms)
3. **Reciprocal Rank Fusion (RRF)** merges both ranked lists: `rrf_score = 1 / (rank + 60)`. Results found by both methods get a boost.
4. **Optional reranker** — a cross-encoder model re-scores the top results if `rerank=true`

### Language Support

| Category | Languages | Behavior |
|---|---|---|
| **Dedicated vectors** | `ar`, `de`, `en`, `fr` | Search within that language's vectors only |
| **Other languages** | 140+ (ace, af, am, arz, ast, az, ... `zu`) | Query is machine-translated to English, then searched across all vectors |
| **`all`** | All languages | Search the entire vector database regardless of language |

Set `lang=all` (the default) for the broadest results. Set a specific `lang` (e.g. `lang=de`) when you need results from a particular language's embedding space.

---

## Endpoints

All endpoints are `GET` requests to `https://wd-vectordb.wmcloud.org`.

### 1. Search Items — `GET /item/query/`

Find Wikidata items (QIDs) by semantic meaning.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | **required** | Free-text description, label, or QID. Examples: `"Douglas Adams"`, `"Q42"`, `"author of Hitchhiker's Guide to the Galaxy"`, `"marine biologist who wrote about conservation"` |
| `lang` | string | `"all"` | Language code (`en`, `de`, `ar`, `fr`, `all`). Use `all` to search everything; use a specific code to constrain vector space. The utility script and sitelink filter also accept full project codes like `enwiki`, `frwikisource`, `commonswiki` — see the script section below. |
| `K` | integer | `50` | Number of results (minimum 1) |
| `instanceof` | string | — | Comma-separated QIDs to filter by class (⚠️ currently non-functional) |
| `rerank` | boolean | `false` | Apply cross-encoder reranker for improved relevance (slower) |
| `return_vectors` | boolean | `false` | Include raw embedding vectors in the response |

**Response:** Array of:

```json
{
  "QID": "Q42",
  "similarity_score": 0.8758,
  "rrf_score": 0.0392,
  "source": "Vector Search, Keyword Search"
}
```

The `source` field tells you whether the item was found by vector similarity, keyword match, or both.

### 2. Search Properties — `GET /property/query/`

Find Wikidata properties (PIDs) by semantic meaning. Same parameters as item search, plus:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `exclude_external_ids` | boolean | `false` | Filter out external-identifier-type properties (cleaner results for data properties) |

**Response:** Same shape as item search but with `PID` instead of `QID`.

### 3. Similarity Score — `GET /similarity-score/`

Compare a free-text query against a specific list of Wikidata entities. Useful for disambiguation or ranking candidates.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | string | **required** | Free-text to compare against |
| `qid` | string | **required** | Comma-separated QIDs/PIDs to score (e.g., `"Q42,Q2,Q36153"`) |
| `lang` | string | `"all"` | Language code |
| `return_vectors` | boolean | `false` | Include raw vectors |

**Response:** Array sorted by similarity descending:

```json
[
  { "QID": "Q2",   "similarity_score": 0.5423 },
  { "QID": "Q36153", "similarity_score": 0.5135 },
  { "QID": "Q42",  "similarity_score": 0.5103 }
]
```

---

## Worked Examples

### Example 1: Finding a QID for an entity when you don't know the label

You have a description but no exact label. For example, "the author who wrote about time travel and black holes and was married to a scientist."

```bash
curl -sL -H "User-Agent: MyBot/1.0 (me@example.com) WikidataSearch" \
  "https://wd-vectordb.wmcloud.org/item/query/?query=author+who+wrote+about+time+travel+and+black+holes+married+to+scientist&lang=en&K=3" | \
  python3 -m json.tool
```

**Result** (top 3):
```json
[
  { "QID": "Q24255708",  "similarity_score": 0.81, "source": "Vector Search" },
  { "QID": "Q3540992",  "similarity_score": 0.79, "source": "Vector Search" },
  { "QID": "Q4659809",  "similarity_score": 0.78, "source": "Vector Search" }
]
```

Then resolve the QIDs to labels via the Wikidata REST API:

```bash
curl -sL -H "User-Agent: ..." \
  "https://www.wikidata.org/wiki/Special:EntityData/Q970555.json" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print(d['entities']['Q970555']['labels']['en']['value'])"
# → "Jane Hawking"  (married to Stephen Hawking, wrote about his life)
```

The intended target (Stephen Hawking's wife or perhaps his daughter) is surfaced even though the query text doesn't match any existing label exactly.

### Example 2: Finding a property by description

You remember there's a property for "date of birth" but can't remember the PID.

```bash
curl -sL -H "User-Agent: MyBot/1.0 (me@example.com) WikidataSearch" \
  "https://wd-vectordb.wmcloud.org/property/query/?query=date+of+birth&lang=en&K=5" | \
  python3 -m json.tool
```

**Result** (top 3):
```json
[
  { "PID": "P569",     "similarity_score": 0.80, "source": "Vector Search" },
  { "PID": "P19",      "similarity_score": 0.72, "source": "Keyword Search" },
  { "PID": "P3150",    "similarity_score": 0.77, "source": "Vector Search" }
]
```

`P569` is indeed **date of birth** — top result.

### Example 3: Disambiguation — which QID matches this entity?

You have a set of candidate QIDs and need to determine which one a piece of text refers to. Use the similarity-score endpoint:

```bash
curl -sL -H "User-Agent: MyBot/1.0 (me@example.com) WikidataSearch" \
  "https://wd-vectordb.wmcloud.org/similarity-score/?query=mathematics&qid=Q42,Q2,Q36153&lang=en" | \
  python3 -m json.tool
```

**Result:**
```json
[
  { "QID": "Q2",      "similarity_score": 0.542 },
  { "QID": "Q36153",  "similarity_score": 0.514 },
  { "QID": "Q42",     "similarity_score": 0.510 }
]
```

`Q2` (Earth) is scored highest against the query "mathematics" — correct, since `Q36153` is "Leonhard Euler" (a mathematician, but a specific person) and `Q42` is "Douglas Adams" (a writer). The entity about the broader mathematical concept would be `Q395` (mathematics), which is included here as a negative example.

### Example 4: Cross-lingual search

Search for "science fiction novel" in a language without dedicated vectors:

```bash
curl -sL -H "User-Agent: MyBot/1.0 (me@example.com) WikidataSearch" \
  "https://wd-vectordb.wmcloud.org/item/query/?query=ciencia+ficci%C3%B3n+novela&lang=es&K=3" | \
  python3 -m json.tool
```

The query is translated to English internally, then searched against the full database. Results include science fiction novels from English Wikidata entities.

---

## SOP: When to Use Vector Search vs SPARQL vs the Wikibase REST API

The Vector Database fills a specific niche: **semantic discovery when you don't know the exact identifier**. Use this decision tree:

```
Need to find Wikidata entities?
│
├─ You know the exact label or QID → Use Wikidata REST API
│   https://www.wikidata.org/wiki/Special:EntityData/{QID}.json
│
├─ You know the exact structure (class, property, value) → Use SPARQL
│   See the [wikidata](../wikidata/SKILL.md) skill
│
├─ You have a free-text description and want the closest entities → Use Vector Search
│   /item/query/?query=...
│
├─ You have candidate QIDs and want to rank them → Use Similarity Score
│   /similarity-score/?query=...&qid=Q1,Q2,Q3
│
└─ You want properties by description → Use Property Search
    /property/query/?query=...
```

### Chaining with other skills

The Vector Database **only returns QIDs/PIDs and scores**. To turn those into usable Wikipedia data, chain with:

1. **Wikidata REST API** (from the [`wikidata`](../wikidata/SKILL.md) skill) to get labels, descriptions, and statements for each QID
2. **Wikibase Action API** to search or edit
3. **SPARQL** for structured filtering of a result set

Example chain — get the label and description for every top result:

```bash
#!/bin/bash
QUERY="deep sea exploration vehicle"
curl -sL -H "User-Agent: MyBot/1.0 (me@example.com) WikidataSearch" \
  "https://wd-vectordb.wmcloud.org/item/query/?query=$(echo $QUERY | sed 's/ /+/g')&lang=en&K=5" | \
  python3 -c "
import json, sys, urllib.request

results = json.load(sys.stdin)
for r in results:
    qid = r['QID']
    url = f'https://www.wikidata.org/wiki/Special:EntityData/{qid}.json'
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'MyBot/1.0 (me@example.com) WikidataSearch'})) as resp:
        data = json.load(resp)
        entity = data['entities'][qid]
        label = entity.get('labels', {}).get('en', {}).get('value', '?')
        desc = entity.get('descriptions', {}).get('en', {}).get('value', '')
        print(f\"{r['QID']:>8}  {r['similarity_score']:.4f}  {label:40s}  {desc[:80]}\")
"
```

---

## SOP: Handling Edge Cases and Pitfalls

### 1. The `instanceof` filter is non-functional

The parameter is accepted but **silently ignored in the current alpha**. Results are not filtered by class even when you specify `instanceof=Q5`. Do not rely on this parameter. If you need class-based filtering, use SPARQL instead:

```sparql
SELECT ?item WHERE {
  ?item wdt:P31 wd:Q5 .       # instance of human
  ?item rdfs:label "Einstein"@en .
}
```

### 2. Only QIDs/PIDs are returned — no labels

Every Vector Database response contains identifiers and scores only. You **must** make a follow-up call to the Wikidata REST API to get human-readable labels, descriptions, or statements. See the chaining example above.

### 3. The top result may be the *concept itself*, not an instance

Querying "programming language" returns **Q9143** (the concept "programming language") before Q380 (the language "C++") or Q261 (the language "Python"). If you want instances of a class instead of the class itself, this is not the right tool — use SPARQL.

### 4. Semantic search is not question answering

The query "Who wrote Hitchhiker's Guide to the Galaxy?" returns Q3107329 (the novel itself) rather than Q42 (its author). The vector database finds entities *similar to the query text*, it does not understand the grammatical structure of questions. To answer questions, chain with the Wikibase API or SPARQL after getting candidate QIDs.

### 5. User-Agent is mandatory

The server rejects requests without a descriptive User-Agent header. Use the format from [`wikimedia-api-access`](../wikimedia-api-access/SKILL.md).

### 6. Rate limiting and caching

While the Vector Database doesn't document explicit rate limits, the web UI starts embedded queries immediately. For programmatic use, if you're making many queries:
- Cache results to avoid re-querying for the same search terms
- Batch multiple queries if possible
- Respect the service being in alpha — report issues rather than hammering the endpoint

---

## Standalone Utility Script

The skill ships a query script that searches the Vector Database, **automatically resolves every QID/PID to its label and description** (batching all lookups into one API call), and by default **filters to only main-namespace Wikipedia articles** (no categories, templates, portals, etc.).

### Basic usage

```bash
# Search items (default: top 5, English labels, enwiki articles only)
./scripts/wd-vector-search.sh "marine biologist who wrote about conservation"

# Search items — top 10
./scripts/wd-vector-search.sh "quantum physicist 20th century" --K 10

# Show ALL entities (categories, journals, templates, etc.)
./scripts/wd-vector-search.sh "marine biologist" --no-filter

# Search properties
./scripts/wd-vector-search.sh "date of birth" --property

# Similarity score against specific entities
./scripts/wd-vector-search.sh "mathematics" --similarity Q42,Q2,Q36153

# Raw JSON output (QIDs/PIDs only, for chaining with other tools)
./scripts/wd-vector-search.sh "Einstein" --json | jq '.[].QID'

# With reranker
./scripts/wd-vector-search.sh "deep sea exploration" --rerank
```

### Language and project selection (`--lang`)

The `--lang` flag controls **three things at once**: the Vector DB query language, the sitelink filter (what Wikimedia project to check), and the label/description language. It accepts:

| `--lang` value | Vector DB | Sitelink filter | Labels | Returns... |
|---|---|---|---|---|
| `en` (default) | English vectors | `enwiki` (mainspace) | English | Wikipedia articles |
| `fr` | French vectors | `frwiki` (mainspace) | French | French Wikipedia articles |
| `de` | German vectors | `dewiki` (mainspace) | German | German Wikipedia articles |
| `enwiki` | English vectors | `enwiki` (mainspace) | English | Same as `en` (explicit) |
| `frwikisource` | French vectors | `frwikisource` (any) | French | French Wikisource pages |
| `commonswiki` | English vectors | `commonswiki` (any) | English | **Commons category names** (not media files) |
| `enwiktionary` | English vectors | `enwiktionary` (any) | English | Wiktionary entries |
| `metawiki` | English vectors | `metawiki` (any) | English | Meta-Wiki pages |

> **commonswiki note:** The Vector Database indexes Wikidata items, not Commons media files directly. When filtered by `commonswiki`, the results are Wikidata items that *have* a Commons category page — so you get **category names** (e.g. "Category:Marine biologists"). To find actual media files on Commons, use the [wikimedia-commons](../wikimedia-commons/SKILL.md) skill instead.

```bash
# French Wikipedia — searches French vectors, filters by frwiki, shows French labels
./scripts/wd-vector-search.sh "écrivain français" --lang fr

# French Wikisource — filters to items with a frwikisource page
./scripts/wd-vector-search.sh "Victor Hugo" --lang frwikisource

# Commons categories — filters to items with a Commons category
./scripts/wd-vector-search.sh "marine biologist" --lang commonswiki

# German Wikipedia
./scripts/wd-vector-search.sh "programmiersprache" --lang de
```

### Example output

```
🔍 Searching Wikidata Vector Database...
   Query: marine biologist
   Mode: item
   Language: en (site filter: enwiki, labels: en)
   Results: 5
   Filter: enwiki pages only (use --no-filter for ALL entities)

   (removed 4 entities without a enwiki mainspace page)
      Item   Score  Label                                               Description
  ----------------------------------------------------------------------------------------------------
🔤 Q3640160  0.8340  marine biologist                                    scientist specializing in marine biology
```

Each row shows an icon: 🧠 (vector similarity), 🔤 (keyword match), or 🧠🔤 (both).

### How the sitelink filter works

1. After the Vector DB returns its top K results, the script calls the **Wikidata Action API** with one batch request per phase:
   - **Phase 2 (sitelink check):** `action=wbgetentities&props=sitelinks&sitefilter={SITE_CODE}` — checks all K QIDs in one call
   - **Phase 3 (labels):** `action=wbgetentities&props=labels|descriptions&languages={lang}|en` — fetches labels and descriptions in one call

2. **For language Wikipedias** (`enwiki`, `frwiki`, `dewiki`, etc.): only **main-namespace articles** pass (pages whose sitelink title doesn't start with `Category:`, `Template:`, `Portal:`, `File:`, `Module:`, etc.)

3. **For other projects** (`commonswiki`, `frwikisource`, `enwiktionary`, `metawiki`, etc.): any page with a sitelink is included — categories, templates, and all namespaces are valid results

4. Entities without a qualifying sitelink are silently dropped; a summary line shows how many were removed

If all top K results are non-article entities (common for queries like "marine biologist" where the Vector DB returns categories first), the script warns you and suggests `--no-filter` or a higher `--K`.

### Why `--no-filter`?

The Vector Database indexes **every** Wikidata entity — categories, journals, templates, disambiguation pages, Commons categories, and pure Wikidata items without any Wikipedia page. If you're looking for specific scholarly entities, obscure journals, or Wikimedia project pages, use `--no-filter` to see everything the database returns.## Known Limitations (Alpha v0.2.1)

| Limitation | Impact | Workaround |
|---|---|---|
| `instanceof` filter ignored | Can't restrict results to a class | Use SPARQL for class-filtered queries |
| Only 4 languages with dedicated vectors (ar, de, en, fr) | Other languages fall back to English translation | Use `lang=all` for best cross-lingual results |
| No freshness guarantee | May lag behind live Wikidata | Check entity revision IDs via REST API |
| Top result can be the concept item, not an instance | "programming language" → Q9143, not Python or C++ | Use SPARQL for instance-level queries |
| No structured data in response | QIDs only, no labels/statements | Chain with Wikidata REST API |
| Queries logged to JinaAI for 90 days | Privacy consideration for sensitive queries | Use `lang` parameter to minimize data exposure |

---

## Relationship to Other Skills

- **[wikidata](../wikidata/SKILL.md)** — SPARQL, Wikibase REST and Action APIs. Vector search is a *complement*: use vector for discovery, then SPARQL for precision.
- **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** — Required User-Agent format and rate-limiting patterns for all Wikimedia API calls.
- **[wikipedia-en-article-audit](../wikipedia-en-article-audit/SKILL.md)** — Phase 2 verification could be accelerated by using vector search to surface candidate QIDs for claim cross-referencing.
- **[wikimedia-commons](../wikimedia-commons/SKILL.md)** — No direct overlap; Commons has its own media similarity search via the Multimedia API.

---

## References

- **Web UI:** [wd-vectordb.wmcloud.org](https://wd-vectordb.wmcloud.org/) — try queries interactively
- **API Docs (OpenAPI/Swagger):** [wd-vectordb.wmcloud.org/docs](https://wd-vectordb.wmcloud.org/docs)
- **Project Page:** [Wikidata:Vector Database](https://www.wikidata.org/wiki/Wikidata:Vector_Database)
- **Embedding Project:** [Wikidata:Embedding Project](https://www.wikidata.org/wiki/Wikidata:Embedding_Project)
- **Feedback Survey:** [wikimedia.sslsurvey.de/Wikidata-Vector-DB-Feedback-Alpha-release](https://wikimedia.sslsurvey.de/Wikidata-Vector-DB-Feedback-Alpha-release)
