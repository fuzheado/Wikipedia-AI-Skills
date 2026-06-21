# Wikipedia AI Skills — Network Analysis

**Date:** 2026-06-18  
**Nodes:** 43 skills  
**Edges:** 186 cross-references  
**Graph:** `skills-network.dot` → `skills-network.svg` / `skills-network.png`

---

## Quick Reference

```
Network Metrics:
  Diameter:     ~3 hops (max distance between any two skills)
  Average degree: 4.3
  Density:       0.10 (sparse — only 10% of possible connections exist)
  Graph type:    Directed, scale-free hub-and-spoke

Hub scores:
  Top 1%:   api-access (77) — the foundation
  Top 5%:   wikidata (18), commons (15), thumbnails (11), auth-oauth (11), pywikibot (11)
  Median:   4 inbound refs
  Long tail: 29 skills with 1-3 inbound refs
```

---

## Centrality Rankings — Top 10 Hubs

These are the skills that the rest of the network depends on most heavily:

| Rank | Skill | Inbound Refs | Role | Why |
|:----:|-------|:-----------:|------|-----|
| 1 🔴 | `wikimedia-api-access` | **77** | **Foundation** | User-Agent, rate limiting, 429/403 — every API call in every other skill |
| 2 🔴 | `wikidata` | **18** | **Data Hub** | SPARQL, entity lookups, cross-wiki structured data |
| 3 🟢 | `wikimedia-commons` | **15** | **Platform Hub** | File search, upload, licensing — entry point for all media |
| 4 🟢 | `wikimedia-commons-thumbnails` | **11** | **Subsystem** | Thumbnail generation used by every file-type skill |
| 4 🔴 | `wikimedia-auth-oauth` | **11** | **Auth Hub** | OAuth, bot passwords, CSRF — required for write ops |
| 4 🟡 | `pywikibot` | **11** | **Bot Framework** | Wraps Action API for bulk editing and automation |
| 7 🟡 | `wikimedia-wikitext` | **10** | **Parser** | AST parsing with mwparserfromhell |
| 8 🟡 | `wikipedia-templates` | **8** | **Content** | Template syntax, parser functions |
| 8 🟣 | `wikimedia-ml-services` | **8** | **ML Hub** | Quality, revert risk, topics, readability |
| 10 🟡 | `wikipedia-page-anatomy` | **7** | **Content** | Page structure, infoboxes, sections |

---

## Full Centrality Ranking (All 43 Skills)

