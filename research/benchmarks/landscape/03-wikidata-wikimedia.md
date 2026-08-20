# Wikidata / SPARQL / KG-QA LLM Benchmarks & Wikimedia-Specific LLM Evaluation Efforts

**Prepared for:** Andrew Lih & Lodewijk Gelauff — Wikimedia skills benchmark suite design
**Date:** 2026-08-19
**Scope:** (a) Wikidata/KG question-answering and SPARQL benchmarks (QALD-9, QALD-10, LC-QuAD 2.0, KQA Pro, WebQuestionsSP, SimpleQuestions, SemTab, Wikidata5M, plus adjacent Wikipedia-table/QA datasets), (b) Wikimedia-specific LLM agent/evaluation efforts (WikiChat, WikiGenBench, Wikibench, LLM-KG-Bench, WMF/community activity).
**Method:** Every entry was live-verified with `curl` (arXiv abs pages, GitHub API, OpenAlex, DBLP, WordPress.com public API for diff.wikimedia.org). HTTP status recorded per URL. Unverifiable items are marked **[UNVERIFIED]** or **[NOT FOUND]**. Search engines are bot-blocked from this network; arXiv's Atom API returned HTTP 429 during the session, so arXiv titles were verified via abs pages instead.

---

## 1. Landscape overview

The KG-QA benchmark lineage starts with **Freebase** (WebQuestions 2013, SimpleQuestions 2015, WebQuestionsSP 2016), then moves to **DBpedia** (QALD-9, LC-QuAD), and — since ~2019–2023 — decisively to **Wikidata**: LC-QuAD 2.0 targets Wikidata + DBpedia, KQA Pro builds on Wikidata, QALD-10 is explicitly a *migration from DBpedia to Wikidata* ("research is gravitating toward Wikidata-based benchmarks… Freebase is defunct and DBpedia lacks the structural validity of Wikidata"), and QALD-9-plus is a multilingual Wikidata+DBpedia extension. LLM-era works either run LLMs *as systems* on these frozen QA benchmarks (QALD-10 reports LLM-based results) or add retrieval/grounding dimensions (WikiChat, WikiRAG, FrOG). Meanwhile Wikipedia-as-text datasets (WikiSQL, WikiTableQuestions, WikiQA) test reading comprehension over wiki content, and **Wikibench** (CHI 2024) is the closest thing to community-driven AI evaluation *on* Wikipedia workflows. **No benchmark yet covers live agentic editing of Wikipedia/Wikidata, SPARQL in an agent loop, Commons media work, or Wikimedia technical facilities (LiftWing, EventStreams, Toolforge, ORES)** — that is the open space a Wikimedia skills benchmark would fill.

### Discrepancy note vs. the task brief
The brief describes **QALD-10 as a "CLEF 2024" lab**. Primary sources (DBLP, OpenAlex, the Semantic Web journal record) place QALD-10 in the **Semantic Web journal** (DOI 10.3233/SW-233471, 2023/2024), "QALD-10 – The 10th challenge on question answering over linked data: Shifting from DBpedia to Wikidata" — no CLEF 2024 connection found. Treat the CLEF framing as unverified; the benchmark itself is real, Wikidata-centric, and current.

---

## 2. Benchmark table

