# Skill Inventory Audit — Consolidated Report

> **Generated:** 2026-06-05
> **Method:** 4 parallel scouts, each inspecting 4–5 skills against SKILL.md, tests/conftest.py, README.md, ROADMAP.md, and filesystem
> **Total skills audited:** 19

---

## Status Matrix

| # | Skill | Lines | Frontmatter | Tests | README | ROADMAP | Scripts | Assets | Refs | Issues |
|---|-------|-------|-------------|-------|--------|---------|---------|--------|------|--------|
| 1 | pywikibot | 792 | ✅ | ✅ | ✅ | Published | 1 | 1 | 1 | — |
| 2 | wikidata | 384 | ✅ | ⚠️ dup | ✅ | Published | 2 | 1 | 1 | Duplicate in conftest.py |
| 3 | wikidata-vector-search | 418 | ✅ | ⚠️ dup | ✅ | Published | 1 | 0 | 1 | Duplicate in conftest.py; empty assets/ |
| 4 | wikimedia-api-access | 238 | ✅ | ✅ | ✅ | Published | 1 | 2 | 1 | — |
| 5 | wikimedia-cdn-assets | 159 | ✅ | ✅ | ✅ | Published | 2 | 2 | 1 | — |
| 6 | wikimedia-commons | 313 | ✅ | ✅ | ✅ | Published | 1 | 1 | 1 | — |
| 7 | wikimedia-database | 175 | ✅ | ✅ | ✅ | Published | 3 | 2 | 2 | — |
| 8 | wikimedia-diffs | 298 | ✅ | ✅ | ✅ | Published | 2 | 1 | 1 | `__pycache__` |
| 9 | wikimedia-eventstreams | 1001 | ✅ | ✅ | ✅ | Published | 1 | 1 | 1 | — |
| 10 | wikimedia-ml-services | 635 | ✅ | ✅ | ✅ | Published | 3 | 4 | 3 | `__pycache__` |
| 11 | wikimedia-page-assessment | 216 | ✅ | ✅ | ✅ | Published | 2 | 2 | 1 | — |
| 12 | wikimedia-pageviews | 200 | ✅ | ✅ | ✅ | Published | 2 | 1 | 1 | `__pycache__` |
| 13 | wikimedia-toolforge | 594 | ✅ | ✅ | ✅ | Published | 4 | 1 | 1 | `__pycache__` |
| 14 | wikimedia-wikitext | 314 | ✅ | ✅ | ✅ | Published | 2 | 3 | 3 | `__pycache__` |
| 15 | wikipedia-edit-history | 389 | ✅ | ✅ | ✅ | Published | 3 | 1 | 1 | — |
| 16 | wikipedia-en-article-audit | 914 | ✅ | ✅ | ✅ | ❌ Missing | 5 | 5 | 2 | **No ROADMAP entry** |
| 17 | wikipedia-en-biography-writing | 223 | ✅ | ✅ | ✅ | Published | 2 | 3 | 2 | — |
| 18 | wikipedia-page-anatomy | 347 | ✅ | ✅ | ✅ | Published | 2 | 2 | 1 | — |
| 19 | wikipedia-talk-page | 211 | ✅ | ✅ | ✅ | Published | 2 | 1 | 1 | — |

**Totals** | **19 skills** | **7,421 avg 391** | **✅ 19/19** | **✅ 19/19** | **✅ 19/19** | **18/19** | **43 total** | **34 total** | **24 total** | **8 issues**

---

## Issues Found

### 🔴 Missing: `wikipedia-en-article-audit` not in ROADMAP

The second-largest skill in the repo (914 lines, 12 files) has **no entry** in `ROADMAP.md`. It was added via commit `d056b04` but never documented in the roadmap. All other Published skills have descriptions.

**Fix:** Add a Published entry to ROADMAP.md's What's done section.

### 🟡 Duplicate entries in `tests/conftest.py`

