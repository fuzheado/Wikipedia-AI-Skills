# Historic Page Reconstruction Reference

How to recover **what a page looked like at a past date** — the Main Page is the
classic hard case — including the templates and images as they were then.

## The problem, precisely

MediaWiki always expands templates and modules from their **current** revisions.
So neither `action=parse&oldid=<id>` nor the REST endpoint
`/w/rest.php/v1/revision/<id>/html` reproduces what readers actually saw. The
wikitext of the old revision is faithfully returned; everything transcluded into
it is today's version.

The limitation is documented at <https://www.mediawiki.org/wiki/Help:History/en>:
*"You can only use the current versions of templates and images unless you rename
old versions."*

**Measured example** (probe run 2026-09-12, enwiki Main Page):

| Item | As of 2016-06-01 | Current (2026-09-14) |
|---|---|---|
| Main Page revision | `696846920` (last edited 2015-12-26) | — |
| Templates resolved by `action=parse&oldid=696846920` | 79 (all from **today's** revisions) | — |
| `Template:In the news` | 2,445 bytes | 1,852 bytes |
| `Template:Did you know` | 2,482 bytes | 1,840 bytes |
| `Template:Main Page banner` | 406 bytes | 593 bytes |

The Main Page's own history is also misleading: since the late 2000s nearly all
of its text is transcluded from cascade-protected templates, so its history shows
only changes to *which sections are included*. See
<https://en.wikipedia.org/wiki/Wikipedia:Main_Page_history>.

## Option 1 — WikiHist.html (reconstructed full revision history, enwiki)

The only project that has done the work at scale.

- **What:** English Wikipedia revision history `2001-01-01 → 2019-03-01` parsed to
  HTML — 580M revisions of 5.8M articles, **7 TB** gzip-compressed.
- **How they solved the template problem:** they patched MediaWiki and
  *"intercepted the database calls to return the version of the templates
  available at the revision creation"* — i.e. every macro expands at the version
  active when that revision was made.
- **Where:** data <https://archive.org/details/WikiHist_html> · code
  <https://github.com/epfl-dlab/WikiHist.html> · pipeline
  <https://github.com/epfl-dlab/enwiki_history_to_html> · metadata
  <https://doi.org/10.5281/zenodo.3605388> · paper
  <https://arxiv.org/abs/2001.10256> (ICWSM 2020)
- **Caveats:** enwiki only; ends March 2019; **boilerplate (page header, footer,
  sidebars) is excluded**, so it is article HTML rather than a picture of the
  rendered page; and **deleted templates/modules cannot be expanded at all**
  (deleted history is gone) — raw wikitext or Lua errors leak into the output.
  That last point is inherited from Wikipedia's deletion policy, not a tool bug.

## Option 2 — Official rendered-HTML dumps (current revisions only)

**Not retroactive — and the mirror that existed here stopped.**

- **Wikimedia Enterprise HTML dumps:** <https://dumps.wikimedia.org/other/enterprise_html/>
  The `runs/` directory contains exactly **four** runs — `20250201`, `20250220`,
  `20250301`, `20250320` — with files named
  `<wiki>-NS<n>-<date>-ENTERPRISE-HTML.json.tar.gz` (plus `-STATS.json`); the last
  run holds 6,540 files and does include enwiki.
  The index page states the situation plainly: *"The partial mirrors of Wikimedia
  Enterprise HTML dumps that were later hosted here were an experimental service
  that, as of 24 March 2025, are no longer replicated on this site."*
- **Current source of rendered HTML:** the Wikimedia Enterprise **Snapshot API**
  (regularly updated dumps) and **On-demand API** (single articles), both needing
  a free account or a Cloud Services developer account. These serve *current*
  revisions at request time — no history.
- **The one genuinely dated official set — legacy static HTML dumps:**
  <https://dumps.wikimedia.org/other/static_html_dumps/> holds
  `November_2006/`, `December_2006/`, `April_2007/`, `August_2007/`,
  `September_2007/`, `2008-03/`, `2008-06/` and `current/`. Layout is by language
  code (`aa/`, `ab/`, `af/`, …) with per-wiki directories such as `en.wikipedia`.
- **Why no per-revision pipeline:** this is how
  <https://phabricator.wikimedia.org/T182351> ("Make HTML dumps available", opened
  2017-12-07) was **closed as resolved** — via a WMF pipeline for *current*
  revisions only. The thread is worth reading: a single template edit can require
  re-rendering hundreds of thousands of pages, which is why per-revision HTML
  dumps were judged impractical and the gap persists.

