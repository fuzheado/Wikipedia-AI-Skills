# LLM Benchmarks Grounded in Wikipedia / Wikimedia Knowledge & QA

**Research date:** 2026-08-19 · **Researcher:** HermesAgent subagent (verification via live HTTP fetches, User-Agent `HermesAgent/1.0 benchmark research`)
**Purpose:** Landscape survey for Andrew Lih (Fuzheado) & Lodewijk Gelauff's planned benchmark suite testing LLMs on Wikimedia-relevant tasks (on-wiki editing, MediaWiki APIs, Wikidata SPARQL, Commons, Toolforge, ML services). This file covers topic #1: **benchmarks where Wikipedia is the knowledge source / test material** (knowledge QA, factuality, long-form generation, tables, multi-hop, freshness, RAG, community evaluation).
**Verification mandate:** every entry below was verified against a primary source (arXiv abs page, arXiv API, GitHub API, HuggingFace API/page, or official site) with the HTTP status recorded. Items that could not be verified live are marked **[UNVERIFIED]**.

---

## 1. Landscape overview

Wikipedia is the single most-used knowledge substrate in NLP/LLM benchmarking. Roughly five waves are visible:

1. **Reading comprehension (2015–2019):** SQuAD, WikiQA, TriviaQA, Natural Questions, HotpotQA made Wikipedia articles the corpus for extractive/multi-hop QA, establishing EM/F1 as the default metrics.
2. **Structured data on Wikipedia (2015–2020):** WikiTableQuestions, WikiSQL, TabFact mined Wikipedia's HTML tables for semantic parsing and table entailment.
3. **Knowledge grounding & verification (2017–2021):** FEVER/FEVEROUS (claim verification against Wikipedia), Wizard of Wikipedia (knowledge-grounded dialogue), ELI5 (long-form QA), and KILT — Facebook's attempt to unify eight knowledge-intensive tasks on one Wikipedia snapshot with a shared evidence-retrieval metric (R-precision).
4. **LLM factuality & freshness (2023–2025):** FActScore (atomic fact precision of long-form generation), FreshQA (time-sensitive knowledge), SimpleQA (short-form factuality + calibration), HLE and SimpleBench (frontier-knowledge breadth), WikiContradict (knowledge conflicts), WIKIGENBENCH (full-article generation), FreshTab (contamination-resistant table-to-text generated on the fly from Wikipedia).
5. **RAG, agents & community (2024–2026):** LongBench, RAGBench, CRAG (retrieval-augmented generation; CRAG includes Wikipedia as one of five domains and adds tool-use scoring), Wikibench (community-driven AI-eval data curation **on** Wikipedia), LLM-WikiRace (planning over the Wikipedia hyperlink graph), Wiki Live Challenge (deep-research agents on expert-level Wikipedia articles), TSM-Bench/WETBench (detecting LLM-written text in Wikipedia editing practice).

Notable absences across all waves — and thus the opening for the Wikimedia suite — are **live interaction with the wiki itself** (no benchmark requires editing, MediaWiki API calls, SPARQL against current Wikidata, Commons workflows, or Toolforge operations; see §5 Gaps). Also note: several arXiv IDs circulating for these benchmarks are **wrong** (see §6 verification log); e.g. "WikiBench arXiv:2411.09103" is a physics paper, RAGBench is 2407.11005 (not 2407.11054), CRAG is 2406.04744 (not 2401.12843).

---

## 2. Benchmark table

Legend — sources: arXiv abs page, GitHub API/repo, HF (HuggingFace API), site (official page). Statuses captured 2026-08-19.

