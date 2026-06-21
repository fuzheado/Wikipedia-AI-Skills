# Skills Audit Report — Wikipedia AI Skills

**Date:** 2026-06-18  
**Scope:** 42 skills in `.claude/skills/`  
**Method:** Full read of all 42 `SKILL.md` files, front matter analysis, cross-reference graph construction, structural pattern comparison

---

## Executive Summary

The skill collection is **comprehensive, well-structured, and largely consistent** — a remarkable achievement for 42 skills totaling ~250KB of documentation. The core strengths are clear domain coverage, rich code examples, consistent tooling sections, and a clear dependency on `wikimedia-api-access` as the foundational skill.

However, the audit reveals **three structural gaps** that, if addressed, would make the skills more discoverable, more interconnected, and more maintainable:

1. **`depends_on` front matter is severely underused** — only 14/42 (33%) declare formal dependencies, despite extensive cross-referencing in body text
2. **`skill_discovery_hints` is missing from 21/42 (50%)** — halving the discoverability of half the skills for keyword-based agent matching
3. **Six skills have zero cross-references** — creating orphaned skills that can't be discovered by following links from related skills

---

## 1. YAML Front Matter Analysis

### 1.1 Field Presence Matrix

| Field | Present In | Missing From | % Coverage |
|-------|-----------|-------------|:----------:|
| `name` | 42/42 | — | 100% |
| `description` | 42/42 | — | 100% |
| `license` | 42/42 (all `MIT`) | — | 100% |
| `compatibility` | 42/42 | — | 100% |
| `last_verified` | 42/42 | — | 100% |
| `skill_discovery_hints` | 21/42 | 21 | **50%** |
| `depends_on` | 14/42 | 28 | **33%** |

### 1.2 Missing `skill_discovery_hints` — 21 Skills

These skills are **undiscoverable by keyword matching** in agent skill selection:

| # | Skill | Has Hints? |
|---|-------|:---------:|
| 1 | `mediawiki-page-navigation` | ❌ |
| 2 | `mediawiki-translate-extension` | ❌ |
| 3 | `pywikibot` | ❌ |
| 4 | `wikidata-vector-search` | ❌ |
| 5 | `wikimedia-auth-oauth` | ❌ |
| 6 | `wikimedia-cdn-assets` | ❌ |
| 7 | `wikimedia-database` | ❌ |
| 8 | `wikimedia-diffs` | ❌ |
| 9 | `wikimedia-page-styling` | ❌ |
| 10 | `wikimedia-pageviews` | ❌ |
| 11 | `wikimedia-toolforge` | ❌ |
| 12 | `wikipedia-categories` | ❌ |
| 13 | `wikipedia-citations` | ❌ |
| 14 | `wikipedia-edit-history` | ❌ |
| 15 | `wikipedia-en-article-audit` | ❌ |
| 16 | `wikipedia-en-biography-writing` | ❌ |
| 17 | `wikipedia-pagetriage-api` | ❌ |
| 18 | `wikipedia-reference-verifiability` | ❌ |
| 19 | `wikipedia-talk-page` | ❌ |
| 20 | `wikipedia-templates` | ❌ |
| 21 | `wikipedia-wikitables` | ❌ |

**Impact:** Half the skills won't surface when an agent searches by keyword. For example, `pywikibot` won't be discovered for "bot framework" or "automated editing" queries.

### 1.3 Missing `depends_on` — 28 Skills

Despite 36/42 skills having cross-references in their body text, only 14 declare formal dependencies in front matter:

| Has `depends_on` | Has Body Refs | Mismatch |
|:---:|:---:|:---:|
| 14 | 36 | **22 skills have body refs but no formal `depends_on`** |

**Examples of skills that SHOULD have `depends_on` but don't:**

