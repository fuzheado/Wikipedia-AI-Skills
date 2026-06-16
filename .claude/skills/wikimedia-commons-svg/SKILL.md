---
name: wikimedia-commons-svg
description: Work with SVG files on Wikimedia Commons — viewing and retrieving raw SVG source vs PNG preview, W3C validation badges, creation tools (Inkscape, Illustrator), optimization (scour, SVGO), versioning and diffing SVG revisions, SVG-specific templates and categories, structured data for vector files, and animated SVG considerations
depends_on: [wikimedia-api-access, wikimedia-commons, wikimedia-commons-thumbnails, wikimedia-commons-sdc]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["SVG", "SVG file", "vector image", "vector graphics", "scalable vector graphics", "raw source", "viewBox"]
  - keywords: ["ValidSVG", "InvalidSVG", "SVG validation", "W3C validator", "SVG error"]
  - keywords: ["Inkscape", "scour", "svgo", "SVG optimization", "text-to-path", "font licensing", "SVG cleanup"]
  - keywords: ["animated SVG", "SVG flag", "SVG map", "SVG logo", "SVG category", "SVG diagram"]
  - keywords: ["SVG versioning", "SVG diff", "SVG edit", "re-upload SVG", "SVG upload"]
  - keywords: ["Commons SVG", "Wikimedia SVG", "Wikipedia SVG", "vector file Commons"]
last_verified: 2026-06-16
---

> ⚠️ **User-Agent required:** All curl and code examples in this skill access Wikimedia APIs. Requests without a descriptive `User-Agent` header will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

---

## 1. SVG on Commons: What's Different

SVG files on Commons behave differently from raster images in several important ways:

**No native raster resolution.** The `width` and `height` reported by the API are the SVG's **viewBox** dimensions, not a pixel grid. An SVG might report `width: 103, height: 94` (like the Wikipedia logo) but can be rendered cleanly at any size.

**Commons rasterizes SVGs to PNG.** When a thumbnail is requested, Commons converts the SVG source to a PNG bitmap. This means:

- The raw SVG source and the displayed preview are different files
- The `thumbmime` is `image/png`, not `image/svg+xml`
- Any requested width is valid — there's no native resolution cap

**The file page shows a PNG preview.** When you visit `File:Wikipedia-logo-v2.svg` on Commons, what you see in the browser is a rasterized PNG render, not the SVG itself rendered by your browser. Clicking "Download" gives you the raw SVG.

> 🔗 **Thumbnail mechanics:** See **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** (Section 4: Format Conversion Matrix) for how SVG→PNG rasterization works via `iiurlwidth` and the `thumbmime` field.

---

## 2. Viewing and Retrieving SVG Source

### Via the File Page

1. Navigate to `File:Foo.svg` on Commons
2. The page displays a PNG **preview** of the SVG
3. Below the preview, the "File information" section shows metadata (description, date, source, author, license)
4. The **download link** provides the raw `.svg` file

### Via the Action API — Raw Source URL

The API's `prop=imageinfo` with `iiprop=url` returns the raw SVG URL:

```python
import requests
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "url|mime",
    "titles": "File:Wikipedia-logo-v2.svg",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

info = resp.json()["query"]["pages"]["10337301"]["imageinfo"][0]
raw_svg_url = info["url"]  # → "https://upload.wikimedia.org/wikipedia/commons/8/80/Wikipedia-logo-v2.svg"
print(f"MIME: {info['mime']}")  # → "image/svg+xml"
```

### Via `action=raw` (Wikitext Source)

You can also retrieve the **wikitext description page** of the file (which contains the `{{Information}}` template and categories) using `action=raw`:

```
https://commons.wikimedia.org/w/index.php?title=File:Foo.svg&action=raw
```

> ⚠️ This returns the **file description wikitext**, NOT the SVG source. To get the SVG source, use the URL from `prop=imageinfo` → `url` (as above).

