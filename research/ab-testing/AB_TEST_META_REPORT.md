# Wikipedia AI Skills — A/B Test: Complete Meta-Report

**Conclusive findings from 24 agent runs across 12 tasks, 3 rounds**
**Date:** 2026-06-09
**Context:** These A/B tests were run on an early version of the skills (roughly
25-30 skills existed at the time, using Claude Code as the agent harness). The
findings were instrumental in validating the skill structure and guiding
subsequent enhancements. As of June 2026, the repo has grown to 45 skills and
switched to Pi as the primary agent harness. Some specific findings may not apply
to the current skill set, but the methodology and lessons learned remain relevant.

---

## 1. Methodology

**24 parallel agent runs** (12 tasks × 2 variants each) using the `worker` subagent:

| Variant | Label | Skill Injection | Knowledge Source |
|---------|:-----:|:---------------:|:-----------------|
| **A** | With Skills | ✅ Relevant skills from the Wikipedia AI Skills repo loaded into context | Documented API endpoints, response formats, domain conventions, code examples |
| **B** | No Skills | ❌ `skill: false` — no skill injection | General knowledge, API design conventions, prior experience, trial-and-error |

Tasks escalated in complexity across 3 rounds:

| Round | Focus | Tasks | Avg APIs Per Task |
|:-----:|-------|:-----:|:-----------------:|
| **1** | Simple single-API calls | Pageviews, SPARQL, Revisions, Category listing | 1 |
| **2** | Multi-step workflows | Content gaps, Patrol monitor, Citation×Quality, Structural audit | 3-4 |
| **3** | Cross-domain deep orchestration | Pywikibot framework, Commons×Wikidata×Wikipedia, Cross-language ML, Real-time SSE+ML+Diffs | 4-5 |

---

## 2. Aggregate Results

### 2.1 Speed

| Round | Avg With Skills | Avg Without Skills | Speedup |
|:-----:|:---------------:|:-----------------:|:-------:|
| **1** | ~2.5 min | ~5.5 min | **2.2×** |
| **2** | ~7 min | ~19 min | **2.7×** |
| **3** | ~7 min | ~22 min | **3.1×** |
| **Overall** | **~5.5 min** | **~15.5 min** | **2.8×** |

The speed advantage grows with complexity, peaking at **9.0×** for the Pywikibot framework task (Task 9) where a v11.3 API rename would otherwise consume 10+ minutes of debugging.

### 2.2 Correctness

| Round | With Skills | Without Skills | No-Skills Failure Rate |
|:-----:|:-----------:|:--------------:|:----------------------:|
| **1** | ✅ 4/4 correct | ⚠️ 3/4 correct, 1 silent failure | **25%** |
| **2** | ✅ 4/4 correct | ⚠️ 2/4 correct, 2 silent failures | **50%** |
| **3** | ✅ 4/4 correct | ⚠️ 1/4 correct, 3 with major gaps | **75%** |
| **All** | **✅ 12/12 correct** | **⚠️ 6/12 with hidden errors** | **50%** |

The skills variant produced **zero** incorrect or misleading outputs across all 12 tasks. The no-skills variant produced plausible-looking wrong answers in **half** of all tasks.

### 2.3 What the 6 No-Skills Failures Looked Like

| Task | The Error | Why It Passed Casual Inspection |
|------|-----------|:--------------------------------|
| **R1T1** — Pageviews | Counted 29 days instead of 30 (missed 48h data lag) | Output looked complete — who counts days? |
| **R2T5** — Content gaps | Only got 25 articles instead of 100 (missed recursive subcategories) | Ranked table looked correct, just smaller |
| **R2T8** — Structural audit | Reported 0 navboxes (should be 2+), flagged 5 false empty sections | Health report looked professional with wrong numbers |
| **R3T11** — Cross-language | Substituted length-based "FA-like" labels for actual ML quality scores | Table had a quality column — no indication it was fabricated |
| **R3T12** — Vandalism patterns | No canary filtering, broken diff parsing, 3% throughput | Report had real-looking stats but they were corrupted |

**Common thread:** All 6 failures produced output that looked correct to a non-expert reader. No error messages, no warning signs. Just wrong numbers.

---

## 3. The Four Types of Knowledge Skills Provide

