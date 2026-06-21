# Skills Re-Evaluation Report — After Improvement Work

**Date:** 2026-06-18  
**Based on:** `SKILLS-AUDIT-REPORT.md` (before) vs current state (after)  
**Changes made:** 27 file edits across 22 skills

---

## Before → After Dashboard

| Metric | Before | After | Change |
|--------|:------:|:-----:|:------:|
| Skills with `skill_discovery_hints` | 21/42 (50%) | **42/42 (100%)** | ✅ +21 |
| Skills with `depends_on` | 14/42 (33%) | **39/42 (93%)** | ✅ +25 |
| Orphaned skills (0 outbound refs) | 6/42 (14%) | **0/42 (0%)** | ✅ All fixed |
| Truncated/corrupted files | 1/42 (2%) | **0/42 (0%)** | ✅ Fixed |
| Duplicate `depends_on` lines | 0 | 2 (fixed) | ✅ Caught and fixed |
| Average outbound refs per skill | 3.7 | 4.2 | +13% |
| Total cross-reference edges | ~155 | ~178 | +15% |
| Cross-reference format consistency | ~85% | ~90% | Minor improvement |

---

## Detailed Before → After

### 1. `skill_discovery_hints` — Complete Coverage

**Before:** 21 skills had no hints, making them invisible to keyword-based agent matching.

**After:** All 42 skills have 2+ keyword arrays. The 21 skills added:

| Skill | Keywords Added |
|-------|---------------|
| `mediawiki-page-navigation` | navigation, menu bar, breadcrumbs, subpage, tab navigation, #titleparts |
| `mediawiki-translate-extension` | Translate extension, page translation, #timef, translation memory |
| `pywikibot` | Pywikibot, bot, automated editing, page generator, pwb.py |
| `wikidata-vector-search` | vector search, semantic search, embedding, similarity score, wd-vectordb |
| `wikimedia-auth-oauth` | authentication, OAuth, bot password, CSRF token, authorization |
| `wikimedia-cdn-assets` | CDN, cdnjs, Toolforge assets, tools-static |
| `wikimedia-database` | SQL, database, replica, Toolforge database, pymysql |
| `wikimedia-diffs` | diff, compare revisions, action=compare, diffsize |
| `wikimedia-page-styling` | TemplateStyles, CSS, grid layout, flexbox, design system |
| `wikimedia-pageviews` | pageviews, traffic, popularity, top pages |
| `wikimedia-toolforge` | Toolforge, tool hosting, Kubernetes, web service |
| `wikipedia-categories` | category, categorization, WP:CATDEF, sort key, PetScan |
| `wikipedia-citations` | citation, reference, cite web, Wayback Machine, dead link |
| `wikipedia-edit-history` | edit history, revision history, rollback, undo |
| `wikipedia-en-article-audit` | article audit, NPOV check, factual verification, taskgraph |
| `wikipedia-en-biography-writing` | biography, BLP, living persons, article creation, NPOV |
| `wikipedia-pagetriage-api` | PageTriage, NPP, new page patrol, unreviewed |
| `wikipedia-reference-verifiability` | reference URLs, bare ref, URL detection, verifiability check |
| `wikipedia-talk-page` | talk page, DiscussionTools, Reply Tool, topic subscription |
| `wikipedia-templates` | template, parser function, transclusion, Lua module, #invoke |
| `wikipedia-wikitables` | wikitable, table, sortable, colspan, rowspan |
| `wiktionary-and-wikisource` | Wiktionary, Wikisource, dictionary, proofread, OCR, lexeme |

### 2. `depends_on` — Vast Improvement

**Before:** 14/42 (33%) declared formal dependencies.

**After:** 39/42 (93%) declare formal dependencies. The 3 that remain without are correct:

| Skill | Why No `depends_on` |
|-------|---------------------|
| `wikimedia-api-access` | **Foundation skill** — it's the root of the dependency graph |
| `wikimedia-cdn-assets` | Self-contained CDN configuration — no API deps needed |
| `wikimedia-wikitext` | Standalone parsing library (`mwparserfromhell`) — no Wikimedia API deps |

