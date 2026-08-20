# WAIS-Bench — A Wikimedia LLM Skills Benchmark: Research Synthesis & Proposal

**For:** Andrew Lih (Fuzheado) × Lodewijk Gelauff — brainstorming thread
**Date:** 2026-08-19
**Status:** Landscape verified live (arXiv/GitHub/diff.wikimedia.org fetches, HTTP statuses in §6); proposal is a design sketch, not an implementation.
**Companion files:** `landscape/01-wikipedia-knowledge.md`, `landscape/02-agentic-harnesses.md`, `landscape/03-wikidata-wikimedia.md` (full tables + per-benchmark notes + verification logs) in this directory.

---

## 0. TL;DR

1. **There is no incumbent.** The verified landscape contains 40+ benchmarks that use Wikipedia as *knowledge substrate* (QA, factuality, RAG, article generation) and a dozen agent/tool benchmarks that use generic web or synthetic APIs — but **nothing tests an LLM agent interacting with the wiki itself**: editing, MediaWiki Action/REST APIs, SPARQL against live Wikidata in an agentic loop, Commons workflows, Toolforge, or ORES/LiftWing. The AB suite in `research/ab-testing/` is the closest existing thing on the *task* side; nothing on the *benchmark* side competes.[1]
2. **What to copy is clear.** Pinned data snapshots (KILT[3]), accuracy + calibration grading with a "not attempted" bucket (SimpleQA[2]), outcome-and-evidence joint scoring (FEVER/KILT[3]), contamination resistance via on-the-fly item generation (FreshTab[9]), a self-hosted MediaWiki environment (WebArena's Kiwix snapshot[21][43]), state-based scoring and simulated users (τ-bench[22]), and community-curated eval data (Wikibench[6]).
3. **Critical read of the "why we test" framework:** it is a strong *deployment* objective function (cost of trustworthy result, silent failure as worst property) but it conflates deployment evaluation with benchmark design; "calibration outranks accuracy" is only meaningful with an accuracy floor; and "LiftWing is free" must be measured (free ≠ adequate — their own ~11.9% fabricated-quote finding is evidence).
4. **Critical read of the AB meta-report:** the findings are plausible and useful hypotheses; the *methodology* cannot support the headline numbers (n=24 total, n=2 per cell → no confidence intervals; "0/12 silent failures" is statistically consistent with a true rate as high as ~22% by the rule of three; no rubric, no blinding, no ground truth, tasks not frozen). The 6 named silent-failure modes are the most valuable artifact — they become the trap/canary layer of the new suite.
5. **Proposal:** **WAIS-Bench** — a two-tier (frozen-gold + live) task suite with verifiers-first design, a model × skills-intervention matrix, and a metric stack headed by *plausible-error rate* (silent failures that pass automated plausibility checks), reported with confidence intervals. Phase 0 = retrofit the 12 AB tasks into re-runnable task files. Named provisionally; `WikiAgentBench`/`WikiEval`/`WAB` are already searched-and-not-found as existing names, so the namespace is clear.[29][30][31][32]

---

## 1. The landscape — what exists (all verified live, 2026-08-19)

### 1.1 Wikipedia as knowledge substrate — five waves

Wikipedia is the single most-used knowledge corpus in NLP benchmarking:[3]

| Wave | Era | Examples | What they test |
|---|---|---|---|
| Reading comprehension | 2015–2019 | SQuAD, WikiQA, TriviaQA, Natural Questions, HotpotQA | Extractive/multi-hop QA over article passages; EM/F1 metrics |
| Structured data | 2015–2020 | WikiTableQuestions, WikiSQL, TabFact | Semantic parsing + fact verification over Wikipedia's HTML tables |
| Grounding & verification | 2017–2021 | FEVER/FEVEROUS, Wizard of Wikipedia, ELI5, **KILT** | Claim verification, grounded dialogue, long-form QA — KILT unified 8 tasks over one pinned Wikipedia snapshot with an evidence metric (R-precision)[3] |
| LLM factuality & freshness | 2023–2025 | **FActScore**, **FreshQA**, **SimpleQA**, HLE, SimpleBench, WikiContradict, WIKIGENBENCH, FreshTab | Atomic-fact precision of generation[4]; time-sensitive knowledge[5]; short-form factuality **+ calibration** with correct/incorrect/not-attempted grading[2]; SimpleBench (GitHub, no arXiv)[17]; knowledge-conflict QA mined from Wikipedia's own edit history[7]; full-article generation with citations[8]; contamination-resistant on-the-fly table-to-text[9] |
| RAG, agents, community | 2024–2026 | LongBench, RAGBench, CRAG, **Wikibench**, LLM-WikiRace, Wiki Live Challenge, TSM-Bench/WETBench | Long-context retrieval[14]; RAG component evals[15]; tool-use scoring on a Wikipedia-inclusive domain mix[16]; **community-driven curation of AI-eval datasets on Wikipedia**[6]; hyperlink-graph planning[11]; live-article expert-judged research tasks[12]; detecting LLM-written text in real Wikipedia editing practice[13] |

Also notable: **WikiVQABench** (2026) is the first benchmark explicitly combining Wikipedia text *and* Wikidata structured knowledge — a bridge toward the SPARQL tasks a Wikimedia suite wants.[10]

### 1.2 Agentic & tool-use benchmarks

| Family | Examples | Relevance to a wiki suite |
|---|---|---|
| Live-web task suites | GAIA[19], WebVoyager[20], BrowseComp[25], AssistantBench[23], LoHoSearch | Ecologically valid but non-reproducible (site drift, CAPTCHA). **Correction to a common assumption: WebVoyager's 15 sites do NOT include Wikipedia** (verified from the paper's site list: Allrecipes, Amazon, Apple, arXiv, BBC, Booking, Cambridge Dictionary, Coursera, ESPN, GitHub, Google Flights/Map/Search, HuggingFace, Wolfram Alpha)[20] |
| Self-hosted web environments | WebArena[21][43], Mind2Web[24], BrowserGym | Reproducible snapshots. **WebArena ships a Kiwix-based offline MediaWiki replica (`wikipedia_en_all_maxi_2022-05`) — the only MediaWiki environment in the agent-benchmark literature**, and it is browser-only, static, and pre-2022 — no API surface, no editing[21][43] |
| Tool/function-calling | ToolBench[26], API-Bank[27], BFCL | Measure tool-call correctness, not end-to-end outcomes; their OpenAPI-style tool-spec format is directly reusable for MediaWiki task definitions |
| Conversational tool-agent-user | τ-bench[22] | Simulated users + domain tools + policy guidelines; scored from final system state. **The best template for on-wiki editing tasks** (a simulated Wikimedian reviewer who reverts/requests citations)[22] |
| Computer/GUI | OSWorld[44] | Execution-based scoring methodology transfers; environment doesn't |