| Skill | Body References To | Recommended `depends_on` |
|-------|-------------------|--------------------------|
| `mediawiki-page-navigation` | api-access, templates, page-styling, translate-extension | `[wikimedia-api-access, wikipedia-templates]` |
| `mediawiki-translate-extension` | api-access, templates, page-navigation, page-styling | `[wikimedia-api-access, wikipedia-templates]` |
| `pywikibot` | toolforge, api-access, wikidata, wikitext, auth-oauth, eventstreams | `[wikimedia-api-access, wikidata]` |
| `wikidata` | ml-services, pageviews, categories, commons, api-access, api-strategy, error-handling | `[wikimedia-api-access]` |
| `wikimedia-commons` | thumbnails, svg, pdf, audio-video, sdc, sparql, api-access | `[wikimedia-api-access]` |
| `wikimedia-eventstreams` | ml-services, diffs, pagetriage, api-access, pywikibot | `[wikimedia-api-access]` |
| `wikipedia-page-anatomy` | templates, wikitext, citations, categories, api-access | `[wikimedia-api-access]` |
| `wikipedia-edit-history` | diffs, page-anatomy, talk-page, api-access | `[wikimedia-api-access]` |
| `wikipedia-categories` | page-anatomy, pywikibot, api-access | `[wikimedia-api-access]` |
| `wikimedia-diffs` | edit-history, ml-services, api-access, eventstreams | `[wikimedia-api-access]` |
| `wikipedia-en-article-audit` | page-anatomy, wikitext, page-assessment, api-access, biography-writing, database | `[wikimedia-api-access, wikimedia-wikitext, wikipedia-page-anatomy]` |
| `wikipedia-notability-assessment` | biography-writing, pagetriage, citations, api-access, cirrussearch, ml-services, error-handling | `[wikimedia-api-access]` |

### 1.4 `compatibility` Field

| Value | Count |
|-------|:----:|
| `opencode` | 41 |
| `all` | 1 (`wikimedia-cdn-assets`) |

**Recommendation:** `opencode` vs `all` is a meaningful distinction only if the agent runtime checks this field. Otherwise, standardize on one value.

### 1.5 Description Quality

Generally good — most descriptions are 1 sentence that clearly states what the skill covers. A few are noticeably weaker:

- `wikimedia-database`: "Execute SQL queries against Wikipedia database replicas..." — fine but could mention Toolforge dependency
- `wikimedia-pageviews`: "Retrieve traffic and popularity statistics..." — accurate but could mention both SQL and REST approaches
- `wikimedia-cdn-assets`: "Load JavaScript, CSS, and fonts for Toolforge tools..." — accurate but narrow; misses the fact that this is about the privacy-preserving mirror specifically

---

## 2. Cross-Linking Analysis

### 2.1 Most Referenced Skills (Inbound Links)

These are the "hub" skills that others depend on:

| Rank | Skill | Inbound Refs | Hub Type |
|:----:|-------|:-----------:|----------|
| 1 | `wikimedia-api-access` | 67 | **Foundation** — User-Agent & rate limiting |
| 2 | `wikidata` | 17 | **Data** — SPARQL & entity queries |
| 3 | `wikimedia-commons` | 14 | **Platform** — file repo entry point |
| 4 | `wikimedia-auth-oauth` | 11 | **Auth** — authentication patterns |
| 5 | `pywikibot` | 10 | **Framework** — bot framework |
| 5 | `wikimedia-commons-thumbnails` | 10 | **Subsystem** — thumbnails |
| 7 | `wikimedia-wikitext` | 9 | **Tool** — wikitext parsing |
| 8 | `wikipedia-templates` | 8 | **Content** — template syntax |
| 9 | `wikimedia-ml-services` | 7 | **ML** — scoring services |
| 9 | `wikimedia-commons-sparql` | 7 | **Query** — Commons SPARQL |

### 2.2 Skills with Zero Outbound Cross-References

These are **orphaned** — no reader can discover related skills by following links:

| Skill | Why Orphaned |
|-------|-------------|
| `wikimedia-cdn-assets` | Self-contained topic — but could link to `wikimedia-toolforge` and `wikimedia-security-and-privacy` |
| `wikimedia-database` | **Concerning** — this skill's extensive `pymysql` code duplicates patterns from `wikimedia-page-assessment` and should cross-link |
| `wikimedia-page-assessment` | **Concerning** — the SQL tunnel pattern here is identical to `wikimedia-database`; the WikiProject subpage discovery SOP duplicates content from `wikipedia-talk-page` |
| `wikimedia-phabricator` | Self-contained — but should link to `wikimedia-toolforge` and `wikipedia-error-handling` |
| `wikipedia-en-biography-writing` | **Concerning** — has a complete notability SOP that should link to `wikipedia-notability-assessment` (the dedicated skill for exactly this topic) |
| `wiktionary-and-wikisource` | Self-contained — but should link to `wikimedia-commons-pdf` (Wikisource OCR/PDF integration) |

