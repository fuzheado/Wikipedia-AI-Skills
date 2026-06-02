---
name: wikipedia-en-article-audit
description: Audit an English Wikipedia article for structural issues, factual errors, and NPOV violations, then produce a machine-readable task graph (DAG) that another agent can execute to fix all identified problems
license: MIT
compatibility: opencode
---

> ⚠️ **Read-only policy: This skill audits only. It never edits live Wikipedia articles.**
>
> All three phases fetch data from Wikipedia but **never write back**. The output is a
> `taskgraph.json` specification — a work order for a *separate* agentic system to execute.
> The audit agent does not and should not have edit permissions.
>
> If a user wants to act on the findings, they should start a **new, clean session** with
> edit-capable tools and feed it the `taskgraph.json` as input. Mixing audit and edit in
> the same session risks accidental writes, edit conflicts, and BLP violations.
>
> **Separate the concerns:** one agent audits, a different agent edits (or the same agent
> in a different context with explicit user confirmation).

> ⚠️ **Audit is a three-phase process.** Phase 1 (diagnosis) and Phase 3 (taskgraph generation) are fully automated. Phase 2 (sentence-by-sentence verification) requires a **human reviewer** to read sources and classify each claim. Do not skip Phase 2 — the automated pipeline cannot reliably detect factual contradictions.

## Typical Invocation

A user invokes this skill with a simple request. The agent follows the workflow
below, stopping at Phase 2 for human review and resuming after the reviewer
returns their findings.

```
User:  "Audit the article on Pyrrhus Concer."

Agent: ▶ Runs Phase 1 (diagnosis)
       ▶ Presents diagnosis + sentences.jsonl to human reviewer
       ▶ Waits for human to return verification.json
       ▶ Runs Phase 3 (taskgraph generation)
       ▶ Outputs taskgraph.json + analysis.md
       ▶ "Audit complete. 10 tasks in the DAG:
            p0: 2 (factual correction, NPOV rewrite)
            p1: 4 (infobox, sections, missing details, assessment)
            p2: 4 (grammar, epitaph, reflist, sources)
          The taskgraph is at pyrrhus_concer/taskgraph.json"
```

The human reviewer's role is focused and bounded: review each sentence, read
the cited sources, and fill in verdicts. The rest is handled by the scripts.

---

Enables the agent to produce a structured work order — a `taskgraph.json` validated
against a formal JSON Schema — for improving any English Wikipedia article. The
output is designed for handoff to a separate agentic execution system.

**Related skills (prerequisites for understanding page structure and tools):**

- **[wikipedia-page-anatomy](../wikipedia-page-anatomy/SKILL.md)** — Understanding infoboxes, categories, templates, sections
- **[wikimedia-wikitext](../wikimedia-wikitext/SKILL.md)** — AST-based wikitext parsing
- **[wikimedia-page-assessment](../wikimedia-page-assessment/SKILL.md)** — WikiProject quality ratings
- **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** — User-Agent headers, rate limiting, error handling
- **[wikipedia-en-biography-writing](../wikipedia-en-biography-writing/SKILL.md)** — NPOV / NOR / BLP standards for content evaluation

---

## Overview

The audit pipeline converts a Wikipedia article URL into a repair task graph:

```
Article URL
    │
    ▼
┌─────────────────────────────────────┐
│  Phase 1: Diagnosis                 │  ← Automated
│  ─────────────────────               │
│  • Fetch article, talk page, WD     │
│  • Structural audit (infobox,       │
│    sections, categories, assess)    │
│  • Identify NPOV trigger keywords   │
│  • Extract sentences + citations    │
│  │                                   │
│  Output: diagnosis.json              │
│          sentences.jsonl             │
│          NPOV flags                  │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 2: Verification              │  ← Human-in-the-loop
│  ─────────────────────               │
│  • Review each sentence             │
│  • Read cited sources               │
│  • Cross-reference sister articles  │
│  • Classify as CONFIRMED /          │
│    CONTRADICTED / NPOV_OR /         │
│    UNVERIFIABLE                      │
│  • Write corrections                │
│  │                                   │
│  Output: verification.json           │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Phase 3: Taskgraph Generation      │  ← Automated
│  ────────────────────────            │
│  • One task per identified issue    │
│  • Dependency edges from DAG rules  │
│  • Verify steps from diagnosis      │
│  • Schema validation at output      │
│  │                                   │
│  Output: taskgraph.json              │
│          analysis.md                 │
└─────────────────────────────────────┘
```