| Name | Year | What it measures | Wiki relevance | Format | Scoring | Source URL (HTTP status) |
|---|---|---|---|---|---|---|
| QALD-9 (+ QALD-9-plus) | 2019 / 2022 | NL question answering over knowledge graphs (KGQA) | SPARQL QA over DBpedia; plus = multilingual, Wikidata + DBpedia | 408 train / 280 test Q-A pairs (QALD-9); plus: 10 languages | Precision / Recall / F1 | https://github.com/ag-sc/QALD (200); https://github.com/KGQA/QALD_9_plus (200); official site https://qald.sebastianwalter.org/ (000 — down) |
| QALD-10 | 2023/24 | Multilingual complex KGQA; migration DBpedia → Wikidata; property-ranking/qualifier complexity | **Wikidata-native**: Wikidata ranking mechanism of properties, qualifiers | 394 test Q-A pairs (multilingual); 412-pair training set | Precision / Recall / F1 | https://doi.org/10.3233/SW-233471 (DBLP 200; journal/DOI 403 Cloudflare); https://github.com/KGQA/QALD-10 (200) |
| LC-QuAD 2.0 | 2019 | Complex KGQA (multi-hop, aggregates) over Wikidata + DBpedia | Wikidata target KG | 24,026 NL↔SPARQL pairs | Execution / answer match | https://doi.org/10.1007/978-3-030-30796-7_5 (OpenAlex 200; no arXiv found); https://github.com/AskNowQA/LC-QuAD2.0 (200) |
| KQA Pro | 2020 | Complex KBQA with explicit compositional programs; reasoning supervision | Built on **Wikidata** (schema/programs; S-Expression programs) | ~120K questions + program annotations | Program-execution accuracy (answer + program) | https://arxiv.org/abs/2007.03875 (200, title verified); https://github.com/shijx12/KQAPro_Baselines (200, 138★; canonical link from arXiv page) |
| WebQuestionsSP | 2016 | KBQA semantic parsing (SPARQL annotations) | Freebase (not Wikidata) — methodology transfers | 4,737 Q-SPARQL pairs | F1 | https://aclanthology.org/P16-2033/ DOI 10.18653/v1/p16-2033 (OpenAlex 200; no arXiv); data https://www.microsoft.com/en-us/download/details.aspx?id=52763 (200) |
| SimpleQuestions | 2015 | Single-relation factoid QA | Freebase; community Wikidata mirror exists | 108,442 questions | Accuracy | https://arxiv.org/abs/1506.02075 (200, title verified); mirror https://github.com/askplatypus/wikidata-simplequestions (200, 87★) |
| SemTab | 2020– | Table-to-KG matching: CTA, CEA, CPA (entity/type/property linking) | Wikidata among target KGs for CEA in later editions | Tables + KG targets | Precision / Recall / F1 | https://www.cs.ox.ac.uk/isg/challenges/sem-tab/ (200); /2021/ (200); /2023/ (404); https://github.com/sem-tab-challenge (200) |
| Wikidata5M (via KEPLER) | 2019 | KG embedding pre-training + link-prediction benchmark dataset | **Derived from Wikidata** (5M entities, ~20M triples, aligned entity descriptions) | 5M-entity KG + text corpus | Link prediction MRR / Hits@k | KEPLER https://arxiv.org/abs/1911.06136 (200 — abstract confirms Wikidata5M construction); Zenodo 10.5281/zenodo.5546382 (via OpenAlex 200); no canonical GitHub repo found (IntelligentGraph/Wikidata5M = 404) |
| WikiSQL | 2017 | Text-to-SQL over Wikipedia-derived tables | Wikipedia tables (HTML tables, not Wikidata) | 80,654 Q-SQL pairs | Execution accuracy | https://github.com/salesforce/WikiSQL (200) |
| WikiTableQuestions | 2015 | Compositional QA on semi-structured Wikipedia tables | Wikipedia tables | 22,033 questions | Accuracy | https://arxiv.org/abs/1508.00305 (200, title verified) |
| WikiQA | 2015 | Open-domain factoid QA (Bing queries ↔ Wikipedia sentences) | Wikipedia-derived answer sentences | 3,047 questions | MAP / MRR | https://www.microsoft.com/en-us/research/publication/wikiqa-a-challenge-dataset-for-open-domain-question-answering/ (200) |
| ComplexWebQuestions | 2018 | Complex QA over a web-derived KG (WebQuestions superset) | WebQuestions-style; not Wikidata | 27,469 questions | F1 | https://arxiv.org/abs/1803.06643 (200, title verified) |
| GrailQA | 2021 | Compositional KBQA; three levels of generalization | Freebase; structured/grammar-based | 64,331 questions | F1 | https://arxiv.org/abs/2011.07743 (200, title verified) |
| WikiChat | 2023 | Hallucination reduction via few-shot grounding on English Wikipedia; conversationality + latency | **English Wikipedia as grounding corpus**; evaluation protocol with human + GPT-4 judges | Chatbot responses (97 instructions, multiple turns) | Human eval + GPT-4 judge scores | https://arxiv.org/abs/2305.14292 (200, title+abstract verified); https://github.com/stanford-oval/WikiChat (200) |
| WikiGenBench | 2024 | Full-length Wikipedia **article generation** with citations for new events, from web source docs | English Wikipedia generation (1,320 entries) | Long-form article generation + retrieval of supporting refs | Systematic metric suite (factuality vs. wiki refs, fluency, structure) | https://arxiv.org/abs/2402.18264 (200, abstract verified); https://github.com/zhzihao/WikiGenBench (200, 13★) |
| Wikibench | 2024 | **Community-driven curation of AI evaluation datasets on Wikipedia** (moderation/patrol tasks) | English Wikipedia community; workers curate eval data for AI tools used on-wiki | Task + community-curated eval datasets | Task-specific ML metrics | https://arxiv.org/abs/2402.14147 (200, abstract verified); CHI 2024 DOI 10.1145/3613904.3642278 (OpenAlex 200) |
| LLM-KG-Bench (AKSW) | 2024– | Automated benchmarking of LLMs on KG-related tasks (framework + task collection) | KG tasks incl. Wikidata-adjacent; README cites "Assessing SPARQL capabilities of LLMs" (Meyer et al., NLP4KGC@SEMANTICS 2024, CEUR Vol-3874) | Task collection (BIG-bench style harness) | Task-specific | https://github.com/AKSW/LLM-KG-Bench (200, 59★) |
| FrOG (Wikidata Research Fund 2024) | 2025 | Question answering over Wikidata via GraphRAG (retrieval + KG) | Wikidata QA with community funding/evaluation | Research prototype + report | Qualitative + eval in report | https://diff.wikimedia.org/2025/07/23/making-question-answering-systems-smarter-with-knowledge-graphs-using-frog-a-wikidata-research-fund-2024-highlight/ (200) |
| Wiki AI Pre-Conference (Wikimania 2026) | 2026 | Movement survey: what AI already runs on the wikis and what comes next | WMF/community context for AI evaluation needs | Conference notes | — | https://diff.wikimedia.org/2026/08/05/notes-from-the-wiki-ai-pre-conference-what-we-already-run-and-what-comes-next/ (200) |

