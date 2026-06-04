# Roadmap

## What's done

### Published skills

- **wikimedia-api-access** — Complete. Covers Wikimedia API entry points (REST, Action, SPARQL), User-Agent policy compliance with `ContentGapResearch` as the project identifier, rate limiting with Retry-After backoff, connection reuse via `requests.Session()`, 403/429 error handling, and browser-based `Api-User-Agent` workaround. Links to the official Wikimedia Foundation User-Agent Policy. Updated to clarify that the Action API and REST API work across all Wikimedia projects (Commons, Wikidata, Wiktionary, etc.) — just swap the domain. **New:** Expanded 429 Retry-After section with common causes and anti-pattern warnings. **New:** Title Format Guide (section 11 in `references/endpoints.md`) documenting underscore-vs-space title format differences across 6 APIs, with correct/wrong code comparison. **New:** `assets/cross_api_pipeline.py` — runnable 4-step pipeline script (Pageviews → Wikidata → entity classification → content analysis).

- **wikimedia-commons** — Complete. Covers the two Commons search interfaces (MediaSearch for visual browsing vs. Special:Search/CirrusSearch for advanced queries), structured data search via `haswbstatement:`, programmatic access via the Action/REST APIs, Commons namespaces (File, Gallery, Category, Creator, etc.), categories vs. galleries, licensing guidance (CC0/CC BY/CC BY-SA vs. non-compliant NC/ND licenses), the "three pillars" of free licensing, the fair-use prohibition, uploaded file formats (allowed and disallowed, including MP4 patent issues), bulk upload tools (Pattypan, flickr2commons, url2commons, video2commons, Commonist), the Volunteer Response Team (VRT) permissions verification process, and a search demo script with `--ns` namespace override support.

- **wikidata** — Complete. Covers Wikidata's role as the inter-language linking backbone for Wikipedia, the Q-number (items) and P-number (properties) system, Wikibase as a MediaWiki extension with its own Action API modules (`wbgetentities`, `wbsearchentities`, `wbgetclaims`, etc.), the SPARQL query service at query.wikidata.org (web interface and programmatic access), the fundamental properties P31 (instance of) and P279 (subclass of) with hierarchical query patterns, the community-driven (non-rigid) taxonomy model, a comparison of SPARQL vs. `haswbstatement:`, and workflow guidance for choosing the right access method.

- **wikidata-vector-search** — Complete. Covers the Wikidata Vector Database API at wd-vectordb.wmcloud.org — a semantic/vector search engine over all Wikidata items and properties. Three endpoints: item search, property search, and similarity scoring. Hybrid vector+keyword retrieval with Reciprocal Rank Fusion (RRF), multilingual support (100+ languages, 4 with dedicated vectors), and optional reranker. Includes a CLI query script (wd-vector-search.sh) that resolves QIDs to labels and descriptions and filters to Wikipedia articles by default. Documents the alpha limitations (non-functional instanceof filter, concept-first ranking, no labels in response).

- **wikimedia-database** — Complete. Covers SSH tunnel setup and connection management (plain `ssh` and `autossh`), Python implementation with `pymysql`, configurable local port via `TOOLFORGE_DB_PORT` (default 3307), and data handling guardrails (read-only, namespace filtering, binary decoding, safety limits, database naming conventions).

- **wikimedia-pageviews** — Complete. Covers three data retrieval paths: cached SQL property (`page_props.pp_propname = 'pageview_daily_average'` with `CAST AS UNSIGNED`) for sorting/filtering large result sets, the Analytics QuickMetrics REST API for precise historical data, and the Top Pages REST endpoint (Scenario C) for finding the most-viewed pages across a project. Includes the "no table" guardrail (pageviews table does not exist in SQL replicas), date format warnings (slash vs compact), and cross-API chaining guidance with title normalization.

