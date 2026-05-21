# Roadmap

## What's done

### Published skills

- **wikimedia-api-access** — Complete. Covers Wikimedia API entry points (REST, Action, SPARQL), User-Agent policy compliance with `ContentGapResearch` as the project identifier, rate limiting with Retry-After backoff, connection reuse via `requests.Session()`, 403/429 error handling, and browser-based `Api-User-Agent` workaround. Links to the official Wikimedia Foundation User-Agent Policy.

- **wikimedia-database** — Complete. Covers SSH tunnel setup and connection management (plain `ssh` and `autossh`), Python implementation with `pymysql`, configurable local port via `TOOLFORGE_DB_PORT` (default 3307), and data handling guardrails (read-only, namespace filtering, binary decoding, safety limits, database naming conventions).

- **wikimedia-pageviews** — Complete. Covers two data retrieval paths: cached SQL property (`page_props.pp_propname = 'pageview_daily_average'` with `CAST AS UNSIGNED`) for sorting/filtering large result sets, and the Analytics QuickMetrics REST API for precise historical data. Includes the "no table" guardrail (pageviews table does not exist in SQL replicas).

- **wikimedia-toolforge** — Complete. Covers Toolforge account setup, tool creation, file deployment (rsync, git), web services management (Kubernetes-backed, all runtimes), Kubernetes jobs for batch tasks, cron jobs, environment variables and secrets, logs and debugging. Includes nine guardrails covering common pitfalls (become, SSH keys, NFS, resource limits, etc.) and full example workflows.

- **wikipedia-en-biography-writing** — Complete. Covers notability assessment (WP:GNG, WP:ANYBIO, WP:NACADEMIC, WP:NARTIST, WP:NCREATIVE), biography article structure with wiki markup templates (Infobox person, citation templates, section ordering), citation requirements per section, source hierarchy, policy guardrails for BLP/NPOV/NOR/Verifiability, and seven strict anti-hallucination rules.

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

- **Wikimedia Commons** — Upload workflow, licensing guidance, category navigation, and image description templates.

- **Wikidata** — Entity creation, property selection, query patterns via SPARQL, and reconciliation workflows.

### Improvements to existing skills

- Add more domain-specific infobox templates to the biography skill (e.g., `Infobox scientist`, `Infobox writer`, `Infobox artist`, `Infobox athlete`)
- Add `Api-User-Agent` header guidance to the API access skill for browser-based tools
- Consider adding citation template generators for common scenarios (book with ISBN lookup, news article with URL extraction)

### Process

- Add skill tests: for each skill, define a set of prompts to validate that agents follow the SOP correctly
- Write CONTRIBUTING.md with skill authoring guidelines ✅
- Set up a GitHub issue template for skill suggestions
- Add `.claude.json` project configuration for agent discovery ✅

## Key decisions

### `.claude/skills/<name>/SKILL.md` over flat `.md` files

**Decision:** Each skill lives in `.claude/skills/<name>/SKILL.md` rather than as a flat Markdown file at the project root or directly in `.claude/<name>/`.

**Why:** This is the standard convention documented by opencode, which searches `.claude/skills/*/SKILL.md`. Agents discover skills automatically via the `skill` tool, which reads `name` and `description` from YAML frontmatter and presents them as available tools. Flat files require manual copy-paste into system prompts. The `skills/` subdirectory keeps the `.claude/` namespace clean and is compatible with both opencode and Claude Code discovery mechanisms. The directory-per-skill layout also allows for future expansion (supporting scripts, test data, or sub-documents per skill).

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