### 2.3 Cross-Reference Format Inconsistency

Skills use several different formats for the same cross-reference:

```
[wikimedia-api-access](../wikimedia-api-access/SKILL.md)    ← Most common, correct
[wikimedia-api-access](../wikimedia-api-access/SKILL.md)    ← Same
[wikimedia-api-access](../wikimedia-api-access/)            ← Missing SKILL.md (rare)
[API access](../wikimedia-api-access/SKILL.md)              ← Inconsistent display name
[wikimedia-api-access]                                      ← Missing link path (rare)
```

**Recommendation:** Standardize on `[skill-name](../skill-name/SKILL.md)` everywhere.

### 2.4 Missing Cross-References — Key Gaps

| Reader Is In | Should Also See | Currently Missing? |
|-------------|----------------|:-----------------:|
| `wikipedia-en-biography-writing` | `wikipedia-notability-assessment` | ✅ Missing (has own shortened notability SOP instead) |
| `wikimedia-database` | `wikimedia-page-assessment` | ✅ Missing (duplicate tunnel/pymysql code) |
| `wikimedia-page-assessment` | `wikimedia-database` | ✅ Missing (duplicate SQL setup) |
| `wikimedia-commons-thumbnails` | `wikimedia-cdn-assets` | ✅ Missing (cdn-assets is relevant for Toolforge thumbnail proxying) |
| `wikipedia-reference-verifiability` | `wikipedia-citations` | ✅ Missing (citation analysis overlaps) |
| `wikipedia-pagetriage-api` | `wikipedia-reference-verifiability` | ✅ Missing (NPP workflow naturally leads to ref checking) |
| `mediawiki-translate-extension` | `wikimedia-i18n-l10n-for-tools` | ✅ Missing (both cover i18n but for different contexts) |
| `wikimedia-i18n-l10n-for-tools` | `mediawiki-translate-extension` | ✅ Already present ✓ |

### 2.5 Cross-Reference Graph — The "Family Tree"

```
wikimedia-api-access  ←──── 67 inbound (Foundation)
    ├── wikimedia-auth-oauth
    │   └── wikimedia-commons-sdc
    ├── wikimedia-api-strategy
    ├── wikidata
    │   └── wikidata-vector-search
    ├── wikimedia-commons
    │   ├── wikimedia-commons-thumbnails
    │   ├── wikimedia-commons-svg
    │   ├── wikimedia-commons-pdf
    │   ├── wikimedia-commons-audio-video
    │   ├── wikimedia-commons-sparql
    │   └── wikimedia-commons-sdc
    ├── wikimedia-wikitext
    │   ├── wikipedia-reference-verifiability
    │   ├── wikipedia-wikitables
    │   └── wikipedia-en-article-audit
    ├── wikipedia-templates
    │   ├── mediawiki-page-navigation
    │   ├── mediawiki-translate-extension
    │   └── wikimedia-page-styling
    ├── pywikibot
    ├── wikimedia-eventstreams
    ├── wikimedia-ml-services
    ├── wikipedia-error-handling
    ├── wikipedia-categories
    │   └── wikimedia-search-cirrussearch
    ├── wikipedia-citations
    ├── wikipedia-edit-history
    │   └── wikimedia-diffs
    ├── wikipedia-page-anatomy
    │   └── wikipedia-talk-page
    ├── wikipedia-notability-assessment
    ├── wikipedia-pagetriage-api
    └── wikipedia-en-biography-writing (<- orphan: should link to notability-assessment)
```

---

## 3. Content Length Analysis

### 3.1 Size Distribution

| Category | Count | Size Range | Representative |
|----------|:----:|------------|----------------|
| **Compact** (<10KB) | 5 | 6.8K–8.8K | `wikimedia-database`, `wikimedia-cdn-assets`, `wikimedia-pageviews`, `wikipedia-pagetriage-api` |
| **Standard** (10–25KB) | 22 | 10.7K–24.2K | Most skills fall here |
| **Comprehensive** (25–35KB) | 12 | 25.7K–34.9K | `wikimedia-ml-services`, `wikimedia-commons`, `wikidata`, `pywikibot` |
| **Extensive** (>35KB) | 3 | 35.8K–43.1K | `wikipedia-en-article-audit`, `wikimedia-eventstreams`, `wikimedia-commons-sdc` |

