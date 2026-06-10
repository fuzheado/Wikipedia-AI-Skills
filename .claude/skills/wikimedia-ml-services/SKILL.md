---
name: wikimedia-ml-services
description: Score article quality, revert risk, edit quality (goodfaith/damaging), readability, topic classification, reference quality, language identification, content translation recommendations, article descriptions, and article country using Wikimedia ML inference APIs (Lift Wing and legacy ORES)
depends_on: [wikimedia-api-access]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["revert", "vandalism", "quality", "FA", "GA", "Start", "Stub", "article quality", "goodfaith", "damaging"]
  - keywords: ["readability", "grade level", "Flesch-Kincaid", "reading score"]
  - keywords: ["topic", "classification", "category prediction", "outlink", "article topic"]
  - keywords: ["Lift Wing", "ORES", "ML", "machine learning", "inference", "model score"]
  - keywords: ["reference", "citation quality", "reference need", "unsourced", "reference risk"]
  - keywords: ["language detection", "langid", "identify language"]
  - keywords: ["translation", "content translation", "cross-language", "recommendation"]
---

> ⚠️ **User-Agent required:** All API calls below need a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

## Context: Two Eras of Wikimedia ML Services

Wikimedia has two ML inference pipelines:

| Era | Status | Architecture | Base URL |
|-----|--------|-------------|----------|
| **ORES** | **Deprecated** (unmaintained since late 2023, may break) | Python scoring server, GET-based, batch scoring | `https://ores.wikimedia.org/v3/scores/{wiki}/{revid}` |
| **Lift Wing** | **Active** (current WMF ML platform) | Kubernetes/KServe, POST-based, one model per endpoint | `https://api.wikimedia.org/service/lw/inference/v1/models/{model-name}:predict` |

**Always prefer Lift Wing.** ORES is documented here *only* for migrating existing code. New tools must use Lift Wing.

---

## Reference: Available Lift Wing Models

Lift Wing serves two tiers of models:

### Revscoring Models (Frozen — migrated from ORES, no further improvements)

| Model Name | Input | Output | Purpose | Modern Replacement |
|-----------|-------|--------|---------|-------------------|
| `{wiki}-goodfaith` | `rev_id` | `{"prediction": true/false, "probability": {"true": float, "false": float}}` | Good/bad faith edit | `revertrisk-*` |
| `{wiki}-damaging` | `rev_id` | Same structure | Is edit damaging? | `revertrisk-*` |
| `{wiki}-reverted` | `rev_id` | Same structure | Will edit be reverted? | `revertrisk-*` |
| `{wiki}-articlequality` | `rev_id` | `{"prediction": "FA"/"GA"/"B"/"C"/"Start"/"Stub", "probability": {...}}` | Article quality class | `articlequality` (modern model, continuous score) |
| `{wiki}-draftquality` | `rev_id` | `{"prediction": "...", "probability": {...}}` | Draft quality | — |
| `{wiki}-articletopic` | `rev_id` | `{"prediction": [...], "probability": {...}}` | Article topic scores | `outlink-topic-model` |
| `{wiki}-drafttopic` | `rev_id` | Same structure | Draft topic scores | — |
| `wikidatawiki-itemquality` | `rev_id` | Same structure | Wikidata item quality | — |
| `wikidatawiki-itemtopic` | `rev_id` | Same structure | Wikidata item topic | — |