| Name | Year | Task format | What it measures | How Wikipedia is used | Scoring method | Source URL (HTTP status) |
|---|---|---|---|---|---|---|
| SQuAD | 2016 | Extractive reading comprehension (span QA) | Passage comprehension, answer extraction | 536 Wikipedia articles as passage corpus (100k+ Qs) | Exact Match (EM), token F1 | https://arxiv.org/abs/1606.05250 (200) |
| WikiQA | 2015 | Open-domain answer-sentence selection | Sentence-level answer retrieval | Bing query logs; answer candidates from Wikipedia (one of first to use wiki-linked answers) | MAP, MRR | https://www.microsoft.com/en-us/research/publication/wikiqa-a-challenge-dataset-for-open-domain-question-answering/ (200); HF microsoft/wiki_qa (200) |
| TriviaQA | 2017 | Multi-document reading comprehension | RC with distant supervision | Trivia questions; evidence from Wikipedia + web; Wikipedia-verified answers | EM, F1 | https://arxiv.org/abs/1705.03551 (200); GitHub mandarjoshi90/triviaqa (200) |
| Natural Questions (NQ) | 2019 | Open-domain QA (long + short answers) | Answering real user queries | Real Google queries answered from Wikipedia pages (300k+ pairs) | F1 (short answers), EM variants | https://github.com/google-research-datasets/natural-questions (200); https://research.google/blog/natural-questions-a-new-corpus-and-challenge-for-question-answerin... (200) |
| HotpotQA | 2018 | Multi-hop QA with supporting facts | Multi-hop reasoning, explainability | English Wikipedia + its hyperlink structure (113k Qs) | EM/F1, joint EM incl. supporting facts | https://arxiv.org/abs/1809.09600 (200); http://hotpotqa.github.io/ (200) |
| WikiSQL | 2017 | Text-to-SQL semantic parsing | NL → SQL over tables | ~80k questions over Wikipedia HTML tables (introduced in Seq2SQL paper) | Logical-form accuracy (execution accuracy in later work) | https://arxiv.org/abs/1709.00103 (200); GitHub salesforce/WikiSQL (200) |
| WikiTableQuestions | 2015 | Compositional semantic parsing over semi-structured tables | Complex multi-step reasoning over tables | 22k questions over 2,108 Wikipedia tables | Denotation accuracy | https://arxiv.org/abs/1508.00305 (200); GitHub ppasupat/WikiTableQuestions (200) |
| TabFact | 2020 | Table-based fact verification | Entailment of statements vs tables | 118k statements over ~16k Wikipedia tables | Binary classification accuracy | https://arxiv.org/abs/1909.02164 (200); GitHub wenhuchen/Table-Fact-Checking (200) |
| ELI5 | 2019 | Long-form QA generation | Long-form answer quality | Reddit ELI5 questions; in KILT the ELI5 task grounds answers in Wikipedia evidence | ROUGE-L, METEOR, human eval | https://arxiv.org/abs/1907.09190 (200); GitHub facebookresearch/ELI5 (200) |
| Wizard of Wikipedia | 2019 | Knowledge-grounded dialogue | Grounded conversation quality | 22k dialogues grounded in Wikipedia sentences | Perplexity, knowledge-selection accuracy | https://arxiv.org/abs/1811.01241 (200); GitHub facebookresearch/ParlAI (200) |
| FEVER | 2018 | Claim verification (fact checking) | Verifying claims against evidence | 185k claims generated from Wikipedia sentences; evidence from Wikipedia | FEVER score (label acc × evidence recall) | https://arxiv.org/abs/1803.05355 (200); https://fever.ai/ (200) |
| FEVEROUS | 2021 | Fact verification over text + tables | Verification with mixed evidence | 87k claims; Wikipedia sentences AND tables as evidence | FEVER score variant | https://arxiv.org/abs/2106.05707 (200); GitHub Raldir/FEVEROUS (200) |
| KILT | 2020 | Unified knowledge-intensive tasks (8 datasets, 5 task families) | Task performance + evidence grounding | All tasks (FEVER, NQ, TriviaQA, HotpotQA, ELI5, WoW, entity linking, slot filling) grounded in **one fixed Wikipedia snapshot** | Task metric + R-precision (evidence retrieval) | https://arxiv.org/abs/2009.02252 (200); GitHub facebookresearch/KILT (200) |
| FActScore | 2023 | Long-form generation factuality | Atomic fact precision | Reference facts about people drawn from Wikipedia; biography generation | FActScore = per-atomic-fact precision | https://arxiv.org/abs/2305.14251 (200); GitHub shmsw25/FActScore (200) |
| FreshQA | 2023 | Time-sensitive QA | Freshness/up-to-dateness of knowledge | Dynamic questions whose answers change; Wikipedia among reference sources | Accuracy split by fast/slow-changing answers | https://arxiv.org/abs/2310.03214 (200); GitHub freshllms/freshqa (200) |
| SimpleQA | 2024 | Short-form factuality QA | Factuality + calibration of short answers | 4,326 curated knowledge questions; answers grounded in authoritative sources (incl. Wikipedia) | Accuracy, calibration (ECE) | https://arxiv.org/abs/2411.04368 (200); GitHub openai/simple-evals (200) |
| Humanity's Last Exam (HLE) | 2025 | Expert-level multiple choice / short answer | Frontier knowledge breadth | ~3,000 expert-authored questions across 100+ subjects (NOT Wikipedia-centric) | Accuracy (per modality), human-normalized | https://arxiv.org/abs/2501.14249 (200); GitHub centerforaisafety/hle (200); HF cais/hle (200) |
| SimpleBench | 2024 | Short-answer factuality across ~10 domains | Knowledge + reasoning robustness | Diverse knowledge questions; Wikipedia-related content is a subset | Accuracy | https://github.com/simple-bench/SimpleBench (200) — no arXiv found |
| WikiContradict | 2024 | Knowledge-conflict QA | Detecting/answering under contradictory info | Real-world conflicts mined from Wikipedia's own editing history (article vs. its past/reverted versions) | Accuracy on conflict & non-conflict splits | https://arxiv.org/abs/2406.13805 (200) |
| WIKIGENBENCH | 2024 | Full-length Wikipedia article generation | Long-form generation + factual accuracy | Real Wikipedia articles as targets (real-world scenario incl. structure/citations) | Factual accuracy, structure/style metrics | https://arxiv.org/abs/2402.18264 (200) |
| FreshTab | 2025 | Table-to-text generation (on-the-fly) | Contamination-resistant table insight generation | Tables scraped from Wikipedia **on demand** (multilingual, e.g. German) to dodge LLM training-data contamination | Text-quality + faithfulness metrics | https://arxiv.org/abs/2510.13598 (200) |
| WikiVQABench | 2026 | Knowledge-grounded visual QA (VQA) | Multimodal knowledge reasoning | Wikipedia + Wikidata images & knowledge beyond the pixels | VQA accuracy | https://arxiv.org/abs/2605.21479 (200) |
| LongBench | 2023 | Long-context understanding (21 tasks) | Long-context retrieval & reasoning | Includes Wikipedia-derived multi-doc QA subsets (e.g. MultiFieldQA, 2WikiMultihopQA) | Task-specific (F1, ROUGE, accuracy) | https://arxiv.org/abs/2308.14508 (200); GitHub THUDM/LongBench (200) |
| RAGBench | 2024 | RAG component benchmark (retriever/generator/judge) | Faithfulness, answer/context relevancy, toxicity | 100k+ examples over 10 public RAG datasets incl. Wikipedia-sourced HotpotQA/TriviaQA/FEVER | RAGAS-style metrics | https://arxiv.org/abs/2407.11005 (200) |
| CRAG | 2024 | RAG QA + tool use (KDD Cup 2024) | Answer correctness + tool-use quality (web search vs. knowledge base) | Wikipedia is one of 5 domains (with Finance, Sports, Music, Movies) | Accuracy + tool-call correctness | https://arxiv.org/abs/2406.04744 (200); GitHub facebookresearch/CRAG (200) |
| Wikibench | 2024 | Community-driven AI-eval data curation | How communities co-create AI eval data | **On Wikipedia**: workflow for editors to curate evaluation datasets for Wikipedia-related AI tasks | Crowd agreement / task accuracy | https://arxiv.org/abs/2402.14147 (200) |
| LLM-WikiRace | 2026 | Agentic planning over knowledge graph | Multi-step look-ahead planning | Navigate Wikipedia hyperlink graph from source to target page | Success rate, avg. steps, planning depth | https://arxiv.org/abs/2602.16902 (200) |
| Wiki Live Challenge | 2026 | Deep-research agent evaluation | Expert-level research + answer quality | Expert-level questions tied to current Wikipedia articles; expert judges | Expert-judged answer quality | https://arxiv.org/abs/2602.01590 (200); GitHub WangShao2000/Wiki_Live_Challenge (200) |
| TSM-Bench | 2026 | Machine-generated-text detection | Detecting LLM-written text in real editing practice | Wikipedia edit histories (real-world editing contexts) | Detection F1 / AUC / accuracy | https://arxiv.org/abs/2605.31113 (200) |