**Analysis:** The size distribution is healthy. The 5 compact skills are genuinely narrow in scope and don't appear to be missing content. The 3 extensive skills are appropriately large given their topic complexity (full audit pipeline, real-time streaming with 10+ stream types, complete SDC editing with batch/GLAM workflows).

### 3.2 Correlation: Size vs. Cross-References

| Size Quartile | Avg Unique Outbound Refs | Avg Inbound Refs |
|:---:|:---:|:---:|
| Q1 (Compact) | 0.8 | 2.2 |
| Q2 (Standard) | 4.2 | 5.8 |
| Q3 (Comprehensive) | 4.7 | 8.3 |
| Q4 (Extensive) | 5.7 | 6.0 |

**Finding:** Compact skills have dramatically fewer outbound references — not because they don't need them, but because they were likely written earlier or more quickly. The relationship between size and cross-referencing indicates that longer skills had more editorial attention.

---

## 4. Structural Consistency

### 4.1 Common Structural Elements

| Element | Present In | Notes |
|---------|:----------:|-------|
| Header warning (User-Agent) | 38/42 | Missing from: `wikimedia-database`, `wikimedia-page-assessment`, `wikimedia-pageviews`, `wikimedia-cdn-assets` |
| Prerequisites box | ~25/42 | Format varies: some use `> 📖`, some `> 💡`, some plain text |
| Table of Contents | 8/42 | Only the largest 8 skills have ToCs — this is a deliberate editorial choice, not a gap |
| Tooling section | 40/42 | All except `wikimedia-cdn-assets` (has assets but no scripts section header) and one other have tooling at the end |
| Guardrails section | ~18/42 | Named "Guardrails" in some, "Constraint & Guardrails" in others, "Anti-Patterns" elsewhere |
| Reference Links section | ~25/42 | Format varies: bullet list, table, or mixed |
| Related Skills section | ~30/42 | Named "Related Skills", "Cross-References", "Relationship to Other Skills" inconsistently |

### 4.2 Structural Archetypes

Skills follow one of three structural patterns:

**Pattern A: SOP-Driven** (most common, ~30 skills)
```
Header warning → Prerequisites → SOP sections → Guardrails → Tooling
```

**Pattern B: Reference-Centric** (~8 skills)
```
Header warning → Quick Reference table → Detailed sections → Tooling
```
Used by: `wikidata`, `wikimedia-commons`, `wikimedia-commons-sparql`, etc.

**Pattern C: Workflow/Pipeline** (~4 skills)
```
Overview → Phase/Step 1 → Phase/Step 2 → ... → Tooling
```
Used by: `wikipedia-en-article-audit`, `wikimedia-auth-oauth`

### 4.3 Guardrail/Anti-Pattern Naming

The concept of "don't do this / do this instead" appears under at least 4 different names:

| Name | Used By |
|------|---------|
| "Guardrails" | `wikipedia-citations`, `wikimedia-cdn-assets`, `wikipedia-en-biography-writing` ("Anti-Hallucination Rules"), `wikimedia-i18n-l10n-for-tools`, `wikimedia-search-cirrussearch`, `wikimedia-security-and-privacy`, `wikipedia-notability-assessment` |
| "Anti-Patterns to Avoid" | `wikimedia-wikitext`, `wikimedia-diffs`, `wikimedia-api-strategy` |
| "Common Mistakes" / "Common Pitfalls" | `wikimedia-auth-oauth`, `wikimedia-ml-services` ("Pitfalls Across All Models"), `wikimedia-commons-thumbnails` |
| "Known Limitations" | `wikidata-vector-search` |

**Recommendation:** Standardize on "Guardrails" for policy/rules and "Anti-Patterns" for code/approach mistakes.

---

## 5. Content Quality & Correctness

### 5.1 Content Duplication

Several skills duplicate significant content:

| Content | Appears In | Severity |
|---------|-----------|:--------:|
| SSH tunnel to Toolforge + pymysql connection pattern | `wikimedia-database`, `wikimedia-page-assessment` | **High** — identical code blocks, should be a shared reference |
| User-Agent format + boilerplate | `wikimedia-api-access` + all 38 referencing skills | **Acceptable** — these are brief required reminders |
| Notability assessment SOP | `wikipedia-notability-assessment` (dedicated), `wikipedia-en-biography-writing` (embedded) | **Medium** — biography-writing should link, not duplicate |
| Wikipedia category policy (3 tests) | `wikipedia-categories` (dedicated), `wikipedia-page-anatomy` (summary) | **Acceptable** — anatomy gives a brief overview, categories goes deep |
| Pageview SQL query pattern | `wikimedia-pageviews` (dedicated), `wikimedia-page-assessment` (mentions) | **Low** |
| Citation template reference | `wikipedia-citations` (dedicated), `wikipedia-page-anatomy` (summary) | **Acceptable** |
| Wikitext anti-patterns (regex vs AST) | `wikimedia-wikitext` (dedicated), multiple others mention it | **Acceptable** |

### 5.2 Technical Accuracy Notes

No **factual errors** were found. A few minor observations:

- `wikimedia-database`: References `enwiki.analytics.db.svc.wikimedia.cloud` as the tunnel target — this is correct for analytics replicas, but the main replicas use `enwiki.web.db.svc.wikimedia.cloud`. The skill is correct for its use case (analytics), but users may be confused if they try to connect to the web replicas.
- `wikimedia-commons`: The CORS section cross-references `wikimedia-commons-thumbnails` Section 10, which is the correct location.
- `wikidata-vector-search`: Correctly notes that `instanceof` filter is non-functional in the current release (v0.2.1).

### 5.3 Conciseness Assessment

| Assessment | Skills |
|------------|--------|
| **Too compact** (missing essential context) | `wikipedia-pagetriage-api` — truncates mid-sentence at end |
| **Appropriately concise** | Most skills (~30) |
| **Slightly verbose** (could trim 10-20%) | `wikimedia-commons-sdc` — repetitive example patterns; `wikimedia-page-styling` — CSS property lists are very long |
| **Needs trimming** (>20% could be cut) | None are severely bloated |

---

## 6. Tooling & Assets Quality

### 6.1 Asset Pattern Consistency

Most skills include tooling organized as:

```
Tooling/
├── scripts/        ← Shell scripts (~2-5 per skill)
├── assets/         ← Python libraries, templates, examples
├── references/     ← Deep reference docs
└── tests/          ← Test suites (present in ~15 skills)
```

**Stars:** `wikimedia-auth-oauth` has an exceptional multi-file asset system (Flask app, bot password editor, reusable OAuth2 client, multiple reference docs).  
**Stars:** `wikimedia-ml-services` has an interactive playground (`playground.sh`) that's very agent-friendly.  
**Stars:** `wikipedia-en-article-audit` has a formal JSON Schema (`taskgraph.schema.json`) for its output contract.

### 6.2 Missing Tooling

| Skill | Missing |
|-------|---------|
| `wikimedia-cdn-assets` | Has assets (`load-template.html`, `load-template.js`) but no `scripts/` directory for the checker |
| `wikimedia-database` | Sample SQL queries are in `assets/sample-queries.sql` — but no Python tool for common patterns |
| `wikimedia-pageviews` | Good script coverage, no test suite |

---

## 7. Domain Coverage Analysis

### 7.1 Domain Map

```
                    ┌──────────────────┐
                    │  FOUNDATION (3)  │
                    │ api-access        │
                    │ api-strategy      │
                    │ error-handling    │
                    └────────┬─────────┘
                             │
       ┌─────────────────────┼─────────────────────┐
       │                     │                     │
┌──────▼──────┐    ┌─────────▼────────┐    ┌──────▼──────┐
│  AUTH (1)   │    │  DATA & QUERY (7)│    │  CONTENT (8)│
│ auth-oauth  │    │ wikidata         │    │ page-anatomy │
└──────┬──────┘    │ wikidata-vector  │    │ categories   │
       │           │ database         │    │ citations    │
       │           │ page-assessment  │    │ templates    │
       │           │ pageviews        │    │ wikitext     │
       │           │ ml-services      │    │ wikitables   │
       │           │ cirrussearch     │    │ diffs        │
       │           │ commons-sparql   │    │ edit-history │
       │           └──────────────────┘    │ talk-page    │
       │                                   └──────────────┘
       │
┌──────▼──────────┐    ┌──────────────────┐    ┌──────────────┐
│  COMMONS (6)    │    │  TOOLING & PLATFORM (8)    │  POLICIES (4) │
│ commons         │    │ pywikibot        │    │ page-styling │    │ notability    │
│ ├ thumbnails    │    │ toolforge        │    │ page-nav     │    │ biography     │
│ ├ svg           │    │ cdn-assets       │    │ translate    │    │ audit         │
│ ├ pdf           │    │ eventstreams     │    │ i18n-tools   │    │ reference-    │
│ ├ audio-video   │    │ phabricator      │    │               │    │   verifiability│
│ ├ sdc           │    │ security-privacy │    │               │    │ pagetriage    │
│ └ sparql        │    └──────────────────┘    └──────────────┘    └──────────────┘
└─────────────────┘                                             
       │
┌──────▼──────────┐
│  SISTER PROJECTS│
│  wiktionary-and-│
│  wikisource     │
└─────────────────┘
```

