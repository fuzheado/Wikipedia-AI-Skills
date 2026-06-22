# Skill Enhancement Handbook

> **If you are an AI coding agent reading this:** This document describes a
> completed project to enhance this repository's skills with
> executable tooling (scripts, reference docs, templates) beyond just
> `SKILL.md` instructions. If your task involves any of the skills listed
> below, read on — all skills have received the same treatment.

---

## What This Is

This repo has **45 skills** in `.claude/skills/<name>/SKILL.md`. Initially, each
was just a single `SKILL.md` file with instructions. The goal was to **enhance
every skill** with the full agent-skills structure — completed June 2026.

```
my-skill/
├── SKILL.md              # Updated to reference the new tooling
├── scripts/              # Executable helpers (bash, python, etc.)
├── references/           # Deep reference docs loaded on-demand
└── assets/               # Templates, config files, sample data
```

This makes the skills more powerful — the agent can run actual scripts, load
deep reference material, and hand users ready-to-use templates.

---

## ✅ Completed: `wikimedia-api-access`

This skill is fully enhanced. Use it as a reference implementation.

### What was built

| File | Type | Purpose |
|---|---|---|
| `scripts/test-api.sh` | 🎬 Script | Tests 9 endpoints across Action, REST, SPARQL, Pageviews APIs. Reports green/red per endpoint. |
| `references/endpoints.md` | 📚 Reference | Full catalog of all Wikimedia API endpoints, organized by API family, with parameters and examples |
| `assets/user-agent-template.py` | 🧩 Template | Production-ready Python client with rate limiting, retries, error handling, and convenience methods for all 4 API families |
| `SKILL.md` | 📖 Instructions | Updated with "Tooling" section referencing all 3 new files |

### Key design decisions (for consistency)

1. **Temp files for large responses** — bash `echo` mangles large HTML/JSON
   bodies on macOS. Scripts write curl output to a temp file, extract HTTP code
   with `tail -1`, and extract body with `sed '$d'`.
2. **`set -euo pipefail`** — used throughout for safety.
3. **All-green test suite** — every script's tests must pass before considering
   a skill complete.
4. **Date formats matter** — Pageviews API uses `YYYY/MM/DD` (slashes),
   not compact format. Data is delayed ~48 hours; test with 3 days ago.

---

## 📋 Enhancement Pattern

### Step 1: Read the `SKILL.md`

Understand what the skill does, what services it depends on, and what code
examples it already contains. These are candidates for extraction into
scripts/assets.

### Step 2: Create `scripts/` — executable helpers

Each script should be:
- **Self-contained** — assumes only the skill's documented prerequisites
- **Parameterized** — no hardcoded user-specific values
- **Executable** — `chmod +x`
- **Error-handling** — clear failure messages, graceful exits
- **Self-documenting** — `--help` or usage header

**Good candidates:**
- Connectivity/health check tests
- SSH tunnel management
- Query runners
- Deployment tools
- Validation checks (notability, citations, etc.)

### Step 3: Create `references/` — deep reference docs

Progressive disclosure — loaded on-demand when the agent needs depth.

**Good candidates:**
- API endpoint catalogs
- Database schema docs
- Policy deep-dives
- Common query patterns
- Troubleshooting guides

### Step 4: Create `assets/` — templates and configs

Files the agent can copy, customize, and hand to the user.

**Good candidates:**
- Client templates with configuration placeholders
- SQL query files with common patterns
- Article/biography templates
- Config files (`.env.example`, YAML configs)

### Step 5: Update `SKILL.md`

Add a **"Tooling"** section at the bottom. Show usage examples for each file.

### Step 6: Test everything

Run every script. Import/test every template. Verify SKILL.md renders correctly.

---

## ✅ Completed: All 45 Skills

The enhancement project is complete. Every skill in the repository now has
scripts, reference docs, and/or assets. The 8 skills below were the first to
receive full treatment and served as the reference implementation.

### 1. `wikimedia-database`
| File | Type | Purpose |
|---|---|---|
| `scripts/setup-tunnel.sh` | 🎬 Script | Establish SSH tunnel to Toolforge replicas |
| `scripts/query.sh` | 🎬 Script | Run SQL query against a replica, format results |
| `scripts/close-tunnel.sh` | 🎬 Script | Cleanly tear down tunnel |
| `references/schema-replicas.md` | 📚 Reference | Key table schemas (page, revision, page_props, etc.) |
| `references/connection-guide.md` | 📚 Reference | SSH config, auth methods, troubleshooting |
| `assets/sample-queries.sql` | 🧩 Template | 50+ pre-built SQL queries organized by category |
| `assets/.env.example` | 🧩 Template | Environment variable template |

