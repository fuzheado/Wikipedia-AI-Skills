# Lift Wing LLM Endpoints — Session Reference

Captured 2026-08-14; refreshed against Wikitech and live public API 2026-10-07. Lift Wing now serves open-weight LLMs (up to ~30B params) via vLLM on AMD MI300X GPUs (eqiad `ml-serve` nodes). Unusually for Wikimedia, the public interface is **OpenAI-compatible** (`/openai/v1/chat/completions`), not the KServe `:predict` envelope.

Canonical docs (both `{{Draft}}` as of capture):
- https://wikitech.wikimedia.org/wiki/Machine_Learning/LiftWing/Large_Language_Models
- https://wikitech.wikimedia.org/wiki/Machine_Learning/LiftWing/Large_Language_Models/Wikimania_2026

## Models

### Public (general-purpose — in API + Studio)
| Model ID | Base | Precision | Context | GPUs | Notes |
|---|---|---|---|---|---|
| `llm-qwen3-14b` | Qwen3-14B-FP8 | FP8 + FP8 KV | 16,384 | 1 | Default general-purpose chat model |
| `llm-qwen36-27b` | Qwen3.6-27B-FP8 | FP8 + FP8 KV | 32,768 | 1 | Previously largest public model; text-only (multimodal disabled); live 200 on 2026-10-07 |
| `llm-qwen38-27b` | Qwen3.8-27B-FP8 | FP8 + FP8 KV | 32,768 | 1 | Newer public 27B model; Wikitech says "same as qwen3.6"; live 200 on 2026-10-07 |
| `llm-gpt-oss-safeguard-20b` | gpt-oss-safeguard-20b, ~20B MoE | MXFP4 | 16,384 | 2 (TP) | Listed by Wikitech as public safeguard/policy-violation model, but public chat route returned 404 on 2026-10-07 |

### Internal (NOT public, NOT in Studio)
| Model ID | Type | Precision | Purpose |
|---|---|---|---|
| `cope-b-a4b` | Zentropi CoPE-B, 26B MoE / ~4B active | bf16 | policy-violation detection |
| `cope-a-9b` | Zentropi CoPE-A, 9B (Gemma-2-9b LoRA) | bf16 | policy-violation (experimental ns) |
| `qwen3-embedding` | Qwen3-Embedding-0.6B | fp16 | text embeddings (not a chat model) |
| `jina-embedding` | jina-embeddings-v5-text-nano 0.2B | bf16 | text embeddings (not a chat model) |

## Endpoint

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/{model}/openai/v1/chat/completions
```
Body: `{"model": "...", "messages": [...]}`. Streaming (server-sent events) supported. Only `llm-*` names are routed by the REST gateway. The URL path model and JSON body `model` must match; newly documented model IDs should get a 1-token smoke test before use.

Python (any OpenAI SDK — set `base_url`, `api_key="none"`):
```python
from openai import OpenAI
client = OpenAI(
    base_url="https://api.wikimedia.org/service/lw/inference/v1/models/llm-qwen3-14b/openai/v1",
    api_key="none",
)
resp = client.chat.completions.create(
    model="llm-qwen3-14b",
    messages=[{"role": "user", "content": "Explain vLLM in one sentence."}],
)
```

Note: the LiftWing OpenAPI spec (`/service/lw/specs/openapi.yaml`) now includes the generic LLM chat-completions path, but model availability still comes from Wikitech plus a live smoke test.

## Rate limits (policy `LiftWingLLM`, phab T426749)
| Client class | Limit | Who |
|---|---|---|
| Public / anonymous | **100 req/hour** | shared per-client across ALL `llm-*` models; HTTP 429 past it |
| WMCS (Cloud VPS + Toolforge) | effectively unlimited | `x-trusted-request: A` |
| Known client | effectively unlimited | `x-trusted-request: B` |
| Approved bot | effectively unlimited | JWT auth |

LiftWing Studio runs on Cloud VPS, so it rides the unlimited tier (the gateway sees Studio as one WMCS client).

## Capabilities vs limitations
| Works today | Not yet |
|---|---|
| OpenAI-compatible chat & text completions | web search / browsing |
| streaming (SSE) | RAG (server-side) — but DIY by stuffing context into prompt |
| up to 32K context (public models) | vision / multimodal |
| tool / function calling for general-purpose public models | |
| multilingual input | |
| horizontal scaling of single-GPU models | multi-GPU (tensor parallel) for public Qwen models |

- `<think>…</think>` may wrap chain-of-thought at the start of a Qwen response — strip it if you only want the final answer.
- Experimental, **no availability SLA**; FP8 quantized → small differences vs full precision; model set / endpoints may change without notice.
- Fixed training cutoff, no live data unless you wire tools → do NOT trust for time-sensitive facts; retrieve current content yourself, include it as context, or run a tool-calling loop.
- Wikitech documents hosted tools (`current_date`, `wikipedia_semantic_search`) and an MCP/tool-calling loop example; the model alone will not fetch current data.

## Benchmarks (llm-qwen36-27b FP8, internal endpoint, single replica, 2026-07-17)
| Concurrency | Req/s | Output tok/s | TTFT p50 (ms) | TTFT p99 (ms) | E2EL p50 (ms) | E2EL p99 (ms) |
|---|---|---|---|---|---|---|
| 1 | 0.37 | 35 | 197 | 435 | 3,614 | 3,650 |
| 8 | 1.90 | 179 | 255 | 1,225 | 5,270 | 6,270 |
| 32 | 3.63 | 349 | 730 | 4,798 | 10,342 | 12,393 |
| 64 | 4.24 | 413 | 3,729 | 9,401 | 18,125 | 19,845 |

- Single stream: ~197 ms to first token, ~35 tok/s, ~3.6 s for a 128-token reply.
- Throughput saturates ~410 output tok/s around concurrency 64; scaling is sub-linear past ~8–16. Add capacity by scaling OUT replicas, not pushing one GPU.

## Data & privacy
- **API:** persists nothing — prompts/responses not logged, not retained, not used for training. Each request is independent (send full context each time).
- **LiftWing Studio:** saves chats to its DB by default (and they can be shared). Use a "temporary chat" to avoid persistence.

## Word-on-the-street caveats
- WMF publishes **serving-performance benchmarks only, NOT task quality** — validate on your own examples.
- No Wikimedia-specific task benchmarks (summarization, factual QA, multilingual) yet.
- Quality generally stronger for high-resource languages.

## Get help / report issues
- Phabricator tag `machine-learning-team`; IRC `#wikimedia-ml` (Libera); email ml@wikimedia.org.
- Studio source: https://gitlab.wikimedia.org/repos/machine-learning/liftwing-studio
- Related phab: T426749 (rate limits), T431136 (vLLM metrics), T431554/T431851 (benchmarking/load-testing), T421461 (safeguard model pinning).

