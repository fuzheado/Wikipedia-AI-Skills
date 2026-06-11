# Roadmap

## What's done

### Published skills

- **wikimedia-api-access** — Complete. Covers Wikimedia API entry points (REST, Action, SPARQL), User-Agent policy compliance, rate limiting with Retry-After backoff, connection reuse via `requests.Session()`, 403/429 error handling, and browser-based `Api-User-Agent` workaround.

- **wikimedia-api-strategy** — Complete. Covers choosing the right Wikimedia API or tool for the task — decision framework covering REST API, Action API, SPARQL, SQL replicas, EventStreams, and Pywikibot, with latency/complexity/authentication trade-offs. Ships with `scripts/api-strategy.sh` (interactive CLI) and `assets/api_selector.py` (importable Python module with `recommend()` and `compare()` functions).

- **wikimedia-search-cirrussearch** — Complete. Covers the full CirrusSearch query language — all syntax keywords (insource, hastemplate, linksto, deepcategory, haswbstatement, intitle, incategory, prefix, subpageof, morelike, articletopic, filetype, etc.), three search entry points (full-text, near-match, prefix), Action API search parameters with srwhat/srprop/srsort reference, ranking caveats (stemming, stop words, template expansion, index freshness, regex performance), maintenance query patterns (15+ pre-built queries for patrolling, citation audits, template audits, category maintenance), and guidance on combining CirrusSearch with PetScan, SPARQL, and SQL replicas. Ships with `scripts/cirrus-search.sh` (CLI search tool with formatted output and raw JSON mode), `scripts/maintenance-queries.sh` (pre-built maintenance query runner with 18 query types), `assets/search_client.py` (Python search client with full-text/near-match/prefix/batch modes, 429 retry, pagination), `assets/maintenance_queries.py` (Python maintenance query library with 20+ query generators and catalog), and `references/cirrus-syntax.md` (compact syntax reference card) and `references/search-scenarios.md` (80+ real-world scenarios organized by workflow). Tests: `tests/test_search.py` (100+ tests across the client, maintenance queries, scripts, reference docs, and SKILL.md validation).

- **wikimedia-commons** — Complete. Covers the two Commons search interfaces (MediaSearch for visual browsing vs. Special:Search/CirrusSearch for advanced queries), structured data search via `haswbstatement:`, programmatic access via the Action/REST APIs, Commons namespaces (File, Gallery, Category, Creator, etc.), categories vs. galleries, licensing guidance (CC0/CC BY/CC BY-SA vs. non-compliant NC/ND licenses), the "three pillars" of free licensing, the fair-use prohibition, uploaded file formats (allowed and disallowed, including MP4 patent issues), bulk upload tools (Pattypan, flickr2commons, url2commons, video2commons, Commonist), the Volunteer Response Team (VRT) permissions verification process, and a search demo script with `--ns` namespace override support.

- **wikidata** — Complete. Covers Wikidata's role as the inter-language linking backbone for Wikipedia, the Q-number (items) and P-number (properties) system, Wikibase as a MediaWiki extension with its own Action API modules (`wbgetentities`, `wbsearchentities`, `wbgetclaims`, etc.), the SPARQL query service at query.wikidata.org (web interface and programmatic access), the fundamental properties P31 (instance of) and P279 (subclass of) with hierarchical query patterns, the community-driven (non-rigid) taxonomy model, a comparison of SPARQL vs. `haswbstatement:`, and workflow guidance for choosing the right access method.

- **wikidata-vector-search** — Complete. Covers the Wikidata Vector Database API at wd-vectordb.wmcloud.org — a semantic/vector search engine over all Wikidata items and properties. Three endpoints: item search, property search, and similarity scoring. Hybrid vector+keyword retrieval with Reciprocal Rank Fusion (RRF), multilingual support (100+ languages, 4 with dedicated vectors), and optional reranker. Includes a CLI query script (wd-vector-search.sh) that resolves QIDs to labels and descriptions and filters to Wikipedia articles by default. Documents the alpha limitations (non-functional instanceof filter, concept-first ranking, no labels in response).