### 7.2 Domain Gaps

| Potential Gap | Assessment |
|---------------|------------|
| **Wikidata editing** (write operations) | Covered by `pywikibot` (Wikidata integration section) and `wikimedia-commons-sdc` (SDC writes), but no dedicated "Wikidata editing" skill. Acceptable gap — the `wikidata` skill is read-focused by design. |
| **Wikipedia dispute resolution** | Not covered. Could be a useful skill for agents that encounter edit wars or content disputes. Low priority — this is human-mediated. |
| **Wikimedia Cloud VPS** | Not covered separately from Toolforge. Toolforge is the primary platform; Cloud VPS is a niche power-user option. |
| **Wikipedia bots approval process** | Mentioned in `pywikibot` but not as a detailed SOP. |
| **Commons deletion/nomination** | Covered tangentially in `wikimedia-commons` but no dedicated skill for the deletion process. |
| **Cross-wiki spam detection** | Not covered. |

### 7.3 Coverage Depth Assessment

| Depth Level | Skills | Assessment |
|:-----------:|--------|-----------|
| **Expert** (production-ready patterns, edge cases, caching strategies) | `wikimedia-api-access`, `wikimedia-auth-oauth`, `wikimedia-ml-services`, `wikimedia-eventstreams`, `wikipedia-en-article-audit`, `wikimedia-commons-thumbnails`, `wikimedia-commons-sdc` | Excellent |
| **Thorough** (complete API coverage, good examples) | Most skills (~25) | Good |
| **Adequate** (covers the basics well) | `wikimedia-cdn-assets`, `wikimedia-pageviews`, `wikipedia-pagetriage-api`, `wikimedia-database`, `wikipedia-reference-verifiability` | Fine for scope but could use 20-30% more depth |
| **Needs deepening** | None are inadequate | — |

---

## 8. Recommendations — Priority-Ordered

### P1: Critical (Structural & Discoverability)

| # | Recommendation | Effort | Impact |
|:--:|---------------|:------:|:------:|
| 1 | **Add `skill_discovery_hints` to all 21 skills missing it.** Each needs 2-4 keyword arrays. See Appendix A for suggested hints. | Medium | **High** — doubles discoverability |
| 2 | **Add `depends_on` to the 22 skills that have body cross-references but no formal dependency declarations.** See Section 1.3 for specific recommendations. | Low | **High** — enables dependency-aware skill loading |
| 3 | **Fix the 6 orphaned skills (zero outbound refs).** Each should link to at least 2 related skills. See Section 2.2 for specific targets. | Low | **Medium** — improves navigation graph |
| 4 | **De-duplicate SSH tunnel/pymysql code** between `wikimedia-database` and `wikimedia-page-assessment`. Prefer cross-referencing to a single source of truth. | Low | **Medium** — reduces maintenance burden |

### P2: Important (Consistency & Quality)

| # | Recommendation | Effort | Impact |
|:--:|---------------|:------:|:------:|
| 5 | **Standardize cross-reference format.** Use `[skill-name](../skill-name/SKILL.md)` everywhere. Do a one-pass find/replace. | Low | **Medium** |
| 6 | **Standardize guardrail/anti-pattern section naming.** Use "Guardrails" for policy/rules and "Anti-Patterns" for coding mistakes. | Low | **Low** |
| 7 | **Standardize "Related Skills" section name.** Currently varies: "Related Skills", "Cross-References", "Relationship to Other Skills". Pick one. | Low | **Low** |
| 8 | **Add User-Agent warning header** to the 4 skills that lack it: `wikimedia-database`, `wikimedia-page-assessment`, `wikimedia-pageviews`, `wikimedia-cdn-assets`. | Low | **Medium** — policy compliance |
| 9 | **Add `wikipedia-notability-assessment` cross-reference** to `wikipedia-en-biography-writing`. The biography skill has its own shortened notability SOP that should link to the full skill. | Low | **Medium** |
| 10 | **Fix truncated `wikipedia-pagetriage-api` SKILL.md.** The file ends mid-word ("Grea"). | Low | **Medium** — correctness |

