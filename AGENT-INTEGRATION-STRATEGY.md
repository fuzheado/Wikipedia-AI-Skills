# Agent Integration Strategy

> **Status:** Analysis & planning — not yet implemented.
>
> This document explores how to evolve these SKILL.md files from passive
> markdown (progressive disclosure, LLM-decides-to-read) into a layered
> architecture with deterministic event hooks, callable custom tools, and
> retained skill descriptions for serendipitous discovery.

## Motivation

The current skill model works well: each skill's YAML front-matter description
is always in the system prompt, and the LLM can `read` the full SKILL.md when
it judges the task is relevant. This gives **broad coverage** and
**serendipity** — the LLM might discover a skill it didn't know it needed.

However, this model has known failure modes:

| Failure Mode | Example |
|---|---|
| LLM ignores a description even when relevant | Sees `wikimedia-api-access` but doesn't read it → 403 from missing User-Agent |
| LLM skims instructions and misses a detail | Reads the SPARQL endpoint guide but uses wrong URL format |
| Cross-cutting boilerplate must be re-learned every session | Rate limiting, User-Agent, connection reuse |
| Multiple skills interact; LLM loads only one | Runs SPARQL with Wikidata skill but forgets User-Agent from the other |
| LLM uses an unexpected approach that bypasses skill coverage | Uses `python requests` instead of `curl` → hook misses it |

The solution is a **three-layer architecture** that covers each other's
failure modes.

## The Three-Layer Architecture

```
┌──────────────────────────────────────────────────┐
│              Layer 1: Event Hooks                 │
│  pi.on("tool_call", ...)                          │
│  pi.on("before_agent_start", ...)                 │
│                                                   │
│  Invisible to the LLM — runs in the background.   │
│  Enforces policy, injects boilerplate, applies    │
│  guardrails automatically on every relevant event. │
│  Reliability: near 100% when event pattern matches │
│  Blind spot: any event pattern you didn't code for │
├──────────────────────────────────────────────────┤
│              Layer 2: Custom Tools                 │
│  pi.registerTool({ name, description, execute })  │
│                                                   │
│  Visible in the Available tools list — the LLM    │
│  sees them and can call them like functions.       │
│  Deterministic execution when called.              │
│  Best for: frequent, well-defined, repeatable      │
│  actions (vector search, ML scoring, DB queries).  │
│  Reliability: near 100% when the LLM calls the tool│
│  Blind spot: LLM might not think to call it        │
├──────────────────────────────────────────────────┤
│              Layer 3: Skills (SKILL.md)            │
│                                                   │
│  YAML description always in system prompt.        │
│  Full instructions loaded on-demand via `read`.   │
│  Best for: knowledge-heavy reference, creative    │
│  tasks, infrequent workflows, serendipitous        │
│  discovery.                                        │
│  Reliability: depends on LLM judgment              │
│  Blind spot: LLM may skip or skim                  │
└──────────────────────────────────────────────────┘
```

## Layer Details

### Layer 1: Event Hooks (`pi.on()`)

These are pi extension event listeners that run automatically at specific
lifecycle points. The LLM **never sees them** — they are infrastructure.

**Recommended hook points:**

| Event | Purpose | Candidates from this repo |
|---|---|---|
| `tool_call` | Intercept bash/curl commands to auto-inject User-Agent headers, rate-limiting backoff, auth tokens | wikimedia-api-access, wikimedia-database, wikimedia-toolforge |
| `tool_result` | Post-process results — parse SPARQL JSON, format Wikidata entity output, detect 403/429 errors | wikidata, wikimedia-api-access |
| `before_agent_start` | Inspect user prompt for keywords and inject relevant skill instructions directly into the system prompt | All skills — keyword-based auto-activation |
| `context` | Filter or augment messages before each LLM call — inject recent query results as context | wikidata-vector-search (inject item labels) |

**Example — User-Agent enforcement via `tool_call`:**

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