- **wikipedia-citations** — Complete. Covers Wikipedia citation templates (CS1/CS2) with full parameter reference for 20+ template types, the Wayback Machine API for checking and saving archives, dead link detection workflows, bare URL expansion, citation linting and validation, and 30+ maintenance templates. Ships with 4 CLI scripts (expand-bare-url, archive-check, check-dead-links, citation-inspector), 4 Python assets (wayback_inspector, dead_link_scanner, citation_linter, citation_generator), and 2 reference docs (CS1 parameters, maintenance templates).

- **wikipedia-categories** — Complete. Covers the Wikipedia category system end-to-end: tree hierarchy, three validity tests (Verifiable/Neutral/Defining), topic vs. set categories, sort keys and DEFAULTSORT, comprehensive comparison of all access methods (Action API, Pywikibot, PetScan, WDQS, Special pages) with trade-off analysis, overcategorization rules, naming conventions, and category maintenance. Ships with 2 reference docs, 1 CLI script ($category-tree.sh), and 2 Python assets.

- **wikimedia-database** — Complete. Covers SSH tunnel setup and connection management (plain `ssh` and `autossh`), Python implementation with `pymysql`, configurable local port via `TOOLFORGE_DB_PORT` (default 3307), and data handling guardrails (read-only, namespace filtering, binary decoding, safety limits, database naming conventions).

- **wikimedia-pageviews** — Complete. Covers three data retrieval paths: cached SQL property (`page_props.pp_propname = 'pageview_daily_average'` with `CAST AS UNSIGNED`) for sorting/filtering large result sets, the Analytics QuickMetrics REST API for precise historical data, and the Top Pages REST endpoint (Scenario C) for finding the most-viewed pages across a project. Includes the "no table" guardrail (pageviews table does not exist in SQL replicas), date format warnings (slash vs compact), and cross-API chaining guidance with title normalization.

- **wikimedia-page-assessment** — Complete. Covers querying Wikipedia article quality (FA/GA/B/C/Start/Stub) and importance ratings from WikiProject assessment banners stored in `page_assessments` and `page_assessments_projects` tables. Includes deployment scope documentation (which wikis have the extension), full schema reference with real production replica columns (note: `pa_assessed_timestamp` does not exist — use `pa_page_revision` + `revision` table join), CLI scripts for project assessment queries and quality gap detection, Python/pymysql integration for MySQL 9.x compatibility, and 20+ sample SQL queries organized by category.

- **wikimedia-toolforge** — Complete. Covers Toolforge account setup, tool creation, file deployment (rsync, git), web services management (Kubernetes-backed, all runtimes), Kubernetes jobs for batch tasks, cron jobs, environment variables and secrets, logs and debugging. Includes nine guardrails covering common pitfalls (become, SSH keys, NFS, resource limits, etc.) and full example workflows.

- **wikipedia-en-biography-writing** — Complete. Covers notability assessment (WP:GNG, WP:ANYBIO, WP:NACADEMIC, WP:NARTIST, WP:NCREATIVE), biography article structure with wiki markup templates (Infobox person, citation templates, section ordering), citation requirements per section, source hierarchy, policy guardrails for BLP/NPOV/NOR/Verifiability, and seven strict anti-hallucination rules.

- **wikipedia-error-handling** — Complete. Covers HTTP error handling across all Wikimedia APIs: status code reference, per-service rate limits, universal retry pattern, SPARQL-specific rate limiting, User-Agent 403 debugging, Lift Wing model errors (422, 404, empty scores), EventStreams connection drops and canary events, and debugging checklist. Ships with `scripts/check-api-status.sh` (connectivity checker for 9 endpoints) and `assets/api_client.py` (reusable Python client with retry, rate limiting, SPARQL, Lift Wing, and EventStreams methods).

- **wikimedia-cdn-assets** — Complete. Guides agents on loading JavaScript, CSS, and fonts from Wikimedia's privacy-preserving cdnjs.toolforge.org CDN to ensure user privacy and policy compliance.