### P3: Nice-to-Have (Depth & Coverage)

| # | Recommendation | Effort | Impact |
|:--:|---------------|:------:|:------:|
| 11 | **Add test suites** to skills that have Python assets but no tests (`wikimedia-pageviews`, `wikimedia-cdn-assets`). | Medium | **Low** |
| 12 | **Add a quick-reference card** pattern to more skills. `wikimedia-phabricator` has an excellent visual card; `wikidata` and `wikimedia-commons` have great quick-reference tables. Add to: `wikimedia-toolforge`, `wikipedia-categories`, `pywikibot`. | Medium | **Medium** |
| 13 | **Consider splitting `wikimedia-commons-sdc`** (43KB, the largest) into "read" vs "write" sub-skills, similar to how commons-SPARQL is separate from commons-SDC. | High | **Low** — the skill is well-organized despite its size |
| 14 | **Add a "Wikipedia Dispute Resolution" skill** covering 3RR, ANI, dispute resolution noticeboard, mediation — for agents that encounter edit wars. | High | **Low** — niche use case |
| 15 | **Add consistency to the `last_verified` dates.** Most are 2026-06-10 to 2026-06-16 — a 6-day window. Consider a batch update script. | Low | **Low** |

---

## 9. Summary Dashboard

| Metric | Current | Target | Status |
|--------|:------:|:------:|:------:|
| Skills with `skill_discovery_hints` | 21/42 (50%) | 42/42 (100%) | 🔴 |
| Skills with `depends_on` | 14/42 (33%) | 36/42 (86%) | 🔴 |
| Orphaned skills (0 outbound refs) | 6/42 (14%) | 0/42 (0%) | 🟡 |
| Duplicated content blocks | 2 significant | 0 | 🟡 |
| Skills without User-Agent warning | 4/42 (10%) | 0/42 (0%) | 🟡 |
| Truncated/corrupted files | 1/42 (2%) | 0/42 (0%) | 🟡 |
| Structural consistency (section naming) | ~70% | 100% | 🟢 |
| Cross-reference format consistency | ~85% | 100% | 🟢 |
| Technical accuracy | 100% | 100% | 🟢 |
| Consistent `last_verified` dates | 1-week window | 1-week window | 🟢 |

**Overall Grade: B+** — Strong foundation with clear, addressable gaps.

---

## Appendix A: Suggested `skill_discovery_hints` for Missing Skills

### mediawiki-page-navigation
```yaml
skill_discovery_hints:
  - keywords: ["navigation", "menu bar", "breadcrumbs", "subpage", "tab navigation", "#titleparts"]
  - keywords: ["page hierarchy", "sub-navigation", "dynamic menu", "AvoinGLAM"]
```

### mediawiki-translate-extension
```yaml
skill_discovery_hints:
  - keywords: ["Translate extension", "page translation", "translatable", "<translate>", "translation unit", "language subpage"]
  - keywords: ["Special:MyLanguage", "#timef", "translation memory", "message group", "fuzzy translation"]
```

### pywikibot
```yaml
skill_discovery_hints:
  - keywords: ["Pywikibot", "bot", "automated editing", "page generator", "pwb.py", "MediaWiki bot"]
  - keywords: ["bulk edit", "category operations", "template harvesting", "archive bot", "replace.py"]
```

### wikidata-vector-search
```yaml
skill_discovery_hints:
  - keywords: ["vector search", "semantic search", "embedding", "similarity score", "find QID", "fuzzy match"]
  - keywords: ["wd-vectordb", "concept search", "meaning search", "RRF", "cross-lingual search"]
```

### wikimedia-auth-oauth
```yaml
skill_discovery_hints:
  - keywords: ["authentication", "OAuth", "bot password", "login", "CSRF token", "credential"]
  - keywords: ["authorization", "access token", "refresh token", "consumer registration", "Special:BotPasswords"]
```

