# Wikimedia CDN Mirror Guide

## Overview

Wikimedia operates a privacy-preserving mirror of the cdnjs library repository
at `tools-static.wmflabs.org/cdnjs/ajax/libs/`. This allows Toolforge-hosted
tools to load common JavaScript/CSS libraries without sending user data to
third-party CDNs.

---

## Base URL

```
https://tools-static.wmflabs.org/cdnjs/ajax/libs/<library>/<version>/<file>
```

**This is the only confirmed working endpoint.** Other hostnames
(`cdnjs.toolforge.org`, `cdn.toolforge.org`) are unreliable.

---

## Finding Libraries

### Method 1: API Search (recommended)

```bash
curl "https://api.cdnjs.com/libraries?search=d3&fields=version,latest"
```

Response:
```json
{
  "name": "d3",
  "latest": "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js",
  "version": "7.9.0"
}
```

Construct the mirror URL by replacing `cdnjs.cloudflare.com/ajax/libs` with
`tools-static.wmflabs.org/cdnjs/ajax/libs`.

### Method 2: Browse Full Index

Browse `https://cdnjs.toolforge.org/` for the complete list (5MB+).

### Method 3: Use the helper script

```bash
./scripts/list-available.sh d3
./scripts/list-available.sh chart 5
```

---

## Verified Working Libraries

These have been tested and confirmed available on the mirror:

| Library | Example URL |
|---|---|
| jQuery 3.6.0 | `/cdnjs/ajax/libs/jquery/3.6.0/jquery.min.js` |
| jQuery 3.7.1 | `/cdnjs/ajax/libs/jquery/3.7.1/jquery.min.js` |
| D3 7.9.0 | `/cdnjs/ajax/libs/d3/7.9.0/d3.min.js` |
| Bootstrap 5.3.0 | `/cdnjs/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css` |
| Chart.js 4.5.0 | `/cdnjs/ajax/libs/Chart.js/4.5.0/chart.min.js` |
| Mermaid 11.12.0 | `/cdnjs/ajax/libs/mermaid/11.12.0/mermaid.min.js` |

Check availability before use:

```bash
./scripts/check-cdn.sh https://tools-static.wmflabs.org/cdnjs/ajax/libs/library/version/file
```

---

## Complete URL Examples

```html
<!-- JavaScript -->
<script src="https://tools-static.wmflabs.org/cdnjs/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
<script src="https://tools-static.wmflabs.org/cdnjs/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script src="https://tools-static.wmflabs.org/cdnjs/ajax/libs/Chart.js/4.5.0/chart.min.js"></script>
<script src="https://tools-static.wmflabs.org/cdnjs/ajax/libs/mermaid/11.12.0/mermaid.min.js"></script>
<script src="https://tools-static.wmflabs.org/cdnjs/ajax/libs/lodash.js/4.17.21/lodash.min.js"></script>
<script src="https://tools-static.wmflabs.org/cdnjs/ajax/libs/moment.js/2.29.4/moment.min.js"></script>

<!-- CSS -->
<link rel="stylesheet" href="https://tools-static.wmflabs.org/cdnjs/ajax/libs/twitter-bootstrap/5.3.0/css/bootstrap.min.css">
<link rel="stylesheet" href="https://tools-static.wmflabs.org/cdnjs/ajax/libs/font-awesome/6.5.1/css/all.min.css">
```

---

## Guardrails

| Do | Don't |
|---|---|
| Use `tools-static.wmflabs.org/cdnjs/ajax/libs/` | Use `cdnjs.cloudflare.com`, `cdnjs.com`, `unpkg.com`, `jsdelivr.net` |
| Specify exact version numbers | Use `latest` or version-agnostic URLs |
| Verify availability before deploying | Assume a library is mirrored |
| Prefer mirror for Toolforge apps | Load from external CDNs for Toolforge users |
| Use the API to search for libraries | Scrape the 5MB+ HTML index page |

## Policy

See: https://wikitech.wikimedia.org/wiki/Help:Toolforge/Web

> "Toolforge maintainers should use the local copies of libraries at
> `tools-static.wmflabs.org/cdnjs/ajax/libs/` instead of loading from
> external CDNs."

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| 404 on verified library | Case-sensitive path | Check exact capitalization (e.g., `Chart.js` not `chart.js`) |
| 404 on library search | Wrong library name | Try alternative names (e.g., `twitter-bootstrap` for Bootstrap) |
| 404 on version | Version not mirrored | Try a nearby version or the latest |
| Library not available | Not in cdnjs mirror | Use as last resort from official CDN with disclosure |