### Distinguishing the SVG from Its Preview

| URL | Returns | Use Case |
|-----|---------|----------|
| `upload.wikimedia.org/.../Foo.svg` | Raw SVG XML | Processing, editing, analysis |
| `.../thumb/.../Foo.svg/800px-Foo.svg.png` | Raster PNG | Display, embedding |
| `commons.wikimedia.org/wiki/File:Foo.svg` | HTML file page | Browsing metadata |
| `commons.wikimedia.org/w/index.php?title=File:Foo.svg&action=raw` | Wikitext description | Reading categories, templates |

---

## 3. SVG Validation on Commons

Commons runs submitted SVGs through the **W3C Markup Validation Service** to check for well-formed XML and valid SVG elements.

### Validation Badges

Valid SVGs display a badge on the file page:

| Badge | Template | Meaning |
|-------|----------|---------|
| ✅ Valid SVG | `{{ValidSVG}}` | Passed W3C validation |
| ❌ Invalid SVG | `{{InvalidSVG}}` | Failed validation |
| — (no badge) | — | Not yet validated |

### Checking Validation via the API

The validation status is **not directly exposed** as an API field. It's inferred from categories:

```python
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "categories",
    "titles": "File:Wikipedia-logo-v2.svg",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

pages = resp.json()["query"]["pages"]
categories = [cat["title"] for cat in next(iter(pages.values())).get("categories", [])]

is_valid = any("Valid SVG" in cat for cat in categories)
is_invalid = any("Invalid SVG" in cat for cat in categories)
print(f"Valid: {is_valid}, Invalid: {is_invalid}")
```

Common validation categories:
- `Category:Valid SVG` — the SVG passes W3C validation
- `Category:Valid SVG created with Inkscape` — validated + creator tool known
- `Category:Valid SVG created with Adobe Illustrator`
- `Category:SVG with errors` — has issues that may affect rendering

### Common SVG Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Unclosed tags | Missing `</path>`, `</g>`, etc. | Check XML well-formedness |
| Incorrect namespace | Missing `xmlns="http://www.w3.org/2000/svg"` | Add the SVG namespace |
| Invalid CSS | CSS within `<style>` that doesn't parse | Validate CSS separately |
| Non-standard elements | Browser-specific elements or proprietary Inkscape/Illustrator extensions | Use standard SVG elements only, or strip with `--export-plain-svg` |
| Embedded raster images | `<image href="data:image/png...">` inside SVG | Commons allows this but the embedded image may violate licensing |

---

## 4. SVG Creation and Editing Tools

### Common Creation Tools

