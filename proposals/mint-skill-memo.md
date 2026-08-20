# MinT (Machine in Translation) API — Skill Research Memo

**Date:** 2026-08-17
**Author:** Hermes agent research for Andrew Lih (User:Fuzheado)
**Status:** Proposed — add as T2 skill; this memo is the durable rationale + evidence record
**Related PR:** feat/mint (skill: `.claude/skills/mint/`)

---

## 1. Motivation

Evaluate whether the MinT API (`translate.wmcloud.org`) deserves a standalone skill
in this catalog. MinT is the Wikimedia Foundation Language team's open-source neural
machine translation service — the engine behind machine translation in **Content
Translation** (which has produced **2M+ Wikipedia articles**), Section Translation,
and translatewiki.net. It runs open models (NLLB-200, OpusMT, IndicTrans2, Softcatalà,
MADLAD-400) optimized with CTranslate2 to run **on CPU without GPUs**, supporting
**200+ languages, including 70+ no other service covers and 25+ with no Wikipedia yet**.

No existing skill in the catalog provides machine translation; an agent asked to
"translate this to Spanish" has no correct path today (the Action/REST APIs have no
translation endpoint; agents would either guess at external services or invent
endpoints — a documented failure class).

## 2. API surface (small, 2 real endpoints)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/translate` | POST | Translate `content` from `source_language` to `target_language` (optional `provider`, `format`) |
| `/api/languages` | GET | Map of target → source → available models (fetch live; changes as models are added) |
| `/healthz` | GET | Health check |
| `/docs`, `/openapi.json` | GET | FastAPI Swagger UI + machine-readable spec |

Request body fields: `content`, `source_language`, `target_language`, `provider`
(optional), `format` (`html`, `json`, `markdown`, `text`, `svg`, `webpage`).
Response: `translation`, `translationtime`, `sourcelanguage`, `targetlanguage`, `model`.

⚠️ The bare path `/api` returns 404 — a classic silent-404 trap.
⚠️ Field names are `content`/`source_language`/`target_language` — using `text`/`from`/`to`
returns 422 with a missing-field list (verified live; see §4).