**No benchmark in this family exercises the MediaWiki Action API / REST / SPARQL / editing stack.**[21] That is the core of the gap.

### 1.3 Wikidata / KG-QA

The lineage moved Freebase → DBpedia → **Wikidata**: QALD-10 is explicitly the migration benchmark ("research is gravitating toward Wikidata… Freebase is defunct")[29][30]; LC-QuAD 2.0 (24,026 NL↔SPARQL pairs, scored by *execution*)[31]; KQA Pro (~120K questions with compositional programs, scored by program execution)[32]; SimpleQuestions has a community Wikidata mirror[33]; SemTab covers table-to-KG matching against Wikidata; Wikidata5M (via KEPLER) is the standard Wikidata-derived KG-embedding corpus[48]. **LLM-KG-Bench** (AKSW) is a BIG-bench-style harness for LLMs on KG tasks, including SPARQL-capability probes — closest existing "harness" but no live endpoint, no agent loop.[34]

All of these are **single-shot, offline**: one question → one query → one answer. None models the agentic loop (draft query → execute → hit WDQS timeout/429 → repair → verify), none touches Wikidata *editing* (wbeditentity, references, qualifiers, constraints).

### 1.4 Wikimedia-specific LLM efforts (verified)

- **WikiChat** (Stanford OVAL): few-shot grounding on English Wikipedia to stop hallucination; evaluated with a *hybrid human + GPT-4 judge* protocol on live Wikipedia — prior art for both grounding checks and judge design.[18]
- **WIKIGENBENCH**: full-length article generation with citations, scored on factuality vs. wiki references — generation only, never validates an edit against wiki rules.[8]
- **Wikibench** (CHI 2024): a system for the Wikipedia community to *co-curate* AI evaluation datasets, navigating ambiguity through discussion; field study on Wikipedia. The governance model to copy.[6]
- **TSM-Bench / WETBench** (2025–26): detecting LLM-written text in real Wikipedia editing practice — guardrail metrics for the editing side.[13]
- **Wiki Live Challenge** (2026): expert-judged deep-research tasks on current articles — the live-article-as-task-generator pattern.[12]
- **FrOG** (Wikidata Research Fund 2024): GraphRAG question answering over Wikidata — community-funded QA prototype, not a benchmark, but evidence of demand.[46]
- **Wikimania 2026 Wiki-AI pre-conference** notes survey what AI already runs on the wikis — context for which tasks matter.[47]
- Explicitly **searched and NOT FOUND** (do not cite as existing): `WikiEval`, `WAB`, `WikiAgentBench`, `Wiki-Agent`, `WikiEdit`, `WikidataEdit`.[29][30][31][32] The name space for a new suite is clear.