---

## 3. Per-benchmark notes

**SQuAD** — The benchmark that made Wikipedia the default reading-comprehension corpus. Its weakness (answerable, span-extractable questions only; no unanswerable cases until SQuAD 2.0) is a lesson for any wiki QA design: real wiki queries are noisy, open-ended, and often unanswerable from one page.

**WikiQA** — Early open-domain QA using Bing queries with Wikipedia-linked answers; one of the first to pair real user queries with wiki evidence. No arXiv version (verified via MSR page + HF). Old (2015) but historically important; too easy/saturated for modern LLMs.

**TriviaQA** — Distantly supervised from trivia websites with Wikipedia + web evidence. Introduced the "answer present in wiki but hard to locate" regime. Still widely used as a RAG probe (also inside RAGBench and LongBench).

**Natural Questions** — Real Google queries with Wikipedia answers; long (paragraph) and short (span) answer variants. The TACL 2019 paper has no arXiv; GitHub repo is the canonical source. Its user-query flavor is the closest classic analogue to "what do people actually ask about Wikipedia content".

**HotpotQA** — Multi-hop QA exploiting Wikipedia's hyperlink structure for gold reasoning chains ("supporting facts"). The joint EM (answer + facts) metric is the template for "did the model actually use the right source" — directly transferable to Wikimedia citation/reference checks.