Replace `{wiki}` with the wiki code (e.g., `enwiki`, `frwiki`, `arwiki`). Available wikis vary per model — check the [model list](https://wikitech.wikimedia.org/wiki/Machine_Learning/LiftWing#Revscoring_models_(migrated_from_ORES)).

### Modern Models (Actively developed, preferred for new tools)

| Model Name | Input | Output (Key Fields) | Best For |
|-----------|-------|-------------------|----------|
| `revertrisk-language-agnostic` | `{"rev_id": int, "lang": string}` | `output.prediction` (bool), `output.probabilities.{true, false}` (float) | **Anti-vandalism** — single score replacing goodfaith+damaging combined |
| `revertrisk-multilingual` | `{"rev_id": int, "lang": string}` | `output.prediction` (bool), `output.probabilities.{true, false}` (float) | Anti-vandalism across 300+ languages |
| `revertrisk-wikidata` | `{"rev_id": int}` | `output.prediction` (bool), `output.probabilities.{true, false}` (float) | Wikidata-specific revert risk |
| `readability` | `{"rev_id": int, "lang": string}` | `output.score` (float 0–1), `output.fk_score_proxy` (grade level) | **Readability scoring** — complexity and grade level |
| `reference-need` | `{"rev_id": int, "lang": string}` | `reference_need_score` (float 0–1) | **Find unsourced claims** in an article |
| `reference-risk` | `{"rev_id": int, "lang": string}` | `reference_risk_score` (float), `reference_count` (int), `survival_ratio` (dict) | **Reference quality risk** — are citations reliable? |
| `outlink-topic-model` | `{"page_title": string, "lang": string}` | `prediction.results[]` — array of `{topic: string, score: float}` | **Topic classification** — replaces articletopic, link-based |
| `articlequality` | `{"rev_id": int, "lang": string}` | `score` (float 0–1) | **Quality scoring** — continuous quality score (modern model, different from Revscoring grades) |
| `article-country` | `{"title": string, "lang": string}` | `prediction.results[]` — array of `{country: string, score: float, source: {...}}` | Predict which country an article is about |
| `article-descriptions` | `{"title": string, "lang": string, "num_beams": int}` | (generates Wikidata-style short description — heavy model, may be slow) | Generate a Wikidata-like short description |
| `langid` | `{"text": string}` | `wikicode` (string), `score` (float confidence) | **Language identification** of raw text |

> 💡 **Prefer modern models.** The Revscoring models are frozen — no retraining, no new wikis. The modern models (especially `revertrisk-*`, `outlink-topic-model`) are trained on fresher data and cover more wikis.

> ⚠️ **Model naming is inconsistent.** The modern `articlequality` model is called just `articlequality` (not `articlequality-language-agnostic`). The content translation service is a **GET REST API** at `/service/lw/recommendation/api/v1/translation`, not a POST inference model. See the individual SOPs below.

---

## SOP: Making Lift Wing API Calls

### Common Request Pattern

All Lift Wing models use `POST` to the same base URL pattern:

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/{MODEL_NAME}:predict
Content-Type: application/json
Authorization: Bearer {TOKEN}    (optional — needed for >50k req/hr)
User-Agent: MyBot/1.0 (user@example.com) ContentGapResearch
```

```python
import requests

headers = {
    "User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch",
    "Content-Type": "application/json",
}
url = "https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-articlequality:predict"
data = {"rev_id": 123456789}

resp = requests.post(url, json=data, headers=headers, timeout=30)
result = resp.json()
```

### Authentication for Higher Rate Limits

| Client Type | Rate Limit (req/h) | Rate Limit (req/s) | How to Qualify |
|-------------|-------------------|-------------------|----------------|
| Anonymous | 50,000 | 15 | No auth needed |
| Browser session | 50,000 | 50 | Login cookie |
| **Authenticated** | **100,000** | **100** | OAuth token via `api.wikimedia.org/wiki/Authentication` |
| **Known client** (Toolforge, approved bots) | **200,000** | **200** | OAuth token + known user-agent |

To authenticate, follow the [Wikimedia API authentication guide](https://api.wikimedia.org/wiki/Authentication) to obtain an OAuth access token, then include it in requests:

```python
headers = {
    "Authorization": f"Bearer {access_token}",
    "User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch",
    "Content-Type": "application/json",
}
```

### Handling Response Structure

> ⚠️ **This is the single most common source of bugs.** The response formats are nested and non-obvious. Always check the response structure before writing access code.

**Revscoring models** on Lift Wing use the **old ORES response format** (not the Lift Wing envelope):
```json
{
  "enwiki": {                            # ← key is the wiki code (changes per model!)
    "models": {
      "articlequality": {"version": "0.9.2"}
    },
    "scores": {
      "123456789": {                      # ← key is the revision ID as a STRING
        "articlequality": {              # ← key is the model name
          "score": {
            "prediction": "C",           # ← "FA"/"GA"/"B"/"C"/"Start"/"Stub"
            "probability": {              # ← per-class confidence (sums to 1.0)
              "B": 0.02, "C": 0.78, "FA": 0.0,
              "GA": 0.12, "Start": 0.07, "Stub": 0.01
            }
          }
        }
      }
    }
  }
}
```

**Access pattern:**
```python
result[wiki]["scores"][str(rev_id)][model_name]["score"]["prediction"]
# Example:
grade = result["enwiki"]["scores"]["123456789"]["articlequality"]["score"]["prediction"]
```

**Modern revert-risk models** use a flat unified envelope:
```json
{
  "model_name": "revertrisk-language-agnostic",
  "model_version": "3",
  "wiki_db": "enwiki",
  "revision_id": 123456789,
  "output": {
    "prediction": false,                 # ← bool: true = likely reverted
    "probabilities": {
      "true": 0.34,                       # ← float 0-1: probability of revert
      "false": 0.66
    }
  }
}
```

**Access pattern:**
```python
risk = result["output"]["probabilities"]["true"]   # ← float 0-1
prediction = result["output"]["prediction"]          # ← bool
```

**Modern articlequality model (continuous score):**
```json
{
  "model_name": "articlequality",
  "model_version": "1",
  "wiki_db": "enwiki",
  "revision_id": 123456789,
  "output": {
    "prediction": {"score": 0.72}        # ← float 0-1, NOT a discrete grade
  }
}
```

**Access pattern:**
```python
score = result["output"]["prediction"]["score"]    # ← float 0-1
# 0.72 is closer to "B" grade (the continuous model is different from the discrete Revscoring model!)
```

**Modern models** have per-model response schemas. See the model-specific SOPs below.

---

## SOP: Editing the Page — How Lift Wing and EventStreams Work Together

Lift Wing ML predictions integrate naturally with the EventStreams real-time feed. The most common production pattern is:

1. **Consume** `recentchange` or `revision-create` events via EventStreams (see the **[wikimedia-eventstreams](../wikimedia-eventstreams/SKILL.md)** skill)
2. **Score** each new revision via Lift Wing (revert risk, damaging, goodfaith)
3. **Act** on the score (flag for review, auto-revert, pass through)

```python
import requests, json

HEADERS = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}