---

## Prerequisites

### Tools and accounts

| Requirement | For | Notes |
|---|---|---|
| Python 3.10+ | Phase 1 scripts, Phase 3 generator | Standard library + `requests` |
| `pip install requests mwparserfromhell` | Wikitext parsing, API calls | See `wikimedia-wikitext` skill |
| Wikipedia account | Phase 3 execution (optional — not needed for audit) | Needed if you run the resulting taskgraph |
| SSH tunnel to Toolforge (optional) | Database assessment queries | See `wikimedia-database` skill |
| Text editor or JSON-aware IDE | Phase 2 human review | Needed to edit `verification_stub.json` |

### User-Agent

All API calls must include a descriptive User-Agent header or they will be blocked
with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)**
skill for the correct format.

### Environment variables

| Variable | Required for | Default |
|---|---|---|
| `WIKIPEDIA_USER_AGENT` | All API calls | None (must be set) |
| `TOOLFORGE_USER` | Database queries (optional) | — |
| `TOOLFORGE_SQL_USER` | Database queries (optional) | — |
| `TOOLFORGE_SQL_PASSWORD` | Database queries (optional) | — |

---

## SOP: Phase 1 — Diagnosis

### Purpose

Produce a structured inventory of everything wrong with the article. Phase 1 is
entirely mechanical — no creativity or judgment required.

### Steps

#### 1a. Resolve the article title

```bash
curl -s "https://en.wikipedia.org/w/api.php?action=query&titles=$TITLE&redirects=1&format=json"
```

- If the title is a redirect, follow it to the canonical page.
- If it's a disambiguation page, abort and list the options.
- Record the canonical title and page ID.

#### 1b. Fetch article components

Fetch and store:

| Component | API call | Stored as |
|---|---|---|
| Wikitext | `action=raw` | `sources/article.wikitext` |
| Talk page wikitext | `action=raw&page=Talk:TITLE` | `sources/talk.wikitext` |
| Page info (protection, length, watchers) | `prop=info` | `diagnosis.json` |
| Wikidata entity | `https://www.wikidata.org/wiki/Special:EntityData/{Q}.json` | `sources/wikidata.json` |
| Categories | `prop=categories` | `diagnosis.json` |
| Templates used | `prop=templates` | `diagnosis.json` |
| Page assessments (if tunnel available) | SQL on `enwiki_p.page_assessments` | `diagnosis.json` |

#### 1c. Structural audit

Check for:

- **Infobox:** Is an `{{Infobox ...}}` template present? If not, note which
  infobox type would be appropriate based on the article category.
- **Sections:** How many `== Level 2 ==` headings exist? Are standard sections
  present (Early life, Career, Legacy, etc.)?
- **Categories:** How many? Any obvious gaps (e.g., birth/death year, occupation)?
- **Protection:** Is the page protected? At what level? Does that affect what
  the taskgraph can do?
- **Assessment:** What class is the article assessed at (Stub/Start/C/B/GA/FA)?
  Is it under-assessed?
- **Maintenance templates:** Any `{{citation needed}}`, `{{POV}}`, `{{expand section}}`,
  `{{dead link}}`?
- **Short description:** Does the short description use correct demonym adjectives?
  Check for the common error pattern `China + noun` (e.g. "China businesswoman")
  which should be `Chinese + noun` ("Chinese businesswoman"). Other patterns:
  `America + noun` → `American + noun`, `Britain + noun` → `British + noun`.
- **Reference count:** How many `<ref>` tags? Any citation dumping (one ref covering
  many paragraphs)?
- **Image count:** Does the article have a lead image? An infobox image?
  If no image is found, check whether a Commons category exists for the subject
  (`https://commons.wikimedia.org/wiki/Category:{PAGENAME}`) and whether a
  free-licensed portrait is available. Note the result so Phase 2 can recommend
  adding an image to the infobox if one exists.

#### 1d. Article-type classification

Before the NPOV scan, determine the article type from its infobox, categories,
and BLP status. This shapes the expected section structure and the severity of
certain findings.