**WikiSQL / WikiTableQuestions / TabFact** — The table trilogy. WikiSQL (NL→SQL) and WTQ (denotation) mine Wikipedia HTML tables; TabFact verifies statements against them. Together they show Wikipedia's tables are a rich, under-exploited structured-data surface — a gap the Wikimedia suite can fill with *live* table extraction and current articles.

**ELI5** — Reddit long-form QA (not Wikipedia-authored), but KILT re-grounds it with Wikipedia evidence, making it a good "explain-like-I'm-five a Wikipedia topic" analogue. Long-form evaluation remains hard (ROUGE is weak); FActScore-style atomic decomposition is the modern fix.

**Wizard of Wikipedia** — Knowledge-grounded dialogue where every utterance is tied to a Wikipedia sentence; measures both fluency (perplexity) and knowledge selection accuracy. The retrieval-vs-generation separation is a useful scoring pattern.

**FEVER / FEVEROUS** — Claim-verification benchmarks built by mutating Wikipedia sentences into claims. FEVER score (label accuracy × evidence recall) is the canonical "right answer AND right evidence" metric. FEVEROUS adds tables. Both are the backbone of fact-checking evals and are heavily reused in RAG/faithfulness research (VitaminC, 2103.08541, is a Wikipedia-based variant with contrastive evidence).

**KILT** — The most important architectural template for the Wikimedia suite: **one fixed Wikipedia snapshot, many tasks, a shared evidence metric**. KILT's R-precision (retrieval precision of gold evidence among the model's retrieved passages) is exactly the "did you ground this in the right page/revision" idea the Wikimedia suite needs — but KILT's snapshot is frozen and its tasks are all *read-only*.

**FActScore** — Decomposes long-form generations into atomic facts and scores precision per fact. Used heavily for biography generation grounded in Wikipedia. The atomic-fact decomposition is the strongest available tool for scoring wiki-style writing (articles, DYK summaries, talk-page contributions).

**FreshQA** — 600 questions with answers that change over time (fast vs slow changing); measures whether models know *current* facts. Directly motivates the Wikimedia suite's freshness angle: Wikipedia's edit stream is the world's largest continuously updated knowledge source — a live-versioned benchmark is uniquely possible there.

**SimpleQA** — OpenAI's 4,326 short-fact questions with a strict "simple, unambiguous answer" design and a calibration component. Its design principle — answers must be verifiable against authoritative sources (Wikipedia heavily overlaps) — is a good fit for auto-scored Wikimedia QA.

**HLE / SimpleBench** — Frontier-knowledge breadth benchmarks. HLE (~3,000 expert questions, 100+ subjects) is deliberately hard; SimpleBench (GitHub-only, no arXiv found) targets factuality of short answers. Neither is Wikipedia-centric; include as context, not as models for the Wikimedia suite.

**WikiContradict** — Uses Wikipedia's own edit history to build *real* knowledge-conflict scenarios (article vs. contradicted versions). Novel and directly transferable: the Wikimedia suite can generate conflict/contradiction items from live article histories (and from cross-language disagreement).

**WIKIGENBENCH** — Full-length Wikipedia article generation "under real-world scenario" (structure, infoboxes, citations). Closest existing work to "write a Wikipedia article", but it only scores text — it does not check whether the output would survive on-wiki (revert risk, NPOV, citation validity). That is the gap the editing-side suite fills.

