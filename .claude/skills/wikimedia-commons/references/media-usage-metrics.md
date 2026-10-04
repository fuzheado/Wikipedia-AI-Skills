# Measuring Media-File Usage in Wikimedia — Full Method Matrix

Verified against live APIs/datasets 2026-08. Answers "how is this Commons file
(or category of files) being used?" — a question that splits into **four distinct
axes**. Do not conflate them.

## The four axes

| Axis | Question | Primary signal |
|---|---|---|
| **Transfers** | How many times were the file's *bytes* served? | `mediacounts` / `mediarequests` |
| **Usage (embeds)** | *Where* is it transcluded? | `GlobalUsage` / `imagelinks` |
| **Reach** | How many people *viewed pages* containing it? | pageviews / CIM |
| **External reuse** | Is it hotlinked *off-Wikimedia*? | `mediacounts` referer fields (the **only** source) |

A file can have huge transfer counts (thumbnails on a high-traffic article) yet
near-zero File-page views, and vice-versa. Example (2026-08-10): `Crab_Nebula.jpg`
= 211,688 requests but only ~9 File-page views/day.

## Method index

| # | Method | Measures | Pre-computed / on-demand | Access |
|---|---|---|---|---|
| 1 | Mediacounts (dumps + Hive) | Transfers, bytes, referer | Pre (daily) | Public dumps / cluster |
| 2 | Mediarequests AQS | Transfers per-file/top | On-demand API | Public REST |
| 3 | Raw `webrequest` (Data Lake) | Anything, custom | On-demand compute | WMF cluster creds |
| 4 | GlobalUsage (API + table) | Cross-wiki embeds | Maintained table, on-demand query | Public API / SQL |
| 5 | `imagelinks` (SQL) | Local embeds per wiki | On-demand SQL | Toolforge replicas |
| 6 | `imageusage` (Action API) | Local embeds | On-demand API | Public |
| 7 | GLAMorous / PetScan | Embeds by category | On-demand tools | Public web tools |
| 8 | Pageviews API | Reach (File page + embeds) | On-demand API | Public REST |
| 9 | Commons Impact Metrics (CIM) | Reach, leverage, edits (GLAM) | Pre (monthly) | Public API + dumps |
| 10 | BaGLAMa 2 / GLAMorgan | Legacy GLAM reach | Pre (cron) / on-demand | Public tools |
| 11 | Mediacounts referer fields | External/off-wiki reuse | Pre | Dumps / cluster |
| 12 | SDC SPARQL (WCQS/QLever) | Discovery (depicts, etc.) | On-demand | Public / OAuth |
| 13 | EventStreams | Real-time usage *changes* | Real-time push | Public SSE |

## Methods + gotchas

### 1. Mediacounts — dumps + Hive `wmf.mediacounts`
Daily TSV, one row per file. Columns: `total`, `original`, `transcoded_image`
(width buckets 0–199…1000+), `transcoded_audio`, `transcoded_movie`,
`total_response_size`, `referer_internal/external/unknown`.
- Caveats: HTTP 304 **not** counted; MediaViewer prefetch inflates image counts up
  to **~50%**; streamed-media "jump to start" double-counts; no bot filtering
  (status-code based only); not per-wiki. History since 2015-01-01.
- Dumps: `https://dumps.wikimedia.org/other/mediacounts/daily/`
- Source: https://wikitech.wikimedia.org/wiki/Data_Platform/Data_Lake/Traffic/Mediacounts

### 2. Mediarequests AQS — `metrics/mediarequests/{aggregate,top,per-file}`
Filters: `referer` (all-referers/internal/external/unknown — `all` is **not** valid and returns
HTTP 404), `media_type` (image/audio/video/document/other/all-media-types), `agent_type`
(user/spider/all-agents), `granularity` (daily/monthly). All values probed live 2026-10-04.
- **GOTCHA (verified 2026-10-04):** `agent_type` has **no `automated` bin** here —
  `agent_type=automated` is invalid and returns HTTP 400. Unlike the pageviews
  AQS `agent` parameter, which *does* accept `automated` (a heuristic split of
  non-human traffic), mediarequests only splits self-identified bots: use
  `user`, `spider` or `all-agents` — the error body lists the allowed set
  (`[all-agents, user, spider]`). Verified live:
  `/metrics/mediarequests/aggregate/all-referers/image/{automated→400|user→200}/monthly/…`
