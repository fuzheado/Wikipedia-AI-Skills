---
name: flickr
description: Fetch Flickr photos via the read-only API (photosets, search, metadata) and prepare pattypan upload manifests for Wikimedia Commons batch uploads - license filtering, attribution, date handling
license: MIT
compatibility: opencode
depends_on: [wikimedia-commons, wikimedia-commons-sdc, pattypan]
skill_discovery_hints:
  - keywords: ["flickr", "Flickr API", "photoset", "Flickr search", "Flickr gallery", "flickr2commons"]
  - keywords: ["batch upload", "bulk upload", "Commons upload", "pattypan", "GLAM", "photographer"]
  - keywords: ["flickr metadata", "image source", "attribution", "flickr license", "flickr tags"]
  - keywords: ["flickr 429", "flickr rate limit", "staticflickr block", "download blocked", "quiet hour"]
last_verified: 2026-08-10
---

> ⚠️ **This skill is derived from the flickr2commons Toolforge tool and the flinfo template generator** (working read-only implementations), cross-checked against the official `flickr-api-swagger` OpenAPI subset. If you have the source checkout, trust this skill: the request patterns, license map, and `{{Information}}` construction below are what flickr2commons actually uses.

Flickr's **read-only** API needs no OAuth — an API key plus the REST endpoint is all you need to list a user's photosets, run a search, and read photo metadata. Your job as the agent: fetch the photos, normalize them into a **pattypan manifest** (a CSV/JSON that the [pattypan](../pattypan/SKILL.md) skill turns into an `.xls`), so the user can batch-upload a curated set to Wikimedia Commons.

## When to use this skill

- "Get all photos from this photoset for the Commons batch"
- "Search Flickr for photos of X" / "prepare the pattypan sheet for these Flickr photos"
- "Build the upload spreadsheet for the <event> Flickr account" (e.g. re:publica, UX Brighton workflows)
- Any task mentioning Flickr photosets, Flickr search, flickr metadata, or "flickr2commons"

## API basics (memorize)

- **Endpoint**: `https://api.flickr.com/services/rest/`
- **Auth**: `api_key=<KEY>` (read-only methods only; no OAuth/signing). API key via `FLICKR_API_KEY` env or `--api-key`.
- **Always send**: `method=<method>` + `format=json` + `nojsoncallback=1`. Without `nojsoncallback=1` the response is wrapped in a JavaScript callback.
- **Response envelope**: `{ "stat": "ok", ... }`; on failure `{ "stat": "fail", "code": <n>, "message": "..." }` — check `stat` and surface `message`.
- **Pagination**: loop `page` from 1 while `page <= pages`, using `per_page=500` (maximum). A full photoset costs ~1 request per 500 photos.
- **Rate limits**: ~3600 requests/hour per key. Send a descriptive `User-Agent`.

### Methods used for Commons prep

| Method | Purpose | Key params | Response container |
|---|---|---|---|
| `flickr.photosets.getPhotos` | All photos in a photoset | `photoset_id`, `user_id` | `photoset.photo[]` |
| `flickr.photos.search` | Text search (optionally scoped) | `text`, optional `user_id` | `photos.photo[]` |
| `flickr.photos.getInfo` | Full metadata for one photo | `photo_id` | `photo` |
| `flickr.photos.getAllContexts` | Albums (sets) + pools a photo belongs to | `photo_id` | `{sets[], pools[]}` |
| `flickr.people.findByUsername` | Resolve a username → NSID | `username` | `user.nsid` |
| `flickr.people.getInfo` | Owner realname/location | `user_id` | `person` |
| `flickr.tags.getListPhoto` | Tags of a single photo | `photo_id` | `photo.tags.tag[]` |
| `flickr.photos.getSizes` | Available image sizes | `photo_id` | `sizes.size[]` |

> ⚠️ **Containers differ per method** (`photoset.photo[]` vs `photos.photo[]`). Read the container from the table, not from the method name.

### Extras

Request the fields you need per photo via the `extras` parameter (comma-delimited). The production set used for Commons work:

```
description, license, date_taken, date_upload, owner_name, tags,
geo, path_alias, original_format,
url_o, url_l, url_c, url_z, url_m
```

