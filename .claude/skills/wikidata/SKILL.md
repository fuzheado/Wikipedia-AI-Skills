---
name: wikidata
description: Understand and query Wikidata — the free, collaborative, multilingual knowledge graph that underpins Wikipedia's inter-language links, Commons structured data, and semantic facts across all Wikimedia projects. Covers SPARQL, the Wikibase REST/Action APIs, RDF data dumps, and semantic web concepts
license: MIT
compatibility: opencode
---

> ⚠️ **User-Agent required:** All curl and code examples in this skill access Wikimedia APIs. Requests without a descriptive `User-Agent` header will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns. Before writing any code, load that skill for the required User-Agent boilerplate.

Wikidata (https://www.wikidata.org) is a **free, collaborative, multilingual knowledge graph** that serves as the central structured data repository for the Wikimedia ecosystem. It is operated by the Wikimedia Foundation and is openly editable by anyone.

## **What Wikidata Is**

Wikidata is a **semantic database** — it stores facts (called "statements") about the world in a machine-readable, language-independent way. Unlike a traditional encyclopedia article written in one language, a Wikidata item is a single node that accumulates knowledge from contributors across all languages.

### **The Inter-Language Linking Backbone**

Every Wikipedia article across every language edition is linked to a Wikidata **item** (identified by a Q-number like `Q937` for "Albert Einstein"). This is what powers the language switcher in the left sidebar of every Wikipedia article — when you click "Deutsch" or "Français" on an English article, the mapping comes from Wikidata, not from cross-wiki bot scripts.

> 💡 **How it works:** The English Wikipedia article `Albert Einstein` and the German `Albert Einstein` and the French `Albert Einstein` are all linked to the same Wikidata item `Q937`. When an editor adds a new language link to any one of them, it automatically propagates to all the others — no manual syncing needed.

### **Structured, Language-Independent Knowledge**

Because Wikidata stores facts as typed property-value pairs (e.g., "Einstein" has "occupation" → "physicist") instead of free-form text, the data is:

- **Language-independent** — A statement like `Q937` + `P106` (occupation) + `Q169470` (physicist) doesn't need translation. Each label can be rendered in any language automatically.
- **Machine-readable** — Software can query, filter, aggregate, and reason over the data programmatically.
- **Cross-project** — The same item is used by Wikipedia, Commons, Wiktionary, Wikisource, and any external tool that consumes the data.
- **Globally editable** — A contributor in Japan and a contributor in Brazil can both add facts about the same item in their own language, and both contributions enrich the same shared node.

## **Q Numbers and P Numbers**

Wikidata has two fundamental namespaces:

### **Q Numbers — Items** (the "things")

Every item — a person, place, concept, object, event, etc. — gets a unique Q identifier. The Q number is stable and does not change, even if the label does.

| Item | Q ID | Example Labels |
|------|------|---------------|
| Albert Einstein | `Q937` | Albert Einstein (en), アルベルト・アインシュタイン (ja), Альберт Эйнштейн (ru) |
| Earth | `Q2` | Earth (en), 地球 (ja), Erde (de) |
| Human | `Q5` | Human (en), Mensch (de), 人間 (ja) |
| French Revolution | `Q6534` | French Revolution (en), Révolution française (fr), フランス革命 (ja) |
| Python (programming language) | `Q28865` | Python (en), Python (de), Python (fr) |

### **P Numbers — Properties** (the "attributes")

Properties describe relationships between items or attach values to them. Each property also has a unique, stable P identifier.

| Property | P ID | Used For | Example Value |
|----------|------|----------|--------------|
| instance of | `P31` | What class of thing this is | Einstein → `P31` → human (`Q5`) |
| subclass of | `P279` | Hierarchical parent class | mammal → `P279` → animal |
| occupation | `P106` | What a person does | Einstein → `P106` → physicist (`Q169470`) |
| date of birth | `P569` | When someone was born | Einstein → `P569` → 14 March 1879 |
| country | `P17` | Which sovereign state | France → `P17` → French Republic |
| depicts | `P180` | What a Commons file shows | (used on Commons files) |
| image | `P18` | Representative image | (links to a Commons file name) |
| author | `P50` | Creator of a work | (used on books, articles, films) |

> 💡 **You can explore any Q or P by visiting its page:** `https://www.wikidata.org/wiki/Q937` or `https://www.wikidata.org/wiki/P31`. The page shows labels, descriptions, aliases, statements, and sitelinks (connections to Wikipedia articles).

---

## **How Wikidata Works Under the Hood**

Wikidata is built on the **Wikibase** software, which is a **MediaWiki extension**. This means:

- Every item is a **wiki page** — it has a history, a talk page, and can be edited via the normal MediaWiki interface.
- The same **Action API** (`https://www.wikidata.org/w/api.php`) used by Wikipedia works here too — just with Wikibase-specific modules (`wbgetentities`, `wbsearchentities`, `wbgetclaims`, etc.).
- The same **User-Agent policy** and rate-limiting rules apply (see the [wikimedia-api-access](../wikimedia-api-access/SKILL.md) skill).
- Because it's MediaWiki under the hood, you can also use ordinary wiki modules like `action=query&prop=revisions` to inspect edit history.

### **Wikibase-Specific Action API Modules**

| Module | Purpose |
|--------|---------|
| `wbgetentities` | Fetch items, properties, and their statements by Q/P ID |
| `wbsearchentities` | Search for items and properties by label |
| `wbgetclaims` | Fetch statements (claims) for a specific item |
| `wbeditentity` | Create or edit items (requires authentication) |
| `wbformatvalue` | Format a value into a human-readable string |

**Example — fetch an item via the Action API:**
```
https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q937&props=labels|descriptions|claims&format=json
```

---

## **SPARQL Query Service**

Wikidata's most powerful query interface is the **SPARQL endpoint** at `https://query.wikidata.org`. It allows you to ask complex, relational questions across the entire knowledge graph.

### **Web Interface**

Open https://query.wikidata.org in a browser — a full-featured query editor with syntax highlighting, auto-complete for Q/P IDs, and result visualization (table, map, timeline, graph). You can also share queries via a short URL.

### **Programmatic Access**

```sparql
# Example: Find all museums in Paris with their coordinates
SELECT ?museum ?museumLabel ?coords WHERE {
  ?museum wdt:P31 wd:Q33506;       # instance of museum
          wdt:P131 wd:Q90;          # located in Paris
          wdt:P625 ?coords.         # coordinate location
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

Access via the REST API:
```
GET https://query.wikidata.org/sparql?format=json&query=SELECT...
```

### **Rate Limits & Usage Guidelines**

The WDQS SPARQL endpoint has **stricter limits than the general Wikimedia APIs** because a SPARQL query is more resource-intensive than a typical REST call.

| Limit | Value | Notes |
|-------|-------|-------|
| **Query timeout** | 60 seconds | Hard deadline per query — both web UI and API |
| **Processing time** | 60s per 60s window | Per client (user-agent + IP pair) |
| **Error rate** | 30 errors per minute | Burst allowed to 60; errors are queries that fail, not empty results |
| **429 response** | `Retry-After` header | Stop sending immediately and wait; ignoring 429 leads to a ban |
| **SLO** | 95% availability | Lower than other WMF services — plan for intermittent failures |
| **Query size** | URL length limit | Use POST with `query=` body prefix for large queries |

**Required headers:**
- `User-Agent` — descriptive string with contact info (strictly enforced; see [wikimedia-api-access](../wikimedia-api-access/SKILL.md))
- `Accept: application/sparql-results+json` — for JSON results
- `Accept-Encoding: gzip, deflate` — required per robot policy

**429 handling pattern:**
```python
import time
import requests

resp = requests.get(
    "https://query.wikidata.org/sparql",
    params={"format": "json", "query": query},
    headers={"User-Agent": UA, "Accept": "application/sparql-results+json"},
    timeout=30,
)

if resp.status_code == 429:
    retry_after = int(resp.headers.get("Retry-After", 60))
    print(f"Rate limited — waiting {retry_after}s", file=sys.stderr)
    time.sleep(retry_after)
    # Retry the request
elif resp.status_code != 200:
    resp.raise_for_status()
```

**⚠️ `SERVICE wikibase:label` performance warning:** The label service can make queries dramatically slower. When optimizing an expensive query, disable the label service first, get the query efficient, then re-enable it. See the [official query optimization guide](https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/query_optimization) for more patterns.

**Use the `wikimedia-api-access` skill** for the required User-Agent header, general rate limiting, and retry patterns.

### **Why SPARQL vs. `haswbstatement:` (Commons)**

| Aspect | SPARQL (Wikidata) | `haswbstatement:` (Commons) |
|--------|-------------------|---------------------------|
| Scope | Entire Wikidata (items, properties, qualifiers, references) | Commons files only |
| Complexity | Full graph queries, joins, aggregations, filters | Simple equality matches only |
| Speed | Slower (seconds) — queries against a triplestore | Fast (sub-second) — search index backed |
| Query types | Numerical comparisons, date ranges, transitive properties, complex joins | Exact value matching on a single property |

---

## **The Fundamental Properties: P31 and P279**

Wikidata has **no rigid taxonomy**. The community decides how items are classified through discussion and consensus. However, two properties form the backbone of most classification:

### **P31 (instance of)**

Indicates that an item is a **specific example** of a class. This is the most commonly used property on Wikidata.

| Item | P31 Value | Meaning |
|------|-----------|---------|
| Eiffel Tower (`Q243`) | tourist attraction (`Q570116`) | The Eiffel Tower is *an instance of* a tourist attraction |
| Mars (`Q111`) | planet (`Q634`) | Mars is *an instance of* a planet |
| Mona Lisa (`Q12418`) | painting (`Q3305213`) | Mona Lisa is *an instance of* a painting |

### **P279 (subclass of)**

Indicates that a class is a **subset** of another, more general class. This creates a hierarchy.

| Item | P279 Value | Meaning |
|------|-----------|---------|
| mammal (`Q7377`) | animal (`Q729`) | Mammals are *a subclass of* animals |
| planet (`Q634`) | astronomical object (`Q6999`) | Planets are *a subclass of* astronomical objects |
| painting (`Q3305213`) | work of art (`Q4502142`) | Paintings are *a subclass of* works of art |

**Distinction:** `P31` is for *individual things* (this specific thing is an instance of a class). `P279` is for *classes themselves* (one class is a subclass of another).

```
            astronomical object (Q6999)
                   │
             subclass_of (P279)
                   │
            planet (Q634)
                   │
             instance_of (P31)
                   │
           Mars (Q111)
```

> 💡 **Why this matters:** When you query Wikidata for "all astronomical objects" using the `wdt:P279*` (transitive subclass) syntax, the query engine automatically follows the `P279` chain — so Mars shows up even though it's directly tagged as a planet. This makes queries more powerful without needing to know the full hierarchy in advance.

---

## **SOP: Batch Entity Classification from Wikipedia Titles**

A common cross-API workflow is: take a list of Wikipedia titles (e.g., from the Pageviews API), resolve each to its Wikidata ID, then classify the type of entity (person, place, film, etc.) using P31 (instance of). This requires chaining the Action API and the Wikibase `wbgetentities` module efficiently.

⚠️ **User-Agent required:** All HTTP requests below need a descriptive `User-Agent` header. Load the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the required boilerplate, rate limiting, and retry patterns.

### Step 1: Resolve Wikipedia Titles to Wikidata IDs

Use the Action API's `prop=pageprops` with `ppprop=wikibase_item` to batch-resolve up to 50 titles per call:

```python
params = {
    'action': 'query',
    'titles': '|'.join(titles),       # accepts underscores or spaces
    'prop': 'pageprops',
    'ppprop': 'wikibase_item',
}
```

⚠️ **Critical: Title normalization.** The Action API returns titles **with spaces** (e.g., `Donald Trump`), not underscores. When using titles from the Pageviews API (which uses underscores like `Donald_Trump`) as dictionary keys, normalize: `t.replace('_', ' ')`. See the **[Title Format Guide](../wikimedia-api-access/references/endpoints.md#11-title-format-guide-cross-api-gotcha)** in the API access reference for a full cross-API table.

```python
def resolve_wikidata_ids(session, titles):
    """Batch-resolve Wikipedia titles to Wikidata Q IDs."""
    results = []
    for i in range(0, len(titles), 50):
        batch = titles[i:i+50]
        params = {
            'action': 'query',
            'titles': '|'.join(batch),
            'prop': 'pageprops',
            'ppprop': 'wikibase_item',
            'format': 'json',
        }
        data = session.get('https://en.wikipedia.org/w/api.php', params=params).json()

        # Build lookup dict — keys are space-normalized (Action API output format)
        id_by_title = {}
        for pid, info in data['query']['pages'].items():
            if 'missing' not in info and 'pageprops' in info:
                wid = info['pageprops'].get('wikibase_item')
                if wid:
                    id_by_title[info['title']] = wid

        for title in batch:
            wid = id_by_title.get(title.replace('_', ' '))  # normalize!
            if wid:
                results.append((title, wid))

        time.sleep(0.5)  # rate limiting
    return results
```

### Step 2: Batch-Check Entity Type via wbgetentities

Once you have Wikidata IDs, use the Wikibase `wbgetentities` module to fetch P31 (instance of) claims for up to 50 IDs per call:

```python
params = {
    'action': 'wbgetentities',
    'ids': '|'.join(entity_ids),       # up to 50 IDs per call
    'props': 'claims',
    'format': 'json',
}
```

⚠️ Do **not** use `Special:EntityData/{id}.json` for batch lookups — that endpoint only accepts a single ID at a time.

### Step 3: Check P31 (instance of) Values

Each entity's P31 claims contain the Q ID of the class it belongs to. Common entity types:

| Q ID | Label | Use Case |
|------|-------|----------|
| Q5 | human | Biographies (people) |
| Q11424 | film | Movie articles |
| Q515 | city | Place/city articles |
| Q4022 | river | Geographic features |
| Q12136 | mountain | Geographic features |
| Q16521 | taxon | Species articles |
| Q7889 | video game | Game articles |
| Q571 | book | Book articles |
| Q101352 | family name | Surname articles |
| Q4830453 | business | Company articles |
| Q43229 | organization | Organization articles |
| Q3918 | university | Educational institution articles |

```python
def is_human(entity):
    """Check if a Wikidata entity is instance of human (Q5)."""
    p31 = entity.get('claims', {}).get('P31', [])
    for c in p31:
        ds = c.get('mainsnak', {}).get('datavalue', {})
        if ds.get('value', {}).get('id') == 'Q5':
            return True
    return False


def classify_entities(session, entries):
    """Batch-classify Wikipedia titles by entity type.
    
    entries: list of (title, wikidata_id) tuples
    returns: dict mapping title -> set of class Q IDs
    """
    classification = {}
    for i in range(0, len(entries), 50):
        batch = entries[i:i+50]
        ids = [e[1] for e in batch]
        params = {
            'action': 'wbgetentities',
            'ids': '|'.join(ids),
            'props': 'claims',
            'format': 'json',
        }
        data = session.get('https://www.wikidata.org/w/api.php', params=params).json()

        for title, eid in batch:
            entity = data.get('entities', {}).get(eid, {})
            p31 = entity.get('claims', {}).get('P31', [])
            classes = set()
            for c in p31:
                ds = c.get('mainsnak', {}).get('datavalue', {})
                qid = ds.get('value', {}).get('id')
                if qid:
                    classes.add(qid)
            classification[title] = classes

        time.sleep(0.5)
    return classification
```

### Handling Subclass Hierarchies

Some entities are instances of subclasses rather than directly of a common type (e.g., `instance of actor` instead of `instance of human`). For thorough checks, traverse `P279` (subclass of) in SPARQL to find all ancestor classes:

```sparql
# Check if Q33999 (actor) is a subclass of Q5 (human) transitively
SELECT ?item ?itemLabel WHERE {
  wd:Q33999 wdt:P279* wd:Q5.  # Follow subclass chain up to Q5
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

For programmatic use, precompute a transitive closure for commonly-needed ancestors and cache the results.

### Typical Pipeline Pattern

The full cross-API pipeline:

```
Get list of titles → Batch-resolve Wikidata IDs → Batch-check P31 → Filter by type → Enrich
```

Each batch step uses the largest limit the API supports (50 for `prop=pageprops`, 50 for `wbgetentities`). Maintain a 0.3–0.5s delay between batches and respect `Retry-After` on 429 responses. See the **[cross-API pipeline example](../wikimedia-api-access/assets/cross_api_pipeline.py)** for a complete, runnable implementation.

---

## **Workflow Guidance**

### **When to use each access method**

| Task | Best Method | Example |
|------|-------------|---------|
| Look up a single item's label, description, or statements | Action API (`wbgetentities`) | `https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q937` |
| Search for an item by name | Action API (`wbsearchentities`) | `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=Einstein&language=en` |
| Complex relational queries across many items | SPARQL | "Find all French physicists born before 1900" |
| Check the edit history of an item | Action API (`prop=revisions`) | `https://www.wikidata.org/w/api.php?action=query&prop=revisions&titles=Q937` |
| Quick item lookup in a browser | Item page URL | `https://www.wikidata.org/wiki/Q937` |
| Explore and build SPARQL queries visually | Query Service web UI | `https://query.wikidata.org` |

### **When to reach for the API skill**

Any time you write code to interact with Wikidata — whether fetching items via the Action API or running SPARQL queries — load the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for:
- Mandatory User-Agent header format
- Rate-limiting and Retry-After handling
- 403 / 429 error troubleshooting
- The `requests.Session()` connection-reuse pattern

---

## **Tooling**

This skill includes helper scripts and reference docs:

### 🔧 Q-ID Lookup (`scripts/wikidata-lookup.sh`)

Look up a Wikidata item or property by Q/P ID — returns label, description, and basic statements.

```bash
./scripts/wikidata-lookup.sh Q937
./scripts/wikidata-lookup.sh P31
```

### 🔧 SPARQL Quick Query (`scripts/sparql-query.sh`)

Run a SPARQL query against the Wikidata Query Service and display results in the terminal.

```bash
./scripts/sparql-query.sh "SELECT ?item ?itemLabel WHERE { wd:Q937 wdt:P106 ?item. SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\". } }"
./scripts/sparql-query.sh --examples
```

### 📚 Wikidata API Reference (`references/wikidata-api.md`)

Deep reference for Wikidata-specific API endpoints:
- Wikibase Action API modules (wbgetentities, wbsearchentities, wbgetclaims, etc.)
- SPARQL query patterns with common examples (P31/P279 transitive queries, qualifiers, references)
- Response structure for entity data (labels, descriptions, aliases, claims, sitelinks)
- Common Q IDs and P IDs (reference card)

### 🐍 Wikidata Entity Fetcher (`assets/wikidata-entity-fetcher.py`)

A Python tool to fetch and display Wikidata item data — labels, descriptions, claims (with qualifiers), sitelinks, and more — using the Action and SPARQL APIs.
