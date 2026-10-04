# Wikimedia Commons mass-upload tooling: landscape and gaps

Condensed research on frustrations with Commons mass-upload tools, for evaluating a
**new** upload tool. Compiled Aug 2026 from the GLAM CSI report, `Commons:Upload_tools`,
`Commons talk:Flickypedia` (through July 2026), and the commons-l mailing list.

**Analytical framing that works for this class of question** (apply it, don't just list
complaints):
1. **Constituents differ** — "not all uploaders are equal." GLAM collections managers,
   Wikimedians-in-Residence, campaign managers (WLM), transfer volunteers, bot operators,
   and edit-a-thon educators each have a *different* core frustration.
2. **User rights change what "fix it later" means** — `upload_by_url` and Flickr import are
   gated to admins/reviewers/autopatrollers; license review can't be self-done; batch
   post-processing needs a bot flag. Whether ELT+T is even *available* is a rights question.
3. **ETL vs ELT+T** — what *must* be right at upload vs what's fixable post-upload (below).

Prefer the synthesis delivered as a **single self-contained Markdown report file**,
not a long chat message.

## Primary sources (fetch first)
- **GLAM CSI report 2024** (PDF on Commons): `File:GLAM_CSI_report_2024.pdf` — survey + 7
  persona/user-story narratives. The "ETL vs ELT" framing originates here.
- **Commons:Upload_tools** — the ~30-tool inventory (many dead/abandoned).
- **Commons talk:Flickypedia** — 2023–2026 failure log of the Flickr Foundation tool.
- **Commons:File naming** — the naming policy (auto-generated names banned; renames costly).
- **commons-l** mailing list (hyperkitty archive).

## Tool status snapshot (mid-2026)
| Tool | Fate |
|---|---|
| GLAMwiki Toolset (Europeana) | Removed 2022 — the one funded/staffed mass-upload tool |
| Pattypan (Yarl) | Unmaintained; its uploads get 80M+ views/month |
| Commonist | "Not working" |
| VicuñaUploader | Login bug in stable release |
| Flickr2Commons (Magnus Manske) | One-person tool |
| Flickypedia (Flickr Foundation) | Engineer left + funding collapsed → reproduced the exact problem it was built to fix |

>50% of the top-13 GLAM tools are maintained by one person (Magnus Manske). No systematic
tool-assessment/prioritization exists ("lacks formal methods to identify and prioritize
mission-critical tools" — GLAM CSI).

## Headline: maintenance before features
The single biggest frustration is the **bus factor** — tools die when their maintainer leaves.
A new tool's #1 feature is sustainability (funded/staffed or community multi-maintainer +
public handoff plan), not any specific capability.

## ETL vs ELT+T (the core distinction)
- **Must be right at upload (irreversible / deletion-triggering):** license + source + author
  (copyright chain), file format (MP4 blocked → WebM/OGV), file name (fix costly), attribution
  preservation (author/geolocation).
- **Fixable later (but the fix layer is broken):** categories, captions, depicts (SDC),
  descriptions, translations, geolocation, dedup, resolution upgrades. Broken because Cat-a-lot
  is API-throttled, SDC writes need separate tools (QuickStatements/pywikibot/OpenRefine), and
  WCQS requires auth (blocks scripting).
- **Split-brain hazard:** Flickypedia wrote metadata *only* to SDC → cropped/derived files lose
  description/date/source/author. A tool must write to **both SDC and wikitext**.
- **No-code transform gap:** filename/metadata mapping is regex/GREL/pywikibot today. Should be
  token templating — `IMG_23828342.jpg` → `Paris - 2026-06-23 - Eiffel Tower - 23828342.jpg` —
  driven by EXIF `DateTimeOriginal` (date), GPS (location), user input (subject), retained
  original ID (traceability). Policy makes meaningful names mandatory and renames deliberately
  costly, so this transform must happen at upload time.
- **Reconciliation gap:** no diff of "what's already on Commons" vs "what I have"; checksum
  matching is imperfect. Should be built in (persistent IDs + checksum/URL matching).
- **Metadata mapping is manual/lossy:** semi-structured `{{Artwork}}`/`{{Information}}` hard to
  parse programmatically; no persistent source IDs → round-tripping (BHL story) unsupported.

## Key quotes (verbatim, citable)
- Jmabel on Flickypedia: *"90% of the point of this thing was supposed to be to have a more
  reliable, funded development and maintenance commitment compared to Flickr2Commons. I sure
  don't see any signs of that."*
- GLAM CSI: *"more of an iterative ELT (extract-load-transform) process rather than a
  traditional ETL process."*
- File naming policy: *"Meaningful – Names should not consist entirely of auto-generated
  letters and numbers, such as 'DSC123456.jpg'."* and *"select high-quality filenames during
  the initial upload or soon afterwards, as otherwise they will likely never be improved."*

## Key permalinks
- GLAM CSI report: https://commons.wikimedia.org/wiki/File:GLAM_CSI_report_2024.pdf
- Commons:Upload_tools: https://commons.wikimedia.org/wiki/Commons:Upload_tools
- Commons:File_naming: https://commons.wikimedia.org/wiki/Commons:File_naming
- Commons talk:Flickypedia: https://commons.wikimedia.org/wiki/Commons_talk:Flickypedia
  - Big picture question (funding collapse): `#Big_picture_question`
  - Cannot login (401 OAuth): `#Cannot_login`
  - Metadata not transferring when cropped: `#Description,_source,_date_etc_not_transferring_over_when_cropped`
  - License review ambiguous: `#Uploaded_with_Flickypedia_template_and_License_Review`
  - Failure to detect duplicates: `#Failure_to_detect_some_duplicates`

## Fetch technique notes (reusable gotchas)
- **Wikitext:** `action=parse&prop=wikitext&format=json&formatversion=2` (cleaner than HTML).
- **Download a Commons file:** get the real URL via `action=query&titles=File:X&prop=imageinfo&
  iiprop=url` — do NOT guess the `/wikipedia/commons/<hash>/` path (returns "File not found").
- **PDF text extraction:** `uv venv .venv && uv pip install --python .venv/bin/python pymupdf`,
  then `import pymupdf; doc = pymupdf.open(f); "".join(p.get_text() for p in doc)`. Note: the
  global `uv` lives at `/usr/local/bin/uv`, not inside the venv.
- **Mailing-list search:** `https://lists.wikimedia.org/hyperkitty/search?q=...&
  mlist=commons-l@lists.wikimedia.org` — parse `/hyperkitty/list/<list>/message/<ID>/` hrefs for
  thread subjects.
- All Wikimedia API calls require a descriptive `User-Agent` header (see wikimedia-api-access).