Source: [mediawiki.org/wiki/MinT](https://www.mediawiki.org/wiki/MinT),
`/openapi.json` at [translate.wmcloud.org/openapi.json](https://translate.wmcloud.org/openapi.json),
code: [wikimedia/mediawiki-services-machinetranslation](https://github.com/wikimedia/mediawiki-services-machinetranslation).

## 3. Capability analysis vs. the existing catalog

| Existing skill | Relationship | Detail |
|---|---|---|
| `wikimedia-api-access` | **Prerequisite** | UA header + request patterns (depends_on) |
| `wikimedia-api-strategy` | **Needs pointer** | MinT is the translation surface; no Action/REST translation endpoint exists |
| `wikimedia-ml-services` | **Complements** | Lift Wing language identification — MinT has no `auto` source detection, so detect language first |
| `wikimedia-i18n-l10n-for-tools` | **Complements** | i18n covers message-file conventions; MinT provides the raw translation |
| — | **New territory** | Machine translation, markup-preserving translation (`html`/`json`/`markdown`/`svg`/`webpage`), provider selection |

Verdict: **entirely new territory**; no overlap, no existing home.

## 4. Live measurements (2026-08-17, descriptive UA)

| Test | Result |
|---|---|
| `GET /api/languages` | 200 JSON (target→source→models map) |
| `GET /healthz` | 200 |
| `GET /docs`, `/openapi.json` | 200 |
| `POST /api/translate` (16 words en→es) | 200, median **0.58s** |
| `POST /api/translate` (101 words, en→es) | 200, median **1.27s** |
| `POST /api/translate` (404 words, en→es) | 200, median **4.0s** |
| 101 words en→de / fr / ar / hi / zh / sw | 2.3 / 2.8 / 2.7 / **4.4** / 1.3 / 2.3s |
| 101 words es→en / de→en | 1.8 / 1.7s |
| 101 words en→es via OpusMT | 2.2s |
| HTML format (markup preservation) | 200 — `<p>`/`<b>` preserved, 0.49s |
| JSON format | 200 — JSON structure preserved, 0.30s |
| Wrong field names (`text`/`from`/`to`) | **422** with missing-field list |
| Bare `/api` path | **404** `{"detail":"Not Found"}` |
| Concurrency 1 / 4 / 8 (101w en→es) | 0.9 / 0.6 / 0.4 req/s aggregate — **degrades** (CPU-bound) |
| Availability during test window | 42/42 requests succeeded |

**Throughput ~28–101 words/s** single-stream (en→hi slowest). The test instance is
CPU-bound and does not scale under parallel load — the skill encodes synchronous,
≥1s-pacing etiquette.

## 5. Documented operational limits

- **Test instance disclaimer:** `translate.wmcloud.org` is "intended for testing, so
  performance and availability may be reduced" vs. production (which serves Content
  Translation / Section Translation / translatewiki.net).
- **No documented rate limit** — WMF API etiquette applies: descriptive User-Agent,
  ≥1s pacing, 429/403 handling (see `wikimedia-api-access`).
- **Errors:** 422 (validation — missing/wrong fields, unsupported provider/pair),
  503 (overloaded — back off). Health: `GET /healthz`.
- **Licensing:** translations are derivative works under the source content's CC-BY-SA
  license; MinT makes no accuracy warranties ([disclaimer](https://www.mediawiki.org/wiki/MinT#Disclaimer)).
- **Privacy:** only freely-licensed content is sent; no nonpublic user information
  ([FAQ](https://www.mediawiki.org/wiki/Content_translation/Machine_Translation/MinT)).
- **Freshness:** language/model coverage changes as models are added — fetch
  `/api/languages` live; never hardcode the language list.
- **History:** MinT launched 2023; infra scaled Dec 2023 (Phab T352853, T352136);
  code MIT and active (pushed 2026-06).

## 6. Candidacy filter (design-philosophy.md §2)

| # | Test | Verdict |
|---|---|---|
| 1 | Procedure vs. topic | ✅ PASS — concrete SOPs (translate, discover languages, rich formats, provider selection) |
| 2 | Generalizability | ✅ PASS — any language pair (~200+ languages), any content, any wiki context |
| 3 | Reuse frequency | ✅ PASS — translation is a recurring step in multilingual workflows, localization, research |
| 4 | Context clutter | ✅ PASS — "mint"/"machine translation" keywords are distinctive; no discovery-hint collisions |
| 5 | Staleness | ✅ PASS with shape — language/model lists are volatile → encoded as fetch-on-demand via `/api/languages`; skill encodes only the stable shape + traps |
| 6 | Fetch-on-demand | ✅ PASS — the volatile parts (languages, models) are pulled live; the skill encodes what cannot be fetched (field names, formats, traps, etiquette) |
| 7 | Home vs. new | ✅ PASS — no existing skill covers MT; verified against the catalog and skills network |

**Tier: T2** (high-value). Failure-severity evidence: without the skill an agent either
(a) invents a translation endpoint (404), (b) uses the wrong field names (`text`/`from`/`to`
→ 422), or (c) falls back to external/commercial MT services with different licensing —
all plausible-wrong-output territory. The 422 field-name trap and the bare-`/api` 404
trap were both hit live during research.

## 7. Structure decision

Hub skill + CLI + test, no separate references (the API surface is small enough to live
in SKILL.md; the deep detail lives in this memo):

```
.claude/skills/mint/
├── SKILL.md                    # hub: when to use, API basics, SOPs, guardrails
└── scripts/translate.py        # stdlib-only CLI: translate text/file, list languages
```

Tests: `tests/test_mint.py` (content-anchor + script-compile checks).
Registration: README.md skill table + "What can I do" rows; ROADMAP.md "Published skills".

## 8. Follow-ups (not in the initial PR)

- Add a "translation" row to `wikimedia-api-strategy` (MinT is the only MT surface).
- Cross-reference from `wikimedia-i18n-l10n-for-tools` (message-file translation workflow).
- Re-verify benchmark numbers and `/api/languages` coverage when the service majors
  versions or new models land (skill `last_verified` cadence).
- Watch "MinT for Wiki Readers" (Phab T341196) — a reader-facing AI-translation product
  with its own policy/attribution implications.

## 9. Key sources

- https://www.mediawiki.org/wiki/MinT (+ disclaimer section)
- https://www.mediawiki.org/wiki/Content_translation/Machine_Translation/MinT
- https://translate.wmcloud.org/openapi.json and /docs
- https://github.com/wikimedia/mediawiki-services-machinetranslation
- https://phabricator.wikimedia.org/project/view/6526/ (MinT project)
- Live benchmark by this research (2026-08-17, §4)
