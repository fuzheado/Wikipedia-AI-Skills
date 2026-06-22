---
name: wikimedia-commons
description: Search, upload, and understand Wikimedia Commons — the free media repository of images, video, sound, 3D files, PDFs, and other media used across Wikipedia and its sister projects. Browse categories, find reusable media, and retrieve file metadata
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["Commons", "Commons file", "Commons upload", "image", "photo", "file", "media", "free media"]
  - keywords: ["search Commons", "find image", "media search", "find file", "category"]
  - keywords: ["license", "copyright", "CC BY", "Creative Commons", "public domain", "CC0"]
  - keywords: ["upload", "UploadWizard", "upload file", "bulk upload", "Pattypan"]
  - keywords: ["EXIF", "metadata", "file info", "global usage", "file metadata"]
  - keywords: ["depicts", "haswbstatement", "structured data", "QuickStatements"]
  - keywords: ["VRT", "permission", "Commons policy"]
  - keywords: ["Commons namespaces", "gallery", "Creator namespace"]
  - keywords: ["CORS", "cross-origin", "upload.wikimedia.org", "browser app", "Canvas", "WebGL"]
last_verified: 2026-06-16
---

> ⚠️ **User-Agent required:** All curl and code examples in this skill access Wikimedia APIs. Requests without a descriptive `User-Agent` header will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