### 1.5 Harnesses (for running the suite)

promptfoo (24k★, CI-native, prompt/agent variants + assertions + cost)[35], DeepEval (17.7k★, pytest-style, tool-call-correctness metric)[36], **Inspect AI** (UK AISI; first-class agent loops, tool protocol, run-diff comparison — best fit for the skills-vs-no-skills A/B)[37], LangSmith/Braintrust (tracing + experiment comparison), openai/evals[39], EleutherAI lm-eval[40] and HELM[41] (static-prompt only — not agent runtimes), RAGAS[42] (metric library: faithfulness/relevancy — reusable for SPARQL-grounded answers).

---

## 2. What we can learn — lessons that transfer

1. **Pin every task to a data version.** KILT's fixed-snapshot design is the reproducibility gold standard; go further and pin *page revisions*, recording them in the harness. Re-run scores when data moves.[3]
2. **Score outcome AND evidence jointly.** FEVER score, KILT R-precision, HotpotQA joint-EM all penalize "right answer, wrong source". For wiki work: did the model answer from the right page/revision and cite it correctly? Maps onto FActScore-style atomic fact checks for article writing.[3][4]
3. **Design for contamination resistance from day one.** FreshTab generates items on the fly from live Wikipedia; Wiki Live Challenge uses current articles; static dumps rot twice (memorization + corpus drift). Generate/refresh items programmatically from live APIs.[9][12]
4. **Freshness is a first-class axis.** FreshQA and WikiContradict show stale knowledge and knowledge-conflict are separate failure modes. Wikipedia's edit stream enables a *versioned temporal* benchmark no static corpus can: ask about a page before/after a notable edit.[5][7]
5. **Score the actions, not just the answer.** CRAG's tool-call scoring and LLM-WikiRace's step counting are the templates: SPARQL query validity, API-call correctness, edit quality should be scored separately from final text.[11][16]
6. **Score from environment state, not the judge.** τ-bench's DB-state diff and OSWorld's execution checks are the gold standard: verify that the revision exists, the diff matches, the SPARQL result set equals the reference. Reserve LLM-as-judge for subjective parts (style, lead quality) and validate it against humans first — WebVoyager's ~90% judge-human agreement is the bar to report.[22][20][44][45]
7. **A/B rigor:** same task set, same model + temperature, counterbalanced order, ≥3 seeds; report per arm: success, silent-failure rate, wall-clock, token/API cost, judge-human agreement; use τ-bench's `pass^k` reliability statistic.[22]
8. **Let the community curate.** Wikibench demonstrates editors co-curating eval data works; WikiProject assessment grades are a ready-made ground-truth source. This also builds legitimacy — and keeps humans at the center of knowledge construction.[6]
9. **Reuse mature metric machinery.** RAGAS rubrics[42], FEVER score[3], FActScore atomic decomposition[4], SimpleQA's ECE calibration[2][38] are off-the-shelf.
10. **Benchmark infrastructure decays; data must live in repos.** QALD-9's official site is dead (qald.sebastianwalter.org → 000), qald.aksw.org unreachable today, SemTab 2023 page 404s, canonical repos vanished (KQAPro, Wikidata5M), facebookresearch/KILT dormant since 2022.[30][31][32][3] A Wikimedia suite must live in a maintained repo with data mirrored (Zenodo/HF) and URL-checked — the repo already has this pattern (`scripts/verify-links.py`).
11. **Don't trust memory for citations.** In this research, 4 of 8 remembered arXiv IDs were wrong, and two widely repeated claims ("WebVoyager includes Wikipedia"; "web-scale WikiBench exists") turned out false. The suite's docs must link verified primary sources only.[20]

