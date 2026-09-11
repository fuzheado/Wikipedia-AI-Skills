# Wikisource: Catalogue, Delivery & the AI Layer

Reference for everything *outside* the proofreading editor: how finished works are
discovered, counted, and shipped to readers — and the community's norms around the
OCR/LLM tooling that feeds the pipeline.

All measured/verified **2026-09-11**.

---

## 1. The Wikidata backbone (Books data model)

Wikisource works are described on Wikidata using an FRBR-derived, two-level model:

| Level | `instance of` (P31) | Notes |
|-------|--------------------|-------|
| **Work** | written work `Q47461344` (or subclass) | the abstract work |
| **Edition** | version, edition or translation `Q3331189` | one specific publication; **one item per edition** |

Linking and Wikisource-specific properties:

| Property | Meaning |
|----------|---------|
| `P747` | has edition or translation (work → editions) |
| `P629` | edition or translation of (edition → work) |
| **`P1957`** | **Wikisource index page URL** — the primary discovery key |
| `P996` | document file on Wikimedia Commons (the scan) |
| `P953` | work available at URL (the text on Wikisource) |

**Completion status is carried by sitelink badges**, not by a statement:

| Badge | QID | Meaning |
|-------|-----|---------|
| not proofread | `Q20748091` | transcription started/absent |
| problematic | `Q20748094` | flagged problems |
| **proofread** | **`Q20748092`** | read by one person |
| **validated** | **`Q20748093`** | read by two people |

The badge reflects the state of the `Index:` page. It is the **only machine-readable,
cross-wiki completion signal** — and it is applied unevenly (see §3).

---

## 2. wsindex — the completed-books catalogue API

```
https://wsindex.toolforge.org/books/
```

- JSON, paginated: `{"count": N, "next": url|null, "previous": url|null, "results": [Book, …]}`
- Django app on Toolforge; source `gitlab.wikimedia.org/toolforge-repos/wsindex`
- Analytics UI: `https://wsindex.toolforge.org/analytics/`
- Root `/` returns only `{"books": "…"}` — go straight to `/books/`

**Per-book fields:** `wikidata_qid`, `title`, `title_native_language`, `languages[]`,
`date_of_publication`, `authors[]`, `editors[]`, `translators[]`, `genre[]`,
`literary_genres[]`, `type_of_work`, `form_of_work[]`, `ws_url`, `thumbnail_url`,
`epub_url`, `wikisource_index_url`, `view_count`, `main_subjects[]`, `subjects[]`,
`places_of_publication[]`, `publishers[]`.

### ⚠️ Parameter trap

`languages` works (`?languages=en`). **Unrecognised parameters are silently ignored** —
`?wikidata_qid=Q19026962` returns the *unfiltered* list with `count` = the global total,
not an error and not an empty result. Always sanity-check `count` after adding a filter
(global total was **10,302**; `languages=en` was **2,572**).

### What qualifies a book (from the tool's `updatecatalog.py`)

```sparql
SELECT (STRAFTER(STR(?item), "http://www.wikidata.org/entity/") AS ?itemID) WHERE {
  ?sitelink schema:isPartOf <https://{lang}.wikisource.org/> ;
            schema:about ?item .
  { ?sitelink wikibase:badge wd:Q20748092. }   # proofread
  UNION
  { ?sitelink wikibase:badge wd:Q20748093. }   # validated
  ?item wdt:P1957 ?indexPage .
}
GROUP BY ?item HAVING (COUNT(DISTINCT ?indexPage) = 1)
```

Three conditions: a **badge**, a **`P1957`**, and **exactly one** index page.

---

## 3. ⚠️ Badge adoption is wildly uneven

Measured: badge-qualified books ÷ works whose Wikisource sitelink has a recorded `P1957`.

| Wiki | Works w/ sitelink+P1957 | Badge-qualified | Share |
|------|------------------------:|----------------:|------:|
| ta | 849 | 844 | **99.4 %** |
| bn | 699 | 640 | **91.6 %** |
| en | 3,190 | 2,576 | **80.8 %** |
| fr | 5,515 | 4,157 | **75.4 %** |
| es | 1,105 | 391 | 35.4 % |
| sv | 716 | 236 | 33.0 % |
| it | 609 | 118 | 19.4 % |
| ru | 47 | 3 | 6.4 % |
| zh | 18 | 1 | 5.6 % |
| de | 253 | **4** | **1.6 %** |
| nl | 13 | **0** | **0.0 %** |

**Consequences for any dashboard, ranking, or "finished books" claim:**

1. The catalogue measures **Wikidata curation practice** as much as proofreading status.
   de.wikisource has ~654k content pages and contributes **4** books.
2. Cross-wiki comparisons built on it are invalid without stating this bias.
3. When you need true completion, combine: badge status (Wikidata) **and** the
   `Index:`-level quality distribution (§4 of the SKILL) for the specific work.

Sanity check performed: the badge count for `en` computed directly via SPARQL (2,576)
matches the API's own `?languages=en` count (2,572).

---

## 4. WSExport — EPUB / PDF generation

| Endpoint | Purpose |
|----------|---------|
| `https://ws-export.wmcloud.org/` | interactive UI (all languages; `www` = multilingual, `beta` = Beta Wikisource) |
| `https://ws-export-app.wmcloud.org/?format=epub-3&lang=en&page=Constitution_of_the_United_States_of_America` | direct download; returns `application/epub+zip` (substitute `lang` and `page`) |

