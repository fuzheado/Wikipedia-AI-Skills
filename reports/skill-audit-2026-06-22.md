# Wikipedia-AI-Skills: Comprehensive Audit Report

**Date:** 2026-06-22
**Skills Audited:** 45
**New Additions (focus):** `commons-file-resolution`, `toolforge-nodejs`

---

## 1. Executive Summary

The 45-skill library is in **excellent overall health**. Scores break down as:

| Rating | Count | % |
|--------|-------|---|
| Excellent | 32 | 71% |
| Good | 12 | 27% |
| Fair | 1 | 2% |
| Poor | 0 | 0% |

### Top-Level Findings

1. **Cross-referencing is the #1 systemic weakness** — 40+ missed bidirectional links, CORS sections duplicated across 3+ skills, and `depends_on` arrays frequently lagging body content
2. **YAML descriptions trend too long** — 18/45 skills exceed 35 words; 4 exceed 50 words
3. **Two skills are candidates for splitting** — `wikimedia-i18n-l10n-for-tools` (1,072 lines) and `wikimedia-commons-sdc` (5,126 words)
4. **The two new additions are excellent** — `commons-file-resolution` and `toolforge-nodejs` both score "excellent" with only minor fixable issues
5. **One skill has a code bug** — `wiktionary-and-wikisource`: `extract_translations()` never populates the `translations` dict

---

## 2. New Addition Deep-Dive

### `commons-file-resolution` ⭐ EXCELLENT
**Score:** Excellent | **Words:** 2,461 | **Lines:** ~500

| Area | Assessment |
|------|-----------|
| Structure | Excellent — Problem → Quick Ref → 5 SOPs → Cheat Sheet → CORS table → See Also |
| Completeness | Covers Special:FilePath, Action API, cache-busting, local caching, cross-wiki — all practical use cases |
| Cross-refs | Only 3 internal links — should add `wikimedia-auth-oauth`, `wikimedia-commons-sdc` |
| Correctness | MD5 hash split explanation slightly ambiguous (`[0:2]` vs directory structure) |
| Conciseness | Nearly flawless — well-written and focused |

**Top 3 Fixes:**
1. Clarify hash_path split: "first char = directory, first 2 = subdirectory"
2. Add cross-refs to `wikimedia-auth-oauth` and `wikimedia-commons-sdc`
3. Note minimum Node.js version for `redirect: 'manual'` behavior

### `toolforge-nodejs` ⭐ EXCELLENT
**Score:** Excellent | **Words:** 2,756 | **Lines:** 602

| Area | Assessment |
|------|-----------|
| Structure | Excellent — 9 numbered SOPs from bootstrap to cron to restarting, pitfall table |
| Completeness | Covers zero-dep pattern, PORT, static serving, npm, env vars, cron — thorough |
| Cross-refs | References `commons-file-resolution` and `commons-commons-thumbnails` (good for image context!) |
| Correctness | **1 real bug:** `filePath.startsWith(__dirname)` is fragile (matches sibling dirs) |
| Conciseness | SOP 1.3 has a 60-line server.mjs inline — belongs in an asset file |

**Top 3 Fixes:**
1. **Fix path traversal check** — use `path.resolve()` + check is-within, not just `startsWith`
2. Move full server.mjs to an asset file, keep critical pattern inline
3. Flag `:latest` Docker tag as discouraged for production; note pinned version

---

## 3. Cross-Referencing Audit

### Density by Domain

| Domain | Skills | Avg Internal Ref Links | Status |
|--------|--------|----------------------|--------|
| Commons | 8 | 10.9 | ✅ Strong internal routing |
| Toolforge/Infra | 8 | 6.1 | ⚠️ Hub doesn't route to children |
| APIs & Auth | 7 | 6.3 | ⚠️ Missing bidirectional pairs |
| Wikidata/Search | 5 | 7.6 | ⚠️ pageviews ↔ assessment gap |
| Content/Editing | 10 | 5.9 | ⚠️ 11 missing link pairs identified |
| Tools/Special | 7 | 4.3 | 🔴 `wikimedia-wikitext`: 1 link only |