Wikimedia Commons (https://commons.wikimedia.org) is a **free media repository** — a central library of freely licensed images, audio, video, 3D models, PDF documents, and other media files. Media uploaded to Commons is available for use across all Wikimedia projects (Wikipedia, Wiktionary, Wikisource, etc.) and by the general public. As of 2026, Commons hosts over 100 million file uploads.

### **Related Commons Skills**

This skill covers the **generic** Commons workflow (search, upload, licensing, categories). Specialized file types and subsystems have their own dedicated skills:

| Skill | Covers |
|-------|--------|
| **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** | Thumbnail generation, thumb URL scheme, `iiurlwidth`/`iiurlheight`, `thumbmime` format conversion, responsive/retina URLs, REST API thumbnails, SPARQL `thumbnailUrl` |
| **[wikimedia-commons-svg](../wikimedia-commons-svg/SKILL.md)** | SVG source access and editing, W3C validation, creation/optimization tools, versioning/diffing, vector-specific categories and SDC |
| **[wikimedia-commons-pdf](../wikimedia-commons-pdf/SKILL.md)** | Multi-page PDF/DjVu model, page selection for thumbnails, Wikisource proofread integration, OCR, document metadata |
| **[wikimedia-commons-audio-video](../wikimedia-commons-audio-video/SKILL.md)** | Audio/video format policy (patent restrictions), upload + transcoding, metadata (duration, codecs, resolution), player widget, TimedText subtitles, derivatives |
| **[commons-file-resolution](../commons-file-resolution/SKILL.md)** | Resolve `File:` references to browser-usable HTTP URLs — origin URLs, thumbnails, `Special:FilePath`, cache-busting, CORS-aware serving |
| **[wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md)** | Structured Data on Commons — captions, depicts, copyright/license statements, batch editing |
| **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** | Commons SPARQL queries via QLever and WCQS — MediaInfo entities, depicts/copyright/license graph, federated queries with Wikidata |

---

## **What Commons Is — and Isn't**

- **Is:** A repository for **educational media** — photographs, diagrams, maps, charts, sound recordings, video clips, 3D models (`.stl`), PDF documents, and other materials that serve an educational purpose.
- **Is:** A host for **freely licensed** content that anyone can reuse, adapt, and redistribute — including for commercial purposes.
- **Is:** A project of the Wikimedia Foundation, governed by its own community policies.
- **Is not:** A personal photo album, a social media platform, a web host, or a place for content that is only available under restrictive licenses.

## **File Types Accepted**

Commons accepts uploads in many formats. The most common categories:

| Category | Common Formats | See Dedicated Skill |
|----------|---------------|--------------------|
| Images (raster) | JPEG, PNG, GIF, TIFF, WebP, AVIF | — |
| Images (vector) | SVG | **[svg](../wikimedia-commons-svg/SKILL.md)** |
| Audio | MP3, OGG (Vorbis/Opus), FLAC, WAV | **[audio-video](../wikimedia-commons-audio-video/SKILL.md)** |
| Video | WebM (VP8/VP9/AV1), OGV (Theora) | **[audio-video](../wikimedia-commons-audio-video/SKILL.md)** |
| 3D Models | STL (rendered via [3D viewer](https://commons.wikimedia.org/wiki/Commons:3D)) | — |
| Documents | PDF, DjVu | **[pdf](../wikimedia-commons-pdf/SKILL.md)** |
| Animations | GIF, APNG, animated SVG | **[svg](../wikimedia-commons-svg/SKILL.md)** (animated SVG) |

## **Quick Reference: What Do You Want to Find?**

| Goal | Best Method | API / Endpoint | Key Parameters |
|------|-------------|----------------|----------------|
| Find images by keyword | Action API search (`srnamespace=6`) | `https://commons.wikimedia.org/w/api.php` | `action=query&list=search&srnamespace=6&srsearch=keyword&srlimit=50` |
| Find images with visual browsing | MediaSearch backend | `https://commons.wikimedia.org/w/api.php` | `action=query&list=search&srnamespace=6&srbackend=MediaSearch&srsearch=keyword` |
| Find files by structured data (e.g., "depicts human") | `haswbstatement:` prefix in search | `https://commons.wikimedia.org/w/api.php` | `srsearch=haswbstatement:P180=Q5` (works in `srsearch` for Action API, or directly in the web search box) |
| Get file metadata (license, author, date) | Action API (`prop=imageinfo`) | `https://commons.wikimedia.org/w/api.php` | `action=query&prop=imageinfo&titles=File:Example.jpg&iiprop=extmetadata\|user\|timestamp` |
| Check where a file is used across wikis | Action API (`prop=globalusage`) | `https://commons.wikimedia.org/w/api.php` | `action=query&prop=globalusage&titles=File:Example.jpg` |
| Generate a thumbnail | Action API `iiurlwidth` or URL construction | `prop=imageinfo&iiurlwidth=800` | See **[thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** skill |
| Find files in a specific category | Action API (`list=categorymembers`) | `https://commons.wikimedia.org/w/api.php` | `action=query&list=categorymembers&cmtitle=Category:Bridges_in_Paris&cmnamespace=6` |
| Get EXIF/camera data | Action API (`prop=imageinfo`) with `iiprop=metadata` | `https://commons.wikimedia.org/w/api.php` | `action=query&prop=imageinfo&titles=File:Example.jpg&iiprop=metadata` |
| Upload a single file | Action API (`action=upload`) | `https://commons.wikimedia.org/w/api.php` | Requires authentication + bot password. See [Uploading to Commons](#uploading-to-commons). |
| Check licensing | Action API (`prop=imageinfo`) with `iiprop=extmetadata` | `https://commons.wikimedia.org/w/api.php` | Parse `extmetadata.Credit.value` and `extmetadata.LicenseShortName.value` for license info |
| **Browser app: display image** | Use `Special:FilePath/` URL | `https://commons.wikimedia.org/wiki/Special:FilePath/Example.jpg?width=800` | CORS-friendly redirect; works for `<img>` tags |
| **Browser app: Canvas/WebGL** | Proxy through your server | Your server fetches from Commons, serves locally | See **[CORS Considerations](#browser-applications-cors-considerations)** section |

> ⚠️ **All API calls require a descriptive `User-Agent` header.** See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill.

---

## **Searching Commons**

Commons has **two distinct search interfaces**, each with different strengths. Choose based on your task.

### **1. MediaSearch** — `https://commons.wikimedia.org/wiki/Special:MediaSearch`

The newer, **media-first** search interface, powered by a dedicated search index optimized for finding reusable media files.

🎯 **Best for:** Finding images, audio, or video files for reuse. Results are displayed as a visual grid with thumbnails and file-type badges. The interface is designed for quick visual browsing — scanning many results at a glance to find the right file.

**Characteristics:**
- Returns primarily **files** (not category pages, galleries, or user pages)
- Visual grid layout with large thumbnails
- Fast, approximate matching (semantic search)
- Built-in license filters (e.g., "Creative Commons only")
- File-type facet filters (image, video, audio, document, 3D)
- Ideal when you know roughly what you're looking for and want to browse

**Example task:** "Find a freely licensed photo of the Eiffel Tower at sunset."

### **2. Traditional Search (Special:Search)** — `https://commons.wikimedia.org/wiki/Special:Search`

The older, **full-text** search interface, based on the same CirrusSearch engine used by Wikipedia. It searches all page text on Commons — file descriptions, category pages, galleries, user pages, help pages, and templates.

🎯 **Best for:** Finding specific files by metadata, navigating Commons's complex category structure, locating maintenance templates, or searching within file descriptions and captions.

**Characteristics:**
- Searches the full text of all Commons pages (not just file metadata)
- Returns a mix of files, categories, galleries, and help pages
- Supports advanced CirrusSearch syntax (intitle, incategory, prefix, filetype, etc.)
- More precise for structured queries with multiple filters
- Integrates with Commons's extensive category tree (e.g., `incategory:"Bridges_in_Paris"`)
- Supports `haswbstatement:` for querying **Wikibase structured data** statements — a powerful way to filter files by their semantic annotations without writing SPARQL (see below)

**Example task:** "Find all PDF documents uploaded by User:Example in the 'Historical Documents' category from before 2020."

#### Structured Data Search via `haswbstatement:`

Commons files carry structured data statements (Wikibase annotations) that describe what a file depicts, who created it, when it was created, and more. These statements can be queried directly in the search box using the `haswbstatement:` prefix, providing a quick alternative to writing a full SPARQL query.

**Syntax:** `haswbstatement:<property>=<value>`

> 💡 **Works in both search interfaces.** While this section appears under Special:Search (CirrusSearch), `haswbstatement:` also works in the MediaSearch search box — just enter it directly. The key difference is that CirrusSearch supports advanced combinations with `intitle:`, `incategory:`, and other prefixes, while MediaSearch treats it as a plain search term alongside its semantic matching.

where  `<property>` is a Wikidata property ID (e.g., `P180` for "depicts", `P170` for "creator", `P571` for "inception") and `<value>` is a Wikidata item ID (e.g., `Q5` for "human", `Q30` for "United States").

**Examples:**

| Query | What It Finds |
|-------|---------------|
| `haswbstatement:P180=Q5` | All files that have the structured data statement "depicts → human" |
| `haswbstatement:P180=Q30` | All files that "depict → United States" |
| `haswbstatement:P170=Q42` | All files whose "creator → [some artist/item Q42]" |
| `haswbstatement:P180=Q5 Eiffel Tower` | All files depicting a human **and** matching the text "Eiffel Tower" |
| `haswbstatement:P180=Q5 -haswbstatement:P180=Q115` | All files depicting a human **but not** depicting a beard (`Q115`) |

**Why use this instead of SPARQL?**

- **Instant results** — `haswbstatement:` is backed by a search index, so results appear as fast as a text search (sub-second). SPARQL queries against the Wikidata Query Service can take multiple seconds.
- **No external service** — The query runs against Commons's own search index, not the Wikidata SPARQL endpoint. No need for a separate connection or query language.
- **Composable** — Combine `haswbstatement:` with regular text, `incategory:`, `filetype:`, and exclusion (`-haswbstatement:...`) in a single search box query.
- **Limitation:** `haswbstatement:` only supports **exact equality** on single values. For numerical comparisons, date ranges, or aggregations, you still need [SPARQL](https://query.wikidata.org) (see the `wikimedia-api-access` skill).

> 💡 **Try it now:** Open [Special:Search on Commons](https://commons.wikimedia.org/wiki/Special:Search?search=haswbstatement:P180=Q5) to see all files that have a "depicts → human" structured data statement.

### **Quick Comparison**

| Aspect | MediaSearch | Special:Search |
|--------|-------------|---------------|
| Search scope | File metadata + captions | Full page text (categories, galleries, templates, etc.) |
| Layout | Visual grid | Text results list |
| Best for | Browsing, finding reusable media | Precise queries, category navigation, advanced filters |
| Advanced syntax | Limited | Full CirrusSearch (intitle, incategory, filetype, haswbstatement, etc.) |
| Structured data search | Supported via `haswbstatement:` in search box (though without dedicated UI facets) | `haswbstatement:P180=Q5` — query Wikibase statements directly |
| License filters | Built-in UI | Via search syntax or advanced parameters |

### **3. Programmatic APIs (Action API & REST API)**

Beyond the web interfaces, Commons can be searched and queried programmatically via the same MediaWiki APIs used by Wikipedia. These are covered in depth by the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill, which covers User-Agent requirements, rate limiting, and error handling.

- **Action API** (`https://commons.wikimedia.org/w/api.php`) — Search files, fetch metadata (license, author, EXIF, categories), and get file usage data across all wikis. Use `srnamespace=6` to limit results to the `File:` namespace. The `haswbstatement:` search prefix works here too — just include it in the `srsearch` parameter value.
- **REST API** (`https://commons.wikimedia.org/api/rest_v1/`) — Retrieve file metadata in JSON format, generate thumbnails at specific widths, and download PDF files.
- **MediaSearch backend** — The Action API also supports `srbackend=MediaSearch` to use the newer search engine programmatically.

> 💡 **When to reach for the API skill:** Any time you need to write code that interacts with Commons — whether for metadata extraction, batch analysis, or automated uploads — first load the `wikimedia-api-access` skill for the mandatory User-Agent pattern, retry logic, and rate-limiting guardrails.

---

## **Navigating Commons**

### **Categories vs. Galleries**

Commons organizes files using two overlapping but distinct systems:

**🏷️ Categories** — The primary organizational system, based on the same MediaWiki category engine used by Wikipedia. Categories form a hierarchical tree (e.g., `Eiffel Tower` → `Towers in Paris` → `Buildings in Paris`). A file can belong to multiple categories. Categories are machine-readable and essential for API queries and structured navigation.

- Used by the API (`prop=categories`), CirrusSearch (`incategory:`), and the category tree widget.
- Automatically populated — files show up in a category when editors add `[[Category:Name]]` to the file description page.
- **Best for:** Systematic browsing, API-driven discovery, and finding all files in a topic area.

**🖼️ Galleries** — Hand-curated, wiki-style pages that present selected files in a layout. Galleries are essentially ordinary wikitext pages (in the `Gallery:` namespace) that editors write by hand, selecting and arranging specific files for presentation.

- Manually maintained — editors choose the layout, captions, and ordering of each file displayed.
- **Best for:** Curated showcases — "Best of" collections, thematic exhibitions, or guided tours through a topic.
- Not easily queried via the API since they are free-form wikitext.

**How to choose:** Use **categories** for exploration and API work. Use **galleries** when you want to see how human editors have curated and presented a selection of files on a topic.

---

## **Commons Namespaces**

Like all MediaWiki sites, Commons organizes pages into **namespaces** — numbered buckets that distinguish different types of content. When searching via the [`--ns` flag in the search tool](scripts/commons-search.sh) or via the Action API (`srnamespace`), knowing the namespace IDs lets you target exactly what you need.

| Namespace ID | Name | What Lives There | Example |
|:---:|---|----|----|
| `0` | **Main** (Gallery) | Curated gallery pages — hand-written wikitext pages that present selected files on a topic. This is **not** the default for file uploads; it's for editorial pages. | `Toronto` |
| `2` | **User** | Personal user pages and sandboxes. | `User:Jimbo Wales` |
| `4` | **Commons** | Project namespace — policies, guidelines, community discussions (named `Commons:` on this wiki). | `Commons:Volunteer_Response_Team` |
| `6` | **File** | Media files themselves — the **default** namespace for most Commons work. Every uploaded image, video, audio file, PDF, and 3D model lives here. | `File:Eiffel_Tower_from_below.jpg` |
| `10` | **Template** | Reusable wiki templates (information boxes, license tags, maintenance notices). | `Template:CC-BY-SA-4.0` |
| `12` | **Help** | Help pages explaining how to use Commons. | `Help:Contents` |
| `14` | **Category** | Category pages — the hierarchical classification system for organizing files and other pages. | `Category:Eiffel_Tower` |
| `100` | **Creator** | Creator pages — copyright/author metadata about photographers, artists, and other creators. Unique to Commons. | `Creator:Leonardo_da_Vinci` |
| `102` | **TimedText** | Subtitles and closed captions for video files. | `TimedText:Video.webm.en.srt` |
| `106` | **JSON Schema** | Structured data JSON schemas for Commons file annotations. | — |

### **Quick Rules of Thumb**

- **Files are always in namespace 6.** If you're looking for media you can use or download, search namespace 6.
- **Categories are always in namespace 14.** Use `incategory:"CategoryName"` or `srnamespace=14` to find category pages.
- **Don't confuse namespace 0 (Galleries) with Wikipedia articles.** On Commons, namespace 0 is not encyclopedia articles — it's curated gallery pages that editors build by hand.
- **The `--ns` flag** in the search tool (`srnamespace` in the API) accepts a single ID or comma-separated list: `--ns 6` (files only), `--ns 0,6` (galleries + files), `--ns 14` (categories only).

---

## **Licensing on Commons**

All files on Wikimedia Commons must be **freely licensed** or in the **public domain**. This is a strict, non-negotiable requirement. Content that does not meet this standard is deleted by the community.

### **The Three Pillars of Free Licensing**

For a license to be acceptable on Commons, it must allow **anyone** to:

1. **Use** the work for any purpose (including commercial)
2. **Study** the work and apply the information
3. **Redistribute** copies of the work
4. **Make and redistribute derivative works** (modified versions)

### **Most Common Free Licenses**

| License | Abbrev. | What It Allows | Attribution Required |
|---------|---------|---------------|:---:|
| **Creative Commons Zero** | CC0 | Waives all copyright; public domain equivalent. Does not require attribution, though it is good practice. | No |
| **Creative Commons Attribution** | CC BY | Free use, modification, and commercial distribution — as long as credit is given to the creator. | Yes |
| **Creative Commons Attribution-ShareAlike** | CC BY-SA | Same as CC BY, but derivative works must be released under the same (or compatible) license. Wikipedia uses CC BY-SA 4.0. | Yes |

### **Licenses That Are NOT Acceptable**

Despite their names, the following Creative Commons licenses **are not considered free enough** for Commons because they restrict commercial use:

- **CC BY-NC** (NonCommercial) — Prohibits commercial use
- **CC BY-NC-SA** (NonCommercial-ShareAlike) — Prohibits commercial use
- **CC BY-NC-ND** (NonCommercial-NoDerivatives) — Prohibits both commercial use and derivative works
- **CC BY-ND** (NoDerivatives) — Prohibits derivative works

> ⚠️ **Common misconception:** "NonCommercial" sounds harmless, but it is fundamentally incompatible with Commons policy. Even if a creator explicitly grants permission for Commons to host their NC-licensed work, the license itself restricts downstream reusers from using it commercially — and Commons only hosts content that is free for **any** use.

### **Other Acceptable Licenses**

- **Public Domain** (various tags: {{PD-old}}, {{PD-US}}, {{PD-self}}, etc.)
- **GFDL** (GNU Free Documentation License)
- **Free Art License** (FAL)
- Various government/specific free licenses (e.g., NASA images, US federal government works)

### **Copyrighted Material — Strict Prohibition**

- **Do not upload copyrighted material** unless the copyright holder has explicitly released it under an acceptable free license.
- **Fair use does not apply on Commons.** Unlike English Wikipedia, Commons does not accept any content under fair use / fair dealing claims. All content must be free in the copyright sense.
- **Screenshots** of copyrighted software, websites, or video games may be acceptable only if they depict solely freely licensed elements. Most screenshots are not acceptable.
- **Logos** are generally not acceptable unless they are simple enough (e.g., text only) to fall below the threshold of originality.

---

## **Uploading to Commons**

To upload files to Commons, you need a registered user account and an understanding of the licensing rules above (all uploads must be freely licensed or public domain).

### **Allowed Formats (with caveats)**

See the [File Types Accepted](#file-types-accepted) table above for the full list. A few important notes:

✅ **Allowed:** JPEG, PNG, GIF, SVG, TIFF, WebP, AVIF, MP3, OGG, FLAC, WAV, WebM, OGV, STL, PDF, DjVu

### **Explicitly Disallowed Formats**

Some formats are blocked from upload because of patent encumbrances, poor compression, or lack of free tools:

- ❌ **MP4 / H.264 / H.265** — Blocked due to software patent concerns. Convert to WebM (VP9/AV1) or OGV (Theora) before uploading.
- ❌ **MPEG, AVI, MOV, WMV, FLV** — These container formats are not accepted.
- ❌ **MP2, AAC** — Audio formats with similar patent issues.
- ❌ **EXE, ZIP, RAR** — Executables and archives are not permitted.
- ❌ **DRM-protected files** — Any file with digital rights management is prohibited regardless of format.

> ⚠️ **Conversion tip:** Use `ffmpeg` to convert video to WebM: `ffmpeg -i input.mp4 -c:v libvpx-vp9 -c:a libopus output.webm`. Audio can be converted to OGG (Vorbis/Opus) or FLAC.

### **Upload Methods**

**🖱️ Upload Wizard (web-based)** — The default upload interface at `https://commons.wikimedia.org/wiki/Special:UploadWizard`. Best for small numbers of files (1–10) with step-by-step guidance on license selection, description, and categorization.

**📦 Bulk Upload Tools** — For larger batches or automated workflows:

| Tool | Purpose | Best For |
|------|---------|----------|
| **[Pattypan](https://commons.wikimedia.org/wiki/Commons:Pattypan)** | Spreadsheet-based bulk uploader | Uploading many files with structured metadata from a `.xlsx` template; supports custom categories, descriptions, and licenses per row |
| **[flickr2commons](https://commons.wikimedia.org/wiki/Commons:Flickr2Commons)** | Imports from Flickr | Transferring freely licensed (CC BY, CC BY-SA, CC0, PD) photos from Flickr to Commons with attribution preserved |
| **[url2commons](https://commons.wikimedia.org/wiki/Commons:Url2Commons)** | Uploads from a list of URLs | Supply a list of direct image URLs and upload them in batch; useful for migration from other open repositories |
| **[video2commons](https://commons.wikimedia.org/wiki/Commons:Video2Commons)** | Uploads/converts video | Handles transcoding (e.g., MP4 → WebM) during upload; ideal for migrating video from YouTube or other sources under free licenses |
| **[Commonist](https://commons.wikimedia.org/wiki/Commons:Commonist)** | Desktop bulk uploader (Java) | Legacy tool for batch uploads with a GUI; lighter than Pattypan for simple batches |

### **Upload Checklist**

Before uploading, verify:

1. ✅ The file is **your own original work**, OR the copyright holder has explicitly released it under an acceptable free license (CC0, CC BY, CC BY-SA, or PD-equivalent).
2. ✅ The file is **educational** — it serves a realistic educational purpose, not just personal or decorative use.
3. ✅ The file is in an **allowed format** (convert MP4/H.264 to WebM if needed).
4. ✅ The file has a **meaningful name** (not `IMG_1234.jpg`).
5. ✅ You have identified the correct **categories** for discoverability.

### **Volunteer Response Team (VRT) — Verifying Permissions**

If you are uploading a file that comes from a source where the license cannot be independently verified online — such as a personal website, email correspondence, or a non-Flickr source where the copyright holder's identity isn't public — you (or the copyright holder) must go through the **[Volunteer Response Team (VRT)](https://commons.wikimedia.org/wiki/Commons:Volunteer_Response_Team)** process.

VRT (formerly known as OTRS) is a team of trusted volunteers who handle permission emails and confirm that the copyright holder has genuinely released their work under a free license.

**How it works:**

1. The copyright holder sends an email to `permissions-commons@wikimedia.org` (or uses the [online release generator](https://wmf.legal-yes.com/#/)) explicitly stating that they release the work under an acceptable free license.
2. The email must come from a verifiable address connected to the copyright holder (e.g., the domain of the website where the work is published, or a known email of the creator).
3. A VRT volunteer reviews the email, and if everything checks out, a **VRT ticket number** is added to the file's description page via the `{{PermissionTicket|id=...}}` template.
4. Until the ticket is confirmed, the file may be flagged for deletion. Once confirmed, it is protected against deletion on copyright grounds.

**When VRT is needed:**

| Scenario | VRT Required? |
|----------|:---:|
| File is your own original work, uploaded by you | ❌ No (your account is the verification) |
| File from Flickr under a clear CC/PD mark | ❌ No (Flickr license is publicly visible) |
| File from a personal website with no license info | ✅ **Yes** |
| File from a publication where you contacted the author who agreed by email | ✅ **Yes** |
| File posted on social media, repurposed with permission | ✅ **Yes** |
| File whose author is unknown or unverifiable | ⛔ **Cannot be uploaded** — VRT cannot help without a clearly identified copyright holder |

> 💡 **Tip:** When reaching out to a copyright holder to request a free license, point them to the [VRT release generator](https://wmf.legal-yes.com/#/) which walks them through the process in plain language.

---

## **Browser Applications: CORS Considerations**

When building **browser-based tools** that display or process Commons media, you may encounter CORS (Cross-Origin Resource Sharing) restrictions. This is a common gotcha for developers new to Commons.

### The Issue

Media files served from `upload.wikimedia.org` **do not include CORS headers**. This is intentional — it prevents third-party sites from reading pixel data or using files in certain browser contexts.

```
# This works fine in server-side code:
resp = requests.get('https://upload.wikimedia.org/wikipedia/commons/a/ab/Example.jpg')

# But in browser JavaScript, this may fail:
const img = new Image();
img.src = 'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/800px-Example.jpg';
// Works for display, but Canvas/WebGL access is blocked
```

### What Works, What Doesn't

| Use Case | Direct URL from `upload.wikimedia.org` |
|----------|:------------------------------------:|
| Server-side download (Python, Node.js) | ✅ Works |
| Display in `<img>` tag | ✅ Works |
| CSS `background-image` | ⚠️ May fail in some browsers |
| Canvas pixel access (`getImageData`) | ❌ Blocked (tainted canvas) |
| WebGL textures | ❌ Blocked |
| Audio/video processing | ⚠️ Limited |

### Solutions

**1. For simple display:** Use the file page redirect URL, which includes CORS headers:

```javascript
// Instead of:
// https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Example.jpg/800px-Example.jpg

// Use:
const displayUrl = 'https://commons.wikimedia.org/wiki/Special:FilePath/Example.jpg?width=800';
```

**2. For Canvas/WebGL/processing:** Proxy through your server:

```javascript
// Browser requests from your origin
const proxiedUrl = '/api/media?url=https://upload.wikimedia.org/...';

// Your server fetches from Commons and caches locally
// Browser sees same-origin response → no CORS restrictions
```

### Quick Decision Guide

```
Are you building a browser app?
├── NO (server-side) → Fetch directly, no CORS issues
└── YES
    └── Just displaying images (<img>)?
        ├── YES → Direct URL works, or use Special:FilePath
        └── NO (Canvas, WebGL, processing)?
            └── Proxy through your server
```

> 📖 **Full details:** See **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** Section 10 for in-depth CORS handling, code examples, and the proxy pattern used by production tools.

---

## **Tooling**

### Skills in This Family

| Skill | Purpose |
|-------|--------|
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** *(this skill)* | Generic Commons — search, upload, licensing, categories, namespaces |
| **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** | Thumbnail generation, thumb URL scheme, `iiurlwidth`, `thumbmime` |
| **[wikimedia-commons-svg](../wikimedia-commons-svg/SKILL.md)** | SVG files — editing, validation, optimization, versioning |
| **[wikimedia-commons-pdf](../wikimedia-commons-pdf/SKILL.md)** | PDF/DjVu documents — page selection, Wikisource integration, OCR |
| **[wikimedia-commons-audio-video](../wikimedia-commons-audio-video/SKILL.md)** | Audio/video — format policy, transcoding, TimedText, player |
| **[wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md)** | Structured Data on Commons — captions, depicts, copyright, batch editing |
| **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** | Commons SPARQL — MediaInfo entities, QLever, federated queries |

### Scripts and Assets

This skill includes helper scripts and reference docs:

#### 🔧 Quick Search Demo (`scripts/commons-search.sh`)

Demonstrates searching Commons via the MediaSearch API and the Action API (traditional search).

```bash
./scripts/commons-search.sh "Eiffel Tower"
./scripts/commons-search.sh --media "Mona Lisa"
```

#### 📚 Commons API Reference (`references/commons-api.md`)

Deep reference for the Commons-specific API endpoints:
- `https://commons.wikimedia.org/w/api.php` — Action API for Commons (upload, search, file info, categories)
- `https://commons.wikimedia.org/api/rest_v1/` — REST API endpoints (file metadata, image scaling)
- MediaSearch API (`Special:MediaSearch` underlying endpoint)
- File metadata extraction patterns (EXIF, categories, usage across wikis)

#### 🐍 Commons File Inspector (`assets/commons-file-inspector.py`)

A Python tool to inspect a Commons file's metadata — license, author, categories, usage, and EXIF data — using the Action and REST APIs.