```python
def classify_article(categories, infobox_type, blp_status):
    if "Living people" in categories or blp_status:
        return "BLP"
    if any("births" in c for c in categories) and any("deaths" in c for c in categories):
        if "business" in str(categories) or "executive" in str(categories):
            return "biography_executive"
        if "scientist" in str(categories) or "engineer" in str(categories):
            return "biography_academic"
        return "biography_general"
    return "topic_article"
```

Each type has standard expected sections. The diagnosis flags missing ones:

| Article type | Expected sections | Examples |
|---|---|---|
| BLP | Early life and education, Career, Personal life (minimal), Awards | He Tingbo |
| biography_executive | Early life, Career, Board positions, Awards, Personal life | — |
| biography_academic | Early life and education, Career, Research, Selected works, Awards | — |
| biography_general | Early life, Career, Later life, Legacy | Pyrrhus Concer |
| topic_article | Varies by topic — use subject-specific conventions | — |

For living subjects, skip checks like "missing Later life section" or "missing
Legacy section" — these only apply to deceased subjects. Similarly, a "Personal
life" section is appropriate for BLPs but optional for historical biographies.

#### 1e. NPOV keyword scan

Scan the article text (after stripping templates and references) for these
trigger words and phrases:

```
# Editorial praise / promotional
undoubtedly, unquestionably, clearly, obviously,
notably, noteworthy, interestingly, importantly,
remarkably, impressively, extraordinarily,
incomparably, unbeatably, famously, notoriously,
renowned, legendary, pioneering, world-class,
visionary, iconic, groundbreaking, transformative

# Original research / speculation
it is possible that, it is likely that, it is plausible that,
it seems that, one can imagine that,
may have been, might have been, could have been,
was likely, was probably, appears to have been,
suggests that, is suggestive of, is indicative of

# Essay-like conclusions
a testament to, serves as a testament,
speaks to his, speaks to her, speaks to their,
is a testament, stands as a testament,
demonstrates his, demonstrates her,
reflects his, reflects her, indicative of

# Weasel words
some say, many believe, it is said that,
critics claim, it is widely regarded,
is considered to be, is thought to be,
is often described as, has been called
```

Each flagged occurrence is recorded with its sentence number, the trigger word,
and its surrounding context (50 chars before/after).

#### 1f. Extract sentences

Split the article body text (lead + all sections) into individual sentences:

```python
import re
# Split on sentence boundaries: . ! ? followed by space + capital letter
sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z"])', plain_text)
```

Each sentence is recorded as one JSON line:

```json
{
  "index": 1,
  "text": "Pyrrhus Concer (March 17, 1814 – August 23, 1897) was a formerly enslaved American sailor from Southampton, New York who was aboard the whaling ship Manhattan, the first American ship to visit Tokyo in 1845.",
  "char_offset": 0,
  "section": "lead",
  "has_inline_ref": true,
  "ref_indices": [0],
  "npov_flags": [],
  "verdict": null
}
```

#### 1g. Extract citations

Extract all `<ref>` tags and citation templates. For each:

```json
{
  "ref_index": 0,
  "template": "cite book",
  "params": {
    "last": "Van Zandt",
    "first": "Howard",
    "title": "Pioneer American Merchants in Japan",
    "year": "1984",
    "publisher": "Tuttle Publishing",
    "isbn": "9994648144",
    "pages": "68–72"
  },
  "url": null,
  "accessible": false,
  "sentence_indices": [1, 2, 3, 4, 5]
}
```

Also resolve which sentence(s) each reference supports. If one reference is
attached to the end of a multi-sentence paragraph, mark all sentences in that
paragraph as potentially supported by that ref.

Additionally, produce a **sources summary table** — a quick-reference view of
all citations with their accessibility status and whether sister articles or
Wikidata also corroborate the same claims. This table lets the Phase 2 human
reviewer skip sources that are confirmed redundant.

```json
{
  "sources_summary": [
    {
      "ref_index": 0,
      "short_ref": "Reuters 2026",
      "url": "https://www.reuters.com/...",
      "accessible": true,
      "accessible_via": ["direct_http"],
      "language": "en",
      "corroborated_by": ["wikidata", "nikkei_asia"],
      "sentences_supported": [1, 2, 3, 4]
    },
    {
      "ref_index": 3,
      "short_ref": "WSJ (paywalled)",
      "url": "https://www.wsj.com/...",
      "accessible": false,
      "accessible_via": ["web_archive"],
      "language": "en",
      "corroborated_by": ["nikkei_asia"],
      "sentences_supported": [28, 29]
    }
  ]
}
```