- **wikimedia-page-assessment** — Complete. Covers querying Wikipedia article quality (FA/GA/B/C/Start/Stub) and importance ratings from WikiProject assessment banners stored in `page_assessments` and `page_assessments_projects` tables. Includes deployment scope documentation (which wikis have the extension), full schema reference with real production replica columns (note: `pa_assessed_timestamp` does not exist — use `pa_page_revision` + `revision` table join), CLI scripts for project assessment queries and quality gap detection, Python/pymysql integration for MySQL 9.x compatibility, and 20+ sample SQL queries organized by category.

- **wikimedia-toolforge** — Complete. Covers Toolforge account setup, tool creation, file deployment (rsync, git), web services management (Kubernetes-backed, all runtimes), Kubernetes jobs for batch tasks, cron jobs, environment variables and secrets, logs and debugging. Includes nine guardrails covering common pitfalls (become, SSH keys, NFS, resource limits, etc.) and full example workflows.

- **wikipedia-en-biography-writing** — Complete. Covers notability assessment (WP:GNG, WP:ANYBIO, WP:NACADEMIC, WP:NARTIST, WP:NCREATIVE), biography article structure with wiki markup templates (Infobox person, citation templates, section ordering), citation requirements per section, source hierarchy, policy guardrails for BLP/NPOV/NOR/Verifiability, and seven strict anti-hallucination rules.
- **wikimedia-cdn-assets** — Complete. Guides agents on loading JavaScript, CSS, and fonts from Wikimedia's privacy-preserving cdnjs.toolforge.org CDN to ensure user privacy and policy compliance.

- **wikimedia-diffs** — Complete. Covers fetching and interpreting diffs between Wikipedia page revisions via the Action API `compare` module and the REST API `/compare` endpoint, with HTML diff table parsing using BeautifulSoup, edit magnitude detection (byte churn, net changes, additions vs. removals), diff sharing links, anti-pattern guidance, and a fetch-diff script and diff-stats analyzer.

- **wikimedia-wikitext** — Complete. Covers the two strategies for reading and manipulating MediaWiki wikitext: AST-based parsing with `mwparserfromhell` (for safe template/infobox/citation extraction and modification) and Parsoid HTML strategy via the REST API `/html` endpoint (for read-only data extraction). Includes anti-pattern tables (why regex fails), common edge cases (nested templates, implicit table spans, unicode), and scripts for wikitext inspection and Parsoid HTML fetching.

- **wikipedia-page-anatomy** — Complete. Covers the full structure of a Wikipedia article: lead section conventions, infobox types (template-based and module-backed), category hierarchy with sort keys and hidden categories, citation templates and identifiers (DOI, PMID, ISBN), transcluded templates and maintenance tags, navigation boxes vs. categories vs. infoboxes, redirect and disambiguation detection, protection levels and page existence checks, and an API methods reference table.

- **wikipedia-talk-page** — Complete. Covers the Talk namespace naming conventions, threaded discussion format and indentation rules, signing with ~~~~ and unsigned comment detection, WikiProject banners with assessment quality (FA/GA/B/C/Start/Stub) and importance ratings (Top/High/Mid/Low), automated and manual archiving with MiszaBot configuration, pings and section editing, talk page etiquette (AGF, NPA, striking vs. deleting), and article talk vs. user talk distinctions. Cross-references wikimedia-page-assessment for bulk database queries.

- **wikipedia-edit-history** — Complete. Covers accessing page history via URL and API with pagination, revision record structure (revid, parentid, user, size, tags), diff basics (deferring to wikimedia-diffs for deep mechanics), edit summary conventions and bot identification, minor vs. major edit flags, user attribution and contributions API, byte size analysis with vandalism red flags, undo vs. rollback permissions and the 3RR, revision tags and their meanings (mobile, visual editor, possible vandalism), vandalism detection signals and block status checks, and an API methods reference table.

