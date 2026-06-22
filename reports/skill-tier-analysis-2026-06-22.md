# Wikipedia-AI-Skills: Skill Portfolio Tier Analysis

**Date:** 2026-06-22
**Context:** Evaluating the 45-skill portfolio for context-bloat risk and
identifying which skills earn their place as standalone entries vs. which
should be merged or demoted.

---

## 1. The Concern

As the skill catalog grows, two risks emerge:

1. **Context bloat** — even with keyword-based loading, a very large catalog
   increases the chance that marginally relevant skills get loaded into context.
2. **Catalog fatigue** — users and maintainers face a longer list with diminishing
   marginal value per skill.

The question: **when is "enough" when enumerating these skills?**

## 2. Methodology

Each skill was assessed against three criteria:

| Criterion | Weight | Question |
|-----------|--------|----------|
| **Procedural necessity** | High | Can the base LLM do this correctly without the skill? |
| **Usage breadth** | Medium | How many tasks/users does this serve? |
| **Self-contained value** | Low | Does this justify its own file vs. being a section in a parent skill? |

## 3. Tier Assignments

### T1 — Foundational (10 skills, ~30K words)

Skills the LLM **cannot** perform correctly without because they involve
procedural knowledge not in training data (specific API endpoints, rate
limiting rules, tool-specific syntax, policy rules):

| Skill | Words | Why T1 |
|-------|-------|--------|
| wikimedia-api-access | 2,796 | User-Agent format, endpoint URLs, 429 handling — LLMs get this wrong constantly |
| wikimedia-api-strategy | 2,248 | Decision tree: REST vs Action vs SPARQL vs SQL — purely procedural |
| wikipedia-error-handling | 2,387 | Retry/backoff patterns for specific Wikimedia services |
| wikimedia-wikitext | 1,436 | mwparserfromhell vs regex — LLMs default to regex, which breaks |
| wikipedia-page-anatomy | 2,162 | Article structure, namespaces, protection levels — domain knowledge |
| wikipedia-citations | 3,245 | CS1/CS2 templates, Wayback Machine API — very domain-specific |
| wikimedia-toolforge | 2,957 | SSH, become, webservice commands — pure procedural knowledge |
| pywikibot | 3,853 | Bot framework with 50+ scripts, generators, object model |
| wikidata | 3,927 | Q/P numbers, SPARQL endpoint, Wikibase API — LLMs guess wrong |
| wikimedia-commons | 4,178 | File namespaces, licensing, CORS — Commons-specific knowledge |

### T2 — High-value (21 skills, ~62K words)

Skills that make agents substantially faster/more reliable but the LLM
could theoretically figure out with trial and error:

| Skill | Words | Why T2 |
|-------|-------|--------|
| wikimedia-search-cirrussearch | 3,745 | Complex syntax (haswbstatement, insource, deepcategory) — huge time saver |
| wikimedia-commons-sdc | 5,123 | MediaInfo API, property types, GLAM workflows — deep domain |
| wikimedia-eventstreams | 4,310 | SSE protocol, stream schemas, canary handling — procedural |
| wikimedia-i18n-l10n-for-tools | 4,346 | ICU plurals, fallback chains, RTL — language engineering |
| wikipedia-templates | 3,483 | Parser functions, Lua, template types — deep domain |
| wikipedia-notability-assessment | 3,188 | GNG, 13 SNGs, source quality — policy engineering |
| wikipedia-categories | 3,521 | Category trees, V/N/D tests, topic vs set — policy rules |
| mediawiki-page-navigation | 2,406 | Subpage hierarchies, breadcrumbs, #titleparts — template logic |
| wikimedia-diffs | 1,852 | Diff API, byte analysis, vandalism signatures |
| wikimedia-commons-thumbnails | 3,585 | Thumb URL scheme, format conversion matrix |
| wikimedia-commons-sparql | 3,650 | WCQS vs QLever endpoints, federated queries |
| wikimedia-ml-services | 4,156 | Lift Wing API, model catalog, ORES migration |
| wikimedia-database | 905 | SSH tunnel, replica hostnames, MySQL 9+ fix |
| wikimedia-pageviews | 1,063 | SQL page_props cache, REST API top endpoint |
| wikimedia-page-assessment | 1,806 | PageAssessments schema, Popular_pages bot |
| wikipedia-en-biography-writing | 1,752 | NPOV, BLP, infobox templates — policy + structure |
| wikipedia-edit-history | 2,092 | Revision API, byte deltas, user contributions |
| wikimedia-security-and-privacy | 3,284 | Suppression, deanonymization, XSS — security domain |
| wikipedia-talk-page | 1,911 | DiscussionTools, WikiProject banners, archives |
| wikipedia-wikitables | 1,871 | Wikitable syntax, CSS classes, accessibility attributes |
| wikimedia-auth-oauth | 3,415 | OAuth 1.0a/2.0 flows, bot passwords, CSRF tokens |