- **wikimedia-diffs** — Complete. Covers fetching and interpreting diffs between Wikipedia page revisions via the Action API `compare` module and the REST API `/compare` endpoint, with HTML diff table parsing using BeautifulSoup, edit magnitude detection (byte churn, net changes, additions vs. removals), diff sharing links, anti-pattern guidance, and a fetch-diff script and diff-stats analyzer.

- **wikimedia-wikitext** — Complete. Covers the two strategies for reading and manipulating MediaWiki wikitext: AST-based parsing with `mwparserfromhell` (for safe template/infobox/citation extraction and modification) and Parsoid HTML strategy via the REST API `/html` endpoint (for read-only data extraction). Includes anti-pattern tables (why regex fails), common edge cases (nested templates, implicit table spans, unicode), and scripts for wikitext inspection and Parsoid HTML fetching.

- **wikipedia-page-anatomy** — Complete. Covers the full structure of a Wikipedia article: lead section conventions, infobox types (template-based and module-backed), category hierarchy with sort keys and hidden categories, citation templates and identifiers (DOI, PMID, ISBN), transcluded templates and maintenance tags, navigation boxes vs. categories vs. infoboxes, redirect and disambiguation detection, protection levels and page existence checks, and an API methods reference table.

- **wikipedia-talk-page** — Complete. Covers the Talk namespace naming conventions, threaded discussion format and indentation rules, signing with ~~~~ and unsigned comment detection, WikiProject banners with assessment quality (FA/GA/B/C/Start/Stub) and importance ratings (Top/High/Mid/Low), automated and manual archiving with MiszaBot configuration, pings and section editing, talk page etiquette (AGF, NPA, striking vs. deleting), and article talk vs. user talk distinctions. Cross-references wikimedia-page-assessment for bulk database queries.

- **wikipedia-edit-history** — Complete. Covers accessing page history via URL and API with pagination, revision record structure (revid, parentid, user, size, tags), diff basics (deferring to wikimedia-diffs for deep mechanics), edit summary conventions and bot identification, minor vs. major edit flags, user attribution and contributions API, byte size analysis with vandalism red flags, undo vs. rollback permissions and the 3RR, revision tags and their meanings (mobile, visual editor, possible vandalism), vandalism detection signals and block status checks, and an API methods reference table.

- **wikipedia-en-article-audit** — Complete. Covers auditing a Wikipedia article for structural issues, factual errors, and NPOV violations using a systematic six-diagnosis pipeline (lead/concision, structure/organization, references, tone/NPOV, talk page context, topic assessment). Produces a machine-readable task graph (DAG) that another agent can execute to fix all identified problems. Ships with `assets/analysis-template.md`, `assets/npov-keywords.txt`, `assets/taskgraph.schema.json`, scripts for diagnosis and task graph generation, and reference docs for intermediate formats and verification protocol.

- **wikipedia-templates** — Complete. Covers creating, designing, and understanding MediaWiki templates end-to-end: template syntax with parameter defaults and inclusion control tags (`<noinclude>`/`<includeonly>`/`<onlyinclude>`), transclusion vs. substitution, parser functions (`#if`, `#ifeq`, `#switch`, `#expr`, `#time`, `#invoke`, etc.), magic words (variables, behavior switches), Lua modules and the `#invoke`/Scribunto system, full template types taxonomy (27 infobox families, citation, navbox, maintenance, stub, hatnote, structural, media, etc.), template detection via the Action API (`prop=templates`, `list=embeddedin`, `action=expandtemplates`), template protection levels and limits (post-expand include size, expensive parser function counts), and template maintenance (documentation, sandbox, tracking categories, TemplateData). Ships with 3 CLI scripts (`scripts/expand-template.sh`, `scripts/template-usage.sh`, `scripts/inspect-template.sh`), 2 Python assets (`assets/template-inspector.py`, `assets/template-scanner.py`), and 3 reference docs (parser functions, magic words, template types).