Across all 12 tasks, skills provided value in four distinct categories. Understanding these categories explains *why* and *when* skills matter.

### Type A: Framework/API Knowledge ⭐⭐⭐⭐⭐ Critical

**What it is:** Exact API endpoint URLs, parameter names, method signatures, response formats — things you must get exactly right or the request fails.

**Examples where it mattered:**
- Pywikibot `CategorizedPageGenerator` vs deprecated `CategoryPageGenerator` (Task 9)
- Lift Wing ML ORES-compatible nested response envelope (Tasks 11, 12)
- Pageviews REST API path segment order (Tasks 1, 5, 10, 11)
- `action=compare` with `fromrev`/`torev` parameters (Task 12)

**Without skills:** The agent must guess, probe, debug, retry. Each wrong guess costs 1-5 minutes. Some response formats (like the Lift Wing ORES envelope) are essentially undiscoverable without documentation — `data["enwiki"]["scores"][str(revid)]["articlequality"]["score"]["prediction"]` is not something you'd guess.

### Type B: Data Model Knowledge ⭐⭐⭐⭐ High

**What it is:** Q-numbers, P-numbers, namespace IDs, property codes — semantic identifiers that encode domain meaning.

**Examples where it mattered:**
- P18 = image property, P166 = award received, P569 = date of birth (Tasks 2, 5, 10, 11)
- Q38104 = Nobel Prize in Physics, Q5 = human, Q95074 = fictional character (Task 2)
- `srnamespace=6` = File namespace on Commons (Task 10)
- `cmnamespace=0` = main namespace (Tasks 4, 5, 7, 10)

**Without skills:** The agent must recall from memory or discover through search. The "well-known" P-numbers (P31, P166) are often correct from general knowledge. The obscure ones (P18, P569) are hit-or-miss.

### Type C: Domain Conventions ⭐⭐⭐⭐ High

**What it is:** Wikipedia editorial conventions, community norms, cultural practices — things that aren't documented in API reference pages.

**Examples where it mattered:**
- Navboxes have diverse names (`{{Portal}}`, `{{Authority control}}`) — not just `{{Navbox}}` (Task 8)
- References/Notes/Further reading sections contain only template calls — not "empty" (Task 8)
- ~48h data lag on pageviews API (Task 1)
- Canary events must be filtered from EventStreams (Task 12)
- Category:Physics content is distributed across subcategories (Task 5)

**Without skills:** The agent either doesn't know about the convention (producing wrong output) or discovers it through trial and error. Canary events and the 48h data lag were simply missed by the no-skills variants.

### Type D: Code Patterns ⭐⭐⭐ Medium

**What it is:** Ready-to-copy code snippets, function signatures, boilerplate patterns.

**Examples where it mattered:**
- Complete Python function for `get_historical_views()` (Task 1)
- `mwparserfromhell` template extraction patterns (Tasks 7, 8, 9)
- Batch QID resolution via `prop=pageprops&ppprop=wikibase_item` (Task 5)
- User-Agent header format (all tasks)

