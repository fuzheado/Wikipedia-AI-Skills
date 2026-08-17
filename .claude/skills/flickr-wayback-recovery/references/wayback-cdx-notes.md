# Wayback CDX API notes for Flickr recovery

Reference for the queries used in `scripts/cdx-photo-ids.py` and the rescue
pipeline. Endpoint: `https://web.archive.org/cdx/search/cdx`.

## Parameters used

| Parameter | Value | Purpose |
|---|---|---|
| `url` | `flickr.com/photos/<nsid>/*` and `flickr.com/photos/<alias>/*` | Glob pattern; `*` matches everything under the account. Query **both** forms. |
| `output` | `json` | JSON rows: first element is the header, rest are data rows. |
| `fl` | `timestamp,original,statuscode,digest` | Columns; `original` is the captured URL, `timestamp` the 14-digit capture time. |
| `filter` | `statuscode:200` | Drop 301/302/404 captures. |
| `collapse` | `digest` | Dedupe captures with identical content. |

URL-encode the `url` value (`*` becomes `%2A`). A descriptive `User-Agent` and
~1 s sleep between calls keeps the service happy; retry timeouts with backoff.

## Reading the response

```
[["timestamp","original","statuscode","digest"],["20220423085409","https://www.flickr.com/photos/44783532@N07/<photo-id>/","200","..."]]
```

## Replaying a capture

- HTML page (rendered):  `https://web.archive.org/web/<timestamp>/<original>`
- Raw bytes (`id_`):    `https://web.archive.org/web/<timestamp>id_/<original>`

Use `id_` for anything you parse (HTML) or download (images); the non-`id_`
form wraps responses in the Wayback page chrome.

## Pitfalls learned in production

1. **Two URL forms.** The same photo page is captured under both
   `flickr.com/photos/<nsid>/<id>/` and `flickr.com/photos/<alias>/<id>/`.
   Union both; neither alone is complete.
2. **Trailing-slash drop.** A first-pass regex `/photos/<account>/(\d+)/` (with
   required trailing slash) silently dropped **209 IDs** whose only captures use
   the NSID form *without* a trailing slash. Make the slash optional and accept
   the `in/photostream|set-*|album-*|pool-*` suffixes.
3. **Content varies per capture.** One timestamp may be a page shell with no
   `modelExport` blob while another has it; iterate the captures newest-first
   and use the first one that parses.
4. **Image originals.** Image bytes live on `c1.staticflickr.com` (etc.);
   `https://web.archive.org/web/<page_ts>id_/<staticflickr-url>` returns them.
   The largest size key in the photo model is `o` (fall back `k, h, l, c, z`).
5. **HTTP 200 ≠ success.** Wayback replays error pages with HTTP 200; validate
   downloads by magic bytes.
6. **Wildcards: `*` must be a plain trailing glob, never `matchType=prefix`.**
   `url=live.staticflickr.com/65535/<id>_*` returns every size capture for that
   ID (all secrets, all sizes) *only with no matchType*. Adding
   `matchType=prefix` makes the `*` a **literal** character → zero rows.
   Leading-domain wildcards (`*.staticflickr.com/*<id>_*`) return generic
   staticflickr.com root captures, not the image — useless. To prove an image
   is *not* archived, query the trailing-wildcard form first.
7. **Image discovery independent of the page.** For modern accounts the crawler
   follows `<img>`/og:image URLs even when the page is an SPA shell, so image
   captures exist at `live.staticflickr.com/65535/<id>_*` for photos whose pages
   have **no metadata at all**. Scan the image host separately (see
   `scan-cdx-images.py`) — "shell page" does not mean "image lost".
8. **One photo, several secrets.** CDX can show different secrets for the same
   ID (`<id>_<secretA>_b.jpg` and `<id>_<secretB>_n.jpg`) from different crawls;
   the wildcard scan surfaces them all.
9. **429 captures are not images.** Flickr rate-limits the crawler; such rows
   are `429` / `text/html`. Keep only `statuscode=200` with an image mimetype
   when picking the best size.

## Image host patterns to scan

| host+server path | when | wildcard form |
|---|---|---|
| `live.staticflickr.com/65535` | uploads from ~2019 onward | `live.staticflickr.com/65535/<id>_*` |
| `live.staticflickr.com` | server path unknown (rare) | try `/65535/` first, then other numeric servers |
| `farm<N>.staticflickr.com/<server>` | pre-~2019 uploads | `farm8.staticflickr.com/<server>/<id>_*` (farm number + server vary) |

Size suffix → largest first: `_o k h b c z w m n s t q sq` (`l` maps to `_b`,
`m` has no suffix).

## Common queries

```bash
# All photo-page captures under the NSID form (deduped, 200s only)
curl -s 'https://web.archive.org/cdx/search/cdx?url=flickr.com%2Fphotos%2F44783532%40N07%2F*&output=json&fl=timestamp,original,statuscode,digest&filter=statuscode:200&collapse=digest'

# Alias form
curl -s 'https://web.archive.org/cdx/search/cdx?url=flickr.com%2Fphotos%2Fstiftelsen%2F*&output=json&fl=timestamp,original,statuscode,digest&filter=statuscode:200&collapse=digest'

# Coverage view: how many distinct photo IDs were ever captured
curl -s 'https://web.archive.org/cdx/search/cdx?url=flickr.com%2Fphotos%2F44783532%40N07%2F*&output=json&fl=original&collapse=urlkey' | grep -oE 'photos/[^/]+/[0-9]+' | sort -u | wc -l
```