- **pywikibot** — Complete. Covers the Pywikibot Python library (v11.3.0) for automating work on MediaWiki sites. Includes installation (pip vs. repository mode), `user-config.py` setup, the core object model (Site, Page, Category, User, FilePage, Link, ItemPage, PropertyPage, Claim, LexemePage), the 40+ page generator system with composable CLI flags, the bot class hierarchy (BaseBot → ExistingPageBot → CurrentPageBot → ConfigParserBot) for writing custom bots, a catalog of 50+ built-in scripts across 7 categories (general, categories, templates, images, wikibase, admin, non-edit), full Wikidata/Wikibase integration with `harvest_template`, `claimit`, and `illustrate_wikidata` scripts, Commons file operations (download, upload, image_transfer), Toolforge/PAWS deployment guidance, a One-of-a-Kind Capabilities section highlighting 8 superpowers that no other API approach can easily replicate, and a decision table for when NOT to use Pywikibot. Ships with `assets/pywikibot-quickref.py` (280 lines of copy-paste ready code snippets), `references/api-mapping.md` (full MediaWiki Action API → Pywikibot method cross-reference), and `scripts/test-pywikibot.sh` (installation validation script).

- **wikimedia-eventstreams** — Complete. Covers the EventStreams HTTP service (SSE-based real-time event streaming). Includes the complete stream catalog (18 streams: recentchange, revision-create, page-create, page-delete, page-move, page-links-change, revision-tags-change, ML prediction streams, Wikidata RDF mutation streams, and more), event schema reference for all recentchange fields with wiki/type/namespace/user/bot metadata, client libraries (Python `requests-sse`, Pywikibot `comms.eventstreams.EventStreams`, Node.js `wikimedia-streams`, browser `EventSource`, `curl` + `jq`), client-side filtering patterns (by wiki, type, namespace, user, bot flag, title pattern), mandatory canary event handling (`meta.domain === 'canary'`), connection lifecycle management with auto-reconnect using `Last-Event-ID`, historical replay via `?since=`, 15-minute timeout handling, and real-world tool patterns (live edit counter, cross-wiki monitor, Wikidata batch edit detector, patrol monitor). Ships with `assets/eventstreams-consumer.py` (207 lines, reusable Python consumer with CLI args, filters, and auto-reconnect), `references/stream-schemas.md` (compact field reference for all stream schemas), and `scripts/test-eventstreams.sh` (connectivity verification script).

- **wikimedia-ml-services** — Complete. Covers 15+ model families (revert risk, article quality, topic classification, readability, reference quality, language identification, content translation, article descriptions, article country, logo detection) via Lift Wing's POST-based inference API, plus ORES migration guidance for legacy code. Ships with `scripts/batch-score.sh`, `scripts/playground.sh`, and multiple Python assets for scoring and analysis.

- **wikimedia-page-styling** — Complete. Covers TemplateStyles for loading custom CSS on wiki pages — responsive grid/flexbox layouts, card-based tile systems, color themes, button systems, and full visual design systems that transform plain wiki pages into rich, interactive-looking interfaces.

- **mediawiki-page-navigation** — Complete. Covers building navigation systems in MediaWiki — menu bars, subpage hierarchies, breadcrumbs, tabs, and the template logic that powers them. Includes `#titleparts` parsing, `#ifexist` link validation, dynamic sub-navigation loading, menu bar design, and page-hierarchy-aware link generation.

- **mediawiki-translate-extension** — Complete. Covers the Translate extension for multilingual wiki content — marking pages for translation with `<translate>` tags, writing translatable templates (avoiding `{{PLURAL:}}` inside translate tags, using `{{formatnum:}}` for locale-aware numbers), using `#timef` for locale-aware date formatting, managing language subpages, and building i18n-aware navigation.

- **wikipedia-reference-verifiability** — Complete. Covers analyzing whether a page's references contain URLs — detecting bare plain-text citations, template-based citations without `url=` parameters (18+ parameter names), shortened footnotes (harvsp/sfn/harvnb), and named ref reuse. Ships with `scripts/check-ref-urls.sh`, `scripts/batch-ref-audit.sh`, `assets/ref_url_checker.py` (importable library with `has_any_url_refs`, `has_infobox`, `get_shortened_footnotes`), and a 27-test test suite.