- **pywikibot** — Complete. Covers the Pywikibot Python library (v11.3.0) for automating work on MediaWiki sites. Includes installation (pip vs. repository mode), `user-config.py` setup, the core object model (Site, Page, Category, User, FilePage, Link, ItemPage, PropertyPage, Claim, LexemePage), the 40+ page generator system with composable CLI flags, the bot class hierarchy (BaseBot → ExistingPageBot → CurrentPageBot → ConfigParserBot) for writing custom bots, a catalog of 50+ built-in scripts across 7 categories (general, categories, templates, images, wikibase, admin, non-edit), full Wikidata/Wikibase integration with `harvest_template`, `claimit`, and `illustrate_wikidata` scripts, Commons file operations (download, upload, image_transfer), Toolforge/PAWS deployment guidance, a One-of-a-Kind Capabilities section highlighting 8 superpowers that no other API approach can easily replicate, and a decision table for when NOT to use Pywikibot. Ships with `assets/pywikibot-quickref.py` (280 lines of copy-paste ready code snippets), `references/api-mapping.md` (full MediaWiki Action API → Pywikibot method cross-reference), and `scripts/test-pywikibot.sh` (installation validation script).

- **wikimedia-eventstreams** — Complete. Covers the EventStreams HTTP service (SSE-based real-time event streaming). Includes the complete stream catalog (18 streams: recentchange, revision-create, page-create, page-delete, page-move, page-links-change, revision-tags-change, ML prediction streams, Wikidata RDF mutation streams, and more), event schema reference for all recentchange fields with wiki/type/namespace/user/bot metadata, client libraries (Python `requests-sse`, Pywikibot `comms.eventstreams.EventStreams`, Node.js `wikimedia-streams`, browser `EventSource`, `curl` + `jq`), client-side filtering patterns (by wiki, type, namespace, user, bot flag, title pattern), mandatory canary event handling (`meta.domain === 'canary'`), connection lifecycle management with auto-reconnect using `Last-Event-ID`, historical replay via `?since=`, 15-minute timeout handling, and real-world tool patterns (live edit counter, cross-wiki monitor, Wikidata batch edit detector, patrol monitor). Ships with `assets/eventstreams-consumer.py` (207 lines, reusable Python consumer with CLI args, filters, and auto-reconnect), `references/stream-schemas.md` (compact field reference for all stream schemas), and `scripts/test-eventstreams.sh` (connectivity verification script).

### Project infrastructure

- `.claude/skills/<name>/SKILL.md` directory structure with YAML frontmatter (name, description, license, compatibility)
- All skills validated for opencode `skill` tool discovery
- MIT license
- README with install instructions
- GitHub repository initialized at `fuzheado/Wikipedia-AI-Skills`
- `.claude.json` project configuration for agent discovery
- `CONTRIBUTING.md` with skill authoring guidelines, accuracy checklist, and PR process
- Test suite with 104 tests across 3 modules: YAML frontmatter validation for all 17 skills,
  mock-based unit tests for the cross-API pipeline script, and content-accuracy checks for key SOPs
- `.gitignore` updated to exclude `.pytest_cache/`

## What's outstanding

### Planned skills

- **General-topic article drafting** — SOPs for writing non-biography Wikipedia articles (events, organizations, concepts, places). Different structure templates, different notability criteria, different citation patterns. Prior art exists in the original project roadmap.

- **Copyediting for encyclopedic tone** — SOPs for auditing existing articles for NPOV violations, promotional language, weasel words, tone drift, and structural issues. Could include a checklist-style workflow.

- **Pywikibot advanced workflows** — Deeper SOPs for chaining multiple Pywikibot scripts in CI/CD pipelines, integrating with Toolforge Kubernetes jobs, scheduling recurring bot tasks via cron, and monitoring bot health. The current skill covers the fundamentals; this would add deployment and operations guidance.