---

## 3. Critical reading of the "why we test / what we optimise for" framework

*(The framework: four constraints — volume, provenance, privacy, reproducibility; optimise total cost of a trustworthy result = inference + verification + undetected errors; inference matters least because LiftWing is free; maximise the fraction acceptable without human review subject to a hard bound on undetected errors; calibration outranks accuracy; silent failure is the worst property.)*

### 3.1 Where it is right

- **Cost-of-trustworthy-result is the correct deployment objective**, and a better north star than raw accuracy for Wikimedia LLM work. The whole point of a benchmark is to *predict* this cost, not to maximize a leaderboard number.
- **Silent failure as the worst property** is the strongest claim, and it is independently corroborated: the AB report's no-skills arm failed 6/12 tasks with plausible-looking output and no error messages[1]; the framework's own runs found 100% schema-valid JSON with wrong values and ~11.9% fabricated quotes; and the eval literature's answer is the same — SimpleQA's "not attempted" bucket exists precisely because a wrong confident answer is worse than no answer[2].
- **The four constraints are a good requirements checklist for a production pipeline** — especially provenance (citable output), which is the Wikimedia-specific value-add (the citation graph is the provenance layer).

### 3.2 Where it needs pushback

1. **It conflates deployment evaluation with benchmark design.** A benchmark is a measurement instrument: standardized, comparable across models, stable over time. Deployment evaluation is acceptance testing: pipeline-specific, cost-weighted. The Wikipedia-AI-Skills question is mostly *benchmark* ("does skill injection help, how much, across task types?") — which requires standardized tasks, ground truth, and statistical power, not just cost accounting. Build both layers: the benchmark produces the capability profile (model × skills); the deployment framework applies cost weights to it. If you only build the cost model, you get scores that change with your workflow and cannot be compared across labs.
2. **"Calibration outranks accuracy" is operationally fragile.** Calibration is measurable for closed-form QA (SimpleQA's ECE)[2] but ill-defined for open-ended agentic tasks: there is no natural confidence score per tool call, and LLM confidence is steerable and unreliable. "Knowing which 70%" cannot be assumed — it must be *measured*, and measurement needs a label space the task may not have. Moreover, the framework's own "hard bound on undetected errors" implies an **accuracy floor**: a well-calibrated 70%-accurate model routed perfectly still fails 30% of the time. The defensible version of the claim: *accuracy above a floor, plus calibration/abstention sufficient to route verification effort*. Without the floor, calibration is decoration. Operational proxies that avoid self-reported confidence: abstention under instruction, self-consistency across samples, and **verification pass rate** (fraction of outputs passing an independent automated check — label-free, measurable, and exactly the "acceptable without review" quantity).
3. **"Inference matters least because LiftWing is free" — only if the free model is above the floor.** Free ≠ adequate. The framework's own ~11.9% fabricated-quote finding suggests the free model may sit *below* the quality floor for some tasks — which is precisely what the benchmark must surface, not assume away. Also, "free" ignores agent-loop costs: token spend inside a multi-step loop, wall-clock, and the fact that the models most editors actually use are commercial frontier models. The benchmark matrix must span LiftWing-hosted *and* frontier models, and report cost per successful item.
4. **"Verification dominates" is pipeline-specific, not a law.** For tasks with cheap automatic verifiers (SPARQL execution, schema checks, counts, diff matching) verification is nearly free and *agent/inference time* dominates. For open-ended tasks (drafting, policy compliance) there is no cheap verifier — human review dominates regardless. The actionable design lever: **engineer verifiability into tasks** (gold answers, deterministic cross-checks, canaries). That is a task-design principle, not a model property — and it's the single most useful thing the framework implies for the suite.
5. **Privacy and volume are pipeline constraints, not benchmark constraints.** Privacy governs *where you run* (WMF-hosted inference for patroller/BLP-adjacent data), not *what you measure* — a public benchmark's tasks must be publishable by construction. Volume (thousands of items) drives statistical power in deployment; a *benchmark* needs task diversity and repeated runs, not item volume (the AB report's n=24 is the cautionary tale, §4). Reproducibility vs. live data is a real tension — resolved by the two-tier design (§5), not by choosing one.