### Critical Missing Bidirectional Links

| Skill A | Skill B | Why Both Ways Matter |
|---------|---------|---------------------|
| `wikimedia-pageviews` | `wikimedia-page-assessment` | Popular_pages bot is the explicit bridge |
| `wikipedia-citations` | `wikipedia-reference-verifiability` | Citation formatting + URL detection are complementary |
| `wikipedia-en-biography-writing` | `wikipedia-en-article-audit` | Writing → Audit → Writing loop |
| `wikimedia-diffs` | `wikipedia-edit-history` | Diffs links to edit-history; edit-history does NOT link back |
| `wikimedia-api-access` | `wikipedia-error-handling` | api-access teaches 403/429 patterns; error-handling teaches recovery — no link from api-access |
| `wikimedia-wikitext` | 6 other skills | Foundation skill referenced by none of the skills that parse text |
| `wikimedia-toolforge` | 5 child skills | Hub skill references only 2 other skills total |
| `commons-file-resolution` | `wikimedia-commons` | Hub doesn't reference this new skill at all |

### Duplicate Content (Same Text Appearing Cross-Skill)

| Content Block | Appears In | Recommendation |
|--------------|-----------|----------------|
| CORS serving patterns | `wikimedia-commons`, `commons-file-resolution`, `wikimedia-commons-thumbnails` | Keep in `commons-file-resolution` only; others cross-ref |
| Wikimedia-commons-sdc references wikimedia-commons | Twice in same relationship box | Fix copy-paste error |
| User-Agent warnings | `wikidata` (4+ times within one file) | Once at top, brief one-liners after |
| Quick Reference vs Workflow Guidance | `wikidata` (~80% overlap between two tables) | Merge into one authoritative table |

---

## 4. YAML Frontmatter Quality

### Description Length Analysis

| Length | Count | Examples |
|--------|-------|----------|
| Excellent (≤25 words) | 15 | `wikimedia-toolforge` (19), `wikimedia-phabricator` (22), `wikimedia-cdn-assets` (22) |
| Good (26-35 words) | 12 | `wikimedia-api-access` (28), `wikimedia-diffs` (29) |
| Long (36-50 words) | 14 | `wikipedia-categories` (40), `wikipedia-templates` (40), `wikipedia-citations` (29) |
| Too Long (50+ words) | 4 | `toolforge-nodejs` (55), `wikidata-vector-search` (59), `wikidata` (56), `wikimedia-eventstreams` (55) |

### Description Anti-Patterns Found

1. **Table-of-contents descriptions** — enumerating every section rather than summarizing (e.g., `toolforge-nodejs`, `wikimedia-eventstreams`)
2. **Ambiguous verbs** — "navigate and understand", "create and design" instead of "Reference for..." or "Working with..."
3. **Description ≠ body** — `wikidata`'s description mentions "RDF data dumps" and "Wikibase REST API" which are barely covered
4. **Self-contradictory scope** — `wikimedia-page-assessment` says "any Wikimedia wiki with PageAssessments" but only 8 wikis have it

### Description Exemplars (Model These)

- `wikimedia-phabricator`: "Navigate Wikimedia's Phabricator instance — search tasks, track project status, file bug reports, and understand why something might not work or what's in development" (22 words)
- `wikipedia-en-article-audit`: "Audit an English Wikipedia article for structural issues, factual errors, and NPOV violations, then produce a machine-readable task graph (DAG) that another agent can execute to fix all identified problems" (32 words — clear I/O, clear handoff)
- `commons-file-resolution`: "Resolve Wikimedia Commons file references to browser-usable HTTP URLs — direct origin URLs, thumbnails, Special:FilePath redirects, cache-busting with timestamps, Action API imageinfo queries, and CORS-aware serving patterns" (accurate but could trim ~5 words)