**Without skills:** The agent writes equivalent code from scratch. Usually works, but takes longer and may miss edge cases (e.g., the 48h data lag fallback that the skills variant's copypasted code already included).

---

## 4. The Complexity-Correctness Curve

```
Correctness of no-skills agent as task complexity increases:

100% │ Simple APIs
     │  ┌─ 3/4 correct
 75% │  │
     │  │     Multi-step workflows
 50% │  │     ┌─ 2/4 correct  
     │  │     │
 25% │  │     │     Deep cross-domain
     │  │     │     ┌─ 1/4 correct
  0% │──┴─────┴─────┴──
     │  R1     R2     R3
     │  (simple)  (moderate)  (complex)
```

The skills variant stays at **100%** across all 3 rounds. The no-skills variant declines linearly with complexity.

**Why:** Simple tasks require only Type A knowledge (API endpoints), which agents can often guess. Complex tasks require Types A+B+C+D simultaneously — and a single missing piece (canary filtering, ORES envelope format, recursive category traversal) produces a silent failure.

---

## 5. The "Well-Known API Floor"

Some tasks showed minimal skills advantage because the APIs involved are widely known:

| Task | Speedup | Why the Floor Held |
|:----:|:-------:|:-------------------|
| **R1T3** — Revisions | 2.0× | MediaWiki Action API is exceptionally well-documented and logically structured |
| **R3T10** — Commons Checker | 1.7× | Commons search (`srnamespace=6`) and Wikidata P18 are well-known patterns |

In these cases, both variants produced functionally identical output. Skills still provided a speed advantage (1.7-2.0×) but no correctness gap.

**Implication:** Skills are most valuable for obscure, internal, or recently-changed APIs — not for well-known public ones. Prioritize skill development for:
- Internal WMF conventions (canary events, namespace IDs)
- Complex response formats (Lift Wing ORES envelope)
- Framework-specific knowledge (Pywikibot API changes)
- Domain conventions (navbox patterns, empty section rules)

---

## 6. The No-Skills Survival Pattern (Defensive Programming)

The no-skills agents consistently showed a compensatory behavior: **they built more defensive code because they were less certain of correctness.**

| Behavior | Observed In | What They Did |
|----------|:-----------:|:---------------|
| **Pre-flight validation** | Task 3 | Ran `curl` first to validate API parameters before writing the full script |
| **Rate-limit handling** | Task 2 | Added exponential backoff for 429s (skills variant didn't — and was luckier) |
| **Stdlib over dependencies** | Task 4 | Used `urllib.request` instead of `requests` (zero external dependencies) |
| **Conservative batching** | Task 5 | Used 50-at-a-time SPARQL batches with 1s delays (skills variant used 100-at-a-time) |
| **Heuristic fallbacks** | Tasks 11, 12 | Approximated quality from length, accepted incomplete diff parsing |

**This is a double-edged sword.** Defensive code is more robust but slower and produces outputs with silent quality degradation (e.g., substituting length-based quality labels for real ML scores).

---

## 7. Skills Documentation Gaps Discovered

Through the testing, several gaps were identified where **both** variants struggled or where the skills documentation was incomplete:

| Gap | Relevant Skill | Impact |
|-----|---------------|--------|
| `revertrisk-language-agnostic` returns HTTP 422 for revision 1 (new pages have no parent revision) | `wikimedia-ml-services` | Both variants discovered this by trial and error |
| `articlequality` model has ~60s processing latency for brand-new revisions | `wikimedia-ml-services` | New page quality scores are unavailable for ~60s after creation |
| No explicit SPARQL example for checking sitelinks via `schema:about`/`schema:isPartOf` | `wikidata` | Skills variant had to debug the query once |
| Canary event filtering (`meta.domain == 'canary'`) is referenced but could be more prominent | `wikimedia-eventstreams` | No-skills variant had no way to know about this |
| Pywikibot v11.3 `CategorizedPageGenerator` vs deprecated `CategoryPageGenerator` | `pywikibot` | Cost 10 minutes of framework probing for no-skills variant |

**Recommendation:** These gaps should be documented in their respective skills. A "Known Limitations" section in each skill would help future agents avoid rediscovering these edge cases.

---

## 8. Recommendations

### For Skill Authors

1. **Add "Known Limitations" sections** — Document API behaviors that cause errors or data gaps (422 for new pages, 60s ML latency, 48h data lag, canary events). These are the most valuable things to document because they're invisible until you hit them.

2. **Prioritize framework-specific knowledge** — Pywikibot API changes (Task 9, 9.0× speedup) are the highest-value documentation targets because they're impossible to guess and cause maximum debugging time.

3. **Add quick-reference decision tables** — The `wikipedia-categories` skill's "I want to..." → "Use this API" table was the most effective format observed. It reduced time-to-solution to near-zero for category-related tasks.

4. **Cross-reference between skills** — The pattern of `wikimedia-api-access` being referenced from every other skill works well. Extend this: `wikidata` could reference `wikimedia-ml-services` for quality scoring, `wikimedia-eventstreams` could reference `wikimedia-diffs` for downstream analysis.

### For Agents Using Skills

5. **Skills don't eliminate the need for defensive programming** — The skills variant sometimes got lucky (no 429s on tasks where the no-skills variant hit rate limits). Always include exponential backoff and error handling regardless of skill availability.

6. **Be aware of skill documentation lag** — Skills document what was known at the time of writing. Framework changes (Pywikibot v11.3 renames) or new API versions may not be reflected. Cross-check with live probing for critical parameters.

7. **Use skills for Type B+C knowledge, not just Type A** — The most valuable skills insights aren't API URLs (which are often guessable) but domain conventions and data model identifiers that have no discoverable structure.

### For Tool Builders

8. **The 50% silent-failure baseline is the strongest argument for skills** — If you're building an automated Wikipedia tool, the choice is not "skills vs. speed." It's "skills vs. wrong answers." The 2.8× speedup is a bonus; the correctness guarantee is the product.

9. **Skills alone aren't enough** — Even with skills, the agent needed to combine knowledge across them. A system that loads all relevant skills simultaneously outperforms one that loads them individually. The subagent skill-injection mechanism (loading multiple comma-separated skills) was essential for multi-step tasks.

---

## 9. Conclusion

**Skills provide a 2.8× average speedup and, more importantly, reduce the silent failure rate from 50% to 0% across Wikipedia automation tasks of varying complexity.**

The advantage is not uniform — it scales with task complexity:
- **Simple tasks** (1 API call): 2.2× faster, same correctness floor
- **Moderate tasks** (3-4 APIs): 2.7× faster, prevents 50% of hidden errors
- **Deep tasks** (cross-domain, real-time, frameworks): 3.1× faster, prevents 75% of hidden errors

The most valuable skill content is not API endpoints (which are often guessable) but **internal conventions, framework-specific knowledge, complex response format documentation, and domain conventions** — knowledge that cannot be inferred from API design alone and that, when missing, produces plausible-looking wrong answers rather than error messages.

**Final verdict:** For any production use of AI coding agents on Wikipedia tasks, loading the relevant skills is strongly recommended. The speed advantage is meaningful; the correctness guarantee is decisive.

---

## Appendix: Round 4 Proposal — Four Untested Dimensions

The three completed rounds covered 12 A/B comparisons across reading, multi-step orchestration, real-time streams, ML inference, and cross-project analysis. However, several major dimensions of Wikipedia automation remain entirely untested. This appendix documents four proposed Round 4 tasks, the skills they would exercise, and why each would provide new insight into skills effectiveness.

### Untested Dimensions Map

| Dimension | R1 | R2 | R3 | R4 Proposed | Why It Would Add New Insight |
|-----------|:--:|:--:|:--:|:------------|:-----------------------------|
| **Reading data** | ✅ | ✅ | ✅ | — | Exhausted across 12 tasks |
| **Writing/editing** | ❌ | ❌ | ❌ | **Task 13** | Tests authentication, BLP compliance, edit summaries, community norms — fundamentally different from read-only |
| **SQL database queries** | ❌ | ❌ | ❌ | **Task 14** | Tests SSH tunnel setup, SQL JOINs, aggregations — a completely different data access paradigm from REST APIs |
| **Multi-agent coordination** | ❌ | ❌ | ❌ | **Task 15** | Tests whether skills compound across agent chains (scout → planner → worker → reviewer) or whether each agent needs individual skill injection |
| **Long-running stateful tasks** | ❌ | ❌ | ❌ | **Task 16** | Tests state management, reconnection, memory handling, periodic reporting — dimensions invisible in <2min runs |
| Real-time streams | ✅ | ✅ | ✅ | — | Covered in Tasks 6, 12 |
| Cross-project reads | — | ✅ | ✅ | — | Covered in Tasks 5, 10, 11 |
| Framework usage | — | — | ✅ | — | Covered in Task 9 (Pywikibot) |
| ML inference | — | ✅ | ✅ | — | Covered in Tasks 6, 7, 11, 12 |

---

### Task 13 — Writing: Draft a Complete Article (Read→Write Transition)

**Skills:** `wikipedia-en-biography-writing`, `wikipedia-citations`, `wikipedia-templates`, `wikipedia-page-anatomy`, `pywikibot`

**What it tests:** The full article creation workflow — research, drafting, structural formatting, citation placement, category assignment, infobox construction, edit summary conventions, and BLP compliance. This is the most consequential untested dimension because **writing is fundamentally different from reading**:

- Authentication and bot credentials (how to obtain and use them)
- Edit conflict detection and resolution
- Policy compliance (BLP, NPOV, verifiability)
- Edit summary conventions (`/* Section */ description`)
- Preview vs. save patterns to avoid breaking the wiki
- Community norms around article creation (notability, sources, disambiguation)

**Why skills would matter:** The `wikipedia-en-biography-writing` skill covers BLP policy, NPOV framing, and structural conventions that are invisible to an agent without it. The no-skills variant would need to infer Wikipedia's biographical article standards from general knowledge — likely producing structurally correct wikitext that violates community policies in subtle ways.

**Proposed task:** Draft a stub article for a notable topic, writing to a local `.wikitext` file only (dry run). The output is evaluated on: structural correctness (infobox, lead, sections), citation quality (CS1 templates with proper parameters), category appropriateness, and policy compliance (neutral tone, verifiable claims, no original research).

**Hypothesis:** The skills variant produces a structurally complete, policy-compliant draft. The no-skills variant produces a draft that *looks* correct (valid wikitext, plausible sections) but has subtle policy violations (NPOV language, missing citations on factual claims, incorrect infobox parameters).

---

### Task 14 — Database: Analytics via Toolforge SQL (API → SQL Paradigm Shift)

**Skills:** `wikimedia-database`, `wikimedia-pageviews`

**What it tests:** The SQL database replicas are a fundamentally different data access paradigm from the REST/Action APIs. Instead of making N API calls for N pages, you write a single SQL query with JOINs and aggregations. This requires:

- SSH tunnel setup to Toolforge (`ssh -L` or `sshtunnel`)
- Database selection (`enwiki_p` for English Wikipedia)
- Table schema knowledge (`page`, `revision`, `page_props`, `page_assessments`)
- SQL query construction with JOINs, window functions, and aggregations
- Result pagination for large datasets
- Connection lifecycle management (open, query, close)

**Why skills would matter:** The `wikimedia-database` skill documents the exact SSH tunnel command, connection string format, table schemas with column types, and query patterns. Without it, the agent would need to guess the database hostname (`enwiki.analytics.db.svc.wikimedia.cloud`), port, credentials location, table names, and schema. This is **impossible to infer from API design** — SQL databases don't have discoverable schemas over the wire.

**Proposed task:** Find the top 20 articles in Category:Physics with the highest pageviews but lowest WikiProject assessment quality scores. Requires: SSH tunnel → `page` JOIN `page_props` JOIN `page_assessments` → `WHERE` quality IN ('Stub', 'Start') → `ORDER BY` pageviews DESC. The no-skills variant must instead use the Action API to fetch category members, then individual API calls for pageviews and assessments — a much slower process.

**Hypothesis:** The skills variant produces the result in a single SQL query (<5 seconds). The no-skills variant uses 40+ individual API calls, takes 2-5 minutes, and may hit rate limits. The speed gap (SQL vs. API) is expected to be the largest of any task — potentially **100× or more**.

**Caveat:** Requires active Toolforge credentials and SSH keys loaded into `ssh-agent`. If unavailable, a substitute task could compare SQL vs. API approaches by simulating the SQL query and counting API calls required.

---

### Task 15 — Multi-Agent: Coordinated Article Improvement Pipeline (Single Agent → Agent Chain)

**Skills:** Using pi's subagent system with chain mode — each agent in the chain brings different specialized skills

**What it tests:** Previous rounds used a single agent that loaded multiple skills. This task tests whether skills **compound across agent handoffs** — does a `scout` agent analyzing an article pass useful context to a `planner` and then to a `worker` and `reviewer`? Or does each agent need its own isolated skill injection?

This tests:
- Knowledge propagation across agent boundaries
- Whether the `{previous}` template variable preserves skill-derived context
- Whether different agent types (analyzer vs. implementer vs. reviewer) benefit from different skills
- Failure modes: what happens when an upstream agent makes an error and passes incorrect context downstream

**Why skills would matter:** A multi-agent pipeline is how real-world Wikipedia automation would work at scale. The `oracle` agent (context preservation) and `reviewer` agent (validation) have built-in patterns that may interact with skill injection differently from the `worker` agent used in all 12 previous tests.

**Proposed task:** Run a chain on pi's subagent system:
1. `scout` — analyze a Wikipedia article for issues (load: `wikipedia-page-anatomy`, `wikipedia-templates`)
2. `planner` — design fixes based on scout's report (load: `wikipedia-citations`, `wikipedia-categories`)
3. `worker` — implement the most important fix as a local file diff (load: `pywikibot`, `wikimedia-wikitext`)
4. `reviewer` — validate the proposed changes (load: `wikipedia-en-article-audit`)

The A/B test compares a chain where each agent loads its relevant skills vs. a chain where no skills are loaded at any stage.

**Hypothesis:** The skills chain propagates increasingly refined context — each agent builds on the last, producing a coherent end-to-end result. The no-skills chain degrades at each step — the scout produces shallow analysis, the planner designs generic fixes, the worker implements them incorrectly, and the reviewer misses the errors. This would reveal whether skills are *additive* (each agent benefits independently) or *multiplicative* (each agent's output quality compounds downstream).

---

### Task 16 — Long-Running: 10-Minute Edit Trend Analysis (Short → Extended Duration)

**Skills:** `wikimedia-eventstreams`, `wikimedia-ml-services`, `wikimedia-diffs`

**What it tests:** Previous real-time tasks (Tasks 6, 12) ran for 30-90 seconds. Extending to 10 minutes tests:

- **SSE reconnection handling:** EventStreams has a 15-minute idle timeout. A 10-minute window may trigger at least one reconnection cycle.
- **State accumulation:** Running counts, rolling windows, periodic snapshots without memory leaks.
- **Periodic reporting:** Log summaries every 2 minutes showing edit rate, revert risk distribution, and trend direction.
- **Graceful shutdown:** Handling SIGINT/SIGTERM to produce a final report rather than dropping data.
- **Data volume:** At ~2-3 edits/second on enwiki, a 10-minute window produces ~1200-1800 events. Memory management for 1800 ML API responses.
- **Rate limiting under sustained load:** 1800 revert-risk API calls in 10 minutes = 3 calls/second. May hit Lift Wing rate limits.

**Why skills would matter:** The `wikimedia-eventstreams` skill documents the 15-minute timeout, reconnection patterns, and backoff strategy. Without it, the agent's connection would silently drop after 15 minutes with no recovery. The `wikimedia-ml-services` skill documents rate limiting patterns that become critical under sustained 3 req/s load.

**Proposed task:** Run the vandalism pattern analysis pipeline from Task 12 for **10 minutes** (vs. 90s in the original test). Track: total edits, high-risk percentage (calculated every 2 minutes), trend direction (is the rate of high-risk edits increasing or decreasing?), top editors by risk score, and namespace breakdown of risky edits.

**Hypothesis:** Both variants produce similar results for the first 2 minutes. From 2-10 minutes, the skills variant continues to produce accurate, structured output while the no-skills variant degrades — hitting rate limits, accumulating unbounded state, or dropping the SSE connection without recovery.

---

### Expected Findings Summary

| Task | New Dimension | Core Skill Value | Expected Speedup | Expected Failure Mode (No Skills) |
|:----:|:--------------|:-----------------|:----------------:|:----------------------------------|
| **13** | Write/Edit | Policy compliance, structural conventions | ~3× | Subtle BLP/NPOV violations in the draft that look correct at first glance |
| **14** | SQL Database | SSH tunnel setup, table schemas, query patterns | **~100×** | Cannot complete — no way to infer database hostname and schema from API knowledge |
| **15** | Multi-Agent | Cumulative context across agent chain | ~2-3× | Chain degradation: each step loses fidelity, final output is incoherent |
| **16** | Long-Running | Reconnection handling, rate limiting, state management | ~2× | Connection drops, rate limits hit, unbounded memory growth |

### Recommendation

If only one Round 4 task is feasible, **Task 15 (Multi-Agent)** would provide the most new insight because it tests an architectural dimension (agent chaining) that interacts with skills in complex, non-obvious ways. The question of whether skills are *additive* or *multiplicative* across agent handoffs is directly relevant to how the skills repo should be structured for production use.

If two tasks are feasible, **Task 13 (Writing)** adds the read→write transition and **Task 15 (Multi-Agent)** adds the orchestration dimension — together they cover the two largest untested areas.

Task 14 (SQL Database) has the highest expected speedup (~100×) but requires Toolforge credentials. Task 16 (Long-Running) has the lowest expected speedup (~2×) because both variants would struggle with extended runtime issues that skills partially but not completely address.