This summary enables a quick triage: sources marked `accessible: true` can be
read directly; inaccessible sources with corroboration from sister articles can
be deprioritized; inaccessible sources with no corroboration need alternative
retrieval attempts.

### Output files

| File | Format | Content |
|---|---|---|
| `diagnosis.json` | JSON | All structural findings, assessment, keyword flags, metadata |
| `sentences.jsonl` | JSONL | One line per sentence with metadata and null verdict |
| `sources/article.wikitext` | Text | Raw wikitext |
| `sources/talk.wikitext` | Text | Raw talk page wikitext |
| `sources/wikidata.json` | JSON | Wikidata entity dump |
| `diagnosis.json` (sources_summary) | JSON | Sources accessibility table with corroboration status |

---

## SOP: Phase 2 — Verification

### Purpose

For every sentence in the article, determine whether it is factually correct,
neutrally framed, and properly cited. This is the **human review** phase — the
automated system cannot reliably detect factual contradictions.

### Input

- `sentences.jsonl` from Phase 1
- `diagnosis.json` from Phase 1
- Article talk page
- Cited sources (fetched in Phase 1; some may be inaccessible)

### Procedure

#### 2a. Set up the working file

Copy `sentences.jsonl` to `verification_stub.json` and convert to a single JSON
array (easier for humans to edit):

```bash
python3 -c "
import json, sys
sentences = [json.loads(line) for line in open('sentences.jsonl')]
with open('verification_stub.json', 'w') as f:
    json.dump({'article_title': '$TITLE', 'sentences': sentences}, f, indent=2)
"
```

The stub has every sentence's `"verdict": null`. The human will fill these in.

#### 2b. BLP spotlight check

> ⚠️ **Stop here if the article is about a living person (BLP).**

If `diagnosis.json` shows `blp: yes`, apply extra scrutiny before proceeding
with sentence-by-sentence verification:

| Check | What to look for | Action if found |
|---|---|---|
| **Contentious claims** | Allegations of wrongdoing, legal disputes, national security implications, negative personal details | Require **multiple** high-quality, independent sources. If only one source supports a contentious claim, flag it. |
| **Private information** | Home address, phone number, email, exact birth date without source, family details not in public record | Remove immediately per WP:BLPPRIVACY. Do not leave in the article even temporarily. |
| **Geopolitical framing** | Sanctions, technology bans, national security designations — these are often politically charged | Ensure every geopolitical claim is attributed to a specific source (e.g., "According to Reuters..." not "The US added Huawei to the Entity List for...") |
| **Editorial monikers** | "Chip queen," "pioneer," "trailblazer" — any nickname or superlative | Must be attributed to the source that coined it. If the article asserts it in Wikipedia's voice, flag as NPOV. |
| **Harm principle** | Could publishing this fact cause real-world harm to the subject? | If the answer is yes and the fact is not essential to the biography, omit it per WP:BLPBALANCE. |

If any BLP violations are found at this stage, pause the audit and flag them
immediately. Do not proceed with sentence-by-sentence verification until the
violations are resolved — there is no point verifying 28 clean sentences if
the 29th is a BLP violation that will get the article deleted.

#### 2c. For each sentence, determine its verdict

| Verdict | When to use | Example |
|---|---|---|
| `confirmed` | A reliable source supports the claim, and the claim is framed neutrally | Sentence 1 (dates, ship, event — supported by Newsday + Wikidata + sister articles) |
| `contradicted` | A reliable source contradicts the claim, or the claim is demonstrably false | Sentence 2 ("Pyrrhus family" — Newsday says "Pelletreau family") |
| `npov_or` | The claim is plausible but framed in editorial/promotional language, or is speculative | Sentences 10–16 (essay-like financial analysis with "undoubtedly impressive", "testament to his business acumen") |
| `unverifiable` | No source could be found for the claim, or all sources are inaccessible | A claim supported only by a paywalled article that couldn't be accessed |
| `mixed` | The sentence contains multiple sub-claims with different verdicts | Sentence 2 (true: farmhand, 1832, Sag Harbor / false: Pyrrhus family) |