---

## 5. Correctness Issues

### Actual Bugs Found

| Skill | Issue | Severity |
|-------|-------|----------|
| `toolforge-nodejs` | `filePath.startsWith(__dirname)` path traversal check is fragile | 🔴 High |
| `wiktionary-and-wikisource` | `extract_translations()` declares translations dict but never populates it | 🔴 High |
| `wikimedia-pageviews` | `datetime.utcnow()` deprecated in Python 3.12+ — use `datetime.now(datetime.UTC)` | 🟡 Medium |
| `wikimedia-commons-sdc` | References `wikimedia-commons` twice in relationship box — copy-paste error | 🟡 Medium |
| `wikimedia-page-assessment` | `'-1' not in pages` key convention is brittle | 🟡 Medium |

### Outdated References

| Skill | Issue |
|-------|-------|
| `wikimedia-api-access` | Uses `https://tools.wmflabs.org/` — legacy domain, should be `*.toolforge.org` |
| `wikimedia-toolforge` | Build Service commands have inconsistent syntax (`buildservice start` vs `--backend=buildservice`) |

### Description/Body Mismatches

| Skill | Description Says | Body Reality |
|-------|-----------------|--------------|
| `wikidata` | "RDF data dumps" | Barely covered — no dump processing instructions |
| `wikidata` | "Wikibase REST API" | Only Action API and SPARQL covered in depth |
| `wikimedia-pageviews` | "cached SQL properties" | Doesn't mention the `page_props` table name where this data lives |

---

## 6. Completeness Gaps by Domain

### Commons Family
- `commons-file-resolution`: No REST API thumbnail endpoint mentioned; no coverage of file overwrite/version scenarios
- `wikimedia-commons`: Doesn't reference the new `commons-file-resolution` skill at all
- `wikimedia-commons-thumbnails`: No AVIF thumbnail support status; no Varnish cache purge behavior

### Toolforge/Infrastructure
- `wikimedia-database`: No replica hostname listing for wikidata/commons (only enwiki); no cross-database JOIN limitation
- `wikimedia-toolforge`: Missing database access, Build Service troubleshooting, Kubernetes debugging, graceful shutdown
- `wikimedia-phabricator`: No coverage of Herald rules, project tagging conventions, or task dependencies

### Content/Editing
- `wikipedia-en-article-audit`: No retry/recovery for partial Phase 1 failures
- `wikipedia-en-biography-writing`: No coverage of disambiguation scenarios when naming conflicts arise
- `wikipedia-reference-verifiability`: Missing DOI/identifier-based verifiability; no cross-links to citations or categories

### APIs & Search
- `wikipedia-error-handling`: No coverage of EventStreams reconnection backoff strategies
- `wikimedia-search-cirrussearch`: No `srnamespace` API parameter guidance; no cross-wiki search workarounds
- `wikimedia-pageviews`: No country-level pageviews endpoint; no access-method breakdown

### Tools & Special
- `wikimedia-wikitext`: No Parsoid HTML caching strategy; no wikitext normalization (NFKC/NFD); no section transclusion
- `wikipedia-pagetriage-api`: Missing tag catalog; no pagination/continuation model; no WP:BEFORE workflow
- `wiktionary-and-wikisource`: No Wikidata lexeme coverage (a major gap); the translation extraction example is broken

---

## 7. Conciseness & Structure Assessment

### Largest Skills (Candidates for Splitting)

| Skill | Lines | Words | Recommendation |
|-------|-------|-------|----------------|
| `wikimedia-i18n-l10n-for-tools` | 1,072 | 4,349 | **Split into two:** `wikimedia-i18n-messages` (SOPs 1-4) + `wikimedia-i18n-wikimedia` (SOPs 5-10) |
| `wikimedia-commons-sdc` | ~1,000 | 5,126 | **Largest by words** — consider splitting Statements section into a reference doc |
| `wikimedia-eventstreams` | 1,034 | 4,312 | Move full stream catalog to `references/streams.md` |
| `wikimedia-page-styling` | ~800 | 7,321 | **Largest by word count** — the longest skill. Move allowed-properties list to reference doc |
| `wikimedia-ml-services` | 705 | 4,162 | Move detailed Revscoring model table to references |

