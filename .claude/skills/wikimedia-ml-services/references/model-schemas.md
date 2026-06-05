# Lift Wing Model Schemas Reference

Complete request/response schema reference for all externally accessible Lift Wing models,
**verified against the live API** (tested June 2026).

> ⚠️ Models in the "experimental" Kubernetes namespace are internal-only. Only models listed here
> or on the [Lift Wing API Reference](https://api.wikimedia.org/wiki/Lift_Wing_API/Reference) are
> accessible from external clients (including Toolforge and Cloud VPS).
>
> 📌 **Model naming note:** The modern article quality model is called just `articlequality` (not `articlequality-language-agnostic`).
> The content translation recommendation is a GET REST API at `/service/lw/recommendation/api/v1/translation`, not a POST inference model.

---

## 1. Edit Quality — Revscoring Models (Frozen)

These were migrated from ORES. They use the **old ORES response format** (not the Lift Wing envelope).

### `{wiki}-goodfaith`, `{wiki}-damaging`, `{wiki}-reverted`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/{wiki}-goodfaith:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rev_id` | int | ✅ | Revision ID to score |

```json
{
  "enwiki": {
    "models": {
      "goodfaith": {"version": "0.5.1"}
    },
    "scores": {
      "123456789": {
        "goodfaith": {
          "score": {
            "prediction": true,
            "probability": {"false": 0.025, "true": 0.975}
          }
        }
      }
    }
  }
}
```

Access pattern: `result[wiki]["scores"][str(rev_id)][model_name]["score"]`

**Available wikis for `goodfaith`:** arwiki, bswiki, cawiki, cswiki, dewiki, enwiki, eswikibooks, eswiki, eswikiquote, etwiki, fawiki, fiwiki, frwiki, hewiki, hiwiki, huwiki, itwiki, jawiki, kowiki, lvwiki, nlwiki, nowiki, plwiki, ptwiki, rowiki, ruwiki, sqwiki, srwiki, svwiki, trwiki, ukwiki, wikidatawiki, zhwiki

**Available wikis for `damaging`:** same set as `goodfaith`

**Available wikis for `reverted`:** bnwiki, elwiki, enwiktionary, glwiki, hrwiki, idwiki, iswiki, tawiki, viwiki

### `{wiki}-articlequality` — Article quality grade

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/{wiki}-articlequality:predict
```

Same request/response format (ORES-style).

Possible predictions: `FA`, `GA`, `B`, `C`, `Start`, `Stub`

**Available wikis:** enwiki, euwiki, fawiki, frwiki, glwiki, nlwiki, ptwiki, ruwiki, svwiki, trwiki, ukwiki

Also available as `wikidatawiki-itemquality` for Wikidata items.

### `{wiki}-draftquality`, `{wiki}-drafttopic`, `{wiki}-articletopic`, `wikidatawiki-itemtopic`

Same request/response format. See the [WMF model list](https://wikitech.wikimedia.org/wiki/Machine_Learning/LiftWing#Revscoring_models_(migrated_from_ORES)) for available wikis per model.

---

## 2. Revert Risk — Modern Models (Preferred)

These replace the combination of `goodfaith` + `damaging`. They use the **Lift Wing unified envelope**.

### `revertrisk-language-agnostic`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-language-agnostic:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rev_id` | int | ✅ | Revision ID to score |
| `lang` | string | ✅ | Language code (e.g., `en`, `fr`) |

```json
{
  "model_name": "revertrisk-language-agnostic",
  "model_version": "3",
  "wiki_db": "enwiki",
  "revision_id": 123456789,
  "output": {
    "prediction": false,
    "probabilities": {"true": 0.34, "false": 0.66}
  }
}
```

### `revertrisk-multilingual`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-multilingual:predict
```

Same request/response as language-agnostic. Trained on 300+ languages.

### `revertrisk-wikidata`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-wikidata:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rev_id` | int | ✅ | Wikidata revision ID |

```json
{
  "model_name": "revertrisk-wikidata",
  "model_version": "2",
  "revision_id": 123456789,
  "output": {
    "prediction": false,
    "probabilities": {"true": 0.34, "false": 0.66}
  }
}
```

Note: No `lang` parameter — Wikidata-specific features only.

---

## 3. Readability

### `readability`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/readability:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rev_id` | int | ✅ | Revision ID (not `page_title`) |
| `lang` | string | ✅ | Language code |

```json
{
  "model_name": "readability",
  "model_version": "4",
  "wiki_db": "enwiki",
  "revision_id": 123456789,
  "output": {
    "score": 0.643,
    "fk_score_proxy": 9.4
  }
}
```

| Field | Range | Interpretation |
|-------|-------|---------------|
| `output.score` | 0–1 | Higher = more readable. >0.6 = accessible. <0.3 = very difficult. |
| `output.fk_score_proxy` | 0–20+ | Approximate Flesch-Kincaid grade level. 8–10 = average adult. |

---

## 4. Article Quality — Modern Model

### `articlequality`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/articlequality:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rev_id` | int | ✅ | Revision ID |
| `lang` | string | ✅ | Language code |

```json
{
  "score": 0.475,
  "model_name": "articlequality",
  "model_version": "1",
  "wiki_db": "enwiki",
  "revision_id": 123456789
}
```

Returns a continuous quality score (float 0–1). Higher = higher quality.
This is different from the Revscoring `{wiki}-articlequality` model which returns
a discrete grade (FA/GA/B/C/Start/Stub).

---

## 5. Topic Classification

### `outlink-topic-model`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/outlink-topic-model:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page_title` | string | ✅ | Page title with underscores |
| `lang` | string | ✅ | Language code |

```json
{
  "prediction": {
    "article": "https://en.wikipedia.org/wiki/Albert_Einstein",
    "results": [
      {"topic": "STEM.STEM*", "score": 0.899},
      {"topic": "STEM.Physics", "score": 0.737},
      {"topic": "Culture.Biography.Biography*", "score": 0.731}
    ]
  }
}
```

Access: `result["prediction"]["results"]` → array of `{topic, score}`

Topic taxonomy is hierarchical with dot-separated paths. Top-level categories: `Culture`,
`Geography`, `History`, `People`, `STEM`, `Society`.

---

## 6. Reference Quality — Modern Models

### `reference-need`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/reference-need:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rev_id` | int | ✅ | Revision ID (not `page_title`) |
| `lang` | string | ✅ | Language code |

```json
{
  "model_name": "reference-need",
  "model_version": 0,
  "wiki_db": "enwiki",
  "revision_id": 123456789,
  "reference_need_score": 0.923
}
```

Returns a single aggregate score (0–1). Higher = more text likely needs citations.
**Does not return per-sentence breakdowns.**

### `reference-risk`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/reference-risk:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rev_id` | int | ✅ | Revision ID (not `page_title`) |
| `lang` | string | ✅ | Language code |

```json
{
  "model_name": "reference-risk",
  "model_version": "2024-11",
  "wiki_db": "enwiki",
  "revision_id": 123456789,
  "reference_count": 7,
  "survival_ratio": {
    "min": 0.154,
    "mean": 0.682,
    "median": 0.715
  },
  "reference_risk_score": 0.0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `reference_risk_score` | float | Risk that citations are unreliable (0–1) |
| `reference_count` | int | Number of references found in the revision |
| `survival_ratio` | dict | Citation survival statistics: `min`, `mean`, `median` |

---

## 7. Language Identification

### `langid`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/langid:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | ✅ | Raw text to identify (not a page reference) |

```json
{
  "language": "eng_Latn",
  "wikicode": "en",
  "languagename": "English",
  "score": 0.782
}
```

| Field | Description |
|-------|-------------|
| `language` | ISO language code with script (e.g., `eng_Latn`) |
| `wikicode` | Wikimedia language code (e.g., `en`, `fr`, `de`) |
| `languagename` | Human-readable language name |
| `score` | Confidence score (0–1) |

---

## 8. Article Country

### `article-country`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/article-country:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ | Page title with underscores (parameter is `title`, not `page_title`) |
| `lang` | string | ✅ | Language code |

```json
{
  "model_name": "article-country",
  "model_version": "1",
  "prediction": {
    "article": "https://en.wikipedia.org/wiki/Albert_Einstein",
    "wikidata_item": "Q937",
    "results": [
      {"country": "United States", "score": 1.0,
       "source": {
         "wikidata_properties": [{"P27": "country of citizenship"}],
         "categories": ["Category:Swiss emigrants to the United States", "..."]
       }
      },
      {"country": "Switzerland", "score": 0.67, "source": {...}},
      {"country": "Germany", "score": 0.17, "source": {...}}
    ]
  }
}
```

Results are sorted by `score` descending. The `source` field shows evidence from
Wikidata properties and category membership.

---

## 9. Content Translation Recommendations

### `content-translation-recommendation`

This is **not a POST inference model** — it's a GET REST API at a different base path:

```
GET https://api.wikimedia.org/service/lw/recommendation/api/v1/translation
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source` | string | ✅ | Source wiki language code (e.g., `en`) |
| `target` | string | ✅ | Target wiki language code (e.g., `fr`) |
| `count` | int | ❌ | Number of recommendations (default `12`) |
| `seed` | string | ❌ | Seed article (pipe `|`-separated for multiple) |
| `topic` | string | ❌ | Topic filter (pipe-separated) |
| `include_pageviews` | bool | ❌ | Include pageview counts |
| `search_algorithm` | string | ❌ | `morelike` or `mostpopular` |

Response:
```json
{
  "recommendations": [
    {"title": "Flamenco (apple)", "pageviews": 0, "wikidata_id": "Q19597233",
     "rank": 7, "langlinks_count": 1, "size": 6871}
  ]
}
```

## 10. Article Descriptions

### `article-descriptions`

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/article-descriptions:predict
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | ✅ | Page title with underscores |
| `lang` | string | ✅ | Language code |
| `num_beams` | int | ✅ | Beam search width (start with 1) |

Generates a Wikidata-style short description. This is a **heavy model** — responses can be slow.

---

## Summary: Input Parameter Patterns

| Pattern | Models Using It |
|---------|---------------|
| `{"rev_id": int}` | All Revscoring models (goodfaith, damaging, articlequality, etc.), `revertrisk-wikidata` |
| `{"rev_id": int, "lang": string}` | `revertrisk-language-agnostic`, `revertrisk-multilingual`, `readability`, `reference-need`, `reference-risk`, `articlequality` |
| `{"page_title": string, "lang": string}` | `outlink-topic-model` |
| `{"title": string, "lang": string}` (note: `title`, not `page_title`) | `article-country` |
| `{"title": string, "lang": string, "num_beams": int}` | `article-descriptions` |
| `{"text": string}` | `langid` |
| GET query params (not POST) | `content-translation-recommendation` (`/service/lw/recommendation/api/v1/translation?source=&target=&seed=...`) |

## Rate Limits (External)

| Client Type | Requests/hour | Requests/second |
|-------------|---------------|-----------------|
| Anonymous | 50,000 | 15 |
| Browser | 50,000 | 50 |
| Authenticated (OAuth) | 100,000 | 100 |
| Known client (Toolforge, approved bots) | 200,000 | 200 |

> 💡 **Per-second limits are the binding constraint** for batch operations.
> At 15 req/s, scoring 1,000 revisions takes ~67 seconds minimum.
> Use authentication (OAuth) to raise the ceiling to 100 req/s.