- **pagetriage-api** — Complete. Covers the PageTriage extension API — listing unreviewed pages (`action=pagetriagelist`), marking pages reviewed/unreviewed (`action=pagetriageaction`), applying curation tags (`action=pagetriagetagging`), and the legacy `unreviewedpages` API. Documents the patrol permission model, review status codes (0=unreviewed through 3=autopatrolled), and the `pagetriage_page` SQL table. Front matter warns that PageTriage is primarily deployed on enwiki and testwiki only. Ships with `scripts/list-unreviewed.sh`, `scripts/check-status.sh`, `assets/pagetriage_client.py` (Python API client), and `assets/patrol_simulator.py` (two-pass pipeline demo).

- **wikimedia-auth-oauth** — Complete. Covers Wikimedia authentication for programmatic access: OAuth 2.0 Authorization Code Grant (multi-user web apps), OAuth 2.0 Client Credentials Grant (owner-only/Toolforge tools), OAuth 1.0a (legacy), bot passwords (personal scripts/cron), PKCE for non-confidential clients, CSRF token handling for write actions, permission/user rights checking, secure credential storage, and 8 categories of anti-patterns. Ships with `assets/oauth2_client.py` (importable Python library), `assets/flask-oauth2-app.py` (full demo web app), `assets/bot-password-editor.py` (CLI editing script), `references/oauth-endpoints.md`, `references/scopes-reference.md`, `references/common-mistakes.md`, `scripts/register-consumer.sh`, `scripts/test-auth.sh` (tests 3 auth methods), and `tests/test_auth_client.py` (17 mock-based tests). Depends on `wikimedia-api-access`, `wikimedia-error-handling`, `wikimedia-toolforge`.

- **wikimedia-security-and-privacy** — Complete. Covers building tools that respect Wikimedia user privacy and security: data minimization (collecting only needed fields, avoiding PII in logs), deanonymization risks (safe aggregation, forbidden patterns), public log leaks (Toolforge log awareness, IP stripping), data retention (auto-expiring caches, user data deletion), XSS prevention in gadgets and Toolforge apps, AbuseFilter and block awareness (check before editing), suppressed/deleted revision handling (visibility flags, safe display), and permission-aware design (rights checking before actions). Ships with `assets/safe_editor.py` (importable safe editing library with block/protection/rights checks, AbuseFilter handling, and suppressed revision filtering), `assets/privacy_cache.py` (importable auto-expiring cache with PII-safe logging, user data deletion, and aggregate counters), `scripts/check-tool-privacy.sh` (heuristic source code scanner for hardcoded secrets, IP logging, XSS, missing CSP, and other common issues), `references/policy-links.md` (quick-reference WMF policy docs), `references/anti-patterns.md` (12 extended anti-patterns with before/after code), and `tests/test_security_privacy.py` (41 tests). Depends on `wikimedia-api-access`, `wikimedia-auth-oauth`, `wikimedia-toolforge`.

- **wikipedia-wikitables** — Complete. Covers creating, parsing, styling, and fixing MediaWiki wikitable syntax — delimiters (`{|`, `|}`, `|-`, `|+`), header vs. data cells (`!` vs. `|`), 6 built-in CSS classes and their combinations (`wikitable`, `sortable`, `mw-collapsible`, `mw-collapsed`, `mw-datatable`, `sortbottom`), inline CSS at table/row/cell level (alignment, colors, spacing, borders), accessibility (`scope` attributes), colspan/rowspan, and programmatic generation from Python dicts or CSV. Ships with `scripts/wikitable-to-html.sh` (preview in browser), `scripts/generate-table.sh` (CSV → wikitable), `assets/wikitable_tools.py` (importable library with `dicts_to_wikitable`, `parse_wikitable`, `style_cell`, `csv_to_wikitable`), and a 25-test test suite.

### Project infrastructure

