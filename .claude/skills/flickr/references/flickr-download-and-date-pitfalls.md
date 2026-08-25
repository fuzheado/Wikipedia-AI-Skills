# Downloading originals, rate limits & date pitfalls — field notes

Hard-won lessons from a real whole-account transfer (**FESTIVAL-SALON**,
`31980831@N04`, alias `emperi`, 1817 photos → Commons). The two places this
workflow breaks are **downloading the image files** and **trusting the
`date_taken` metadata**. Both have cheap, reliable fixes.

## 1. Downloading originals: the staticflickr rate limiter

The API (api.flickr.com) is generously rate-limited (~3600 req/h), but the
**image CDN (`live.staticflickr.com`) throttles far more aggressively** — the
bottleneck of any full-account transfer is the file download, not the metadata.

Observed behaviour:

- The limiter is **wave-like**. You can fetch ~150–200 originals in a fast
  burst, then every request returns **HTTP 429** for a while, then it recovers
  for another burst.
- Once the 429s start, in-burst retries do **not** help — each retry inside the
  same wave also 429s and can extend the block. Retrying an ID that 429'd in
  the same pass wastes time.
- ⚠️ **Recovery is NOT a fixed ~10 minutes** (corrected 2026-08-10, 518-file
  transfer; earlier notes claimed ~10 min): the block is per-IP/global, not
  per-URL, and for sustained bursts the window lasts **~60 minutes after the
  last 429 in the burst** — each probe or retry during the block can extend
  it. Observed cycles: ~85-160 downloads per ~60-min window, then hard 429s
  until the window slides. A lone 429 after a short burst can clear in ~10
  min; a sustained burst does not.
- **The working pattern for batch downloads:** on the first 429, pause ~600s and
  retry the same file (up to 3-4 attempts); if the block persists, go **fully quiet
  for 3600s** (no probes — a single probe during the block can reset the window),
  then resume. The batch then self-heals through any number of block cycles.
- Escalating per-request backoff (120s → 240s → 360s …) inside one pass works for
  short blocks, but it is wasteful for window-based blocks: prefer the quiet-hour
  pattern above.

### The resumable, self-pacing pass pattern that works

Run the download as **repeated short passes** over the full file list instead
of one long loop:

1. Read the full URL list (or manifest) once.
2. For each file **not already present on disk**: try once.
3. If it succeeds → save (skip tiny/zero-byte files, e.g. `< 1000 bytes`).
4. If it returns 429 → **record the ID as "deferred"** and move on immediately
   (do not retry it this pass).
5. If it fails otherwise → record as failed for manual review.
6. At the end, stop. The next pass retries only what's still missing (deferred
   IDs are picked up automatically because they're simply still missing).

```bash
python download_all.py --max 250   # pass 1
python download_all.py --max 250   # pass 2 (resumes: skips existing)
python count_jpg.py                # how many are left
```

Properties:

- **Resumable**: existing files are skipped, so an interrupted pass loses
  nothing. Ctrl-C at any point is safe.
- **Self-pacing**: the pass itself naturally slows down under 429s; with the
  *defer-429* rule it never burns time on futile in-pass retries.
- **Deterministic**: running N passes is idempotent; the working set shrinks
  monotonically.
- Typical yield: 100–200 files per pass, rate-limited. A 1800-file account
  takes several passes — start each from a fresh shell (or your own terminal)
  rather than letting an agent hold one process open.

## 2. `date_taken` is often just the upload date — verify, don't trust

**Pitfall**: when an uploaded file has **no EXIF capture date**, Flickr sets
`date_taken` to the upload/processing time. An account holder uploading their
2007 festival photos in 2009 therefore produces photos with `date_taken=2009`
and a perfectly good `2007` tag. If you take `date_taken` at face value, every
one of those photos gets a wrong date in the manifest.

Real numbers (Festival Salon): **289 of 1817** photos were affected — the
`datetaken` said `2009`/`2010` while the tags said `emperi2006`/`emperi2007`/
`emperi2008`/`emperi 2011`. The year mismatch broke down as
`2006: 41, 2007: 105, 2008: 44, 2011: 99`.

### How to detect it (cheap, per-photo)

`flickr.photos.getInfo` returns a `dates` object with `taken`, `posted` and
`takengranularity`. Two cheap checks, then EXIF on the downloaded file:

1. **`taken` vs `posted`** — if they differ, `taken` came from somewhere
   (EXIF or manual). If they are equal, `taken` is an upload-time artifact.
2. **EXIF on the downloaded original** — open the file and look for
   `DateTimeOriginal` / `DateTimeDigitized` (the capture tags):
   - **Present** → that is the real capture date; compare it to `taken`.
   - **Absent** → the file has no trustworthy capture date at all. A generic
     `DateTime` tag alone (no `DateTimeOriginal`) is *not* a reliable capture
     stamp — it tracks file-modification time and often matches the (wrong)
     `taken` value.

Festival Salon's 289 resolved exactly this way: the 2006/2007/2008 files had
**no EXIF date at all** (14/48/1 sampled — 0 with any EXIF date), while the
2011 files carried only a generic `DateTime = 2010-08-xx` (no
`DateTimeOriginal`) that matched `taken`. Either way: no trustworthy capture
date existed.

### The fix: tags/albums are the source of truth for the year

- Check the **tags** (`flickr.photos.getInfo` → `photo.tags.tag[]`) and the
  **albums** (`flickr.photos.getAllContexts` → `sets[]` — 1 cheap request per
  photo, no need to enumerate whole photosets). The account owner's own
  `emperi2007` tag or an album title is the authoritative classification.
- Re-derive the date from the **edition/event year** in the tag/album, at the
  precision you actually know. For a yearly festival held every August, the
  project convention was `YYYY-08` (year + month, text) — never invent a day.
