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
---
```

The fields are:

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Hyphenated, lowercase identifier (e.g., `wikimedia-pageviews`). This is how agents reference the skill. |
| `description` | Yes | One sentence describing what the skill does. Shown in the agent's `<available_skills>` list. Keep under 200 characters. |
| `license` | Yes | Must be `MIT` for this project. |
| `compatibility` | Yes | The agent platform (e.g., `opencode`, `claude-code`). Use `opencode` as the default. |
| `depends_on` | No | A list of skill names this skill depends on (e.g., `[wikimedia-api-access]`). |

### Frontmatter Validation Checklist

- [ ] `name` is lowercase, hyphenated, and unique
- [ ] `description` is under 200 characters and describes what the agent will be able to do
- [ ] `license` is `MIT`
- [ ] `compatibility` is `opencode` (or appropriate platform)
- [ ] If `depends_on` is present, each dependency exists in the repository
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

## Pull Request Process

1. **Fork and branch** — Create a feature branch from `main`
2. **One change per PR** — If you have multiple changes, submit separate PRs
3. **Update the README** — If adding a new skill, add it to the skill table in README.md
4. **Update the ROADMAP** — Move the completed item from "Planned" to "Published" if it was listed
5. **Run the checklist** — Go through the [Content Accuracy Checklist](#content-accuracy-checklist)
6. **Open the PR** — Include a clear description of what changed and why

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

---

Thank you for contributing to make Wikipedia AI Skills better for everyone!