**FreshTab** — Table-to-text generated **on the fly from Wikipedia**, explicitly to dodge training-data contamination; multilingual (German experimented). The "generate items on demand, don't ship a static split" idea is a best practice for any long-lived Wikimedia benchmark.

**WikiVQABench** — 2026 VQA benchmark requiring knowledge from Wikipedia + Wikidata beyond image pixels. Notable as the first entry to *explicitly combine Wikipedia text with Wikidata structured knowledge* — a bridge toward the Wikidata SPARQL tasks the Wikimedia suite wants.

**LongBench** — 21 long-context tasks (English/Chinese); Wikipedia-derived subsets included. Its lesson: long-context eval on Wikipedia text is about *finding the needle* in long documents — relevant to full-article context windows.

**RAGBench** — RAG pipeline evaluation (faithfulness, relevancy, toxicity) over 10 datasets including Wikipedia-based ones. Provides ready-made rubric definitions (RAGAS) the Wikimedia suite can reuse for "did the model answer from the right wiki pages".

**CRAG** — KDD Cup 2024; 5 domains incl. Wikipedia; the first RAG benchmark to score **tool-use behavior** (when to call web search vs. answer from knowledge base) alongside answer accuracy — a step toward agentic scoring, though its "tool" is generic search, not MediaWiki.

**Wikibench** — Community-driven data curation *on* Wikipedia: lets editors shape AI-evaluation datasets for their own community. Conceptually the closest relative to the Wikimedia suite's philosophy — evaluation built with, not just about, the Wikimedia community. (Do not confuse with the 2009 "WikiBench" web-app performance benchmark of the same name.)

**LLM-WikiRace** — Turns the WikiRace game into a planning benchmark: navigate Wikipedia hyperlinks from source to target with limited lookahead. Measures planning over a real knowledge graph; a nice bridge into navigation/agentic tasks on wiki infrastructure.

**Wiki Live Challenge** — 2026; deep-research agents answer expert-level questions grounded in current Wikipedia articles, judged by experts. Shows the live-article-as-task-generator pattern (fresh, contamination-resistant, expert-scored).

**TSM-Bench / WETBench** — 2026/2025 benchmarks for detecting LLM-generated text in real Wikipedia editing practices. Relevant as *guardrail* evaluations (patrolling, edit-filtering) for the editing side of the Wikimedia suite, and to the "silent failure" measurement Andrew's A/B work cares about.

---

## 4. Adjacent / partially relevant (not in main table)

- **MMLU** (arXiv 2009.03300, 200) — exam-style MCQ breadth; not Wikipedia-grounded; useful as a baseline comparison point, not a model.
- **TruthfulQA** (arXiv 2109.07958, 200) — imitative falsehoods; partially overlaps Wikipedia content; scoring via GPT-judge.
- **PopQA** — long-tail entity QA: questions built from **Wikipedia entities**, answers from **Wikidata** — the cleanest existing Wikipedia→Wikidata bridge benchmark. ICLR 2023; **no arXiv found**; data verified at GitHub AlexTMallen/adaptive-retrieval (200, README mentions PopQA + Wikipedia).
- **TimeQA** — temporal QA from Wikipedia knowledge updates (NeurIPS 2021); **no arXiv found**; repo GitHub wenhuchen/Time-Sensitive-QA (200).
- **VitaminC** (arXiv 2103.08541, 200) — Wikipedia-based fact verification with contrastive evidence.
- **WebQuestionsSP** — complex KG QA over Freebase (NAACL 2018; no arXiv; DOI 10.18653/v1/n18-1059 verified via Crossref, 200). Precursor of Wikidata SPARQL QA; Freebase is dead — Wikidata is its live successor.
- **LC-QuAD** — complex QA over **Wikidata with SPARQL queries** (ESWC 2017; DOI 10.1007/978-3-319-68204-4_22 verified via Crossref, 200; repo GitHub AskNowQA/LC-QuAD 200). The closest thing to a "Wikidata SPARQL for LLMs" benchmark — but it predates LLMs and is a static corpus, not a live-endpoint eval. **QALD series** (QALD-9 et al.) similar; **[UNVERIFIED]** from this network. **SimpleQuestions-Wikidata** **[UNVERIFIED]** (repo guesses 404).
- **FIB** (arXiv 2211.08412, 200; repo r-three/fib 200) — factual-consistency of long-form generation, but built on **news** summarization, not Wikipedia; include only as a metric pattern.
- **WikiAutoGen** (arXiv 2503.19065, 200) — multimodal Wikipedia-style article generation eval; read-only scoring, no live wiki interaction.
- **HelloFresh** (arXiv 2406.03428, 200) — LLM evals on streams of real human editorial actions incl. Wikipedia; adjacent to the editing topic.
- **"Wikimedia data for AI: a review of Wikimedia datasets for NLP tasks and AI-assisted editing"** (arXiv 2410.08918, 200) — **key reference paper** for the suite: catalogs Wikimedia datasets usable for NLP/AI eval and AI-assisted editing.
- **"Wikipedia in the Era of LLMs: Evolution and Risks"** (arXiv 2503.02879, 200; repo HSM316/LLM_Wikipedia) — analysis of LLM impact on Wikipedia; context for motivation.
- **TiC-LM** (arXiv 2504.02107, 200; repo apple/ml-tic-lm) — web-scale **time-continual pretraining** benchmark from 114 Common Crawl dumps (not Wikipedia); relevant to the freshness/update angle only.
- **EntityQuestions** — open-domain QA over Wikipedia entities, frequently cited; **[UNVERIFIED]** — no primary source reachable from this network (arXiv search returned nothing; Google repo path 404). Do not cite without checking.
- **OKBench** (arXiv 2511.08598, 200) — automated on-demand open-knowledge benchmark generation; methodologically interesting (auto-generate eval items to dodge contamination).
- **LakeQA** (arXiv 2606.10460, 200) — QA over a million-scale data lake incl. Wikipedia tables.
- **CRAG-MM** (arXiv 2510.26160, 200) — multimodal multi-turn extension of CRAG.

