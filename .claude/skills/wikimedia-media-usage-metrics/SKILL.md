---
name: wikimedia-media-usage-metrics
description: Measure and count the use of Wikimedia media files — transfers (mediacounts/mediarequests), embeds (GlobalUsage), reach (pageviews/CIM), external reuse — with verified gotchas, a decision tree, and a live report pipeline
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access, wikimedia-database, wikimedia-pageviews, wikimedia-commons, wikimedia-commons-sparql, wikimedia-petscan]
skill_discovery_hints:
  - keywords: ["media usage", "file usage", "image usage", "media reach", "file reach", "media metrics", "usage analytics"]
  - keywords: ["mediacounts", "mediarequests", "GlobalUsage", "globalimagelinks", "imagelinks", "file transfer counts", "image serve counts"]
  - keywords: ["how many times was image served", "where is file used", "pageviews of articles using image", "GLAM impact", "GLAM metrics"]
  - keywords: ["BaGLAMa", "GLAMorgan", "GLAMorous", "external reuse", "hotlink", "referer", "media transfer counts"]
last_verified: 2026-09-05
---

# Media Usage Metrics — Measuring Use of Wikimedia Files

> ⚠️ **User-Agent required** on every HTTP call below. See **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)**.
> A layperson-facing version of this material lives at `references/layperson-guide.md` (send to non-Wikimedia audiences).

## 1. The four meanings of "use" (read this first)

People mean four different things by "use of a media file". Mixing them is the #1 source of wrong numbers.

| Axis | Question | Primary signal | Key caveat |
|---|---|---|---|
| **Transfers** | How many times were the file's bytes *served*? | `mediacounts` / `mediarequests` | Counts requests, not humans; thumbnails count |
| **Usage (embeds)** | *Where* is the file transcluded? | `GlobalUsage` / `imagelinks` | Tells *where*, never *how often* |
| **Reach** | How many people *viewed pages* containing it? | pageviews / CIM | Page loads ≠ image loads |
| **External reuse** | Is it hotlinked *off-Wikimedia*? | `mediacounts` referer fields | The **only** source that sees off-wiki use |

## 2. Master index