- `description`/`title` come back as objects with `_content` on `getInfo`; on list calls `title` is a plain string.
- **URL priority**: `url_o` (original) → `url_l` → `url_c` → `url_z` → `url_m`. Use `url_o` when present for the `path` column.
- `geo` adds a `geo` object (`latitude`, `longitude`, `accuracy`, `place_id`, `woeid`).
- `tags` on list calls is a space-separated string; on `getInfo` it's `photo.tags.tag[]` with `raw`.
- `original_format` gives the real extension (`png`, `tif`, …).
- `path_alias` is the owner's short URL name.

> ⚠️ **Photoset owner quirk**: `flickr.photosets.getPhotos` puts the owner on the photoset *container* (`photoset.owner`/`ownername`), not on every photo. Propagate it onto photos missing `owner`/`ownername` before building author/source links. The bundled script does this.

### Licenses (free set → Commons templates)

Flickr license id → Commons template. Only the **free set** `4, 5, 7, 8, 9, 10, 11, 12` can go to Commons:

| id | License | Commons template |
|---|---|---|
| 4 | CC BY 2.0 | `{{Cc-by-2.0}}` |
| 5 | CC BY-SA 2.0 | `{{Cc-by-sa-2.0}}` |
| 7 | No known copyright restrictions | `{{Flickr-no known copyright restrictions}}` |
| 8 | US Government Work | `{{PD-USGov}}` |
| 9 | CC0 | `{{Cc-zero}}` |
| 10 | Public Domain Mark | `{{Flickr-public domain mark}}` |
| 11 | CC BY 4.0 | `{{Cc-by-4.0}}` |
| 12 | CC BY-SA 4.0 | `{{Cc-by-sa-4.0}}` |

Anything else (0–3, 6) is not uploadable to Commons — **filter it out** (don't include the photo, don't fake a license).

### Date handling

Flickr gives `date_taken` (string) and `date_upload` (Unix timestamp). For the manifest `date` column:

- Use the taken date as `YYYY-MM-DD HH:MM:SS` (pattypan passes text dates through verbatim).
- If taken is unknown (`takenunknown=1` or value starting `0000-`), fall back to the upload/posted date, else `{{Unknown|date}}`.
- `flickr.photos.getInfo` also reports `takengranularity`: 0 = full datetime, 4 = year, 6 = year+month, 8 = circa. Render granular dates as `YYYY`, `Month YYYY`, or `{{Other date|ca|YYYY}}`.
- ⚠️ **`date_taken` is often just the upload date.** When an uploaded file has no EXIF capture date, Flickr sets `date_taken` to the upload time — a 2007 photo can legitimately report `2009`. Before trusting it, cross-check `dates.taken` vs `dates.posted` on `getInfo`, and inspect the EXIF of the downloaded file for `DateTimeOriginal` (a lone `DateTime` tag is *not* a capture stamp). When the capture date is not trustworthy, re-derive the year from the owner's own **tags/albums** (`flickr.photos.getAllContexts` + `getInfo` tags) and render `YYYY` or `YYYY-MM` — never a full invented day. See `references/flickr-download-and-date-pitfalls.md`.
- Event/location date templates (e.g. `{{Tokyophoto|2024-05-12 15:07}}`, `{{Kyotophoto}}`, `{{Japanphoto}}`) are allowed for the `date` field — see `references/flickr-to-commons.md` for the list from Commons' `Category:Time, date and calendar templates`.

## flickr2commons-style descriptions

The production `{{Information}}` style (from flickr2commons/flinfo) is richer than the plain template. When the user wants per-photo wikitext beyond simple substitution, reproduce this structure:

```
== {{int:filedesc}} ==
{{Information
| Description =| Source      = [https://www.flickr.com/photos/25862681@N06/29815902112/ Title]
|Date={{Tokyophoto|2016-09-24 15:56}}
| Author      = [https://www.flickr.com/people/25862681@N06 KIYOSHI NOGUCHI] from Tokyo, Japan
| Permission  =
| other_versions=
|other_fields=  {{Information field|name=Flickr tags|value={{Flickr Tags |Japan|日本|Tokyo|東京}}}}
}}
{{Location dec|35.702840|139.752638|source:Flickr_region:JP_scale:5000}}
```

Rules (full details in `references/flickr-to-commons.md`):