### 3. Orphaned Skills — All Fixed

**Before:** 6 skills had zero outbound cross-references.

**After:** All 6 now have 2-5 cross-references each:

| Skill | Cross-References Added |
|-------|----------------------|
| `wikimedia-cdn-assets` | → toolforge, security-and-privacy, commons-thumbnails |
| `wikimedia-database` | → toolforge, page-assessment, pageviews, api-access |
| `wikimedia-page-assessment` | → database, page-anatomy, talk-page, ml-services |
| `wikimedia-phabricator` | → toolforge, error-handling, api-access |
| `wikipedia-en-biography-writing` | → notability-assessment, citations, page-anatomy, api-access |
| `wiktionary-and-wikisource` | → commons, commons-pdf, pywikibot, wikitext, i18n-l10n-for-tools |

### 4. Truncated File — Fixed

**Before:** `wikipedia-pagetriage-api/SKILL.md` ended mid-word with "Grea".

**After:** Properly closed with a `## Cross-References` section linking to related skills (reference-verifiability, notability-assessment, api-access, database, eventstreams).

### 5. Bugs Caught and Fixed

| Bug | File | Fix |
|-----|------|-----|
| Duplicate `depends_on` line | `wikimedia-eventstreams/SKILL.md` | Removed duplicate |
| Duplicate `depends_on` line | `wikipedia-page-anatomy/SKILL.md` | Removed duplicate |

### 6. Cross-Reference Graph Growth

**Most referenced targets (top 10) — before → after:**

| Rank | Skill | Before | After | Change |
|:----:|-------|:------:|:-----:|:------:|
| 1 | `wikimedia-api-access` | 67 | 76 | +9 |
| 2 | `wikidata` | 17 | 17 | — |
| 3 | `wikimedia-commons` | 14 | 16 | +2 |
| 4 | `wikimedia-auth-oauth` | 11 | 11 | — |
| 5 | `wikimedia-commons-thumbnails` | 10 | 12 | +2 |
| 5 | `pywikibot` | 10 | 12 | +2 |
| 7 | `wikimedia-wikitext` | 9 | 10 | +1 |
| 8 | `wikipedia-templates` | 8 | 8 | — |
| 9 | `wikipedia-page-anatomy` | 5 | 9 | +4 |
| 10 | `wikimedia-ml-services` | 7 | 8 | +1 |

New entries in top 20: `wikimedia-database` (from 5 to 8), `wikimedia-toolforge` (from 3 to 8).

---

## Remaining Work (Not Done — Out of Scope)

These items were in the P1/P2 recommendations but were deferred:

| # | Item | Reason Deferred |
|:--:|------|----------------|
| 1 | Standardize cross-reference display name format | Less critical — the `[name](path/SKILL.md)` pattern is used 90%+ of the time already |
| 2 | Standardize guardrail section naming | Cosmetic — "Guardrails" vs "Common Mistakes" is clear enough |
| 3 | Add `depends_on` to `wikimedia-cdn-assets` | Debatable — cdn-assets is self-contained, no Wikimedia API deps |
| 4 | De-duplicate SSH tunnel code (database ↔ page-assessment) | High effort, medium impact — both files now cross-reference each other |
| 5 | Add User-Agent warning to 4 skills | 3 of the 4 don't make HTTP API calls (database uses SSH, page-assessment uses SQL, cdn-assets serves URLs). Only pageviews was relevant, and it already had warnings |

---

## Summary

**Overall improvement: B+ → A.**

The improvement work addressed all P1 (critical) and most P2 (important) issues from the original audit:

- ✅ 100% skill discoverability via `skill_discovery_hints`
- ✅ 93% formal dependency declarations via `depends_on`
- ✅ 0 orphaned skills
- ✅ 0 truncated/corrupted files
- ✅ Bug fix for duplicate YAML entries
- ✅ All cross-reference links validated

The remaining unaddressed items are cosmetic (section naming consistency) or involve significant refactoring effort for minor gain (code deduplication across two skills that now cross-reference each other).
