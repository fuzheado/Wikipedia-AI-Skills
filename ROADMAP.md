# Roadmap

## What's done

### Published skills

- **wikimedia-api-access** — Complete. Covers Wikimedia API entry points (REST, Action, SPARQL), User-Agent policy compliance with `ContentGapResearch` as the project identifier, rate limiting with Retry-After backoff, connection reuse via `requests.Session()`, 403/429 error handling, and browser-based `Api-User-Agent` workaround. Links to the official Wikimedia Foundation User-Agent Policy. Updated to clarify that the Action API and REST API work across all Wikimedia projects (Commons, Wikidata, Wiktionary, etc.) — just swap the domain.

- **wikimedia-commons** — Complete. Covers the two Commons search interfaces (MediaSearch for visual browsing vs. Special:Search/CirrusSearch for advanced queries), structured data search via `haswbstatement:`, programmatic access via the Action/REST APIs, Commons namespaces (File, Gallery, Category, Creator, etc.), categories vs. galleries, licensing guidance (CC0/CC BY/CC BY-SA vs. non-compliant NC/ND licenses), the "three pillars" of free licensing, the fair-use prohibition, uploaded file formats (allowed and disallowed, including MP4 patent issues), bulk upload tools (Pattypan, flickr2commons, url2commons, video2commons, Commonist), the Volunteer Response Team (VRT) permissions verification process, and a search demo script with `--ns` namespace override support.

- **wikidata** — Complete. Covers Wikidata's role as the inter-language linking backbone for Wikipedia, the Q-number (items) and P-number (properties) system, Wikibase as a MediaWiki extension with its own Action API modules (`wbgetentities`, `wbsearchentities`, `wbgetclaims`, etc.), the SPARQL query service at query.wikidata.org (web interface and programmatic access), the fundamental properties P31 (instance of) and P279 (subclass of) with hierarchical query patterns, the community-driven (non-rigid) taxonomy model, a comparison of SPARQL vs. `haswbstatement:`, and workflow guidance for choosing the right access method.

- **wikimedia-database** — Complete. Covers SSH tunnel setup and connection management (plain `ssh` and `autossh`), Python implementation with `pymysql`, configurable local port via `TOOLFORGE_DB_PORT` (default 3307), and data handling guardrails (read-only, namespace filtering, binary decoding, safety limits, database naming conventions).

- **wikimedia-pageviews** — Complete. Covers two data retrieval paths: cached SQL property (`page_props.pp_propname = 'pageview_daily_average'` with `CAST AS UNSIGNED`) for sorting/filtering large result sets, and the Analytics QuickMetrics REST API for precise historical data. Includes the "no table" guardrail (pageviews table does not exist in SQL replicas).

- **wikimedia-page-assessment** — Complete. Covers querying Wikipedia article quality (FA/GA/B/C/Start/Stub) and importance ratings from WikiProject assessment banners stored in `page_assessments` and `page_assessments_projects` tables. Includes deployment scope documentation (which wikis have the extension), full schema reference with real production replica columns (note: `pa_assessed_timestamp` does not exist — use `pa_page_revision` + `revision` table join), CLI scripts for project assessment queries and quality gap detection, Python/pymysql integration for MySQL 9.x compatibility, and 20+ sample SQL queries organized by category.

- **wikimedia-toolforge** — Complete. Covers Toolforge account setup, tool creation, file deployment (rsync, git), web services management (Kubernetes-backed, all runtimes), Kubernetes jobs for batch tasks, cron jobs, environment variables and secrets, logs and debugging. Includes nine guardrails covering common pitfalls (become, SSH keys, NFS, resource limits, etc.) and full example workflows.

- **wikipedia-en-biography-writing** — Complete. Covers notability assessment (WP:GNG, WP:ANYBIO, WP:NACADEMIC, WP:NARTIST, WP:NCREATIVE), biography article structure with wiki markup templates (Infobox person, citation templates, section ordering), citation requirements per section, source hierarchy, policy guardrails for BLP/NPOV/NOR/Verifiability, and seven strict anti-hallucination rules.
- **wikimedia-cdn-assets** — Complete. Guides agents on loading JavaScript, CSS, and fonts from Wikimedia's privacy-preserving cdnjs.toolforge.org CDN to ensure user privacy and policy compliance.

- **wikimedia-diffs** — Complete. Covers fetching and interpreting diffs between Wikipedia page revisions via the Action API `compare` module and the REST API `/compare` endpoint, with HTML diff table parsing using BeautifulSoup, edit magnitude detection (byte churn, net changes, additions vs. removals), diff sharing links, anti-pattern guidance, and a fetch-diff script and diff-stats analyzer.

