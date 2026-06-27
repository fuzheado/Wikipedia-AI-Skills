---
name: wikimedia-commons-thumbnails
description: Generate, construct, and retrieve raster thumbnail previews for any Wikimedia Commons file — thumb URL scheme, iiurlwidth/iiurlheight Action API pattern, thumbmime format conversion matrix (raster downscale, SVG→PNG, PDF→JPEG, video keyframes), responsive/retina URLs, REST API thumbnails, SPARQL thumbnailUrl, and caching behavior
depends_on: [wikimedia-api-access, wikimedia-commons]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["thumbnail", "thumb", "preview", "rasterize", "render", "image scaling", "responsive image", "Retina"]
  - keywords: ["thumburl", "thumbmime", "iiurlwidth", "iiurlheight", "responsiveUrls", "thumbwidth", "thumbheight"]
  - keywords: ["thumb.php", "thumbhandler", "thumbnailUrl", "contentUrl", "rendering pipeline", "image thumbnail API"]
  - keywords: ["SVG rasterize", "PDF page render", "DjVu thumbnail", "keyframe", "video thumbnail", "page rendering"]
  - keywords: ["resize image", "downscale", "preview size", "Varnish cache", "thumb cache"]
last_verified: 2026-06-16
---

> ⚠️ **User-Agent required:** All curl and code examples in this skill access Wikimedia APIs. Requests without a descriptive `User-Agent` header will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.
>
> ⚡ **This skill is about the rendering pipeline only.** For file-type-specific concerns (SVG editing, PDF Wikisource integration, audio/video transcoding), see the dedicated skills cross-referenced below.
>
> 💡 **Quickest thumbnail from just a filename:** Skip hash-path computation and
> extra API calls — use `Special:FilePath` instead. See [Section 0](#0-the-easiest-way-special-filepath).



---

## What Is the Commons Thumbnail System?

Every file on Wikimedia Commons gets a **raster thumbnail preview** — a downscaled, reformatted image that can be served quickly to browsers, embedded in articles, and consumed by the API. The thumbnail system:

- **Downscales** raster images (JPEG, PNG, GIF, WebP, TIFF, AVIF) to any supported width
- **Rasterizes** vector and document formats (SVG, PDF, DjVu) into PNG or JPEG at any requested width
- **Extracts keyframes** from video files as JPEG thumbnails
- **Serves generic placeholders** for audio (speaker icon) and other non-visual files
- **Generates responsive/retina versions** (2×, 1.5×) automatically for sufficiently large files

The system spans four access methods: the **Action API**, **direct URL construction**, the **REST API**, and the **legacy thumbhandler**.

---

## Quick Reference

| Goal | Method | Example |
|------|--------|---------|
| Get thumbnail URL inline with file metadata | Action API `iiurlwidth` | `&iiurlwidth=800` on `prop=imageinfo` |
| Construct a thumb URL from scratch | URL scheme | `.../thumb/{hash}/{filename}/{width}px-{filename}.{ext}` |
| Get thumbnail via REST API | `GET /page/image/{title}/{width}px` | `https://commons.wikimedia.org/api/rest_v1/page/image/Example.jpg/800px` |
| Get thumbnail URL from SPARQL | `schema:thumbnailUrl` | `?file schema:thumbnailUrl ?thumb` |
| Responsive/retina versions | `responsiveUrls` field | `"2": ".../1600px-..."` |

### File-Type Behavior at a Glance

| File Type | Original MIME | `thumbmime` | Format Change | Resolution Limit |
|-----------|--------------|-------------|---------------|-----------------|
| JPEG, PNG, GIF, WebP, TIFF, AVIF | `image/jpeg`, etc. | Same as original | ❌ No | Native raster dimensions |
| SVG | `image/svg+xml` | `image/png` | ✅ SVG → PNG | Unlimited (vector) |
| PDF | `application/pdf` | `image/jpeg` | ✅ PDF → JPEG | Unlimited (per page) |
| DjVu | `image/vnd.djvu` | `image/jpeg` | ✅ DjVu → JPEG | Unlimited (per page) |
| Video (WebM, OGV) | `video/webm`, etc. | `image/jpeg` | ✅ Keyframe → JPEG | Keyframe resolution |
| Audio (OGG, FLAC, etc.) | `audio/ogg`, etc. | — | N/A — no real thumb | Generic icon only |

> 🔗 **File-type-specific skills:**
> - SVG rasterization → **[wikimedia-commons-svg](../wikimedia-commons-svg/SKILL.md)**
> - PDF/DjVu page rendering → **[wikimedia-commons-pdf](../wikimedia-commons-pdf/SKILL.md)**
> - Video keyframe extraction → **[wikimedia-commons-audio-video](../wikimedia-commons-audio-video/SKILL.md)**

---

## 0. The Easiest Way: `Special:FilePath`

If you have a filename (e.g., `File:Sunset_over_the_ocean.jpg`) and need a
thumbnail without computing the hash path or making an API call, use the
`Special:FilePath` endpoint:

```
https://commons.wikimedia.org/wiki/Special:FilePath/File:Sunset_over_the_ocean.jpg?width=320
```

This endpoint:
- Accepts the full title (with `File:` prefix), URL-encoded
- Redirects transparently to the actual thumbnail (browser handles the redirect)
- Sets appropriate CORS headers for `<img>` tags
- Works with any file type (JPEG, PNG, SVG, PDF, video keyframes)
- Requires **no** hash-path computation, **no** MD5 hashing, **no** extra API calls

**From JavaScript (browser):**

```javascript
const filename = 'File:Example.jpg';
const thumbUrl = `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(filename)}?width=320`;
document.getElementById('preview').src = thumbUrl;
```