| Rank | Skill | Inbound | Group |
|:----:|-------|:------:|-------|
| 1 | `wikimedia-api-access` | 77 | 🔴 Foundation |
| 2 | `wikidata` | 18 | 🔴 Foundation |
| 3 | `wikimedia-commons` | 15 | 🟢 Commons |
| 4 | `wikimedia-commons-thumbnails` | 11 | 🟢 Commons |
| 4 | `wikimedia-auth-oauth` | 11 | 🔴 Foundation |
| 4 | `pywikibot` | 11 | 🟡 Tooling |
| 7 | `wikimedia-wikitext` | 10 | 🟡 Tooling |
| 8 | `wikipedia-templates` | 8 | 🟡 Content |
| 8 | `wikimedia-ml-services` | 8 | 🟣 ML |
| 10 | `wikipedia-page-anatomy` | 7 | 🟡 Content |
| 10 | `wikimedia-database` | 7 | 🟡 Tooling |
| 10 | `wikimedia-commons-sparql` | 7 | 🟢 Commons |
| 13 | `wikipedia-error-handling` | 6 | 🔴 Foundation |
| 13 | `wikimedia-eventstreams` | 6 | 🟣 Streaming |
| 13 | `wikimedia-diffs` | 6 | 🟡 Tooling |
| 13 | `wikimedia-commons-svg` | 6 | 🟢 Commons |
| 13 | `wikimedia-commons-sdc` | 6 | 🟢 Commons |
| 13 | `wikimedia-commons-pdf` | 6 | 🟢 Commons |
| 13 | `wikimedia-commons-audio-video` | 6 | 🟢 Commons |
| 13 | `mediawiki-translate-extension` | 6 | 🟡 Content |
| 21 | `wikipedia-categories` | 5 | 🟡 Content |
| 21 | `wikimedia-toolforge` | 5 | 🟡 Tooling |
| 23 | `wikipedia-edit-history` | 4 | 🟡 Content |
| 23 | `wikimedia-page-styling` | 4 | 🟡 Content |
| 23 | `wikimedia-page-assessment` | 4 | 🟣 ML |
| 23 | `wikimedia-api-strategy` | 4 | 🔴 Foundation |
| 23 | `mediawiki-page-navigation` | 4 | 🟡 Content |
| 28 | `wikipedia-pagetriage-api` | 3 | 🟣 Workflow |
| 28 | `wikipedia-en-biography-writing` | 3 | 🟣 Workflow |
| 28 | `wikipedia-citations` | 3 | 🟡 Content |
| 31 | `wiktionary-and-wikisource` | 2 | ⬜ Sisters |
| 31 | `wikipedia-talk-page` | 2 | 🟡 Content |
| 31 | `wikipedia-reference-verifiability` | 2 | 🟣 Workflow |
| 31 | `wikipedia-notability-assessment` | 2 | 🟣 Workflow |
| 31 | `wikimedia-pageviews` | 2 | 🟡 Tooling |
| 31 | `wikidata-vector-search` | 2 | 🔴 Foundation |
| 37 | `wikipedia-en-article-audit` | 1 | 🟣 Workflow |
| 37 | `wikimedia-security-and-privacy` | 1 | 🟣 Workflow |
| 37 | `wikimedia-search-cirrussearch` | 1 | 🟡 Tooling |
| 37 | `wikimedia-i18n-l10n-for-tools` | 1 | 🟣 Workflow |
| 37 | `wikimedia-phabricator` | 1 | 🟣 Workflow |
| 37 | `wikimedia-cdn-assets` | 1 | 🟡 Tooling |

---

## Graph Properties

| Property | Value |
|-----------|-------|
| Nodes (skills) | 43 |
| Edges (cross-references) | 186 |
| Average outbound edges per skill | 4.3 |
| Median outbound edges | 3 |
| Max outbound edges | 9 (`cirrussearch`, `i18n`) |
| Min outbound edges | 1 (`wikitext`, `auth-oauth`, `cdn-assets`, `phabricator`) |
| Network diameter (max path) | ~3 hops |
| Network density | 0.10 (sparse) |

**Interpretation:** This is a **scale-free, hub-and-spoke** network. A few skills (api-access, wikidata, commons) are the "hubs" that the entire network depends on. Most skills link to only 1-4 others. The average path between any two skills is ~1-2 hops, so the network is well-connected but not over-connected.

---

## Outbound Degree Analysis — Which Skills Link the Most?

| Rank | Skill | Outbound Edges | Targets |
|:----:|-------|:------------:|---------|
| 1 | `wikimedia-search-cirrussearch` | 9 | api-access, categories, commons, wikidata, vector-search, api-strategy, database, pywikibot, errors, page-anatomy |
| 2 | `wikimedia-i18n-l10n-for-tools` | 8 | api-access, translate, wikidata, commons, wikitext, database, pywikibot, errors |
| 2 | `wikimedia-commons` | 8 | api-access, thumbnails, svg, pdf, audio-video, sdc, sparql |
| 4 | `wikipedia-notability-assessment` | 7 | api-access, ml-services, cirrussearch, citations, biography-writing, errors, pagetriage |
| 4 | `wikimedia-eventstreams` | 7 | api-access, pywikibot, diffs, ml-services, toolforge, edit-history, pagetriage |
| 4 | `pywikibot` | 7 | api-access, wikidata, database, diffs, toolforge, wikitext, edit-history |
|