- **wikimedia-wikitext** — Complete. Covers the two strategies for reading and manipulating MediaWiki wikitext: AST-based parsing with `mwparserfromhell` (for safe template/infobox/citation extraction and modification) and Parsoid HTML strategy via the REST API `/html` endpoint (for read-only data extraction). Includes anti-pattern tables (why regex fails), common edge cases (nested templates, implicit table spans, unicode), and scripts for wikitext inspection and Parsoid HTML fetching.

- **wikipedia-page-anatomy** — Complete. Covers the full structure of a Wikipedia article: lead section conventions, infobox types (template-based and module-backed), category hierarchy with sort keys and hidden categories, citation templates and identifiers (DOI, PMID, ISBN), transcluded templates and maintenance tags, navigation boxes vs. categories vs. infoboxes, redirect and disambiguation detection, protection levels and page existence checks, and an API methods reference table.

- **wikipedia-talk-page** — Complete. Covers the Talk namespace naming conventions, threaded discussion format and indentation rules, signing with ~~~~ and unsigned comment detection, WikiProject banners with assessment quality (FA/GA/B/C/Start/Stub) and importance ratings (Top/High/Mid/Low), automated and manual archiving with MiszaBot configuration, pings and section editing, talk page etiquette (AGF, NPA, striking vs. deleting), and article talk vs. user talk distinctions. Cross-references wikimedia-page-assessment for bulk database queries.

- **wikipedia-edit-history** — Complete. Covers accessing page history via URL and API with pagination, revision record structure (revid, parentid, user, size, tags), diff basics (deferring to wikimedia-diffs for deep mechanics), edit summary conventions and bot identification, minor vs. major edit flags, user attribution and contributions API, byte size analysis with vandalism red flags, undo vs. rollback permissions and the 3RR, revision tags and their meanings (mobile, visual editor, possible vandalism), vandalism detection signals and block status checks, and an API methods reference table.

### Project infrastructure

- `.claude/skills/<name>/SKILL.md` directory structure with YAML frontmatter (name, description, license, compatibility)
- All skills validated for opencode `skill` tool discovery
- MIT license
- README with install instructions
- GitHub repository initialized at `fuzheado/Wikipedia-AI-Skills`
- `.claude.json` project configuration for agent discovery
- `CONTRIBUTING.md` with skill authoring guidelines, accuracy checklist, and PR process

## What's outstanding

### Planned skills

- **General-topic article drafting** — SOPs for writing non-biography Wikipedia articles (events, organizations, concepts, places). Different structure templates, different notability criteria, different citation patterns. Prior art exists in the original project roadmap.

- **Copyediting for encyclopedic tone** — SOPs for auditing existing articles for NPOV violations, promotional language, weasel words, tone drift, and structural issues. Could include a checklist-style workflow.

- **Domain-specific article templates** — Structure templates for common article types: companies, educational institutions, films, albums, software, scientific concepts. Each has distinct section conventions and notability guidelines.

- **Notability assessment tool** — A standalone skill for evaluating whether a subject/topic meets Wikipedia notability criteria before investing in drafting. Could produce a structured report against GNG and relevant SNGs.

- **Citation health checker** — SOPs for checking whether citations actually support the claims they are attached to, identifying dead links, missing metadata, and inappropriate sources.

### Improvements to existing skills

- Add more domain-specific infobox templates to the biography skill (e.g., `Infobox scientist`, `Infobox writer`, `Infobox artist`, `Infobox athlete`)
- Add `Api-User-Agent` header guidance to the API access skill for browser-based tools
- Consider adding citation template generators for common scenarios (book with ISBN lookup, news article with URL extraction)

### Process

- Add skill tests: For each skill, define prompts and validation criteria to ensure agents correctly follow SOPs and adhere to policies.
    - **Testing Facility:** Utilize a Python-based testing framework (e.g., `pytest`) within a dedicated `tests/` directory. Tests will parse `SKILL.md` files, validate YAML frontmatter, extract SOP instructions, and simulate agent interactions to verify adherence to policies and guardrails.
    - **Test Definition:** Tests will cover core functionalities, critical guardrails, content accuracy (e.g., policy references, code examples), and edge cases identified within the skill's SOP.
    - **Coverage Goal:** Aim for a minimum of 3-5 distinct tests per skill, ensuring comprehensive coverage of critical functions and safety constraints. Test suites should be expanded iteratively.
- Write CONTRIBUTING.md with skill authoring guidelines ✅
- Set up a GitHub issue template for skill suggestions
- Add `.claude.json` project configuration for agent discovery ✅

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
