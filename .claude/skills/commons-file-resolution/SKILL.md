---
name: commons-file-resolution
description: Resolve Wikimedia Commons file references (File:Example.jpg) to browser-usable HTTP URLs — direct origin URLs, thumbnails, Special:FilePath redirects, cache-busting with timestamps, Action API imageinfo queries, and CORS-aware serving patterns for web applications
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access, wikimedia-commons]
skill_discovery_hints:
  - keywords: ["Commons file", "file URL", "direct URL", "resolve file", "image URL", "upload URL", "Special:FilePath"]
  - keywords: ["File: prefix", "File reference", "wiki file", "filename resolution", "media URL"]
  - keywords: ["CORS", "cross-origin", "upload.wikimedia.org", "image proxy", "cache image", "local cache"]
  - keywords: ["imageinfo", "prop=imageinfo", "iiprop=url", "thumburl", "file metadata", "file info"]
  - keywords: ["cache bust", "timestamp", "v parameter", "image version", "file history", "purge file"]
  - keywords: ["browser app", "WebGL", "Canvas", "Pannellum", "360 photo", "photosphere", "panorama viewer"]
last_verified: 2026-06-20
---

> ⚠️ **User-Agent required:** All curl and code examples access Wikimedia APIs. Requests without a descriptive `User-Agent` header will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill.

> 💡 **Already know which endpoint you need?** See the **Quick Reference** table below. Otherwise, the **SOPs** walk through each approach step by step.

---

## The Problem

Browser applications cannot use `File:Example.jpg` — the wiki page reference — as an image source. They need a real HTTP URL. Wikimedia Commons stores uploaded files at `upload.wikimedia.org` with a hash-based path, but the exact URL depends on the file's upload timestamp, the hash of its name, and whether you want the original or a thumbnail.

This skill covers every method for resolving a `File:` reference to a working URL, from simplest (server-side redirect) to most robust (full Action API query with cache busting).

---

## Quick Reference

| Goal | Method | Code / URL | Complexity |
|------|--------|------------|------------|
| One-off URL, server-side | `Special:FilePath/` redirect | `https://commons.wikimedia.org/wiki/Special:FilePath/File:Example.jpg` | ⭐ |
| One-off URL, browser `<img>` | `Special:FilePath/` redirect | Same URL, browser follows 302 redirect | ⭐ |
| Full metadata + URL | Action API `prop=imageinfo` | `action=query&prop=imageinfo&titles=File:Example.jpg&iiprop=url\|timestamp\|size\|mime` | ⭐⭐ |
| Thumbnail URL | Add `?width=` to `Special:FilePath/` | `Special:FilePath/File:Example.jpg?width=800` | ⭐ |
| Thumbnail via API | `iiurlwidth` parameter | `prop=imageinfo&iiurlwidth=800` | ⭐⭐ |
| Cache-busted URL (latest version) | `timestamp` from API + `?v=` param | Append `?v={unix timestamp}` to URL | ⭐⭐ |
| Same-origin for WebGL/Canvas | Proxy through own server | Fetch → cache locally → serve from own domain | ⭐⭐⭐ |
| Batch resolution | Action API multi-title query | `titles=File:A.jpg\|File:B.jpg\|File:C.jpg` | ⭐⭐ |

---

## How Commons File URLs Work

### The `upload.wikimedia.org` URL Structure

Every file on Commons has a canonical URL with this structure:

```
https://upload.wikimedia.org/wikipedia/commons/{hash_prefix}/{filename}
```

The `hash_prefix` is derived from the **MD5 hash of the filename** (including the `File:` namespace prefix, but as it appears in the wiki database — the first two hex characters):

```
md5("Example.jpg")[0:2]  →  "4d"
```

So `File:Example.jpg` lives at:

```
https://upload.wikimedia.org/wikipedia/commons/4/4d/Example.jpg
```

The hash prefix determines which of the 256 possible subdirectories the file sits in. This is the **permanent, immutable base URL** for a given filename.

### Thumbnail URL Structure

Thumbnails follow a consistent pattern branching off the base URL:

```
https://upload.wikimedia.org/wikipedia/commons/thumb/{hash}/{filename}/{width}px-{filename}.{ext}
```

