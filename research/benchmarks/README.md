# WAIS-Bench — Wikimedia LLM Skills Benchmark

**Status: Phase 0 (task registry, ported from the AB-testing rounds).**
Provisional name; namespace verified clear (`WikiAgentBench`, `WikiEval`, `WAB` all
searched-and-not-found as of 2026-08).

## What this is

A benchmark suite for testing LLM agents on Wikimedia tasks — on-wiki editing,
MediaWiki Action/REST APIs, Wikidata SPARQL, Commons, Toolforge, and WMF ML
services — measuring both capability (model × task) and intervention (skills
injected vs. no skills). The full rationale, landscape research, and design are
in [`WAIS_BENCH_SYNTHESIS.md`](WAIS_BENCH_SYNTHESIS.md); the verified benchmark
landscape (40+ benchmarks, all URLs live-checked 2026-08-19) is in
[`landscape/`](landscape/).

**Key finding from the landscape research:** no existing benchmark tests an LLM
agent interacting with the wiki itself. The closest things are WebArena (a
Kiwix offline MediaWiki replica, browser-only, pre-2022), QALD/LC-QuAD (single-shot
offline SPARQL QA), WikiGenBench (article *generation*, not editing), and
Wikibench (community-curated eval data — the governance model to copy).

## Layout

```
research/benchmarks/
├── README.md                     <- this file
├── WAIS_BENCH_SYNTHESIS.md       <- proposal + critical analysis + 48 verified sources
├── landscape/                    <- verified benchmark landscape (3 research files + logs)
├── tasks/                        <- Phase 0: 12 task files (JSON), ported from AB rounds
│   ├── r1t1-pageviews.json       ...
│   └── r3t12-vandalism-patterns.json
└── scripts/
    └── validate-benchmark-tasks.py   <- schema validator (stdlib only)
```

## Task schema (v0.1.0)

Each file in `tasks/` is one machine-readable task. Required fields:

| Field | Meaning |
|---|---|
| `id` | `r<round>t<task>-<slug>`, must prefix the filename |
| `prompt` | The exact assignment given to the agent (reproducible) |
| `skills` | Skills the A-variant loads; each must exist in `.claude/skills/` |
| `apis` | APIs/facilities involved |
| `canaries[]` | Known silent-failure traps, each with a `detection` method |
| `verifier.checks[]` | Declarative checks: `kind`, `detail`, `pass_condition` |
| `tier` | `live` (current APIs, drift-tolerant) or `gold` (frozen snapshots) |
| `safety` | `read-only` \| `sandbox-write` \| `live-write` |
| `time_budget_min` | Wall-clock budget for one run |

Verifier check kinds (Phase 1 will implement them in the runner):
`api_crosscheck`, `count_check`, `schema_check`, `canary_detection`,
`membership_check`, `anti_contamination`, `ordering_check`, `artifact_check`,
`namespace_check`, `assertion_check`, `safety_check`, `sanity_check`,
`sparql_match`, `anti_fabrication`, `throughput_check`.

## How to contribute

1. Validate: `python3 research/benchmarks/scripts/validate-benchmark-tasks.py --report`
2. Tests: `python3 -m pytest tests/test_benchmark_tasks.py -q`
3. New tasks follow the schema; ported AB tasks carry `port_notes` pointing at
   the round reports in `research/ab-testing/`.

## Phase 0 provenance

The 12 tasks are ported from the three AB round reports
(`research/ab-testing/AB_TEST_REPORT_ROUND{1,2,3}.md`, June 2026, 24 agent runs).
The verifiers encode the known failure modes those runs surfaced — most
importantly the six silent failures: 48h pageviews lag (r1t1), recursive
category truncation (r2t5), navbox diversity + template-only sections (r2t8),
fabricated ML quality labels (r3t11), and canary/diff/throughput failures
(r3t12). Each task's `canaries[]` is the machine-readable form of those lessons.

## Next phases (see synthesis §5.3)

- **Phase 1:** gold-tier frozen snapshots; runner (Inspect AI or promptfoo) that
  executes tasks against the matrix model × skills; metric stack (success,
  plausible-error rate, time, cost, calibration proxies) with CIs.
- **Phase 2:** live-tier tasks; **Phase 3:** editing tier on test.wikipedia.org;
  **Phase 4:** community-curated tasks (Wikibench model).
