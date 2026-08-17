# XTools API — Skill Research Memo

**Date:** 2026-08-17
**Author:** Andrew Lih (with agent research)
**Status:** Decided — add as T2 skill; this memo is the durable rationale + evidence record
**Related PR:** feat/xtools (skill: `.claude/skills/xtools/`)

---

## 1. Motivation

Evaluate whether the XTools API (`xtools.wmcloud.org/api`) deserves a standalone
skill in this catalog. XTools is the long-standing "canonical stats API" for
Wikimedia — the tool most editors actually use for edit counts, article info,
and top-editor questions — maintained by MusikAnimal and Samwilson (WMF-affiliated
volunteer maintainers). A prior skill-candidate run recommended it as
"the canonical stats API; complements pageviews skill."

## 2. API surface (≈35 endpoints, 4 families)

| Family | Endpoints |
|---|---|
| **Page** (7) | `pageinfo` (renamed from `articleinfo` in 3.20.0, Aug 2024), `prose`, `links`, `top_editors`, `assessments`, `bot_data`, `automated_edits` |
| **User** (14) | `simple_editcount`, `pages_count`, `pages`, `automated_editcount`, `automated_edits`, `nonautomated_edits`, `edit_summaries`, `top_edits`, `category_editcount`, `log_counts`, `month_counts`, `timecard`, `globalcontribs`, `automated_tools` (removed → project) |
| **Project** (9) | `normalize`, `namespaces`, `assessments`, `assessments_configuration`, `automated_tools`, `admin_groups`, `admin_stats`, `patroller_stats`, `steward_stats`, `largest_pages` |
| **Quote** (3) | random / single / all (trivial; not covered by the skill) |

