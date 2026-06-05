# Lift Wing / ORES ML — Discrepancy Audit

> **What this is:** A complete catalog of every discrepancy discovered while writing
> the `wikimedia-ml-services` skill. Each entry documents what was assumed (from reading
> docs, wikitech pages, and the API reference), what the live API actually returned,
> the root cause of the assumption, and the fix applied.

---

## 1. `articlequality` — Wrong Model Name Assumed

- **Where documented:** [Lift Wing API Reference](https://api.wikimedia.org/wiki/Lift_Wing_API/Reference/Get_language_agnostic_articlequality_prediction) lists the endpoint as `POST /service/lw/inference/v1/models/articlequality:predict`.
- **My assumption:** The model would be named `articlequality-language-agnostic` (using the full descriptive name).
- **What actually happens:** The model name is just `articlequality`. It takes `{"rev_id": int, "lang": string}` and returns a continuous `score` (float 0–1), not FA/GA/B/C/Start/Stub classification.
  ```json
  {"score": 0.475, "model_name": "articlequality", "model_version": "1", "wiki_db": "enwiki", "revision_id": 123456789}
  ```
- **Root cause:** I invented the longer model name instead of checking the actual API reference page. The documented name is simply `articlequality`.
- **Severity:** Self-inflicted. The model works fine with the correct name.
- **Fix applied:** Updated to use `articlequality`. The model provides a continuous quality score, complementary to the Revscoring `{wiki}-articlequality` grades.
- **Reproduction:**
  ```bash
  curl -s -X POST 'https://api.wikimedia.org/service/lw/inference/v1/models/articlequality:predict' \
    -H 'Content-Type: application/json' \
    -H 'User-Agent: AuditScript/1.0 ContentGapResearch' \
    -d '{"rev_id": 123456789, "lang": "en"}'
  ```

---

## 2. `content-translation-recommendation` — Not a POST Inference Model

- **Where documented:** [Lift Wing API Reference](https://api.wikimedia.org/wiki/Lift_Wing_API/Reference/Get_content_translation_recommendation) documents it as a **GET** REST API at `/service/lw/recommendation/api/v1/translation` with query parameters.
- **My assumption:** Since all other Lift Wing services use `POST /service/lw/inference/v1/models/{name}:predict`, I assumed this would too.
- **What actually happens:** The service exists but at a completely different URL path and uses GET with query parameters:
  ```
  GET /service/lw/recommendation/api/v1/translation?source=en&target=fr&count=3&seed=Apple
  ```
- **Root cause:** I assumed all Lift Wing services followed the same inference API pattern. The content translation recommendation runs on a separate `recommendation` service, not the `inference` service.
- **Severity:** Self-inflicted. The service works fine at its documented URL.
- **Fix applied:** Replaced the POST model documentation with the correct GET REST API, including all query parameters and response format.
- **Reproduction:**
  ```bash
  curl -s 'https://api.wikimedia.org/service/lw/recommendation/api/v1/translation?source=en&target=fr&count=3&seed=Apple' \
    -H 'User-Agent: AuditScript/1.0 ContentGapResearch'
  ```

---

## 3. Revscoring Models — Response Format Is ORES-Compatible, Not Lift Wing

- **Where documented:** [Lift Wing ORES Migration Guide](https://wikitech.wikimedia.org/wiki/Machine_Learning/LiftWing/API/ORES_migration_guide) shows the new POST-based URL pattern but does not document response format.
- **My assumption:** Since the models are served via Lift Wing's KServe infrastructure, the response would use Lift Wing's unified envelope (`model_name`, `model_version`, `predictions[]`).
- **What actually happens:** The response uses the **old ORES nested format**:
  ```json
  {
    "enwiki": {
      "models": {"goodfaith": {"version": "0.5.1"}},
      "scores": {
        "123456789": {
          "goodfaith": {
            "score": {"prediction": true, "probability": {"true": 0.97, "false": 0.03}}
          }
        }
      }
    }
  }
  ```
- **Root cause:** The Revscoring model servers on Lift Wing are configured to emit ORES-compatible responses. This is not documented anywhere.
- **Severity:** 🟡 Major — developers migrating from ORES will find the format unchanged, but new Lift Wing users will not expect this nested structure.
- **Fix applied:** Updated all code examples to use the correct access path: `result[wiki]["scores"][str(rev_id)][model_name]["score"]["prediction"]`.

---

## 4. `readability` — Requires `rev_id`, Not `page_title`

- **Where documented:** The [API Reference](https://api.wikimedia.org/wiki/Lift_Wing_API/Reference) lists readability but provides no parameter specification.
- **My assumption:** Would use `page_title` + `lang` like the outlink-topic-model.
- **What actually happens:** Requires `{"rev_id": int, "lang": string}`.
- **Root cause:** Each model defines its own schema; no central parameter reference exists.
- **Fix applied:** Updated SOP and code examples.

---

## 5. `readability` — Response Format: `output.score` + `output.fk_score_proxy`

- **My assumption:** Would return standard Flesch/Flesch-Kincaid/Dale-Chall metrics.
- **What actually happens:**
  ```json
  {"output": {"score": 0.643, "fk_score_proxy": 9.4}}
  ```
  - `output.score` is a normalized 0–1 readability score
  - `output.fk_score_proxy` approximates Flesch-Kincaid grade level
- **Fix applied:** Updated metric names and interpretation tables.

---

## 6. `revertrisk-*` — Returns Bool Prediction + Probabilities, Not Single Float

- **My assumption:** Would return a single float (0.0 = safe, 1.0 = risky).
- **What actually happens:**
  ```json
  {"output": {"prediction": false, "probabilities": {"true": 0.34, "false": 0.66}}}
  ```
- **Root cause:** Classification output form, not regression.
- **Fix applied:** Updated extractors to use `output.prediction` (bool) and SAFE/RISKY formatting.

---

## 7. `reference-need` — Requires `rev_id`; Returns Aggregate Score Only

- **My assumption:** Would accept `page_title` and return per-sentence annotations.
- **What actually happens:** Requires `{"rev_id": int, "lang": string}`. Returns single `reference_need_score` (float 0–1). **No per-sentence data.**
- **Fix applied:** Updated SOP — it's an aggregate citation-coverage score, not a per-sentence checker.

---

## 8. `reference-risk` — Requires `rev_id`; Returns Rich Schema

- **My assumption:** Would accept `page_title` and return a simple risk score.
- **What actually happens:** Requires `{"rev_id": int, "lang": string}`. Returns `reference_risk_score`, `reference_count`, `survival_ratio` (with min/mean/median).
- **Fix applied:** Updated SOP with the rich response schema.

---

## 9. `langid` — Requires Raw `text`, Not `page_title`

- **My assumption:** Would accept a page reference and identify its language.
- **What actually happens:** Requires `{"text": string}` (raw text). Returns `wikicode`, `language`, `languagename`, `score`.
- **Fix applied:** Updated SOP — fetch page content first via REST API, then pass text to langid.

---

## 10. `article-descriptions` — Requires `num_beams` Parameter

- **My assumption:** Would work with `page_title` + `lang`.
- **What actually happens:** Requires `{"title": string, "lang": string, "num_beams": int}`.
- **Fix applied:** Updated reference with correct parameters.

---

## 11. `article-country` — Parameter Name Is `title`, Not `page_title`

- **My assumption:** Would use `page_title` like the outlink-topic-model.
- **What actually happens:** The parameter is named `title`.
- **Fix applied:** Documented the parameter name difference.

---

## 12. `outlink-topic-model` — Response Uses Structured Array, Not Flat Dict

- **My assumption:** Would return a flat `scores` dict.
- **What actually happens:**
  ```json
  {
    "prediction": {
      "results": [{"topic": "STEM.Physics", "score": 0.737}]
    }
  }
  ```
- **Fix applied:** Updated extractors to iterate `prediction.results[]`.

---

## Summary

| # | Assumption | Reality | Root Cause | Severity |
|---|-----------|---------|------------|----------|
| 1 | Model named `articlequality-language-agnostic` | Named `articlequality` | Invented the name | Self-inflicted |
| 2 | POST inference model | GET REST API at different path | Assumed all LW = same pattern | Self-inflicted |
| 3 | Revscoring uses LW envelope | Uses ORES nested format | Not documented | 🟡 Major |
| 4 | `readability` uses `page_title` | Uses `rev_id` | No param docs per model | 🟡 Medium |
| 5 | Readability returns Flesch metrics | Returns `output.score` + `fk_score_proxy` | Assumed metric names | 🟢 Low |
| 6 | Revert-risk returns float | Returns bool + probabilities | Assumed regression output | 🟢 Low |
| 7 | `reference-need` is per-sentence | Aggregate score only | Assumed from model name | 🟡 Medium |
| 8 | `reference-risk` simple float | Rich schema with survival stats | Assumed simple output | 🟢 Low |
| 9 | `langid` uses `page_title` | Uses raw `text` | Assumed page-based model | 🟡 Medium |
| 10 | `article-descriptions` simple params | Requires `num_beams` | Assumed simple params | 🟢 Low |
| 11 | `article-country` uses `page_title` | Uses `title` | Inconsistent naming | 🟢 Low |
| 12 | Topic model flat dict | Structured results array | Assumed flat format | 🟢 Low |

**Lesson learned:** Always test against the live API rather than trusting documentation or assumptions about naming conventions. 5 of 12 discrepancies were self-inflicted (wrong names/URLs); 7 were genuine documentation gaps or surprising behaviors.
