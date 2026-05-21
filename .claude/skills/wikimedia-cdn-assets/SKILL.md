---
name: wikimedia-cdn-assets
description: Guides agents on loading JavaScript, CSS, and fonts from Wikimedia's privacy-preserving cdnjs.toolforge.org CDN to ensure user privacy and policy compliance.
license: MIT
compatibility: all
---

## SOP: Load Web Assets from Wikimedia's CDN

This skill provides guidelines for agents to load common web assets (JavaScript libraries, CSS stylesheets, fonts) from Wikimedia's internal CDN service, `cdnjs.toolforge.org`. This practice is crucial for maintaining user privacy and adhering to Wikimedia's policies by avoiding external, third-party CDNs that may track users.

### 1. Rationale: Privacy and Policy Compliance

*   **User Privacy:** Wikimedia's stance is to protect user privacy. Loading assets from external, third-party CDNs (like the public cdnjs.com, unpkg.com, or Google Fonts) can introduce privacy risks. These external services may log IP addresses, track usage patterns, or inject their own tracking cookies, even if the primary asset is benign.
*   **Toolforge Web Hosting Policy:** The `Help:Toolforge/Web` page on wikitech.wikimedia.org mandates the use of internal Wikimedia CDN services for hosted web applications. This ensures that asset delivery aligns with Wikimedia's privacy commitments.
*   **Performance & Reliability:** While external CDNs can be fast, using the internal one keeps traffic within Wikimedia's infrastructure, potentially reducing latency for users accessing Wikimedia projects and ensuring a consistent experience.

**Key Principle:** Always prioritize `cdnjs.toolforge.org` for loading common web assets when building tools hosted on Toolforge or interacting with Wikimedia services.

### 2. How to Find and Load Assets

The primary source for these assets is:
`https://cdnjs.toolforge.org/`

This service mirrors many popular libraries and frameworks available on the public cdnjs.com but serves them from Wikimedia's domain.

**General URL Structure:**
The URLs typically follow this pattern:

`https://cdnjs.toolforge.org/<library-name>/<version>/<file-type>/<file-name>`

**Examples:**

#### a. Loading JavaScript Libraries

To include a JavaScript library (e.g., jQuery, Bootstrap JS), use an HTML `<script>` tag.

**Example: Loading jQuery 3.6.0**

```html
<script src="https://cdnjs.toolforge.org/jquery/3.6.0/jquery.min.js"></script>
```

**Example: Loading Bootstrap 5.3.0 JavaScript**

```html
<script src="https://cdnjs.toolforge.org/twitter-bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
```

#### b. Loading CSS Stylesheets

To include a CSS stylesheet (e.g., Bootstrap CSS, custom stylesheets), use an HTML `<link>` tag in the `<head>` section of your HTML document.

**Example: Loading Bootstrap 5.3.0 CSS**

```html
<link rel="stylesheet" href="https://cdnjs.toolforge.org/twitter-bootstrap/5.3.0/css/bootstrap.min.css">
```

#### c. Loading Fonts

If a specific font is required and available on `cdnjs.toolforge.org`, it can be loaded via CSS.

**Example: Loading Google Fonts (via cdnjs.toolforge.org)**
If a font like "Open Sans" is available, you might load it via a CSS import or a `<link>` tag pointing to a Google Fonts stylesheet hosted on the Toolforge CDN.
*First, check `https://cdnjs.toolforge.org/` for font packages or CSS files that import fonts.*

```html
<!-- Assuming a font CSS is available -->
<link rel="stylesheet" href="https://cdnjs.toolforge.org/google-fonts/opensans/3.0.0/css/opensans.css">
```
*(Note: Verify the exact path and version for specific fonts on `cdnjs.toolforge.org`)*

### 3. Guardrails and Best Practices

*   **DO NOT** use external, non-Wikimedia CDNs (e.g., `cdnjs.com`, `unpkg.com`, `jsdelivr.net`, `fonts.googleapis.com`, `fonts.gstatic.com`) for assets served to users of your Toolforge application.
*   **ALWAYS** specify an exact version number for the asset (e.g., `3.6.0` for jQuery). Avoid using `latest` or version-agnostic URLs, as this can lead to unexpected changes and breakages when libraries update.
*   **VERIFY** asset availability on `https://cdnjs.toolforge.org/` before incorporating it into your project.
*   **IF** an asset is *absolutely essential* and not found on `cdnjs.toolforge.org`, consider bundling it locally within your tool's deployment. However, this should be a last resort and carefully considered for licensing and maintenance.
*   **CONSULT** `https://wikitech.wikimedia.org/wiki/Help:Toolforge/Web` for the most up-to-date policies and recommendations regarding web asset management on Toolforge.

By adhering to these guidelines, agents can ensure their applications are privacy-conscious and compliant with Wikimedia's hosting policies.