- **ORES / Lift Wing (ML services)** — SOPs for using Wikimedia's ML-as-a-service APIs (edit quality prediction, article quality scoring, topic classification, revert-risk scoring). Covers the ORES API (`api.wmflabs.org/ores/v3/scores/`) and the newer Lift Wing replacement, available models (`damaging`, `goodfaith`, `articlequality`, `itemquality`, `reverted`, `topic`), threshold tuning, and integration patterns for patrol tools, quality dashboards, and vandalism detection. Complements the article-audit and page-assessment skills by adding ML-powered scores.

- **Wikipedia XML/SQL dump processing** — SOPs for working with Wikimedia's monthly data dumps from `dumps.wikimedia.org`. Covers dump types (`pages-articles`, `pages-meta-current`, `stub-meta-history`, SQL dumps), streaming XML parsing with `mwxml`/`mwdump` (memory-safe iteration over gigabytes), Pywikibot's `xmlreader` module and `-xml:` generator filter, filtering by namespace or date range, and use cases like "extract all infobox data from the entire English Wikipedia without hitting the API". Complements the database-replicas skill (live SQL) by covering offline bulk analysis.

- **Wikipedia bot policy, flagging & etiquette** — Governance skill covering what's ALLOWED when running bots on Wikimedia wikis. Covers the Bot Approvals Group (BAG) process, bot flag requirements (which differ between enwiki, Commons, and Wikidata), `put_throttle` ethics, Commons bot policy (no automated uploads without approval), Wikidata's permissive but property-restricted rules, communicating with other editors, and the higher standard bots are held to for edit-warring and 3RR. Complements the Pywikibot technical skill with the policy layer.

- **Wikimedia REST API v1 — deep reference** — Comprehensive endpoint reference for the modern REST API. Covers `/page/{title}/html`, `/page/{title}/wikitext`, `/page/{title}/summary`, `/page/{title}/links`, `/page/{title}/related`, `/revision/{id}/diff`, `/revision/{id}/content`, `/search/title`, `/search/page`, `/transform/wikitext/to/html`, `/transform/html/to/wikitext`, `/feed/featured`, `/feed/onthisday`. Includes a decision table for choosing REST vs. Action API vs. EventStreams vs. SPARQL for a given task. Complements the api-access skill (which focuses on authentication and patterns) with an endpoint-by-endpoint reference.

- **PAWS (Jupyter notebooks for Wikimedia)** — SOPs for using PAWS (`paws.wmflabs.org`), the hosted Jupyter notebook environment with Pywikibot pre-installed. Covers launching sessions, Pywikibot + pandas + matplotlib workflows, authentication flow, exporting notebooks as scripts, and when to use PAWS vs. Toolforge vs. local development. Complements the Toolforge skill with the exploration/prototyping tier.

- **Domain-specific article templates** — Structure templates for common article types: companies, educational institutions, films, albums, software, scientific concepts. Each has distinct section conventions and notability guidelines.

- **Notability assessment tool** — A standalone skill for evaluating whether a subject/topic meets Wikipedia notability criteria before investing in drafting. Could produce a structured report against GNG and relevant SNGs.

- **Citation health checker** — SOPs for checking whether citations actually support the claims they are attached to, identifying dead links, missing metadata, and inappropriate sources.

### Improvements to existing skills

- Add more domain-specific infobox templates to the biography skill (e.g., `Infobox scientist`, `Infobox writer`, `Infobox artist`, `Infobox athlete`)
- Add `Api-User-Agent` header guidance to the API access skill for browser-based tools
- Consider adding citation template generators for common scenarios (book with ISBN lookup, news article with URL extraction)

### Completed improvements