Example: `File:Example.jpg` at 800px width:

```
https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Example.jpg/800px-Example.jpg
```

For SVG, PDF, and video files, the thumbnail URL may include an extra page/frame parameter:

```
https://upload.wikimedia.org/wikipedia/commons/thumb/{hash}/{filename}/{width}px-{filename}.png
https://upload.wikimedia.org/wikipedia/commons/thumb/{hash}/{filename}/{width}px-{filename}.jpg  # PDF->JPEG
```

> 🔗 For full thumbnail URL construction rules (responsive/retina, format conversion, file-type-specific behavior), see **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)**.

---

## SOP 1: `Special:FilePath/` — Simplest Server-Side Resolution

The `Special:FilePath/` page redirects to the file's canonical URL. This is the **easiest and most reliable** method when you just need a browser-usable URL on the server side.

### How It Works

`https://commons.wikimedia.org/wiki/Special:FilePath/File:Example.jpg` returns an HTTP **302 redirect** to the canonical `upload.wikimedia.org` URL. The `/w/` path also works:

```
https://commons.wikimedia.org/w/index.php?title=Special:FilePath/File:Example.jpg
```

### Server-Side Usage (Node.js)

```javascript
async function resolveCommonsFile(filename) {
    const url = `https://commons.wikimedia.org/wiki/Special:FilePath/${encodeURIComponent(filename)}`;
    const resp = await fetch(url, {
        method: 'HEAD',                 // HEAD avoids downloading the file
        redirect: 'manual',             // Don't follow the redirect — we want the URL
        headers: { 'User-Agent': 'YourApp/1.0 (contact)' },
    });
    if (resp.status !== 302 && resp.status !== 301) {
        throw new Error(`File not found: ${filename} (HTTP ${resp.status})`);
    }
    return resp.headers.get('location'); // The direct upload.wikimedia.org URL
}
```

**Why HEAD + redirect:manual over GET:**
- HEAD avoids downloading the file just to find its URL
- `redirect: manual` lets you capture the `Location` header instead of following it

### Browser Usage

In an `<img>` tag, the browser follows the redirect automatically:

```html
<img src="https://commons.wikimedia.org/wiki/Special:FilePath/File:Example.jpg?width=800">
```

The `?width=` parameter adjusts thumbnail size (omitting it returns the original).

### Limitations

| Limitation | Impact |
|------------|--------|
| **No metadata** | You only get the URL. No timestamp, size, MIME type, or license info |
| **HEAD may not redirect** | Some file types return 200 instead of 302 for HEAD (rare, but confirmed for certain SVGs) |
| **No cache-busting** | The URL is fixed — if the file is overwritten, the old URL still points to the old version (see cache busting below) |
| **CORS** | `upload.wikimedia.org` doesn't set permissive CORS headers. `Special:FilePath/` itself is on `commons.wikimedia.org` which has permissive CORS — but the redirect destination (`upload.wikimedia.org`) does NOT |

---

## SOP 2: Action API `prop=imageinfo` — Full Metadata + URL

When you need the URL **plus metadata** (timestamp, size, MIME type) in a single call, use the Action API. This is the most robust method.

### Basic Query

```http
GET https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File:Example.jpg&iiprop=url|timestamp|size|mime&format=json
```

### Response Structure

```json
{
  "query": {
    "pages": {
      "12345": {
        "pageid": 12345,
        "ns": 6,
        "title": "File:Example.jpg",
        "imageinfo": [
          {
            "url": "https://upload.wikimedia.org/wikipedia/commons/4/4d/Example.jpg",
            "descriptionurl": "https://commons.wikimedia.org/wiki/File:Example.jpg",
            "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Example.jpg/800px-Example.jpg",
            "thumbwidth": 800,
            "thumbheight": 600,
            "timestamp": "2024-06-15T12:34:56Z",
            "size": 1234567,
            "width": 4000,
            "height": 3000,
            "mime": "image/jpeg"
          }
        ]
      }
    }
  }
}
```

### Key Properties

| Field | Purpose |
|-------|---------|
| `url` | **Direct canonical URL** — use this for `<img>` or as the `panorama` URL in Pannellum |
| `thumburl` | Pre-generated thumbnail URL (defaults to 800px wide) |
| `timestamp` | Last modification timestamp — essential for cache busting |
| `size`, `width`, `height` | File size and dimensions |
| `mime` | MIME type — useful for format detection |

### Custom Thumbnail Size via `iiurlwidth`

```http
GET https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File:Example.jpg&iiurlwidth=1920&format=json
```

The response includes `thumburl`, `thumbwidth`, and `thumbheight` for the requested width.

### Batch Resolution (Multiple Files)

Query up to **50 files** in a single request:

```http
GET https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File:A.jpg|File:B.jpg|File:C.jpg&iiprop=url|timestamp&format=json
```

### Node.js Implementation

```javascript
async function resolveCommonsFile(filename) {
    const url = 'https://commons.wikimedia.org/w/api.php?' + new URLSearchParams({
        action: 'query',
        prop: 'imageinfo',
        titles: filename,
        iiprop: 'url|timestamp|size|mime',
        format: 'json',
    });
    const resp = await fetch(url, {
        headers: { 'User-Agent': 'YourApp/1.0 (contact)' },
    });
    const data = await resp.json();
    const pages = data?.query?.pages;
    if (!pages) throw new Error('API returned no pages');
    const page = Object.values(pages)[0];
    if (!page || page.missing === '') throw new Error(`File not found: ${filename}`);
    return page.imageinfo[0];
}
```

Returns: `{ url, thumburl, thumbwidth, thumbheight, timestamp, size, width, height, mime }`

---

## SOP 3: Cache Busting — Always Get the Latest Version

Files on Commons can be overwritten with new versions (new upload to the same filename). The canonical URL (`upload.wikimedia.org/...`) is **immutable per upload** — if the file is overwritten, a NEW hash-based path is created, and the old URL still serves the OLD version.

To always get the latest version, append the file's timestamp as a query parameter:

```javascript
const info = await resolveCommonsFile('File:Example.jpg');
const unixTimestamp = new Date(info.timestamp).getTime();  // e.g., 1718469296000
const bustedUrl = info.url + '?v=' + unixTimestamp;
// → https://upload.wikimedia.org/wikipedia/commons/4/4d/Example.jpg?v=1718469296000
```

The `?v=` parameter is respected by Commons' CDN/Varnish layer — it treats URLs with different `?v=` as distinct cache entries.

### Cache Busting for Thumbnails

Apply the same pattern to thumbnails:

```javascript
const bustedThumb = info.thumburl + '?v=' + new Date(info.timestamp).getTime();
```

### Updating Cached URLs

When you've cached a file locally (see SOP 4), re-resolve periodically or on error:

```javascript
// If an image fails to load, re-resolve in case it was overwritten
async function getFreshUrl(filename) {
    const info = await resolveCommonsFile(filename);
    return info.url + '?v=' + new Date(info.timestamp).getTime();
}
```

---

## SOP 4: Same-Origin Serving for WebGL / Canvas Applications

Browsers that use **WebGL** (e.g., Pannellum 360° viewer) or **Canvas 2D** faces a CORS problem: `upload.wikimedia.org` does not set `Access-Control-Allow-Origin: *`. This means:

- ❌ `<img>` tags work fine (CORS doesn't affect display)
- ❌ `fetch()` to `upload.wikimedia.org` fails for cross-origin reads
- ❌ WebGL textures from `upload.wikimedia.org` fail with security errors
- ✅ **Proxied images** from your own server work everywhere

### Solution: Local Image Cache

Download images from Commons through your server, caching them locally, and serve them from your own domain. This gives you:

- ✅ Same-origin WebGL/CORS compatibility
- ✅ Faster repeat loads (local cache)
- ✅ Cache control headers you control
- ✅ Bandwidth savings (one download from Commons, many serves to clients)

### Server-Side Implementation (Node.js, zero dependencies)

```javascript
import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';