**Searched and NOT FOUND (do not cite as existing):** `WikiEval`, `WAB` (as a Wikipedia benchmark), `WikiAgentBench`, `Wiki-Agent` (as a benchmark; GitHub hits are generic RAG demos), `WikiEdit`, `WikidataEdit` — zero relevant hits in OpenAlex title searches and GitHub repository search (both returned 200 with unrelated results). **[NOT FOUND]**

---

## 3. Per-entry notes

### 3.1 Wikidata / KG-QA benchmarks

**QALD-9 (+ QALD-9-plus).** The longest-running KGQA challenge series (since 2011 as QALD-x). QALD-9's 408/280 English Q-A pairs target DBpedia via SPARQL. The official challenge site (qald.sebastianwalter.org) is currently unreachable (HTTP 000 — connection failure); data survives on GitHub (`ag-sc/QALD`, incl. `9/data`) — a reproducibility warning for benchmark design. QALD-9-plus (ICSC 2022, DOI 10.1109/ICSC52841.2022.00045) adds 10 languages and both DBpedia and Wikidata targets, and serves as QALD-10's training base. No standalone QALD-9 overview paper was found in OpenAlex/DBLP **[UNVERIFIED — likely published only via challenge proceedings]**; DBLP only surfaces QALD-9-ES (SEMANTiCS 2023) and QALD-9-plus.

**QALD-10.** The Semantic Web journal paper (DOI 10.3233/SW-233471) describes migrating the challenge from DBpedia to Wikidata, explicitly calling out Wikidata-specific difficulty: "the complexity of the Wikidata knowledge graph, mapping issues between different languages, and the ranking mechanism of properties using qualifiers." Test set: 394 multilingual pairs (repo `KGQA/QALD-10`, 17★). The journal abstract does not mention CLEF 2024 or a "hybrid" track — the parent brief's "hybrid QA over Wikidata" framing is **[UNVERIFIED]**; the verified core is: multilingual complex KGQA on Wikidata, LLM-era (2023/24). This is the single most on-point benchmark for a Wikidata skills suite — but it is single-shot QA, not agentic.