### Recommended Offload Pattern

Several skills have large reference tables that could be moved to `references/` files:
- `wikimedia-i18n-l10n-for-tools`: Language code alias table → `references/language-codes.md`
- `wikimedia-eventstreams`: Full stream catalog → `references/streams.md`
- `wikimedia-ml-services`: Revscoring model table → `references/models.md`
- `wikipedia-citations`: 22-template CS1/CS2 table → `references/cs1-templates.md`
- `wikimedia-page-styling`: Allowed CSS properties → already has `references/allowed-properties.md` (verify inline summary isn't duplicative)

---

## 8. Standardization Opportunities

### Structural Patterns Worth Standardizing

1. **Cross-Reference sections** — Only ~60% of skills have a dedicated "Related Skills" or "Cross-References" section. The good ones use a table with "Why" column (see `wikimedia-database` for the model). Standardize on this.

2. **`depends_on` arrays** — Consistently under-specified. 15+ skills reference prerequisite skills in prose but don't include them in the formal `depends_on` YAML. Create a rule: if the body says "see also X" or "assumes familiarity with Y", Y must be in `depends_on`.

3. **New skill onboarding checklist** — When a new skill is added (`commons-file-resolution`, `toolforge-nodejs`), a checklist should ensure:
   - [ ] Hub skills in the domain cross-ref it
   - [ ] `depends_on` is populated
   - [ ] Description is ≤35 words
   - [ ] It appears in any upstream "Related Skills" tables
   - [ ] CORS/serving content isn't duplicated from other skills

4. **Guardrails section** — `wikipedia-citations`, `wikipedia-en-biography-writing`, and `wikipedia-notability-assessment` have excellent guardrails sections. This should be a standard pattern for all skills.

5. **Tooling section** — Present in most skills but format varies. Standardize on: Scripts (inline + references/) → Assets → Reference Docs → External Tools.

### Admonition Consistency
All skills use `> ⚠️` and `> 💡` — this is consistent ✅. No issues.

---

## 9. Matrix: Cross-Reference Density

```
                     api-acc api-str auth sec err diff edit-hist
api-access               -     ✓     ✓   —    —    —      ✓
api-strategy             ✓     -     —   —    ✓    —      —
auth-oauth               ✓     —     -   —    ✓    —      —
security                 ✓     —     ✓   -    —    —      —
error-handling           ✓     —     —   —    -    —      —
diffs                    ✓     —     —   —    —    -      —
edit-history             ✓     —     —   —    —    ✓       -

Missing: api-access → error-handling; diffs ← edit-history (bidirectional);
         api-strategy → auth-oauth; api-strategy → toolforge
```

```
                     wd   wd-vec search pviews passess
wikidata              -     ✗      ✗     ✓      ✗
wd-vector-search      ✓     -      ✗     ✗      ✗
cirrussearch          ✓     ✓      -     ✗      ✗
pageviews             ✓     ✗      ✗     -      ✗
page-assessment       ✗     ✗      ✗     ✗      -

Missing: pageviews ↔ page-assessment (Popular_pages bridge);
         page-assessment → cirrussearch; page-assessment → wikidata
```

```
                     commons file-res av  pdf sdc sparql svg thumb
commons               -       ✗     ✓   ✓   ✓    ✓     ✓   ✓
file-resolution       ✓       -     —   —   —    —     —   ✓
audio-video           ✓       ✗     -   —   ✓    —     —   ✓
pdf                   ✓       —     —   -   —    —     —   ✓
sdc                   ✓       —     ✓   —   -    —     —   —
sparql                ✓       —     —   —   —    -     —   —
svg                   ✓       —     —   —   —    —     -   ✓
thumbnails            ✓       ✗     ✓   ✓   —    ✓     ✓   -

Missing: commons → file-res (hub doesn't ref new child);
         file-res → sdc (file versioning); thumbnails → file-res (CORS)
```

```
                     cat cit anatomy talk templ tables audit bio notab ref-verif
categories            -  ✗    ✓     —    —     —      —    —    —     —
citations             —  -    ✓     —    —     —      —    —    —     ✗
page-anatomy          —  —    -     ✓    ✓     —      —    ✓    —     —
talk-page             —  —    ✓     -    —     —      —    —    ✗     —
templates             —  ✗    ✓     ✗    -     ✗      —    —    —     —
wikitables            —  —    ✗     —    ✓     -      —    —    —     —
article-audit         —  —    ✓     —    ✓     —      -    ✓    —     —
biography-writing     —  ✓    ✓     ✓    —     —      ✗    -    ✓     —
notability            —  ✓    —     —    —     —      —    ✓    -     —
ref-verifiability     ✗  ✗    —     —    —     —      —    —    —      -

11 missing pairs in this domain alone
```

```
                     tf   tf-node db  events i18n ml   cdn  phab
toolforge             -     ✗     ✗    ✗     ✗   ✗    ✗     ✗
toolforge-nodejs      ✓     -     ✗    ✗     ✗   ✗    ✗     ✗
database              ✓     ✗     -    ✗     ✗   ✗    ✗     ✗
eventstreams          ✓     ✗     ✗    -     ✗   ✓    ✗     ✗
i18n                  ✗     ✗     ✓    ✗     -   ✗    ✗     ✗
ml-services           ✗     ✗     ✗    ✓     ✗   -    ✗     ✗
cdn-assets            ✓     ✗     ✗    ✗     ✗   ✗    -     ✗
phabricator           ✓     ✗     ✗    ✗     ✗   ✗    ✗     -

Hub (toolforge) only refs 2/7 children — the biggest cross-ref blindspot in the entire repo
```

---

## 10. Prioritized Action Plan

### 🔴 P0 — Fix Bugs (Do First)
1. **`toolforge-nodejs`**: Fix `startsWith(__dirname)` path traversal → use `path.resolve()` + parent-check
2. **`wiktionary-and-wikisource`**: Fix `extract_translations()` — populate the `translations` dict or remove dead code
3. **`wikimedia-api-access`**: Update `tools.wmflabs.org` → `*.toolforge.org` everywhere

### 🟠 P1 — Fill Cross-Reference Gaps (High Impact)
4. **`wikimedia-toolforge` (hub)**: Add cross-refs to all 7 child skills (database, nodejs, eventstreams, i18n, ml, cdn, phab)
5. **`wikimedia-wikitext`**: Add cross-refs to 6+ skills that parse wikitext (templates, wikitables, citations, page-anatomy, pywikibot, wiktionary-and-wikisource)
6. **`wikimedia-commons` (hub)**: Add cross-ref to `commons-file-resolution`
7. **Make pageviews ↔ page-assessment bidirectional** (Popular_pages bridge)
8. **Make diffs ↔ edit-history bidirectional**
9. **Make api-access → error-handling** explicit
10. **Fix all 11 missing pairs in the Content/Editing domain**

### 🟡 P2 — Trim Descriptions (Medium Impact)
11. Shorten the 4 longest descriptions (50+ words each): `toolforge-nodejs`, `wikidata-vector-search`, `wikidata`, `wikimedia-eventstreams`
12. Shorten 14 descriptions in the 36-50 word range — aim for ≤35 words
13. Fix description/body mismatches: `wikidata` (remove "RDF dumps" and "REST API" OR add sections for them)

### 🟡 P3 — Eliminate Duplicate Content
14. Consolidate CORS sections: keep full content in `commons-file-resolution`; replace in `wikimedia-commons` and `wikimedia-commons-thumbnails` with 2-paragraph summary + cross-ref
15. Merge `wikidata`'s Quick Reference and Workflow Guidance tables (80% overlap)
16. Remove duplicate `wikimedia-commons` reference in `wikimedia-commons-sdc` relationship box

### 🟢 P4 — Long-Term Structural Improvements
17. Split `wikimedia-i18n-l10n-for-tools` (1,072 lines) into two skills
18. Move reference tables out of bodies: streams catalog, language codes, CS1 templates, Revscoring models, CSS properties
19. Standardize cross-reference section format (adopt `wikimedia-database`'s table-with-Why format)
20. Add "New Skill Onboarding Checklist" to CONTRIBUTING.md

---

## 11. Domain-by-Domain Health Scores

| Domain | Skills | Avg Score | Key Strength | Key Weakness |
|--------|--------|-----------|-------------|--------------|
| APIs & Auth | 7 | 4.0/5 | `api-strategy` is the gold-standard decision framework | Missing bidirectional links; `auth-oauth` has `depends_on` with no inline refs |
| Wikidata/Search | 5 | 4.0/5 | All well-structured with clear SOPs | pageviews ↔ assessment gap; wikidata description/body mismatch |
| Commons | 8 | 3.9/5 | Strong internal routing; `file-resolution` is an excellent new addition | CORS content triplicated; `sdc` is 5K+ words |
| Content/Editing | 10 | 4.0/5 | `page-anatomy` is the architectural gold standard; citation tooling is peerless | 11 missing link pairs; `depends_on` consistently under-specified |
| Toolforge/Infra | 8 | 3.6/5 | `nodejs` is a strong new skill; `eventstreams` is comprehensive | Hub only refs 2/7 children; `i18n` needs splitting |
| Tools/Special | 7 | 3.6/5 | `page-styling` is the most thorough; `pywikibot` covers immense scope well | `wikitext` has only 1 cross-ref; `pagetriage-api` under-scoped; `wiktionary` has a code bug |

---

## 12. Appendix: Complete Skill Inventory with Scores

| # | Skill | Words | Lines | Links | Score | Top Issue |
|---|-------|-------|-------|-------|-------|-----------|
| 1 | wikimedia-api-access | 3,748 | 726 | 6 | Excellent | Legacy toolforge URL |
| 2 | wikimedia-api-strategy | 2,845 | 617 | 7 | Excellent | Missing auth-oauth cross-ref |
| 3 | wikimedia-auth-oauth | 3,285 | 785 | 11 | Good | depends_on without inline refs |
| 4 | wikimedia-security-and-privacy | 3,285 | 785 | 7 | Good | Missing toolforge-nodejs cross-ref |
| 5 | wikipedia-error-handling | 2,388 | 480 | 11 | Excellent | No EventStreams backoff patterns |
| 6 | wikimedia-diffs | 2,093 | 394 | 4 | Good | No back-link to edit-history |
| 7 | wikipedia-edit-history | 2,093 | 394 | 4 | Good | Duplication with diffs |
| 8 | wikidata | 3,950 | ~700 | 12 | Excellent | Description mentions things body doesn't cover |
| 9 | wikidata-vector-search | 2,700 | ~450 | 10 | Excellent | 59-word description |
| 10 | wikimedia-search-cirrussearch | 3,748 | 726 | 29 | Excellent | Missing pagetriage-api cross-ref |
| 11 | wikimedia-pageviews | 1,040 | ~220 | 3 | Excellent | Python 3.12+ deprecation |
| 12 | wikimedia-page-assessment | 1,890 | ~350 | 5 | Good | Missing pageviews cross-ref |
| 13 | wikimedia-commons | 4,165 | ~650 | 27 | Excellent | Doesn't ref file-resolution |
| 14 | **commons-file-resolution** ⭐ | 2,461 | ~500 | 5 | Excellent | Hash_path explanation ambiguous |
| 15 | wikimedia-commons-audio-video | 2,832 | ~500 | 8 | Excellent | 52-word description |
| 16 | wikimedia-commons-pdf | 3,591 | ~650 | 8 | Good | No page extraction via API |
| 17 | wikimedia-commons-sdc | 5,126 | ~1,000 | 11 | Good | Largest skill; duplicate ref; no depends_on |
| 18 | wikimedia-commons-sparql | 1,819 | ~400 | 6 | Good | Depends_on lists 2 skills not in body |
| 19 | wikimedia-commons-svg | 2,152 | ~450 | 10 | Good | 55-word description |
| 20 | wikimedia-commons-thumbnails | 3,591 | ~700 | 12 | Good | CORS section duplicates file-resolution |
| 21 | wikimedia-toolforge | 2,845 | 617 | 2 | Good | Only refs 2/7 child skills |
| 22 | **toolforge-nodejs** ⭐ | 2,756 | 602 | 5 | Excellent | Path traversal bug |
| 23 | wikimedia-database | 906 | 193 | 5 | Good | No wikidata/commons replica hostnames |
| 24 | wikimedia-eventstreams | 4,312 | 1,034 | 26 | Excellent | 55-word description |
| 25 | wikimedia-i18n-l10n-for-tools | 4,349 | 1,072 | 24 | Good | Needs splitting |
| 26 | wikimedia-ml-services | 4,162 | 705 | 13 | Excellent | 37-word description |
| 27 | wikimedia-cdn-assets | ~1,200 | ~250 | 4 | Good | No cross-refs to page-styling or navigation |
| 28 | wikimedia-phabricator | ~1,200 | ~250 | 1 | Good | Only 1 internal cross-ref |
| 29 | wikipedia-categories | 3,460 | 632 | 3 | Excellent | Missing citations cross-ref |
| 30 | wikipedia-citations | 3,186 | 683 | 17 | Excellent | depends_on missing page-anatomy |
| 31 | wikipedia-page-anatomy | 2,163 | 390 | 7 | Excellent | Gold standard architecture |
| 32 | wikipedia-talk-page | 1,902 | 318 | 2 | Excellent | 52-word description |
| 33 | wikipedia-templates | 3,397 | 722 | 2 | Excellent | Missing wikitables/citations cross-refs |
| 34 | wikipedia-wikitables | 1,819 | 466 | 3 | Excellent | depends_on missing templates |
| 35 | wikipedia-en-article-audit | 4,721 | 920 | 6 | Excellent | No partial-failure recovery |
| 36 | wikipedia-en-biography-writing | 1,609 | 240 | 5 | Good | Missing article-audit cross-ref |
| 37 | wikipedia-notability-assessment | 3,189 | 572 | 21 | Excellent | — |
| 38 | wikipedia-reference-verifiability | 1,403 | 351 | 2 | Good | Missing citations/categories cross-refs |
| 39 | pywikibot | 4,988 | ~800 | 24 | Excellent | Minor logging section gap |
| 40 | mediawiki-page-navigation | 3,329 | ~600 | 14 | Excellent | Missing accessibility section |
| 41 | mediawiki-translate-extension | 3,318 | ~600 | 15 | Excellent | Missing i18n cross-ref |
| 42 | wikimedia-page-styling | 7,321 | ~800 | 24 | Excellent | Largest by words; no dark mode |
| 43 | wikimedia-wikitext | 1,341 | 319 | 1 | Good | 🔴 Only 1 cross-ref |
| 44 | wikipedia-pagetriage-api | 1,249 | 260 | 7 | Fair | Under-scoped; missing tag catalog |
| 45 | wiktionary-and-wikisource | 2,152 | 554 | 16 | Good | extract_translations() bug |

---

*Report generated by parallel audit of 6 subagents analyzing 45 skills across 6 domains.*
@