This is what produces the `epub_url` values inside wsindex records. Per-wiki
behaviour (fonts, credit pages, templates) is configured via `Wikisource:WS Export`;
some configuration needs admin rights.

---

## 5. Consumers of the catalogue

| Consumer | What it is | Notes |
|----------|-----------|-------|
| **Wikisource Reader** (Android) | Mobile reader for proofread/validated works | CIS India; package `org.cis_india.wsreader`; repo `github.com/cis-india/Wikisource-Reader`; 22 languages; built on **Myne** (UI) + **Readium** (rendering); offline download, Text-to-Speech, completion indicator; **depends on wsindex** |
| **Sangkalak** | Cross-Wikisource library catalogue (Flask on Toolforge) | `https://sangkalak.toolforge.org/`; docs on bn.wikisource at `User:Mahir256/Sangkalak`; **no public API** (`/api/` → 404) |

Both are independent evidence that wsindex is a **production dependency**, not a demo.

---

## 6. The AI / OCR layer

### OCR endpoints

| Tool | Purpose |
|------|---------|
| `https://ocr.wmcloud.org/` | Wikimedia OCR — **Google Cloud Vision** (scripts Tesseract can't do) + **Tesseract** (default). Image input only. |
| `https://ws-google-ocr.toolforge.org/` | Standalone Google OCR for any Commons image URL |
| `https://wsstats.toolforge.org/` | ProofreadPage usage statistics (extension won the 2020 Coolest Tool Award) |

DjVu/PDF **text layers** (usually vendor OCR) are injected into the edit window on a
page's first edit — so "OCR quality" in practice means *the text layer you inherit*,
not only on-demand OCR.

### Where AI is contested (measured community record)

1. **Bulk OCR — the live engineering frontier.** GSoC 2026 project **T420680**
   ("Bulk OCR Improvements", umbrella **T415145**). The extension's bulk OCR exists but
   is **not production-ready**: no access control, **no review step** (output lands in
   the text layer unreviewed), no progress UI.
2. **LLM proofreading.** en.wikisource *Scriptorium* thread "Using AI to edit
   Wikisource" (2026): a fr.wikisource contributor published a small Python tool that
   edits/proofreads via ChatGPT. The companion essay
   (`User:Mathmitch7/Loosely organized thoughts on using AI to edit Wikisource`,
   Apr 2026) argues for **advisory** AI use and against unmarked AI validation —
   "validate with an asterisk … in no way guaranteed" — and distrusts LLMs as OCR engines.
3. **Bot discipline around `pagequality`.** A June 2026 bot-approval case: the bot was
   approved to upload machine-OCR text **only at quality level 1 ("Not proofread")**,
   never to mark proofread/validated; it was then opposed for exceeding its remit
   (rewriting local transcriptions, "fixing" hyphens visibly present in the scan) and for
   transcluding unproofread text into mainspace.

**The norms to encode in any AI-assisted Wikisource work:**

- **OCR may fill level 0/1 only.** Never programmatically promote a page's quality level.
- **Don't pre-empt the proofreader.** Community position: *"OCR dump ⇒ no one works on
  it immediately ⇒ discourages further work"* — contribute OCR only where someone will
  proofread it soon.
- **Fidelity beats plausibility.** Never "correct" a spelling/hyphenation that is
  present in the scan; that is a proofreading judgement, not a machine's.
- **AI is an advisor, not a validator.** Any AI-touched validation must be labelled.

---

## 7. Namespace heterogeneity (T74525) — verified table

| Wiki | Page ns | name | Index ns | name |
|------|--------:|------|---------:|------|
| en | 104 | Page | 106 | Index |
| fr | 104 | Page | 112 | **Livre** |
| de | 102 | Seite | 104 | Index |
| pl | 100 | Strona | 102 | Indeks |
| it | 108 | Pagina | 110 | Indice |
| es | 102 | Página | 104 | Índice |
| nl | 104 | Pagina | 106 | Index |
| ru | 104 | Страница | 106 | Индекс |
| zh | 104 | Page | 106 | Index |
| sv | 104 | Sida | 108 | Index |
| pt | 106 | Página | **104** | **Galeria** |
| bn | 104 | পাতা | **102** | **নির্ঘণ্ট** |
| ml | 106 | താൾ | **104** | **സൂചിക** |
| ta | **250** | பக்கம் | **252** | அட்டவணை |

Resolved with `assets/ws_namespace_resolver.py` (content-model probe, §SKILL).

Three independent failure modes for naive code:

1. **IDs are not portable** — 100, 102, 104, 106, 108, and even 250.
2. **Names are not portable** — fr calls it `Livre`, pt `Galeria`, bn `নির্ঘণ্ট`.
3. **The "Index = Page + 2" convention is false** — sv is Page 104 / Index 108, and
   on pt/bn/ml the Index ID is **lower** than the Page ID. Applying the offset rule
   lands on Portal namespaces on fr (`Portail`), bn (`প্রবেশদ্বার`), pt (`Em Tradução`)
   and ml (`കവാടം`) — silent false positives.

See **T74525** (open since 26 Oct 2014) and **T325505**.
