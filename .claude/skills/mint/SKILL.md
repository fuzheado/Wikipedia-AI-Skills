---
name: mint
description: "Translate text and rich content via MinT — the Wikimedia machine translation service: 200+ languages, open NMT models (NLLB-200, OpusMT, IndicTrans2), plain/HTML/JSON/markdown formats"
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["machine translation", "translate text", "mint", "language translation", "NLLB", "translate to spanish"]
  - keywords: ["content translation", "translate article", "translatewiki", "section translation", "automatic translation"]
  - keywords: ["translation API", "multilingual", "translate page", "translatewiki.net"]
last_verified: 2026-08-17
---

> ⚠️ **User-Agent required:** All requests below require a descriptive `User-Agent` header. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

MinT (**M**achine **in** **T**ranslation) is the Wikimedia Foundation Language team's open-source machine translation service. It runs open NMT models — **NLLB-200** (Meta), **OpusMT** (Helsinki), **IndicTrans2** (AI4Bharat), **Softcatalà**, **MADLAD-400** (Google) — optimized with CTranslate2 to run on **CPU (no GPU needed)**. It supports **200+ languages, including 70+ no other service covers and 25+ with no Wikipedia yet**. MinT powers machine translation inside Content Translation, Section Translation, and translatewiki.net.

**When to use MinT:** when the task is *translation* — "translate this article/sentence to Spanish", "what does this text say in Arabic?", "produce a localized version of this content", or translating structured content (HTML/JSON/markdown) while preserving markup. No other skill in this catalog provides machine translation.

**⚠️ Test instance vs. production:** `translate.wmcloud.org` is the public **test instance** — fine for experiments, benchmarks, and low-volume use, but the docs warn performance and availability "may be reduced" compared to the production instances that serve Content Translation. Treat benchmark numbers (below) as lower bounds for production.

## API Basics

- **Base URL:** `https://translate.wmcloud.org` — FastAPI service. **Docs:** `/docs` (Swagger UI) and `/openapi.json` (machine-readable spec).
- **⚠️ `/api` alone returns 404.** The real endpoints are `POST /api/translate`, `GET /api/languages`, and `GET /healthz`. Do not guess paths — consult `/openapi.json`.
- **Request body** (`POST /api/translate`, JSON): `content` (text to translate), `source_language`, `target_language` (2-letter codes; `auto` is not supported — detect language first, see Cross-References), `provider` (optional; defaults to the first matching model for the pair), `format` (one of `html`, `json`, `markdown`, `text`, `svg`, `webpage`).
- **⚠️ Field names are `content`/`source_language`/`target_language`** — NOT `text`/`from`/`to`. Using the wrong names returns **422** with a list of missing fields.
- **Response:** `translation` (translated text), `translationtime` (seconds), `sourcelanguage`, `targetlanguage`, `model` (which model served it).
- **Etiquette:** synchronous requests, ≥1s pacing between calls. Inference is CPU-bound: ~30–100 words/s per request, and latency grows under concurrency — do not parallelize.

**Quick smoke test:**

```bash
curl -s -X POST "https://translate.wmcloud.org/api/translate" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName" \
  -H "Content-Type: application/json" \
  -d '{"content":"Jazz is a music genre that originated in New Orleans.","source_language":"en","target_language":"es","format":"text"}'
# {"translation":"El jazz es un género musical que se originó en Nueva Orleans.",
#  "translationtime":0.49,"sourcelanguage":"en","targetlanguage":"es","model":"nllb200-600M"}
```

## SOP: Discover Languages and Providers

`GET /api/languages` returns a map of `target_language → source_language → [available models]`:

```bash
curl -s "https://translate.wmcloud.org/api/languages" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName"
# {"as":{"en":["indictrans2-indic-en","nllb200-600M"],"bn":["indictrans2-indic-indic","nllb200-600M"],...}}
```

**Always fetch this live before translating** — supported languages and models change as new models are added (fetch-on-demand; never hardcode the language list). A pair not in the map is not translatable, even if both languages exist individually.

## SOP: Translate Plain Text

```python
import requests

def translate(content, source, target, ua, provider=None, fmt="text"):
    body = {"content": content, "source_language": source,
            "target_language": target, "format": fmt}
    if provider:
        body["provider"] = provider
    r = requests.post("https://translate.wmcloud.org/api/translate",
                      json=body, headers={"User-Agent": ua}, timeout=60)
    r.raise_for_status()
    return r.json()["translation"]
```