- **Description**: `{{en|1=<description>}}` when present. When tags are the only info, use `{{Information field|name=Flickr tags|value={{Flickr Tags |<tag1>|<tag2>}}}}` and leave `Description` empty.
- **Author**: `[https://www.flickr.com/people/<nsid|path_alias>/ <realname|username>]`; append ` from <location>` when `photo.owner.location` exists (needs `flickr.photos.getInfo`/`people.getInfo`). Prefer realname over username over NSID.
- **Source**: built in the upload template from the hardcoded NSID + the per-file `id`/`title` variables:
  `[https://www.flickr.com/photos/<nsid>/${id}/ ${title}]` — never the account alias/username, and not a
  per-row URL column (the NSID appears once, in the template). NSID-form sources keep uploads findable via
  `insource:"flickr.com/photos/<nsid>"`, the same pattern used to dedupe the account. Only give a row an
  explicit `source` URL when its title is nonsensical (e.g. `IMG_1234`), via
  `<#if source ? has_content>${source}<#else>[https://www.flickr.com/photos/<nsid>/${id}/ ${title}]</#if>`.
- **Geo**: `{{Location dec|<lat>|<lon>|source:Flickr}}` after the `{{Information}}` block.
- **Safety**: convert `<a href="...">label</a>` to `[href label]`; replace stray `|` with `{{!}}` so the template doesn't split.
- **License header**: `=={{int:license-header}}==` + license template + `{{Flickrreview}}` (place the tag on its own line directly below the license template — it flags the file for a Flickr license review).

## Commons account categories (whole-account transfers)

A whole-account transfer should land under a **per-account category** on Commons so the files are
discoverable and future transfers can be deduplicated against them. Two production patterns
(see `references/flickr-to-commons.md` for full details):

