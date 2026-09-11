---
name: wikidata-reconciliation
description: Resolve unstructured labels to verified Wikidata QIDs — OpenRefine reconciliation protocol, wbsearchentities fallback, candidate scoring, and LLM QID grounding guardrails
license: MIT
compatibility: opencode
last_verified: 2026-08-26
depends_on: [wikimedia-api-access, wikidata]
skill_discovery_hints:
  - keywords: ["reconcile", "reconciliation", "match QID", "resolve QID", "entity matching", "QID verification", "label to QID", "OpenRefine reconcile"]
  - keywords: ["grounding", "verify entity", "hallucinated QID", "candidate scoring", "disambiguation", "fuzzy entity match"]
---

# Wikidata Reconciliation

> ⚠️ **User-Agent required:** All calls to Wikidata and the reconciliation service require a descriptive `User-Agent` header. Requests without one are blocked with HTTP 403/429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill.

## When to use

- You have **unstructured labels** ("Eiffel Tower", "Jane Smith (artist?)", "Church of the Holy Sepulchre") and need the **correct QID** — reliably, with confidence, not just the first search hit.
- You are **preparing data for Wikidata/Commons edits** (QuickStatements batches, SDC depicts values, OpenRefine schemas) and must **verify every QID before writing**.
- An **LLM produced a QID** (from memory, from a tool call, from a caption) and you must check it actually exists, refers to the right entity, and has the right type — the single most important guardrail for AI-assisted editing.
- You want to **deduplicate**: check whether an entity already exists before `CREATE` (QuickStatements duplicate-item disaster prevention).

**Do NOT use for:** querying Wikidata structure (see `wikidata`), semantic/vector discovery when you don't know the label shape (see `wikidata-vector-search`), or editing Structured Data on Commons (see `wikimedia-commons-sdc` — which this skill feeds).

## The core principle: never trust a QID you didn't verify

A QID is a *claim* about identity. The cost of a wrong QID is not a typo — it is **data corruption**: wrong depicts statements on Commons, wrong statements on Wikidata, duplicate items, or edits that other editors must clean up (or that poison downstream queries). The rules:

1. **Every QID used in a write operation must be verified in the same session** — fetched back via `wbgetentities` and checked: exists ✓, label matches intent ✓, P31 type is plausible ✓.
2. **An LLM-emitted QID is a hypothesis, not a fact.** Treat "Q243" from a model as "maybe Q243" until `wbgetentities` confirms it.
3. **When a label is ambiguous, prefer the reconciliation service (or `wbsearchentities`) candidate list with descriptions** over guessing from label alone.
4. **When confidence is below threshold, emit a "needs human review" verdict instead of a QID.** It is always correct to say "unresolved" and wrong to say "Q123" when you are guessing.

## The reconciliation service (OpenRefine protocol)

### Endpoint (verified 2026-08-18)

| Host | Status |
|---|---|
| **`https://wikidata-reconciliation.wmcloud.org`** | ✅ Canonical (moved from `wikidata.reconci.link`, which 307-redirects) |
| `https://reconcile.wikidata.org` | ❌ NXDOMAIN (dead) |

Service URL: `https://wikidata-reconciliation.wmcloud.org/en/api` (language prefix `en`, `fr`, `de`, …).

The service speaks the **OpenRefine Reconciliation Service API** — the same protocol OpenRefine, Flickypedia, and other tools use. You can call it directly without OpenRefine.

### 1. Service manifest (`GET /api`)

```bash
curl -s -A "$WIKIMEDIA_USER_AGENT" "https://wikidata-reconciliation.wmcloud.org/en/api"
```

Returns JSON: `name`, `identifierSpace`, `schemaSpace`, `defaultTypes` (e.g. `Q35120` entity), and an `extend` block with `property_settings` (limit, ranks, references) usable for the `extend` endpoint. Always read `defaultTypes` — you can filter queries by type (`/common/topic`, etc.) but Wikidata's reconciliation service mostly supports `Q35120` (entity) as a practical default.

### 2. Autocomplete (`GET /suggest/entity`)

```bash
curl -s -A "$WIKIMEDIA_USER_AGENT" \
  "https://wikidata-reconciliation.wmcloud.org/en/suggest/entity?prefix=Eiffel%20Tower&type=/common/topic"
```

Returns `{"result": [{"id": "Q243", "name": "Eiffel Tower", "description": "tower located on the Champ de Mars in Paris, France"}, ...]}`. The description field is the **disambiguation key** — always read it.

### 3. Batch query (`POST /api`) — ⚠️ type-filtered queries fail (root cause known, fix merged upstream but not deployed)

```bash
curl -s -A "$WIKIMEDIA_USER_AGENT" -X POST \
  "https://wikidata-reconciliation.wmcloud.org/en/api" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode 'queries={"q0":{"query":"Eiffel Tower","limit":3}}'           # ✅ works
  --data-urlencode 'queries={"q0":{"query":"Eiffel Tower","limit":3,"type":"Q35120"}}'  # ✅ works (default type)
  --data-urlencode 'queries={"q0":{"query":"Barack Obama","limit":3,"type":"/person"}}' # ❌ fails
```