**What it covers:** Every `bash` tool call, every `curl`, every Python HTTP
request — automatically, without the LLM remembering to load the skill.

**What it misses:** Anything the LLM does via a custom tool, via the browser,
via `wget`, via a Node.js `fetch()`, or via any tool invocation that doesn't
match your pattern. This is the blind spot of event hooks — they are only as
broad as the patterns you anticipated.

**Recommendation:** Use event hooks only for:
- Policies that must **never** be violated (User-Agent, read-only database guard)
- Boilerplate that is tedious for the LLM to re-invoke each session
- Auth token injection (Toolforge, database SSH tunnel)

---

### Layer 2: Custom Tools (`pi.registerTool()`)

These are TypeScript functions registered as callable tools. The LLM sees them
in the `Available tools` section of the system prompt, alongside `bash`,
`read`, `write`, and `edit`. When the LLM calls them, execution is
deterministic — no "did it follow the instructions correctly" overhead.

**Best candidates from this repo** (frequent, well-defined, repeatable actions):

| Skill | Tool Name | Why |
|---|---|---|
| wikidata-vector-search | `wikidata_vector_search` | Single API call — search by meaning → return QIDs |
| wikimedia-ml-services | `wikimedia_score_quality` | Predict article quality with fixed parameters |
| wikimedia-pageviews | `wikimedia_pageviews` | Simple REST API with numeric result |
| wikimedia-page-assessment | `wikimedia_page_assessment` | Look up FA/GA/B/C rating by page title |
| wikimedia-database | `wikimedia_database_query` | Common SQL lookups with safe parameter binding |
| wikimedia-diffs | `wikimedia_fetch_diff` | Compare two revisions by ID |
| wikimedia-commons | `wikimedia_commons_search` | Search Commons files by keyword |