| Tool | Template | Notes |
|------|----------|-------|
| **[Inkscape](https://inkscape.org)** | `{{Created with Inkscape}}` | Free, open-source. Most popular for Commons. Use `File → Save As → Plain SVG` to remove Inkscape-specific XML |
| **Adobe Illustrator** | `{{Created with Adobe Illustrator}}` | Proprietary. Export as plain SVG. May add illustrator-specific XML |
| **Text Editor** | `{{Created with Text Editor}}` | For hand-coded SVGs. Minimal, clean SVG |
| **[SVG-edit](https://github.com/SVG-Edit/svgedit)** | `{{Created with SVG-edit}}` | Browser-based, lightweight |
| **[Draw.io / diagrams.net](https://app.diagrams.net)** | `{{Created with draw.io}}` | For diagrams and flowcharts |

> 💡 **Always use "Plain SVG" or equivalent.** Inkscape adds Inkscape-specific namespace declarations and metadata (`inkscape:version`, `sodipodi:namedview`) that are unnecessary on Commons. Use `File → Save As → Plain SVG` (`inkscape --export-plain-svg`) to strip them.

### Converting from Other Formats

| Source | Method |
|--------|--------|
| PDF → SVG | `inkscape input.pdf --export-plain-svg=output.svg` |
| EPS → SVG | `inkscape input.eps --export-plain-svg=output.svg` |
| AI → SVG | Open in Illustrator → "Save As" → SVG |
| Image trace → SVG | Inkscape: `Path → Trace Bitmap`, or `potrace` CLI |

### Font Licensing: The Text-to-Path Decision

This is a recurring debate among SVG contributors:

| Approach | Pros | Cons |
|----------|------|------|
| **Embedded text** (`<text>`) | Editable, smaller file, searchable | Font must be freely licensed; may render differently on different systems |
| **Text-to-path** (`<path>`) | Renders identically everywhere; no font dependency | Not editable as text; larger file; not searchable |

**Commons policy:** If using embedded fonts, the font must itself be freely licensed (compatible with CC BY-SA). When in doubt, convert text to paths. Always keep an editable copy locally.

```bash
# Convert text to paths in Inkscape (CLI)
inkscape input.svg --export-text-to-path --export-plain-svg=output.svg
```

---

## 5. SVG Optimization

SVG files can balloon in size from verbose paths, high decimal precision, unused defs, and editor metadata. Optimization is encouraged on Commons.

### Tools

| Tool | Purpose | Example |
|------|---------|---------|
| **[scour](https://github.com/scour-project/scour)** | Python-based SVG cleaner | `scour -i input.svg -o output.svg --enable-viewboxing` |
| **[SVGO](https://github.com/svg/svgo)** | Node.js-based optimizer | `npx svgo input.svg -o output.svg` |
| Inkscape | Remove editor metadata | `inkscape --export-plain-svg --export-filename=output.svg input.svg` |

### What Optimization Does

- Reduces decimal precision: `M0.000000,5.000000` → `M0,5`
- Removes unused `<defs>`, gradients, masks
- Removes editor metadata (`inkscape:`, `sodipodi:`, `illustrator:` namespaces)
- Merges overlapping paths
- Collapses redundant groups
- Compresses path data

### Optimization Templates on Commons

Editors can mark optimization status on the file page:

| Template | Meaning |
|----------|---------|
| `{{SVG|optimized}}` | The SVG has been run through an optimizer (scour, SVGO) |
| `{{SVG|cleaned}}` | Editor-specific namespaces have been removed |
| `{{SVG|unoptimized}}` | The SVG uses raw output from the creation tool |

```bash
# Full optimization pipeline
scour -i raw.svg -o cleaned.svg --enable-viewboxing --strip-xml-prologue \
  --remove-titles --remove-descriptions --remove-metadata \
  --disable-escape-non-ascii --enable-id-stripping

# SVGO alternative
npx svgo --multipass raw.svg -o cleaned.svg
```

---

## 6. Versioning and Updating SVGs

### Uploading a New Version

Upload a new version of an existing SVG using the Action API:

```python
import requests

SESSION = requests.Session()
SESSION.auth = ("User@botname", "bot_password")
SESSION.headers.update({"User-Agent": "MyBot/1.0 (user@example.com)"})

# Step 1: Get CSRF token
token_resp = SESSION.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query", "meta": "tokens", "type": "csrf", "format": "json",
})
csrf_token = token_resp.json()["query"]["tokens"]["csrftoken"]

# Step 2: Upload the new SVG version
with open("improved-version.svg", "rb") as f:
    resp = SESSION.post("https://commons.wikimedia.org/w/api.php", data={
        "action": "upload",
        "filename": "Existing_File.svg",  # must match existing filename
        "comment": "Fixed overlapping paths, optimized with SVGO",
        "token": csrf_token,
        "format": "json",
    }, files={"file": f})

print(resp.json())
```

> ⚠️ **Authentication required.** See **[wikimedia-auth-oauth](../wikimedia-auth-oauth/SKILL.md)** for bot password setup.

### File History

All previous versions of an SVG are retained in the file history. You can access them via the "File history" section on the file page or via the API:

```python
resp = SESSION.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "url|timestamp|user|comment|size",
    "titles": "File:Foo.svg",
    "iiend": "2024-01-01T00:00:00Z",   # optional: end date
    "format": "json",
})
```

### Diffing SVG Versions

Since SVG is XML (text), you can diff versions using standard text comparison:

```python
import difflib

# Fetch two versions' raw SVG source
v1_url = "https://upload.wikimedia.org/wikipedia/commons/archive/8/80/20220101120000%21Foo.svg"
v2_url = "https://upload.wikimedia.org/wikipedia/commons/8/80/Foo.svg"

v1 = requests.get(v1_url, headers={"User-Agent": "MyBot/1.0"}).text
v2 = requests.get(v2_url, headers={"User-Agent": "MyBot/1.0"}).text

diff = difflib.unified_diff(v1.splitlines(), v2.splitlines(), lineterm="")
print("\n".join(diff))
```

> ⚠️ **Archive URL pattern:** Previous versions are stored at `https://upload.wikimedia.org/wikipedia/commons/archive/{hash_path}/{timestamp}!{filename}`. The timestamp format is `YYYYMMDDHHMMSS`.

### ⚠️ Cache Implications of Updating SVGs

When you update an SVG:

1. All existing thumbnail URLs remain **the same URL path**
2. The old thumbnails are **purged** from Varnish cache
3. New thumbnails are generated on first request (cold cache — may be slow for the first few requests)
4. Wikipedia articles using this SVG will reflect the updated version once their page cache refreshes

---

## 7. SVG-Specific Metadata and Categories

### Information Template for SVGs

The `{{Information}}` template on SVG file pages has the same fields as for raster files, but some are especially relevant:

| Field | SVG Relevance |
|-------|---------------|
| `Description` | What the SVG depicts, including its intended use (flag, map, logo, diagram) |
| `Date` | Date of creation, not date of upload |
| `Source` | How the SVG was created (traced from raster? generated from data? hand-coded?) |
| `Author` | Creator name (may differ from uploader) |
| `Other versions` | Links to related SVG files (e.g., localized versions, color variants) |

### SVG-Specific Templates

| Template | Purpose |
|----------|---------|
| `{{SVG}}` | Marks the file as an SVG; adds it to `Category:SVG files` |
| `{{ValidSVG}}` | Indicates the SVG passed W3C validation |
| `{{InvalidSVG}}` | Indicates the SVG failed validation |
| `{{Created with Inkscape}}` | + `Category:Valid SVG created with Inkscape` |
| `{{Created with Adobe Illustrator}}` | + `Category:Valid SVG created with Adobe Illustrator` |
| `{{Path text SVG}}` | The SVG uses paths for text (text-to-path) |
| `{{Uses SVG}}` | Places the SVG in `Category:Uses SVG` (for non-SVG pages that describe/reference SVG files) |

### Category Hierarchy for SVGs

The SVG category tree on Commons is extensive:

```
Category:SVG files
├── SVG files by topic
│   ├── SVG flags
│   ├── SVG maps
│   ├── SVG logos
│   ├── SVG coats of arms
│   └── SVG diagrams
├── SVG files by creation tool
│   ├── Valid SVG created with Inkscape
│   ├── Valid SVG created with Adobe Illustrator
│   └── ...
├── SVG files by validity
│   ├── Valid SVG
│   └── SVG with errors
├── SVG files by language
│   ├── SVG files in English
│   └── ...
├── SVG files with embedded text
├── SVG files converted to path
└── SVG files by size
    ├── Large SVG files
    └── Tiny SVG files
```

### The "High-resolution or SVG" Category

Commons uses the `Category:High-resolution or SVG` as a meta-category. Files here are either:
- Raster images above a certain pixel threshold, **or**
- SVG files (which are inherently resolution-independent)

This is relevant for search — you can find "high quality" files by including this category.

---

## 8. SVG and Structured Data (SDC)

SVG files use the same SDC system as raster files (see **[wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md)**), but some property usage patterns differ.

### Depicts (P180) for SVGs

SVGs often depict abstract, structured, or typographic subjects:

| Type | Common P180 Values |
|------|-------------------|
| Flag | `Q14660` (flag), specific country/city flag Q item |
| Map | `Q40087` (map), geographic region Q item |
| Logo | `Q179903` (logo), organization Q item |
| Diagram | Appropriate topic Q item |
| Emblem | `Q1642034` (coat of arms), specific entity Q item |
| Symbol | Appropriate concept Q item |

### Digital Representation of (P6243)

For SVGs that are direct digital surrogates of a specific work or item:

```python
# In the SDC editor (via wbcreateclaim):
# entity=M12345, property=P6243, value={"id":"Q179900"}
```

This is especially common for:
- Vectorized versions of famous logos
- SVG recreations of historical maps
- Digital versions of flags based on official specifications

### Instance of (P31) for SVG Types

| P31 Value | SVG Type | Example |
|-----------|----------|---------|
| `Q207694` | Flag | `File:Flag_of_France.svg` |
| `Q40087` | Map | `File:World_map.svg` |
| `Q179903` | Logo | `File:Wikipedia-logo-v2.svg` |
| `Q1642034` | Coat of arms | `File:Coat_of_arms_of_Germany.svg` |
| `Q8274129` | Vector image | Generic SVG (fallback) |

---

## 9. Animations and Special Formats

### Animated SVG on Commons

SVG supports animation via:
- **CSS animations** (`@keyframes`, `animation-*`)
- **SMIL** (Synchronized Multimedia Integration Language — `<animate>`, `<animateTransform>`, `<set>`)

Commons **does support** animated SVGs — they are not stripped on upload. However:

- Animated SVGs are still rasterized to a **static PNG** for the file page preview
- The animation plays only when the raw SVG is opened directly (in a compatible browser)
- Wikipedia articles typically display the static PNG preview, not the animation
- For animated content on articles, **GIF** or **APNG** are usually preferred because they work in all browsers automatically

### SVG vs APNG vs GIF

| Format | Animation | Quality | File Size | Browser Support |
|--------|-----------|---------|-----------|-----------------|
| Animated SVG | Native vector animation | Perfect at any scale | Small | Good, but disabled in Wikipedia article rendering |
| APNG | Frame-based | Lossless | Medium | Wide (replacing GIF) |
| GIF | Frame-based | 256 colors | Medium-Large | Universal |

**When to use each:**
- **Animated SVG**: For vector animations that benefit from scaling (spinners, icons, loading animations). Works best as a standalone file.
- **APNG**: For complex frame animations with millions of colors (screenshots, UI demos). Preferred over GIF on Commons.
- **GIF**: For simple frame animations with flat colors or when backward compatibility is essential.

### ⚠️ JavaScript in SVGs

SVGs may contain `<script>` elements, but **Commons strips JavaScript from uploaded SVG files**. If you upload an SVG with embedded JS, it will be removed by the upload pipeline. This is a security measure to prevent XSS in the wiki context.

If you need interactivity, consider:
- Using CSS animations (which are allowed) for visual effects
- Creating a separate interactive tool on Toolforge and linking to it from the file description

---

## Related Skills

| Skill | Relevance |
|-------|-----------|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent, rate limiting, error handling |
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | File search, categories, upload basics |
| **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** | SVG→PNG rasterization, thumb URL scheme, `thumbmime` |
| **[wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md)** | Structured data for SVG depicts, copyright, license |
| **[wikimedia-commons-sparql](../wikimedia-commons-sparql/SKILL.md)** | Query SVGs by file type, depicts, or dimensions via SPARQL |
| **[wikimedia-auth-oauth](../wikimedia-auth-oauth/SKILL.md)** | Authentication for uploading new SVG versions |
