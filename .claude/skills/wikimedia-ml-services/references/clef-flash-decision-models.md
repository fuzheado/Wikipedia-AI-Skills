# Decision models on Lift Wing — `llm-clef-flash` (`:predict` only)

The LLM chat route is not the only LLM-shaped service on the platform. Wikitech now
documents a third kind of deployment, *"Public — Task Specific models (public API, not in
Studio)"* (Wikitech `Machine Learning/LiftWing/Large Language Models`, rev 2466734,
2026-10-13), whose first member is a **decision model**: you send a state plus a set of
**typed questions** and get back one probability (or expected value) per question — no free
text to parse.

**The trap this reference exists for:** decision models are *not* OpenAI-compatible. Point an
OpenAI client at `llm-clef-flash` and you get an HTTP 404, not a chat completion.

## Endpoint and contract

```
POST https://api.wikimedia.org/service/lw/inference/v1/models/llm-clef-flash:predict
Content-Type: application/json        # no API key required
```

```json
{
  "model": "llm-clef-flash",
  "state": "any string or JSON value",          // required
  "questions": {
    "face_visible": {"type": "noul",  "instructions": "Is a face clearly visible?"},
    "quality":      {"type": "score", "instructions": "Photo quality",
                     "criteria": ["unusable", "poor", "acceptable", "good", "excellent"]},
    "pose":         {"type": "choice", "instructions": "Framing?",
                     "criteria": {"head_shoulders": "Head and shoulders", "group": "Group"}}
  },
  "images": ["<base64>"]                        // optional, max 4
}
```

Response (`usage.output_tokens` is always `0` — the head scores, it does not generate):

```json
{"model": "llm-clef-flash",
 "answers": {
   "face_visible": {"type": "noul", "noul": 0.6352},
   "quality": {"type": "score", "score": 2.2936, "confidence": 0.5188,
               "legend": {"0": "unusable", "2": "acceptable", "4": "excellent"},
               "probabilities": {"0": 0.0275, "1": 0.08, "2": 0.5188}},
   "pose": {"type": "choice", "choice": "head_shoulders", "confidence": 0.71,
            "probabilities": {"head_shoulders": 0.71, "group": 0.29}}},
 "usage": {"input_tokens": 155, "output_tokens": 0}}
```

Answer fields by type: `noul` → `noul` (probability); `choice` → `choice` + `confidence` +
`probabilities`; `score` → `score` (expected value over the criteria order, echoed in
`legend`) + `confidence` + `probabilities`.

### Route reality check (verified live 2026-10-16)

| Call | Result |
|---|---|
| `…/models/llm-clef-flash:predict` | **HTTP 200**, 0.14–0.16 s warm |
| `…/models/llm-clef-flash/openai/v1/chat/completions` | **HTTP 404** `{"detail":"Not Found"}` |
| same chat route on `llm-qwen3-14b` | HTTP 200 (control) |

`llm-clef-flash` is also absent from `https://api.wikimedia.org/service/lw/specs/openapi.yaml`
and does not appear in LiftWing Studio. Wikitech places it in the public API tier only.

## Guard rails (verbatim HTTP 400 bodies, re-verified 2026-10-16)

- `{"error":"Invalid payload format. Must contain a 'state' field."}`
- `{"error":"'questions' must be a non-empty mapping of id to question."}` — a JSON **list** is rejected
- `{"error":"33 questions exceeds the maximum of 32."}` — server cap, tighter than the vendor's 64
- `{"error":"5 images exceeds the maximum of 4."}`
- `{"error":"'videos' is not supported by this server."}`
- `{"error":"Image at index 0 is not valid base64: Only base64 data is allowed"}` — remote image URLs are refused
- `{"error":"Question 'a' is a choice and needs 'criteria' as a mapping of at least two options."}`

A web request for "no `state`" can transiently return `503 upstream connect error …` (observed
once, 2026-10-16); retry once before treating it as a payload problem — the deterministic answer
is the 400 above.

## Measured behaviour

- **Fast and deterministic.** Warm text calls 0.137–0.161 s; two identical replicates returned
  byte-identical JSON (2026-10-16). Earlier image runs: 0.387–0.413 s warm, n=3 identical.