---

## 4. Critical reading of the AB meta-report

### 4.1 What survives

The qualitative findings are plausible, useful hypotheses: skills speedup grows with complexity (2.2× → 3.1×), the "well-known API floor" (well-documented APIs show minimal skills advantage), the four knowledge types (API / data model / conventions / code patterns), and the no-skills "defensive programming" pattern.[1] The **six named silent-failure modes** are the most valuable artifact in the report — they are a ready-made canary/trap layer for the next suite: 48h pageviews lag, recursive-subcategory truncation, navbox-name diversity, fabricated quality labels, canary-event filtering, broken diff parsing.[1]

### 4.2 What doesn't survive scrutiny

- **Sample size.** n=24 total, n=2 per cell, single run each — no variance, no confidence intervals. The observed 6/12 no-skills failure rate has a 95% CI of roughly [25%, 75%]. The skills arm's 0/12 implies (rule of three) an upper bound of **~22%** on the true silent-failure rate — so "reduced silent failure from 50% to 0%" is not supported; the honest claim is "observed 6/12 → observed 0/12, indistinguishable from up to ~1-in-5 at this sample size".
- **No ground truth, no rubric, no blinding.** "Correct" was assessed without a defined scoring rubric, a second judge, or inter-rater reliability. The task definitions were never versioned or frozen, so the suite is not re-runnable and the numbers are not auditable.
- **Timings** are wall-clock on a shared interactive machine; no seed control, no model-version pinning (the skill set itself changed across rounds), no token/API-call cost capture.
- **Task selection** was ad hoc; there is no taxonomy-coverage claim and no negative control (e.g., a task where skills should *not* matter).
- **Not the report's fault alone:** this is the standard weakness of hand-run agent A/Bs everywhere. The fix is mechanical — that's what the proposal automates.

---

## 5. Proposal: WAIS-Bench

### 5.1 Design principles