- Cross-check afterwards: confirm every corrected photo has a tag/album naming
  the year you used, and no photo carries **conflicting year tags**
  (e.g. both `emperi2006` and `emperi2009`). 289/289 checked out clean.
- Prefer a conservative render when the month is also uncertain:
  `{{Information|date=YYYY}}` (year only) is always defensible; full blanking
  throws away the one fact you do know (the year), so it's the last resort.

## 3. Categories and dedupe reminders (from the same transfer)

- Keep the **photo id in the Commons filename** — `Title (12345678901).jpg` —
  it is the only stable Flickr↔Commons key.
- Base account category: `Photographs by Festival Salon` (via
  `{{Flickr user category |id=31980831@N04|cat=p}}`).
- **Per-person tag → per-person category**: photos tagged `tavernier` got
  `Photographs by Nicolas Tavernier` added alongside the account category.
  A person-name tag is a legitimate trigger for a person category.
- Dedupe against files already on Commons: SPARQL by author-name-string
  (P2093) ∪ Flickr-user-id (P3267), plus the account category listing. The
  Wikidata item for the account (e.g. Q3070609) carries the `Flickr user ID`
  property — that's what ties the category → Wikidata → SPARQL chain together.

## 4. Uploading to Commons: the server-side URL-fetch 429 trap (2026-08-10 field notes)

**Symptom.** Bulk-uploading Flickr originals to Commons via the MediaWiki API
with `action=upload&url=<live.staticflickr.com URL>` (pywikibot
`Site.upload(..., source_url=...)`, or any upload-by-URL client) fails
persistently with:

```
API error http-bad-status: There was a problem during the HTTP request: 429 Too Many Requests
[servedby: mw-api-ext.eqiad.main-...; help: See https://commons.wikimedia.org/w/api.php ...]
```

after the first ~100 uploads. Local-file uploads, queries, logins, and the
account's own rate-limit state all stay healthy.

**Root cause — the fetch happens server-side, on Wikimedia's shared outbound IPs.**
`action=upload&url=` does *not* record the URL: MediaWiki's `UploadFromUrl`
fetches the image itself, from Wikimedia's shared outbound fetcher IPs. Those
IPs hit Flickr's CDN rate limiter after ~100 originals in a burst — the exact
same "~150–200 originals, then a wave of HTTP 429s" behavior this document
describes for direct downloads (section 1), except the victims are shared by
everyone (UploadWizard's Flickr importer, flickr2commons, all URL-upload
clients), so the block can persist for hours and is not under your control.

> **Scale nuance (2026-08-25):** even Flickypedia — the Flickr Foundation's
own uploader — uses `action=upload&url=` (60 s timeout, no retry logic beyond
a raised timeout). It survives only because its volume is interactive (a user
picks a handful of photos per session, far below the ~100-fetch window).
Batch tools (100s–1000s of files) must not copy that pattern: download
client-side, upload bytes (see section 1's download strategy).

**How to confirm it's this and not your account being rate-limited:**

1. The error envelope arrives inside an **HTTP 200** response — the API
   request itself succeeded; the failure happened inside MediaWiki. (A
   requests-layer spy sees `200` + `{"error":{"code":"http-bad-status",...}}`.)
2. `apierror-http-bad-status` is MediaWiki's message for "an **internal
   outbound** HTTP request failed" (same code appears for Parsoid/VisualEditor
   backend failures) — not a per-account API rate limit.
3. `meta=userinfo&uiprop=ratelimits` shows `hits=None/max=None` for `upload`
   (no classic MediaWiki limit applies), and the 2026 API-gateway limits give
   authenticated sessions 2000 req/min — yet URL uploads still 429.
4. The same file uploads instantly when posted as bytes (`source_filename`).

**Fix — download locally, then upload the file.** Client-side downloads are
resumable, cacheable, and rate-limit-manageable with the section-1 pass
pattern; the upload then goes out as a multipart file POST that touches no
outbound fetcher. Proven in production: 97/458 files via URL upload then a
hard block; switched to local-file uploads and the remaining 361 completed
cleanly at ~6s/file.

**Keep the 429 retry anyway.** `Retry-After` (fallback ≥60s) + retry the file
up to 4 times: local uploads can still hit transient gateway 429s, and the
backoff makes the batch self-healing.

## 5. The client-side download block is also a thing — and a filename gotcha

**Download-side 429 waves (verified 2026-08-10).** The same staticflickr
per-IP limiter that blocks Wikimedia's server-side fetchers (section 4) also
blocks *your* client downloads: ~150-200 originals at ~10/min sustained
tripped it, then every download returned plain `HTTP Error 429: Too Many
Requests` (from `urllib`/`requests` — no MediaWiki envelope involved, no
Retry-After header on the body). Recovery follows the same window model as
section 1: the block persists **~60 minutes after the last 429** and probes
or retries during the block can extend it — a sustained burst does **not**
clear in ~10 minutes (a lone 429 after a short burst can).
Fix: retry downloads with backoff (120s minimum, 4 attempts) and let the
batch pause-and-recover instead of failing files; if the block persists,
go fully quiet for 3600s (no probes) before the next pass. Keep the resumable
cache so re-runs skip what's already on disk.

**`/` in Commons filenames (verified 2026-08-10).** MediaWiki's upload API
rejects filenames containing `/` with a `badfilename` warning (it suggests
the hyphenated form, e.g. `Homozygous-Heterozygous`) and does not upload the
file. Sanitize `/`→`-` in the target name while keeping the Flickr title
verbatim in the description/source. Also note: pywikibot 11.6.0 crashes on
ANY upload Warning result with `TypeError: 'bool' object is not callable`
(it calls the bool `ignore_warnings`), so sanitize names *before* uploading
rather than relying on warning handling.