- **First call at a new input shape is slow:** 2.7–7.2 s (a one-off compile in the serving pod),
  then fast — image batching should warm up per shape.
- **The question set changes the numbers.** The head scores all questions jointly, so the same
  input scored with 2 questions gave `face_visible` 0.6352 vs 0.6105 with 1 question
  (2026-10-16); an earlier 2-vs-5-question comparison gave 0.923 vs 0.9274 (2026-10-12).
  **Only compare runs that used an identical schema**, and version the schema with your results.
- **Images are downscaled to 640 px wide server-side** before the encoder, and capped at 8 MiB
  base64 per image — sending larger files costs upload bandwidth for no gain.
- **Token cost is set by aspect ratio, not file size:** every 3:2 file billed 905 input tokens
  whether the original was 5472×3648 or 12000×8000; every 2:3 file 1245 (2026-10-12).
- **Rate limiting on `:predict` is real, and `Retry-After` is authoritative.** There is no
  `x-wmf-ratelimit-class` header (the chat route sends `unauthed-bot`), but an exhausted budget
  answers **HTTP 429** with `x-envoy-ratelimited: true` and a `retry-after` in **seconds**. Observed
  values: **1347** (2026-11-02) and **~800** (2026-10-20, after ~200 calls in ~80 min). Treat it as a
  budget reset, not a transient hiccup.

### Observed rate-limit behaviour (2026-10-20, 2026-11-02)

| observation | value |
|---|---|
| 429 after ~200 calls in ~80 min | `retry-after: ~800` s |
| 429 on the first call of a session, budget already spent by earlier runs | `retry-after: 1347` s |
| headers present on 429 | `x-envoy-ratelimited: true`, `retry-after`, `x-client-ip`, `x-request-id` |
| body | `You are making too many requests to the API … contact bot-traffic@wikimedia.org` |

Both observations came from shared egress IPs on modest runs (~200 and 1 call respectively), so the
budget is per-IP and can be spent by anything else behind the same address. Planning figure:
**~2.5 calls/min sustained**. Size a job against that before promising a runtime — 122,000 calls
(one deployment's 2,000 hours of video at 50 calls per hour) is weeks of wall clock, not hours.

**The trap this cost us.** A client that honoured `Retry-After` but capped it at 1200 s retried
**147 s early** on the 1347 s header and re-entered the wall; the retry looked like intermittent
flakiness, and the cap converted a correct wait into a guaranteed failure. If a runaway ceiling is
needed, **refuse the call and report the wait** — never shorten it silently.

## Why it looks like this (serving internals)

Served by a KServe Python model-server on Hugging Face `transformers`, **not vLLM**
(`src/models/decision_models/clef/model.py` in
`wikimedia/machinelearning-liftwing-inference-services`), which is why there is no
OpenAI-compatible route and no context window in the chat-completion sense: the server truncates
via `encode_record` at 16,384 tokens and refuses a `state` longer than 60,000 characters.
Wikitech: "9B multimodal decision model. At the moment is using HF backend (no vllm). Only
supports `:predict` endpoint for now." Deployment trail: Phabricator T440223 (2026-10-07 /
2026-10-09).

## Using decision models well

- Right for **fixed-schema batch classification** where you want numbers and confidence, not
  prose (image triage, policy/quality bucketing, candidate screening). Wrong for anything needing
  explanation, free text, or follow-up turns — use the chat models for that, and read their output
  as a draft.
- Keep the schema **stable and versioned**; store it alongside the answers, because the
  probabilities are only meaningful relative to it.
- Treat a single score as **evidence, not a verdict**: calibrate any threshold on your own
  examples before automating an action.
- Batch politely: no published rate-limit tier for this route, and the shared platform has no SLA.

## Known unknowns

- The exact window the 429 budget resets on, and whether `:predict` shares the anonymous
  100 req/hour budget with the chat route. Observed waits (~800 s, 1347 s) are consistent with an
  hourly per-IP budget but do not prove it.
- No published task-quality numbers for this model (vendor Decision Index covers text/structured
  usage only) — validate on your own examples.
- Whether more task-specific models will follow this pattern; check the Wikitech "Public — Task
  Specific models" table before assuming the chat route is the only public LLM surface.

See also: `lift-wing-llm.md` for the chat models, rate-limit tiers, and serving benchmarks.
