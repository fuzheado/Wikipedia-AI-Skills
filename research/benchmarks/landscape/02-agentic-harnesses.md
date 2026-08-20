# 02 — Agentic / tool-use LLM benchmarks and evaluation harnesses

*Research for a Wikimedia-agent benchmark (Action API / REST / SPARQL / live editing / Toolforge). Companion file: `01-*` (prior art, if present). Every entry below was verified by live fetch on 2026-08-19 (arXiv abs pages, GitHub API, official docs). HTTP status recorded in the per-entry notes and in the Verification Log (§6). Anything not confirmed by a fetch is marked **[UNVERIFIED]`.***

---

## 1. Landscape overview

**Agentic benchmarks** fall into five families, each with distinct trade-offs for a Wikimedia benchmark:

1. **Live-web task suites** (GAIA, WebVoyager, BrowseComp, AssistantBench, LoHoSearch): agents hit the *real* web, so results are ecologically valid but non-reproducible (site drift, paywalls, CAPTCHA). WebVoyager explicitly omitted sites requiring login/CAPTCHA — a lesson for editing tasks.
2. **Self-hosted web environments** (WebArena, Mind2Web, BrowserGym): reproducible snapshots of real sites — **WebArena ships a Kiwix-based offline Wikipedia (MediaWiki) replica**, the only benchmark in this survey with a MediaWiki environment. No benchmark found that exercises the **MediaWiki Action API / REST / SPARQL** stack (WebArena's wiki is browser-only, and the underlying wiki is old/snapshot).
3. **Tool/function-calling suites** (ToolBench, API-Bank, BFCL): thousands of API schemas and function calls; measure tool-call correctness, not end-to-end task outcomes. Their *tool-spec formats* (OpenAPI-style) are directly reusable for MediaWiki API task definitions.
4. **Conversational tool-agent-user** (tau-bench): simulated users + domain tools + policy guidelines; evaluates task success from final *system state* and user satisfaction — the best template for on-wiki editing tasks with reviewer feedback.
5. **Computer/GUI use** (OSWorld): desktop control; methodology (execution-based scoring) transfers, environment does not.

**2024–2026 benchmarks with explicit Wikipedia/MediaWiki presence** (verified): **WebArena** (MediaWiki replica), **Wikibench** (2024; community-curated AI-eval datasets *for Wikipedia* — not agentic but benchmark-construction), plus **GAIA** (web/tool-use tasks; per-task Wikipedia usage not verified). **WebVoyager — contrary to a common assumption — does NOT include Wikipedia among its 15 sites** (verified from the paper itself, see §3). No dedicated "MediaWiki-API agent benchmark" exists as of this survey → the proposed Wikimedia suite fills a genuine gap.

**Eval harnesses** split into: agent-native frameworks (**Inspect AI**, **LangSmith**, **Braintrust**, **promptfoo**, **AutoGenBench**, **DeepEval**), static prompt evals (**OpenAI Evals**, **lm-eval**, **HELM**), and metric libraries (**RAGAS**). For the "skills vs no-skills A/B on live wiki tasks" pattern, Inspect / LangSmith / Braintrust / promptfoo / DeepEval are the practical candidates (§5); lm-eval and HELM are not agent runtimes.

---

## 2. Master table

| Name | Type | Year | What it measures | Wikipedia relevance | Scoring | Source URL (HTTP status) |
|---|---|---|---|---|---|---|
| GAIA | Benchmark | 2023 | General assistant ability: reasoning + tool use + web browsing on 466 real-world questions | Low–med (browsing tasks; per-task wiki usage **[UNVERIFIED]**) | LLM-judge vs reference answers; humans 92% vs GPT-4+plugins 15% | arxiv.org/abs/2311.12983 (200); HF dataset gaia-benchmark/GAIA (200); GitHub facebookresearch/GAIA (404) |
| WebVoyager | Benchmark | 2024 | End-to-end LMM web agents on 643 tasks across 15 live sites | **None — Wikipedia NOT among the 15 sites** (paper §4.1, verified) | "WebVoyager Judge" (GPT-4V), ~90% human agreement | arxiv.org/abs/2401.13919 (200); github.com/MinorJerry/WebVoyager (200) |
| WebArena | Benchmark + env | 2023 | Language agents on 812 tasks in 6 self-hosted sites | **High — ships a Kiwix offline Wikipedia (MediaWiki) snapshot env** | Task success from env state + LLM evaluator | arxiv.org/abs/2307.13854 (200); github.com/web-arena-x/webarena (200) |
| Mind2Web | Benchmark | 2023 | Generalist web agents on 2,000+ tasks from 137 real sites (cross-domain generalization) | None verified (no wiki hits in official card) | Element acc / op F1 / step success | arxiv.org/abs/2306.06070 (200); github.com/OSU-NLP-Group/Mind2Web (200, via search API) |
| BrowseComp | Benchmark | 2024 | Browsing/deep-research agents on 1,266 hard multi-step questions | **[UNVERIFIED]** (openai.com blog is JS-rendered; no text confirm) | Automated grader on final answer | openai.com/index/browsecomp/ (200); github.com/openai/simple-evals (200) |
| tau-bench | Benchmark | 2024 | Tool-agent-user conversations in real customer-service domains | None | DB-state task success + pass^k reliability + user satisfaction | arxiv.org/abs/2406.12045 (200); github.com/sierra-research/tau-bench (200) |
| AgentBench | Benchmark | 2023 | LLMs-as-agents across 8 envs (OS, DB, KG, card game, lateral thinking, web shop, web browse, coding) | None | Success rate per env | arxiv.org/abs/2308.03688 (200); github.com/THUDM/AgentBench (200) |
| OSWorld | Benchmark | 2024 | Multimodal computer-use agents on 369 open-ended desktop tasks | None | Execution-based success rate (env state); human-verified subset | arxiv.org/abs/2404.07972 (200); github.com/xlang-ai/OSWorld (200) |
| AssistantBench | Benchmark | 2024 | Web agents on 214 realistic, time-consuming research tasks (auto-evaluated) | Low (web-research tasks; wiki usage **[UNVERIFIED]**) | Automated, reference-based judging | arxiv.org/abs/2407.15711 (200); github.com/oriyor/assistantbench (200) |
| ToolBench | Benchmark | 2023 | Open-source LLMs' tool manipulation on 16k+ RapidAPI tools | None (RapidAPI catalogue) | ToolEval: API-call pass rate + LLM-judged preference | arxiv.org/abs/2305.16504 (200); github.com/OpenBMB/ToolBench (200) |
| API-Bank | Benchmark | 2023 | Tool-augmented LLMs on 73 API tools, 314 dialogues, 753 calls | **[UNVERIFIED]** (possible wiki-type APIs in tool list) | APIEval: call-level + answer-level scores | arxiv.org/abs/2304.08244 (200); github.com/AlibabaResearch/DAMO-ConvAI (200) |
| BFCL | Benchmark + leaderboard | 2023– | Function-calling accuracy across categories (single/multi-turn, parallel, live APIs) | Low (live-API category; not wiki-specific) | AST/exact function-call match | gorilla.cs.berkeley.edu/leaderboard.html (200); github.com/ShishirPatil/gorilla (200) |
| AutoGenBench | Benchmark + harness | 2025 | AutoGen agents' task correctness with replay-based determinism | None | Task success (LLM-judge graded); replay for reproducibility | github.com/microsoft/autogen (200); "Introduces AutoGenBench" PR #1048 (200) |
| SWE-bench | Benchmark | 2023 | Resolving 2,294 real GitHub issues (coding; detailed here for completeness only) | None | Test-suite pass@1 | arxiv.org/abs/2310.06770 (200); github.com/princeton-nlp/SWE-bench (200) |
| Wikibench | Eval-data curation system | 2024 | Community-driven AI evaluation dataset curation on Wikipedia | **Core — built for Wikipedia** (not an agent benchmark) | Community-curated labels via discussion + agreement metrics | arxiv.org/abs/2402.14147 (200); github.com/tskuo/Wikibench (cited in paper; search hit 200) |
| LoHoSearch | Benchmark | 2026 | Long-horizon search agents; auto-generated tasks beyond human difficulty ceiling | **[UNVERIFIED]** | Task success on auto-generated searches | arxiv.org/abs/2606.12837 (200) |
| promptfoo | Harness | 2023 | Prompt/agent/RAG testing; assertions, LLM-judge, cost/latency, red-teaming | n/a | Assertions + model-graded rubric + custom JS/Py | github.com/promptfoo/promptfoo (200); promptfoo.dev (200) |
| DeepEval | Harness | 2023 | pytest-style LLM eval; 100+ metrics incl. tool-call correctness | n/a | Metric-based (LLM-as-judge) | github.com/confident-ai/deepeval (200, search); docs.confident-ai.com (200) |
| OpenAI Evals | Harness | 2023 | Registry of prompt evals; model-graded / exact / rubric | n/a | LLM-as-judge (fact/match/rubric) + exact | github.com/openai/evals (200); evals.openai.com (200) |
| LangSmith | Platform/harness | 2023 | Dataset-driven eval + tracing of chains/agents; experiment A/B | n/a | LLM-as-judge + custom scorers + assertions | docs.smith.langchain.com (200); github.com/langchain-ai/langsmith-sdk (200) |
| Braintrust | Platform/harness | 2023 | Experiments over datasets; scoring; regression dashboards | n/a | LLM-as-judge + custom scoring | braintrust.dev/docs (200); github.com/braintrustdata/braintrust-sdk (200) |
| RAGAS | Metric library | 2023 | RAG pipeline quality (faithfulness, context precision/recall, answer relevance) | n/a (reusable for retrieval-grounded answers) | Reference-free LLM-as-judge metrics | github.com/explodinggradients/ragas (200); arxiv.org/abs/2309.15217 (200); docs.ragas.io (200) |
| EleutherAI lm-eval | Harness | 2022 (paper 2024) | Reference-based accuracy/perplexity on hundreds of static tasks | n/a | Exact/reference match; no LLM-judge | github.com/EleutherAI/lm-evaluation-harness (200); arxiv.org/abs/2405.14782 (200); docs URL (404 → **[UNVERIFIED]**) |
| Stanford HELM | Harness | 2022 | Holistic multi-metric LM eval (accuracy, calibration, robustness, fairness, bias, toxicity, efficiency) | n/a | Multi-metric, reference-based scenarios | github.com/stanford-crfm/helm (200); arxiv.org/abs/2211.09110 (200); crfm.stanford.edu/helm (200) |
| Inspect AI | Harness | 2024 | UK AISI agent-eval framework: solvers (agents/tool protocols incl. MCP), scorers, logging, cost | n/a | LLM-as-judge, exact, model-graded, custom scorers | github.com/UKGovernmentBEIS/inspect_ai (200); inspect.ai-safety-institute.org.uk (200) |

---

## 3. Per-entry notes (incl. known weaknesses)

### Benchmarks

**GAIA** (arXiv 2311.12983, 200; HF dataset 200; GitHub 404 at check — use HF). 466 questions (test hidden, validation public) demanding reasoning + multimodal + browsing + tool use; human 92% vs GPT-4+plugins 15%. Graded by an LLM judge against reference answers. *Weaknesses:* answer-grading via judge model has known false-positive/negative cases; live browsing drifts; per-task Wikipedia usage not documented. *Reuse:* task-style (multi-hop, web-backed questions) and the "conceptually simple for humans, hard for agents" calibration philosophy — ideal for wiki tasks with verifiable ground truth.

**WebVoyager** (arXiv 2401.13919, 200; repo MinorJerry/WebVoyager 200, 1.1k★). 643 tasks over 15 live websites; Selenium-driven multimodal agent; "WebVoyager Judge" (GPT-4V) with ~90% human agreement. **Verification finding: the paper's §4.1 site list is Allrecipes, Amazon, Apple, ArXiv, BBC News, Booking, Cambridge Dictionary, Coursera, ESPN, GitHub, Google Flights, Google Map, Google Search, Huggingface, Wolfram Alpha — Wikipedia is NOT included** (0 "Wikipedia" occurrences in the full paper text). *Weaknesses:* live-site drift (later runs saturate/change), judge is model-dependent, sites needing login/CAPTCHA excluded. *Reuse:* judge-calibration methodology (validate LLM judge against human on a subset).

**WebArena** (arXiv 2307.13854, 200; repo web-arena-x/webarena 200, 1.6k★). 812 tasks in 6 self-hosted sites; **includes a Wikipedia environment served from a Kiwix offline snapshot (`wikipedia_en_all_maxi_2022-05`, verified in README)** — a real MediaWiki install, browser-only. *Weaknesses:* static snapshot (2022), no Action-API surface, no auth/editing; sim-vs-live gap noted by authors and by follow-ups (VisualWebArena, WebArena-Lite). *Reuse:* the Kiwix-MediaWiki pattern is a ready-made offline wiki for a *reproducible* variant of the Wikimedia suite; shows what a browser-only wiki env buys (reproducibility) vs misses (API).

**Mind2Web** (arXiv 2306.06070, 200 — ID corrected via official HF card; repo OSU-NLP-Group/Mind2Web 200 via search, 1.0k★). 2,000+ tasks from 137 real websites; cross-domain generalization metrics (element accuracy, op F1, step success). No Wikipedia component found in the official card/README. *Weaknesses:* single-turn-ish action traces, no env for live replay; site drift. *Reuse:* cross-domain generalization framing ("trained on 100 sites, tested on 37 unseen") applies to wiki task families (read/query/edit on different wikis).

**BrowseComp** (openai.com/index/browsecomp 200; reference impl in openai/simple-evals 200, 4.6k★; no arXiv). 1,266 multi-step browsing questions; graders check the final answer. *Weaknesses:* [UNVERIFIED] any Wikipedia link (blog is JS-rendered); expensive to run; quickly saturated by deep-research models (per LoHoSearch abstract). *Reuse:* answer-verification design (specific, checkable strings) fits wiki-fact tasks.

**tau-bench** (arXiv 2406.12045, 200; sierra-research/tau-bench 200, 1.4k★). Agent + simulated user + domain API tools + policy guidelines; scores task success by comparing final **database state** to goal state, plus pass^k (reliability over k trials) and user satisfaction. *Weaknesses:* user-sim fidelity; domain scope. *Reuse:* the state-diff scoring pattern maps perfectly to on-wiki edits (compare resulting revision/API state), and the simulated user models a "reviewer" for edit tasks.

**AgentBench** (arXiv 2308.03688, 200; THUDM/AgentBench 200, 3.7k★, ICLR'24). 8 environments: OS, DB, knowledge graph, digital card game, lateral thinking, web shopping, web browsing, programming. *Weaknesses:* envs age; heterogeneous scoring. *Reuse:* multi-env design template (one suite, many API surfaces).

**OSWorld** (arXiv 2404.07972, 200; xlang-ai/OSWorld 200, 3.1k★, NeurIPS'24). Real desktop environment, execution-based evaluation, supports learning. *Weaknesses:* GUI, not API; heavy infra. *Reuse:* "execution-based evaluation" doctrine — score outcomes from environment state, not model self-reports.

**AssistantBench** (arXiv 2407.15711, 200 — ID corrected via repo citation; oriyor/assistantbench 200, 72★). 214 realistic time-consuming web tasks, automatically evaluated. *Weaknesses:* small set; judge-based grading; models still far from solved. *Reuse:* "tasks that take a human minutes-to-hours of web research" pattern — e.g., multi-page wiki research tasks with factual answer keys.

**ToolBench** (arXiv 2305.16504, 200; OpenBMB/ToolBench 200, 5.7k★, ICLR'24 spotlight). Tool-learning platform over 16k+ RapidAPI tools; ToolEval = pass rate (API-call success) + win rate (LLM-judged preference). *Weaknesses:* API-call success ≠ task success; RapidAPI catalogue is not wiki-centric. *Reuse:* tool-schema standardization for MediaWiki endpoints.

**API-Bank** (arXiv 2304.08244, 200; repo in AlibabaResearch/DAMO-ConvAI 200, 1.6k★). 73 API tools, 314 dialogues, 753 calls; APIEval scores call-level and answer-level. Whether the 73 include Wikipedia-type APIs: **[UNVERIFIED]**. *Weaknesses:* small, dated. *Reuse:* two-tier scoring (did the call succeed / was the answer right) = cheap version of the wiki A/B metric stack.

**BFCL** (gorilla.cs.berkeley.edu/leaderboard.html 200; harness code in ShishirPatil/gorilla 200, 13k★; results archive HuanzhiMao/BFCL-Result 200, 31★). Function-calling accuracy over many categories; recent versions add multi-turn, parallel, and live-API calls. *Weaknesses:* measures call correctness, not end-task outcome; heavy model churn on leaderboard. *Reuse:* its AST-based function-call matching is a ready-made "did the agent invoke the Action API correctly" checker.

**AutoGenBench** (verified inside microsoft/autogen 200, 60k★; 41 issues/PRs incl. PR #1048 "Introduces AutoGenBench", 200; standalone docs path 404 → **[UNVERIFIED]**). Benchmark + harness for AutoGen agents; replay-based determinism so runs are reproducible; task templates with graded success. *Weaknesses:* AutoGen-specific; code-heavy tasks. *Reuse:* the replay idea (record tool traces, replay to verify) for debugging silent failures.

**SWE-bench** (arXiv 2310.06770, 200; princeton-nlp/SWE-bench 200, 5.7k★). 2,294 real GitHub issues → test-suite pass@1. Skipped per scope; relevant only as the reference for agentic coding evals.

**Wikibench** (arXiv 2402.14147, 200; repo tskuo/Wikibench, cited in the paper's HTML, 200 via search). A system for **communities to collaboratively curate AI evaluation datasets on Wikipedia**, with field study on Wikipedia content-moderation tasks; addresses ambiguity through discussion. Not an agent benchmark, but the only verified Wikipedia-native benchmark-construction work — directly relevant to task-authoring with WikiProjects.

**LoHoSearch** (arXiv 2606.12837, 200, 2026). Long-horizon search-agent benchmark with auto-generated tasks past the human difficulty ceiling; notes BrowseComp saturation. Wikipedia link **[UNVERIFIED]**. Signals the field's direction: auto-generated, entity-statistics-driven tasks — a pattern Wikidata could serve uniquely.

**Adjacent (one-liners):** **BrowserGym** (ServiceNow/BrowserGym, 200, 1.3k★) — gym environment wrapping WebArena/WebVoyager-style tasks; **TheAgentCompany** (TheAgentCompany/TheAgentCompany, 200, 766★; no wiki env, verified 0 "wiki" hits in README) — 2025 software-company agent benchmark.

### Harnesses

**promptfoo** (github.com/promptfoo/promptfoo 200, 24.4k★; promptfoo.dev 200; sitemap 200, 550 pages incl. 19 agent pages: `docs/guides/test-agent-skills`, `evaluate-openai-agents-python`, `model-graded/agent-rubric`). Open-source; YAML/JS configs; assertions (exact/contains/regex/model-graded/custom JS+Python); **prompt variants & matrix = native A/B of skills-vs-no-skills**; cost/latency tracking; CI + red-team tooling. *Weaknesses:* agent-loop support is thinner than Inspect's (needs custom evaluators for long tool loops); model-graded assertions are only as good as the rubric.

**DeepEval** (confident-ai/deepeval 200 via search, 17.7k★; docs.confident-ai.com 200; tool-call-correctness metric page 200). Pytest-style unit tests; 100+ metrics (G-Eval, faithfulness, **tool-call correctness**); LLM-as-judge; CI-native; optional Confident AI cloud for dashboards/cost. *Weaknesses:* less tracing/versioning than platforms; agent-loop orchestration is yours to write.

**OpenAI Evals** (openai/evals 200, 19.2k★; evals.openai.com 200). Registry + templates (model-graded fact/match/rubric, exact, embedding). *Weaknesses:* static prompt evals; no agent runtime, no cost tracking built in; A/B requires wrapping your agent as the completion function.

**LangSmith** (docs.smith.langchain.com 200; langchain-ai/langsmith-sdk 200, 1.0k★). Dataset-driven evaluation + full tracing of agent runs (every tool call, latency, token cost); run two variants over one dataset and diff; prompt/dataset versioning; cloud + self-hosted. *Weaknesses:* SaaS-centric; LangGraph-centric for agent tracing; costs money at scale.

**Braintrust** (braintrust.dev/docs 200; braintrustdata/braintrust-sdk 200, 27★ — JS SDK repo). Experiments over datasets, scoring functions, LLM-as-judge, cost/latency tracking, regression dashboards; Python/TS SDKs; agent tracing. *Weaknesses:* platform-dependent (hosted); smaller ecosystem than LangSmith.

**RAGAS** (explodinggradients/ragas 200, 15.4k★; arXiv 2309.15217 200; docs.ragas.io 200). Reference-free RAG metrics (faithfulness, answer relevance, context precision/recall). *Weaknesses:* RAG-only; not agentic. *Reuse:* its faithfulness/context metrics for grading answers grounded in retrieved wiki/SPARQL content.

**EleutherAI lm-eval** (repo 200, 13.7k★; arXiv 2405.14782 200; all readthedocs variants 404 → docs **[UNVERIFIED]**). Hundreds of static reference-based tasks; no agents, no LLM-as-judge. *Reuse:* none for agent A/B (keep in mind for base-model checks).

**Stanford HELM** (repo 200, 2.9k★; arXiv 2211.09110 200; crfm.stanford.edu/helm 200). Multi-metric holistic eval (accuracy, calibration, robustness, fairness, bias, toxicity, efficiency) over scenarios; static prompts. *Weaknesses:* not an agent runtime; extension needed for tool loops. *Reuse:* its metric taxonomy (esp. efficiency = cost/time) for reporting standards.

**Inspect AI** (UKGovernmentBEIS/inspect_ai 200, 2.6k★; inspect.ai-safety-institute.org.uk 200). UK AISI's agentic eval framework: **solvers** (agents with tool-use protocols incl. MCP), **scorers** (LLM-as-judge, exact, model-graded, custom Python), live tool connections, per-run JSONL transcripts, cost/time tracking, parallel execution, `inspect eval` CLI; provider-agnostic (any OpenAI-compatible/API model). **Best overall fit** for the A/B pattern — designed exactly for "same tasks, different agent configurations, compare scored runs."

---

## 4. Lessons for a Wikimedia agent benchmark

1. **Live vs sandbox is the central design decision.** WebVoyager/BrowseComp show live-web validity but drift and saturation; WebArena chose self-hosted snapshots for reproducibility. Wikimedia uniquely offers *both*: live read APIs (stable, versioned, caches) and sandboxes (test.wikipedia.org, beta.wikimedia.org, or a self-hosted MediaWiki from a Kiwix dump — WebArena already proves the Kiwix route). Recommend: **read tasks → live; edit tasks → test/beta wikis or self-hosted replica**; freeze task-specific snapshots (page revisions, SPARQL endpoint dumps) for scoring.
2. **Score from environment state, not the judge.** tau-bench's DB-state diff and OSWorld's execution-based checks are the gold standard: for wiki tasks, verify the resulting page/revision/API response deterministically (e.g., the revision exists, diff matches expected change, SPARQL result set equals reference). Reserve LLM-as-judge for subjective parts (style, "is this a good lead section?") and validate it against humans on a subset first (WebVoyager's ~90% judge-human agreement is the bar to report).
3. **A/B rigor for skills-vs-no-skills**: same task set, same model + temperature, counterbalanced order, ≥3 seeds; report per-arm: success rate, **silent-failure rate** (tool calls that returned errors but the agent claimed success — the metric from the existing Wikipedia-AI-Skills A/B), wall-clock time, token/API cost, and judge-human agreement. tau-bench's `pass^k` is the right reliability statistic.
4. **User-simulation for editing tasks.** tau-bench's simulated user pattern can model a Wikimedian reviewer (revert, request citation, BLP concerns) — giving editing tasks a conversational dimension without needing real users.
5. **Track everything.** Silent failures are invisible without per-tool-call logs: use a tracing harness (Inspect transcripts, LangSmith traces) and record every Action-API/REST/SPARQL call with status code, latency, and bytes — this also feeds the cost analysis Wikimedia will care about (their APIs are free; your model calls aren't).
6. **Tool-call correctness is a useful intermediate metric.** BFCL's AST matching and ToolBench's pass rate isolate "did the agent call `action=query&prop=revisions` correctly" from "did it answer the user's question" — publish both layers (API-Bank's two-tier scoring).
7. **Respect Wikimedia infrastructure rules.** Real-account editing needs bot accounts + rate limits (`maxlag`), User-Agent policy, and test-wiki preference; the benchmark should encode this as part of the agent's constraints (tau-bench's "policy guidelines" pattern) — and it doubles as a realistic constraint test.
8. **Community-curated ground truth.** Wikibench shows Wikipedia's community can co-curate eval data; WikiProjects (e.g., WikiProject's assessment grades) are a ready-made ground-truth source for task authoring and answer keys.
9. **You occupy a real gap.** No benchmark in this survey exercises the MediaWiki Action API / REST / SPARQL / editing stack; WebArena's wiki is browser-only and static. The Wikimedia suite's differentiation: **API-native, live-or-reproducible, state-verified** agent tasks.
10. **Format for reuse**: define tasks as JSONL (task, environment, ground-truth check, judge rubric) and tools as OpenAPI-style schemas (ToolBench/BFCL pattern) so any harness (Inspect, promptfoo, LangSmith) can ingest them.

---

## 5. Harness suitability: can it run the "skills vs no-skills on live wiki APIs" A/B?

| Harness | Runs agent loops on live APIs? | LLM-as-judge | Assertions / custom checks | Cost & time tracking | Versioning / A/B compare | Verdict for wiki A/B |
|---|---|---|---|---|---|---|
| **Inspect AI** | ✅ first-class (tool protocol, MCP) | ✅ | ✅ (exact, model-graded, Python) | ✅ per-run | ✅ run diffs via `inspect eval` + compare | **Best fit** — two plan variants (with/without skills) over the same task JSONL; score + diff everything |
| **LangSmith** | ✅ (any agent SDK; tracing native) | ✅ | ✅ | ✅ | ✅ experiments over datasets | **Excellent** — tracing exposes silent failures; A/B via dataset experiments |
| **Braintrust** | ✅ (SDK tracing) | ✅ | ✅ | ✅ | ✅ experiments/regressions | **Excellent** — same pattern, lighter ecosystem |
| **promptfoo** | ⚠️ via custom evaluators (agent guides exist) | ✅ (incl. agent rubric) | ✅ (exact/contains/JS/Py) | ✅ | ✅ prompt variants/matrix | **Good, lightweight** — cheapest way to start the A/B; CI-native |
| **DeepEval** | ⚠️ you orchestrate the agent | ✅ | ✅ (incl. tool-call-correctness metric) | ⚠️ via Confident AI cloud | ⚠️ pytest parametrization | **Good** — two parametrized pipelines, metric diff in CI |
| **OpenAI Evals** | ⚠️ wrap agent as completion fn | ✅ | ✅ (limited) | ❌ | ⚠️ DIY | **Marginal** — static-prompt heritage; DIY agent runner |
| **RAGAS** | ❌ | ✅ (as metric basis) | ⚠️ RAG metrics only | ❌ | ❌ | **Partial** — reuse faithfulness/context metrics inside another harness for SPARQL/RAG-grounded answers |
| **EleutherAI lm-eval** | ❌ | ❌ | ✅ reference-only | ❌ | ❌ | **No** — static tasks only |
| **Stanford HELM** | ❌ | ❌ | ⚠️ scenario metrics | ⚠️ efficiency metric | ❌ | **No** (base-model checks only) |
| **AutoGenBench** | ✅ (AutoGen agents) | ✅ | ✅ | ⚠️ | ✅ replay determinism | **Conditional** — only if the agent is built on AutoGen; replay idea worth stealing |

**Recommended stack for the Wikimedia A/B:** Inspect AI (or LangSmith if tracing UX is preferred) as the runner; task JSONL + OpenAPI-style tool specs as the portable artifact; two plan variants (skills injected vs not); scorers = deterministic state checks (revision diff, SPARQL result match) + a validated LLM-judge rubric; report success, silent-failure rate, wall-clock, and $ cost per arm; `pass^k` over ≥3 seeds. promptfoo is the pragmatic minimal start (YAML variants + assertions + cost) before graduating to Inspect.

---

## 6. Verification log (all fetched 2026-08-19, User-Agent `HermesAgent/1.0 benchmark research`)

**Benchmarks — primary sources:**
- https://arxiv.org/abs/2311.12983 (GAIA) — **200**
- https://huggingface.co/datasets/gaia-benchmark/GAIA — **200**
- https://api.github.com/repos/facebookresearch/GAIA — **404** (repo no longer resolvable; use HF)
- https://arxiv.org/abs/2401.13919 (WebVoyager) — **200**; paper HTML https://arxiv.org/html/2401.13919v1 — **200** (§4.1 site list; **no Wikipedia**)
- https://api.github.com/repos/MinorJerry/WebVoyager — **200** (1,121★, pushed 2025-06); raw README — **200**
- https://arxiv.org/abs/2307.13854 (WebArena) — **200**
- https://api.github.com/repos/web-arena-x/webarena — **200** (1,584★); README confirms `WIKIPEDIA` env (Kiwix `wikipedia_en_all_maxi_2022-05`)
- https://arxiv.org/abs/2306.06070 (Mind2Web, correct ID via official HF card) — **200**
- https://api.github.com/search/repositories?q=Mind2Web (OSU-NLP-Group/Mind2Web, 1,019★) — **200**; HF card https://huggingface.co/datasets/osunlp/Mind2Web/raw/main/README.md — **200** (cites arXiv 2306.06070; 0 wiki hits)
- https://openai.com/index/browsecomp/ — **200** (JS-rendered; text unverifiable → Wikipedia link **[UNVERIFIED]**)
- https://api.github.com/repos/openai/simple-evals — **200** (4,606★; README references BrowseComp)
- https://arxiv.org/abs/2406.12045 (tau-bench) — **200**; https://api.github.com/repos/sierra-research/tau-bench — **200** (1,391★)
- https://arxiv.org/abs/2308.03688 (AgentBench) — **200**; https://api.github.com/repos/THUDM/AgentBench — **200** (3,675★)
- https://arxiv.org/abs/2404.07972 (OSWorld) — **200**; https://api.github.com/repos/xlang-ai/OSWorld — **200** (3,099★)
- https://arxiv.org/abs/2407.15711 (AssistantBench, correct ID via repo citation) — **200**; https://api.github.com/repos/oriyor/assistantbench — **200** (72★)
- https://arxiv.org/abs/2305.16504 (ToolBench) — **200**; https://api.github.com/repos/OpenBMB/ToolBench — **200** (5,729★)
- https://arxiv.org/abs/2304.08244 (API-Bank) — **200**; https://api.github.com/repos/AlibabaResearch/DAMO-ConvAI — **200** (1,577★)
- https://gorilla.cs.berkeley.edu/leaderboard.html (BFCL) — **200**; https://api.github.com/repos/ShishirPatil/gorilla — **200** (12,997★); https://api.github.com/repos/HuanzhiMao/BFCL-Result — **200** (31★)
- https://api.github.com/repos/microsoft/autogen — **200** (60,520★); issues search `repo:microsoft/autogen AutoGenBench` — **200** (41 hits; PR #1048 "Introduces AutoGenBench"); AutoGenBench docs subpath — **404** **[UNVERIFIED]**
- https://arxiv.org/abs/2310.06770 (SWE-bench) — **200**; https://api.github.com/repos/princeton-nlp/SWE-bench — **200** (5,669★)
- https://arxiv.org/abs/2402.14147 (Wikibench) — **200**; paper HTML — **200** (cites github.com/tskuo/Wikibench); GitHub search `wikibench in:name` — **200** (tskuo/Wikibench present); https://api.github.com/repos/wikimedia/wikibench — **404** (wrong org)
- https://arxiv.org/abs/2606.12837 (LoHoSearch) — **200**
- https://api.github.com/repos/TheAgentCompany/TheAgentCompany — **200** (766★; 0 wiki hits in README); https://theagentcompany.com — **200**
- https://api.github.com/repos/ServiceNow/BrowserGym — **200** (1,325★, org moved from microsoft)

**Harnesses — primary sources:**
- https://api.github.com/repos/promptfoo/promptfoo — **200** (24,377★); https://promptfoo.dev/ — **200**; sitemap — **200** (19 agent-related pages)
- https://api.github.com/search/repositories?q=deepeval (confident-ai/deepeval, 17,706★) — **200**; https://docs.confident-ai.com/ — **200**; https://docs.confident-ai.com/docs/metrics-tool-call-correctness — **200**
- https://api.github.com/repos/openai/evals — **200** (19,203★); https://evals.openai.com/ — **200**
- https://docs.smith.langchain.com/ — **200**; https://api.github.com/repos/langchain-ai/langsmith-sdk — **200** (1,024★)
- https://www.braintrust.dev/docs/ — **200**; https://api.github.com/repos/braintrustdata/braintrust-sdk — **200** (27★)
- https://api.github.com/repos/explodinggradients/ragas — **200** (15,383★); https://arxiv.org/abs/2309.15217 — **200**; https://docs.ragas.io/ — **200**
- https://api.github.com/repos/EleutherAI/lm-evaluation-harness — **200** (13,717★); https://arxiv.org/abs/2405.14782 — **200**; docs: lm-eval.readthedocs.io / lm-evaluation-harness.readthedocs.io / evaluationharness.readthedocs.io — all **404** **[UNVERIFIED]**
- https://api.github.com/repos/stanford-crfm/helm — **200** (2,880★); https://arxiv.org/abs/2211.09110 — **200**; https://crfm.stanford.edu/helm/ — **200**
- https://api.github.com/repos/UKGovernmentBEIS/inspect_ai — **200** (2,577★); https://inspect.ai-safety-institute.org.uk/ — **200**

**Notes on method:** arXiv export API (`export.arxiv.org/api/query`) was rate-limited (429) from this network; abs pages worked, so titles/abstracts were parsed from arxiv.org/abs HTML. GitHub core API rate limit was exhausted mid-run (403) — remaining repos were verified via GitHub search API, raw.githubusercontent.com, paper citations, or official HF cards, each recorded above. Search engines (Google/Bing) and Semantic Scholar were bot-blocked or rate-limited (429) and were not relied on.

**[UNVERIFIED] items** (could not confirm by fetch): GAIA per-task Wikipedia usage; BrowseComp Wikipedia link (blog JS-rendered); API-Bank tool list incl. wiki-type APIs; AssistantBench Wikipedia usage; LoHoSearch Wikipedia link; lm-eval docs URL; AutoGenBench docs subpath; Mind2Web-1.0 / agentorg HF cards (401/404); `MinZheng-HKUST/WebVoyager`, `xlang-ai/Mind2Web`, `microsoft/BrowserGym`, `confidently-ai/deepeval`, `gorilla-llm/Berkeley-Function-Calling-Leaderboard` (old repo paths, all 404 — resolved to current locations above).