const CACHE_DIR = './images';
const USER_AGENT = 'YourApp/1.0 (contact)';

async function resolveCommonsFile(filename) {
    const apiUrl = 'https://commons.wikimedia.org/w/api.php?' + new URLSearchParams({
        action: 'query',
        prop: 'imageinfo',
        titles: filename.startsWith('File:') ? filename : 'File:' + filename,
        iiprop: 'url|timestamp',
        format: 'json',
    });
    const resp = await fetch(apiUrl, {
        headers: { 'User-Agent': USER_AGENT },
    });
    const data = await resp.json();
    const page = Object.values(data.query.pages)[0];
    if (!page || page.missing === '') throw new Error(`File not found: ${filename}`);
    const info = page.imageinfo[0];
    return {
        url: info.url + '?v=' + new Date(info.timestamp).getTime(),
        thumb: info.thumburl + '?v=' + new Date(info.timestamp).getTime(),
        original: info.url,
        timestamp: info.timestamp,
    };
}

async function cacheImage(sourceUrl) {
    const hash = createHash('sha256').update(sourceUrl).digest('hex').substring(0, 16);
    const cachePath = join(CACHE_DIR, hash + '.jpg');
    const cacheMeta = join(CACHE_DIR, hash + '.json');

    // Serve from cache if available
    if (existsSync(cachePath)) {
        const meta = JSON.parse(await readFile(cacheMeta, 'utf-8'));
        return { url: '/images/' + hash + '.jpg', thumb: meta.thumb, original: meta.original };
    }

    // Download and cache
    if (!existsSync(CACHE_DIR)) await mkdir(CACHE_DIR, { recursive: true });
    const resp = await fetch(sourceUrl, {
        headers: { 'User-Agent': USER_AGENT },
    });
    if (!resp.ok) throw new Error(`Failed to download: HTTP ${resp.status}`);
    const buffer = Buffer.from(await resp.arrayBuffer());
    await writeFile(cachePath, buffer);

    // Determine extension from MIME type
    const contentType = resp.headers.get('content-type') || 'image/jpeg';
    const ext = { 'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp' }[contentType] || '.jpg';
    const finalPath = join(CACHE_DIR, hash + ext);
    if (finalPath !== cachePath) {
        // Remove old .jpg path, write with correct extension
        await writeFile(finalPath, buffer);
    }

    return { url: '/images/' + hash + ext, thumb: null, original: sourceUrl };
}
```

### Serving Cached Images

```javascript
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