## Live tests
- 2026-08-14: `llm-qwen3-14b` answered a simple one-sentence prompt in ~1.1 s, returning clean OpenAI-format JSON (`id`, `choices[].message.content`, `usage` with token counts). No API key was used.
- 2026-10-07: 1-token public API smoke tests: `llm-qwen36-27b` → HTTP 200, `llm-qwen38-27b` → HTTP 200, `llm-gpt-oss-safeguard-20b` → HTTP 404 (`{"detail":"Not Found"}`).

## Task benchmark — llm-qwen36-27b (2026-08-18)

Reusable battery: `scripts/benchmark-llm.py` (8 wiki tasks, live enwiki data, JSON output).
Run with `python3 benchmark-llm.py` (full, ~12 LLM calls) or `--quick` (smoke test).

| Task | Latency | Result | Verdict |
|---|---|---|---|
| T1 Wikidata statement extraction (prose→JSON) | 14.1s | Valid JSON, **13 statements**, correct P-IDs (P31/P19/P569/P20/P570/P509/P106/P27/P166), qualifiers handled (P585 on awards) | ✅ Excellent; 1 label slip (P1412 mislabeled) |
| T2 Article quality grading (FA/GA/B/C/Start/Stub), lead-only | 0.25s | B vs GA · B vs FA · Stub vs C — all wrong | ❌ Use dedicated `articlequality` model |
| T3 NPP notability triage | 1.7s | Clean verdict+rationale; judged a real surviving article DELETE | ⚠️ Pre-filter only; needs full context + human review |
| T4 Short description generation | 0.3s | All ≤40 chars, semantically right; often more precise than live ("Landlocked country in South Asia") | ✅ Strong |
| T5 CS1 citation generation | 2.9s | `{{cite journal}}` all fields correct, valid wikitext | ✅ Flawless |
| T6 Talk page summarization | 5.1s | Accurate consensus framing + position counts on real dispute | ✅ Excellent |
| T7 NPOV audit (Trump lead) | 0.4s | "No significant NPOV issues" | ⚠️ Too lenient as sole arbiter; triage only |
| T8 Full-article digest (14K chars in) | 11.4s | Correct facts, clean structured format | ✅ 32K window pays off |

**Recommended uses (benchmark-backed):** prose→Wikidata statements (SDC, infobox data, property suggestions); short-description generation (millions of articles lack them); CS1 citation construction; RfC/noticeboard consensus summarization; cross-wiki gap analysis (two language versions in one 32K prompt → list missing sections/claims).

**Avoid:** article-quality grading (statistical model strictly better); NPOV as final call; live-data tasks without pre-fetching context or a tool-calling loop. Long structured outputs are where latency lives (531 completion tokens ≈ 14s).

**Latency profile:** short tasks 0.2–0.4s; medium (verdict+rationale, citation, talk summary) 1.7–5s; long (14K-char digest) 11s; heavy structured JSON 14s.

## Few-shot short-description generation (2026-08-18)