### wikimedia-cdn-assets
```yaml
skill_discovery_hints:
  - keywords: ["CDN", "cdnjs", "Toolforge assets", "JavaScript CDN", "CSS CDN", "font loading"]
  - keywords: ["tools-static", "cdnjs mirror", "privacy CDN", "Wikimedia CDN"]
```

### wikimedia-database
```yaml
skill_discovery_hints:
  - keywords: ["SQL", "database", "replica", "Toolforge database", "enwiki_p", "MySQL"]
  - keywords: ["SSH tunnel", "pymysql", "query Wikipedia", "schema", "page table", "revision table"]
```

### wikimedia-diffs
```yaml
skill_discovery_hints:
  - keywords: ["diff", "compare revisions", "edit comparison", "action=compare", "diffsize"]
  - keywords: ["visual diff", "rendered comparison", "change detection", "byte change"]
```

### wikimedia-page-styling
```yaml
skill_discovery_hints:
  - keywords: ["TemplateStyles", "CSS", "styling", "grid layout", "flexbox", "design system"]
  - keywords: ["wiki design", "custom CSS", "templatestyles", "card layout", "button styling"]
```

### wikimedia-pageviews
```yaml
skill_discovery_hints:
  - keywords: ["pageviews", "traffic", "popularity", "article views", "views per article"]
  - keywords: ["top pages", "pageview API", "daily views", "analytics"]
```

### wikimedia-toolforge
```yaml
skill_discovery_hints:
  - keywords: ["Toolforge", "tool hosting", "Kubernetes", "web service", "cron job", "deploy"]
  - keywords: ["toolforge tools create", "become", "webservice", "toolforge jobs"]
```

### wikipedia-categories
```yaml
skill_discovery_hints:
  - keywords: ["category", "categorization", "category tree", "WP:CATDEF", "WP:CATV"]
  - keywords: ["sort key", "DEFAULTSORT", "hidden category", "category redirect", "PetScan"]
```

### wikipedia-citations
```yaml
skill_discovery_hints:
  - keywords: ["citation", "reference", "cite web", "cite book", "CS1", "Wayback Machine"]
  - keywords: ["dead link", "archive URL", "bare URL", "Citoid", "DOI", "ISBN"]
```

### wikipedia-edit-history
```yaml
skill_discovery_hints:
  - keywords: ["edit history", "revision history", "page history", "user contributions", "rollback"]
  - keywords: ["revision ID", "undo", "edit summary", "minor edit", "mw-reverted"]
```

### wikipedia-en-article-audit
```yaml
skill_discovery_hints:
  - keywords: ["article audit", "audit", "NPOV check", "factual verification", "taskgraph"]
  - keywords: ["article diagnosis", "structural audit", "sentence verification", "DAG"]
```

### wikipedia-en-biography-writing
```yaml
skill_discovery_hints:
  - keywords: ["biography", "BLP", "living persons", "article creation", "drafting"]
  - keywords: ["NPOV", "biography writing", "infobox person", "WP:NOR", "verifiability"]
```

### wikipedia-pagetriage-api
```yaml
skill_discovery_hints:
  - keywords: ["PageTriage", "NPP", "new page patrol", "unreviewed", "page curation"]
  - keywords: ["pagetriagelist", "patrol", "new pages feed", "review status"]
```

### wikipedia-reference-verifiability
```yaml
skill_discovery_hints:
  - keywords: ["reference URLs", "citation URLs", "bare ref", "URL detection", "verifiability check"]
  - keywords: ["named ref", "shortened footnote", "url= parameter", "reference analysis"]
```

### wikipedia-talk-page
```yaml
skill_discovery_hints:
  - keywords: ["talk page", "DiscussionTools", "Reply Tool", "topic subscription", "WikiProject banner"]
  - keywords: ["talk page archive", "discussion", "indentation", "ping", "@-mention"]
```

### wikipedia-templates
```yaml
skill_discovery_hints:
  - keywords: ["template", "wikitext template", "parser function", "transclusion", "Lua module"]
  - keywords: ["#if", "#switch", "#invoke", "TemplateData", "TemplateStyles"]
```

### wikipedia-wikitables
```yaml
skill_discovery_hints:
  - keywords: ["wikitable", "table", "sortable", "colspan", "rowspan", "data table"]
  - keywords: ["table generation", "CSV to wikitable", "wikitable styling", "mw-collapsible"]
```

---

*End of report.*
