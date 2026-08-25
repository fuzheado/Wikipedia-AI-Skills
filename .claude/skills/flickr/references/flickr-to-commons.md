# Flickr → Commons patterns (flickr2commons / flinfo)

These are the production conventions from the flickr2commons Toolforge tool and its
flinfo template generator. Use them when building the per-photo wikitext / description
fields for a pattypan upload.

## Information template (reference style)

Historical output from a tags-only Tokyo photowalk upload:

```
== {{int:filedesc}} ==
{{Information
| Description =| Source      = [https://www.flickr.com/photos/25862681@N06/29815902112/ 天空の城]
|Date={{Tokyophoto|2016-09-24 15:56}}
| Author      = [https://www.flickr.com/people/25862681@N06 KIYOSHI NOGUCHI] from Tokyo, Japan
| Permission  =
| other_versions=
|other_fields=  {{Information field|name=Flickr tags|value={{Flickr Tags |Japan|日本|Tokyo|東京}}}}
}}
{{Location dec|35.702840|139.752638|source:Flickr_region:JP_scale:5000}}
```

### Field construction

- **Description**: `{{en|1=<description>}}` when the photo has one. When tags are the only
  info available, put them in an `Information field` instead:
  `{{Information field|name=Flickr tags|value={{Flickr Tags |<tag1>|<tag2>|...}}}}`
  (pipe-separated, no spaces inside the template) and leave `Description` empty.
- **Source**: built entirely in the upload template from the hardcoded NSID + the per-file `id` (and `title`
  when meaningful): `[https://www.flickr.com/photos/<nsid>/${id}/ ${title}]` (the account's NSID, never its
  alias/username), or the `{{Flickr|1=<photo_url>}}` template. The spreadsheet carries `id`/`title` only — the
  NSID appears once, in the template, not in a repeated per-row URL column. Uploads whose source keeps the NSID
  form stay findable with `insource:"flickr.com/photos/<nsid>"`, the same search used to dedupe the account.
  When the title is nonsensical (e.g. `IMG_1234`, `613`), leave the `title` cell empty; the template renders
  the bare URL `https://www.flickr.com/photos/<nsid>/${id}/` instead of a link with a meaningless label.
- **Date**: from `photo.dates.taken` with `takengranularity`:
  - 0 (full datetime): raw `YYYY-MM-DD HH:MM:SS`;
  - 4 (year only): `YYYY`;
  - 6 (year+month): `Month YYYY`;
  - 8 (circa): `{{Other date|ca|YYYY}}`;
  - unknown taken (`takenunknown=1` or value starting `0000-`): fall back to posted date
    `Y-m-d`, else `{{Unknown|date}}`.
  - Event/location date templates are allowed (see below).
- **Author**: `[https://www.flickr.com/people/<nsid|path_alias>/ <realname|username>]`; append
  ` from <location>` when `photo.owner.location` exists. Prefer realname over username over NSID.
- **Geo**: from `flickr.photos.getInfo` → `photo.location.latitude/longitude` (or the `geo` extra
  on list calls). Emit `{{Location dec|<lat>|<lon>|source:Flickr}}` after the `{{Information}}`
  block; historical output used `source:Flickr_region:<CC>_scale:<n>`.
- **License header**: `=={{int:license-header}}==` + one license template per license +
  `{{Flickrreview}}`.
- **Categories**: `[[Category:...]]` lines; skip when none.

### Description safety (sanitizeDescriptionForTemplate)

1. Convert `<a href="...">label</a>` anchors to wiki external links `[href label]`
   (strip nested tags from the label).
2. Replace stray `|` with `{{!}}` so the `{{Information}}` template does not split on it.

## Date templates (Commons Category:Time, date and calendar templates)

The `Date` field may use any template from Commons'
`Category:Time, date and calendar templates`. Relevant ones for photo uploads:

- Generic: `{{Taken on|...}}`, `{{Other date|ca|YYYY}}`, `{{ISOdate|...}}`, `{{Date|...}}`,
  `{{Circa}}`, `{{Wrong date}}`, `{{Expiry}}`, `{{Unknown|date}}`.
- Event/location-specific photo date templates (location + capture date):
  - `{{Tokyophoto|YYYY-MM-DD HH:MM}}`, `{{Kyotophoto}}`, `{{Japanphoto}}`, `{{TKYphoto}}`, `{{KYOphoto}}`
  - `{{Osakaphoto}}`/`{{OSAphoto}}`, `{{Nagoyaphoto}}`/`{{NGYphoto}}`, `{{Yokohamaphoto}}`/`{{YKMphoto}}`
  - `{{Melbournephoto}}`/`{{MELphoto}}`, `{{Sydneyphoto}}`/`{{SYDphoto}}`, `{{Brisbanephoto}}`/`{{BNEphoto}}`
  - `{{Austriaphoto}}`/`{{AUTphoto}}`, `{{Canadaphoto}}`/`{{CANphoto}}`, `{{USphoto}}`/`{{USAphoto}}`,
    `{{UKphoto}}`/`{{UnitedKingdomphoto}}`, `{{Australiaphoto}}`/`{{AUSphoto}}`
  - `{{Japanaviationphoto}}`, `{{Japanrailphoto}}` (+ regional variants like `{{Japanrailphoto/Tokyo}}`)