- `.claude/skills/<name>/SKILL.md` directory structure with YAML frontmatter (name, description, license, compatibility)
- All skills validated for opencode `skill` tool discovery
- MIT license
- README with install instructions
- GitHub repository initialized at `fuzheado/Wikipedia-AI-Skills`
- `.claude.json` project configuration for agent discovery
- `CONTRIBUTING.md` with skill authoring guidelines, accuracy checklist, and PR process
- Test suite with **250+ tests across 8 modules**: YAML frontmatter validation for all 21 skills (deduplicated),
  mock-based unit tests for the cross-API pipeline script, content-accuracy checks for key SOPs,
  mock-based tests for the Lift Wing multi-model scorer and article quality report,
  citation tool tests (wayback, dead link scanner, linter, generator), category skill tests,
  and template skill tests (expand-template, template-usage, inspect-template scripts,
  template-inspector, template-scanner Python assets, and reference docs)
- `.gitignore` updated to exclude `.pytest_cache/`

## What's outstanding

### Future skill candidates

- **General-topic article drafting** — SOPs for writing non-biography Wikipedia articles (events, organizations, concepts, places). Different structure templates, different notability criteria, different citation patterns. Prior art exists in the original project roadmap.

- **Copyediting for encyclopedic tone** — SOPs for auditing existing articles for NPOV violations, promotional language, weasel words, tone drift, and structural issues. Could include a checklist-style workflow.

- **Pywikibot advanced workflows** — Deeper SOPs for chaining multiple Pywikibot scripts in CI/CD pipelines, integrating with Toolforge Kubernetes jobs, scheduling recurring bot tasks via cron, and monitoring bot health. The current skill covers the fundamentals; this would add deployment and operations guidance.

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

- **Script compliance audit** — Completed a full audit of all 33+ shell and Python scripts across all skills. Fixed 8 scripts with missing zero-argument guards, bash 4+ incompatibilities (`declare -A` → `case`), unsafe `curl | python3` pipes (→ temp files with HTTP status checks), non-portable `mktemp` templates, deferred imports that blocked `--help`. Published `.claude/guidelines/script-audit-guidelines.md` with compliance standard, pre-commit hook template, and CI workflow template.

- **`wikimedia-api-strategy` skill** — New skill (added June 2026) providing a decision framework for choosing between the 6 Wikimedia access methods (REST API, Action API, SPARQL, SQL replicas, EventStreams, Pywikibot). Covers: quick decision flowchart, latency/complexity/authentication comparison table, 6 decision trees by task category (reading, batch, analytics, real-time, editing, graph queries), performance comparison (API vs. SQL speed ratios), strategy selection SOP with constraint checking, common anti-patterns with better alternatives, and quick reference cards by data size/operation scale. Ships with `scripts/api-strategy.sh` (interactive CLI with keyword-based task auto-detection) and `assets/api_selector.py` (importable Python module with `recommend()` and `compare()` functions).

- **Code example standardization** — Systematic fixes to make code examples self-contained and copy-pasteable across all skills:
  - **Curl User-Agent headers:** Added `-H "User-Agent: ..."` to 16 curl commands in 3 skills (pagetriage-api, wikimedia-ml-services, wikipedia-en-article-audit) that previously required manual header setup
  - **Curl `-s` flag:** Added `-s` (silent) to 7 curl commands in wikimedia-ml-services (only skill missing it)
  - **Python `timeout=` parameter:** Added `timeout=30` or `timeout=60` to 17 `requests.post()` and `requests.get()` calls across 3 skills (wikimedia-ml-services, wikimedia-diffs, wikimedia-pageviews) to prevent hanging on slow API responses
  - **Response structure documentation:** Added annotated JSON with field descriptions and access patterns to wikimedia-api-access (Action API query response) and wikimedia-eventstreams (SSE event schema)
  - **SPARQL Python wrappers:** Wrapped the last raw SPARQL block in wikidata (P279 subclass traversal) with complete Python request code including User-Agent, timeout, and response parsing