`'wikidata'` and `'wikidata-vector-search'` each appear **twice** in `SKILL_NAMES`, causing YAML frontmatter tests to run twice for these skills. 4 duplicated test runs out of 177 total — not a correctness bug but wastes CI time.

**Fix:** Deduplicate the list in `tests/conftest.py`.

### 🟡 `__pycache__/` in 5 skills' `assets/` directories

| Skill | Path |
|-------|------|
| wikimedia-diffs | `assets/__pycache__/` |
| wikimedia-ml-services | `assets/__pycache__/` |
| wikimedia-pageviews | `assets/__pycache__/` |
| wikimedia-toolforge | `assets/__pycache__/` |
| wikimedia-wikitext | `assets/__pycache__/` |

Compiled Python bytecode from running scripts. Harmless but shouldn't be committed.

**Fix:** Add `__pycache__/` to `.gitignore` and clean existing caches.

### 🟢 `wikidata-vector-search` has empty `assets/` directory

The directory exists but contains no files. Minor — not referenced by the SKILL.md.

**Fix:** Remove the empty directory or ship an asset.

### 🟢 Only 1 skill uses `depends_on` frontmatter

Only `wikimedia-ml-services` declares `depends_on: [wikimedia-api-access]`. Several other skills reference `wikimedia-api-access` in prose (for User-Agent boilerplate) but don't declare it formally.

**Fix:** Optional — not a critical issue since the dependency is documented in prose.

---

## Size Distribution

| Range | Count | Skills |
|-------|-------|--------|
| < 200 lines | 3 | cdn-assets (159), database (175), pageviews (200) |
| 200–350 | 7 | biography-writing, talk-page, page-assessment, api-access, diffs, wikitext, page-anatomy |
| 350–600 | 4 | wikidata, edit-history, vector-search, toolforge |
| 600–1000 | 3 | ml-services, pywikibot, article-audit |
| 1000+ | 1 | eventstreams (1001) |
| **Total** | **19** | **7,421 lines** |

---

## Script/Accessory Distribution

| Accessories | Count | Skills |
|-------------|-------|--------|
| 1–2 scripts | 10 | api-access, commons, diffs, eventstreams, pywikibot, vector-search, page-assessment, pageviews, wikitext, biography-writing, page-anatomy, talk-page |
| 3–4 scripts | 4 | database, edit-history, ml-services, toolforge |
| 5 scripts | 1 | article-audit |
| 0 assets | 1 | vector-search (empty) |
| 1 asset | 8 | pywikibot, wikidata, commons, diffs, eventstreams, database, edit-history, talk-page, toolforge |
| 2–3 assets | 6 | api-access, cdn-assets, page-assessment, pageviews, wikitext, biography-writing, page-anatomy |
| 4+ assets | 2 | ml-services (4), article-audit (5) |

---

## Recommendations by Priority

### Now — bugs

| Action | Target | Why |
|--------|--------|-----|
| Add ROADMAP entry | `wikipedia-en-article-audit` | Missing from roadmap; easiest fix with highest impact |
| Deduplicate conftest.py | `tests/conftest.py` | 2 dupes wasting CI time; trivial one-line fix |
| Add `__pycache__/` to `.gitignore` | `.gitignore` | Prevents future bytecode commits |
| Clean `__pycache__/` dirs | 5 skills' assets/ | Remove committed bytecode |

### Soon — polish

| Action | Target | Why |
|--------|--------|-----|
| Remove empty `assets/` | `wikidata-vector-search` | Dead directory; minor cleanup |
| Consider `depends_on` for other skills | Multiple | Only 1 of 19 uses it; inconsistent |

### Future — enhancement

| Action | Target | Why |
|--------|--------|-----|
| Add test modules for skills with no dedicated tests | All skills with scripts/assets | Currently only api-access, ml-services have dedicated test files; others rely only on YAML frontmatter validation |
| Balance script/asset counts | Low-count skills | Not a problem per se, but some skills (cdn-assets, commons) have minimal tooling |