- Utility templates in the same category: `{{Birth date and age}}`, `{{Gregorian serial date}}`,
  `{{Age}}`, `{{As of}}`, `{{MONTHNUMBER}}`, `{{ISOyear}}`, `{{Ymd}}`, `{{Time}}`, `{{Day}}`,
  `{{Century}}`, `{{Millennium}}`.

Confirm a template exists before emitting it (Commons template namespace) — a wrong name
produces a redlink in the upload.

## Commons filename generation

flickr2commons' `generateFilenameForCommons`:

1. Replace `_` with space and `[:/|]` with space; collapse whitespace; trim.
2. Strip a trailing image extension (`.JPG`, `.JPEG`, `.PNG`, `.TIF`, `.TIFF`).
3. Cap the base at 230 characters; empty title → a default prefix (e.g. `Unnamed Flickr file`).
4. Append ` (<photo id>)` and the real extension from the `original_format` extra (fall back to `jpg`).
5. If the target already exists on Commons, disambiguate with ` (<n>)` before the extension.

The skill's manifest uses `Sanitized Title (<photo id>).jpg` — keep the photo id in the name so
Commons↔Flickr matching stays possible. Follow the pattypan skill's filename rules
(no `:`, no `# < > [ ] | { }`, no camera prefixes, ≤ 240 bytes).

### Filename-sanitization field notes (verified 2026-08-25)

- **flickr2commons' `[:/|]`→space mapping diverges from MediaWiki's own behavior.**
  `: / \` are `$wgIllegalFileChars` (default `':\/\\'`, 1.39+): the upload API
  **auto-converts them to `-`** (`badfilename` warning) rather than to a space. A
  batch manifest builder should remap to `-` itself so the final names are known
  before upload (dedupe/progress); flickr2commons only gets away with its mapping
  because it re-queries Commons per file and reports the effective name.
- **flickr2commons does not remap `# < > [ ] { }`** — those uploads fail with
  `badfilename` and need manual fixes; a manifest builder should remap them.