### T3 — Nice-to-have (9 skills, ~28K words)

Niche workflows that save hours when needed but serve a smaller audience:

| Skill | Words | Why T3 |
|-------|-------|--------|
| wikidata-vector-search | 2,898 | Alpha service, niche use case (fuzzy semantic search) |
| wikimedia-commons-svg | 2,638 | SVG-specific (Inkscape, validation, optimization) |
| wikimedia-commons-audio-video | 2,829 | Audio/video formats, patent policy, transcoding |
| wikimedia-commons-pdf | 2,310 | Multi-page PDF/DjVu, Wikisource OCR integration |
| wikimedia-page-styling | 4,304 | TemplateStyles CSS, grid/flexbox — niche power-user feature |
| wikipedia-en-article-audit | 4,718 | DAG-based audit pipeline — sophisticated but narrow use case |
| mediawiki-translate-extension | 3,805 | Translate extension — not on Wikipedia, wiki-admins only |
| commons-file-resolution | 2,460 | File URL resolution — important for browser apps, niche audience |
| wiktionary-and-wikisource | 2,147 | Dictionary and proofreading — separate projects from Wikipedia |

### ⚠️ Consider Demotion or Merge (5 skills, ~8K words)

Skills where the ROI as a standalone file is questionable:

| Skill | Words | Concern | Recommendation |
|-------|-------|---------|----------------|
| **wikimedia-cdn-assets** | 922 | One paragraph of knowledge | ✅ **Executed:** Merged into wikimedia-toolforge |
| **wikipedia-pagetriage-api** | 1,247 | enwiki only, patrol rights required, small API surface | ✅ **Executed:** Merged into wikipedia-reference-verifiability |
| **wikimedia-phabricator** | 1,634 | LLMs can navigate web UIs | **Kept** — planned expansion for bug report quality |
| **wikipedia-reference-verifiability** | 1,476 | Single-purpose analysis tool | **Kept** — gains value from absorbing pagetriage-api |
| **toolforge-nodejs** | 2,789 | Could be SOPs in toolforge | **Kept for now** — has real procedural knowledge |

## 4. Portfolio After Merges

| Metric | Before | After |
|--------|--------|-------|
| Skills | 45 | **43** |
| Total words | ~127K | ~125K (saved ~2K) |
| Avg skill size | 2,818 | 2,907 |
| Foundation (T1) | 10 | 10 |
| High-value (T2) | 21 | 21 |
| Nice-to-have (T3) | 9 | 9 |
| Demoted/merged | 5 | 3 |

## 5. Key Insight: Splitting Is Better Than Merging

A counterintuitive finding: **splitting skills reduces context bloat**, it doesn't
increase it. A monolithic 26K-word "Commons" skill would load 26K words for
every Commons task. With 8 sub-skills, a typical task loads the 4K hub + 1-2
specialized skills (2-5K each) = ~10K. That's a 60% reduction.

The same logic applies to the entire catalog: 43 focused skills are better
than 20 monolithic ones. The risk isn't the size of the catalog — it's the
size of individual skills.

## 6. Recommendations

1. **Monitor the largest skills** — `wikimedia-commons-sdc` (5,123 words),
   `wikipedia-en-article-audit` (4,718), `wikimedia-page-styling` (4,304),
   `wikimedia-i18n-l10n-for-tools` (4,346). These are candidates for
   splitting if they grow further.

2. **Consider merging `toolforge-nodejs`** into `wikimedia-toolforge` if the
   two skills' audiences consistently overlap. Currently kept separate because
   Node.js has enough procedural knowledge to justify it.

3. **Review T3 skills periodically** — as Wikimedia evolves, some niche
   skills (like `wikidata-vector-search` if the alpha becomes stable) may
   graduate to T2.

4. **Don't add more Commons sub-skills** — 8 is enough. New Commons formats
   should be handled by expanding existing skills or adding reference docs.

5. **Keep the catalog lean** — the bar for a new standalone skill should be:
   either the LLM catastrophically fails without it (T1), or it saves
   2-5× time on a common workflow (T2). If it's only useful 1% of the time,
   it should be a reference doc or SOP inside an existing skill.
