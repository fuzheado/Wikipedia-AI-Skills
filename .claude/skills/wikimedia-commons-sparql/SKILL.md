---
name: wikimedia-commons-sparql
description: Query Wikimedia Commons structured data via SPARQL — MediaInfo entities (M IDs), the depicts/copyright/licensing graph, Schema.org media metadata, and federated queries with Wikidata. Covers both the official WCQS endpoint (OAuth-authenticated) and the QLever third-party endpoint (no auth required)
depends_on: [wikimedia-api-access]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["Commons SPARQL", "WCQS", "QLever", "Commons Query Service", "MediaInfo", "M ID", "M number", "structured data on Commons", "SDC"]
  - keywords: ["depicts", "P180", "schema:url", "schema:contentUrl", "image grid", "commons-query"]
  - keywords: ["federated query Commons", "Commons Wikidata federation", "cross-project SPARQL"]
  - keywords: ["file metadata", "copyright SPARQL", "license SPARQL", "media dimensions", "camera data"]
last_verified: 2026-06-12
---

> ⚠️ **User-Agent required:** All HTTP requests to Wikimedia endpoints need a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns. Requests without a proper User-Agent will be blocked with HTTP 403.
>
> 💡 **Relationship to other skills:**
> - This skill covers **Commons-specific SPARQL** — M IDs, Schema.org media predicates, and Commons property patterns. General SPARQL syntax (SELECT, FILTER, OPTIONAL, property paths), the WDQS label service (`SERVICE wikibase:label`), and WDQS rate limits are covered in the **[wikidata](../wikidata/SKILL.md)** skill.
> - For **adding, editing, and managing** Structured Data on Commons (not querying it), see the **[wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md)** skill — covers captions editing, `wbcreateclaim`, batch GLAM workflows, ISA Tool, OpenRefine, and constraint checking.
> - The **[wikimedia-commons](../wikimedia-commons/SKILL.md)** skill covers non-SPARQL Commons access: Action API search, file upload, EXIF metadata, `haswbstatement:` prefix, and category navigation.
> - The **[wikimedia-api-strategy](../wikimedia-api-strategy/SKILL.md)** skill helps decide *when* to use SPARQL vs. the Action API vs. other methods.

---

## What Is Commons Structured Data?

Every file on Wikimedia Commons can carry **Wikibase statements** — the same kind of structured, machine-readable annotations used by Wikidata. These statements describe:

- **What a file depicts** (P180 — "depicts" → a Wikidata item)
- **Who created it** (P170 — "creator")
- **When it was created** (P571 — "inception")
- **Copyright status and license** (P6216, P275)
- **Camera and capture metadata** (P4082 — "captured with")
- **Digital representation of** (P6243 — links a file to the Wikidata item it's a digital surrogate of)
- **And more** — any Wikidata property can, in principle, be used on Commons files.

This is called **Structured Data on Commons (SDC)**. The data is stored as **MediaInfo entities**, each identified by an **M ID** (e.g., `M37200540`), which is distinct from Wikidata's Q IDs.

> 💡 **Where to find an M ID:** On any Commons file page, look in the left sidebar for "Concept URI" — the link contains the M ID. Or use "Page information" — the Page ID prefixed with `M` is the M ID.

## Two Endpoints, One Dataset

There are two SPARQL endpoints you can use to query Commons structured data:

| Aspect | WCQS (Official) | QLever (Third-Party) |
|--------|-----------------|---------------------|
| **URL** | `https://commons-query.wikimedia.org/sparql` | `https://qlever.dev/api/wikimedia-commons` |
| **Web UI** | `https://commons-query.wikimedia.org/` | `https://qlever.dev/wikimedia-commons` |
| **Authentication** | OAuth — requires a Commons account and manual cookie extraction | **None** — open access |
| **Operated by** | Wikimedia Foundation (Search Platform team) | University of Freiburg (QLever project) |
| **Status** | Beta; usage <1 query/min; may be decommissioned (see [T376979](https://phabricator.wikimedia.org/T376979)) | Active; updated from the `mediainfo-streaming-updater.mutation.v2` stream |
| **Data source** | Weekly dumps from `dumps.wikimedia.org/other/wikibase/commonswiki/` | "Munged" version of the same dumps + streaming updates |
| **Federation with WDQS** | Supported | Supported |
| **Rate limits** | Per authenticated user (request-based) | Usual QLever rate limiting |

> ⚠️ **Practical advice:** For automated tools, scripts, and programmatic access, **use QLever** — it requires no authentication and returns results via a standard SPARQL GET/POST endpoint. The official WCQS endpoint exists but its OAuth requirement makes it impractical for most programmatic use. The [Commons SPARQL examples page](https://commons.wikimedia.org/wiki/Commons:SPARQL_query_service/queries/examples) itself directs users to QLever as "the way faster [alternative] which does not require login." It also contains dozens of runnable example queries you can adapt.

---

## The M ID / MediaInfo Data Model

The biggest difference from Wikidata SPARQL is that **subjects are M IDs** (MediaInfo entities), not Q IDs.

| Concept | Wikidata | Commons (MediaInfo) |
|---------|----------|-------------------|
| Entity ID prefix | **Q** (e.g., `Q42`) | **M** (e.g., `M37200540`) |
| Subject URI pattern | `http://www.wikidata.org/entity/Q42` | `http://commons.wikimedia.org/entity/M37200540` |
| What the entity represents | Abstract concepts, people, places, things | **Files** (images, audio, video, PDFs, 3D models) |
| Labels | Multilingual labels and descriptions | Multilingual **file captions** (`?file rdfs:label ?caption`) |
| File URL predicates | — | `schema:url`, `schema:contentUrl`, `schema:thumbnailUrl` |
| Media metadata predicates | — | `schema:width`, `schema:height`, `schema:encodingFormat` |

### Finding M IDs

**Method 1: By Commons file title.** Use the `wikibase:mwapi` SERVICE (see [Pattern 7: Media from a Specific Commons Category](#pattern-7-media-from-a-specific-commons-category) below) or construct the URI directly:

```sparql
BIND(URI(CONCAT("http://commons.wikimedia.org/entity/M", ?pageid)) AS ?file)
```

**Method 2: By known file path.** The `schema:url` predicate matches `Special:FilePath` URLs:

```sparql
?file schema:url <http://commons.wikimedia.org/wiki/Special:FilePath/Eiffel_Tower_from_below.jpg> .
```

**Method 3: From PetScan or Minefield.** PetScan can list Page IDs for all files in a Commons category; Minefield converts file titles to M IDs. See the [Commons SPARQL page](https://commons.wikimedia.org/wiki/Commons:SPARQL_query_service) for details.

---

## Quick Reference: What Do You Want to Do?

| Goal | Example Query Pattern | Endpoint |
|------|----------------------|----------|
| Find files depicting a Wikidata item | `?file wdt:P180 wd:Q42 .` | Both |
| Show images in a grid | `?file schema:url ?image .` + `#defaultView:ImageGrid` | Both |
| Find files by copyright status | `?file wdt:P6216 wd:Q50402863 .` (public domain) | Both |
| Find files by license | `?file wdt:P275 wd:Q50829104 .` (CC0) | Both |
| Get file dimensions | `?file schema:width ?w ; schema:height ?h .` | Both |
| Find files by camera model | `?file wdt:P4082 wd:Q649631 .` (Canon EOS 5D) | Both |
| Federated: file depicts + Wikidata label | `SERVICE <https://query.wikidata.org/sparql> { ... }` | Both |
| Files in a Commons category | `SERVICE wikibase:mwapi { ... wikibase:endpoint "commons.wikimedia.org" ... }` | Both |
| Count files by file type | `SELECT ?encoding (COUNT(*) AS ?total) { ?file schema:encodingFormat ?encoding . } GROUP BY ?encoding` | Both |
| Find files with point-of-view coordinates | `?file wdt:P1259 ?coords .` (Map view) | Both |

---

## Commons-Specific Properties Reference

These are the most commonly used properties for querying Commons structured data:

### 🔗 Core File Properties

| Property | Label | Type of Value | Example Use |
|----------|-------|---------------|-------------|
| `wdt:P180` | depicts | Wikidata Q item | `?file wdt:P180 wd:Q42 .` (files depicting Douglas Adams) |
| `wdt:P6243` | digital representation of | Wikidata Q item | `?file wdt:P6243 wd:Q179900 .` (files that are digital surrogates of Michelangelo's David) |
| `wdt:P170` | creator | Wikidata Q item or string | `?file wdt:P170 wd:Q5582 .` (files created by Van Gogh) |
| `wdt:P571` | inception | Date literal | `FILTER(YEAR(?date) > 2020)` |
| `wdt:P7482` | source of file | Wikidata Q item | `?file wdt:P7482 wd:Q74228490 .` (file available on the internet) |
| `wdt:P6216` | copyright status | Wikidata Q item | `?file wdt:P6216 wd:Q50402863 .` (public domain) |
| `wdt:P275` | copyright license | Wikidata Q item | `?file wdt:P275 wd:Q50829104 .` (CC0) |
| `wdt:P4082` | captured with | Wikidata Q item (camera) | `?file wdt:P4082 wd:Q649631 .` (Canon EOS 5D) |
| `wdt:P1259` | coordinates of point of view | Coordinates literal | Works with `#defaultView:Map` |
| `wdt:P2079` | fabrication method | Wikidata Q item | `?file wdt:P2079 wd:Q226881 .` (digital photography) |
| `wdt:P973` | described at URL | URL literal | `?file wdt:P973 ?url .` |

### 🏷️ Schema.org Media Predicates

These are **not** Wikidata properties — they use the Schema.org vocabulary directly in the RDF dump:

| Predicate | Meaning | Example |
|-----------|---------|---------|
| `schema:url` | File page URL (for `#defaultView:ImageGrid`) | `?file schema:url ?image .` |
| `schema:contentUrl` | Direct file download URL | `?file schema:contentUrl ?download .` |
| `schema:thumbnailUrl` | Thumbnail URL | `?file schema:thumbnailUrl ?thumb .` |
| `schema:width` | Image width in pixels | `?file schema:width ?w . FILTER(?w > 1000)` |
| `schema:height` | Image height in pixels | `?file schema:height ?h .` |
| `schema:encodingFormat` | MIME type | `?file schema:encodingFormat "image/jpeg" .` |
| `schema:datePublished` | Publication date | `?file schema:datePublished ?date .` |

### ⭐ Wikidata Properties Commonly Used on Commons Files

| Property | Label | Notes |
|----------|-------|-------|
| `wdt:P180` | depicts | The most-used property on Commons. Links to a Wikidata Q item. Qualifiers can specify: `pq:P462` (color), `pq:P6022` (expression/gesture/body pose), `pq:P518` (applies to part) |
| `wdt:P6243` | digital representation of | Stronger than depicts — the file *is* a digital version of the item (usually for artworks) |
| `wdt:P170` | creator | Can be a Q item (known Wikidata person) or use a qualifier `pq:P2093` for a text string author name |
| `wdt:P7482` | source of file | Common values: `Q74228490` (file available on the internet), `Q548662` (original creation by uploader) |

---

## QLever: Practical Usage (Recommended Endpoint)

QLever at `https://qlever.dev/api/wikimedia-commons` is the recommended endpoint for programmatic access. It requires **no authentication** and uses standard SPARQL over HTTP.

> ⚠️ **Prefix requirement:** QLever requires explicit PREFIX declarations. All examples below include the common prefixes. Copy-paste ready.

### GET request (simple queries)

```bash
curl -G "https://qlever.dev/api/wikimedia-commons" \
  --data-urlencode "query=PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/> SELECT ?file WHERE { ?file wdt:P180 wd:Q42 } LIMIT 10" \
  -H "Accept: application/sparql-results+json" \
  -H "User-Agent: MyBot/1.0 (https://example.com; user@example.com)"
```

### POST request (long queries)

```bash
curl -X POST "https://qlever.dev/api/wikimedia-commons" \
  -H "Accept: application/sparql-results+json" \
  -H "User-Agent: MyBot/1.0 (https://example.com; user@example.com)" \
  -d "query=PREFIX wd: <http://www.wikidata.org/entity/> PREFIX wdt: <http://www.wikidata.org/prop/direct/> SELECT ?file WHERE { ?file wdt:P180 wd:Q42 } LIMIT 10"
```

### Python with `requests`

```python
import requests

query = """
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>

SELECT ?file WHERE {
  ?file wdt:P180 wd:Q42 .
}
LIMIT 10
"""

headers = {
    "User-Agent": "MyBot/1.0 (https://example.com; user@example.com)",
    "Accept": "application/sparql-results+json",
}
resp = requests.get(
    "https://qlever.dev/api/wikimedia-commons",
    params={"query": query},
    headers=headers,
    timeout=60,
)
resp.raise_for_status()
data = resp.json()

for binding in data["results"]["bindings"]:
    file_uri = binding["file"]["value"]
    m_id = file_uri.rsplit("/", 1)[-1]  # Extract M37200540 from URI
    print(f"{m_id}: {file_uri}")
```

### QLever-specific notes

- Rate limiting: standard QLever limits apply (generous for reasonable usage)
- No OAuth, no cookies, no session management
- The QLever web UI at `https://qlever.dev/wikimedia-commons` provides a WIkidata-Query-Service-like interface with "Try it!" links, example queries, and result visualization
- Index information (last update date) is shown under the "Index Information" button in the UI
- QLever also supports `#defaultView:ImageGrid`, `#defaultView:Map`, and other visual directives

> ⚠️ **Required: explicit PREFIX declarations on QLever.** Unlike Blazegraph (used by WCQS and WDQS), which auto-registers common Wikidata prefixes (`wd:`, `wdt:`, `p:`, `ps:`, `pq:`), **QLever requires every prefix to be explicitly declared**. All SPARQL queries sent to the QLever endpoint must include PREFIX lines. Copy the block below as a header for every QLever query:
>
> ```sparql
> PREFIX wd: <http://www.wikidata.org/entity/>
> PREFIX wdt: <http://www.wikidata.org/prop/direct/>
> PREFIX p: <http://www.wikidata.org/prop/>
> PREFIX ps: <http://www.wikidata.org/prop/statement/>
> PREFIX pq: <http://www.wikidata.org/prop/qualifier/>
> PREFIX schema: <http://schema.org/>
> PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
> PREFIX commons: <http://commons.wikimedia.org/wiki/Special:FilePath/>
> ```
>
> The examples in this skill omit prefixes for brevity (they follow the WCQS/Blazegraph convention where prefixes are auto-registered). When running them against QLever, prepend the prefix block above.

---

## WCQS: Authentication (Official Endpoint, Use Only When Necessary)

The official WCQS at `https://commons-query.wikimedia.org/sparql` requires OAuth authentication. To use it programmatically, you must extract an OAuth cookie from your browser after logging in.

### Obtaining the `wcqsOauth` cookie

1. Visit `https://commons-query.wikimedia.org/` and log in with your Commons account
2. Open browser developer tools → Storage/Cookies → `https://commons-query.wikimedia.org`
3. Find the `wcqsOauth` cookie — its value is a hex string pair separated by a period (e.g., `b8d15147d1cfed1129f1f7f38e2acb03.9f8b5d50d1861bf2198ead63ff345c4a94986c61`)
4. Store this in an environment variable: `export WCQS_AUTH_TOKEN="..."`

> ⚠️ **Cookie lifespan:** The `wcqsOauth` cookie is valid indefinitely until you revoke the grant at [Special:OAuthManageMyGrants](https://commons.wikimedia.org/wiki/Special:OAuthManageMyGrants). Logging out of Commons does **not** invalidate it.

### Using the cookie with curl

```bash
curl -X POST "https://commons-query.wikimedia.org/sparql" \
  -H "Accept: application/sparql-results+json" \
  -H "User-Agent: MyBot/1.0 (https://example.com; user@example.com)" \
  -H "Cookie: wcqsOauth=$WCQS_AUTH_TOKEN" \
  --cookie-jar /tmp/wcqs-cookies.txt \
  -L \
  -d "query=SELECT ?file WHERE { ?file wdt:P180 wd:Q42 . } LIMIT 10"
```

The `-L` flag and `--cookie-jar` are important — WCQS issues a `wcqsSession` cookie via a 307 redirect on the first request, and subsequent requests need both cookies.

### Using the cookie with Python

```python
from http.cookiejar import Cookie
import os
import requests
from urllib.parse import urlparse

def init_wcqs_session(token):
    """Create a requests.Session authenticated against WCQS."""
    endpoint = "https://commons-query.wikimedia.org/sparql"
    domain = urlparse(endpoint).netloc
    session = requests.Session()
    session.headers.update({
        "User-Agent": "MyBot/1.0 (https://example.com; user@example.com)",
    })
    session.cookies.set_cookie(
        Cookie(0, "wcqsOauth", token, None, False,
               domain, False, False, "/", True,
               False, None, True, None, None, {})
    )
    return session

session = init_wcqs_session(os.environ["WCQS_AUTH_TOKEN"])
resp = session.post(
    "https://commons-query.wikimedia.org/sparql",
    data={"query": "SELECT ?file WHERE { ?file wdt:P180 wd:Q42 . } LIMIT 10"},
    headers={"Accept": "application/sparql-results+json"},
)
resp.raise_for_status()
print(resp.json())
```

### Using with Pywikibot

```python
import pywikibot
from pywikibot.data import sparql

site = pywikibot.Site('commons', 'commons')
site.login()

query = """
SELECT ?item WHERE {
  ?item wdt:P180 wd:Q42 .
} LIMIT 10
"""

entity_url = 'https://commons.wikimedia.org/entity/'
endpoint = 'https://commons-query.wikimedia.org/sparql'

query_object = sparql.SparqlQuery(endpoint=endpoint, entity_url=entity_url)
data = query_object.select(query, full_data=True)

for row in data:
    page_id = int(row['item'].getID().replace('M', ''))
    pages = list(site.load_pages_from_pageids([page_id]))
    if pages:
        print(pages[0])
```

---

## Core Query Patterns

### Pattern 1: ImageGrid — Visual Results

The `#defaultView:ImageGrid` directive displays results as a visual grid of thumbnails (works in both the WCQS web UI and QLever web UI):

```sparql
#defaultView:ImageGrid
SELECT ?file ?image WHERE {
  ?file wdt:P180 wd:Q42 ;       # depicts Douglas Adams
         schema:url ?image .     # file URL for thumbnail display
}
```

**Key requirement:** The query must select a variable bound to `schema:url` — that's what the ImageGrid view uses to render thumbnails.

### Pattern 2: Map — Geolocated Files

Files with `wdt:P1259` (coordinates of point of view) can be displayed on a map:

```sparql
#defaultView:Map
SELECT ?file ?pov_coords ?image WHERE {
  ?file wdt:P180 wd:Q12280 ;      # depicts bridge
         wdt:P1259 ?pov_coords ;   # has point-of-view coordinates
         schema:url ?image .
}
```

### Pattern 3: Captions (Labels for M IDs)

M IDs have multilingual captions accessible via `rdfs:label` or the `wikibase:label` SERVICE:

```sparql
SELECT ?file ?fileLabel WHERE {
  ?file wdt:P180 wd:Q102231 .          # depicts rose
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "en" .
  }
}
```

Note: The `wikibase:label` SERVICE works the same way as in WDQS but returns the **file caption** as the label for M IDs.

### Pattern 4: Media Metadata — Files by Dimensions

```sparql
# Find square images larger than 2000×2000 pixels
SELECT ?file ?w ?h WHERE {
  ?file schema:width ?w ;
         schema:height ?h .
  FILTER(?w = ?h && ?w > 2000)
}
LIMIT 100
```

### Pattern 5: Files by File Type

```sparql
SELECT ?encoding (COUNT(*) AS ?total) WHERE {
  ?file schema:encodingFormat ?encoding .
}
GROUP BY ?encoding
ORDER BY DESC(?total)
```

### Pattern 6: Copyright / License Analysis

```sparql
# Files under CC0 license
SELECT ?file ?image WHERE {
  ?file wdt:P275 wd:Q50829104 ;   # copyright license = CC0
         schema:url ?image .
}
LIMIT 100
```

```sparql
# Public domain files
SELECT ?file ?image WHERE {
  ?file wdt:P6216 wd:Q50402863 ;   # copyright status = public domain
         schema:url ?image .
}
LIMIT 100
```

### Pattern 7: Media from a Specific Commons Category

Uses the `wikibase:mwapi` SERVICE to find all files in a Category:

```sparql
# Files directly in Category:Spoken English Wikipedia
SELECT ?member WHERE {
  BIND("Category:Spoken English Wikipedia" AS ?category) .
  SERVICE wikibase:mwapi {
     bd:serviceParam wikibase:endpoint "commons.wikimedia.org";
                     wikibase:api "Generator";
                     mwapi:generator "categorymembers";
                     mwapi:gcmtype "file";
                     mwapi:gcmtitle ?category;
                     mwapi:gcmprop "title";
                     mwapi:gcmlimit "max".
     ?member wikibase:apiOutput mwapi:title.
  }
}
```

To construct M IDs from the MWAPI output:

```sparql
SELECT ?file ?category WHERE {
  BIND("Category:Media from iNaturalist" AS ?category) .
  SERVICE wikibase:mwapi {
     bd:serviceParam wikibase:endpoint "commons.wikimedia.org";
                     wikibase:api "Generator";
                     mwapi:generator "categorymembers";
                     mwapi:gcmtype "file";
                     mwapi:gcmtitle ?category;
                     mwapi:gcmlimit "max";
                     mwapi:gcmprop "title|pageid".
     ?title wikibase:apiOutput mwapi:title .
     ?pageid wikibase:apiOutput "@pageid" .
  }
  BIND(URI(CONCAT('https://commons.wikimedia.org/entity/M', ?pageid)) AS ?file)
}
```

---

## Federated Queries: Commons ↔ Wikidata

One of the most powerful features is **federating** between the Commons SPARQL endpoint and the Wikidata Query Service. This lets you find Commons files based on Wikidata properties.

### Pattern A: File depicts a Wikidata item → get Wikidata label

```sparql
SELECT ?file ?itemLabel WHERE {
  ?file wdt:P180 wd:Q42 .
  SERVICE <https://query.wikidata.org/sparql> {
    SERVICE wikibase:label {
      bd:serviceParam wikibase:language "en" .
      wd:Q42 rdfs:label ?itemLabel .
    }
  }
}
```

### Pattern B: All files depicting Van Gogh's artworks

Finds all Wikidata items where `creator = Vincent van Gogh`, then finds all Commons files that depict those items:

```sparql
#defaultView:ImageGrid
SELECT ?image ?painting ?paintingLabel WITH {
  SELECT * {
    SERVICE <https://query.wikidata.org/sparql> {
      ?painting wdt:P170 wd:Q5582 .                          # painter = Van Gogh
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en" .
        ?painting rdfs:label ?paintingLabel .
      }
    }
  }
} AS %paintings WHERE {
  INCLUDE %paintings .
  ?image wdt:P180 ?painting ;      # file depicts this painting
         schema:url ?image .
}
```

### Pattern C: Subclass-aware — files depicting roses (and all rose subclasses)

```sparql
#defaultView:ImageGrid
SELECT DISTINCT ?item ?itemLabel ?image WITH {
  SELECT ?item ?itemLabel WHERE {
    SERVICE <https://query.wikidata.org/sparql> {
      ?item wdt:P31/wdt:P279* wd:Q34687 .   # subclasses of rose
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en" .
        ?item rdfs:label ?itemLabel .
      }
    }
  }
} AS %wikidataItems WHERE {
  INCLUDE %wikidataItems .
  ?file wdt:P180 ?item ;            # file depicts this rose species/variety
         schema:url ?image .
}
LIMIT 1000
```

### Pattern D: Camera analytics — cameras used by iNaturalist contributors

```sparql
SELECT DISTINCT ?capturedWith ?capturedWithLabel (COUNT(?file) AS ?counts)
WITH {
  SELECT ?file ?title WHERE {
    SERVICE wikibase:mwapi {
      bd:serviceParam wikibase:api "Generator";
                      wikibase:endpoint "commons.wikimedia.org";
                      mwapi:gcmtitle "Category:Media from iNaturalist";
                      mwapi:generator "categorymembers";
                      mwapi:gcmtype "file";
                      mwapi:gcmlimit "max".
      ?title wikibase:apiOutput mwapi:title .
      ?pageid wikibase:apiOutput "@pageid" .
    }
    BIND(URI(CONCAT('https://commons.wikimedia.org/entity/M', ?pageid)) AS ?file)
  }
} AS %get_files
WHERE {
  INCLUDE %get_files
  ?file wdt:P4082 ?capturedWith .
  SERVICE <https://query.wikidata.org/sparql> {
    SERVICE wikibase:label {
      bd:serviceParam wikibase:language "en" .
      ?capturedWith rdfs:label ?capturedWithLabel .
    }
  }
}
GROUP BY ?capturedWith ?capturedWithLabel
ORDER BY DESC(?counts)
```

### ⚠️ Federation Performance Notes

- Federated queries are **slower** than single-endpoint queries — expect 10-60s
- On WCQS, the Blazegraph optimizer can interfere with federated queries. Add hints if needed:
  ```sparql
  hint:Query hint:optimizer "None"
  ```
  or
  ```sparql
  hint:Prior hint:runFirst true
  ```
- On QLever, federation performance is generally better due to the QLever engine's design
- For performance, consider fetching data from Wikidata first (small result set), then using `VALUES` to pass it to the Commons endpoint

---

## Advanced Qualifier Query Patterns

Commons statements can carry **qualifiers** — additional context for a statement. For example, a `depicts` (P180) statement can be qualified with `P462` (color) or `P6022` (expression/gesture/body pose).

### Pattern A: Depicts + Color qualifier

```sparql
# Files depicting roses + the color of the rose
SELECT ?file ?color ?image WITH {
  SELECT ?color (IRI(REPLACE(STR(SAMPLE(?photo)), "^.*/", STR(commons:))) AS ?image) WHERE {
    ?file a schema:ImageObject ;
          schema:contentUrl ?photo ;
          p:P180 [                      # statement-level path
            ps:P180 wd:Q102231 ;        # value = rose
            pq:P462 ?color              # qualifier = color
          ] .
  }
  GROUP BY ?color
} AS %roses WHERE {
  INCLUDE %roses .
  SERVICE <https://query.wikidata.org/sparql> {
    SERVICE wikibase:label {
      bd:serviceParam wikibase:language "en" .
      ?color rdfs:label ?colorName .
    }
  }
}
```

### Pattern B: Depicts + Gesture qualifier

```sparql
# Most common gesture/expression values for depicts statements
SELECT ?count ?value ?valueLabel ?example
WITH {
  SELECT (COUNT(DISTINCT(?file)) AS ?count) ?value (SAMPLE(?file) AS ?example) WHERE {
    ?file p:P180/pq:P6022 ?value .     # qualifier path: depicts → expression/gesture
  }
  GROUP BY ?value
  ORDER BY DESC(?count)
  LIMIT 2000
} AS %values
WHERE {
  INCLUDE %values .
  SERVICE <https://query.wikidata.org/sparql> {
    SERVICE wikibase:label {
      bd:serviceParam wikibase:language "en" .
      ?value rdfs:label ?valueLabel .
    }
  }
}
ORDER BY DESC(?count)
```

### Path syntax summary

| Path | Meaning |
|------|---------|
| `?file wdt:P180 wd:Q42` | File has a **direct** `depicts` statement with value Q42 |
| `?file p:P180 ?statement` | Bind the `depicts` **statement node** (to then access qualifiers) |
| `?statement ps:P180 wd:Q42` | The statement node's value is Q42 |
| `?statement pq:P462 ?color` | The statement node's qualifier is `color = ?color` |
| `?file p:P180/pq:P6022 ?value` | Shorthand: navigate from file through statement to qualifier |

---

## Practical Limitations

### WCQS Limitations

- **Beta status:** No stability, interface, or backward-compatibility guarantees
- **Weekly reloads:** Data reloaded every Monday from Sunday dumps; service is down ~4 hours during reload
- **HTTP URIs:** MediaInfo concept URIs are still HTTP, not HTTPS (may change — see [T258590](https://phabricator.wikimedia.org/T258590))
- **No prefix support:** URI prefixes for Commons-specific data don't work yet — use full URIs
- **No autocomplete:** Autocomplete for Commons entities doesn't work in the WCQS web UI

### QLever Limitations

- **Third-party service:** Not operated by WMF — no SLO, no operational guarantees
- **Index freshness:** Updates depend on the QLever project's ingestion pipeline
- **Different query engine:** QLever's SPARQL implementation has some differences from Blazegraph — certain complex queries may behave differently

### Common to Both

- 1.5 billion triples/year growth — data volumes will continue increasing
- MediaInfo vocabulary is a subset of the full Wikidata property space — not all properties are equally populated on Commons files
- The query you write may need to use a random sample (`bd:sample` SERVICE on WCQS) to avoid timeouts on large result sets

---

## Tooling

### 🔧 Commons SPARQL Quick Query (`scripts/commons-sparql-query.sh`)

Run a SPARQL query against the QLever Commons endpoint and display results:

```bash
./scripts/commons-sparql-query.sh "SELECT ?file WHERE { ?file wdt:P180 wd:Q42 } LIMIT 10"
./scripts/commons-sparql-query.sh --ql "SELECT ?file WHERE { ?file wdt:P180 wd:Q42 } LIMIT 10"
```

### 📚 Commons SPARQL Patterns Reference (`references/commons-sparql-patterns.md`)

Deep reference including:
- All Commons Wikibase properties with their data types and usage
- Pre-built query patterns for common tasks
- Catalogs-specific queries
- GLAM workflow queries
- Performance optimization for federated queries

### 🐍 Commons SPARQL Inspector (`assets/commons-sparql-inspector.py`)

A Python tool to inspect Commons structured data — find M IDs by file title, query depicts/copyright/camera data, and display results as formatted output.