**Protocol for reading sources:**

1. First check the article's own cited sources. Open each URL or citation and
   read the relevant passages. Do not trust the article's interpretation — read
   the source yourself.
2. If the cited source is inaccessible (paywall, Cloudflare, 404), try the
   Wayback Machine at `web.archive.org`.
3. Cross-reference against Wikipedia sister articles (e.g., if the article says
   "first American ship to visit Tokyo", check the Mercator Cooper and Manhattan
   ship articles for confirmation).
4. For biographical articles, check Wikidata for birth/death dates, occupation,
   and known-for statements.
5. If no source can be found after reasonable effort, mark the sentence as
   `unverifiable`.

**Protocol for `contradicted` verdict:**

```json
{
  "index": 2,
  "verdict": "contradicted",
  "contradiction": {
    "source": "Newsday 2005 via Wayback Machine",
    "source_url": "https://web.archive.org/web/20050918211029/http://www.newsday.com/community/guide/lihistory/ny-history-hs509b,0,7157701.story",
    "source_quote": "He was owned by the Pelletreau family",
    "explanation": "The article says 'enslaved by the Pyrrhus family' but the Newsday article, based on Southampton Historical Museum records, says 'owned by the Pelletreau family'. Pyrrhus was Concer's given name (after the Greek king), not his enslaver's surname."
  },
  "correction": "Concer, named after the Greek king Pyrrhus, was enslaved by the Pelletreau family",
  "correction_citation": {
    "template": "cite news",
    "params": {
      "last": "Bleyer",
      "first": "Bill",
      "title": "Legacy: Pyrrhus Concer",
      "work": "Newsday",
      "year": "2005",
      "url": "https://web.archive.org/web/20050918211029/http://www.newsday.com/community/guide/lihistory/ny-history-hs509b,0,7157701.story"
    }
  }
}
```

**Protocol for `npov_or` verdict:**

```json
{
  "index": 10,
  "verdict": "npov_or",
  "npov_explanation": "The phrase 'indicate a level of financial stability and engagement with the financial institutions of his community' is the editor's interpretation of raw data, not a factual claim. The underlying data (savings accounts, shares) may be in the cited thesis, but the framing is editorial.",
  "suggested_action": "replace with neutral factual statement: 'Probate records showed he held four savings accounts, shares in the Southampton Water Works, and had lent money to others.'",
  "source_for_facts": {
    "citation_index": 2,
    "note": "Button thesis pp. 181, 183 — verify data access"
  }
}
```

**Protocol for `unverifiable` verdict:**

```json
{
  "index": 20,
  "verdict": "unverifiable",
  "reason": "The claim that Elihu Root wrote the epitaph is cited to a paywalled NYT article and previously to findagrave.com. Neither could be independently verified. The epitaph text itself is confirmed by Newsday, but the Root attribution is not.",
  "suggested_action": "add {{citation needed}} after 'engraved with an epitaph written by Elihu Root'"
}
```

**Protocol for `mixed` verdict:**

```json
{
  "index": 2,
  "verdict": "mixed",
  "sub_claims": [
    {
      "text": "enslaved by the Pyrrhus family",
      "verdict": "contradicted",
      "correction": "Pelletreau family"
    },
    {
      "text": "worked as a farmhand",
      "verdict": "confirmed",
      "source": "Newsday",
      "source_quote": "worked as a farmhand"
    },
    {
      "text": "until 1832",
      "verdict": "confirmed",
      "source": "Newsday",
      "source_quote": "Freed when he turned 18 in 1832"
    },
    {
      "text": "slavery in New York formally ended in 1827",
      "verdict": "confirmed",
      "source": "Historical fact (NY Gradual Emancipation Act)"
    },
    {
      "text": "worked on whale ships out of Sag Harbor, New York",
      "verdict": "confirmed",
      "source": "Newsday",
      "source_quote": "began shipping out on whaleships"
    }
  ]
}
```

#### 2d. Handle inaccessible sources

If a source cannot be accessed despite reasonable effort:

1. Check the Wayback Machine at `web.archive.org`
2. Check Wikipedia sister articles that cite the same source
3. Check Google Scholar or other databases for an accessible version
4. If still inaccessible, note it in the sentence's verdict