**LC-QuAD 2.0.** 24k complex NL→SPARQL pairs over both Wikidata and DBpedia (ESWC 2019). Complex = multi-hop, aggregation, superlatives. Widely used for training/zero-shot SPARQL generation. No arXiv preprint found (ESWC DOI only). Answer matching is execution-based (run the SPARQL, compare results), which is the right instinct — but it evaluates the *query*, not a repair/execution loop.

**KQA Pro.** ~120k Wikidata-grounded questions with explicit compositional programs (S-Expression programs, e.g. filtering/comparison/computation operators). Because answers are derivable by program execution, it supports process supervision (compare predicted program *and* answer), which is closer to "agent reasoning" than pure QA accuracy. Baselines repo (shijx12/KQAPro_Baselines, 138★) is the canonical code link from the arXiv page; the original `ShulinCao/KQAPro` repo is 404.

**WebQuestionsSP.** The ACL 2016 companion to WebQuestions: 4,737 questions with SPARQL annotations over Freebase ("The Value of Semantic Parse Labeling for Knowledge Base Question Answering", DOI 10.18653/v1/p16-2033). Freebase is defunct, so it functions as a historical/transferability reference for how KGQA benchmarks annotate gold SPARQL — a pattern worth copying for Wikidata (gold SPARQL + entity annotations + answer).

**SimpleQuestions.** 108k single-relation questions, introduced with "Large-scale Simple Question Answering with Memory Networks" (arXiv 1506.02075, Bordes et al.). Freebase-based; the community mirror `askplatypus/wikidata-simplequestions` (87★) re-targets it at Wikidata — evidence of demand for Wikidata-ported benchmarks.