**Example — vector search as a callable tool:**

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
      language: Type.Optional(
        Type.String({ description: "Language code (default: en)" })
      ),
      limit: Type.Optional(
        Type.Integer({ description: "Max results (default: 10)", minimum: 1, maximum: 50 })
      ),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      // Deterministic API call — no LLM judgment involved
      const url = new URL("https://wd-vectordb.wmcloud.org/search_items");
      url.searchParams.set("query", params.query);
      url.searchParams.set("top_k", String(params.limit ?? 10));
      if (params.language) url.searchParams.set("lang", params.language);

      const response = await fetch(url.toString(), {
        headers: {
          "User-Agent": "WikipediaAIAgent/1.0 (https://github.com/user; user@email.com) SkillsDemo",
          Accept: "application/json",
        },
        signal, // Respects Ctrl+C / abort
      });

      if (!response.ok) {
        return {
          content: [{ type: "text", text: `Vector search failed: HTTP ${response.status}` }],
          isError: true,
        };
      }

      const data = await response.json();
      return {
        content: [{ type: "text", text: JSON.stringify(data.results, null, 2) }],
      };
    },
  });
}
```

**What it covers:** The LLM sees `wikidata_vector_search` in its tool list.
It's one function call away. No `read`, no parsing curl examples, no
constructing URLs. Zero chance of URL typos, wrong headers, or misread
instructions.

**What it misses:** The LLM must decide to call it. If the LLM thinks "I'll
just query Wikidata directly with SPARQL" and never reaches for the tool,
the tool never fires. This is the same failure mode as skills, but the
bar is lower — calling a tool is simpler than reading a file and following
instructions.

**Recommendation:** Use custom tools for any skill whose core action is:
1. A single API call with fixed parameters
2. A database query with safe parameter binding
3. Any action you want to make "one-shot" for the LLM

Leave the SKILL.md in place as reference documentation — the tool handles the
90% case, the skill handles the 10% case where the LLM needs the full context.

---

### Layer 3: Skills (Retained as-is)

The existing SKILL.md files stay exactly where they are. They serve roles that
hooks and tools cannot:

| Role | Example |
|---|---|
| Reference documentation | Full SPARQL query patterns, all endpoint URL forms, parameter catalogs |
| Creative/nuanced tasks | Biography writing (NPOV/BLP guidance), article auditing (6-diagnosis pipeline) |
| Infrequent workflows | Toolforge Kubernetes job setup, Pywikibot bot authoring |
| Serendipitous discovery | LLM browses descriptions and finds a skill it didn't know existed |

**What they cover:** Everything hooks and tools miss. The long tail.

**What they miss:** The LLM must choose to `read` them. Same single point of
failure as always. But in the three-layer model, this is acceptable — the
skill is the *last resort* for the cases the other layers don't handle.

## Coverage Map

How each skill maps to the three layers:

### Cross-cutting (Event hooks only — no custom tool needed)

| Skill | Hook | What it does |
|---|---|---|
| wikimedia-api-access | `tool_call` | Auto-inject User-Agent on all curl/python commands hitting Wikimedia |
| wikimedia-database | `tool_call` | Auto-inject SSH tunnel check + connection params before SQL queries |
| wikimedia-toolforge | `tool_call` | Auto-inject `become <toolname>` before Kubernetes/SSH commands |

### Action-oriented (Custom tool + retained SKILL.md)

| Skill | Tool Name | Skill Retained For |
|---|---|---|
| wikidata-vector-search | `wikidata_vector_search` | API reference, edge cases, reranker docs |
| wikimedia-ml-services | `wikimedia_score_quality` | All model names, ORES vs Lift Wing differences |
| wikimedia-pageviews | `wikimedia_pageviews` | SQL property approach, date format warnings |
| wikimedia-page-assessment | `wikimedia_page_assessment` | Full schema, advanced query patterns |
| wikimedia-diffs | `wikimedia_fetch_diff` | Diff parsing details, BeautifulSoup reference |
| wikimedia-commons | `wikimedia_commons_search` | Licensing guidance, namespace reference |
| wikimedia-database | `wikimedia_database_query` | Connection setup, guardrails, shard names |
| wikidata | `wikidata_entity_lookup` | Full SPARQL patterns, taxonomy docs |
| wikimedia-eventstreams | `wikimedia_eventstreams_subscribe` | Schema reference, client library catalog |
| wikimedia-wikitext | `wikimedia_parse_wikitext` | mwparserfromhell reference, edge case tables |
| wikipedia-citations | `wikipedia_citation_lookup` | CS1/CS2 parameter reference, maintenance templates |

### Knowledge-only (Skills only — no hook or tool needed)

| Skill | Reason |
|---|---|
| wikipedia-en-biography-writing | Creative task — NPOV/BLP judgment, not a single API call |
| wikipedia-en-article-audit | Multi-step pipeline — 6 diagnoses, produces DAG |
| wikipedia-page-anatomy | Pure reference — no action, just structural knowledge |
| wikipedia-templates | Pure reference + creative — template syntax/parser functions/magic words reference, template design judgment |
| wikipedia-talk-page | Pure reference — discussion conventions, archiving |
| wikipedia-edit-history | Reference + creative — edit interpretation, not just data fetch |
| wikimedia-cdn-assets | Configuration reference — static CDN paths |
| pywikibot | Full library reference — 50+ scripts, bot class hierarchy |

## Implementation Path

### ✅ Phase 0: Foundation (one extension) — DONE

A single pi extension at `.pi/extensions/wikimedia-skills/index.ts` houses the
first event hook. The extension:

1. ✅ Registers the User-Agent enforcement event hook
2. ⬜ Registers custom tools (future)
3. ⬜ Uses `before_agent_start` for keyword-based auto-activation (future)

See the [README](../README.md#pi-agent-setup) for install instructions.

### ✅ Phase 1, Item 1: User-Agent enforcement — DONE

Creates a `pi.on("tool_call")` event hook that automatically injects a
descriptive `User-Agent` header into every `curl`, `wget`, `python`, and
`node` bash command targeting a Wikimedia domain (`*.wikipedia.org`,
`*.wikidata.org`, `*.wikimedia.org`, `*.wmcloud.org`, `*.toolforge.org`).

- Ships with a placeholder UA that users replace via `~/.config/wikimedia-skills/config.json` or `WIKIMEDIA_USER_AGENT` env var
- UI: no-op skip injected if UA already present
  - Configurable per-tool type (curl, wget, python, node) via `config.json`
  - Users config survived `git pull` by placing config in `~/.config/`
  - 36 node --test unit tests + 17 pytest structure tests

### Remaining Phase 1 hooks

1. **Rate-limit backoff** (`tool_result` interceptor for 429) — auto-retry with
   exponential backoff
2. **SSH tunnel health check** (`tool_call` before SQL) — prevents "can't
   connect to database" failures

### Phase 2: Top 5 custom tools (highest frequency)

Implement tools for: vector search, page quality, pageviews, page assessment,
and diff fetch. These cover >80% of the LLM's likely Wikipedia data needs.

### Phase 3: Auto-activation by keyword

Wire `before_agent_start` to detect domain-specific keywords in the user
prompt and inject concise bullet-point instructions from the relevant skill:

| Keyword matches | Inject from skill |
|---|---|
| "wikidata", "SPARQL", "QID", "entity" | wikidata (endpoint URL, QID-first rule) |
| "page view", "traffic", "popularity" | wikimedia-pageviews (date format warning) |
| "article quality", "FA", "GA", "rating" | wikimedia-page-assessment (schema reminder) |
| "diff", "revision", "change", "edit" | wikimedia-diffs (API endpoints) |
| "template", "infobox", "parser function", "magic word", "Lua module", "#invoke" | wikipedia-templates (syntax quick-ref) |
| "citation", "reference", "cite", "source" | wikipedia-citations (template param reminder) |
| "commons", "image", "media", "upload" | wikimedia-commons (license policy) |

### Phase 4: Event-driven tool orchestration

For compound workflows, use event hooks to auto-call tools. Example:

- LLM runs a SPARQL query → hook detects SPARQL in the bash call
- Hook auto-calls `wikidata_vector_search` to resolve labels, injects them
  into the result
- LLM gets QID numbers *and* human-readable labels without thinking about it

## Comparison: Current vs. Three-Layer

| Dimension | Current (Skills Only) | With Three-Layer Architecture |
|---|---|---|
| User-Agent compliance | LLM must read skill and remember | Hook auto-injects — 100% reliable |
| Vector search | LLM reads curl examples, constructs URL manually | One tool call — deterministic, typed |
| Page quality lookup | LLM reads SQL patterns, constructs query | One tool call — no SQL needed |
| Rate limit handling | LLM must notice 429, find and follow retry logic | Hook auto-retries with backoff |
| SPARQL query patterns | Full reference in SKILL.md — LLM can read creatively | Skill retained — plus optional auto-injection |
| Serendipitous discovery | YAML descriptions visible → LLM may discover new skills | Retained — no change |
| Cross-skill workflows | LLM must load + combine multiple skills | Event hooks can orchestrate across tools |
| Cold start (no LLM knowledge) | LLM must `read` to learn anything | Hooks fire immediately, tools available immediately |
| Novel/unanticipated pattern | Skill covers it (broad instructions) | Falls through to skill layer — still covered |

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Hooks don't fire because LLM used an unanticipated approach | The skill layer still exists as a fallback; the LLM reads the description and adapts |
| Too many custom tools clutter the tool list | Group by category, keep descriptions concise, use `promptGuidelines` sparingly |
| Before_agent_start injects too much text | Keep injected text to 2-5 bullet points max; full details stay in the skill file |
| Extension breaks on pi version upgrade | Pin to specific pi SDK version, test on `/reload` |
| LLM ignores custom tool and crafts manual solution anyway | Acceptable — the manual solution will trigger the event hooks (User-Agent, rate limits) and the skill reference is still there |
