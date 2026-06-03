# Wikidata Vector Database — Endpoint Reference

## Base URL

```
https://wd-vectordb.wmcloud.org
```

## Authentication

No API key required. A descriptive `User-Agent` header is mandatory (HTTP 403 without one).

## Data Retention

Query text is sent to JinaAI for embedding and stored for up to 90 days for quality improvement. See the [privacy notice on the web UI](https://wd-vectordb.wmcloud.org/).

## Endpoints

### `GET /item/query/` — Search Items

Search Wikidata items (QIDs) by semantic similarity to a free-text query.

| Parameter | Required | Type | Default | Description |
|---|---|---|---|---|
| `query` | ✅ | string | — | Free-text search query. Examples: `"Douglas Adams"`, `"Q42"`, `"author of Hitchhiker's Guide"` |
| `lang` | — | string | `"all"` | Language code. Supported: `"all"`, `"en"`, `"de"`, `"ar"`, `"fr"`. Other languages → translated to English then searched. |
| `K` | — | integer | `50` | Number of results. Minimum 1. |
| `instanceof` | — | string | — | Comma-separated QIDs for class filter. ⚠️ Non-functional in v0.2.1. |
| `rerank` | — | boolean | `false` | Apply cross-encoder reranking for improved relevance. |
| `return_vectors` | — | boolean | `false` | Include raw embedding vectors in response. |

**Response:** `200 OK`

```json
[
  {
    "QID": "Q42",
    "similarity_score": 0.8758,
    "rrf_score": 0.0392,
    "source": "Vector Search",
    "vector": null,
    "reranker_score": null
  }
]
```

| Field | Type | Description |
|---|---|---|
| `QID` | string | Wikidata item identifier |
| `similarity_score` | float | Dot product between query and entity vectors (0–1 range typically) |
| `rrf_score` | float or null | Reciprocal Rank Fusion score (combines vector + keyword ranks) |
| `source` | string | `"Vector Search"`, `"Keyword Search"`, or `"Vector Search, Keyword Search"` |
| `vector` | float[] or null | Present when `return_vectors=true` |
| `reranker_score` | float or null | Present when `rerank=true` |

**Error responses:** `422` (bad parameters), `500` (internal server error)

---

### `GET /property/query/` — Search Properties

Search Wikidata properties (PIDs) by semantic similarity.

Same parameters as item search, plus:

| Parameter | Required | Type | Default | Description |
|---|---|---|---|---|
| `exclude_external_ids` | — | boolean | `false` | Filter out properties with external-identifier datatype |

**Response:** Same shape as item search but with `PID` instead of `QID`.

---

### `GET /similarity-score/` — Compare Query Against Specific Entities

Compute similarity scores between a query and specific Wikidata entities.

| Parameter | Required | Type | Default | Description |
|---|---|---|---|---|
| `query` | ✅ | string | — | Free-text query to compare against |
| `qid` | ✅ | string | — | Comma-separated list of QIDs and/or PIDs |
| `lang` | — | string | `"all"` | Language code |
| `return_vectors` | — | boolean | `false` | Include raw vectors |

**Response:** `200 OK`

```json
[
  { "QID": "Q2",   "similarity_score": 0.5423 },
  { "QID": "Q36153", "similarity_score": 0.5135 },
  { "QID": "Q42",  "similarity_score": 0.5103 }
]
```

| Field | Type | Description |
|---|---|---|
| `QID` | string or null | Wikidata item identifier (present for items) |
| `PID` | string or null | Wikidata property identifier (present for properties) |
| `similarity_score` | float | Dot product similarity |
| `vector` | float[] or null | Present when `return_vectors=true` |

---

## Query Parameter Encoding

All parameters are standard URL query parameters. Encode special characters in the `query` value:

```bash
# Python
python3 -c "import urllib.parse; print(urllib.parse.quote('author of Hitchhiker\'s Guide'))"

# JavaScript
encodeURIComponent("author of Hitchhiker's Guide")

# curl (manual)
curl "...?query=author+of+Hitchhiker%27s+Guide"
```

## Language Code Reference

See the `/languages` endpoint for the full list:

```bash
curl -sL -H "User-Agent: MyBot/1.0" https://wd-vectordb.wmcloud.org/languages
```

Returns:

```json
{
  "vectordb_langs": ["ar", "de", "en", "fr"],
  "other_langs": ["ace", "acm", "acq", ..., "zu"]
}
```

- `vectordb_langs` — languages with dedicated vector datasets. Queries in these languages search their native vector space.
- `other_langs` — all other supported languages. Queries are machine-translated to English and searched against the full database.