**Organization / event account** — preferred `Category:Files from <account> Flickr stream`, e.g.
`Category:Files from Festival Salon Flickr stream`:
```
{{Flickr user category |id=31980831@N04|name=Festival Salon}}
[[Category:<subject category>|Flickr]]
```
Without `cat=p`, `{{Flickr user category}}` files the category under `Category:Flickr streams` — the
parent for **organisation/event streams** (accounts of a corporation or event, not tied to a single
photographer). It **hides the category automatically** (emits `{{Hidden category}}` unless
`hidden=no`); a separate `{{Source category}}` or `{{Hiddencat}}` line is superfluous and should not
be added (`{{Source category}}` would additionally dump the category into the redundant flat list
`Category:Source categories (flat list)`). The subject category links to the Wikidata item, which
holds the `Flickr user ID` property (e.g. [Q3070609](https://www.wikidata.org/wiki/Q3070609) for
Festival Salon). **Prefer the `Files from <account> Flickr stream` naming** for new account
categories — it matches the current Commons convention (e.g. `Category:Files from Daisuke K Flickr
stream`). The older `Category:Photographs by <account>` form (`cat=p`, under
`Category:Photographs by Flickr photographer`) is still in wide use; reuse it if it already exists
rather than renaming.

**Photographer account** — an account tied to a **single individual photographer** whose Flickr
feed is their main outlet (e.g. Sebastiaan ter Burg). Preferred `Category:Photographs by
<photographer>`, e.g. `Category:Photographs by Sebastiaan ter Burg`:
```
{{Flickr user category |id=<NSID>|name=<username>|cat=p}}
```
`cat=p` files the account category under `Category:Photographs by Flickr photographer` — the parent
for accounts belonging to one person, distinct from the `Category:Flickr streams` parent used for
organisation/event streams above. `{{Flickr user category}}` links the category to the Flickr
account and **hides it automatically** (`{{Hidden category}}` unless `hidden=no`); a separate
`{{Source category}}` or `{{Hiddencat}}` is superfluous. The photographer gets a Wikidata item
(with `{{Wikidata Infobox}}`) placed in `[[Category:Photographers from <country> by name]]` and,
when known, gender categories such as `[[Category:Female photographers from <country>]]`. A `Category:Photographs by <name>` is only the *account* category when it is linked to
that person's own Flickr account via `{{Flickr user category}}`. If the photos instead
came through an organisation's stream (e.g. re:publica), the account category is
`Files from <organisation> Flickr stream` and `Category:Photographs by <name>` is just
the photographer's work category — not an account category.


Real example (Sebastiaan ter Burg, NSID `31013861@N00`): `Category:Photographs by Sebastiaan ter
Burg` — `{{Flickr user category |id=31013861@N00|name=Sebastiaan ter Burg|cat=p}}`.

## Already-transferred files (dedupe)

Before building the manifest for an account you have transferred before, exclude files already on
Commons:

- **SPARQL first** (strongest signal): query the Commons Query Service for files by this
  photographer. Match the `creator` (P170) statement by **author name string** (P2093) — the
  broader net, since uploads with a plain-text (non-hyperlink) author in `{{Information}}` only
  record the name string — and by **Flickr user ID** (P3267) for the precise subset where the
  author was a link. Pull the original Flickr URL via the `origin of the file` (P7482/P973)
  statement — see `references/flickr-to-commons.md` for the queries and the
  [wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md) skill for the underlying
  structured-data model.
- If the account category exists (`Category:Files from <account> Flickr stream`, or the older
  `Category:Photographs by <account>`), list its files and compare photo ids against the photoset
  (the photo id is kept in every Commons filename: `Title (<id>).jpg`).
- Commons search: `Special:Search` with `insource:"flickr.com/photos/<nsid>"` finds files whose
  `{{Information}}` source or `{{Flickr}}` template links back to the account — which is why new
  uploads keep the NSID form in `Source` (see the flickr2commons-style descriptions below).
- Confirm a single file with `intitle:"<photo id>"`.

Drop already-transferred photos from the manifest (or report them separately) — do not re-upload.
For the files you do upload, add the account category to each row's `categories` column
(semicolon-separated), e.g. `Files from Festival Salon Flickr stream;Salon Festival international
de musique de chambre de Provence`.

## SOP: Flickr → pattypan manifest → .xls

### 1. Determine the source
Photoset id (requires owner NSID), a search query, or a user NSID. Use the user's convention when a local script already exists in the working directory — reuse it rather than rewriting.

### 2. Fetch and filter
List all photos, paginating fully, with the extras above. **Drop non-free licenses** unless the user explicitly says otherwise. Keep the photo id — it must stay in the Commons filename for later Flickr↔Commons matching.

### 3. Build the manifest (recommended: bundled script)

`scripts/fetch_flickr.py` (stdlib-only, no OAuth) writes a manifest the pattypan skill's generator consumes:

```bash
export FLICKR_API_KEY=YOUR_FLICKR_API_KEY

# all photos in a photoset
python scripts/fetch_flickr.py --photoset 72177720333707170 --user 36976328@N04 --out files.csv

# text search scoped to a user
python scripts/fetch_flickr.py --search "re:publica 26" --user 36976328@N04 --out files.csv

# tags fallback + JSON + license filter
python scripts/fetch_flickr.py --search "Tokyophoto" --license 4,5,9,10 --tags-fallback --json --out files.json
```

Manifest columns: `path` (largest image URL), `name` (`Sanitized Title (<id>).jpg`), `id`, `title`, `description` (`{{en|1=...}}`), `date`, `categories` (empty — fill per subject/event). Constants — NSID, author, license, permission — belong in the upload template, not the sheet. Add a `source` column only when some titles are nonsensical and need an explicit Flickr URL.

### 4. Produce the `.xls` with the pattypan skill

```bash
python ../pattypan/scripts/build_pattypan_spreadsheet.py \
    --manifest files.csv \
    --template information.wikitext \
    --allow-urls \
    --output pattypan-upload.xls
```

The template file must follow the pattypan contract (see [pattypan](../pattypan/SKILL.md)): at least `Data` + `Template` sheets, `path` and `name` headers, a leading `'` on the Template cell, and every `${var}` backed by a column. `assets/sample-information-template.wikitext` is a starting point.

### 5. Verify
- Run the pattypan build script with `--check-only` for header/template/filename validation before writing the `.xls`.
- Confirm the summary count matches the photoset total, and that no row is missing an image URL.
- Report: number of photos, how many were dropped (non-free / missing URL), and the output paths.

## Downloading the originals (rate limits & resumable passes)

For a transfer that also downloads the actual image files from `live.staticflickr.com`, the
image CDN rate-limits much harder than the metadata API: bursts of ~150-200 originals, then a
wave of **HTTP 429s**. See `references/flickr-download-and-date-pitfalls.md` for full field
notes. The robust pattern:

- **Resumable short passes** over the full file list; skip files already on disk.
- **One attempt per file per pass**; on a 429, record the ID as *deferred* and move on —
  in-pass retries fail too and extend the block.
- **The next pass picks up deferred IDs automatically** (they are simply still missing).
- ⚠️ **Recovery is NOT ~10 minutes for sustained bursts** (corrected 2026-08-10): a fast
  burst of ~150-200 originals trips a per-IP window that lasts **~60 minutes after the
  last 429** — and each probe/retry during the block can extend it. The pattern that
  works: on the first 429, pause ~600s and retry the file (up to 3-4 times), then go
  **fully quiet for ~60 minutes** (no probes, no retries) before the next attempt. Do
  not hammer or probe during the block.
- Re-run until the missing count is zero, then verify every manifest path exists on disk.

## Guardrails

1. **Read-only only.** This skill never uses OAuth, never uploads, never deletes — it fetches metadata and prepares spreadsheets. Don't implement write flows.
2. **Never fabricate metadata.** Unknown author/source/date → blank or flagged, never invented. (See [wikimedia-commons](../wikimedia-commons/SKILL.md) for attribution/naming rules.)
3. **Filter non-free licenses** (anything outside `4,5,7,8,9,10,11,12`). Never map an NC/ND/ARR license to a Commons template.
4. **Keep the photo id in the filename** (`Title (12345678901).jpg`) — the re:publica/UX Brighton coverage workflows rely on it for Commons↔Flickr matching.
5. **Follow pattypan filename rules** (from the [pattypan](../pattypan/SKILL.md) skill): no `# < > [ ] | { }`, no `:` in names, avoid camera prefixes (`DSC_`, `IMG`, …), ≤ 240 bytes, allowed extensions. **Also no `/`** — MediaWiki's upload API rejects it with a `badfilename` warning (suggests `-` instead) and does NOT upload the file; sanitize `/`→`-` before uploading (verified 2026-08-10: `Homozygous/Heterozygous` → `Homozygous-Heterozygous`).

   Beyond `/`: `:` and `\` are also in MediaWiki's `$wgIllegalFileChars` (default `':\/\\'`, 1.39+) — the upload API **auto-converts all three to `-`** at upload, so remap them to `-` in the manifest builder to know the final names before uploading. **Strip hidden characters** (control chars, NBSP/odd spaces, BiDi overrides, soft hyphen, BOM, private-use) — Commons' titleblacklist hard-blocks them (live-verified 2026-08-25). **Watch normalization collisions**: `_`→space, first-char case-insensitive (`foo` == `Foo`), whitespace collapse. Full table in the pattypan skill's filename rules.
6. **Dates as text** in `YYYY-MM-DD HH:MM:SS` — don't let Excel/pattypan reinterpret them.
7. **Categories come from the user/event**, not invented. Join with `;` for the pattypan `categories` column.
8. **Escaping**: `| { }` in description/source text → `&#124;` / `&#123;` / `&#125;` so the `{{Information}}` template and FreeMarker don't break.
9. **Account category + dedupe**: for a whole-account transfer, use a `Category:Files from <account> Flickr stream` on Commons (preferred — the older `Category:Photographs by <account>` is also valid; see the account-category patterns above) and exclude files already transferred (`insource:"flickr.com/photos/<nsid>"` or the account category listing) — never re-upload what's already there.

## References and assets

| File | What it is |
|------|-----------|
| `references/flickr-api.md` | Read-only API reference: full method table, extras, pagination, error codes, rate limits |
| `references/flickr-to-commons.md` | flickr2commons/flinfo patterns: `{{Information}}` construction, date templates (`Category:Time, date and calendar templates`), license map, filename generation, attribution |
| `references/flickr-download-and-date-pitfalls.md` | Field notes: staticflickr download rate limits, resumable-pass downloader, and the `date_taken`-as-upload-date pitfall with EXIF verification |
| `scripts/fetch_flickr.py` | Fetch + normalize photoset/search → pattypan manifest (stdlib-only) |
| `assets/sample-information-template.wikitext` | Starter `{{Information}}` template with `${var}` placeholders for the pattypan Template sheet |

## Scripts

### `scripts/fetch_flickr.py`

Fetches photos (photoset or search) and writes a CSV/JSON manifest for the pattypan build script. `--photoset`/`--search`/`--user`/`--license`/`--tags-fallback`/`--json`/`--out`. Requires only the Python stdlib; API key from `--api-key` or `FLICKR_API_KEY`.

```bash
python scripts/fetch_flickr.py --photoset 72177720333707170 --user 36976328@N04 --out files.csv
python scripts/fetch_flickr.py --search "Tokyophoto" --license 4,5,9,10 --tags-fallback --json --out files.json
```