**From Python:**

```python
import urllib.parse

filename = 'File:Example.jpg'
url = f'https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(filename)}?width=320'
```

### When to Use vs. the Action API

| Scenario | Recommended | Why |
|---|---|---|
| You have a filename and need an `<img>` src | ✅ `Special:FilePath` | Zero extra API calls, simplest code |
| You already have file metadata from an API call | ✅ Action API `iiurlwidth` | Thumbnail URL is already in the response |
| You need exact dimensions or responsive 2× URLs | ✅ Action API `iiurlwidth` | Returns `responsiveUrls` and exact `thumbwidth`/`thumbheight` |
| You're building a URL without browser redirects (server-side) | ⚠️ Either approach | `Special:FilePath` requires following a redirect; direct URL is one-hop |
| You don't want to URL-encode special characters | ✅ Action API | Returns pre-built, correctly-encoded URLs |

---

## 1. The Thumb URL Scheme

Every thumb URL follows a predictable pattern:

```
https://upload.wikimedia.org/wikipedia/commons/thumb/{hash_path}/{filename}/{width}px-{dashified_filename}.{ext}
```

Where:

| Part | Source | Example |
|------|--------|---------|
| `{hash_path}` | First two chars of the file's MD5 hash, split into two subdirectories | `a/ab` (from MD5 hash starting with `ab...`) |
| `{filename}` | The bare file name, URL-encoded | `Example.jpg` |
| `{width}` | Requested width in pixels | `800` |
| `{dashified_filename}` | Filename with spaces replaced by underscores, URL-encoded | `Example.jpg` |
| `{ext}` | The **thumbnail** extension (may differ from original) | `.jpg`, `.png` |

### Finding the Hash Path

The hash path is **not computed manually** — it's obtained from the file's `url` field in the API response:

```python
import re

resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "url",
    "titles": "File:Example.jpg",
    "format": "json",
}, timeout=30, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

url = resp.json()["query"]["pages"]["pageid"]["imageinfo"][0]["url"]
# url = "https://upload.wikimedia.org/wikipedia/commons/a/ab/Example.jpg"

# Extract hash path from URL:
# Pattern: commons/{hash_path}/{filename}
match = re.search(r"/commons/([a-f0-9]/[a-f0-9]+)/", url)
hash_path = match.group(1)  # "a/ab"
```