### 2. `wikimedia-pageviews`
| File | Type | Purpose |
|---|---|---|
| `scripts/top-pages.sh` | 🎬 Script | Fetch top N pages for a project or category |
| `scripts/per-article.sh` | 🎬 Script | Fetch historical pageviews for a specific article with bar chart |
| `references/pageview-api.md` | 📚 Reference | Full REST API parameter reference |
| `assets/example-queries.sql` | 🧩 Template | SQL for page_props pageview lookups |
| `assets/analysis-template.py` | 🐍 Template | Python script for trend analysis with multiple output modes |

### 3. `wikipedia-en-biography-writing`
| File | Type | Purpose |
|---|---|---|
| `scripts/check-notability.sh` | 🎬 Script | Walk through notability criteria with structured assessment |
| `scripts/citation-check.sh` | 🎬 Script | Check a draft for citation issues and hallucination risks |
| `references/policies.md` | 📚 Reference | Key policy excerpts (NPOV, BLP, V, NOR) with checklists |
| `references/notability-guide.md` | 📚 Reference | Deep dive on all notability guidelines with flowchart |
| `assets/biography-template.md` | 🧩 Template | Article skeleton with standard sections and checklist |
| `assets/citation-template.md` | 🧩 Template | Ready-to-use citation templates with anti-hallucination rules |
| `assets/infobox-templates/` | 🧩 Template | Templates for 6 subject-specific infobox types |

### 4. `wikimedia-toolforge`
| File | Type | Purpose |
|---|---|---|
| `scripts/deploy.sh` | 🎬 Script | Deploy files via rsync with dry-run preview |
| `scripts/status.sh` | 🎬 Script | Check web service, jobs, disk usage, and active processes |
| `scripts/manage-k8s.sh` | 🎬 Script | Manage Kubernetes jobs (run, list, logs, delete) |
| `scripts/manage-cron.sh` | 🎬 Script | Manage cron jobs (list, add, remove by pattern) |
| `references/toolforge-cli.md` | 📚 Reference | CLI command reference organized by category |
| `assets/deploy-config.sh` | 🧩 Template | Deployment configuration template |
| `assets/app-template.py` | 🐍 Template | Ready-to-deploy Flask app with Wikimedia API proxy |

### 5. `wikimedia-cdn-assets`
| File | Type | Purpose |
|---|---|---|
| `scripts/check-cdn.sh` | 🎬 Script | Verify a CDN URL is accessible or search by library name |
| `scripts/list-available.sh` | 🎬 Script | Search and list available libraries on the cdnjs mirror |
| `references/cdn-mirror-guide.md` | 📚 Reference | Complete CDN mirror usage guide with troubleshooting |
| `assets/load-template.html` | 🧩 Template | HTML page loading jQuery, Bootstrap, and Font Awesome from CDN |
| `assets/load-template.js` | 🧩 Template | Dynamic JavaScript asset loader for programmatic use |

### 6. `wikimedia-commons`
| File | Type | Purpose |
|---|---|---|
| `scripts/commons-search.sh` | 🎬 Script | Search Commons via CirrusSearch or MediaSearch backend, with `--ns` namespace override |
| `references/commons-api.md` | 📚 Reference | Commons Action API and REST API endpoints, license detection patterns |
| `assets/commons-file-inspector.py` | 🐍 Template | Inspect a Commons file's license, author, categories, usage across wikis, and EXIF data |

### 7. `wikidata`
| File | Type | Purpose |
|---|---|---|
| `scripts/wikidata-lookup.sh` | 🎬 Script | Look up a Wikidata item or property by Q/P ID — returns label, description, and basic statements |
| `scripts/sparql-query.sh` | 🎬 Script | Run a SPARQL query against the Wikidata Query Service and display results |
| `references/wikidata-api.md` | 📚 Reference | Wikibase Action API modules, SPARQL query patterns, common Q/P ID reference card |
| `assets/wikidata-entity-fetcher.py` | 🐍 Template | Fetch and display Wikidata item data — labels, descriptions, claims with qualifiers, sitelinks |

---

## Completed Skill: Full Reference

To see the complete enhanced structure, look at:

```
.claude/skills/wikimedia-api-access/
├── SKILL.md
├── scripts/
│   └── test-api.sh
├── references/
│   └── endpoints.md
└── assets/
    └── user-agent-template.py
```

## Agent Discovery

These skills are loaded by pi via:
- **Repo location:** `~/.pi/repos/Wikipedia-AI-Skills/`
- **pi config:** `~/.pi/agent/settings.json` has `"skills": ["~/.pi/repos/Wikipedia-AI-Skills/.claude/skills"]`
- **Sync:** `~/.pi/bin/sync-wikimedia-skills` (runs daily at 9 AM via cron)

## pi Skills Documentation

See: `/opt/homebrew/lib/node_modules/@earendil-works/pi-coding-agent/docs/skills.md`