def score_revision_revscoring(wiki: str, rev_id: int, model: str) -> dict:
    """Score a single revision using a Revscoring model on Lift Wing.
    
    Note: Revscoring models return the old ORES response format.
    """
    url = f"https://api.wikimedia.org/service/lw/inference/v1/models/{wiki}-{model}:predict"
    resp = requests.post(url, json={"rev_id": rev_id}, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()

# Example: score an edit for goodfaith
result = score_revision_revscoring("enwiki", 123456789, "goodfaith")
prediction = result["enwiki"]["scores"]["123456789"]["goodfaith"]["score"]["prediction"]
confidence = result["enwiki"]["scores"]["123456789"]["goodfaith"]["score"]["probability"]["true"]

# Modern models use a flat output structure — see per-model SOPs below
```

---

## SOP: Revert Risk Scoring (Anti-Vandalism)

The `revertrisk-*` models are the **recommended** replacement for the older `goodfaith` + `damaging` pair. They provide a single probability score for whether an edit will be reverted.

### Language-Agnostic Revert Risk

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-language-agnostic:predict"
data = {"rev_id": 123456789, "lang": "en"}

resp = requests.post(url, json=data, headers=headers, timeout=30)
result = resp.json()
# result["output"]["prediction"] is a bool (false = safe, true = likely reverted)
# result["output"]["probabilities"]["true"] is a float 0.0–1.0
```

### Multilingual Revert Risk

Same pattern, different model name — covers 300+ languages with a single model:

```python
url = "https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-multilingual:predict"
data = {"rev_id": 123456789, "lang": "en"}
```

### Threshold Guidance

| Revert Risk Score | Action |
|-------------------|--------|
| `< 0.3` | Low risk — pass through |
| `0.3 – 0.7` | Medium risk — flag for human review |
| `> 0.7` | High risk — escalate (tag, auto-revert if confident) |

Calibrate thresholds to your tool's precision/recall requirements. The model card provides precision-recall curves: [Language-agnostic revert risk model card](https://meta.wikimedia.org/wiki/Machine_learning_models/Language-agnostic_revert_risk).

> 🎮 **Try it:** `python3 assets/patrol_simulator.py Albert_Einstein` — simulates patrolling the latest edit and produces a verdict.

---

## SOP: Article Quality Scoring

### With Revscoring Model (Frozen — uses ORES response format)

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-articlequality:predict"
data = {"rev_id": 123456789}

resp = requests.post(url, json=data, headers=headers, timeout=30)
result = resp.json()
scores = result["enwiki"]["scores"]["123456789"]["articlequality"]["score"]
grade = scores["prediction"]          # "FA", "GA", "B", "C", "Start", "Stub"
probs = scores["probability"]         # {"FA": 0.0, "GA": 0.12, "B": 0.02, ...}
```

> 💡 The modern `articlequality` model provides a **continuous quality score** (float 0–1), while the Revscoring `{wiki}-articlequality` model provides a **discrete grade** (FA/GA/B/C/Start/Stub). The modern model name is just `articlequality` — not `articlequality-language-agnostic`.

### Integration with Page Assessment

Combine ML quality scores with WikiProject assessment data from the **[wikimedia-page-assessment](../wikimedia-page-assessment/SKILL.md)** skill:

```python
# ML quality — available for any wiki
ml_grade = scores["prediction"]

# WikiProject quality — only for wikis with PageAssessments (enwiki, frwiki, etc.)
# query: SELECT pa_class FROM page_assessments WHERE pa_page_id = {page_id}
```

Use ML scores as a **fallback** when PageAssessments are not available (most wikis don't have the extension), or as a second opinion for unassessed articles.

> 🎮 **Try it:** `python3 assets/article_quality_report.py Albert_Einstein en` — generates a full report with quality + readability + topics + reference risk.

---

## SOP: Topic Classification

The `outlink-topic-model` replaces the older `articletopic` model. It uses the article's outlinks to predict topics and is available for more wikis.

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://api.wikimedia.org/service/lw/inference/v1/models/outlink-topic-model:predict"
data = {"page_title": "Douglas_Adams", "lang": "en"}

resp = requests.post(url, json=data, headers=headers, timeout=30)
result = resp.json()
# result["prediction"]["results"] is an array of {topic, score} objects:
# [
#   {"topic": "STEM.STEM*", "score": 0.90},
#   {"topic": "Culture.Biography.Biography*", "score": 0.73},
#   ...
# ]
topics = {r["topic"]: r["score"] for r in result["prediction"]["results"]}
```

### Topic Hierarchy

The outlink topic model uses a hierarchical taxonomy. Topics are dot-separated paths (e.g., `Culture.Media.Books`, `STEM.Science.Physics`). The top-level categories are:

| Top-Level | Examples |
|-----------|----------|
| `Culture` | Media, Books, Television, Music, Sports, Food |
| `Geography` | Regions, Countries, Cities |
| `History` | Events, People, Periods |
| `People` | Biographical topics |
| `STEM` | Science, Technology, Engineering, Mathematics |
| `Society` | Law, Education, Politics, Religion |

Interpret scores by their top-level prefix for broad categorization, or drill into subcategories for fine-grained classification.

> 🎮 **Try it:** `bash scripts/playground.sh` and choose option 4 — interactive topic classification.

---

## SOP: Readability Scoring

The `readability` model scores how readable an article's content is using standard metrics.

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://api.wikimedia.org/service/lw/inference/v1/models/readability:predict"
data = {"rev_id": 123456789, "lang": "en"}

resp = requests.post(url, json=data, headers=headers, timeout=30)
result = resp.json()
# Takes rev_id (not page_title). Returns:
# result["output"]["score"] is a float 0–1 readability score
# result["output"]["fk_score_proxy"] approximates Flesch-Kincaid grade level
score = result["output"]["score"]
grade = result["output"]["fk_score_proxy"]
```

### Interpreting Readability Scores

| Field | Range | Interpretation |
|-------|-------|----------------|
| `output.score` | 0–1 | Higher = more readable. >0.6 = accessible. <0.3 = very difficult. |
| `output.fk_score_proxy` | 0–20+ | US grade level (approximate). 8–10 = average adult. >14 = complex academic text. |

> 🎮 **Try it:** `python3 assets/article_quality_report.py Albert_Einstein en` includes a readability section.

---

## SOP: Reference Quality Scoring

Two models help assess citation quality in articles. Both use `rev_id` + `lang` (not `page_title`).

### Reference Need (Find Unsourced Claims)

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://api.wikimedia.org/service/lw/inference/v1/models/reference-need:predict"
data = {"rev_id": 123456789, "lang": "en"}

resp = requests.post(url, json=data, headers=headers, timeout=30)
result = resp.json()
# Returns a single reference_need_score (float 0–1), not per-sentence breakdown:
# result["reference_need_score"] — higher = more claims need citations
# result["model_version"] — model version
score = result["reference_need_score"]
```

### Reference Risk (Citation Quality)

```python
url = "https://api.wikimedia.org/service/lw/inference/v1/models/reference-risk:predict"
data = {"rev_id": 123456789, "lang": "en"}

resp = requests.post(url, json=data, headers=headers, timeout=30)
result = resp.json()
# Returns:
# result["reference_risk_score"] — float, higher = riskier citations
# result["reference_count"] — int, number of references in the revision
# result["survival_ratio"] — dict with min/mean/median citation survival
risk = result["reference_risk_score"]
ref_count = result["reference_count"]
```

---

## SOP: Language Identification

The `langid` model predicts what language a piece of text is written in. It takes **raw text** (not a page reference).

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://api.wikimedia.org/service/lw/inference/v1/models/langid:predict"
data = {"text": "Albert Einstein was a German-born theoretical physicist."}

resp = requests.post(url, json=data, headers=headers, timeout=30)
result = resp.json()
# result["wikicode"] is the language code, e.g., "en"
# result["score"] is the confidence (float 0–1)
# result["language"] is the full language name, e.g., "English"
# result["languagename"] is an alternative name
```

To get the text of a Wikipedia article for language identification, first fetch the page content via the [REST API](../wikimedia-api-access/SKILL.md).

> 🎮 **Try it:** `python3 assets/language_explorer.py` — interactive REPL. Type any text and see the detected language. Or `python3 assets/language_explorer.py --samples` to test 10 languages at once.

---

## SOP: Article Country Prediction

The `article-country` model predicts which countries an article is about, with confidence scores and evidence sources.

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://api.wikimedia.org/service/lw/inference/v1/models/article-country:predict"
data = {"title": "Albert_Einstein", "lang": "en"}

resp = requests.post(url, json=data, headers=headers, timeout=30)
result = resp.json()
# result["prediction"]["results"] is an array sorted by score (descending):
# [
#   {"country": "United States", "score": 1.0, "source": {"wikidata_properties": [...], "categories": [...]}},
#   {"country": "Switzerland", "score": 0.67, "source": {...}},
#   ...
# ]
top_country = result["prediction"]["results"][0]["country"]
all_countries = {r["country"]: r["score"] for r in result["prediction"]["results"]}
```

Note: uses `title` (not `page_title`) as the parameter name.

---

## SOP: Content Translation Recommendations

The content translation recommendation is a **GET-based REST API** (not a POST inference model).

```python
import requests

headers = {"User-Agent": "MyBot/1.0 (user@example.com) ContentGapResearch"}
url = "https://api.wikimedia.org/service/lw/recommendation/api/v1/translation"
params = {
    "source": "en",       # Source wiki language code
    "target": "fr",       # Target wiki language code
    "count": 3,            # Number of recommendations (default 12)
    "seed": "Apple",      # Seed article for personalized recommendations
}

resp = requests.get(url, params=params, headers=headers, timeout=30)
result = resp.json()
# result["recommendations"] is an array of:
# {"title": "Flamenco (apple)", "pageviews": 0, "wikidata_id": "Q19597233",
#  "rank": 7, "langlinks_count": 1, "size": 6871, ...}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source` | string | ✅ | Source wiki language code (e.g., `en`) |
| `target` | string | ✅ | Target wiki language code (e.g., `fr`) |
| `count` | int | ❌ | Number of recommendations (default `12`) |
| `seed` | string | ❌ | Seed article title for personalized recommendations (pipe `|`-separated for multiple) |
| `topic` | string | ❌ | Article topic filter (pipe `|`-separated) |
| `include_pageviews` | bool | ❌ | Include pageview counts (`true`/`false`, default `false`) |
| `search_algorithm` | string | ❌ | `morelike` or `mostpopular` (default `morelike`) |

---

## SOP: Migrating from ORES (Legacy Code)

If you encounter code that calls ORES, here is the migration pattern:

### ORES Call (Legacy)
```bash
# ORES — GET, batch multiple models in one call
curl -s -H "User-Agent: MyBot/1.0 (user@example.com) LiftWingMigration" \
  'https://ores.wikimedia.org/v3/scores/enwiki/12345?models=goodfaith|damaging'
```

### Equivalent Lift Wing Calls
```bash
# Lift Wing — POST, one call per model
curl -s -X POST -H "User-Agent: MyBot/1.0 (user@example.com) LiftWingMigration" \
  'https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-goodfaith:predict' \
  -H 'Content-Type: application/json' \
  -d '{"rev_id": 12345}'
curl -s -X POST -H "User-Agent: MyBot/1.0 (user@example.com) LiftWingMigration" \
  'https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-damaging:predict' \
  -H 'Content-Type: application/json' \
  -d '{"rev_id": 12345}'
```

### ORES → Lift Wing Feature Extraction
```bash
# ORES could return features with ?features=True
curl -s -H "User-Agent: MyBot/1.0 (user@example.com) LiftWingMigration" \
  'https://ores.wikimedia.org/v3/scores/enwiki/12345/goodfaith?features=True'

# Lift Wing equivalent
curl -s -X POST -H "User-Agent: MyBot/1.0 (user@example.com) LiftWingMigration" \
  'https://api.wikimedia.org/service/lw/inference/v1/models/enwiki-goodfaith:predict' \
  -H 'Content-Type: application/json' \
  -d '{"rev_id": 12345, "extended_output": "True"}'
```

### ORES → Modern Revert Risk
```bash
# Old: two calls for goodfaith + damaging
curl -s -H "User-Agent: MyBot/1.0 (user@example.com) LiftWingMigration" \
  'https://ores.wikimedia.org/v3/scores/enwiki/12345?models=goodfaith|damaging'

# New: single call to revertrisk with language parameter
curl -s -X POST -H "User-Agent: MyBot/1.0 (user@example.com) LiftWingMigration" \
  'https://api.wikimedia.org/service/lw/inference/v1/models/revertrisk-language-agnostic:predict' \
  -H 'Content-Type: application/json' \
  -d '{"rev_id": 12345, "lang": "en"}'
```

### Key ORES → Lift Wing Differences

| Aspect | ORES | Lift Wing |
|--------|------|-----------|
| HTTP method | GET | POST |
| Batch support | Yes (multiple models, multiple revisions in one call) | No (one model per call) |
| Caching | Yes (pre-cached scores for recent edits) | **No** (must implement your own cache) |
| Features | `?features=True` | `"extended_output": "True"` (per model) |
| Auth | None | OAuth for higher rate limits |
| Response | `{"wiki": {"models": {"model": {"scores": {...}}}}}` | Per-model response (see individual SOPs) |

---

## SOP: Implementing Caching (Lift Wing Has None)

Lift Wing does **not** cache predictions (unlike ORES which pre-cached scores). If you score the same revision twice, you pay two inference calls. For production tools, implement your own cache:

```python
import time

class MLScoreCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._cache = {}
        self._ttl = ttl_seconds
    
    def get(self, model: str, rev_id: int) -> dict | None:
        key = (model, rev_id)
        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["ts"] < self._ttl:
                return entry["data"]
            del self._cache[key]
        return None
    
    def set(self, model: str, rev_id: int, data: dict):
        self._cache[(model, rev_id)] = {"data": data, "ts": time.time()}

# Usage
cache = MLScoreCache()

def scored_revision(wiki, rev_id):
    cached = cache.get(f"{wiki}-goodfaith", rev_id)
    if cached:
        return cached
    result = call_liftwing(f"{wiki}-goodfaith", {"rev_id": rev_id})
    cache.set(f"{wiki}-goodfaith", rev_id, result)
    return result
```

---

## Guardrails

### ❌ Don't use ORES for new tools
ORES is **deprecated**. Always use Lift Wing. The ORES service could stop working at any time without notice.

### ❌ Don't use frozen Revscoring models when modern alternatives exist
- Use `revertrisk-*` instead of `goodfaith` + `damaging`
- Use `outlink-topic-model` instead of `articletopic`

The frozen models won't be retrained, won't gain new language support, and their accuracy degrades over time (model drift).

### ❌ Don't assume all models cover all wikis
Revscoring models only cover the wikis they were trained on. Check the [model list](https://wikitech.wikimedia.org/wiki/Machine_Learning/LiftWing#Revscoring_models_(migrated_from_ORES)) before using a wiki-specific model. Modern models (`revertrisk-multilingual`, `outlink-topic-model`) are language-agnostic and cover more wikis.

### ❌ Don't ignore model cards
Every model has a model card on Meta-Wiki that documents:
- Training data and methodology
- Performance metrics (precision, recall, F1)
- Known biases and limitations
- Appropriate use cases

Read the model card before using a model in production. Links are in the reference table below.

### ⚠️ Implement caching for repeated scoring
Since Lift Wing has no caching, scoring the same revision multiple times wastes rate limit quota and adds latency. Use an in-memory cache (as shown above) for short-lived tools, or a persistent cache (Redis, SQLite) for long-running services.

### ⚠️ Respect per-second rate limits, not just per-hour
The per-second limits (15 req/s anonymous, 100 req/s authenticated) are tighter than the per-hour limits. For batch operations:
- Add `time.sleep(0.1)` between requests (10 req/s)
- Use `requests.Session()` for connection reuse
- Implement exponential backoff on 429 responses

### ⚠️ Some models are internal-only
Models in the "experimental" Kubernetes namespace are only accessible from WMF production infrastructure. The externally accessible models are documented in the [API reference](https://api.wikimedia.org/wiki/Lift_Wing_API/Reference). If a model is not listed there, it's internal.

---

## Model Card Reference

| Model | Model Card |
|-------|------------|
| Language-agnostic revert risk | [Model card](https://meta.wikimedia.org/wiki/Machine_learning_models/Language-agnostic_revert_risk) |
| Multilingual revert risk | [Model card](https://meta.wikimedia.org/wiki/Machine_learning_models/Multilingual_revert_risk) |
| RevertRisk Wikidata | [Model card](https://meta.wikimedia.org/wiki/Machine_learning_models/RevertRisk_Wikidata) |
| Outlink-based article topic | [Model card](https://meta.wikimedia.org/wiki/Machine_learning_models/Language_agnostic_link-based_article_topic_model) |
| Article descriptions | [Model cards (description generation)](https://meta.wikimedia.org/wiki/Machine_learning_models) |
| Logo detection | [Model card](https://meta.wikimedia.org/wiki/Machine_learning_models/Logo_detection) |

---

## Known Limitations

| Limitation | Affected Models | Impact | Workaround |
|------------|:---------------:|--------|------------|
| **Revert-risk models return HTTP 422 for revision 1.** New pages have no parent revision to compare against, so the model cannot compute a score. | `revertrisk-language-agnostic`, `revertrisk-multilingual`, `revertrisk-wikidata` | Cannot score brand-new page creations — a common use case for real-time patrol tools. | Use the `articlequality` model as a fallback for new pages (it scores the revision itself, not the diff). Note that `articlequality` has ~60s processing latency (see below). |
| **Articlequality model has ~60s processing latency.** Newly created revisions are not immediately available for scoring. The model returns empty scores for revisions less than ~60 seconds old. | `articlequality`, `{wiki}-articlequality` | Real-time patrol tools may get empty scores for very new pages. | Retry with exponential backoff (max 3 attempts, 30s apart). Or accept the empty score as "unknown" and re-score later. |
| **Lift Wing has no prediction cache.** Unlike ORES (which pre-computed scores), every call to Lift Wing runs a fresh inference. | All models | Scoring the same revision twice wastes rate limit quota and doubles latency. Risk: rate limit exhaustion in batch operations. | Implement your own cache (see [SOP: Implementing Caching](#sop-implementing-caching-lift-wing-has-none)). Use an LRU cache with TTL for short-lived tools, Redis/SQLite for persistent services. |
| **Revscoring models are frozen — no retraining.** The `{wiki}-goodfaith`, `{wiki}-damaging`, `{wiki}-articlequality` etc. models are ported from ORES with no further updates. | All Revscoring models (`{wiki}-*`) | Model accuracy degrades over time (model drift). No new language coverage. | Migrate to modern models (`revertrisk-*`, `articlequality` continuous, `outlink-topic-model`) where available. Check the [model list](https://wikitech.wikimedia.org/wiki/Machine_Learning/LiftWing#Revscoring_models_(migrated_from_ORES)) for coverage. |
| **Not all models cover all wikis.** Revscoring models only work on the wikis they were trained on. | `{wiki}-*` Revscoring models | Calling a model with an unsupported wiki returns a 404 or empty prediction. | Check the [model list](https://wikitech.wikimedia.org/wiki/Machine_Learning/LiftWing#Revscoring_models_(migrated_from_ORES)) before using a wiki-specific model. Use language-agnostic modern models for broader coverage. |
| **Per-second rate limits are tighter than per-hour.** Anonymous: 15 req/s. Authenticated: 100 req/s. Batch operations can hit the per-second limit before the per-hour limit. | All models | 429 errors during batch scoring. | Add `time.sleep(0.1)` between requests (10 req/s). Use `requests.Session()` for connection reuse. Implement exponential backoff on 429. Authenticate via OAuth for 100 req/s. |
| **Some models are internal-only.** Models in the "experimental" Kubernetes namespace are not accessible from external clients. | Varies | 403/404 errors when calling models not in the public API. | Only use models listed in the [public API reference](https://api.wikimedia.org/wiki/Lift_Wing_API/Reference). |
| **`article-descriptions` model is heavy and slow.** Generating a short description is computationally expensive due to the beam search pattern. | `article-descriptions` | Requests can take 10-30 seconds or timeout. | Use `num_beams=1` for faster (but lower quality) results. Increase HTTP timeout to 60s. |

---

## Tooling

### 🔧 CLI Scripts

| Script | Purpose | Usage Example |
|--------|---------|---------------|
| [`scripts/score-revision.sh`](./scripts/score-revision.sh) | Score a single revision or page via curl | `./score-revision.sh enwiki 123456789 revertrisk-language-agnostic en` |
| [`scripts/batch-score.sh`](./scripts/batch-score.sh) | Batch score multiple revisions from stdin or a file | `cat revids.txt \| ./batch-score.sh enwiki revertrisk-multilingual --output csv` |
| [`scripts/playground.sh`](./scripts/playground.sh) | **Interactive menu** — pick a model, enter input, see results. No arguments to memorize | `bash scripts/playground.sh` |

### 🐍 Python Assets

| Script | Purpose | Usage Example |
|--------|---------|---------------|
| [`assets/liftwing_multi_model.py`](./assets/liftwing_multi_model.py) | Score a revision against multiple models in parallel with caching | `python3 liftwing_multi_model.py enwiki 123456789 --all` |
| [`assets/article_quality_report.py`](./assets/article_quality_report.py) | Full article report: quality + readability + topics + reference need | `python3 article_quality_report.py Albert_Einstein en` |
| [`assets/patrol_simulator.py`](./assets/patrol_simulator.py) | **Simulate patrolling** — score the latest edit to a page with revert-risk + goodfaith + damaging, get a verdict | `python3 patrol_simulator.py Albert_Einstein` |
| [`assets/language_explorer.py`](./assets/language_explorer.py) | **Language explorer** — type text and see what language langid detects, with confidence | `python3 language_explorer.py --samples` (built-in test suite in 10 languages) |

### 📚 Reference Docs

| Document | Contents |
|----------|----------|
| [`references/model-schemas.md`](./references/model-schemas.md) | Complete request/response schema for all 15+ externally accessible models, available wikis per model, and rate limit tables |

> 💡 The code examples in the SOPs above are self-contained and ready to copy-paste.
> The scripts and assets add CLI convenience, batch processing, and production patterns.