| # | Method | Measures | Pre-computed / on-demand | Access |
|---|---|---|---|---|
| 1 | Mediacounts (dumps + Hive `wmf.mediacounts`) | Transfers, bytes, referer split | Pre (daily) | Public dumps / cluster |
| 2 | Mediarequests AQS | Transfers per-file/top | On-demand API (pre-aggregated) | Public REST |
| 3 | Raw `webrequest` (Data Lake) | Anything, custom | On-demand compute | WMF cluster creds |
| 4 | GlobalUsage (API + `globalimagelinks`) | Cross-wiki embeds | Maintained table, on-demand query | Public API / SQL |
| 5 | `imagelinks` (SQL) | Local embeds per wiki | On-demand SQL | Toolforge replicas |
| 6 | `imageusage` (Action API) | Local embeds | On-demand API | Public |
| 7 | GLAMorous / PetScan | PetScan: file-population selection; GLAMorous: embeds by category | On-demand tools | Public web tools |
| 8 | Pageviews API | Reach (File page + embeds) | On-demand API (pre-aggregated) | Public REST |
| 9 | Commons Impact Metrics / AQS | Reach, leverage, edits (GLAM) | Pre (monthly) | Public API + dumps |
| 10 | BaGLAMa 2 / GLAMorgan | Legacy GLAM reach | Pre (cron) / on-demand | Public tools |
| 11 | Mediacounts referer fields | External/off-wiki reuse | Pre | Dumps / cluster |
| 12 | SDC SPARQL (WCQS/QLever) | Discovery (depicts, etc.) | On-demand | Public / OAuth |
| 13 | EventStreams | Real-time usage *changes* | Real-time push | Public SSE |
| 14 | **Sightglass** (Toolforge) | Transfers for files/category trees, shareable | Pre (mediacounts) + on-demand queries | Public web + OAuth API ([repo](https://gitlab.wikimedia.org/repos/wikiportraits/sightglass)) |

## 3. Method deep-dive (endpoints + gotchas)

### 3.1 Mediacounts — dumps + Hive `wmf.mediacounts`
Daily TSV, one row per file. Columns: `total`, `original`, `transcoded_image` (width buckets 0-199 … 1000+), `transcoded_audio`, `transcoded_movie` (height buckets), `total_response_size`, `referer_internal/external/unknown`.
- **Caveats:** HTTP 304s NOT counted; MediaViewer prefetch inflates image counts up to ~50%; stream "jump back to start" double-counts; no bot filtering (status-code based only); not per-wiki.
- **Access:** `https://dumps.wikimedia.org/other/mediacounts/daily/` (TSV); Hive table `wmf.mediacounts` (hourly Parquet) for cluster users. **No cluster or dumps?** Use the Sightglass web tool/API (§3.14) for per-file and category-tree queries.
- **Ideal:** bulk/historical GLAM reporting, bandwidth/byte-volume analysis, offline batch, referer attribution.

### 3.2 Mediarequests AQS — `metrics/mediarequests/*`
Endpoints (all verified 2026-08-14): `aggregate/{referer}/{media_type}/{agent_type}/{granularity}/{start}/{end}`, `top/{referer}/{media_type}/{year}/{month}/{day}`, `per-file/{referer}/{agent_type}/{file_path}/{granularity}/{start}/{end}`.
- `referer` ∈ all-referers/internal/external/unknown/**none**/search-engine **or a project domain** (e.g. `en.wikipedia`); `media_type` ∈ image/audio/video/all-media-types; `agent_type` ∈ user/spider/all-agents — **`automated` is not a valid value (HTTP 400), and there is no automated bin in the data at all: `all-agents` = `user` + `spider` exactly** (diff 0, verified 2026-09-05), so automated clients' image requests are UA-counted as **`user`**. The pageview API's heuristic `automated` split does not exist here — for request-per-pageview ratios use pageviews(**user + automated**) as the denominator, or you inflate by 1/(1 − automated share) on exactly the high-agent articles. `granularity` ∈ daily/monthly. Data since 2015 (agent split 2019-05-17).
- **GOTCHA (verified 2026-09-05): the referer classes are NOT a partition of all-referers.** Project-hostname values (e.g. `en.wikipedia`) hold 75–91% of a file's requests; internal/external/search-engine/none/unknown cover the remainder, and **`internal` is a rump class (~0.1%)** — do not read it as "rendered by a Wikimedia page". **`none` (no Referer header) is real and large** — apps and date-keyed API clients land there, not in `unknown`: on a TFA-feature day the day-before bump was 96.7% referer=none.
- **GOTCHA (verified):** `per-file` `file_path` MUST be the upload path URL-encoded **with the leading slash** — e.g. `/wikipedia/commons/0/00/Crab_Nebula.jpg` → `%2Fwikipedia%2Fcommons%2F0%2F00%2FCrab_Nebula.jpg`. Omitting the leading slash returns 404.
- **Article attribution trick (verified 2026-09-05):** `per-file` with a **project-domain referer** (e.g. `en.wikipedia`) counts that file's requests served *to that wiki's pages*. Restrict to **single-host files** — `globalusage` exactly one page on the target wiki — and the series is attributable to that one article. Worked case: `Calvin-cycle4.svg` (1 en page: `Wikipedia:What Wikipedia is not`) → de-embedding it from that page collapsed its en series −85.4% in one month while a still-embedded control rose +22% (seasonality). Media requests are page-driven: ≈1.5 requests/pageview/image, ~86% of a single-host file's traffic attributable to its host article.
- **GOTCHA (verified 2026-09-05):** `globalusage` caps at **500 entries and truncates BEFORE returning all wikis** — a high-embed file can report zero pages on the target wiki while still being on the page (Walnut.png: 500 results across 17 wikis, 0 en pages reported, embedded in en articles). Never read `here==0` as "unused"; paginate (`gucontinue`) or cross-check `prop=images`.
- Inherits mediacounts caveats; filters self-identified bots but not automated traffic; cannot break down per wiki page (except via the single-host trick above).
- **Ideal:** quick per-file request counts, top-media leaderboards, article-level media-request series for single-host files.

### 3.3 Raw `webrequest` (Data Lake)
Source of #1/#2. Hive/Spark/Presto over `wmf.webrequest`. Needs WMF analytics cluster + Kerberos. Full control (status, referer, wiki, UA, geo=private, hourly), dedupe prefetch, custom bot filtering.

### 3.4 GlobalUsage — API + `globalimagelinks` table
Definitive cross-wiki "where used".
- **API (verified):** `action=query&prop=globalusage&titles=File:Name.jpg&format=json&guprop=namespace` → `{wiki, title, ns}` per using page. Paginates via `gucontinue` + `gulimit`.
- **GOTCHA (verified):** globalusage is its OWN prop — `prop=globalusage`, NOT `iiprop=globalusage` (returns "Unrecognized value"). `guprop=title` is also unrecognized (title is always returned); use `guprop=namespace` for the ns field.
- **SQL:** `commonswiki_p.globalimagelinks` (`gil_wiki`, `gil_page`, `gil_to`, `gil_page_namespace_id`) — bulk joins/aggregates ("files used in most wikis") in one query.
- **Ideal:** per-file usage maps, cross-wiki reach (distinct wiki/page counts), feeding pageview lookups.

### 3.5 `imagelinks` (per-wiki SQL) + 3.6 `imageusage` (Action API)
- `imagelinks`: `{db}_p.imagelinks` (`il_from`, `il_to`) — local usage incl. non-Commons images. Single-wiki only.
- `imageusage`: `list=imageusage&iutitle=File:…` — on-demand local usage, no SQL needed.

### 3.7 GLAMorous / PetScan — population selection, not counting

PetScan's role in metrics workflows is **upstream: choosing the file set to
measure**. It does **not** emit usage counts — output params like
`globalusage=1` or `file_usage=1` are silently ignored (verified 2026-08-14).
Useful functions (verified):

- **Category-tree enumeration** in namespace 6 with `depth` — e.g. 360
  bitmap files in `Crab_Nebula` at depth 1 via `file_type=bitmap`.
- **Filters:** `file_type` (bitmap/drawing/video/audio/office/multimedia),
  license templates (`templates_yes=PD-US`), Wikidata/SPARQL sources
  (`depicts`, camera, …), ORES.
- **Bulk export** (JSON/TSV/CSV) feeds the measurement step: enumerate with
  PetScan → measure transfers with mediarequests/Sightglass (§3.14) →
  reach via pageviews/CIM.

Full parameter surface: the **[wikimedia-petscan](../wikimedia-petscan/SKILL.md)** skill.
GLAMorous = global usage per category (embeds), slow at scale.

### 3.8 Pageviews API — `metrics/pageviews/*`
API reference and media-views (mediarequests) coverage live in the
**[wikimedia-pageviews](../wikimedia-pageviews/SKILL.md)** skill. Unique gotchas
verified for this workflow:
- **GOTCHA (verified):** File-page views ≈ interest in the file itself, NOT media views. Example: `File:Crab_Nebula.jpg` ≈ 4–12 File-page views/day vs **211,688** mediarequests/day (thumbnails embedded in articles).
- **GOTCHA (verified):** `per-article` returns **HTTP 404 for pages with no pageview data** (e.g. low-traffic user/talk pages) — the page still exists, it just has zero records in the window. Treat 404 as 0 views, not an error (the pipeline script does this).
### 3.9 Commons Impact Metrics / Commons Analytics AQS

> ⚠️ **NOT on-demand.** CIM is pre-computed **monthly** for **allow-listed**
> categories only (~1,755 GLAM/campaign categories, depth <= 7). If the
> category is not registered, queries return HTTP 404 (body "...not loaded
> yet") — that is the not-registered signal, not an API error. You cannot
> get same-day numbers for an arbitrary category; use the §5 live pipeline
> for anything not on the list.

**Registration is a staff cycle, not an API call:** add
`{{Views from category}}` to the category page -> hidden tracking category ->
staff add it to the allow-list at month-end (submit by the 20th) -> data
starts the following month, **no retroactive backfill**. A Phabricator
ticket (project `Commons-Impact-Metrics-Requests`) is created automatically
for documentation; renames/removals go through the same monthly cycle via
the pre-filled Phabricator form. Full process: the
**[wikimedia-commons](../wikimedia-commons/SKILL.md)** skill.

Endpoint table, `category-scope`/`edit-type` values, and the try-CIM-
then-fallback pattern also live in **wikimedia-commons**. Gotchas unique
to usage-metrics workflows:
- **GOTCHA (verified):** `category-metrics-snapshot` has **no pageviews
  field** — use `pageviews-per-category-monthly`.
- **Caveats:** monthly drift (pageviews attributed from the 1st even if a
  file was added mid-month); pageview-based (not mediarequests); category
  rename breaks the pipeline until the allow-list is updated.

### 3.10 BaGLAMa 2 / GLAMorgan / GLAM Wiki Dashboard
Legacy community GLAM tools (Magnus Manske) that CIM was built to replace. Prone to outages/inconsistency. `https://glamtools.toolforge.org/baglama2/`, `…/glamorgan.html`.

### 3.11 Mediacounts referer fields — the ONLY external-reuse signal
`referer_external` = transfers with a non-WMF referer (hotlinking/embedding on external sites, apps, AI crawlers). No other method sees off-wiki use.

### 3.12 SDC SPARQL (WCQS / QLever)
Discovery only, not counting — find files by `depicts`/license/camera, then feed into #2/#4/#8. WCQS (`commons-query.wikimedia.org`, OAuth) or QLever (`qlever.dev/wikimedia-commons`, no auth). See **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)**.

### 3.13 EventStreams
Real-time file *usage changes* (page adds/removes file) via `stream.wikimedia.org`, not view counts.

### 3.14 Sightglass — Toolforge UI + API over mediacounts (WikiPortraits project)

[Sightglass](https://sightglass.toolforge.org/) (`sightglass.toolforge.org`) queries the **mediacounts** dataset server-side for
individual files OR category trees (subcategory depth 0-10, up to 300,000
files per category query), with shareable results. Made for GLAM/impact
reporting; fills the gap left by GLAMorgan (current usage only) and CIM
(opt-in, misses short bursts). Data since 2015-01-01, ~2-day lag.

- **Web UI:** browse queries on the dashboard; queries auto-delete after 7
  days unless saved. **Login (Wikimedia OAuth, identity-only) is required to
  run queries** — for load management.
- **API (authenticated, except jobs):**
  - `GET /api/media/stats?filename=File:X.jpg&start=YYYYMMDD&end=YYYYMMDD&granularity=daily|monthly&referer=&agent=` — per-file mediacounts (defaults: last 30 days, all-referers, all-agents).
  - `POST /api/category/stats` — JSON `{category, start, end, granularity, depth (0-10), referer, agent}`; **async** — returns `{jobId, statusUrl}` immediately.
  - `GET /api/jobs/:jobId` — job progress/results; **no auth needed (shareable permalink)**.
  - `GET /api/media/search?query=...` — Commons file search.
- **Gotchas:** counts inherit mediacounts caveats (bot/scraper/prefetch inflation, 304s not counted); unauthenticated calls return 401; category jobs can take a while (300k-file cap).

## 4. Decision tree

```
Want to choose WHICH files to measure (category tree × filters)?
  → PetScan enumeration (namespace 6) → feed titles into the branches below
Want "how many times was the file served?"
  → quick single file: mediarequests per-file
  → whole category tree, no cluster: Sightglass (mediacounts UI/API)
  → bulk/historical: mediacounts dumps
  → custom/bespoke: raw webrequest (cluster)
Want "where is it used, on which wikis?"
  → GlobalUsage API (single file) / globalimagelinks SQL (bulk)
Want "how many people saw it in articles?"
  → GlobalUsage → pageviews (arbitrary files)
  -> CIM/Commons Analytics — only if the category is already allow-listed (else the live pipeline, §5)
Want "is it reused off-wiki?"
  → mediacounts referer_external
Want "GLAM institutional impact dashboard"
  → CIM / Commons Analytics API
Want "real-time usage changes"
  → EventStreams
```

## 5. The live-computation pipeline (arbitrary, non-allow-listed files)

Works for ANY file today, no allow-list. Implemented in `scripts/media_usage_report.py`.

1. **Resolve title → upload path** — `prop=imageinfo&iiprop=url` (Action API). ⚠️ GOTCHA (verified 2026-08-14): the returned `url` carries tracking params (`?utm_source=commons.wikimedia.org&utm_campaign=imageinfo&utm_content=original`). **Strip everything from `?` onward** before using it as a storage path, or `mediarequests`/`mediacounts` lookups return 404 (the script does this).
2. **Where used** — `prop=globalusage` (paginate) → `[{wiki,title}]`; count distinct wikis/pages.
3. **Transfers** — `mediarequests/per-file` (encode path WITH leading slash).
4. **Reach** — batch `pageviews/per-article` over using pages; sum. Cap with `--max-pages` (default 50) and flag truncation. ⚠️ This is a *lower-bound sample* (first N using pages, not the most-viewed); exact reach needs pageviews for ALL using pages, or CIM when the file is allow-listed.
5. **File-page interest** — `pageviews/per-article` for the `File:` title.
6. Combine into one report.

## 6. Verification log (2026-08-14, all live-tested)

- mediarequests `top` + `aggregate` + `per-file` all return data; `per-file` leading-slash encoding confirmed.
- GlobalUsage via `prop=globalusage` confirmed; `iiprop=globalusage` and `guprop=title` both rejected.
- Commons Analytics `category-metrics-snapshot` returns real data (`Smithsonian_American_Art_Museum`: 10,614 files deep, 1,549 used, 176 wikis, 3,809 pages); `media-file-metrics-snapshot` on a non-allow-listed file → 404.
- Pageviews `per-article` on `File:Crab_Nebula.jpg` returns File-page views.
- `imageinfo&iiprop=url` appends `?utm_source=…&utm_campaign=imageinfo&utm_content=original` tracking params to the URL (verified) — must be stripped before reuse.
- Reach sample-bias magnitude (verified): same `--max-pages` cap → `File:Earth.jpg` reach **7,279** vs `File:Crab_Nebula.jpg` reach **279**, because Earth's first-50 using-pages are high-traffic articles while Crab Nebula's are low-traffic featured-picture galleries. Don't trust the DIY reach number without this context.

## 7. Cross-references

| Skill | Why |
|---|---|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | UA format, rate limits, endpoints |
| **[wikimedia-database](../wikimedia-database/SKILL.md)** | `globalimagelinks`/`imagelinks` SQL via Toolforge |
| **[wikimedia-pageviews](../wikimedia-pageviews/SKILL.md)** | pageviews API + `pageview_daily_average` sorting |
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | Commons Analytics endpoint table + CIM allow-list process |
| **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** | SDC/SPARQL discovery (WCQS/QLever) |