- **`wikipedia-error-handling` skill** — New skill (added June 2026) covering HTTP error handling across all Wikimedia APIs: status code reference, per-service rate limits, universal retry pattern, SPARQL-specific rate limiting, User-Agent 403 debugging, Lift Wing model errors (422, 404, empty scores), EventStreams connection drops and canary events, SPARQL error handling (timeout, syntax, empty results), and a general debugging checklist. Ships with `scripts/check-api-status.sh` (connectivity checker for 9 endpoints) and `assets/api_client.py` (reusable Python client with retry, rate limiting, SPARQL, Lift Wing, and EventStreams methods).

- **Known Limitations sections** — Added to `wikimedia-ml-services/SKILL.md`: 8 documented limitations including 422 on revision 1, ~60s articlequality latency, no prediction cache, frozen Revscoring models, wiki coverage gaps, per-second rate limits, internal-only models, and heavy model performance.

- **JSON response structure annotations** — Added to `wikimedia-ml-services/SKILL.md` (Revscoring ORES envelope, modern revert-risk envelope, modern articlequality continuous score, all with access patterns) and `wikimedia-diffs/SKILL.md` (Action API compare response with net/churn distinction).

- **Decision tables** — Added to `wikidata/SKILL.md` (11-row "What Do You Want to Do?" table) and `wikimedia-commons/SKILL.md` (10-row table), matching the effective format from `wikipedia-categories`.

- **Diff classification SOP** — Added to `wikimedia-diffs/SKILL.md`: change type classification by byte statistics and diff table structure, common vandalism signatures table, and integration guidance with ML revert-risk scoring.

- **Cross-language SPARQL sitelink examples** — Added to `wikidata/SKILL.md`: complete Python code for cross-language gap analysis using `schema:about` / `schema:isPartOf` pattern with `FILTER NOT EXISTS`. All SPARQL examples now include full Python request code with response parsing.

- **Cross-references between related skills** — Added to `wikidata` (→ ml-services, pageviews, categories, commons), `wikimedia-eventstreams` (→ ml-services, diffs, pagetriage-api), `wikipedia-page-anatomy` (→ templates, wikitext, citations, categories).

- **`skill_discovery_hints` metadata** — Added to 5 skills: `wikidata`, `wikimedia-ml-services`, `wikimedia-eventstreams`, `wikimedia-commons`, `wikipedia-error-handling`. Each maps keywords to skills for automatic agent discovery.

- **WDQS SPARQL rate limits documented** — Researched and documented WDQS-specific rate limits (60s query timeout, 60s processing per 60s window, 30 errors/min, 429 with Retry-After, SLO 95%) in `wikidata/SKILL.md` and `references/wikidata-api.md`. Added 429 handling code example with retry logic. Documented `Accept-Encoding: gzip, deflate` requirement, POST body format for large queries, and `SERVICE wikibase:label` performance warning. Fixed `sparql-query.sh` to use temp-file + HTTP status pattern with explicit 429 detection.

- **Pywikibot `categorypages` → `categorizedpages` rename** — Updated all 5 occurrences of the deprecated `site.categorypages()` method to `site.categorizedpages()` (renamed in Pywikibot v11.3). Affected files: `SKILL.md` (2 code examples), `assets/pywikibot-quickref.py` (2 calls), `references/api-mapping.md` (mapping table).

- **Skill freshness metadata (`last_verified`)** — Added `last_verified: YYYY-MM-DD` to the YAML frontmatter of all skills, documenting when each skill was last reviewed for accuracy. Updated `CONTRIBUTING.md` to require this field. Added test check (`test_last_verified_is_date`) to the test suite. Created `.github/workflows/skill-freshness.yml` — a weekly CI workflow that flags skills not reviewed in >6 months (warning) or >1 year (error).

- **`wikipedia-categories` skill** — new skill covering the Wikipedia category system end-to-end: tree hierarchy, three validity tests (Verifiable/Neutral/Defining), topic vs. set categories, sort keys and DEFAULTSORT, comprehensive comparison of all access methods (Action API, Pywikibot, PetScan, WDQS, Special pages) with trade-off analysis, Pywikibot generators and built-in scripts, overcategorization rules, naming conventions, and category maintenance. Ships with 2 reference docs, 1 CLI script, and 2 Python assets. The proposal was written first in `proposals/categories-skill.md` before implementation.

