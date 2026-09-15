# Contributing to Wikipedia AI Skills

Thank you for your interest in contributing! This project provides reusable skill files for AI coding agents to help with Wikipedia and Wikimedia-related tasks.

## Table of Contents

- [Types of Contributions](#types-of-contributions)
- [Skill Format](#skill-format)
- [Skill Authoring Guidelines](#skill-authoring-guidelines)
- [Content Accuracy Checklist](#content-accuracy-checklist)
- [Testing Your Skill](#testing-your-skill)
- [Pull Request Process](#pull-request-process)
- [Style Guide](#style-guide)

## Types of Contributions

- **New skills** — A self-contained SOP for a new Wikipedia/Wikimedia task
- **Improvements to existing skills** — Better code examples, clearer guardrails, additional edge cases
- **Bug fixes** — Broken links, outdated policy references, incorrect code
- **Tests** — Prompt-test pairs that validate skill behavior
- **Documentation** — README, this guide, or other project docs

## Skill Format

Every skill lives in `.claude/skills/<name>/SKILL.md` and must include YAML frontmatter at the top:

```yaml
---
name: skill-name
description: Short description for agent discovery
license: MIT
compatibility: opencode
last_verified: 2026-06-10
---
```

The fields are:

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Hyphenated, lowercase identifier (e.g., `wikimedia-pageviews`). This is how agents reference the skill. |
| `description` | Yes | One sentence describing what the skill does. Shown in the agent's `<available_skills>` list. Aim for under 200 characters, max 400. |
| `license` | Yes | Must be `MIT` for this project. |
| `compatibility` | Yes | The agent platform (e.g., `opencode`, `claude-code`). Use `opencode` as the default. |
| `last_verified` | Yes | ISO-8601 date (e.g., `2026-06-10`) when the skill's content was last reviewed for accuracy against the systems it documents. Bump this when making substantive edits. |
| `depends_on` | No | A list of skill names this skill depends on (e.g., `[wikimedia-api-access]`). |
| `skill_discovery_hints` | No | A list of keyword groups that help AI agents discover this skill by topic. Each group is a `{keywords: [...]}` mapping. Add when the skill covers a topic that users commonly search for by these terms. |

Example with optional fields:

```yaml
---
name: wikidata
description: Understand and query Wikidata — SPARQL, Wikibase APIs, RDF dumps
license: MIT
compatibility: opencode
last_verified: 2026-06-10
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["SPARQL", "Wikidata", "knowledge graph", "QID", "entity"]
  - keywords: ["cross-wiki", "interlanguage", "sitelink"]
---
```

### Frontmatter Validation Checklist

- [ ] `name` is lowercase, hyphenated, and unique
- [ ] `description` is under 200 characters (max 400) and describes what the agent will be able to do
- [ ] `license` is `MIT`
- [ ] `compatibility` is `opencode` (or appropriate platform)
- [ ] `last_verified` is a valid ISO-8601 date
- [ ] `last_verified` is reasonably current (check `skill-freshness.yml` CI if applicable)
- [ ] If `depends_on` is present, each dependency exists in the repository
- [ ] `skill_discovery_hints` keywords are lowercase, relevant, and not duplicated across skills
- [ ] No trailing spaces in frontmatter values

## Skill Authoring Guidelines

### 1. Write for Agents, Not Humans

Skills are injected into an agent's context and consume tokens. Every sentence must earn its place.

**Do** write:
```markdown
## SOP: Data Source Selection

Use the `page_props` table for sorting by popularity. Use the REST API for precise historical data.
```

**Do not** write:
```markdown
## Overview

In this section, we will explore the different ways to access pageview data. First, let's understand the background...
```

### 2. Use the SOP Structure

Organize skills as Standard Operating Procedures with clear step-by-step instructions:

```markdown
## SOP: Main Task

### 1. Prerequisites
What must be in place before starting.

### 2. Implementation
Concrete code examples the agent can use directly.

### 3. Guardrails
Rules the agent must follow to avoid errors.
```

### 3. Include Guardrails

Every skill must include a guardrails section that prevents common mistakes. If there's a way for an agent to fail, document it.

### 4. Provide Concrete Code Examples

Agents copy-paste code. Provide runnable examples with realistic placeholder values:

```python
# Good
headers = {
    'User-Agent': 'MyBot/1.0 (https://example.com; user@example.com) ProjectName'
}

# Bad
headers = {
    'User-Agent': '<your-user-agent>'
}
```

### 5. Follow the Policy Reference Rule

Every Wikipedia policy reference (WP:NPOV, WP:BLP, etc.) must include a working link to the policy page on Wikipedia. Do not assume the agent knows the policy.

### 6. One Concern Per Skill

Each skill should cover one well-defined task. If a skill covers two unrelated concerns, split it.

### 7. Name Files Correctly

- Directory: `.claude/skills/<skill-name>/`
- File: `.claude/skills/<skill-name>/SKILL.md`
- The directory name and the `name` field in frontmatter must match.

### 8. Cross-Reference What the Skill Uses

Skill-to-skill links become graph edges (`docs/skills-network.html`) and relationship chips in the
skills explorer, so they are read as claims about how the skills fit together:

- **Link a skill only for a capability, technique, or artifact this skill actually uses** — and say
  which one in the table's *Why* column ("`langlinks` table for interlanguage lookups", not
  "general concepts").
- **Do not link the universal hubs from leaf skills.** `wikimedia-api-access` (and friends) are one
  hop from everything already; adding them everywhere adds edges without adding information and
  inflates the node in the force-directed layout. Use the `depends_on` field for genuine
  prerequisites instead.
- **Avoid trivia and structural-only links** ("runs on X infrastructure", "the sister project").
  If the only relationship is that both skills are Wikimedia-adjacent, leave it out.
- **Do not link to yourself** — self-links are ignored by the graph but show up as noise in tables.

Auditing an existing skill: regenerate the explorer with `python3 scripts/generate-skills-explorer.py`
and read each card's related-skill list as a set of claims to check against the skill body.

### 9. Research APIs Thoroughly — Don't Stop at the TOC

Wikimedia API documentation is extensive and often spread across multiple pages.
The following failure mode has happened in production: an agent reads a
summary/table-of-contents page, assumes it is the full documentation, and writes
incorrect code based on missing or inferred details. To avoid this:

1. **The TOC page is never the full documentation.** Wikitech, the API Portal,
   and MediaWiki docs use a hub-and-spoke model: one index page links to many
   individual endpoint pages. Always follow the links to individual pages.

2. **Verify model and endpoint names against the actual reference.**
   Don't invent names by combining words from a description. For example, the
   Lift Wing API lists "Get language agnostic articlequality prediction" — the
   model name is `articlequality`, not `articlequality-language-agnostic`.
   The only way to know this is to read the individual page.

3. **Don't assume consistent naming conventions.** One model may use `rev_id`,
   another `page_title`, another `title`, another `text`. Each defines its own
   parameter schema. Check per-model docs.

4. **Don't assume URL patterns are uniform.** Not every service under
   `api.wikimedia.org/service/lw/` follows the same URL scheme. Some use POST,
   some GET. Some use path parameters, some query strings. Verify each URL from
   its own documentation.

5. **A 404 is not proof a resource doesn't exist.** When you get a 404, first
   check for:
   - A different URL path prefix (e.g., `/recommendation/` vs `/inference/`)
   - A different model name (e.g., `articlequality` vs `articlequality-language-agnostic`)
   - A different HTTP method (GET vs POST)
   - A different parameter style (query params vs JSON body)

6. **Test every model/endpoint against the live API before finalizing code.**
   Documentation can be stale or aspirational. A 30-second curl call can surface
   response format differences, missing models, or parameter name mismatches
   that would otherwise end up in a skill.

    ```bash
    # Workflow: systematically verify all endpoints from a TOC page
    # 1. Fetch the TOC
    curl -sL 'https://api.wikimedia.org/wiki/Lift_Wing_API/Reference' \
      | grep -oP 'href="[^"]*"' | grep -i 'Get_' > endpoint_pages.txt

    # 2. For each endpoint page, extract the URL, parameters, and method
    for page in $(cat endpoint_pages.txt); do
        curl -sL "https://api.wikimedia.org$page" \
          | python3 -c "import sys,re; print(re.sub(r'<[^>]+>',' ',sys.stdin.read()))" \
          | grep -A5 'POST\|GET\|Parameters\|Responses'
    done

    # 3. Test each model with a known-good revision ID
    curl -s -X POST 'https://api.wikimedia.org/service/lw/inference/v1/models/MODEL:predict' \
      -H 'Content-Type: application/json' \
      -H 'User-Agent: SkillValidator/1.0 (contact) ContentGapResearch' \
      -d '{"rev_id": 123456789, "lang": "en"}'
    ```

7. **When in doubt, check the model card.** Every Lift Wing model has a model
   card on Meta-Wiki that documents training data, performance metrics, and
   appropriate use cases. The model card is the authoritative source — not
   the API docs, not the Wikitech page.

## Content Accuracy Checklist

Before submitting a skill, verify every item:

### Policy References
- [ ] Every WP: link resolves (e.g., `https://en.wikipedia.org/wiki/Wikipedia:Notability`)
- [ ] Policy names match the current Wikipedia naming convention
- [ ] Policy descriptions accurately reflect the current guideline

### Code Examples
- [ ] Every code example is syntactically correct
- [ ] API endpoints are valid and not deprecated
- [ ] Environment variable names are consistent throughout the skill
- [ ] Database queries use correct table and column names
- [ ] URLs are not fabricated or guessed

### Technical Facts
- [ ] Rate limits are accurate
- [ ] Database names match Wikimedia's conventions (e.g., `_p` suffix)
- [ ] Port numbers, hostnames, and connection strings are correct
- [ ] Template names match current MediaWiki conventions

### Documentation Freshness
- [ ] **README** updated:
  - Skill table (`## Skills`) — add to the appropriate category (For editors / For tool developers)
  - "What can I do" usage table — add relevant use-case rows
  - Verify the link path follows the pattern `.claude/skills/<name>/SKILL.md`
- [ ] **ROADMAP** updated:
  - Add to "Published skills" section with a brief description of what ships with the skill
  - Remove from "Future skill candidates" if it was listed there
  - Keep prose references to counts generic ("all skills") — hardcoded counts go stale
- [ ] **CI will verify on push:** The `.github/workflows/skill-registration-check.yml` CI workflow checks that:
- [ ] **Ground-truth verification:** `.github/workflows/skill-verification.yml` runs six checks on every PR touching skills:
  - `verify-commands.py` — CLI commands (`toolforge`, `pwb.py`, `webservice`, `sql`, `become`) must exist in `scripts/command-registry.json`
  - `verify-api.py` — `action=`/`prop=`/`list=`/`meta=` tokens must exist in `scripts/api-surface.json`
  - `verify-links.py` — `depends_on`, cross-skill links, and external URLs (status from `scripts/url-registry.json`)
  - `verify-snippets.py` — python/bash/json/js code blocks must parse
  - `verify-freshness.py` — `last_verified` within the freshness window
  - `verify-mul-labels.py` — `mul` (default value) present in SPARQL label services, pinned label readers, and multi-language `languages=` requests
  If you document a new command/API/URL, regenerate the matching registry first (see README "Ground-truth verification suite").
- [ ] **Test suite:** `.github/workflows/tests.yml` runs `python3 -m pytest tests/ -q` on every PR. Node 22 is
  set up for the extension syntax check; dependencies come from `requirements.txt` plus `pytest pyyaml xlrd`.
  - Every skill directory is linked in `README.md`
  - Every skill is mentioned in `ROADMAP.md` under Published skills
  - `conftest.py` auto-discovers all skill directories (no manual list needed)
- [ ] **Test suite** — `conftest.py` auto-discovers new skills (no manual SKILL_NAMES entry needed)
- [ ] **New tests added** for any new Python assets or scripts

### Guardrails
- [ ] All known failure modes for this task are documented
- [ ] Error messages direct the user to a solution
- [ ] Hallucination risks are explicitly called out

## Testing Your Skill

### Manual Testing

After writing or updating a skill, test it with these methods:

1. **Open a project that uses the skill** and verify the agent discovers it:
   ```
   skill  list
   ```

2. **Load the skill** and confirm it appears in context:
   ```
   skill  load <skill-name>
   ```

3. **Run prompt tests** relevant to the skill's domain and verify the agent follows the SOP correctly.

### Prompt-Test Pairs

Consider adding a `tests/` directory in your skill directory with prompt-test pairs. These are not run automatically yet but help reviewers understand what the skill should do:

```
.claude/skills/<skill-name>/
├── SKILL.md
└── tests/
    ├── prompt-1.txt       # Example prompt
    └── expected-1.md      # Expected behavior / guardrail checks
```

### Testing Guardrails

Test that the agent respects each guardrail. For example, if a skill says "never query a table named X", test that the agent refuses to do so or flags it.

### Live-API tests

Tests that make real API calls must be marked `@pytest.mark.slow` (registered in `pytest.ini`; deselect with
`-m "not slow"`) and run their commands through `run_live()` from `tests/live_calls.py` instead of calling
`subprocess.run()` directly:

```python
from live_calls import run_live

@pytest.mark.slow
def test_scanner_real_page():
    result = run_live([sys.executable, str(TMPL_SCANNER), 'Berlin'],
                      capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, f"Failed: {result.stderr}"
```

`run_live()` paces calls at least one second apart (Wikimedia etiquette), retries an HTTP 429 or network drop,
and then **skips** the test with the API output in the skip reason instead of failing CI — data-centre
runners get throttled far more often than laptops (this is what failed the `tests` job on 2026-09-15, with
eight HTTP 429s in `tests/test_templates.py`). Real failures still fail: the transient signatures must match
*and* the command must have exited non-zero. Set `SKILLS_LIVE_STRICT=1` to turn those skips back into
failures when you deliberately want to verify the live API from a given host.

## Pull Request Process

1. **Fork and branch** — Create a feature branch from `main`
2. **One change per PR** — If you have multiple changes, submit separate PRs
3. **Update the README** — If adding a new skill, add it to the skill table in README.md and the "What can I do" usage table
4. **Update the ROADMAP** — Add to "Published skills" with a brief description; remove from "Future skill candidates" if listed
5. **Do NOT update `tests/conftest.py`** — It auto-discovers skill directories from the filesystem
6. **Run the checklist** — Go through the [Content Accuracy Checklist](#content-accuracy-checklist)
7. **Run the full test suite:** `python3 -m pytest tests/ -q`
8. **Open the PR** — Include a clear description of what changed and why. For **new skills**, run the 7-question candidacy filter in [`docs/Design-philosophy.md`](docs/Design-philosophy.md) §2 and record the verdict (which tests passed, and any failure-severity evidence) in the PR description.

> **CI will catch missed registrations.** The `.github/workflows/skill-registration-check.yml` workflow
> runs on every push to the `main` branch and on PRs that touch skill files. It verifies that every
> skill directory is linked in `README.md` and mentioned in `ROADMAP.md`. If the CI fails, fix the
> documentation before merging.

### PR Template

```markdown
## Summary
<!-- One sentence describing the change -->

## Type of Change
- [ ] New skill
- [ ] Improvement to existing skill
- [ ] Bug fix
- [ ] Documentation
- [ ] Other

## Content Accuracy Checklist
- [ ] Policy links verified
- [ ] Code examples tested
- [ ] Guardrails documented
- [ ] Candidacy filter applied (new skills only) — 7 questions + failure-severity test, see `docs/Design-philosophy.md` §2

## Testing
<!-- Describe how you tested the change -->
```

## Style Guide

### Markdown
- Use ATX headings (`##`, `###`, `####`)
- Use fenced code blocks with language specifiers
- Use absolute URLs for external links
- Use relative paths for references within the repository

### Code Examples
- Python examples must use `import` statements that are complete
- Shell commands must use `$` prefix to distinguish from output
- SQL examples should use uppercase keywords (`SELECT`, `FROM`, `WHERE`)

### Wording
- Use imperative mood ("Open a connection", "Set the header")
- Use "must" for requirements, "should" for recommendations, "may" for options
- Avoid "please", "just", "simply" — these are noise for agents
- Use Oxford commas for lists of three or more items

### Links
- Wikipedia policies: `[WP:GNG](https://en.wikipedia.org/wiki/Wikipedia:Notability)`
- Wikimedia docs: `[User-Agent Policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy)`
- Code references: use inline code backticks for variable names, file paths, and commands

For the rationale behind skill sizing, tier assignments, and the split-vs-merge
philosophy, see **[docs/design-philosophy.md](docs/design-philosophy.md)**.

---

Thank you for contributing to make Wikipedia AI Skills better for everyone!