> 💡 **You normally don't construct thumb URLs manually** — the Action API's `iiurlwidth` parameter (see [Section 2](#2-requesting-thumbnails-via-the-action-api)) returns the complete `thumburl` for you. Manual construction is only needed when you have a file URL but want to build the thumb URL without an extra API call.

### Real URL Examples by File Type

| File Type | Thumb URL (800px) |
|-----------|------------------|
| JPEG | `.../thumb/a/ab/Example.jpg/960px-Example.jpg` |
| SVG | `.../thumb/8/80/Wikipedia-logo-v2.svg/960px-Wikipedia-logo-v2.svg.png` |
| PDF (page 1) | `.../thumb/2/27/PDF_metadata.pdf/page1-960px-PDF_metadata.pdf.jpg` |
| WebM (keyframe) | `.../thumb/a/a2/Elephants_Dream_%282006%29.webm/960px--Elephants_Dream_%282006%29.webm.jpg` |

Note the differences:
- **SVG**: extension changes to `.png`
- **PDF**: `page1-` prefix before the width
- **Video**: `--` (double dash) instead of `-{dashified_filename}-` before the filename
- **JPEG**: extension stays `.jpg`

---

## 2. Requesting Thumbnails via the Action API

The most common way to get thumbnail URLs is to request them inline with file metadata using the `iiurlwidth` and `iiurlheight` parameters on `prop=imageinfo`.

### Basic Usage

```bash
curl -s "https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|mime|thumbmime&iiurlwidth=800&titles=File:Example.jpg&format=json" \
  -H "User-Agent: MyBot/1.0 (user@example.com)" | python3 -m json.tool
```

The response includes these thumbnail-specific fields within each `imageinfo` entry:

```json
{
  "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/960px-Example.jpg",
  "thumbwidth": 800,
  "thumbheight": 600,
  "thumbmime": "image/jpeg",
  "responsiveUrls": {
    "2": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/1920px-Example.jpg"
  }
}
```

| Field | Always Present? | Meaning |
|-------|:---:|---|
| `thumburl` | ✅ | Full URL to the generated thumbnail |
| `thumbwidth` | ✅ | Actual width of the returned thumbnail (may differ slightly from requested width due to aspect ratio) |
| `thumbheight` | ✅ | Actual height of the returned thumbnail |
| `thumbmime` | ✅ | MIME type of the **thumbnail** (may differ from the file's `mime`) |
| `responsiveUrls` | ⚠️ | Object with multiplier keys (`"2"`, `"1.5"`) mapping to higher-resolution versions. Only present for files large enough to need responsive scaling. |

### Requesting Exact Dimensions

You can request a specific width or height:

```python
import requests

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "MyBot/1.0 (user@example.com)"})

resp = SESSION.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "url|mime|thumbmime",
    "iiurlwidth": 400,         # request exactly 400px wide
    "titles": "File:Example.jpg",
    "format": "json",
})
data = resp.json()
info = next(iter(data["query"]["pages"].values()))["imageinfo"][0]

print(f"Thumbnail: {info['thumburl']}")
print(f"Dimensions: {info['thumbwidth']}×{info['thumbheight']}")
print(f"Format: {info['thumbmime']}")
```

If you specify both `iiurlwidth` and `iiurlheight`, the server will fit the thumbnail within those bounds while preserving aspect ratio (it may be smaller in one dimension).

### Batch Thumbnails — Multiple Files at Once

The same `iiurlwidth` applies to all titles in one query:

```python
resp = SESSION.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "url|thumbmime",
    "iiurlwidth": 200,
    "titles": "File:Example.jpg|File:Example2.png|File:Example3.svg",
    "format": "json",
})
```

### Requesting Different Thumbnail Sizes for Different Files

The `iiurlwidth` is a single value for the entire query. To get different widths for different files, make separate queries or use `iiurlheight` for one dimension and let the other vary.

---

## 3. Responsive / Retina URLs

When a file is large enough that serving a single thumbnail would look pixelated on high-DPI (Retina) displays, Commons returns a `responsiveUrls` object:

```json
"responsiveUrls": {
  "2": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/1920px-Example.jpg",
  "1.5": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/1440px-Example.jpg"
}
```

| Key | Meaning | When Present |
|-----|---------|-------------|
| `"2"` | 2× Retina (double the requested width) | Always, if file is large enough |
| `"1.5"` | 1.5× Retina | Sometimes, for mid-range files |

**Use in HTML:**

```html
<img src="https://.../960px-Example.jpg"
     srcset="https://.../1440px-Example.jpg 1.5x,
             https://.../1920px-Example.jpg 2x"
     width="800" height="600"
     alt="Example">
```

**Python — constructing responsive srcset from API response:**

```python
info = resp.json()["query"]["pages"]["pageid"]["imageinfo"][0]
srcset_parts = [f"{info['thumburl']} 1x"]

for multiplier, url in info.get("responsiveUrls", {}).items():
    srcset_parts.append(f"{url} {multiplier}x")

srcset = ", ".join(srcset_parts)
```

> ⚠️ **Small files may not get responsive URLs.** If the file's raster dimensions are close to or smaller than the requested thumbnail width, Commons may skip generating responsive versions.

---

## 4. The `thumbmime` Field — Format Conversion Matrix

The `thumbmime` field tells you the MIME type of the generated thumbnail, which may differ from the file's original `mime`. This is the key to understanding what Commons does to render each file type.

### How to Read the Matrix

```bash
curl -s "https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=mime|thumbmime&iiurlwidth=400&titles=File:Example.jpg|File:Logo.svg|File:Doc.pdf|File:Video.webm&format=json" \
  -H "User-Agent: MyBot/1.0 (user@example.com)" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for pid, page in data['query']['pages'].items():
    ii = page.get('imageinfo', [{}])[0]
    print(f\"{page['title']}:  original={ii.get('mime')}  →  thumb={ii.get('thumbmime')}\")
"
```

### Full Matrix

| Original `mime` | File Type | `thumbmime` | Ext | What Happens |
|----------------|-----------|-------------|-----|-------------|
| `image/jpeg` | JPEG | `image/jpeg` | `.jpg` | Downscaled JPEG |
| `image/png` | PNG | `image/png` | `.png` | Downscaled PNG |
| `image/gif` | GIF | `image/gif` | `.gif` | Static frame (animated GIFs get a single frame) |
| `image/webp` | WebP | `image/webp` | `.webp` | Downscaled WebP |
| `image/tiff` | TIFF | `image/jpeg` | `.jpg` | TIFF → JPEG conversion + downscale |
| `image/avif` | AVIF | `image/avif` | `.avif` | Downscaled AVIF |
| `image/svg+xml` | SVG | `image/png` | `.png` | **Rasterized** to PNG at requested width (vector→raster) |
| `application/pdf` | PDF | `image/jpeg` | `.jpg` | **Page rendered** as JPEG |
| `image/vnd.djvu` | DjVu | `image/jpeg` | `.jpg` | **Page rendered** as JPEG |
| `video/webm` | WebM | `image/jpeg` | `.jpg` | **Keyframe extracted** as JPEG |
| `video/ogg` | OGV (Theora) | `image/jpeg` | `.jpg` | **Keyframe extracted** as JPEG |
| `audio/ogg` | OGG Audio | — | — | No real thumbnail; generic icon |
| All audio types | Audio | — | — | No real thumbnail; generic icon |

> ⚠️ **Key takeaway:** Never assume the thumbnail extension matches the file extension. Always check `thumbmime` and derive the extension from it, or just use `thumburl` directly.

### Deriving Extension from thumbmime

```python
MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/avif": ".avif",
}
thumb_ext = MIME_TO_EXT.get(info.get("thumbmime", ""), ".jpg")
```

But again — you rarely need this. Just use `thumburl` directly.

---

## 5. Thumbnail Size Constraints

### Maximum Width

| Context | Max Width | Notes |
|---------|-----------|-------|
| Default API / URL request | **2048 px** | The standard maximum for unauthenticated thumbnails |
| Logged-in users (via API) | **4096 px** | Larger thumbs available to authenticated requests |
| SVG (any request) | **4096 px** | SVGs can be rendered larger because they scale cleanly |
| PDF/DjVu (any request) | **4096 px** | Same reasoning — page rendering is resolution-independent |

**What happens when you exceed the limit?**

The server returns the largest allowed thumbnail (e.g., 2048px instead of 3000px). It does NOT return an error — it silently caps the width. Always check `thumbwidth` in the response to confirm the actual size.

### The Retina Multiplier and Max Width

If you request `iiurlwidth=800`, Commons generates:
- `800px` thumbnail → `thumburl`
- `1600px` (2×) thumbnail → `responsiveUrls["2"]`

But if `1600 > max_width`, the 2× version is capped at max_width and the server returns `responsiveUrls` at the capped size.

### Aspect Ratio Preservation

The thumbnail always preserves the original aspect ratio. If you request `iiurlwidth=800`, the `thumbheight` will be computed automatically:

```
thumbheight = requested_width * (original_height / original_width)
```

For SVGs, the aspect ratio comes from the `viewBox` attribute. For PDFs, from the page dimensions.

---

## 6. REST API Thumbnail Endpoint

The Wikimedia REST API also provides a thumbnail endpoint:

```
GET https://commons.wikimedia.org/api/rest_v1/page/image/{title}/{width}px
```

### Usage

```bash
curl -s "https://commons.wikimedia.org/api/rest_v1/page/image/Example.jpg/800px" \
  -H "User-Agent: MyBot/1.0 (user@example.com)" \
  -o thumbnail.jpg
```

### Limitations

| Aspect | REST API | Direct URL / Action API |
|--------|----------|------------------------|
| File types | Images only (JPEG, PNG, GIF, SVG) | All file types with visual output |
| PDF/DjVu | ❌ Not supported (404) | ✅ Supported via `iiurlwidth` + URL construction |
| Video | ❌ Not supported | ✅ Supported via `iiurlwidth` |
| Metadata in response | Binary only — no metadata returned | Returns `thumbwidth`, `thumbheight`, `thumbmime`, `responsiveUrls` as JSON |
| Headers | Content-Type, Content-Length | N/A (Action API returns JSON) |

> 💡 **When to use the REST API:** When you only need to **download** a thumbnail for a known image file and don't need metadata about it. For anything else (PDFs, video, responsive URLs), use the Action API with `iiurlwidth`.

---

## 7. Thumbhandler Legacy API

Commons has a legacy thumbhandler at:

```
https://commons.wikimedia.org/w/thumb.php?f={filename}&w={width}
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `f` | ✅ | Filename (e.g., `Example.jpg`) |
| `w` | ✅ | Width in pixels |
| `p` | ❌ | Page number for PDF/DjVu (e.g., `1`) |
| `q` | ❌ | Quality (1-100, default ~85) |

### Example

```bash
curl -s "https://commons.wikimedia.org/w/thumb.php?f=Example.jpg&w=400" \
  -H "User-Agent: MyBot/1.0 (user@example.com)" \
  -o thumbnail.jpg
```

### ⚠️ Status

The thumbhandler is **legacy/deprecated**. It still works but:

- Slower than direct URL construction (it's a PHP handler, not a CDN-optimized path)
- No `responsiveUrls` support
- No structured metadata in the response
- Prefer the Action API `iiurlwidth` method or direct URL construction whenever possible

---

## 8. SPARQL Thumbnail Patterns

When querying Commons via SPARQL, you can retrieve thumbnail URLs directly using the `schema:thumbnailUrl` predicate. This is especially useful for generating visual result grids.

### Basic SPARQL — Get Thumbnails for Depicts

```sparql
PREFIX schema: <http://schema.org/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>

SELECT ?file ?thumb ?caption WHERE {
  ?file wdt:P180 wd:Q42 ;            # depicts Douglas Adams
         schema:thumbnailUrl ?thumb ; # thumbnail URL
         rdfs:label ?caption .        # file caption
  FILTER(LANG(?caption) = "en")
}
LIMIT 50
```

> ⚠️ **QLever requires explicit PREFIX declarations.** See the **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** skill for the full prefix block and endpoint details.

### ImageGrid View

The `#defaultView:ImageGrid` directive renders results as a visual grid. It needs `schema:url` (the file page URL, not the thumbnail URL):

```sparql
#defaultView:ImageGrid
PREFIX schema: <http://schema.org/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>

SELECT ?file ?image WHERE {
  ?file wdt:P180 wd:Q42 ;
         schema:url ?image .       # file page URL — ImageGrid renders this as thumbnail
}
```

### Content URL vs Thumbnail URL

| Predicate | Returns | Use Case |
|-----------|---------|----------|
| `schema:url` | File **page** URL (`Special:FilePath/...`) | ImageGrid view, linking |
| `schema:contentUrl` | Direct **download** URL for the full file | Raw file access |
| `schema:thumbnailUrl` | **Thumbnail** URL (typically ~800px) | Embedding in results, previews |

```sparql
SELECT ?full ?thumb ?file WHERE {
  ?file schema:contentUrl ?full ;
         schema:thumbnailUrl ?thumb .
}
LIMIT 10
```

### Filtering by Image Size (Useful for Thumbnails)

```sparql
# Files wider than 4000px — useful to know which files have large responsive thumbnails
PREFIX schema: <http://schema.org/>

SELECT ?file ?w ?h ?thumb WHERE {
  ?file schema:width ?w ;
         schema:height ?h ;
         schema:thumbnailUrl ?thumb .
  FILTER(?w > 4000)
}
LIMIT 100
```

---

## 9. Caching Behavior

Commons uses **Varnish** as its HTTP cache, deployed globally across multiple data centers. Thumbnails are cached aggressively.

### Cache Keys

Thumbnails are cached by their full URL. The same URL always returns the same thumbnail unless the file is updated.

### Cache Invalidation

| Event | Effect |
|-------|--------|
| New file upload | Thumbnails generated on first request (cold cache) |
| File updated (new version) | All thumbnails for that file are **purged** from cache |
| Thumbnail requested at new width | Generated and cached; previously cached widths are unaffected |

### Cold vs Warm Cache

- **Cold cache** (first request after upload or update): The server renders the thumbnail on-demand. For SVGs, PDFs, and videos, this can take **several seconds** for the first request.
- **Warm cache** (subsequent requests): The thumbnail is served from edge cache in **milliseconds**.

### Cache Durations

| Content | TTL (typical) |
|---------|---------------|
| Popular thumbnails (frequently requested) | Indefinite (pinned in cache) |
| Unpopular thumbnails | Until evicted by LRU |
| After file update | Immediately purged |

> 💡 **Practical implication:** When you upload a new version of a file (especially an SVG), the first few thumbnail requests may be slow as the cache warms. This is normal. The thumbnail URL stays the same — the old cache entry is purged and the new one is generated on first access.

---

## Putting It All Together: A Complete Example

```python
#!/usr/bin/env python3
"""
Fetch thumbnails for multiple Commons files with different types.
Demonstrates iiurlwidth, thumbmime handling, and responsive URLs.
"""

import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = "ThumbnailDemo/1.0 (https://example.com; user@example.com)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA})

def get_thumb_info(title, width=400):
    """Get thumbnail info for a file at the given width."""
    resp = SESSION.get(API, params={
        "action": "query",
        "prop": "imageinfo",
        "iiprop": "url|mime|thumbmime|size",
        "iiurlwidth": width,
        "titles": title,
        "format": "json",
    })
    resp.raise_for_status()
    pages = resp.json()["query"]["pages"]
    page = next(iter(pages.values()))
    info = page.get("imageinfo", [{}])[0]
    return page["title"], info.get("mime"), info.get("thumbmime"), info.get("thumburl"), info.get("thumbwidth"), info.get("thumbheight"), info.get("responsiveUrls", {})

files = [
    "File:Example.jpg",
    "File:Wikipedia-logo-v2.svg",
    "File:PDF metadata.pdf",
    "File:Elephants Dream (2006).webm",
]

for title in files:
    name, mime, tmime, url, tw, th, resp_urls = get_thumb_info(title, 400)
    print(f"\n📄 {name}")
    print(f"   Original: {mime}")
    print(f"   Thumb:    {tmime}")
    print(f"   URL:      {url}")
    print(f"   Size:     {tw}×{th}")
    if resp_urls:
        for mult, u in resp_urls.items():
            print(f"   {mult}×:  {u}")
```

---

## 10. CORS: When Direct Thumbnail URLs Are Blocked

When embedding Commons thumbnails in browser-based applications (JavaScript, CSS `background-image`, `<img>` elements), you may encounter **CORS (Cross-Origin Resource Sharing) errors**. This happens when your application runs on one origin (e.g., `localhost:8765` or `your-app.toolforge.org`) and tries to fetch resources directly from `upload.wikimedia.org`.

### The Problem

```
Access to image at 'https://upload.wikimedia.org/wikipedia/commons/thumb/...'
from origin 'http://localhost:8765' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

Chrome DevTools shows: `net::ERR_BLOCKED_BY_ORB` (Opaque Response Blocking).

### Why This Happens

Wikimedia's image servers (`upload.wikimedia.org`) **do not send CORS headers** by default. This is intentional — it prevents third-party sites from:
- Reading image pixel data via JavaScript Canvas APIs
- Using the images in WebGL contexts that require `crossorigin` attributes
- Exfiltrating user-specific information through image requests

For most use cases, this is fine — images are displayed, not processed. But browser security policies now block certain operations on cross-origin images without explicit CORS headers.

### Solutions

| Approach | When to Use | Complexity |
|----------|-------------|------------|
| **Use the file page URL** | Displaying images in `<img>` tags | Low — works for simple display |
| **Proxy through your server** | Canvas/WebGL/`background-image` in CSS | Medium — requires server-side code |
| **Use the REST API thumbnail endpoint** | Modern browsers, single-origin apps | Low — returns CORS headers |

#### 1. Use the File Page URL (Simple Display Only)

For basic image display (no Canvas, no WebGL), use the **file page URL** instead of the direct upload URL:

```
# Direct upload URL (no CORS headers)
https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/800px-Example.jpg

# File page URL (CORS-friendly, redirects to thumbnail)
https://commons.wikimedia.org/wiki/Special:FilePath/Example.jpg?width=800
```

The `Special:FilePath/` endpoint sets appropriate CORS headers and redirects to the actual image. This works for `<img>` tags but may still fail for Canvas/WebGL operations.

#### 2. Proxy Through Your Server (Canvas/WebGL/`background-image`)

For applications that need full access to image data (Canvas, WebGL textures, CSS `background-image`), **proxy the image through your own server**:

```javascript
// Client: request from your server
const thumbUrl = '/images/abc123.jpg';  // your proxied path

// Server (Node.js example):
// 1. Download from Commons
const resp = await fetch(thumbnailUrl);
const buffer = await resp.arrayBuffer();

// 2. Cache locally (e.g., SHA-256 hash filename)
const hash = createHash('sha256').update(buffer).digest('hex');
const filepath = `cache/${hash}.jpg`;
await writeFile(filepath, buffer);

// 3. Serve from your origin (same-origin = no CORS)
return { url: `/images/${hash}.jpg`, original: thumbnailUrl };
```

**Key insight:** The browser requests from `your-origin` → your server fetches from Commons → your server caches and serves from `your-origin`. The browser sees the response as **same-origin**, so no CORS restrictions apply.

**Example from the Wikimedia Photosphere Tours project:**

```javascript
// Server endpoint: /api/resolve?file=Example.jpg
// Returns: { url: "/images/<hash>.jpg", thumb: "...", original: "..." }

// Client uses the local path (same-origin, no CORS)
scene.panorama = "/images/abc123.jpg";  // works in Canvas/WebGL/CSS

// Server already provides direct Commons URLs for export (not for browser use)
scene._thumb = "https://upload.wikimedia.org/.../200px-...";  // CORS blocked if used in browser
scene._original = "https://upload.wikimedia.org/.../Example.jpg";  // fine for export/download
```

#### 3. Use REST API Thumbnail Endpoint

The REST API's thumbnail endpoint (`/api/rest_v1/page/image/{title}/{width}px`) may include CORS headers in some configurations. Check the response headers for your specific use case.

### Decision Tree

```
Do you need to read pixel data (Canvas, WebGL)?
├── YES -> Proxy through your server (Solution 2)
└── NO
    └── Is it just for display (<img>, CSS background)?
        ├── YES -> Try Special:FilePath URL (Solution 1)
        └── Still blocked?
            └── Proxy through your server (Solution 2)
```

### Common Pitfall: Ignoring Proxy Paths

When your server returns both `url` (proxied path) and `thumb`/`original` (direct Commons URLs), **always use `url` for browser rendering**. A common mistake is to use `thumb` directly:

```javascript
// WRONG - direct Commons URL, CORS blocked
const thumbUrl = scene._thumb;  // "https://upload.wikimedia.org/..."
element.style.backgroundImage = `url(${thumbUrl})`;

// CORRECT - proxied path, same-origin
const thumbUrl = scene.panorama;  // "/images/abc123.jpg"
element.style.backgroundImage = `url(${thumbUrl})`;
```

This pattern applies to thumbnails, panoramas, audio/video files, and any other media served from `upload.wikimedia.org`.

---

## Related Skills

| Skill | Relevance |
|-------|-----------|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent, rate limiting, error handling for all API calls |
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | File search, metadata, categories — finding files to thumbnail |
| **[wikimedia-commons-svg](../wikimedia-commons-svg/SKILL.md)** | SVG editing, versioning, and the rasterization implications |
| **[wikimedia-commons-pdf](../wikimedia-commons-pdf/SKILL.md)** | PDF page rendering, page selection in thumbnails |
| **[wikimedia-commons-audio-video](../wikimedia-commons-audio-video/SKILL.md)** | Video keyframe extraction, transcoding pipeline |
| **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** | SPARQL queries for `schema:thumbnailUrl` and `schema:contentUrl` |
