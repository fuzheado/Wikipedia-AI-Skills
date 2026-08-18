# Extracting Lead Text for LLM Context — the Spectrum of Choices

**Last verified:** 2026-08-18 (live against en.wikipedia.org)
**Origin:** ShortDesc Studio (short-description generation tool) — every approach
below was tested live on real articles and diffed against the browser render.

When a tool needs "the article's lead" as text — for LLM prompting, RAG, or
display — there are **four** approaches, and **none is universally correct**.
They differ on three axes that matter:

1. **Fidelity** — is the output the actual rendered page (what a browser shows),
   or a derived/transformed text?
2. **Content loss** — does it strip parentheticals (dates!), pronunciations,
   or truncate?
3. **Artifacts** — does it leave junk behind (boxes, banners, template debris)?

---

## The four approaches

| # | Approach | Endpoint | Fidelity | Length | Known gotchas (verified) |
|---|----------|----------|----------|--------|--------------------------|
| 1 | **REST summary** | `GET /api/rest_v1/page/summary/{title}` | Derived — **transforms** content | ~600 chars max, mid-sentence cut | **Strips parentheticals — including dates**: John Williams loses "(born February 8, 1932)", World War II loses "(1 September 1939 – 2 September 1945)". Cleanest output otherwise (no banners/navboxes). |
| 2 | **TextExtracts** | `action=query&prop=extracts&exintro=1&explaintext=1` | Derived plaintext | Full lead (no cap) | Keeps dates ✓, drops banners/navboxes ✓, but leaves **template debris**: "(locally  )" empty parens, respelling fragments ("MARR-ib-or"), stray newlines inside parentheticals. |
| 3 | **Parsoid HTML + DOM cleaning** | `action=parse&prop=text&section=0` (JSON) or `GET /api/rest_v1/page/{title}/html` | **Literal browser render** | Any (truncate yourself) | Only approach that is token-identical to the browser render. Requires a **noise contract** (selector list below) — a small, closed set of artifact families. `action=parse&section=0` **appends the section's rendered reference list** (`div.mw-references-wrap`) that the browser's lead doesn't contain — remove it. |
| 4 | **LLM-generated summary** | LiftWing / any LLM: "summarize this lead" | Synthetic — **unverifiable** | As asked | Hallucination risk on the input everything downstream trusts; costs an extra LLM call; a lossy transformation of text the model will see anyway. Use only when a *human-style* summary is the deliverable, never as preprocessing for another LLM step. |

---

## Decision rule of thumb

| Your use case | Choose |
|---------------|--------|
| Mobile-app-style summary, display, thumbnails | **REST `/page/summary`** (1) |
| Clean plaintext, dates must survive, artifacts tolerable | **TextExtracts** (2) |
| Fidelity to the rendered page is critical (LLM context, extraction, testing oracles) | **Parsoid HTML + noise contract** (3) |
| A *human-readable* summary is the end product | LLM summarization (4) — last resort |

**The trap to avoid:** `/page/summary` looks like the obvious choice for "lead
text" and is clean — but it silently strips parentheticals. For any
disambiguation-sensitive downstream use (short descriptions, entity dates,
BLP facts), that's content loss, not cleanliness.

---

## The Parsoid noise contract (approach 3)

The complete closed set of artifact families to decompose before extracting text
(verified on enwiki, 2026-08):

```
table.infobox, table.sidebar, table.vertical-navbox,   # boxes
table[class*='navbox'],                                # navbox/navbox-inner/navbox-vertical (campaign boxes)
figure, figcaption,                                    # lead-image captions
div.mw-references-wrap,                                # ref list appended to action=parse&section=0
.ambox, .cmbox, .tmbox, .ombox, .fmbox,                # Module:Message box family (maintenance banners)
sup.reference,                                         # inline [1] citation markers
.mw-editsection, .hatnote, .shortdescription,          # edit links, dab hatnotes, live short description
.preview-warning, style, script, .error                # Parsoid deprecation warnings, CSS/JS, errors
```

Notes:
- The families are **closed sets** — navbox (via `[class*='navbox']`) and mbox
  (ambox/cmbox/tmbox/ombox/fmbox) cover the template space completely.
- The live short description (`.shortdescription`) must be removed or it leaks
  the answer into the prompt.
- `action=parse&prop=text` on modern wikis returns Parsoid HTML (`data-mw`
  attributes present), so approach 3 works through the Action API too — one
  call, `section=0`, no REST Accept-header dance.

---

## The fidelity-test pattern (make extraction bugs impossible)

The only reliable way to keep extraction honest: **test the excerpt against the
browser render**. Ground truth = REST `/html` lead section
(`<section data-mw-section-id="0">`), noise contract applied. Assert the tool's
output is token-sequence-identical (normalize: collapse whitespace, strip edge
punctuation, drop empty tokens — tolerates template whitespace nesting while
still catching any missing/invented/reordered word).

```
tool_excerpt ≡ browser_render_lead  (token sequence, same order)
```

This is what caught, in one afternoon: campaign boxes, lead-image captions,
appended reference lists, and maintenance banners — four separate leak classes.
The test deliberately **duplicates** the noise contract so contract drift in
either direction fails loudly. Sabotage-proven: reverting any single selector
fails the suite on the affected article(s).
