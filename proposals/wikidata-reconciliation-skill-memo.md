# Wikidata Reconciliation — Skill Research Memo

**Date:** 2026-08-18
**Author:** WikiButler-bot (agent research, for Andrew Lih)
**Status:** Proposed — add as T2 skill (high-value; T1-adjacent for AI harnesses)
**Related PR:** feat/wikidata-reconciliation (skill: `.claude/skills/wikidata-reconciliation/`)

---

## 1. Motivation

An audit of the catalog (2026-08-18) found that **reconciliation is the biggest
blind spot in the repo**: of 59 skills, only 2 mention "reconcil" — `pattypan`
(1 hit, about spreadsheet header matching — a false positive) and
`wikimedia-commons-sdc` (3 hits, passing OpenRefine workflow mentions with no
procedure). The building blocks exist scattered across `wikidata`
(`wbsearchentities`, `prop=pageprops`) and `quickstatements` ("search before
CREATE" — one line, no SOP), but **no skill teaches an agent to resolve an
unstructured label to a verified QID with confidence, or to verify a QID before
writing it** — the single most important guardrail for LLM-assisted editing of
Wikidata/Commons.

This gap was identified in discussion with Luis Villa (OpenRefine as an LLM
harness target) and Andrew Lih: the reconciliation step is *separable* from
OpenRefine (it's a protocol, not a feature), and LLM harnesses need it as a
standalone, callable discipline.

## 2. API surface

| Component | Endpoint | Status (2026-08-18, verified live) |
|---|---|---|
| Reconciliation service manifest | `GET https://wikidata-reconciliation.wmcloud.org/en/api` | ✅ 200, JSON manifest (moved from `wikidata.reconci.link`, which 307-redirects) |
| Autocomplete | `GET /en/suggest/entity?prefix=...&type=...` | ✅ 200, returns id/name/description |
| **Batch query** | `POST /en/api` (OpenRefine `queries=` protocol) | ❌ **Broken**: `{"status":"error","message":"invalid query","details":"...Attempt to decode JSON with unexpected mimetype: text/plain..."}` — internal SPARQL call to query.wikidata.org failing |
| Legacy host | `https://reconcile.wikidata.org` | ❌ NXDOMAIN (dead) |
| **Primary search** | `action=wbsearchentities` (Wikidata Action API) | ✅ 200, ranked candidates with descriptions + `match` metadata |
| **Verification** | `action=wbgetentities` (ids, labels/descriptions/claims) | ✅ 200 |

## 3. Capability analysis vs. the existing catalog

| Existing skill | Relationship | Detail |
|---|---|---|
| `wikidata` | **Builds on** | Has `wbsearchentities` as a lookup row and `prop=pageprops` batch title→QID, but no candidate-scoring SOP, no disambiguation discipline, no verify-before-write guardrail |
| `wikimedia-commons-sdc` | **Feeds** | Depicts/creator/license values must be reconciled QIDs; this skill supplies the reconciliation procedure the SDC skill references but doesn't document |
| `quickstatements` | **Feeds** | "Search before CREATE" is the #1 QS disaster rule; this skill is that search done properly (SOP + script) |
| `wikidata-vector-search` | **Complements** | Semantic/fuzzy discovery when you don't know the label; exact reconciliation is the counterpart |
| `wikimedia-api-access` | **Depends on** | UA/rate-limit/429 discipline for all calls |

Verdict: **adds new territory** (reconciliation protocol + verification
guardrails); nothing replicated. No existing skill documents the OpenRefine
reconciliation protocol or the verify-before-write discipline.

## 4. Live measurements (2026-08-18, descriptive UA, 0.5s pacing)

| Call | Result |
|---|---|
| `wbsearchentities` "Eiffel Tower" | Q243 (high, exact label match), Q3533063 "Eiffel Tower with Trees" (painting — description disambiguates) |
| `wbsearchentities` "Leonardo da Vinci" | Q762, "Italian Renaissance polymath (1452−1519)", high |
| `wbsearchentities` "Jane Smith (artist?)" | no candidate → `UNRESOLVED` (correct graceful failure) |
| `wbsearchentities` "Barack Obama" | **Q649593 = Barack Obama Sr. (his father!)** — search ranking put the father first; `--verify` caught `label_matches: false`. Perfect live demonstration of why verification is mandatory |
| `wbgetentities` Q243 | exists, label "Eiffel Tower", P31 ∈ {Q1440476, Q1440300, Q2319498} |
| `suggest/entity?prefix=Eiffel` | Q243 first, with description |
| `POST /en/api` batch query | **partial** — plain-text & default-type queries work; type-filtered queries fail (WDQS UA-policy 403 → misleading "invalid query"). Root cause identified 2026-08-26: T400119 enforcement; confirmed by others at T419770 + forum #2641/#2779; fix merged in nfdi4culture fork MR #11 (2026-04-13) but not deployed. |

## 5. Candidacy filter

1. **Procedure vs. topic** — pure procedure ("resolve label → verified QID") ✅
2. **Generalizability** — recurs across any Wikidata/Commons write task, any entity type, any language ✅
3. **Reuse frequency** — every QuickStatements/SDC/upload prep workflow; recurring in AI-harness work ✅
4. **Context clutter** — keywords (`reconcile`, `match QID`, `grounding`) distinctive; no collisions with `wikidata`/`quickstatements`/`wikidata-vector-search` hints checked ✅
5. **Staleness** — encodes protocol shape + verified traps; batch-endpoint failure scope (type-filtered queries) is timestamped with root cause + upstream fix links (T400119/T419770/MR #11) and instructs re-testing; links live endpoints ✅
6. **Fetch-on-demand** — points at live endpoints (`wbsearchentities`, `wbgetentities`, service URLs); no enumerated volatile data ✅
7. **Home vs. new** — audited: no existing home. `wikidata` lacks the SOP; `quickstatements` lacks the procedure; `commons-sdc` references but doesn't document ✅

**Tier: T2** (agent could eventually figure out `wbsearchentities`, but at 2–5×
cost and *without the verify guardrail* — which is the catastrophic-failure
prevention). For LLM-harness builders it's effectively T1: writing a
hallucinated QID corrupts data silently. "Evidence beats prediction": the
Barack Obama Sr. live result is a documented real failure mode caught by
verification.

## 6. Structure decision

Single-file skill (~3,300 words) + one stdlib script (`scripts/reconcile.py`),
per the mint pattern (small surface, one CLI). Sections: when to use → core
principle (never trust an unverified QID) → reconciliation service (manifest/
autocomplete/batch-broken trap) → `wbsearchentities` primary path → candidate
scoring SOP → verify-before-write checklist → LLM QID grounding → batch
patterns (Python) → guardrails → use cases → tooling → cross-references.

## 7. Follow-ups

- Re-test `POST /api` on the reconciliation service once the WDQS mimetype
  issue is resolved upstream; update the trap section when fixed.
- `wikimedia-commons-sdc`: add "Reconcile values before batch editing" section
  linking this skill (separate PR).
- `quickstatements`: elevate "search before CREATE" to a short SOP calling
  this skill (separate PR).
- `wikidata`: add a "Resolving labels to QIDs" cross-reference subsection.

## 8. Key sources

- Reconciliation service: `https://wikidata-reconciliation.wmcloud.org/en/api`
  (manifest, live-verified); legacy `wikidata.reconci.link` (307 redirect).
- Wikidata Action API: `action=wbsearchentities`, `action=wbgetentities`
  (live-verified, formatversion=2).
- OpenRefine reconciliation protocol: manifest/suggest/batch shape (verified
  against the live service; the type-filtered batch failure is documented in
  the skill with root cause: WDQS UA-policy 403, T400119 → T419770, fix in
  nfdi4culture fork MR #11).
- Repo framework: AGENTS.md (PR-first), CONTRIBUTING.md (skill format),
  docs/design-philosophy.md §2 (tier system + candidacy filter).