- **Title Format Guide** (section 11 of `wikimedia-api-access/references/endpoints.md`) — cross-API table documenting underscore-vs-space title formats across 6 endpoints, with correct/wrong code comparison. Fixes the single most costly bug when chaining Pageviews, Action API, and SQL results.
- **Expanded 429 Retry-After handling** in `wikimedia-api-access/SKILL.md` — dedicated subsection explaining the importance of server-supplied Retry-After values, an anti-pattern warning against fixed backoff, and three common causes of 429 responses.
- **Batch entity classification SOP** in `wikidata/SKILL.md` — resolves the gap between the SPARQL-focused Wikidata skill and the need for a concrete multi-API pipeline workflow. Covers batch Wikidata ID resolution, P31 type checking with 11 common Q IDs, and subclass hierarchy traversal.
- **Cross-API pipeline script** (`wikimedia-api-access/assets/cross_api_pipeline.py`) — a runnable 4-step demo showing Pageviews → Wikidata ID resolution → P31 entity classification → content analysis, with proper batch processing, rate limiting, and title normalization.
- **Scenario C (Top Pages)** in `wikimedia-pageviews/SKILL.md` — adds the Top Pages REST endpoint as a third data retrieval path alongside the existing SQL and per-article API scenarios. Includes date format warnings and cross-API chaining guidance.

### Agent integration (event hooks + custom tools)

See **[AGENT-INTEGRATION-STRATEGY.md](AGENT-INTEGRATION-STRATEGY.md)** for the full analysis and phased implementation plan.

**Summary:** Evolve from passive SKILL.md files only to a three-layer architecture:
1. **Event hooks** (`pi.on()`) — auto-enforce User-Agent, rate limiting, auth — invisible to the LLM, fires on every relevant tool call
2. **Custom tools** (`pi.registerTool()`) — callable functions for vector search, page quality, pageviews, diffs, etc. — visible in the LLM's tool list, deterministic execution
3. **Skills (retained)** — reference documentation and creative tasks, serendipitous discovery

**Done:**
- ✅ **Phase 0:** Single pi extension at `.pi/extensions/wikimedia-skills/index.ts` — auto-injects User-Agent headers on all `curl`, `wget`, `python`, and `node` commands targeting Wikimedia servers. Ships with unit tests (36 tests via `node --test`), extension structure validation (13 tests via `pytest`), config.json for customization, and full README install docs.

**Phases:**
- Phase 1: Top 3 hooks — rate limit backoff (`tool_result` interceptor for 429), SSH tunnel health check (`tool_call` before SQL)
- Phase 2: Top 5 custom tools (vector search, page quality, pageviews, page assessment, diffs)
- Phase 3: Keyword-based auto-activation via `before_agent_start`
- Phase 4: Event-driven cross-tool orchestration

### Process

- Write CONTRIBUTING.md with skill authoring guidelines ✅
- Set up a GitHub issue template for skill suggestions
- Add `.claude.json` project configuration for agent discovery ✅
- **Add skill tests** ✅ — `pytest`-based test suite in `tests/` with 290 tests:
    - `test_yaml_frontmatter.py`: YAML frontmatter validation for all skills (5 checks each: exists, required fields, description length, MIT license, directory match; duplicate entries removed)
    - `test_cross_api_pipeline.py`: Mock-based unit tests for the pipeline script (title normalization, batch splitting, P31 classification, citation counting, namespace filtering)
    - `test_markdown_sops.py`: Content-accuracy checks for new/modified SOPs (batch entity classification, Scenario C, Title Format Guide, 429 Retry-After)
    - `test_liftwing_multi_model.py`: Mock-based tests for the Lift Wing multi-model scorer (cache, extractors, formatting, error handling)
    - `test_article_quality_report.py`: Mock-based tests for the article quality report generator (all 4 model extractors, format functions, chaining)
    - `test_citations.py`: Mock-based tests for citation tools (wayback inspector, dead link scanner, citation linter, citation generator — 25 tests)
    - `test_extension.py`: Extension structure and config validation (13 tests)

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
