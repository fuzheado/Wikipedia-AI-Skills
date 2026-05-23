# Wikipedia AI Skills

A curated collection of reusable skill files for AI coding agents — [OpenCode](https://opencode.ai), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), and any agent that supports the `.claude/<name>/SKILL.md` convention — to help with Wikipedia and Wikimedia-related tasks.

Each skill is a self-contained set of instructions, policy knowledge, and code examples that an agent loads on demand via the `skill` tool. This means agents get expert-level guidance without bloating their system prompt.

## Skills

| Name | Description |
|------|-------------|
| [wikimedia-api-access](.claude/skills/wikimedia-api-access/SKILL.md) | Access Wikimedia APIs (REST, Action, SPARQL) with correct User-Agent headers, rate limiting, and 429/403 error handling |
| [wikimedia-database](.claude/skills/wikimedia-database/SKILL.md) | Execute SQL queries against Wikimedia production replicas via an SSH tunnel to Toolforge |
| [wikimedia-pageviews](.claude/skills/wikimedia-pageviews/SKILL.md) | Retrieve traffic and popularity statistics for Wikipedia articles using cached SQL properties or the REST API |
| [wikipedia-en-biography-writing](.claude/skills/wikipedia-en-biography-writing/SKILL.md) | Draft and edit English Wikipedia biographies following NPOV, verifiability, no original research, and BLP policies |
| [wikimedia-toolforge](.claude/skills/wikimedia-toolforge/SKILL.md) | Manage Toolforge accounts, web services, Kubernetes pods, cron jobs, and file deployment for Wikimedia tools |
| [wikimedia-cdn-assets](.claude/skills/wikimedia-cdn-assets/SKILL.md) | Guides agents on loading JavaScript, CSS, and fonts from Wikimedia's privacy-preserving cdnjs.toolforge.org CDN to ensure user privacy and policy compliance. |

## Usage

### Install all skills into your project

```bash
git clone https://github.com/fuzheado/Wikipedia-AI-Skills.git
cp -r Wikipedia-AI-Skills/.claude /path/to/your/project/
```

### Install a single skill

```bash
cp -r Wikipedia-AI-Skills/.claude/skills/wikimedia-pageviews /path/to/your/project/.claude/skills/
```

Once installed, your AI coding agent will discover the skill automatically through the `skill` tool. You can also open any `SKILL.md` file and paste its contents directly into an agent's instructions.

## Skill format

Every skill lives in `.claude/skills/<name>/` with this enhanced structure:

```
my-skill/
├── SKILL.md              # Agent-facing instructions with SOPs
├── scripts/              # Executable helpers (bash, python, etc.)
├── references/           # Deep reference docs loaded on-demand
└── assets/               # Templates, config files, sample data
```

The `SKILL.md` file includes YAML frontmatter for agent discovery:

```yaml
---
name: skill-name
description: Short description for agent discovery
license: MIT
compatibility: opencode
---
## SOP: ...
...agent-facing instructions...
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on adding new skills, improving existing ones, and the pull request process. All skills must follow the YAML frontmatter format and pass the content accuracy checklist.

## Enhancement Status

This repository is undergoing an enhancement pass to add executable tooling
(scripts, reference docs, and templates) to each skill beyond just
`SKILL.md` instructions.

✅ `wikimedia-api-access` — Enhanced with scripts, references, assets
✅ `wikimedia-database` — Enhanced with scripts, references, assets
✅ `wikimedia-pageviews` — Enhanced with scripts, references, assets
✅ `wikipedia-en-biography-writing` — Enhanced with scripts, references, assets
✅ `wikimedia-toolforge` — Enhanced with scripts, references, assets
✅ `wikimedia-cdn-assets` — Enhanced with scripts, references, assets

All 6 skills completed. See the [Enhancement Handbook](ENHANCEMENT-HANDBOOK.md) for the full reference and enhancement pattern.

## License

MIT