Script: `scripts/fewshot-short-description.py` — use existing short descriptions from
same-type articles as in-context examples. Type is detected via Wikidata (P106 occupation
for people, P31 instance-of otherwise); same-type examples are pulled from the article's
own enwiki categories (real `prop=description` values, not Wikidata descriptions, so the
model imitates the exact artifact — including its conventions like "YYYY film by Director").
~8 examples fit comfortably in the window.

| Case | Zero-shot (baseline) | Few-shot (8 same-type examples) | Live ground truth |
|---|---|---|---|
| Maribor (city) | "Slovenian city and second-largest urban centre" | **"City in Styria, Slovenia"** | "City in Styria, Slovenia" |
| Lise Meitner (nuclear physicist) | "Austrian-Swedish nuclear physicist" | "Austrian-Swedish nuclear physicist" | "Austrian-Swedish nuclear physicist (1878–1968)" |
| Inception (film) | "2010 American sci-fi film directed by Christopher Nolan" | **"2010 film by Christopher Nolan"** | "2010 film by Christopher Nolan" |

The few-shot prompt consistently converges on the *conventions* of the type (nationality+role
for people, "City/Town in X, Country" for places, "YYYY film by Director" for films) and
matched live descriptions exactly in 2 of 3 cases, while zero-shot drifted to wordy
non-conventional phrasing. Use `temperature=0.3` for a little variety while staying on-pattern.
Variants worth trying: more examples (up to ~16), examples filtered to the same country/year,
and the target article's own categories re-ranked by type-word match.

## Adaptive example-count selection (2026-08-18)

Fixed example counts are wrong: 16 examples from a heterogeneous category *regressed*
Inception ("American" leaked in from 3 of 16 noisy members) while 8 was exact. Homogeneous
categories (Maribor coverage 0.69, DSOTM 0.88) absorb 16 fine. Rule implemented in
`adaptive_select()` — measure **pattern coverage** (share of candidates sharing the dominant
token skeleton, zero extra LLM calls): coverage ≥0.6 → keep 16; 0.4–0.6 → 10; <0.4 → 7, and
score-rank examples by pattern support (penalizing index/list/series/parenthetical entries).

| Article | Coverage | Patterns | Adaptive count | Result |
|---|---|---|---|---|
| Inception (mixed pool) | 0.38 | 5 | → 7 ex | "American" leak fixed |
| Nile (wrong category) | 0.31 | 8 | → 7 ex | semantic (category is root problem) |
| Maribor / Meitner / DSOTM | 0.62–0.88 | 2–3 | → 16 ex | exact preserved |

## Constitutional guidance + examples (2026-08-18) — two-layer design

Architecture: **system-prompt guidance (policy) + few-shot examples (house style)**. The
guidance is distilled from real policy: [Wikipedia:Short description](https://en.wikipedia.org/wiki/Wikipedia:Short_description)
(Content, Format, Inclusion of dates sections) and [Wikidata Help:Description](https://www.wikidata.org/wiki/Help:Description).
Layers:
1. **General rules** — max 40 chars, no leading article, no terminal period, no markup,
   no subjective/time-specific adjectives, avoid duplicating title info.
2. **Date rules** — the John Smith case: common names need dates to disambiguate.
   Deceased: `(birthyear–deathyear)`; living (BLP): `(born year)` only if sourced;
   `(died year)` / `(c. yyyy–yyyy)` variants. **Without this, zero-shot produced
   "American composer and conductor" for John Williams — ambiguous with hundreds of
   same-named people. With guidance: "American composer and conductor (born 1932)" = exact live.**
3. **Type-specific** (keyed by P31/P106 QID) — films "YYYY film by Director", albums
   "YYYY studio album by Artist", cities "City/Town in X, Country", countries
   "Country in [region]", rivers "River in X".

Full regression suite with guidance + adaptive count (all live-compared):

| Article | Result | Live | Verdict |
|---|---|---|---|
| John Williams (conductor) | American composer and conductor (born 1932) | American composer and conductor (born 1932) | ✅ exact — date rule fired |
| Lise Meitner | Austrian-Swedish nuclear physicist (1878–1968) | Austrian-Swedish nuclear physicist (1878–1968) | ✅ exact — date rule fired |
| Inception | 2010 film by Christopher Nolan | 2010 film by Christopher Nolan | ✅ exact — film convention fixed "directed by" |
| Nile | Major river in northeast Africa | Major river in northeast Africa | ✅ exact — "major" rule fired |
| Maribor | City in Styria, Slovenia | City in Styria, Slovenia | ✅ exact |
| Dark Side of the Moon | 1973 studio album by Pink Floyd | 1973 studio album by Pink Floyd | ✅ exact |
| Nepal | Landlocked country in South Asia | Country in South Asia | ⚠️ valid variant (landlocked is arguably more precise) |

6/7 exact, 1 defensible variant. The two signals can conflict (Nepal's "landlocked" came from
guidance over the "Country in South Asia" example majority) — currently the prompt makes
guidance authoritative ("follow examples unless the guidance overrides"), which is the right
default for policy-critical cases like dates/BLP.