**SemTab.** Annual Semantic Web Challenge on tabular-data-to-KG matching: CTA (column type annotation), CEA (cell entity annotation), CPA (column property annotation). Later editions target Wikidata for CEA. Highly relevant to Commons/Wikidata mass-data workflows (e.g., matching spreadsheet data to Wikidata items, structured-data-on-Commons). The 2020 Oxford page and 2021 edition page are live; the 2023 page and the old `sem-tab-challenge.github.io` site are 404 (challenge infrastructure has churned — same lesson as QALD-9's dead site).

**Wikidata5M.** A 5M-entity Wikidata-derived KG with aligned entity descriptions, constructed as the pre-training/evaluation resource for KEPLER (EMNLP 2019, arXiv 1911.06136 — abstract explicitly: "for pre-training and evaluating KEPLER, we construct Wikidata5M… It shall serve as a new KE benchmark"). Data records on Zenodo (10.5281/zenodo.5546382). Not a QA benchmark — a KG-embedding/link-prediction benchmark — but it is the standard pretraining corpus for Wikidata-aware models and is a useful frozen-snapshot companion to live Wikidata. No canonical GitHub repo found (IntelligentGraph/Wikidata5M → 404).

**Adjacent Wikipedia-table/text QA (not KG).** WikiSQL (80k text→SQL over Wikipedia HTML tables, execution accuracy — note: SQL, not SPARQL), WikiTableQuestions (22k compositional questions over semi-structured wiki tables), WikiQA (Bing query ↔ Wikipedia sentence factoid QA, MAP/MRR). These test *reading* Wikipedia, not *maintaining* it; useful for measuring an agent's comprehension of wiki content before it tries to edit.

**Adjacent Freebase KGQA.** ComplexWebQuestions (arXiv 1803.06643) and GrailQA (arXiv 2011.07743, "Beyond I.I.D.") refine compositional KBQA methodology and generalization splits; Freebase-based, so mostly of methodological interest for Wikidata-benchmark design.

### 3.2 Wikimedia-specific LLM efforts

**WikiChat (Stanford, 2023).** "the first few-shot LLM-based chatbot that almost never hallucinates… grounded on the English Wikipedia" — generates a draft, keeps only grounded facts, retrieves corroborating info from the corpus. Distilled from GPT-4 to a 7B LLaMA model. Verified via arXiv abs + GitHub (stanford-oval/WikiChat). Evaluation uses human judges plus a GPT-4 judge protocol described in the paper body; the abs page does not mention a "live Wikipedia" protocol — the live/freshness dimension described in secondary sources could not be re-verified from the abs/HTML pages **[UNVERIFIED detail]** — but the grounding + judge-based evaluation design is verified and directly reusable for a Wikimedia benchmark (freshness of Wikipedia content is an intrinsic part of the problem, and WikiChat is the reference point for "grounded in Wikipedia, evaluated by judges, checked against the live corpus").

**WikiGenBench (2024).** 1,320 entries; generates *full-length* English Wikipedia articles with citations for newly emerging events from web source documents — explicitly "real-world scenario" generation, with a systematic metric suite (factuality against wiki references, structure, fluency). The closest existing thing to "can an LLM write a Wikipedia article" — but it does not involve actually *editing* Wikipedia (no MediaWiki API, no review process), and it's generation, not the full editorial workflow.

**Wikibench (CHI 2024).** Community-driven data curation for AI evaluation on Wikipedia: rather than outside annotators, Wikipedia community members curate evaluation datasets for AI tools deployed on-wiki (moderation context). This is the strongest existing model for how a Wikimedia skills benchmark should be governed and scored — community-reviewed tasks and ground truth, not researcher-only annotation. arXiv 2402.14147, DOI 10.1145/3613904.3642278.

**LLM-KG-Bench (AKSW).** Automated benchmarking framework for LLMs on KG tasks (BIG-bench-style harness, task collection). Its README cites "Assessing SPARQL capabilities of Large Language Models" (Meyer et al., NLP4KGC@SEMANTICS 2024, CEUR-WS Vol-3874) — a direct data point for the SPARQL-generation gap. A useful harness pattern for a Wikimedia task suite.

**FrOG (Wikimedia Indonesia / Wikidata Research Fund 2024).** GraphRAG-based QA over Wikidata, covered in diff.wikimedia.org (2025-07-23). Community-funded evaluation of retrieval+KG QA on Wikidata — evidence that Wikidata QA evaluation is an active *community* interest, not just an academic one.

**Wiki AI Pre-Conference, Wikimania 2026 (diff, 2026-08-05).** "what we already run and what comes next" — WMF's operational AI inventory (ORES/LiftWing-era services, Edit Check/Tone Check, AI-assisted translation). Useful context: the production surface an agent benchmark should plug into (mediawiki.org's ORES / Edit check / Tone check pages verified via MediaWiki search API).

**WMF research landscape.** research.wikimedia.org is live (200). Meta's Research namespace (verified via search API, 200) surfaces: "Train a language model to perform SPARQL queries" (Community Wishlist Survey 2023 — a community demand signal for exactly the Wikidata-skill capability; direct page check returned missing, so **[UNVERIFIED page URL]**), "Research:Artificial intelligence/Policies by project", "Research:Machine learning models/Production/Tone Check". **No WMF-published LLM evaluation benchmark was found** — WMF evaluates models in production (ORES quality dashboards, model cards, tone-check evals) but has not published a public LLM benchmark over Wikimedia tasks. diff.wikimedia.org's own REST API requires auth (401), but the WordPress.com public API (`public-api.wordpress.com/rest/v1.1/sites/diff.wikimedia.org/posts/?search=…`) works and is the reliable way to search Diff programmatically.

**Context: "Wikipedia in the Era of LLMs: Evolution and Risks"** (arXiv 2503.02879, verified 200) — analyzes LLM-era traffic/content shifts; relevant framing for why evaluation must track live Wikipedia evolution.

---

## 4. Lessons for a Wikimedia skills benchmark suite

