# Wikipedia AI Skills

A curated collection of reusable skill files for AI coding agents — [OpenCode](https://opencode.ai), [Claude Code](https://docs.anthropic.com/en/docs/claude-code), and any agent that supports the `.claude/<name>/SKILL.md` convention — to help with Wikipedia and Wikimedia-related tasks.

Each skill is a self-contained set of instructions, policy knowledge, and code examples that an agent loads on demand via the `skill` tool. This means agents get expert-level guidance without bloating their system prompt.

## Skills

| Name | Description |
|------|-------------|
| [wikidata](.claude/skills/wikidata/SKILL.md) | Understand and query Wikidata — the free, collaborative, multilingual knowledge graph that underpins Wikipedia's inter-language links, Commons structured data, and semantic facts across all Wikimedia projects. Covers SPARQL, the Wikibase REST/Action APIs, RDF data dumps, and semantic web concepts |
| [wikimedia-api-access](.claude/skills/wikimedia-api-access/SKILL.md) | Access Wikimedia APIs (REST, Action, SPARQL) with correct User-Agent headers, rate limiting, and 429/403 error handling |
| [wikimedia-commons](.claude/skills/wikimedia-commons/SKILL.md) | Search and understand Wikimedia Commons — the free media repository of images, video, sound, 3D files, PDFs, and other media used across Wikipedia and its sister projects |
| [wikimedia-database](.claude/skills/wikimedia-database/SKILL.md) | Execute SQL queries against Wikimedia production replicas via an SSH tunnel to Toolforge |
| [wikimedia-pageviews](.claude/skills/wikimedia-pageviews/SKILL.md) | Retrieve traffic and popularity statistics for Wikipedia articles using cached SQL properties or the REST API |
| [wikipedia-en-biography-writing](.claude/skills/wikipedia-en-biography-writing/SKILL.md) | Draft and edit English Wikipedia biographies following NPOV, verifiability, no original research, and BLP policies |
| [wikimedia-toolforge](.claude/skills/wikimedia-toolforge/SKILL.md) | Manage Toolforge accounts, web services, Kubernetes pods, cron jobs, and file deployment for Wikimedia tools |
| [wikimedia-cdn-assets](.claude/skills/wikimedia-cdn-assets/SKILL.md) | Guides agents on loading JavaScript, CSS, and fonts from Wikimedia's privacy-preserving cdnjs.toolforge.org CDN to ensure user privacy and policy compliance. |
| [wikimedia-wikitext](.claude/skills/wikimedia-wikitext/SKILL.md) | Parse, extract, and manipulate Wikipedia and MediaWiki wikitext (templates, infoboxes, citations, links) using proper AST-based tooling or the Parsoid HTML REST API |

## Usage

### Install all skills into your project

```bash
git clone https://github.com/fuzheado/Wikipedia-AI-Skills.git
cp -r Wikipedia-AI-Skills/.claude /path/to/your/project/
```

### Install a single skill

```bash
cp -r Wikipedia-AI-Skills/.claude/skills/wikimedia-commons /path/to/your/project/.claude/skills/
```

Once installed, your AI coding agent will discover the skill automatically through the `skill` tool. You can also open any `SKILL.md` file and paste its contents directly into an agent's instructions.

### Pi agent setup

[Pi](https://github.com/earendil-works/pi-coding-agent) discovers skills from anywhere on the filesystem via `settings.json`. To use these skills in pi:

```bash
mkdir -p ~/.pi/repos
git clone https://github.com/fuzheado/Wikipedia-AI-Skills.git ~/.pi/repos/Wikipedia-AI-Skills
```

Then add the skills path to `~/.pi/agent/settings.json`:

```json
{
  "skills": [
    "~/.pi/repos/Wikipedia-AI-Skills/.claude/skills"
  ]
}
```

After restarting pi, all the skills will be available on-demand.

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


## License

MIT