- **Title Format Guide** (section 11 of `wikimedia-api-access/references/endpoints.md`) — cross-API table documenting underscore-vs-space title formats across 6 endpoints, with correct/wrong code comparison. Fixes the single most costly bug when chaining Pageviews, Action API, and SQL results.
- **Expanded 429 Retry-After handling** in `wikimedia-api-access/SKILL.md` — dedicated subsection explaining the importance of server-supplied Retry-After values, an anti-pattern warning against fixed backoff, and three common causes of 429 responses.
- **Batch entity classification SOP** in `wikidata/SKILL.md` — resolves the gap between the SPARQL-focused Wikidata skill and the need for a concrete multi-API pipeline workflow. Covers batch Wikidata ID resolution, P31 type checking with 11 common Q IDs, and subclass hierarchy traversal.
- **Cross-API pipeline script** (`wikimedia-api-access/assets/cross_api_pipeline.py`) — a runnable 4-step demo showing Pageviews → Wikidata ID resolution → P31 entity classification → content analysis, with proper batch processing, rate limiting, and title normalization.
- **Scenario C (Top Pages)** in `wikimedia-pageviews/SKILL.md` — adds the Top Pages REST endpoint as a third data retrieval path alongside the existing SQL and per-article API scenarios. Includes date format warnings and cross-API chaining guidance.

### Process

- Write CONTRIBUTING.md with skill authoring guidelines ✅
- Set up a GitHub issue template for skill suggestions
- Add `.claude.json` project configuration for agent discovery ✅
- **Add skill tests** ✅ — `pytest`-based test suite in `tests/` with 104 tests:
    - `test_yaml_frontmatter.py`: YAML frontmatter validation for all 17 skills (5 checks each: exists, required fields, description length, MIT license, directory match)
    - `test_cross_api_pipeline.py`: Mock-based unit tests for the pipeline script (title normalization, batch splitting, P31 classification, citation counting, namespace filtering)
    - `test_markdown_sops.py`: Content-accuracy checks for new/modified SOPs (batch entity classification, Scenario C, Title Format Guide, 429 Retry-After)
    - Coverage meets the 3-5 test minimum per affected skill; the full suite serves as a foundation to expand iteratively.

## Key decisions

### YAML frontmatter requirement

**Decision:** Every `SKILL.md` must start with `name`, `description`, `license`, and `compatibility` in YAML frontmatter.

**Why:** The `name` field is how agents reference and load the skill. The `description` field is shown in the `skill` tool's `<available_skills>` list, so the agent can decide which skill is relevant without loading it. Without frontmatter, the skill is invisible to agent tooling.

### Agent-facing SOPs, not human READMEs

**Decision:** Skills are written as direct, imperative instructions for an AI agent, organized as Standard Operating Procedures (SOPs). They do not contain project overviews, setup instructions, or community guidelines.

**Why:** A skill injected into an agent's context takes up tokens and must be maximally useful per token. README-style content ("What's in this repo", "How to try it", "Contributing") wastes context on information the agent does not need. That meta-content belongs in the project's `README.md`, not in skill files. An agent needs concrete SOPs, guardrails, and code examples — not a pitch.

### Separate skills per concern, not one monolithic skill

**Decision:** Each Wikimedia concern (API access, pageviews, biography writing) is a separate skill in its own directory, rather than one large "Wikipedia" skill.

**Why:** Agents load skills on demand. A single monolithic skill would add unnecessary context to every task. Separation also makes skills independently reusable, testable, and maintainable. A user working on pageview analysis should not have biography writing instructions injected into their context.

### MIT license

**Decision:** The project uses the MIT license.

**Why:** Permissive, standard for open-source projects, matches common practice in the AI tooling ecosystem, and places no restrictions on reuse.

### `ContentGapResearch` as the project identifier in User-Agent strings

**Decision:** Code examples use `ContentGapResearch` as the trailing project identifier in User-Agent headers (e.g., `MyBot/1.0 (contact) ContentGapResearch`).

**Why:** The Wikimedia Foundation User-Agent Policy encourages descriptive agents. A consistent project identifier helps Wikimedia distinguish traffic originating from this project's tools and provides a way to contact maintainers if issues arise. Users should replace the contact information with their own but keep the project identifier.
