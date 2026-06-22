# Design Philosophy

This document explains the rationale behind the structure and sizing of skills
in this repository. It's intended for contributors and maintainers who want to
understand *why* skills are built the way they are.

---

## 1. Why Skills Exist

Base LLMs fail at Wikimedia tasks in predictable ways:

- They invent API endpoints (`/api/v2/pages` doesn't exist)
- They omit User-Agent headers and get 403-blocked
- They parse wikitext with regex instead of AST-based tools
- They guess at policy rules (NPOV, notability, category tests)

Skills inject **procedural knowledge** the model doesn't have — specific
endpoints, rate limits, tool syntax, policy rules. The A/B test results
confirm this: 2.8× speedup and 50%→0% error rate with skills loaded.

---

## 2. The Tier System

Not all knowledge deserves its own skill file. We use three tiers to decide
what gets a standalone skill vs. what should be a section inside another skill:

| Tier | Rule | Example |
|------|------|---------|
| **T1 — Foundational** | The model **cannot** do this correctly without the skill | `wikimedia-api-access` (endpoints, rate limits) |
| **T2 — High-value** | The model could figure it out but at 2-5× the time/cost | `wikimedia-search-cirrussearch` (complex syntax) |
| **T3 — Nice-to-have** | Niche workflow, saves hours when needed | `wikimedia-commons-svg` (vector editing) |

**The bar for a new standalone skill:** Either the LLM catastrophically fails
without it (T1), or it saves 2-5× time on a common workflow (T2). If it's
only useful 1% of the time, it should be a reference doc or SOP inside an
existing skill.

**T3 skills are reviewed periodically.** As Wikimedia evolves, some graduate
to T2 (e.g., if a niche API becomes mainstream). Others may be merged if they
never find a broad audience.

---

## 3. Skill Sizing

### The Sweet Spot: 2,000–3,500 words

Most skills in this repo fall into this range. It's deliberate:

- **Below 1,500 words** — too terse; the model may miss critical edge cases
- **Above 5,000 words** — too comprehensive; drains context on small models
- **2,000–3,500** — enough depth for domain expertise, compact enough to load
  8–10 skills simultaneously on 200K-token models

### Splitting vs. Merging

A surprising finding: **splitting skills reduces context bloat, not increases it.**

| Approach | Words Loaded Per Task |
|----------|----------------------|
| One 26K-word monolithic Commons skill | 26,000 (every time) |
| Hub (4K) + 2 specialized sub-skills (3K each) | ~10,000 |

The same logic applies catalog-wide: 43 focused skills are better than 20
monolithic ones. The risk isn't the size of the catalog — it's the size of
individual skills.

### When to Split

Consider splitting a skill into sub-skills when:
- It exceeds 5,000 words
- Different tasks consistently use different subsets of its content
- The sub-domains have genuinely different APIs, policies, or tooling

The [Commons family](https://github.com/fuzheado/Wikipedia-AI-Skills/blob/main/.claude/skills/wikimedia-commons/SKILL.md)
is the model: a 4K hub skill routing to 7 specialized sub-skills (2-5K each).

---

## 4. Context Management Across Model Sizes

Different models have different context windows, but the sizing strategy works
across all of them:

| Model Family | Context | Max Skills* | Our Strategy |
|-------------|---------|-------------|--------------|
| DeepSeek / Gemini | 1M tokens | All 43 + massive headroom | Don't let headroom tempt you to load all skills |
| Claude | 200K tokens | ~35 + 90K free | Comfortable with 3-8 skills per task |
| GPT-4 | 128K tokens | ~20 + 55K free | Tight but workable with 3-5 skills |

*\*~3,800 tokens/skill (2,900 words + code), ~10K system prompt, ~30K conversation*

**The real defense isn't the model's context size — it's keyword-based loading.**
A task should load 3-8 skills regardless of model capacity. Loading more
marginally relevant skills dilutes attention even when you have room.

**On 1M-token models:** Don't merge skills to "use the space." Smaller,
focused units compose better because the model attends to each one more
effectively.

---

## 5. What Makes a Good Skill

A skill succeeds when an agent can pick it up and use it without reading
anything else. Every skill should have:

1. **YAML frontmatter** — `name`, `description`, `depends_on`, keywords for discovery
2. **Clear SOPs** — numbered procedures with concrete code examples
3. **Guardrails** — explicit "don't do this" warnings for common mistakes
4. **Tooling section** — scripts, reference docs, and reusable assets
5. **Cross-references** — links to related skills with a "Why" column

The `depends_on` field is critical: it tells the agent which skills are
prerequisites, preventing it from loading a specialized skill without its
foundation.

---

## 6. The Catalog's Upper Bound

There's no hard limit, but there are natural constraints:

- **Keyword collision** — If two skills share too many keywords, the loader
  can't distinguish them, and both load unnecessarily.
- **Maintenance burden** — Each skill needs periodic verification of API
  endpoints, rate limits, and policies. More skills = more surface area.
- **Discovery fatigue** — The `<available_skills>` list shown to agents grows.
  Keep descriptions distinct and action-oriented.

The current portfolio of 43 skills is comfortably within these bounds.
Additions should pass the tier test, and merges should happen when a skill
proves narrower than anticipated.