- **Strip hidden characters**: Commons' titleblacklist hard-blocks control chars,
  NBSP/other unusual spaces, BiDi overrides, soft hyphen, BOM, and private-use
  codepoints — delete them from titles (see pattypan skill's filename rules).
- **Normalization collisions**: `_`→space, first-char case-insensitive, whitespace
  collapse — check composed names for pairs that differ only in these.
- **Flickypedia** (the Flickr Foundation's tool) takes the opposite approach:
  reject titles containing `:/\` client-side, and validate everything else via
  API round-trips rather than a local table: `action=titleblacklist&tbaction=create&
  tbtitle=File:…`, `action=query&titles=`, `action=opensearch`. Good pattern for
  single-file flows; batch tools should aggregate the same checks into a preview
  before uploading.

  **`action=titleblacklist` — what it actually catches (live-verified 2026-08-25):**
  returns `{"result":"ok"}`, `{"result":"blacklisted","reason":…,"line":…}`
  (with the matching blacklist entry, e.g. camera prefixes like `IMG_`), or an
  `invalidtitle` API error. It catches the **per-wiki custom blacklist** (camera
  prefixes, hidden chars — NBSP/BiDi/control, pattern blocks) and structurally
  broken titles (>255 bytes, empty). It does **NOT** catch `# < > [ ] | { }`
  (verified: `File:bad#title.jpg` → `ok`), nor `:` `/` `\` (those are upload-time
  conversions, not legality). One call per title — not batchable.

  **`action=query&titles=File:X` is the better batch check** (50 titles/call): the
  response's `normalized[].to` shows what MediaWiki would *actually* store —
  `under_score.jpg` → `Under score.jpg`, `  spaced  name.jpg` → `Spaced name.jpg`,
  and `bad#title.jpg` → `Bad` (the `#` **truncates the title silently**!).
  Comparing input vs normalized output catches normalization collisions AND
  silent mangling in one batched call — use it as a pre-upload gate; keep a local
  table only to render preview names offline.
- **Dedupe index from SDC dumps**: Flickypedia builds a Commons-wide SQLite index
  from weekly SDC snapshots — `P7482 source of file` = file-available-on-internet +
  qualifier `P123 operator` = Flickr + `P973 described at URL` → parse the Flickr
  URL for the photo id (`duplicates_from_sdc/` in their repo). O(1) lookups across
  all of Commons; overkill for category-scoped transfers but the reference
  implementation for a web tool.

## License map

Flickr id → Commons template for the free set: `4→{{Cc-by-2.0}}`, `5→{{Cc-by-sa-2.0}}`,
`7→{{Flickr-no known copyright restrictions}}`, `8→{{PD-USGov}}`, `9→{{Cc-zero}}`,
`10→{{Flickr-public domain mark}}`, `11→{{Cc-by-4.0}}`, `12→{{Cc-by-sa-4.0}}`.
Fallback for unknown: `{{subst:unc}}`. Never map NC/ND/ARR licenses.

## Account categories on Commons

Whole-account transfers (every photo a Flickr user posted) should be filed under a per-account
category so the collection is discoverable and future transfers can be deduplicated. The photo id
stays in each Commons filename (`Title (<id>).jpg`), so the account category plus the id lets you
check "is this photo already here?" later.

### Organization / event account

Preferred: `Category:Files from <account name> Flickr stream` containing:

```
{{Flickr user category |id=<NSID>|name=<account name>}}
[[Category:<subject category>|Flickr]]
```

- Without `cat=p`, `{{Flickr user category}}` files the category under `Category:Flickr streams` —
  the parent for **organisation/event streams** (corporate and event accounts not tied to a single
  photographer). It **hides the category automatically** (emits `{{Hidden category}}` unless
  `hidden=no`); a separate `{{Source category}}` or `{{Hiddencat}}` line is superfluous
  (`{{Source category}}` would only add the redundant `Category:Source categories (flat list)`).
- The subject category (e.g. `Category:Salon Festival international de musique de chambre de
  Provence`) is the real-world subject and connects to the Wikidata item — the item carries the
  `Flickr user ID` (P3267) property (e.g. [Q3070609](https://www.wikidata.org/wiki/Q3070609) for
  Festival Salon), which is the same NSID the API uses.

Real example (Festival Salon, NSID `31980831@N04`):
`Category:Files from Festival Salon Flickr stream` — `{{Flickr user category |id=31980831@N04|name=Festival Salon}}` +
`[[Category:Salon Festival international de musique de chambre de Provence|Flickr]]`.

The `Files from <account> Flickr stream` naming is the **preferred** convention for organisation
and event account categories (e.g. `Category:Files from Daisuke K Flickr stream`). The older
`Photographs by <account>` form — `{{Flickr user category |id=<NSID>|cat=p}}` +
`[[Category:Photographs by Flickr photographer]]` — is still in wide use (and is the correct form
for an *individual photographer's* account, see below) and lives under
`Category:Photographs by Flickr photographer`; reuse it when the category already exists rather
than renaming.

### Photographer account

An account tied to a **single individual photographer** (their main Flickr outlet, e.g. Sebastiaan
ter Burg). Preferred: `Category:Photographs by <photographer>` containing:

```
{{Flickr user category |id=<NSID>|name=<username>|cat=p}}
```

- `cat=p` files the account category under `Category:Photographs by Flickr photographer`, the
  parent for accounts belonging to one person (distinct from the `Category:Flickr streams` parent
  used for organisation/event streams above). `{{Flickr user category}}` also **adds the
  hidden-category behavior automatically** (emits `{{Hidden category}}` unless `hidden=no`) — a
  separate `{{Source category}}` or `{{Hiddencat}}` line is superfluous and should not be added.
- The photographer gets their own Wikidata item with `{{Wikidata Infobox}}`, categorized via
  `[[Category:Photographers from <country> by name]]` and, when known, gender categories
  (`[[Category:Female photographers from <country>]]`).
- A `Category:Photographs by <name>` is only the *account* category when it is linked to
  that person's own Flickr account via `{{Flickr user category}}`. If the photos instead
  came through an organisation's stream (e.g. re:publica), the account category is
  `Files from <organisation> Flickr stream` and `Category:Photographs by <name>` is just
  the photographer's work category — not an account category.


Real example (Sebastiaan ter Burg, NSID `31013861@N00`): `Category:Photographs by Sebastiaan ter
Burg` — `{{Flickr user category |id=31013861@N00|name=Sebastiaan ter Burg|cat=p}}`. (His existing
Commons category still uses the legacy `{{flickr user|31013861@N00}}` layout with a manual
`[[Category:Photographs by Flickr photographer]]`; the template form above is the current
equivalent.)

### Per-file categories

Put the account category (and subject categories) in each uploaded file's pattypan `categories`
column, semicolon-separated:

```
Files from Festival Salon Flickr stream;Salon Festival international de musique de chambre de Provence
```

### Per-year edition categories

When the account covers a recurring event, add one `Category:<Event> <year>` per year and link each
to its Wikidata **edition item** — not just to the parent event item. The edition item has
`instance of` a festival-edition class (e.g. `Q41582469`), `part of` the parent festival
(`P179 → Q3070609`), `point in time` `P585`, `edition number` `P393`, and `Commons category`
`P373`. Do the linking on the Wikidata side (as `1VeertjeBot`/your bot) *after* the categories exist:

- **Add the Commons sitelink** — each edition item gets `commonswiki` → `Category:<Event> <year>`
  (via `wbsetsitelink`). This is the actual "category ↔ Wikidata item" link.
- **Create missing edition items first** — if a year has no item, create it (labels/descriptions
  in the event's languages, the claims above) before linking.
- **Chain the editions** with `P155` (follows) / `P156` (followed by) so navigation is complete.
- The per-file template's edition category must match the category name exactly
  (`Category:Musique à l'Empéri ${year}` from the pattypan `year` column).

Real example: for Festival Salon the 2002 and 2005 items did not exist; after creating
`Musique à l'Empéri 2002` and `Musique à l'Empéri 2005`, each of the ten editions
(2002–2013) has its `commonswiki` sitelink and the `P155`/`P156` chain is unbroken.

## Finding already-transferred files (dedupe)

Before building a manifest for an account you have transferred before, check what is already on
Commons. Use these methods in this order — SPARQL first (strongest signal), then the category,
then search:

1. **SPARQL (best when creator metadata is set)** — query the Commons Query Service
   (`https://query.wikidata.org`) for already-transferred files by this photographer. Run both
   queries below and merge the results:

   - **Author name string (P2093) — the completeness net.** Some uploads carry the author as
     plain wikitext (no hyperlink) in `{{Information}}`, so it cannot be translated to an SDC
     creator entity — only the name string survives. Match on `pq:P2093` to catch those files.
   - **Flickr user ID (P3267) — the precise subset.** Only files whose author field was a link
     that resolved to the Flickr account carry the user-id qualifier. This query typically
     returns *fewer* rows than the P2093 one.

   Both queries' `OPTIONAL` block returns the original source URL for files whose
   `origin of the file` (P7482) is "file available on the internet" (Q74228490) operated by
   (P137) Flickr (Q103204) — that URL (`described at URL`, P973) is the Flickr photo page,
   directly comparable to the photoset:

   By Flickr user ID (P3267) — precise:

   ```sparql
   SELECT ?file ?url ?image WHERE {
     ?file p:P170 [ pq:P3267 "31980831@N04"];
           schema:url ?image.
     OPTIONAL{ ?file p:P7482 [ps:P7482 wd:Q74228490; pq:P137 wd:Q103204; pq:P973 ?url].}
   }
   ```

   By author name string (P2093) — broader net:

   ```sparql
   SELECT ?file ?url ?image WHERE {
     ?file p:P170 [ pq:P2093 "FaceMePLS"];
           schema:url ?image.
     OPTIONAL{ ?file p:P7482 [ps:P7482 wd:Q74228490; pq:P137 wd:Q103204; pq:P973 ?url].}
   }
   ```

   Replace `"31980831@N04"` with the account's NSID (the same P3267 value is on the
   photographer/organization's Wikidata item) and `"FaceMePLS"` with the photographer's name
   string; the P2093 query usually returns more rows. `?image` is the Commons file URL; `?url`
   is the originating Flickr URL when the origin statement exists. Compare the photo ids from
   `?url` against the photoset and drop the matches.

   These are structured-data queries over MediaInfo entities — see the
   [wikimedia-commons-sdc](../../wikimedia-commons-sdc/SKILL.md) skill for adding or editing the
   underlying SDC statements (creator, origin, license) that make this dedupe work.
2. **Account category**: if the account category exists (`Category:Files from <account> Flickr
   stream`, or the older `Category:Photographs by <account>`), list its files (e.g. via the Commons
   API `list=categorymembers&cmtitle=Category:...`) and collect their photo ids from the filenames
   (`Title (<id>).jpg`).
3. **`insource:` search**: `Special:Search` with `insource:"flickr.com/photos/<nsid>"` returns
   every file whose `{{Information}}` source or `{{Flickr}}` template links to the account — this
   catches files uploaded even without the account category. It only works because uploads keep the
   NSID form in their source URL (see field construction above) — an alias-based or `flic.kr` source
   would be invisible to this search.
4. **Single-file confirmation**: `intitle:"<photo id>"` confirms one specific photo.

Exclude matches from the manifest (or list them separately); the batch upload should only contain
files not yet on Commons.