1. **Verifiers first.** Every task ships with a deterministic or semi-automatic checker: schema validation, count checks, cross-API recomputation (e.g., pageviews vs. SQL replica), diff matching, SPARQL result-set equality, canary presence. LLM-as-judge only where unavoidable (style/policy), with position randomization, ≥2 judges, rubric anchoring, and a measured judge-human agreement reported per task (WebVoyager's ~90% is the bar).[20][22]
2. **Two tiers.** *Gold tier*: frozen inputs over pinned page revisions / snapshot dumps — deterministic, comparable across runs and labs (KILT pattern[3]). *Live tier*: tasks against current APIs (freshness, drift, rate-limit behavior) run with repeated seeds and variance reported (WebVoyager pattern[20]). Gold answers for the live tier are generated by reference implementations, not by the model under test.
3. **The matrix that makes it a skills benchmark:** models (LiftWing-hosted + ≥1 frontier) × interventions (skills-injected / no-skills) × tiers. This is the A/B design of the AB report[1], formalized.
4. **Metric stack (per cell, with CIs):**
   - *Success rate* on gold-verified tasks
   - **Plausible-error rate** — errors that pass automated plausibility checks (the silent-failure detector; the headline metric)
   - *Verification efficiency* — human-review rate at a target undetected-error bound (the framework's KPI, operationalized)
   - *Cost* — tokens, API calls, wall-clock per successful item
   - *Calibration proxies* — abstention under instruction, self-consistency, verification pass rate
5. **Task taxonomy** (AB rounds R1–R4[1] + the verified gaps G1–G9[29][30][31][32]):
   - Reading/single-API (pageviews w/ 48h-lag trap, revisions, categories, SPARQL lookups) — R1
   - Multi-step workflows (content gaps, patrol monitor, citation×quality, structural audit) — R2
   - Cross-domain orchestration (pywikibot, Commons×Wikidata×Wikipedia, cross-language ML, real-time SSE+ML+diffs) — R3
   - **Editing (write-tier, on test.wikipedia.org / beta cluster / self-hosted MediaWiki from a Kiwix dump[21])**: stub drafting, cited edits, vandalism reversion, edit summaries, BLP policy — scored from environment state (revision exists, diff matches, not reverted)[22][12]
   - **SPARQL in an agentic loop**: NL → SPARQL → execute on WDQS → repair on timeout/429 → validate (QALD-style queries[29][30] but live and iterative)
   - **Wikidata editing**: wbeditentity, references (P854/P248), qualifiers, constraint compliance, multilingual labels
   - **Commons media**: categorization, SDC "depicts" (P180), licensing (COM:L), P18 image selection
   - **Technical facilities**: ORES/LiftWing quality scoring, EventStreams monitoring, Toolforge deployment, PageTriage
   - **Long-running stateful** and **multi-agent chains** — the AB report's own Round-4 proposals[1]
6. **Governance.** Tasks and rubrics are community-reviewable (Wikibench model[6]); WikiProject assessment grades as ground-truth sources; read-only default; write tasks only on sandbox/test wikis; UA policy, `maxlag`, rate-limit etiquette encoded as agent constraints (τ-bench policy-guidelines pattern[22]) — and double as realistic constraint tests.
7. **Format for reuse.** Tasks as JSONL (task, environment, ground-truth check, judge rubric) + OpenAPI-style tool specs[26][27] so any harness can ingest them; results as versioned JSONL; a leaderboard table in the repo README, regenerated by a script.

### 5.2 Harness

Recommended stack: **Inspect AI** as the runner (first-class agent loops, tool protocol, per-run scoring, `inspect eval` run-diffs for the A/B)[37] — or LangSmith if tracing UX is preferred — with **promptfoo** as the pragmatic minimal start (YAML variants + assertions + cost in CI)[35]. Reuse RAGAS metrics for grounded-answer slices[42]. Reject lm-eval/HELM (static-prompt only)[40][41]; treat AutoGenBench's deterministic replay as an idea worth stealing[28]. Keep it dependency-light and pytest-verifiable per the repo's conventions.[1]

### 5.3 Phasing

- **Phase 0 — Retrofit.** Convert the 12 AB tasks into task files with verifiers and pinned revision snapshots; make the existing suite re-runnable and auditable. Deliver the regression baseline.
- **Phase 1 — Gold tier.** 12–20 tasks across the taxonomy, deterministic, with the metric stack; matrix 2 models × 2 interventions × ≥5 runs; publish CIs.
- **Phase 2 — Live tier.** Freshness, drift, rate-limit, and canary-trap tasks against current APIs.
- **Phase 3 — Editing tier.** Sandbox wiki; policy/rubric validation; τ-bench-style simulated reviewer.[22]
- **Phase 4 — Community.** Wikibench-style task curation on-wiki; leaderboard; versioned re-runs on a schedule (the repo's cron/watchdog pattern).

### 5.4 Risks / anti-patterns

- **Static-only tasks** → contamination and drift (use FreshTab-style on-the-fly generation for prose/table items)[9].
- **LLM-as-judge without validation** → self-preference/verbosity biases; validate against humans per task and report agreement[20].
- **Live-only tasks** → non-reproducible results; always pair with gold tier.
- **Reproducing the AB report's n=24** → budget for ≥5 runs/cell or state CIs honestly.
- **Hosting the benchmark on lab pages** → sites die (QALD's dead site is the exhibit[30]); repo + Zenodo/HF mirrors + link-checking CI.

---

## Sources

[1] https://raw.githubusercontent.com/fuzheado/Wikipedia-AI-Skills/main/research/ab-testing/AB_TEST_META_REPORT.md
[2] https://arxiv.org/abs/2411.04368
[3] https://arxiv.org/abs/2009.02252
[4] https://arxiv.org/abs/2305.14251
[5] https://arxiv.org/abs/2310.03214
[6] https://arxiv.org/abs/2402.14147
[7] https://arxiv.org/abs/2406.13805
[8] https://arxiv.org/abs/2402.18264
[9] https://arxiv.org/abs/2510.13598
[10] https://arxiv.org/abs/2605.21479
[11] https://arxiv.org/abs/2602.16902
[12] https://arxiv.org/abs/2602.01590
[13] https://arxiv.org/abs/2605.31113
[14] https://arxiv.org/abs/2308.14508
[15] https://arxiv.org/abs/2407.11005
[16] https://arxiv.org/abs/2406.04744
[17] https://github.com/simple-bench/SimpleBench
[18] https://arxiv.org/abs/2305.14292
[19] https://arxiv.org/abs/2311.12983
[20] https://arxiv.org/abs/2401.13919
[21] https://arxiv.org/abs/2307.13854
[22] https://arxiv.org/abs/2406.12045
[23] https://arxiv.org/abs/2407.15711
[24] https://arxiv.org/abs/2306.06070
[25] https://arxiv.org/abs/2504.12516
[26] https://arxiv.org/abs/2305.16504
[27] https://arxiv.org/abs/2304.08244
[28] https://arxiv.org/abs/2308.03688
[29] https://github.com/KGQA/QALD-10
[30] https://github.com/ag-sc/QALD
[31] https://github.com/AskNowQA/LC-QuAD2.0
[32] https://arxiv.org/abs/2007.03875
[33] https://github.com/askplatypus/wikidata-simplequestions
[34] https://github.com/AKSW/LLM-KG-Bench
[35] https://github.com/promptfoo/promptfoo
[36] https://github.com/confident-ai/deepeval
[37] https://github.com/UKGovernmentBEIS/inspect_ai
[38] https://github.com/openai/simple-evals
[39] https://github.com/openai/evals
[40] https://github.com/EleutherAI/lm-evaluation-harness
[41] https://github.com/stanford-crfm/helm
[42] https://github.com/vibrantlabsai/ragas
[43] https://github.com/web-arena-x/webarena
[44] https://github.com/xlang-ai/OSWorld
[45] https://github.com/MinorJerry/WebVoyager
[46] https://diff.wikimedia.org/2025/07/23/making-question-answering-systems-smarter-with-knowledge-graphs-using-frog-a-wikidata-research-fund-2024-highlight
[47] https://diff.wikimedia.org/2026/08/05/notes-from-the-wiki-ai-pre-conference-what-we-already-run-and-what-comes-next
[48] https://arxiv.org/abs/1911.06136