Sources: mediawiki.org [XTools/API](https://www.mediawiki.org/wiki/XTools/API),
[XTools/API/Page](https://www.mediawiki.org/wiki/XTools/API/Page),
[XTools/API/User](https://www.mediawiki.org/wiki/XTools/API/User),
xtools.readthedocs.io (3.11.0), and the OpenAPI config in the
[x-tools/xtools](https://github.com/x-tools/xtools) repo (`config/packages/nelmio_api_doc.yaml`).

## 3. Capability analysis vs. the existing catalog

| Existing skill | Relationship | Detail |
|---|---|---|
| `wikimedia-pageviews` | **Supplements** | XTools has *no* pageviews endpoints (that is the separate pageviews.wmcloud.org app). XTools adds the context *around* traffic: watchers, editors, assessments. Prior note "complements pageviews" confirmed. |
| `wikipedia-edit-history` | **Enhances** | `top_edits`, `month_counts`, `edit_summaries`, `simple_editcount` replace dozens of Action API `list=usercontribs` calls with one request. |
| `wikiwho` | **Enhances / pairs** | XTools' *Authorship* tool is powered by the WikiWho algorithm but reports **character-based** attribution vs. WikiWho's token-based. Cross-reference both directions. |
| `wikimedia-page-assessment` | **Overlaps** | XTools `assessments` is a batch multi-page endpoint; PageAssessments is per-page. One line in the skill defines the boundary. |
| `wikimedia-api-strategy` | **Needs pointer** | Should eventually gain an "XTools vs Action API" decision row (follow-up). |
| — | **New territory** | `prose` stats, `bot_data`, admin/patroller/steward stats, `timecard`, `globalcontribs`, `automated_editcount` — no existing skill covers these. |

Verdict: mostly **enhances + adds new**, with one genuine overlap (assessments)
and one complement (pageviews). Nothing is replicated wholesale.

## 4. Live measurements (2026-08-17, descriptive UA, ≥1s pacing)

| Endpoint | HTTP | Total time | Server `elapsed_time` | Payload |
|---|---|---|---|---|
| `page/pageinfo` (Albert Einstein) | 200 | 0.66s | 0.475s | 585 B |
| `page/articleinfo` (legacy name) | 200 | 0.96s | 0.849s | 585 B (still works, excluded from docs) |
| `page/top_editors` (2024, limit 5) | 200 | 0.31s | 0.238s | 1.1 KB |
| `page/prose` (Albert Einstein) | 200 | 0.83s | 0.706s | 178 B |
| `user/simple_editcount` (Fuzheado) | 200 | 0.88s | 0.772s | 273 B |
| `user/simple_editcount` (IP 24.49.192.8) | 200 | 0.12s | 0.048s | 212 B |
| `user/simple_editcount` (Cydebot, high count) | 200 | 0.24s | 0.148s | 291 B, `approximate: true` + `warning` |
| `user/top_edits` (Fuzheado) | 200 | — | — | **very large** (multi-hundred-KB for active editors) |
| `project/admin_stats` (enwiki) | 200 | 1.85s | 1.722s | 89 KB |

**Caching:** `cache-control: private, must-revalidate`, no `X-Cache`/`Age`.
Every request is a full compute round trip — no client-side reuse.

## 5. Documented operational limits (from official docs + OpenAPI config)

- **Rate limits:** no hard number. Courtesy policy: *make requests synchronously —
  one full round trip before the next*. Official 503: "XTools is currently
  overloaded servicing other requests."
- **Heavy users:** 501 above **600,000 edits** ("Maximum 600000"); graceful
  `approximate` + `warning` below that (verified live).
- **Query timeout:** 504 after **900 seconds** — heavy queries run up to 15
  minutes before being killed.
- **UA policy:** informative User-Agent required.
- **Versioning:** **the API is not versioned.** Breaking renames happen
  (`articleinfo` → `pageinfo`, Aug 2024; `last_edit_id` → `modified_rev_id`;
  `author` → `creator`). Deprecations are announced via the `warning` property —
  clients MUST log it.
- **Errors:** RFC 7807 problem+json (`status`, `title`, `details`).
- **Official guidance:** the docs themselves say the Action API and REST API
  "will be considerably faster than XTools" — the skill must encode the
  decision rule to prefer them when they suffice.

## 6. Candidacy filter (design-philosophy.md §2)

| # | Test | Verdict |
|---|---|---|
| 1 | Procedure vs. topic | ✅ PASS — concrete endpoint SOPs |
| 2 | Generalizability | ✅ PASS — any project (~300+ wikis), any page/user |
| 3 | Reuse frequency | ✅ PASS — stats questions are among the most common wiki-research asks |
| 4 | Context clutter | ✅ PASS — "xtools" keyword is distinctive; no discovery-hint collisions |
| 5 | Staleness | ✅ PASS with shape — unversioned API is the *reason* to encode gotchas (warning, renames, 501/503/504) and link live docs |
| 6 | Fetch-on-demand | ✅ PASS — alternatives (Action API grinding) cost 5–50× more requests; that is the value proposition |
| 7 | Home vs. new | ✅ PASS — no existing skill covers the XTools surface |

**Tier: T2** (high-value). Without it an agent either grinds the Action API
(slow but correct) or guesses at an unversioned API whose endpoint names have
been renamed — plausible-wrong-output territory. Failure severity evidence:
the rename alone (old name still returns 200!) is a classic silent-wrong-answer trap.

## 7. Structure decision

Hub + references, matching the split-vs-merge philosophy:

```
.claude/skills/xtools/
├── SKILL.md                    # hub: when to use, etiquette, error semantics, guardrails
└── references/
    ├── page-api.md             # pageinfo, top_editors, prose, links, assessments, bot_data
    └── user-project-api.md     # user editcounts/top_edits + project admin/patroller stats
```

No script shipped in the initial version (endpoints are single GETs; curl/requests
suffice). Tests: SKILL.md/reference content anchors via `tests/test_xtools.py`.

## 8. Follow-ups (not in the initial PR)

- Add an "XTools vs Action API" row to `wikimedia-api-strategy`.
- Cross-reference from `wikiwho` (character vs token attribution) and
  `wikimedia-page-assessment` (batch vs per-page).
- Consider a CLI script (`xtools-stats.sh`) if usage shows demand.
- Re-verify `elapsed_time`/latency numbers when the service changes hands or
  majors versions (skill `last_verified` cadence).

## 9. Key sources

- https://www.mediawiki.org/wiki/XTools/API (+ /Page, /User, /Project, /Quote)
- https://xtools.readthedocs.io/en/3.11.0/api/index.html
- https://github.com/x-tools/xtools (OpenAPI config, routes)
- https://xtools.wmcloud.org/api (JS-rendered; docs link out to mediawiki.org)
