# Skills Improvement Plan

**Date:** 2026-06-18  
**Based on:** `SKILLS-AUDIT-REPORT.md`  
**Goal:** Fix all P1 and P2 issues, then re-evaluate

---

## Execution Order (by dependency)

### Wave 1: Fix truncated/corrupted file
1. Fix truncated `wikipedia-pagetriage-api` SKILL.md ending

### Wave 2: Add `skill_discovery_hints` to 21 missing skills
2. Add hints to each skill (batch by domain group)

### Wave 3: Add `depends_on` to 22 skills with body refs but no formal deps
3. Add front matter `depends_on` to each

### Wave 4: Fix orphaned skills (zero outbound refs) — 6 skills
4. Add cross-reference sections to: wikimedia-cdn-assets, wikimedia-database, wikimedia-page-assessment, wikimedia-phabricator, wikipedia-en-biography-writing, wiktionary-and-wikisource

### Wave 5: Consistency fixes
5. Add User-Agent warning to 4 skills that lack it
6. De-duplicate: link wikipedia-en-biography-writing → notability-assessment
7. De-duplicate: cross-link wikimedia-database ↔ wikimedia-page-assessment

### Wave 6: Re-evaluation
8. Run same analysis methodology
9. Produce before/after comparison
