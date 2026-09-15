# Agent Integration Strategy

> **Status: partially implemented** (refreshed 2026-09-15).
>
> Layer 1 (deterministic event hooks) and the first Layer 2 (callable tool) ship today in
> [`.pi/extensions/wikimedia-skills/`](.pi/extensions/wikimedia-skills/) — User-Agent injection,
> curl/wget retry-flag injection, and the `wikidata_vector_search` tool. The remaining hooks and
> tools, keyword auto-activation, and event-driven orchestration are still open.
> See [As-built](#as-built-what-exists-today) and [Still open](#still-open).

> **Scope: a harness-agnostic model, with pi as the reference implementation.**
>
> The examples below are written against pi's extension API (`pi.on()`, `pi.registerTool()`)
> because that is the harness this repository ships an extension for. **The model itself is not
> pi-specific.** All it assumes is that a harness offers three capabilities:
>
> | Layer | Capability the harness must offer |
> |---|---|
> | 1. Hooks | a way to observe or rewrite tool calls before/after they run |
> | 2. Tools | a way to register a callable function the model can invoke |
> | 3. Skills | a way to put instructions on disk that the model reads on demand (`.claude/skills/`) |
>
> Any harness with those three — Claude Code, OpenCode, Cursor, a bespoke MCP client — can apply
> the same design; only the wiring differs. If you are not on pi, read
> [Portability](#portability-harness-capability-mapping) and skip the pi code samples. Layer 3 is
> identical everywhere: this repository's skills follow the `.claude/skills/<name>/SKILL.md`
> convention that several harnesses already read.

## Motivation

The current skill model works well: each skill's YAML front-matter description is always in the
system prompt, and the model can `read` the full SKILL.md when it judges the task relevant. This
gives **broad coverage** and **serendipity** — the model may discover a skill it didn't know it
needed.

However, this model has known failure modes:

| Failure Mode | Example |
|---|---|
| Model ignores a description even when relevant | Sees `wikimedia-api-access` but doesn't read it → 403 from missing User-Agent |
| Model skims instructions and misses a detail | Reads the SPARQL endpoint guide but uses wrong URL format |
| Cross-cutting boilerplate must be re-learned every session | Rate limiting, User-Agent, connection reuse |
| Multiple skills interact; model loads only one | Runs SPARQL with the Wikidata skill but forgets User-Agent from the other |
| Model uses an unexpected approach that bypasses skill coverage | Uses `python requests` instead of `curl` → hook misses it |

The solution is a **three-layer architecture** in which each layer covers the others' failure modes.

## The Three-Layer Architecture

```
┌──────────────────────────────────────────────────┐
│              Layer 1: Event Hooks    ✅ shipped   │
│  pi.on("tool_call", ...)                          │
│  pi.on("before_agent_start", ...)         ⬜ open │
│                                                   │
│  Invisible to the model — runs in the background. │
│  Enforces policy, injects boilerplate, applies    │
│  guardrails automatically on every relevant event.│
│  Reliability: near 100% when event pattern matches│
│  Blind spot: any event pattern you didn't code for│
├──────────────────────────────────────────────────┤
│              Layer 2: Custom Tools   ◐ partial    │
│  pi.registerTool({ name, description, execute })  │
│                                                   │
│  Visible in the Available tools list — the model  │
│  sees them and can call them like functions.      │
│  Deterministic execution when called.             │
│  Best for: frequent, well-defined, repeatable     │
│  actions (vector search, ML scoring, DB queries). │
│  Reliability: near 100% when the model calls it   │
│  Blind spot: model might not think to call it     │
├──────────────────────────────────────────────────┤
│              Layer 3: Skills (SKILL.md)  ✅ 61    │
│                                                   │
│  YAML description always in system prompt.        │
│  Full instructions loaded on-demand via `read`.   │
│  Best for: knowledge-heavy reference, creative    │
│  tasks, infrequent workflows, serendipitous       │
│  discovery.                                       │
│  Reliability: depends on model judgment           │
│  Blind spot: model may skip or skim               │
└──────────────────────────────────────────────────┘
```

## As-built (what exists today)

Everything below lives in [`.pi/extensions/wikimedia-skills/`](.pi/extensions/wikimedia-skills/):

| Piece | Layer | File |
|---|---|---|
| User-Agent enforcement on `curl`, `wget`, `python`, `node` commands hitting Wikimedia hosts | 1 | `index.ts` (registers the `tool_call` hook and a `session_start` config reload), `core.ts` (`targetsWikimedia`, `hasUserAgentAlready`, `injectUserAgent`) |
| Retry-flag injection for curl/wget (rate-limit/backoff ergonomics) | 1 | `core.ts` (`injectRetry`) |
| `wikidata_vector_search` — semantic Wikidata item search as a callable tool | 2 | `tools/vector-search.ts`, registered by `index.ts` |
| User-Agent config (env var → `~/.config/wikimedia-skills/config.json` → shipped default) | — | `config.json` |
| Tests | — | `test-core.mjs` (**51** `node:test` cases, 0 failures), `tests/test_extension.py` (**23** pytest cases) |

**Syntax-check scope (worth knowing before trusting it):** the TypeScript check in
`tests/test_extension.py` parses each source as ESM with Node's built-in type stripping, which
requires copying it to a `.mts` suffix — `node --check` infers module type from the extension or
`package.json`, and the extension declares no `"type"`, so a plain `.ts` read is parsed as
CommonJS and `export interface` looks like a syntax error. Measured on Node 26, the check catches
JavaScript-level syntax errors (e.g. `const x = ;`) but **not** unbalanced braces/parens or invalid
type annotations — `node --check` tolerates those while stripping types, and a guard test asserts
the checker still fails on invalid input. Identifier and registration mistakes are covered by the
structural tests in the same file. No `tsc`/type check runs in CI (typescript is not vendored).

## Layer Details

### Layer 1: Event Hooks (`pi.on()`)

These are extension event listeners that run automatically at specific lifecycle points. The model
**never sees them** — they are infrastructure. (pi's documented events include `tool_call`,
`tool_result`, `before_agent_start`, `context`, and `agent_end`.)

**Recommended hook points:**

| Event | Purpose | Candidates from this repo |
|---|---|---|
| `tool_call` | Intercept bash/curl commands to auto-inject User-Agent headers, rate-limiting backoff, auth tokens | wikimedia-api-access ✅, wikimedia-database, wikimedia-toolforge |
| `tool_result` | Post-process results — parse SPARQL JSON, format Wikidata entity output, detect 403/429 errors | wikidata, wikimedia-api-access |
| `before_agent_start` | Inspect user prompt for keywords and inject relevant skill instructions into the system prompt | All skills — keyword-based auto-activation ⬜ |
| `context` | Filter or augment messages before each model call — inject recent query results as context | wikidata-vector-search (inject item labels) |

**Example — User-Agent enforcement via `tool_call`** (the shape of what ships today):

```typescript
pi.on("tool_call", (event) => {
  if (event.toolName !== "bash") return;
  const cmd = event.input.command;

  // Intercept curl commands that hit Wikimedia
  if (cmd.includes("curl") && /wikipedia\.org|wikidata\.org|wikimedia\.org/.test(cmd)) {
    event.input.command = cmd.replace(
      /curl\b/g,
      "curl -H 'User-Agent: WikipediaAIAgent/1.0 (https://github.com/user; user@email.com) SkillsDemo'"
    );
  }

  // Intercept python scripts that import requests (inject Session header)
  if (cmd.includes("python") && cmd.includes("requests")) {
    event.input.command = [
      `export WIKIMEDIA_USER_AGENT="WikipediaAIAgent/1.0 (https://github.com/user; user@email.com) SkillsDemo"`,
      cmd,
    ].join("\n");
  }
});
```

**What it covers:** every `bash` tool call, every `curl`, every Python HTTP request —
automatically, without the model remembering to load the skill.

**What it misses:** anything the model does via a custom tool, the browser, `wget`, a Node.js
`fetch()`, or any invocation that doesn't match your pattern. Hooks are only as broad as the
patterns you anticipated — which is why Layer 3 still matters.

**Recommendation:** use event hooks only for:
- policies that must **never** be violated (User-Agent, read-only database guard)
- boilerplate that is tedious for the model to re-invoke every session
- auth token injection (Toolforge, database SSH tunnel)

---

### Layer 2: Custom Tools (`pi.registerTool()`)

These are TypeScript functions registered as callable tools. The model sees them in the
`Available tools` section of the system prompt, alongside `bash`, `read`, `write`, and `edit`.
When the model calls them, execution is deterministic — no "did it follow the instructions
correctly" overhead.

**Best candidates from this repo** (frequent, well-defined, repeatable actions):

| Skill | Tool Name | Status |
|---|---|---|
| wikidata-vector-search | `wikidata_vector_search` | ✅ shipped |
| wikimedia-ml-services | `wikimedia_score_quality` | ⬜ |
| wikimedia-pageviews | `wikimedia_pageviews` | ⬜ |
| wikimedia-page-assessment | `wikimedia_page_assessment` | ⬜ |
| wikimedia-database | `wikimedia_database_query` | ⬜ |
| wikimedia-diffs | `wikimedia_fetch_diff` | ⬜ |
| wikimedia-commons | `wikimedia_commons_search` | ⬜ |

**Example — vector search as a callable tool** (abridged from `tools/vector-search.ts`):

```typescript
import { Type } from "typebox";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI) {
  pi.registerTool({
    name: "wikidata_vector_search",
    description:
      "Search Wikidata items by semantic meaning, concept, or natural language. " +
      "Returns QIDs with labels and descriptions. Use when you need to find a " +
      "Wikidata item by meaning rather than exact label match. Supports 100+ languages.",
    promptGuidelines: [
      "Use wikidata_vector_search before making SPARQL queries — you need QIDs first.",
      "For cross-lingual queries, pass the language parameter.",
    ],
    parameters: Type.Object({
      query: Type.String({ description: "Natural language or concept to search for" }),
      language: Type.Optional(Type.String({ description: "Language code (default: en)" })),
      limit: Type.Optional(
        Type.Integer({ description: "Max results (default: 10)", minimum: 1, maximum: 50 })
      ),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      const url = new URL("https://wd-vectordb.wmcloud.org/search_items");
      url.searchParams.set("query", params.query);
      url.searchParams.set("top_k", String(params.limit ?? 10));
      if (params.language) url.searchParams.set("lang", params.language);

      const response = await fetch(url.toString(), {
        headers: { "User-Agent": "…", Accept: "application/json" },
        signal, // respects Ctrl+C / abort
      });
      if (!response.ok) {
        return {
          content: [{ type: "text", text: `Vector search failed: HTTP ${response.status}` }],
          isError: true,
        };
      }
      const data = await response.json();
      return { content: [{ type: "text", text: JSON.stringify(data.results, null, 2) }] };
    },
  });
}
```

**What it covers:** the model sees `wikidata_vector_search` in its tool list — one function call
away, with no `read`, no URL construction, and no chance of header or parameter typos.

**What it misses:** the model must decide to call it. If it thinks "I'll just query Wikidata
directly with SPARQL" and never reaches for the tool, the tool never fires. Same failure mode as
skills, but the bar is lower — calling a tool is simpler than reading a file and following
instructions.

**Recommendation:** use custom tools when a skill's core action is (1) a single API call with
fixed parameters, (2) a database query with safe parameter binding, or (3) anything you want to be
"one-shot". Leave the SKILL.md in place as reference documentation — the tool handles the common
case, the skill covers the long tail.

---

### Layer 3: Skills (Retained as-is)

The existing SKILL.md files stay exactly where they are. They serve roles that hooks and tools
cannot:

| Role | Example |
|---|---|
| Reference documentation | Full SPARQL query patterns, all endpoint URL forms, parameter catalogs |
| Creative/nuanced tasks | Biography writing (NPOV/BLP guidance), article auditing (6-diagnosis pipeline) |
| Infrequent workflows | Toolforge Kubernetes job setup, Pywikibot bot authoring |
| Serendipitous discovery | The model browses descriptions and finds a skill it didn't know existed |

**What they cover:** everything hooks and tools miss — the long tail.

**What they miss:** the model must choose to `read` them. In the three-layer model this is
acceptable: the skill is the *last resort* for what the other layers don't handle.

## Portability: harness capability mapping

The three layers are a pattern, not an API. Rough equivalents:

| Capability | pi (reference implementation) | Claude Code | OpenCode / other MCP harnesses |
|---|---|---|---|
| Layer 3: instructions on disk | `SKILL.md` under `.claude/skills/` | `SKILL.md` under `.claude/skills/`, plus `CLAUDE.md` | `.claude/skills/` or harness-native rule/instruction files; `AGENTS.md` |
| Layer 1: pre/post tool interception | extension event hooks (`pi.on("tool_call")`) | hooks configured in `settings.json` (e.g. pre/post tool-use events) | plugin/extension hooks where supported; otherwise a wrapper script or an MCP server that performs the request |
| Layer 2: callable tools | `pi.registerTool()` in an extension | MCP server (`claude mcp add …`) | MCP server, or harness-native custom tool files |
| Layer 1 alternative (no hook API) | — | a wrapper command the model is told to use; a `PreToolUse` hook that rewrites the command | same: wrap the request in a helper script (`wmapi curl …`) and instruct the model to use it |
| Config/secret injection | `config.json` + env var | env var / `.env` / MCP server env | env var / MCP server env |

Practical guidance for a non-pi harness:

1. **Keep Layer 3 unchanged.** Start with the skills; they are portable as-is and carry most of the
   value.
2. **Implement Layer 1 as a wrapper before you implement hooks.** A tiny `wmapi` script that always
   sets the User-Agent and honors 429 `Retry-After` gives you the same guarantee on any harness,
   including ones with no hook API — you just have to tell the model (in `CLAUDE.md` / `AGENTS.md`)
   to use it.
3. **Put Layer 2 behind MCP** if you want tools. An MCP server is the lowest-common-denominator way
   to expose `wikidata_vector_search`-style callables to Claude Code, OpenCode, and others.
4. **Treat the mechanism names above as orientation, not specification** — harness APIs move fast.
   Verify against each project's current documentation before implementing.

## Coverage map (illustrative, not an inventory)

This is a sample of how skill *profiles* map to layers, not a complete list — the repository now
carries **61 skills**, most of which post-date this analysis. Use it to classify a skill you are
considering upgrading.

### Cross-cutting (event hooks only — no custom tool needed)

| Skill | Hook | What it does | Status |
|---|---|---|---|
| wikimedia-api-access | `tool_call` | Auto-inject User-Agent on curl/python commands hitting Wikimedia | ✅ |
| wikimedia-database | `tool_call` | Pre-flight SSH tunnel check + connection params before SQL | ⬜ |
| wikimedia-toolforge | `tool_call` | Auto-inject `become <toolname>` before Kubernetes/SSH commands | ⬜ |

### Action-oriented (custom tool + retained SKILL.md)

| Skill | Tool Name | Skill retained for | Status |
|---|---|---|---|
| wikidata-vector-search | `wikidata_vector_search` | API reference, edge cases, reranker docs | ✅ |
| wikimedia-ml-services | `wikimedia_score_quality` | Model names, ORES vs Lift Wing differences | ⬜ |
| wikimedia-pageviews | `wikimedia_pageviews` | SQL property approach, date format warnings | ⬜ |
| wikimedia-page-assessment | `wikimedia_page_assessment` | Full schema, advanced query patterns | ⬜ |
| wikimedia-diffs | `wikimedia_fetch_diff` | Diff parsing details, BeautifulSoup reference | ⬜ |
| wikimedia-commons | `wikimedia_commons_search` | Licensing guidance, namespace reference | ⬜ |
| wikimedia-database | `wikimedia_database_query` | Connection setup, guardrails, shard names | ⬜ |
| wikidata | `wikidata_entity_lookup` | Full SPARQL patterns, taxonomy docs | ⬜ |
| wikimedia-eventstreams | `wikimedia_eventstreams_subscribe` | Schema reference, client library catalog | ⬜ |
| wikimedia-wikitext | `wikimedia_parse_wikitext` | mwparserfromhell reference, edge-case tables | ⬜ |
| wikipedia-citations | `wikipedia_citation_lookup` | CS1/CS2 parameter reference, maintenance templates | ⬜ |

### Knowledge-only (skills only — no hook or tool warranted)

| Skill | Reason |
|---|---|
| wikipedia-en-biography-writing | Creative task — NPOV/BLP judgment, not a single API call |
| wikipedia-en-article-audit | Multi-step pipeline — 6 diagnoses, produces a task graph |
| wikipedia-page-anatomy | Pure reference — structural knowledge, no action |
| wikipedia-templates | Pure reference + creative — syntax/parser functions plus template design judgment |
| wikipedia-talk-page | Pure reference — discussion conventions, archiving |
| wikipedia-edit-history | Reference + creative — edit interpretation, not just data fetching |
| pywikibot | Full library reference — 50+ scripts, bot class hierarchy |

## Still open

1. **Remaining Layer 1 hooks** — SSH tunnel health check before SQL; Toolforge `become` injection.
   (User-Agent injection and curl/wget retry flags are done.)
2. **Remaining Layer 2 tools** — the other six tools in the table above; the top five after vector
   search (page quality, pageviews, page assessment, diff fetch, Commons search) would cover most
   data needs.
3. **Keyword auto-activation (`before_agent_start`)** — detect domain keywords in the user prompt
   and inject 2–5 bullets from the matching skill:

   | Keyword matches | Inject from skill |
   |---|---|
   | "wikidata", "SPARQL", "QID", "entity" | wikidata (endpoint URL, QID-first rule) |
   | "page view", "traffic", "popularity" | wikimedia-pageviews (date format warning) |
   | "article quality", "FA", "GA", "rating" | wikimedia-page-assessment (schema reminder) |
   | "diff", "revision", "change", "edit" | wikimedia-diffs (API endpoints) |
   | "template", "infobox", "parser function", "magic word", "Lua module", "#invoke" | wikipedia-templates (syntax quick-ref) |
   | "citation", "reference", "cite", "source" | wikipedia-citations (template param reminder) |
   | "commons", "image", "media", "upload" | wikimedia-commons (license policy) |

4. **Event-driven orchestration** — e.g. a hook notices a SPARQL call, auto-resolves labels via the
   vector-search tool, and returns QIDs *and* human-readable labels without the model asking.

## Comparison: skills-only vs. three layers

| Dimension | Skills only (baseline) | With hooks + tools | Status |
|---|---|---|---|
| User-Agent compliance | Model must read the skill and remember | Hook injects automatically | ✅ shipped |
| Rate-limit handling | Model must notice 429 and follow retry logic | Hook injects retry flags / backoff | ◐ partial |
| Vector search | Model reads curl examples, builds the URL | One typed tool call | ✅ shipped |
| Page quality / pageviews / diffs | Model writes SQL or URL by hand | One tool call each | ⬜ open |
| SPARQL query patterns | Full reference in SKILL.md | Reference retained, optionally auto-injected | ✅ skills |
| Serendipitous discovery | YAML descriptions visible | No change | ✅ skills |
| Cross-skill workflows | Model must load and combine skills | Hooks can orchestrate across tools | ⬜ open |
| Cold start (no prior knowledge) | Model must `read` to learn anything | Hooks fire immediately; tools are listed | ◐ partial |
| Novel/unanticipated pattern | Skill instructions cover it | Falls through to the skill layer | ✅ skills |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Hooks don't fire because the model took an unanticipated path | Layer 3 remains as fallback; the hook is best-effort, the skill is the catch-all |
| Custom tools clutter the tool list | Keep descriptions concise, group by category, use `promptGuidelines` sparingly |
| `before_agent_start` injects too much text | 2–5 bullets maximum; full detail stays in the skill file |
| Extension breaks on a harness upgrade | Pin the SDK version; re-test after `/reload`; keep the extension free of pi-only imports where practical |
| Model ignores a custom tool and hand-rolls a solution | Acceptable — the hand-rolled path still hits the Layer 1 hooks, and the skill reference remains |
| **Harness API drift** (this document describing an API that moved) | Treat pi call signatures as reference implementation, not specification; the portability table is deliberately mechanism-level |
| **This document drifting from reality** | The status banner and the [As-built](#as-built-what-exists-today) table name concrete files; update them in the same PR that changes the extension |

## References

- `.pi/extensions/wikimedia-skills/` — `index.ts`, `core.ts`, `tools/vector-search.ts`, `config.json`, `test-core.mjs`
- [README → Pi agent setup](README.md#pi-agent-setup) — installation and User-Agent configuration
- [`docs/design-philosophy.md`](docs/design-philosophy.md) — skill tiers, sizing, and the candidacy filter
- Harness documentation for your own harness (pi extensions, Claude Code hooks/MCP, OpenCode plugins)