- **GOTCHA (verified):** `per-file` path MUST be URL-encoded **with the leading
  slash**: `%2Fwikipedia%2Fcommons%2F0%2F00%2FCrab_Nebula.jpg`. Omitting the leading
  slash → 404. `top` returns `file_path` WITH a leading slash (e.g.
  `/wikipedia/commons/0/00/Crab_Nebula.jpg`).
- Inherits mediacounts caveats. Per WMF: "filters self-identified bots, not
  automated traffic."
- Source: https://wikitech.wikimedia.org/wiki/Analytics/AQS/Mediarequests

### 3. Raw `webrequest` (Data Lake)
Source table for #1/#2. Hive/Spark/Presto. Requires WMF cluster + Kerberos. Full
control (status/referer/wiki/UA/geo, dedupe prefetch, custom bot filtering).

### 4. GlobalUsage — `prop=globalusage` + `globalimagelinks` table
- **GOTCHA (verified):** it is a **separate prop module**, NOT `iiprop`:
  `action=query&prop=globalusage&titles=File:X.jpg&guprop=namespace&gulimit=500`.
  Using `iiprop=globalusage` → *"Unrecognized value for parameter iiprop"*. `guprop`
  accepts `namespace` (NOT `"title"`; title is always returned).
- Response per page: `{wiki, title, ns}`.
- SQL table: `commonswiki_p.globalimagelinks` (`gil_wiki`, `gil_page`, `gil_to`,
  `gil_page_namespace_id`).
- Tells WHERE used — never how often viewed. Source:
  https://www.mediawiki.org/wiki/Extension:GlobalUsage

### 5. `imagelinks` (SQL, per-wiki) — `enwiki_p.imagelinks` (`il_from`, `il_to`). Local only.

### 6. `imageusage` (Action API) — `list=imageusage&iutitle=File:X.jpg`. Local usage without SQL.

### 7. GLAMorous / PetScan — tools over GlobalUsage/imagelinks for category-level usage.

### 8. Pageviews API — `metrics/pageviews/per-article/…`
Two uses: (a) File-page views (interest in the file — use project `commons.wikimedia`
+ `File:` title); (b) **reach** = sum of pageviews of all pages GlobalUsage says use
the file. Counts *page loads*, not *image loads*. Requires the GlobalUsage →
pageviews two-step.

### 9. Commons Impact Metrics (CIM) / Commons Analytics AQS
Base: `https://wikimedia.org/api/rest_v1/metrics/commons-analytics/` · CORS `*` ·
dates in `YYYYMM01` (end-exclusive). 14 endpoints — full list in this skill's SKILL.md
and `…/commons-analytics/api-spec.json`.
- **Allow-list only (~1,755 GLAM/campaign categories).** Unregistered → 404 "not
  loaded yet" — that 404 **is** the registration signal, not an error.
- Monthly only; max depth 7; **no retroactive backfill**; **monthly drift**
  (pageviews attributed from the 1st even if a file was added mid-month);
  pageview-based (not mediarequests). Category renames break the pipeline until the
  allow-list is updated.
- Source: https://wikitech.wikimedia.org/wiki/Commons_Impact_Metrics

### 10. BaGLAMa 2 / GLAMorgan / GLAM Wiki Dashboard — legacy community GLAM tools CIM
was built to replace (outages, inter-tool inconsistency).

### 11. Mediacounts referer fields — the ONLY external-reuse signal.
`referer_external` = hotlinking/embedding off-Wikimedia (blogs, news, apps, crawlers).
No other method (GlobalUsage, pageviews, CIM) sees anything off-wiki.

### 12. SDC SPARQL (WCQS/QLever) — discovery, NOT a usage counter. Feed results into #2/#4/#8.

### 13. EventStreams — real-time usage *changes* (page adds/removes a file), not view counts.

## Decision guide

| You want… | Use |
|---|---|
| "How many times was the file served?" | Mediarequests AQS (quick) / Mediacounts dumps (bulk) |
| "Where is it used, on which wikis?" | GlobalUsage API / `globalimagelinks` SQL |
| "How many people saw it in articles?" | GlobalUsage → Pageviews (or CIM if GLAM + allow-listed) |
| "Is it reused off-wiki?" | Mediacounts `referer_external` |
| "GLAM institutional impact dashboard" | Commons Impact Metrics / Commons Analytics |
| "Bespoke research / custom metric" | Raw `webrequest` on the Data Lake |
| "Real-time usage changes" | EventStreams |

## Live pipeline for arbitrary (non-allow-listed) files
`GlobalUsage` (get using pages) → batch `pageviews/per-article` (reach) +
`mediarequests/per-file` (transfers). This is the "live computation" path for any
file today, no allow-list required.