The `accessible` field in the citations array records the outcome:

```json
{
  "ref_index": 2,
  "accessible": false,
  "access_attempted": ["direct_http", "wayback_machine", "google_scholar"],
  "access_note": "Cloudflare protection on repository.library.brown.edu; PDF not publicly accessible"
}
```

#### 2e. Finalize verification.json

After reviewing all sentences, save the file as `verification.json`. The structure
is identical to `verification_stub.json` but with all `verdict` fields filled in.

**Validation checklist before saving:**

- [ ] Every sentence has a non-null `verdict`
- [ ] Every `contradicted` verdict has a `contradiction` object with `source`, `source_quote`, and `correction`
- [ ] Every `npov_or` verdict has a `suggested_action`
- [ ] Every citation has an `accessible` boolean
- [ ] The file is valid JSON (run `python3 -m json.tool verification.json`)

---

## SOP: Phase 3 — Taskgraph Generation

### Purpose

Given the diagnosis from Phase 1 and the verification from Phase 2, produce a
`taskgraph.json` (validated against the schema) and a human-readable `analysis.md`.

### Algorithm

For each sentence with a verdict other than `confirmed`, generate a task:

| Verdict | Task category | Criticality |
|---|---|---|
| `contradicted` | `factual_correction` | `p0` |
| `npov_or` | `npov_rewrite` | `p0` |
| `unverifiable` | `citation` | `p1` (add `{{cn}}`) |

For each structural issue found in the diagnosis, generate a task:

| Diagnosis finding | Task category | Criticality |
|---|---|---|
| Missing infobox | `infobox` | `p1` |
| No section headings | `structural` | `p1` |
| Missing categories | `maintenance` | `p2` |
| Under-assessed (Stub → Start) | `maintenance` | `p1` |
| Grammar / typo | `grammar` | `p2` |
| Citation formatting (`{{Reflist}}` → `{{Reflist|30em}}`) | `maintenance` | `p2` |

### Dependency rules

The generator applies these dependency edges:

| Task | Depends on | Rationale |
|---|---|---|
| All factual corrections | `fetch_and_verify_sources` | Sources must be available before editing |
| All NPOV rewrites | `fetch_and_verify_sources` | Same |
| Structural changes (section headings, infobox) | NPOV rewrites (if same area) | Avoid merge conflicts — rewrite first, then restructure |
| Citation additions | The affected sentence's rewrite task | Don't add `{{cn}}` to text that's about to be rewritten |
| Assessment update | All p0 and p1 tasks | Only update the rating after substantive fixes are done |
| Grammar fix | (none) | Independent — can run anytime |
| Reflist formatting | (none) | Independent |

### Output template

Each task follows this structure (from `taskgraph.schema.json`):

```json
{
  "id": "fix_enslaver_identity",
  "summary": "Correct 'Pyrrhus family' to 'Pelletreau family'",
  "depends_on": ["fetch_and_verify_sources"],
  "category": "factual_correction",
  "criticality": "p0",
  "tools": ["wikipedia_api"],
  "actions": [
    {
      "type": "edit_wikitext",
      "page": "Pyrrhus Concer",
      "oldText": "Concer was enslaved by the Pyrrhus family",
      "newText": "Concer, named after the Greek king Pyrrhus, was enslaved by the Pelletreau family",
      "summary": "fix enslaver identity per Newsday 2005",
      "citation": { ... }
    }
  ],
  "verify": [
    { "type": "page_contains", "page": "Pyrrhus Concer", "text": "Pelletreau" },
    { "type": "page_not_contains", "page": "Pyrrhus Concer", "text": "enslaved by the Pyrrhus family" }
  ]
}
```

### One-directional generation rule

`analysis.md` is a **derived artifact**, not a source document. It is generated
from `verification.json` + `taskgraph.json` and must never be edited by hand.

```
verification.json ──► taskgraph.json ◄── schema validates
       │                    │
       │                    │
       ▼                    ▼
   analysis.md ◄── generated from both, never edited directly
```

To enforce this:

1. **Auto-generated header.** Every generated `analysis.md` begins with:

   ```markdown
   <!-- AUTO-GENERATED from verification.json + taskgraph.json
        Do not edit by hand. To update, modify the source data or the
        generator script (04-generate-taskgraph.sh) and regenerate.
        Generated: 2026-06-02T12:34:56Z
        Article: Pyrrhus Concer -->
   ```