const MIME = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.png': 'image/png',  '.webp': 'image/webp',
};

createServer(async (req, res) => {
    const url = new URL(req.url, 'http://localhost');

    // Serve cached images with proper headers
    if (url.pathname.startsWith('/images/')) {
        const filePath = join(CACHE_DIR, url.pathname.slice(8));
        try {
            const data = await readFile(filePath);
            const ext = '.' + filePath.split('.').pop();
            res.writeHead(200, {
                'Content-Type': MIME[ext] || 'application/octet-stream',
                'Content-Length': data.length,
                'Cache-Control': 'public, max-age=604800, immutable',  // 1 week
            });
            res.end(data);
        } catch {
            res.writeHead(404); res.end('Not found');
        }
        return;
    }

    // API endpoint to resolve and cache
    if (url.pathname === '/api/resolve') {
        const file = url.searchParams.get('file');
        if (!file) { res.writeHead(400); res.end('Missing file param'); return; }
        try {
            const resolved = await resolveCommonsFile(file);
            const cached = await cacheImage(resolved.url);
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify(cached));
        } catch (e) {
            res.writeHead(404, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: e.message }));
        }
        return;
    }

    res.writeHead(404); res.end();
}).listen(8765);
```

### Cache Resolution Flow

```
                   ┌──────────────────────┐
                   │  Browser              │
                   │  (Pannellum Viewer)   │
                   └──────────┬───────────┘
                              │
                        GET /images/abc123.jpg
                              │
                   ┌──────────▼───────────┐
                   │  Your Server          │
                   │  (same origin ✓)      │
                   │                       │
                   │  File on disk?        │
                   │   ├── YES → serve     │
                   │   └── NO  →           │
                   │    1. Fetch from      │
                   │       upload.wikime-  │
                   │       dia.org         │
                   │    2. Save to cache   │
                   │    3. Serve to client │
                   └───────────────────────┘