- Omit `provider` to use the default model for the pair (preference order is defined by MinT's `config.yaml`).
- Pass `provider` explicitly when you need a specific model (e.g. `"nllb200-600M"` for broad coverage, `"indictrans2-indic-indic"` for Indic pairs). An invalid provider for the pair returns 422 — verify against `/api/languages` first.

## SOP: Translate Rich Content (Markup Preservation)

MinT transfers markup from source to translation for structured formats — HTML tags survive translation:

```bash
curl -s -X POST "https://translate.wmcloud.org/api/translate" \
  -H "User-Agent: MyBot/1.0 (me@example.com) ProjectName" \
  -H "Content-Type: application/json" \
  -d '{"content":"<p>Jazz is a <b>music genre</b> that originated in New Orleans.</p>","source_language":"en","target_language":"es","format":"html"}'
# {"translation":"<p>El jazz es un <b>género musical</b> que se originó en Nueva Orleans.</p>",...}
```

Supported formats: `html`, `json`, `markdown`, `text`, `svg`, `webpage`. Use `text` when the content is plain prose (fastest, no markup overhead); use `html`/`markdown`/`json` when you need the structure preserved in the output.

## Constraint & Guardrails

1. **The `/api` 404 trap.** The bare `/api` path returns 404 — the real endpoints are `POST /api/translate` and `GET /api/languages`. When in doubt, read `/openapi.json` — never guess paths.
2. **The field-name trap.** The body fields are `content`, `source_language`, `target_language` (plus optional `provider`, `format`). Using `text`/`from`/`to` returns 422. The 422 error lists exactly which fields are missing — read it and fix, don't retry blindly.
3. **Provider must match the pair.** Check `/api/languages` for the pair's model list before passing `provider`; an unsupported provider or pair returns 422.
4. **Test-instance performance.** Measured 2026-08-17: ~0.6s for 16 words, ~1.3–4.4s for 101 words (pair-dependent; `en→hi` slowest), ~4s for 400 words; throughput ~28–101 words/s. Aggregate throughput **degrades** under concurrency (0.9 → 0.4 req/s at 1 → 8 parallel) — the instance is CPU-bound. Keep requests synchronous with ≥1s pacing.
5. **Licensing & accuracy.** Translations are derivative works under the source content's CC-BY-SA license; MinT makes no accuracy warranties (see the [MinT disclaimer](https://www.mediawiki.org/wiki/MinT#Disclaimer)). Machine output must be reviewed before publishing anywhere.
6. **Privacy.** Only freely-licensed content is sent; no nonpublic user information (per the [MinT service FAQ](https://www.mediawiki.org/wiki/Content_translation/Machine_Translation/MinT)).
7. **Freshness.** Language/model support changes as new models are added — always fetch `/api/languages` live and re-verify this skill's facts periodically (bump `last_verified`).
8. **Health first.** If requests fail, check `GET /healthz` (200 = up) before retrying; a 422 means your request is wrong, a 503 means the service is overloaded — back off.

## Example Use Cases

* "Translate this article's lead section to Spanish and show me the result" (`text` or `html` format)
* "Localize this tool's UI strings from English to Arabic" (translate each string via `text`; or `json` for structured message files)
* "Summarize what this Catalan Wikipedia article says" — translate to English first, then summarize
* "Which model can translate Xhosa, and does MinT support it at all?" (`/api/languages` lookup)
* "Produce a machine-translated first draft for a new Wikipedia article, clearly marked as unedited MT" (Content Translation workflow pattern)

## Tooling

### 🔧 Translation CLI (`scripts/translate.py`)

Stdlib-only command-line client for MinT:

```bash
python3 scripts/translate.py "Jazz is a music genre." en es          # plain text
python3 scripts/translate.py --file article.md --format markdown en fr
python3 scripts/translate.py --list-languages en                     # what can 'en' translate into?
python3 scripts/translate.py "Hello world" en hi --provider indictrans2-indic-en
```

### 🧪 Tests (`../../tests/test_mint.py`)

Content-anchor tests (no network) verifying the documented facts, traps, and cross-references in this skill.

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent header and request patterns for all calls |
| **[wikimedia-api-strategy](../wikimedia-api-strategy/SKILL.md)** | Choosing between APIs — MinT is the translation surface; the Action/REST APIs have no translation endpoint |
| **[wikimedia-ml-services](../wikimedia-ml-services/SKILL.md)** | Language identification (Lift Wing) — MinT has no `auto` source-language detection, so detect the language first |
| **[wikimedia-i18n-l10n-for-tools](../wikimedia-i18n-l10n-for-tools/SKILL.md)** | Localizing tools — MinT provides the raw translation; i18n covers message files and conventions |