2. **Staleness check.** The generator checks file mtimes. If `verification.json`
   is newer than `analysis.md`, it prints:

   ```
   ⚠️  analysis.md is stale (verification.json changed since last generation).
      Regenerate with: 04-generate-taskgraph.sh --force
   ```

3. **No reverse path.** There is no script that reads `analysis.md` to produce
   `verification.json` or `taskgraph.json`. The `.md` file is a report, not
   an input to any downstream process. This prevents sync drift.

### Schema validation

Before writing the output file, validate it against `taskgraph.schema.json`:

```python
import json, jsonschema

with open('taskgraph.schema.json') as f: schema = json.load(f)
with open('taskgraph.json') as f: graph = json.load(f)
jsonschema.validate(graph, schema)
```

If validation fails, fix the generator. Do not output an invalid taskgraph.

### Output files

| File | Content |
|---|---|
| `taskgraph.json` | Validated JSON task DAG |
| `analysis.md` | Human-readable report from the diagnosis + verification data |

The `analysis.md` is generated from a template that includes:

- Quick stats (page length, assessment, infobox status, reference count)
- Per-sentence verdict table
- Key issues summary (grouped by verdict type)
- Recommended action procedures (condensed from the taskgraph)
- Execution order (topological sort)

---

## Workflow: Running a Full Audit

### Step-by-step checklist

```bash
# ── Phase 1: Diagnosis ──
./scripts/01-diagnose.sh "Pyrrhus Concer"
# Output: diagnosis.json, sentences.jsonl, sources/

# ── Phase 2: Verification (human review) ──
# 1. Read analysis.md for context
# 2. Read each cited source from sources/ or via web
# 3. Edit verification_stub.json → verification.json
#    Fill in verdict, correction, source_quote for every sentence
# 4. Validate: python3 -m json.tool verification.json > /dev/null

# ── Phase 3: Taskgraph Generation ──
./scripts/04-generate-taskgraph.sh "Pyrrhus Concer"
# Output: taskgraph.json, analysis.md

# ── Optional: Validate ──
python3 validate.py taskgraph.json
```

### Per-article resource estimates

| Article size | Phase 1 | Phase 2 (human) | Phase 3 |
|---|---|---|---|
| Stub (<2 KB, 3–5 sentences) | <30s | 5–10 min | <10s |
| Start (2–15 KB, 10–30 sentences) | <1 min | 20–60 min | <10s |
| C-class (15–30 KB, 30–80 sentences) | 1–2 min | 1–3 hours | <10s |
| B-class+ (30+ KB, 80+ sentences) | 2–5 min | 3–8 hours | <10s |

Phase 2 dominates the runtime. Budget accordingly.

---

## Tooling

### 🔧 Diagnosis Script (`scripts/01-diagnose.sh`)

Runs Phase 1 end-to-end for a given article title.

```bash
./scripts/01-diagnose.sh "Pyrrhus Concer"
./scripts/01-diagnose.sh "Albert Einstein" --include-db  # with database assessment lookup
./scripts/01-diagnose.sh "Python (programming language)" --format compact
```

Produces: `diagnosis.json`, `sentences.jsonl`, `sources/`

### 🔧 Taskgraph Generator (`scripts/04-generate-taskgraph.sh`)

Runs Phase 3 end-to-end.

```bash
# Must have verification.json + diagnosis.json in working directory
./scripts/04-generate-taskgraph.sh
./scripts/04-generate-taskgraph.sh --project-dir /path/to/project
```

Produces: `taskgraph.json`, `analysis.md`

Includes a staleness check: if `verification.json` is newer than `analysis.md`,
the script warns and requires `--force` to overwrite.

### 🔧 Taskgraph Validator (`validate.py`)

Validates a taskgraph against the schema and checks the DAG.

```bash
python3 validate.py taskgraph.json
python3 validate.py path/to/taskgraph.json --verbose
```

