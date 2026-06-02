---
name: wikimedia-cdn-assets
description: Load JavaScript, CSS, and fonts for Toolforge tools from Wikimedia's privacy-preserving cdnjs mirror, ensuring user privacy and policy compliance
license: MIT
compatibility: all
---

## SOP: Load Web Assets from Wikimedia's CDN

This skill provides guidelines for agents to load common web assets (JavaScript libraries, CSS stylesheets, fonts) from Wikimedia's internal cdnjs mirror. This practice is crucial for maintaining user privacy and adhering to Wikimedia's policies by avoiding external, third-party CDNs that may track users.

### 1. Rationale: Privacy and Policy Compliance

*   **User Privacy:** Wikimedia's stance is to protect user privacy. Loading assets from external, third-party CDNs (like the public cdnjs.com, unpkg.com, or Google Fonts) can introduce privacy risks. These external services may log IP addresses, track usage patterns, or inject their own tracking cookies, even if the primary asset is benign.
*   **Toolforge Web Hosting Policy:** The `Help:Toolforge/Web` page on wikitech.wikimedia.org mandates the use of internal Wikimedia CDN services for hosted web applications. This ensures that asset delivery aligns with Wikimedia's privacy commitments.
*   **Performance & Reliability:** While external CDNs can be fast, using the internal one keeps traffic within Wikimedia's infrastructure, potentially reducing latency for users accessing Wikimedia projects and ensuring a consistent experience.

**Key Principle:** Always prioritize the Toolforge cdnjs mirror for loading common web assets when building tools hosted on Toolforge or interacting with Wikimedia services.

### 2. CDN Mirror URLs

There are two possible hostnames for the CDN mirror, both using the same path structure:

| Hostname | Works | Notes |
|----------|-------|-------|
| `tools-static.wmflabs.org/cdnjs/ajax/libs` | Yes | The only confirmed working endpoint |
| `cdn.toolforge.org/ajax/libs` | Partial | May not have all libraries cached |
| `cdnjs.toolforge.org` | No | Returns 404 for all libraries |

**Only `tools-static.wmflabs.org/cdnjs/ajax/libs/...` has been confirmed to work.** The other hostnames (`cdnjs.toolforge.org`, `cdn.toolforge.org`) do not serve actual content — use `tools-static.wmflabs.org/cdnjs/` instead.

**General URL Structure:**

```
https://tools-static.wmflabs.org/cdnjs/ajax/libs/<library>/<version>/<file>
```

**Examples:**

```html
<script src="https://tools-static.wmflabs.org/cdnjs/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script src="https://tools-static.wmflabs.org/cdnjs/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<link rel="stylesheet" href="https://tools-static.wmflabs.org/cdnjs/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css">
```

### 3. How to Find the Correct Library and Version

The browseable index at `https://cdnjs.toolforge.org/` lists all available libraries but is very large (5MB+). Instead, use the cdnjs API to search for libraries and find the latest version:

**API Endpoint:**
```
https://api.cdnjs.com/libraries?search=<query>&fields=version,latest
```

**Example — find d3 version:**
```
https://api.cdnjs.com/libraries?search=d3&fields=version,latest
```

Response:
```json
{
  "name": "d3",
  "latest": "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js",
  "version": "7.9.0"
}
```

From the response, construct the Toolforge mirror URL by replacing `cdnjs.cloudflare.com/ajax/libs` with `tools-static.wmflabs.org/cdnjs/ajax/libs`:
```
https://tools-static.wmflabs.org/cdnjs/ajax/libs/d3/7.9.0/d3.min.js
```

**Example — search for a specific library:**
```
https://api.cdnjs.com/libraries?search=bootstrap&fields=version,latest
```

### 4. Guardrails and Best Practices

*   **DO NOT** use external, non-Wikimedia CDNs (e.g., `cdnjs.cloudflare.com`, `cdnjs.com`, `unpkg.com`, `jsdelivr.net`, `fonts.googleapis.com`, `fonts.gstatic.com`) for assets served to users of your Toolforge application.
*   **ALWAYS** specify an exact version number for the asset (e.g., `7.9.0` for d3). Avoid using `latest` or version-agnostic URLs, as this can lead to unexpected changes and breakages when libraries update.
*   **VERIFY** asset availability on the Toolforge mirror before incorporating it into a project. Use `webfetch` to check the URL returns a 200 status.
*   **IF** an asset is *absolutely essential* and not found on the Toolforge mirror, consider loading it from the official CDN (`d3js.org` for d3, `code.jquery.com` for jQuery, etc.) as a last resort. Better a minor privacy concern than a broken tool.
*   **CONSULT** `https://wikitech.wikimedia.org/wiki/Help:Toolforge/Web` for the most up-to-date policies and recommendations regarding web asset management on Toolforge.
*   **TO FIND** available libraries, the list at `https://cdnjs.toolforge.org/` is comprehensive but very large — prefer the API search (`api.cdnjs.com`) for targeted lookups.

---

## Tooling

This skill includes helper scripts, reference docs, and templates:

### 🔧 CDN Asset Checker (`scripts/check-cdn.sh`)

Verify that a library is available on the Wikimedia CDN mirror.

```bash
# Check by full URL
./scripts/check-cdn.sh "https://tools-static.wmflabs.org/cdnjs/ajax/libs/jquery/3.6.0/jquery.min.js"

# Search by library name (auto-detects latest version)
./scripts/check-cdn.sh d3

# Specify version and file explicitly
./scripts/check-cdn.sh twitter-bootstrap 5.3.0 css/bootstrap.min.css
```

Returns green (200), redirect warning, or red (404).

### 🔧 Library Search (`scripts/list-available.sh`)

Search for libraries available on the cdnjs mirror.

```bash
./scripts/list-available.sh chart 5
./scripts/list-available.sh jquery 3
```

Outputs library name, version, and CDN path in a formatted table.

### 📚 CDN Mirror Guide (`references/cdn-mirror-guide.md`)

Complete reference for the Wikimedia CDN mirror:
- Base URL and URL construction
- Verified working libraries with tested URLs
- Complete HTML examples for common libraries
- Guardrails table (do/don't)
- Troubleshooting guide for 404s and common issues

### 🧩 HTML Load Template (`assets/load-template.html`)

Ready-to-use HTML page that loads jQuery, Bootstrap, and Font Awesome
from the Wikimedia CDN mirror. Copy and customize for your Toolforge tool.

### 🧩 JavaScript Loader (`assets/load-template.js`)

Dynamic asset loader for programmatic use:

```javascript
// Load common libraries
loadCommonAssets().then(() => {
    // jQuery, Bootstrap, Font Awesome are ready
    $(document).ready(function() {
        console.log('All assets loaded from Wikimedia CDN');
    });
});

// Load specific libraries
loadCDNAssets({
    scripts: [['d3', '7.9.0', 'd3.min.js']],
    styles: [['twitter-bootstrap', '5.3.0', 'css/bootstrap.min.css']],
});

// Load a single script
loadCDNScript('jquery', '3.6.0', 'jquery.min.js')
    .then(() => console.log('jQuery loaded'))
    .catch(err => console.error('Failed:', err));
```