---

## 5. Lessons for a Wikimedia LLM benchmark suite (what to copy)

1. **Ground every task in a pinned data version.** KILT's fixed-snapshot design is the gold standard for reproducibility; a Wikimedia suite can go further — pin *page revisions* (not just a dump date) and record them in the eval harness. Track which revision each prompt was built from, and re-run scores when data moves.
2. **Score outcome AND evidence, jointly.** FEVER score, KILT R-precision, and HotpotQA joint-EM all penalize "right answer, wrong source." For Wikimedia: does the model answer from the *right page/revision*, and can it cite it correctly? This maps directly onto FActScore-style atomic fact decomposition for article writing.
3. **Design for contamination resistance from day one.** FreshTab (on-the-fly item generation), WIKIGENBENCH (real-world scenario), Wiki Live Challenge (live articles), and OKBench (auto-generated items) are the current best practices. Static dumps of Wikipedia text rot in two ways: models memorize them, and Wikipedia itself changes. Generate/refresh items programmatically from live APIs.
4. **Freshness is a first-class axis.** FreshQA and WikiContradict show that "stale knowledge" and "contradictory knowledge" are separate failure modes. Wikipedia's edit stream lets the suite build a *versioned temporal* benchmark no static corpus can: ask about a page before/after a notable edit.
5. **Measure tool/action quality, not just final answers.** CRAG's tool-call scoring and LLM-WikiRace's step counting are the templates for agentic evaluation (SPARQL query validity, API call correctness, edit quality) — the Wikimedia suite should score the *actions*, not just the output text.
6. **Let the community curate.** Wikibench demonstrates community-driven eval-data curation on Wikipedia works; the Wikimedia suite should recruit editors/Wikimedians (the parent project's natural audience) as labelers/judges — this also builds legitimacy for the eval results.
7. **Reuse mature metric/rubric machinery.** RAGAS rubrics (RAGBench), FEVER score, FActScore atomic decomposition, and ECE calibration (SimpleQA) are off-the-shelf and can be applied to wiki-flavored tasks rather than reinventing scoring.
8. **Involve the multimodal/structured surfaces.** WikiVQABench (Commons-style images + Wikidata), TabFact/FreshTab (tables) show Wikipedia's non-prose content is under-tested — the suite should cover infoboxes, tables, categories, and images, not just article prose.
9. **Track LLM-text-detection as a guardrail metric.** TSM-Bench/WETBench give methodology for detecting model-written text in editing pipelines — directly relevant to the "silent failure" rate Andrew's A/B tests measured (if a model's edit is indistinguishable from human writing, detection can't catch failures; the suite needs explicit edit-quality checks instead).

---

## 6. Gaps — what NONE of these benchmarks cover (the Wikimedia suite's opening)

1. **On-wiki editing.** No benchmark requires *producing a valid edit*: wikitext syntax, templates, infoboxes, citations (CS1/CS2), section structure, or category placement. WIKIGENBENCH generates article text but never validates it against wiki rules; TSM-Bench/WETBench only *detect* AI text; none score whether an edit would survive (revert risk, NPOV/BLP/notability compliance).
2. **MediaWiki API interaction.** No benchmark calls the Action API / REST API to fetch pages, diffs, search, or metadata. All existing benchmarks hand the model pre-sliced passages — none test API fluency (params, tokens, continuation, rate limits).
3. **Live Wikidata SPARQL.** Closest analogs (LC-QuAD, QALD, WebQuestionsSP) are static corpora over Freebase/old Wikidata snapshots; none evaluate live SPARQL query generation/execution against the current endpoint, and none test Wikidata *schema* reasoning (properties, qualifiers, ranks, references).
4. **Agentic action on live infrastructure.** CRAG scores tool use but only generic web search; nothing exercises Toolforge, bot frameworks (Pywikibot), or live ML services (ORES/RevisionScoring, LiftWing, Wikitext parser).
5. **Commons / multimedia workflows.** WikiVQABench uses images as *input*; no benchmark covers upload flows, licensing/attribution (CC BY-SA), SDC structured data, thumbnails, or file-format handling.
6. **Edit-quality and patrolling metrics.** No benchmark scores edits by revert rate, survival, patroller acceptance (PageTriage), or policy compliance — yet these are the most operationally meaningful signals for an editing-agent eval, and they are directly measurable via the API.
7. **Multilingual and cross-wiki consistency.** Nearly all entries are English-only; Wikipedia's 300+ languages, interwiki links, and cross-language contradictions (cf. WikiContradict) are untested, despite "Wikimedia data for AI" (2410.08918) documenting the availability of multilingual datasets.
8. **Community norms & safety.** Nothing tests copyright compliance, COI editing, vandalism/revert behavior, or policy-grounded refusal — table stakes for a production editing assistant.
9. **Versioned/temporal reasoning with live data.** FreshQA is static; a suite that queries the live wiki's revision history (as of date X, what did the page say?) has no precedent.
10. **Benchmark maintenance as a service.** Existing benchmarks ship once and rot (NQ/HotpotQA snapshots are 2016–2018). A Wikimedia benchmark can be *continuously versioned, re-scored, and re-published* — no other benchmark ecosystem has that property.

---

## 7. Verification log (live fetches, 2026-08-19, UA `HermesAgent/1.0 benchmark research`)

**arXiv abs pages — HTTP 200 (title matched):**
1606.05250 SQuAD · 1705.03551 TriviaQA · 1809.09600 HotpotQA · 1803.05355 FEVER · 1907.09190 ELI5 · 1811.01241 Wizard of Wikipedia · 1508.00305 WikiTableQuestions · 1709.00103 Seq2SQL (introduces WikiSQL) · 1909.02164 TabFact · 2009.02252 KILT · 2305.14251 FActScore · 2310.03214 FreshQA (repo link freshllms/freshqa) · 2411.04368 SimpleQA · 2501.14249 HLE · 2308.14508 LongBench · 2406.04744 CRAG (repo facebookresearch/CRAG) · 2407.11005 RAGBench (found via arXiv API ti:"RAGBench") · 2106.05707 FEVEROUS · 2211.08412 FIB (repo r-three/fib) · 2103.08541 VitaminC · 2402.14147 Wikibench · 2402.18264 WIKIGENBENCH · 2406.13805 WikiContradict · 2510.13598 FreshTab · 2602.01590 Wiki Live Challenge (repo WangShao2000/Wiki_Live_Challenge) · 2602.16902 LLM-WikiRace · 2605.21479 WikiVQABench · 2605.31113 TSM-Bench · 2507.03373 WETBench · 2503.19065 WikiAutoGen · 2009.03300 MMLU · 2109.07958 TruthfulQA · 2410.08918 Wikimedia-data-for-AI review · 2503.02879 Wikipedia-in-Era-of-LLMs · 2504.02107 TiC-LM · 2511.08598 OKBench · 2606.10460 LakeQA · 2510.26160 CRAG-MM · 2406.03428 HelloFresh

**arXiv IDs checked and found to be WRONG (do not reuse):**
2411.09103 (physics paper — the "WikiBench" ID from the task brief is a misattribution) · 2401.12843 (temporal graphs — not CRAG) · 2407.11054 (health-tech — not RAGBench) · 1507.02326 (math — not WikiQA) · 2301.00727 (MR microscopy — not PopQA) · 2105.06337 (Grad-TTS — not EntityQuestions) · 2106.15357 (adversarial training — not FEVEROUS) · 1508.01675 (physics — not WebQuestionsSP) · 1603.05475 (math — not SimpleQuestions-Wikidata) · 1812.09468 (astronomy — not LC-QuAD 2.0) · 2311.08448 (astronomy — not FIB) · 2105.15348 (404) · 2108.14111 (404 — not TimeQA). No arXiv paper found for: WikiQA, Natural Questions, PopQA, TimeQA, WebQuestionsSP, LC-QuAD, SimpleBench, EntityQuestions.

**GitHub API — 200:** google-research-datasets/natural-questions · mandarjoshi90/triviaqa · facebookresearch/KILT · hotpotqa/hotpot · salesforce/WikiSQL · ppasupat/WikiTableQuestions · wenhuchen/Table-Fact-Checking · facebookresearch/ELI5 · facebookresearch/ParlAI · openai/simple-evals · simple-bench/SimpleBench (215 stars) · shmsw25/FActScore · facebookresearch/CRAG · THUDM/LongBench · centerforaisafety/hle · AlexTMallen/adaptive-retrieval (PopQA; README mentions PopQA+Wikipedia) · wenhuchen/Time-Sensitive-QA (TimeQA) · Raldir/FEVEROUS · AskNowQA/LC-QuAD · hendrycks/test (MMLU) · sylinrl/TruthfulQA · google-research/language · stanford-crfm/helm · freshllms/freshqa (link extracted from arXiv page)
**GitHub API — 404 (wrong guesses; alternatives found):** reworkd/SimpleBench (moved → simple-bench/SimpleBench) · wikibench-ai/WikiBench · langchain-ai/crag (→ facebookresearch/CRAG) · google-deepmind/fresh-llms (→ freshllms/freshqa) · cais/hle (→ centerforaisafety/hle) · FeverBenchmark/FeverBaselines (→ fever.ai site) · sheffieldnlp/feverous (→ Raldir/FEVEROUS) · stanfordnlp/SimpleQuestions-Wikidata · WebQuestionsSP/WebQuestionsSP · google-research-datasets/entity-questions · uwdata/wikibench · google-research/language entity_questions dir (404)

**Sites — 200:** http://hotpotqa.github.io/ · https://fever.ai/ · https://research.google/blog/natural-questions-a-new-corpus-and-challenge-for-question-answerin... · https://www.microsoft.com/en-us/research/publication/wikiqa-a-challenge-dataset-for-open-domain-question-answering/ · https://crfm.stanford.edu/helm/

**HuggingFace API — 200 (canonical redirects shown):** squad→rajpurkar/squad · wiki_qa→microsoft/wiki_qa · wikisql→Salesforce/wikisql · tab_fact→wenhu/tab_fact · eli5→defunct-datasets/eli5 · fever→fever/fever · hotpot_qa→hotpotqa/hotpot_qa · trivia_qa→mandarjoshi/trivia_qa · natural_questions→google-research-datasets/natural_questions · LongBench→zai-org/LongBench · cais/hle
**HuggingFace — HTTP 401 (blocked/rate-limited from this network; entries verified via arXiv/GitHub instead):** facebook/kilt · OpenAI/SimpleQA · UnknownDomain/crag · ragbench/RAGBench · google-deepmind/freshqa · wizard_of_wikipedia · wiki_table_questions. HF pages 404: wizard_of_wikipedia, wiki_table_questions (wrong names).

**Blocked/limited during research:** arXiv export API — 429 on first bursts, recovered with 6–8s pacing; arXiv HTML search — 429 after ~5 rapid queries; Semantic Scholar API — 429 (unusable after first query); DuckDuckGo HTML — HTTP 202 bot-check. Google/Bing/DDG search not used (bot-blocked per brief). Crossref API — 200 (used to verify WebQuestionsSP DOI 10.18653/v1/n18-1059 and LC-QuAD DOI 10.1007/978-3-319-68204-4_22).