**Official rendered-HTML timeline:**

| Period | What exists |
|---|---|
| 2006–2008 | Legacy dated static HTML dumps (Nov/Dec 2006, Apr/Aug/Sep 2007, 2008-03, 2008-06) |
| 2008–2025 | **Nothing official** — use web archives, or reconstruct (WikiHist.html covers enwiki to 2019-03) |
| Feb–Mar 2025 | Four experimental Enterprise mirror runs |
| 24 Mar 2025 → | API-only (Enterprise Snapshot/On-demand), current revisions |


## Option 3 — Web archives: what was actually served (best fidelity)

- **Wayback Machine.** Replay: `https://web.archive.org/web/<YYYYMMDDhhmmss>/<url>`.
  Coverage for `en.wikipedia.org/wiki/Main_Page` is dense — **61 captures for
  May–June 2016 alone** (~1–2/day). Earliest HomePage capture is March 2001;
  the current URL has been archived since December 2003.
- **Images are preserved.** A 2016 snapshot rewrites `<img>` to
  `web.archive.org/web/<ts>im_/<original>` and the image *bytes* are in the
  archive — the CDX index for one 2016 Main Page thumbnail returns
  `mimetype: image/jpeg`, HTTP 200, at 2016-01-21, 2016-07-25, 2016-12-17, plus
  `warc/revisit` records.
- **archive.today** (`archive.ph` / `archive.today`) also holds full-page
  snapshots; `/newest/<url>` redirects to its most recent capture.
- **Why this beats any reconstruction:** time-dependent magic words
  (`{{CURRENTDAY}}`, `{{CURRENTYEAR}}`, `#time` comparisons) were evaluated *at
  request time*. Only the served HTML records what they actually produced. No
  later reconstruction can recover them.
- **Caveat:** only where a capture exists. No capture, no answer.

## Option 4 — DIY reconstruction (arbitrary wiki, arbitrary date)

Substrate: the `pages-meta-history` XML dumps (full wikitext history, monthly).

1. Get the old revision: exact `oldid`, or
   `prop=revisions&rvstart=<ts>&rvdir=older&rvlimit=1&rvprop=ids|timestamp|content`.
2. Resolve **every** transcluded template/module as of that same date — same call,
   per title, recursively. This is the step MediaWiki will not do for you.
3. Expand offline against those frozen revisions — a local MediaWiki whose macro
   fetches are intercepted, exactly as WikiHist.html does it.
4. **Images:** `prop=imageinfo&iistart=<ts>&iilimit=1&iiprop=timestamp|url|size|archivename`
   returns the version current at that date *with a working archived URL* — e.g.
   `.../commons/archive/a/a9/20060307155131%21Example.jpg` (verified HTTP 200).
   **Take `url` from the API**; the hash directories are md5-derived (`a/a9`), not
   name-derived, so hand-built paths 404.
5. Adjacent tooling: the Wikipedia Revision Toolkit / JWPL reconstructs past
   *states* of Wikipedia from dumps (data, not rendering); HT '24
   (`10.1145/3648188.3675150`) covers compressing revision history (~94%).

**Unavoidably lost in any reconstruction:** deleted templates/modules,
time-dependent magic words, parser/extension behaviour differences across
MediaWiki versions, and current Wikidata interwiki links.

## Unresolved — verify from a normal host

- **Common Crawl** is a plausible source of served HTML (multiple crawls per year
  since ~2013) and its service is alive — 127 collections, newest
  `CC-MAIN-2026-34`. But the URL-index endpoint **504'd from this host on every
  query, including a control**, so its Wikipedia coverage is **unverified**.
  Query to run elsewhere:
  `https://index.commoncrawl.org/CC-MAIN-<id>-index?url=en.wikipedia.org%2Fwiki%2FMain_Page&output=json`
- **Kiwix / ZIM** mirrors reachable from here serve *current* snapshots; no dated
  archive was found (`download.kiwix.org/archive/` merely lists the host root).
- Whether WMF retains Enterprise runs older than the four currently listed.

## Decision guide

| Need | Use |
|---|---|
| What readers actually saw on a date, images included | Wayback / archive.today |
| enwiki article HTML for any revision up to 2019-03 | WikiHist.html |
| Today's rendered HTML in bulk | Enterprise HTML dumps |
| Arbitrary wiki or date | DIY with frozen templates (accept the losses above) |
| Just the wikitext of an old revision | `action=parse&oldid=` / `rvprop=content` — but note the templates will be today's |