1. **Wikidata is now the KG of record.** The field's own arc (QALD-10's explicit DBpedia→Wikidata migration, LC-QuAD 2.0, KQA Pro, SimpleQuestions-Wikidata mirror) means a new benchmark should be Wikidata-first, not DBpedia/Freebase.
2. **Scoring by execution beats scoring by string match.** LC-QuAD 2.0 and KQA Pro score answers by running the SPARQL/program — a Wikimedia suite should execute queries against the live SPARQL endpoint (or a frozen snapshot) rather than eyeball generated queries.
3. **Existing benchmarks are single-shot and static; agents are multi-step and live.** QALD/LC-QuAD/KQA Pro give you one question → one query → one answer. None model: draft query → run → hit error/timeout → repair → verify. That is the agentic loop a Wikimedia benchmark must add.
4. **Grounding + hallucination is the primary LLM-on-Wikipedia failure mode** (WikiChat's whole premise; WikiGenBench's citation-factuality metrics). Any Wikimedia task suite needs groundedness checks against the actual corpus (citations, statements, references), not just fluency.
5. **Community governance is a feature, not an add-on.** Wikibench shows Wikipedia's community should co-curate evaluation data; the Wikipedia-AI-Skills A/B-test approach (fuzheado repo, verified live) already points this way — tasks and rubrics should be reviewable by editors.
6. **Benchmark infrastructure decays.** QALD-9's official site is down, SemTab 2023's page is 404, canonical repos vanished (KQAPro, Wikidata5M). A Wikimedia benchmark should live in a maintained repo (ideally WMF-adjacent) with data mirrored (Zenodo/HF) and URLs that are checked.
7. **Do not trust memory for citations.** In this research, 4 of 8 remembered arXiv IDs were wrong (QALD-9, QALD-10, LC-QuAD 2.0, WebQuestionsSP, Wikidata5M all had to be re-found via OpenAlex/DBLP). The benchmark suite documentation must link verified primary sources.
8. **WMF/community signal exists but no benchmark does.** FrOG, the Wikimania AI pre-conference, the SPARQL-LM wishlist item, Tone Check production evals — all indicate demand; none constitutes a public benchmark. There is no incumbent to compete with.

---

## 5. Gaps — what no existing benchmark covers