**Precise failure scope (verified live 2026-08-26):** the batch endpoint works for
plain-text queries and default-type (`Q35120`) queries. It fails **only when a
non-default type filter is supplied** (`/person`, `/common/topic`, ...), because that
path runs the type-subclass SPARQL query (`?child wdt:P279* wd:Q43229`) against
`query.wikidata.org`. WDQS returns `403 text/plain` for the service's non-compliant
User-Agent, aiohttp raises `ContentTypeError` (the `0, message='...'` in the error),
and the service re-labels it as the misleading
`{"status":"error","message":"invalid query","details":"...Attempt to decode JSON with unexpected mimetype: text/plain..."}`.

**Root cause chain (investigated 2026-08-26):** WMF's User-Agent enforcement
([T400119](https://phabricator.wikimedia.org/T400119), resolved 2025-11-21) blocks
requests without a policy-compliant UA; the service's `user_agent` was
`OpenRefine-Wikidata reconciliation interface` (no contact info) and some request
paths sent none at all. Confirmed by other users: Phabricator
[T419770](https://phabricator.wikimedia.org/T419770) (open) and OpenRefine forum
[#2641](https://forum.openrefine.org/t/2641) (2025-11) and
[#2779](https://forum.openrefine.org/t/2779) (2026-04). **A fix is merged upstream**
([nfdi4culture fork MR #11](https://gitlab.com/nfdi4culture/openrefine-reconciliation-services/openrefine-wikibase/-/merge_requests/11),
2026-04-13: adds the UA to all requests, uses policy-compliant UA) but has **not been
deployed** to `wikidata-reconciliation.wmcloud.org` — re-test periodically.

**Practical guidance: do not rely on the batch endpoint for type-filtered queries** —
use `wbsearchentities` (below) as the primary reconciliation path and implement type
filtering as a P31 check on verified QIDs. Plain-text batches work if you need them.

## Primary path: `wbsearchentities` (always works)

The Action API search is the reliable reconciliation primitive — it returns ranked candidates **with descriptions and match metadata**, and it accepts type hints.

```bash
curl -s -A "$WIKIMEDIA_USER_AGENT" \
  "https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&formatversion=2&search=Eiffel%20Tower&language=en&limit=5"
```

Response shape (formatversion=2):

```json
{"search": [
  {"id": "Q243", "label": "Eiffel Tower", "description": "tower located on the Champ de Mars in Paris, France",
   "match": {"type": "label", "language": "en", "text": "Eiffel Tower"}},
  {"id": "Q3533063", "label": "Eiffel Tower with Trees", "description": "painting by Robert Delaunay ..."},
  ...
]}
```

Key parameters:

| Param | Purpose |
|---|---|
| `search` | The label text |
| `language` | Language of the label/description (e.g. `en`, `mul` for multilingual) |
| `uselang` | Language for the returned description |
| `limit` | Max results (50 max) |
| `type` | Optional `item` / `property` filter |
| `formatversion=2` | JSON array response (mandatory) |

### Candidate scoring SOP (how to pick the right QID)

1. **Exact label match** (`match.type == "label"`) with the right language → strong candidate.
2. **Description sanity**: does the description match the entity you mean? "Eiffel Tower with Trees" is a *painting*, not the tower — description kills it.
3. **Type check via P31** (below) when the entity's type matters (person vs. place vs. work).
4. **Multiple plausible candidates → human review.** Never pick by position alone; the search engine's ranking is not a correctness judgment.
5. **No good candidate → `wbsearchentities` with a broader or alternative-language search, then give up gracefully** — do not force a match.

## Verifying a QID before writing (the guardrail)

```bash
curl -s -A "$WIKIMEDIA_USER_AGENT" \
  "https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&formatversion=2&ids=Q243&props=labels|descriptions|claims"
```

Checklist before any write:

1. **Exists** — response has the entity (not a `missing` entry).
2. **Label matches intent** — `labels.en.value` matches (case-insensitive) the label you meant.
3. **Type is plausible** — inspect `claims.P31[].mainsnak.datavalue.value.id`; e.g. a person should have P31 ∈ {Q5 human, ...}, a place should not.
4. **Not a disambiguation page** — check for `claims.P31` containing `Q4167410` (Wikimedia disambiguation page).

If any check fails → **do not write**. Return the discrepancy.

## LLM QID grounding (the AI-harness use case)

When an LLM produces a QID (or you're building a harness where a model proposes entities):

1. **Collect all proposed QIDs** from the model output.
2. **Batch-verify** them in one `wbgetentities` call (`ids=Q1|Q2|...|Q50`, `props=labels|descriptions|claims`).
3. **Drop or flag** any QID that: doesn't exist, has a mismatched label, or has a wrong P31.
4. **Replace** dropped QIDs by re-running `wbsearchentities` on the original label (the model's label is usually right even when its QID is invented).
5. **Threshold rule**: if >10% of a batch fails verification, halt and review the pipeline — that's a systemic hallucination rate, not noise.

This is the same discipline OpenRefine's reconcile step gives you *inside* the tool — you're doing it as a protocol call, so it works in any harness.

## Batch patterns

### Resolve a list of labels → QIDs (spreadsheet/CSV prep)

```python
import json, time, urllib.parse, urllib.request

UA = "MyTool/1.0 (https://example.org; me@example.com) ReconBatch/1.0"

def api(params):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def resolve(label, lang="en"):
    d = api({"action": "wbsearchentities", "format": "json", "formatversion": "2",
             "search": label, "language": lang, "limit": 3})
    for hit in d.get("search", []):
        desc = hit.get("description", "")
        if hit.get("match", {}).get("type") == "label":
            return {"label": label, "qid": hit["id"], "desc": desc, "confidence": "high"}
        if desc:  # first described candidate: medium confidence
            return {"label": label, "qid": hit["id"], "desc": desc, "confidence": "medium"}
    return {"label": label, "qid": None, "desc": "", "confidence": "none"}

labels = ["Eiffel Tower", "Jane Smith (artist?)", "Church of the Holy Sepulchre"]
out = [resolve(l) for l in labels]
for o in out:
    print(f"{o['confidence']:8s} {o['qid'] or 'UNRESOLVED':10s} {o['label']} — {o['desc'][:60]}")
    time.sleep(0.5)  # ≥1s pacing recommended for batches; 0.5s is the floor
```

### Verify a batch of model-proposed QIDs

```python
def verify(qids):
    d = api({"action": "wbgetentities", "format": "json", "formatversion": "2",
             "ids": "|".join(qids), "props": "labels|descriptions|claims"})
    ok = {}
    for qid, ent in d.get("entities", {}).items():
        p31 = [c["mainsnak"]["datavalue"]["value"]["id"]
               for c in ent.get("claims", {}).get("P31", [])
               if c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")]
        ok[qid] = {"label": ent.get("labels", {}).get("en", {}).get("value"),
                   "p31": p31}
    return ok  # caller decides: exists? right label? right type?
```

## Constraint & Guardrails

1. **Never write an unverified QID.** Verify via `wbgetentities` in the same session as the write (see `wikimedia-commons-sdc` / `quickstatements` for the write side).
2. **The reconciliation batch `POST` endpoint fails on type-filtered queries** (root cause known since 2026-08-26: WDQS UA-policy 403 → misleading "invalid query"; see §3 above). `suggest/entity` and `wbsearchentities` are the working paths; plain-text batches work. For type filtering, verify P31 on the QID instead of relying on the service's type filter.
3. **Descriptions are the disambiguation key.** Two entities can share a label; their descriptions cannot (usually). Read `description` on every candidate.
4. **Language matters.** Search in the language of the label; descriptions come back in `uselang`. For multilingual lookups use `language=mul` sparingly — prefer explicit language + `uselang=en`.
5. **Rate limits:** `wbsearchentities`/`wbgetentities` are Action API calls — ≥1s pacing for batch work, batch IDs 50/call, respect 429 `Retry-After`. The reconciliation service is a separate host with its own limits; keep to a few requests/second.
6. **"UNRESOLVED" is a valid answer.** If no candidate passes, return `None`/`UNRESOLVED` and let the caller decide (skip, flag for human, or create a new item deliberately — never auto-create).
7. **Don't confuse the reconciliation service with the Wikidata API.** The service speaks the OpenRefine protocol (manifest/autocomplete/batch); `wbsearchentities` is the underlying search. Prefer `wbsearchentities` for programmatic use — especially for type-filtered lookups, where the service's batch endpoint currently fails (see §3).

## Example Use Cases

- **QuickStatements prep**: resolve a CSV of "Artist Name" strings to QIDs, verify each, then emit `Q...` in the QS batch instead of raw names.
- **SDC depicts**: for a Commons batch upload, resolve object titles → QIDs → use in `P180` depicts statements.
- **LLM article-work enrichment**: a model proposes entities for an article; batch-verify all proposed QIDs; replace hallucinated ones via re-search.
- **Dedupe check**: before `CREATE` on Wikidata, `wbsearchentities` the intended label; if a strong match exists, use it instead.

## Tooling

- `scripts/reconcile.py` — CLI: resolve a label or a list of labels to verified QIDs (`--verify` flag checks via `wbgetentities`). Stdlib only.

## Cross-References

| Related skill | Why |
|---|---|
| **[wikidata](../wikidata/SKILL.md)** | Lookups, SPARQL, entity structure — the search/verify calls here build on it |
| **[wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md)** | The write side: depicts/creator/license values must be reconciled QIDs |
| **[quickstatements](../quickstatements/SKILL.md)** | The write side: "search before CREATE" — this skill is that search, done properly |
| **[wikidata-vector-search](../wikidata-vector-search/SKILL.md)** | Semantic/fuzzy discovery when you don't know the label — complements exact reconciliation |
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent, rate limiting, 403/429 handling for all calls |