Reports:
- JSON Schema conformance
- DAG acyclicity (Kahn's algorithm)
- Dependency reference integrity
- Verify step well-formedness
- Topological execution order

### 📚 Intermediate Format Reference (`references/intermediate-formats.md`)

Full spec for:
- `diagnosis.json` — all structural fields and their types
- `sentences.jsonl` — sentence-at-a-time schema
- `verification_stub.json` / `verification.json` — verdict data model with all verdict types
- Citation accessibility tracking

### 📚 Verification Protocol (`references/verification-protocol.md`)

Extended guidance for the human Phase 2 reviewer:
- Source hierarchy (when to trust one source over another)
- How to handle conflicting sources
- BLP-specific considerations
- What to do when a source contradicts itself
- Working with the Wayback Machine
- Assessing source reliability (academic journals → news → primary sources → blogs)

### 🧩 Taskgraph Schema (`assets/taskgraph.schema.json`)

The JSON Schema defining the taskgraph contract. Shared across all articles.
Supports:

- 7 action types: `edit_wikitext`, `insert_after`, `edit_talk_page`, `replace_text`, `fetch_source`, `run_shell`, `write_file`
- 8 verify types: `page_contains`, `page_not_contains`, `infobox_exists`, `section_exists`, `assessment_equals`, `revision_has_comment`, `file_exists`, `shell_check`
- 3 failure policies: `revert_and_report`, `skip_and_report`, `retry_and_report`
- 6 task categories: `factual_correction`, `npov_rewrite`, `structural`, `infobox`, `citation`, `grammar`, `verification`, `maintenance`

### 🧩 Analysis Template (`assets/analysis-template.md`)

Markdown template for the Phase 3 human-readable report. Fill-in-the-blanks style
with slots. The generator fills these from `verification.json` + `taskgraph.json`.

```markdown
<!-- AUTO-GENERATED from verification.json + taskgraph.json
     Do not edit by hand. Generated: {{TIMESTAMP}} -->

# Article Audit: {{ARTICLE_TITLE}}

{{QUICK_STATS_TABLE}}

## Per-Sentence Verdicts

{{SENTENCE_VERDICT_TABLE}}

## Key Issues

{{KEY_ISSUES}}

## Execution Order

{{EXECUTION_ORDER}}
```

**⚠️ Never edit the generated `analysis.md` directly.** If the report needs
changes, modify the template above or the source data (`verification.json`)
and regenerate. The auto-generated header at the top of every output file
warns against hand-editing.

### 🧩 Example Output — Clean Audit (`assets/example-output.md`)

A complete Phase 1–2 audit report for the article [[He Tingbo]], demonstrating
the expected format and depth of the `analysis.md` output. Includes:
- Structural diagnosis with findings table
- NPOV keyword scan results
- Per-sentence verification (29 sentences, all classified)
- Recommended taskgraph

**28 of 29 sentences confirmed.** No factual errors, no NPOV violations.
Useful as a baseline for articles that are already in good shape.

### 🧩 Example Output — Problematic Audit (`assets/example-output-problematic.md`)

A complete audit report for the article [[Pyrrhus Concer]], showing the same
format applied to an article with multiple issues:
- **Factual error:** enslaver identity (Pyrrhus → Pelletreau)
- **NPOV/OR block:** 9 sentences of editorial essay (45% of article body)
- **Under-assessment:** Stub when it should be Start
- **Missing infobox, poor section structure, citation dumping**

**12 of 20 sentences confirmed. 5 NPOV/OR violations. 1 factual error.**
Useful for pattern-matching against articles that need substantive fixes.

### 🧩 NPOV Keywords List (`assets/npov-keywords.txt`)

Machine-readable list of NPOV trigger words and phrases, one per line. Used by
the Phase 1 diagnosis script. Categorized:

```
# Editorial praise
undoubtedly
unquestionably
noteworthy
...

# Speculation
it is possible that
was likely
...
```

---

## Relationship to Other Skills

- **wikipedia-page-anatomy** — Prerequisite for understanding what the diagnosis script finds (infoboxes, sections, categories, templates)
- **wikimedia-wikitext** — Powers the sentence extraction and template parsing in Phase 1
- **wikimedia-page-assessment** — Provides the assessment lookup that Phase 1 uses to determine if an article is under-assessed
- **wikipedia-en-biography-writing** — Defines the NPOV/NOR/BLP standards that Phase 2's human reviewer must apply
- **wikimedia-api-access** — Required for all API calls throughout the pipeline
- **wikimedia-database** — Optional, for enhanced assessment queries in Phase 1