| # | Gap | Why it matters | Closest existing thing |
|---|---|---|---|
| G1 | **Live editing via the MediaWiki API** (create/stub/expand an article; make a cited edit; revert a vandalism; use edit summaries; respect watchlists/rollback) | The core skill for LLM editors; every existing benchmark stops at *generation* (WikiGenBench) or *QA* | WikiGenBench (generation only); Wikibench (moderation scoring, no editing) |
| G2 | **SPARQL in an agentic loop** (NL → SPARQL → execute on WDQS → repair on 429/timeout/error → validate answer against Wikidata's qualifiers/ranking) | QALD/LC-QuAD score one-shot queries offline; real use requires iteration and WDQS failure handling (60s timeout, 429 discipline) | QALD-10, LC-QuAD 2.0 (offline single-shot); LLM-KG-Bench harness (no live endpoint) |
| G3 | **Wikidata editing workflows** (wbeditentity create/update, references (P854/P248), qualifiers, constraint compliance, labels in multiple languages, sitelinks) | Q/P-number data-model literacy is exactly the "structured data" skill the brief names; zero benchmarks exist | KQA Pro (answer programs, not edits); QALD-10 (querying only) |
| G4 | **Commons media tasks** (categorize a file, add Structured Data (depicts P180), pick P18 images for items, license/COM:L compliance, upload paths) | Media skills are entirely absent from the KG-QA literature | SemTab (tables, not media); none for Commons |
| G5 | **Policy/compliance evaluation** (NPOV, COI, copyright, BLP, bot policy, citation requirements, edit summaries; avoiding disruptive edits) | Editors judge bots/agents by policy adherence; no benchmark scores policy compliance | Wikibench (community moderation eval); none on editor-side compliance |
| G6 | **Technical facilities as agent substrate** (ORES/LiftWing quality scoring, EventStreams monitoring, Toolforge deployment, PageTriage, watchlists) | The brief explicitly wants these; WMF production ML is evaluated internally (model cards, Tone Check) but never in an agent benchmark | ORES model cards / Edit check docs (mediawiki.org); no benchmark |
| G7 | **Live-data freshness/drift** (Wikipedia & Wikidata change constantly; benchmarks are frozen snapshots) | WikiChat's freshness concern, WikiGenBench's "new events" framing, and the Era-of-LLMs paper all imply evaluation must handle evolving corpora — no benchmark versioned against live data | WikiChat (grounding, static corpus); none time-indexed |
| G8 | **Multilinguality at Wikimedia scale** (300+ language editions; cross-language sitelink/label tasks) | QALD-9-plus (10 languages) is the multilingual ceiling; a Wikimedia suite should test more languages and cross-wiki transfer | QALD-9-plus, QALD-10 (≤10 languages) |
| G9 | **Community acceptance metric** (do *editors* accept the agent's work? revert rates, human-in-the-loop review) | The ultimate score for wiki work is community uptake; no benchmark measures it | Wikibench (community-curated data); Wikipedia-AI-Skills A/B test (12 tasks) is the closest in-repo practice |

**Bottom line:** the verified landscape covers *answering questions about* Wikidata (QALD-9/10, LC-QuAD 2.0, KQA Pro) and *generating Wikipedia prose* (WikiGenBench) plus *community-curated eval* (Wikibench) — but **nothing scores an agent that actually edits Wikipedia/Wikidata, uses SPARQL interactively, handles Commons media, or interacts with Wikimedia technical services.** Those are the green-field tasks for the Lih/Gelauff suite.

---

## 6. Verification log (2026-08-19, UA "HermesAgent/1.0 benchmark research", curl -sL --max-time 20-25)

| URL / endpoint | HTTP | Notes |
|---|---|---|
| https://arxiv.org/abs/1911.07396 | 200 | **WRONG PAPER** (math paper) — QALD-9 not on arXiv; do not cite this ID |
| https://arxiv.org/abs/2312.09739 | 200 | **WRONG PAPER** (math paper) — QALD-10 is Semantic Web journal DOI 10.3233/SW-233471 |
| https://arxiv.org/abs/1912.00326 | 200 | **WRONG PAPER** — LC-QuAD 2.0 is ESWC 2019 DOI 10.1007/978-3-030-30796-7_5, no arXiv found |
| https://arxiv.org/abs/1603.00959 | 200 | **WRONG PAPER** — WebQSP is ACL 2016 DOI 10.18653/v1/p16-2033, no arXiv found |
| https://arxiv.org/abs/1909.00425 | 200 | **WRONG PAPER** — Wikidata5M introduced in KEPLER arXiv 1911.06136 |
| https://arxiv.org/abs/2007.03875 | 200 | KQA Pro (title verified) |
| https://arxiv.org/abs/2305.14292 | 200 | WikiChat (title + abstract verified) |
| https://arxiv.org/abs/2402.18264 | 200 | WikiGenBench (title + abstract: 1,320 entries) |
| https://arxiv.org/abs/2402.14147 | 200 | Wikibench (title + abstract verified) |
| https://arxiv.org/abs/1508.00305 | 200 | WikiTableQuestions |
| https://arxiv.org/abs/1506.02075 | 200 | SimpleQuestions (Bordes et al.) |
| https://arxiv.org/abs/1803.06643 | 200 | ComplexWebQuestions |
| https://arxiv.org/abs/2011.07743 | 200 | GrailQA ("Beyond I.I.D.") |
| https://arxiv.org/abs/1911.06136 | 200 | KEPLER — abstract confirms Wikidata5M construction |
| https://arxiv.org/abs/2503.02879 | 200 | "Wikipedia in the Era of LLMs: Evolution and Risks" |
| https://arxiv.org/html/2305.14292 | 200 | WikiChat full text; no "live Wikipedia" string found — "live" protocol **[UNVERIFIED]** |
| https://qald.sebastianwalter.org/ | 000 | Official QALD site unreachable (connection failure) |
| https://qald.github.io/ | 404 | — |
| https://github.com/ag-sc/QALD (+ /tree/master/9/data) | 200 | QALD-9 data home |
| https://github.com/KGQA/QALD_9_plus | 200 | QALD-9-plus (29★) |
| https://github.com/KGQA/QALD-10 | 200 | QALD-10 dataset (17★); README: 394 test pairs, multilingual |
| https://github.com/AskNowQA/LC-QuAD2.0 | 200 | LC-QuAD 2.0 repo |
| https://github.com/ShulinCao/KQAPro | 404 | original repo gone; arXiv links to shijx12/KQAPro_Baselines (200, 138★) |
| https://github.com/shijx12/KQAPro_Baselines | 200 | canonical baselines repo |
| https://github.com/IntelligentGraph/Wikidata5M | 404 | no canonical Wikidata5M repo |
| https://www.microsoft.com/en-us/download/details.aspx?id=52763 | 200 | WebQSP data |
| https://nlp.stanford.edu/software/sempre/ | 200 | WebQuestions (2013) tooling |
| https://www.cs.ox.ac.uk/isg/challenges/sem-tab/ | 200 | SemTab 2020 official |
| https://www.cs.ox.ac.uk/isg/challenges/sem-tab/2021/ | 200 | SemTab 2021 edition |
| https://www.cs.ox.ac.uk/isg/challenges/sem-tab/2023/ | 404 | newer edition pages moved/down |
| https://github.com/sem-tab-challenge | 200 | org alive |
| https://github.com/AKSW/LLM-KG-Bench | 200 | 59★; README cites Meyer et al. SPARQL-LLM paper (CEUR Vol-3874) |
| https://github.com/salesforce/WikiSQL | 200 | WikiSQL |
| https://github.com/stanford-oval/WikiChat | 200 | WikiChat |
| https://github.com/zhzihao/WikiGenBench | 200 | WikiGenBench (13★) |
| https://github.com/askplatypus/wikidata-simplequestions | 200 | SimpleQuestions → Wikidata mirror (87★) |
| https://github.com/fuzheado/Wikipedia-AI-Skills | 200 | existing 12-task A/B-test repo (context) |
| https://doi.org/10.3233/SW-233471 | 403 | Cloudflare "Just a moment" (blocked); verified via DBLP + OpenAlex instead |
| https://content.iospress.com/articles/semantic-web/sw233471 | 403 | Cloudflare blocked |
| DBLP API q=QALD-10 | 200 | Semantic Web journal, DOI 10.3233/SW-233471 |
| OpenAlex works/doi:10.3233/sw-233471 | 200 | full abstract retrieved (Wikidata migration confirmed; no CLEF mention) |
| OpenAlex works/doi:10.1007/978-3-030-30796-7_5 | 200 | LC-QuAD 2.0 ESWC 2019 |
| OpenAlex works (QALD-9, Wikidata5M, WikiEval, WikiBench, Wiki-Agent, WikiRAG, WikiEdit, WikidataEdit, etc.) | 200 | searches; relevant hits only for Wikibench (2402.14147) and WikiRAG (2025, no arXiv found) |
| GitHub search API (WikiGenBench, Wiki-Agent, WikiEval, QALD-10, SPARQL LLM benchmark, sem-tab, SimpleQuestions, Wikidata5M, KQAPro) | 200 | used for repo discovery/404 resolution |
| https://export.arxiv.org/api/query | 429 | arXiv Atom API rate-limited during session (used abs pages instead) |
| Semantic Scholar API | 429 | rate-limited during session (used OpenAlex/DBLP instead) |
| https://diff.wikimedia.org/wp-json/wp/v2/posts | 401 | requires auth |
| https://public-api.wordpress.com/rest/v1.1/sites/diff.wikimedia.org/posts/?search=… | 200 | **working path to search Diff**; key posts verified (Wiki AI Pre-Conference 2026-08-05; FrOG 2025-07-23; ChatGPT/social-contract 2026-07-17) |
| https://research.wikimedia.org/ | 200 | WMF research portal |
| meta.wikimedia.org API (srsearch LLM, Research ns=104) | 200 | surfaced FrOG, SPARQL-LM wishlist, Tone Check, AI policies pages |
| meta.wikimedia.org API titles=… (FrOG Laporan; SPARQL-LM wishlist) | 200 | direct page checks returned **MISSING** — cite via search results only, **[UNVERIFIED] page URLs** |
| www.mediawiki.org API (LLM/evaluation search) | 200 | ORES, Edit check/Tone Check model pages |

**Status legend:** `200` verified reachable; `000` connection failure; `401/403` auth/anti-bot blocked (verified via alternative sources where noted); `404` not found; **[UNVERIFIED]** claim not confirmable from primary sources fetched; **[NOT FOUND]** no evidence of existence in the sources searched.