```

### Caching Caveats

| Concern | Mitigation |
|---------|------------|
| **Stale images** (file overwritten on Commons) | Re-resolve periodically or on 404. Include `?v=` timestamp in source URL before caching. |
| **Disk space** | Implement LRU eviction. 500MB is a safe cap for most tools. |
| **Concurrent requests** for same missing image | Use a promise cache: if a download is in-flight, queue other requests for the same URL. |
| **Extension guessing** | Use Content-Type from the download response, not the filename. |
| **Cache directory growth** | Delete files accessed > N days ago via a periodic cleanup job. |

### When NOT to Cache Locally

- You only need to display images in `<img>` tags (no WebGL/Canvas) → use `Special:FilePath/` directly
- You need thumbnails at varying sizes → use `Special:FilePath/?width=N` or the thumbnail API
- Your traffic is very low → the complexity isn't worth it

---

## SOP 5: Beyond Commons — Cross-Wiki File Resolution

Files can also be hosted on other wikis (e.g., `File:Example.jpg` on English Wikipedia). The `action=query` API works across all wikis:

```javascript
const WIKI_CONFIGS = {
    commons: 'https://commons.wikimedia.org/w/api.php',
    en:      'https://en.wikipedia.org/w/api.php',
    de:      'https://de.wikipedia.org/w/api.php',
    // ... any wiki prefix
};

async function resolveFileAcrossWikis(filename, wikiPrefix = 'commons') {
    const apiUrl = WIKI_CONFIGS[wikiPrefix];
    if (!apiUrl) throw new Error(`Unknown wiki: ${wikiPrefix}`);
    const url = apiUrl + '?' + new URLSearchParams({
        action: 'query',
        prop: 'imageinfo',
        titles: filename,
        iiprop: 'url|timestamp',
        format: 'json',
    });
    const resp = await fetch(url, {
        headers: { 'User-Agent': 'YourApp/1.0 (contact)' },
    });
    const data = await resp.json();
    const page = Object.values(data.query.pages)[0];
    if (!page || page.missing === '') throw new Error(`File not found on ${wikiPrefix}`);
    return page.imageinfo[0];
}
```

**Note:** Files on non-Commons wikis may link to Commons via the `InstantCommons` mechanism — the API returns the Commons URL in that case.

---

## Reference: URL Patterns Cheat Sheet

| What | URL Pattern |
|------|-------------|
| Direct file URL | `https://upload.wikimedia.org/wikipedia/commons/{hash[0:2]}/{hash}/{filename}` |
| Thumbnail | `https://upload.wikimedia.org/wikipedia/commons/thumb/{hash}/{filename}/{width}px-{filename}.{ext}` |
| Special:FilePath | `https://commons.wikimedia.org/wiki/Special:FilePath/File:{filename}` |
| Special:FilePath with width | `https://commons.wikimedia.org/wiki/Special:FilePath/File:{filename}?width={width}` |
| API imageinfo | `https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&titles=File:{filename}&iiprop=url\|timestamp` |
| Cache-busted | `{url}?v={unix_timestamp_ms}` |
| Local cached | `/images/{sha256_prefix}.{ext}` |

---

## Reference: CORS Behavior by URL Type

| URL Type | CORS Headers | WebGL Safe | `<img>` Tag | `fetch()` |
|----------|-------------|------------|-------------|-----------|
| `commons.wikimedia.org/wiki/...` | `Access-Control-Allow-Origin: *` | ✅ | ✅ | ✅ |
| `upload.wikimedia.org/...` | None | ❌ | ✅ | ❌ |
| Your server `/images/...` | You control them | ✅ | ✅ | ✅ |
| `Special:FilePath/` redirect | None on destination | ❌ | ✅ | ❌ |

---

## See Also

- **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** — Full thumbnail URL construction, responsive sizes, format conversion
- **[wikimedia-commons](../wikimedia-commons/SKILL.md)** — File search, metadata, upload, categories
- **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** — User-Agent, rate limiting, error handling
- **CAVEATS.md in the Photosphere Tours project** — Real-world gotchas from a browser app that heavily uses file resolution
