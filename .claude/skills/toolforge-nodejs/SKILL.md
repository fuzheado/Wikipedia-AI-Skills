---
name: toolforge-nodejs
description: Deploy and manage Node.js web services on Wikimedia Toolforge Kubernetes — zero-dependency server patterns, webservice commands, PORT configuration, static file serving with caching headers, npm on NFS, environment variables, logging, and common pitfalls
license: MIT
compatibility: opencode
depends_on: [wikimedia-toolforge, wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["Toolforge Node", "Node.js", "Node webservice", "node22", "node18", "npm", "package.json"]
  - keywords: ["Toolforge port", "PORT env", "webservice port", "Toolforge Kubernetes", "web service"]
  - keywords: ["Toolforge static files", "express", "http server", "zero dependency", "built-in http"]
  - keywords: ["Cache-Control", "Varnish", "Toolforge proxy", "immutable cache", "static asset"]
  - keywords: ["Toolforge environment", "env vars", "secrets", "toolforge env", "config", "environment"]
  - keywords: ["Toolforge logs", "kubectl logs", "webservice logs", "debug", "tail logs", "toolforge debug"]
  - keywords: ["Node streaming", "buffer", "readFile", "createReadStream", "Pannellum", "XHR", "WebGL"]
  - keywords: ["Toolforge cron", "node job", "scheduled task", "cron node", "batch job"]
last_verified: 2026-06-20
---

> ⚠️ **Prerequisites:** This skill assumes you have a Toolforge account and can SSH in. See **[wikimedia-toolforge](../wikimedia-toolforge/SKILL.md)** for account setup, tool creation, and basic SSH configuration.

> 💡 **Zero dependencies by default:** Toolforge's NFS filesystem has slow metadata operations — `npm install` can take minutes. The patterns in this skill use **only Node.js built-in modules** by default, which means zero `npm install`, zero `package.json`, and instant deployment. Add dependencies only when you must.

> ⚠️ **Toolforge Rule #2 — Open Source License Required:** All code in the Tools
> project must be published under an [OSI-approved](https://opensource.org/licenses)
> open source license. Add a `LICENSE` file to your repository before deploying.
> The absence of a license means default copyright laws apply, which is counter to
> the principles of the Wikimedia movement. See the
> [full rules](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Rules).

---

## Quick Reference

| Goal | Command / Pattern |
|------|-------------------|
| Deploy a new Node.js service | See SOP 1 |
| Choose a runtime | `node22` (default), `node18` (legacy) — see SOP 1.1 |
| Start/restart a webservice | `become <tool> webservice --backend=kubernetes node22 start` |
| See logs | `become <tool> kubectl logs -f deployment/<tool>` |
| Set environment variables | `become <tool> toolforge env set NAME value` |
| Serve static files | Use `readFile()` with correct MIME types — see SOP 3 |
| Add npm dependencies | Use a `package.json` and `npm install` on the tool's NFS — see SOP 5 |
| Run a cron job | `become <tool> job schedule node22 --command 'node script.mjs' "0 * * * *"` |

---

## SOP 1: Bootstrap a Zero-Dependency Node.js Server

The fastest way to get a Node.js web service running on Toolforge — **no `npm install`, no `package.json`**, just a single `.mjs` file.

### 1.1 Choose a Runtime

Toolforge offers these Node.js runtime versions:

| Runtime | Kubernetes Image | Status |
|---------|-----------------|--------|
| `node22` | `docker-registry.tools.wmflabs.org/toolforge-node22-sssd-web:latest` | ✅ Current default (Node 22.x) |
| `node18` | `docker-registry.tools.wmflabs.org/toolforge-node18-sssd-web:latest` | ⚠️ Legacy (Node 18.x, available but not recommended for new tools) |

The runtime image includes the operating system, Node.js binary, and basic tools. Your code lives on NFS at `/data/project/<tool>/`.

### 1.2 Create the Tool (One Time)

```bash
# From your local machine
ssh <user>@login.toolforge.org toolforge tools create my-tool
```

### 1.3 Write Your Server

Create a single-file server that uses only Node.js built-in modules. The key detail: **Toolforge sets the `PORT` environment variable** — your server must bind to it.

```javascript
// server.mjs — Zero-dependency Node.js web service for Toolforge
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join, extname, resolve as pathResolve, sep as pathSep } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
const PORT = process.env.PORT || 8765;

// MIME types for static files
const MIME = {
    '.html': 'text/html; charset=utf-8',
    '.css':  'text/css; charset=utf-8',
    '.js':   'application/javascript; charset=utf-8',
    '.mjs':  'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.svg':  'image/svg+xml',
};

const server = createServer(async (req, res) => {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const pathname = url.pathname;

    // API routes
    if (pathname === '/api/hello' && req.method === 'GET') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ message: 'Hello from Toolforge!' }));
        return;
    }

    // Static files
    try {
        const filePath = join(__dirname, 'public', pathname === '/' ? 'index.html' : pathname);
        // Security: prevent directory traversal — resolve and verify containment
        // startsWith without trailing sep matches sibling dirs (e.g. my-tool2)
        const safeDir = __dirname + path.sep;
        const resolved = path.resolve(filePath);
        if (!resolved.startsWith(safeDir)) {
            res.writeHead(403); res.end('Forbidden');
            return;
        }
        const data = await readFile(filePath);
        const ext = extname(filePath);
        res.writeHead(200, {
            'Content-Type': MIME[ext] || 'application/octet-stream',
            'Content-Length': data.length,
            // One-week browser cache for static assets
            'Cache-Control': pathname.startsWith('/images/')
                ? 'public, max-age=604800, immutable'
                : 'public, max-age=3600',
        });
        res.end(data);
    } catch {
        res.writeHead(404, { 'Cache-Control': 'no-store' });
        res.end('Not found');
    }
});

server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

**Naming convention:** Use `.mjs` extension for ES module syntax. If you need `require()`, use `.cjs`. For mixed use, a `package.json` with `"type": "module"` makes `.js` files ES modules.

### 1.4 Deploy

```bash
# From your local machine
scp server.mjs <user>@login.toolforge.org:/data/project/my-tool/

# Create a public/ directory for static files
ssh <user>@login.toolforge.org "mkdir -p /data/project/my-tool/public"

# Copy your static files
scp index.html style.css <user>@login.toolforge.org:/data/project/my-tool/public/

# Start the webservice
ssh <user>@login.toolforge.org "become my-tool webservice --backend=kubernetes node22 start"
```

### 1.5 Verify

```bash
# Check status
ssh <user>@login.toolforge.org "become my-tool webservice --backend=kubernetes node22 status"

# View logs
ssh <user>@login.toolforge.org "become my-tool kubectl logs -f deployment/my-tool"

# Test via curl or browser
curl https://my-tool.toolforge.org/
curl https://my-tool.toolforge.org/api/hello
```

---

## SOP 2: The `PORT` Environment Variable

Toolforge's Kubernetes proxy routes incoming requests to your container. It **ignores** any port you specify in code and expects your server to listen on the port given by the `PORT` environment variable.

### Do This

```javascript
const PORT = process.env.PORT || 8765;  // 8765 is a safe local dev default
server.listen(PORT, () => console.log(`Listening on ${PORT}`));
```

### Don't Do This

```javascript
server.listen(3000);        // ❌ Toolforge proxy won't find it
server.listen(80);          // ❌ Not running as root
server.listen('8080');      // ❌ PORT is a number, not a string
```

### How It Works

```
Browser ─→ toolforge.org ─→ Kubernetes Ingress ─→ Pod:PORT
                                                      │
                                                process.env.PORT
                                               (e.g., "31245")
```

The `PORT` value is assigned per-pod and is **not predictable** — always read it from the environment.

---

## SOP 3: Static File Serving with Correct Caching

### Cache-Control Headers

Toolforge uses **Varnish** as an HTTP accelerator in front of Kubernetes. Setting proper cache headers is critical for performance:

| Asset Type | Recommendation | Effect |
|------------|---------------|--------|
| Images (panoramas, thumbnails) | `public, max-age=604800, immutable` | 1 week, never revalidates |
| JS/CSS (versioned) | `public, max-age=31536000, immutable` | 1 year, never revalidates |
| HTML pages | `public, max-age=3600` | 1 hour, revalidates |
| API responses | `no-cache` (or omit caching) | Always revalidates |
| Error pages (404, 500) | `no-store` | Never caches errors |

```javascript
function cacheHeaders(pathname) {
    if (pathname.startsWith('/images/')) {
        return 'public, max-age=604800, immutable';  // 1 week
    }
    if (pathname.match(/\.(js|css|mjs)$/)) {
        return 'public, max-age=31536000, immutable'; // 1 year
    }
    if (pathname.startsWith('/api/')) {
        return 'no-cache';  // API responses
    }
    return 'public, max-age=3600';  // HTML and everything else
}
```

### Why `immutable` Matters

The `immutable` directive tells the browser it never needs to revalidate the resource before its `max-age` expires. For panorama images that are cache-busted with `?v=` timestamps, this saves a round-trip on every page load. Without it, browsers send `If-Modified-Since`/`If-None-Match` headers even for cached assets.

### Never Cache Error Responses

```javascript
// ❌ Wrong — browser caches the 404 page forever
res.writeHead(404, { 'Cache-Control': 'public, max-age=604800' });
res.end('Not found');

// ✅ Correct — browser never caches error responses
res.writeHead(404, { 'Cache-Control': 'no-store' });
res.end('Not found');
```

### MIME Types Must Be Explicit

Node.js `http` module doesn't set MIME types automatically. Missing or wrong MIME types cause browsers to refuse to load resources:

```javascript
const MIME = {
    '.html': 'text/html; charset=utf-8',
    '.css':  'text/css; charset=utf-8',
    '.js':   'application/javascript; charset=utf-8',
    '.mjs':  'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.png':  'image/png',
    '.jpg':  'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.svg':  'image/svg+xml',
};

// Always set Content-Type and Content-Length
res.writeHead(200, {
    'Content-Type': MIME[ext] || 'application/octet-stream',
    'Content-Length': data.length,
});
```

---

## SOP 4: Serving Images for WebGL/Pannellum — Never Stream

Pannellum's 360° viewer loads panorama images via `XMLHttpRequest` and expects a **complete, buffered response**. Streaming responses (using `createReadStream().pipe(res)`) causes `net::ERR_FAILED 200 (OK)` — the browser sees HTTP 200 but can't read the response body as a Blob.

### ❌ Broken: Streaming

```javascript
// DO NOT USE — Pannellum fails with ERR_FAILED
if (stat.size > 1024 * 1024) {
    const { createReadStream } = await import('node:fs');
    createReadStream(filePath).pipe(res);
    return;
}
```

### ✅ Correct: Buffering

```javascript
// Always read the entire file into memory before responding
const data = await readFile(filePath);
res.writeHead(200, {
    'Content-Type': 'image/jpeg',
    'Content-Length': data.length,
    'Cache-Control': 'public, max-age=604800, immutable',
});
res.end(data);
```

**Why buffering is safe on Toolforge:** Your images are on the local NFS mount — reads are fast. The memory cost (a few MB per image) is negligible on Toolforge's Kubernetes pods with 2GB+ RAM limits.

### When Streaming IS Safe

| Use Case | Method | Why |
|----------|--------|-----|
| `<img>` tags | Streaming works | Browser handles streamed images natively |
| `fetch()` + `response.blob()` | Streaming works | Different internal path than XHR |
| Audio/video file serving | Streaming preferred | Media elements handle buffered seeking |
| Large file downloads | Streaming preferred | Lower memory footprint |

---

## SOP 5: Adding npm Dependencies

For most Wikimedia tools, the built-in `http` module is sufficient. When you need external packages:

### 5.1 Create `package.json`

```json
{
  "name": "my-tool",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "express": "^4.18.0"
  },
  "scripts": {
    "start": "node server.mjs",
    "dev": "node --watch server.mjs"
  }
}
```

The `"type": "module"` field makes all `.js` files use ES module syntax (`import`/`export`). Use `.cjs` extension for files that need CommonJS (`require`).

### 5.2 Install on Toolforge

NFS metadata operations are slow. A full `npm install` can take 2–5 minutes:

```bash
become my-tool npm install
```

### 5.3 Optimize Install Speed

- **Use `.npmrc` to avoid audit/lockfile overhead:**
  ```
  audit=false
  fund=false
  lockfile=false
  ```
- **Pin exact versions** in `package.json` to avoid resolution time on every deploy
- **Install locally, copy binary:** `npm pack` on your machine, upload the `.tgz`, extract on Toolforge
- **Cache `node_modules`** — don't delete it on every deploy. Only re-run `npm install` when dependencies change.

### 5.4 When to Use Dependencies vs. Built-In

| Need | Recommendation |
|------|---------------|
| Simple REST API | Built-in `http` module — zero dependencies |
| Static file server | Built-in `http` + `fs/promises` |
| JSON body parsing | Built-in `JSON.parse()` + streaming body collection |
| URL parsing | Built-in `URL` class |
| Routing (simple) | `if/else` on `url.pathname` |
| Routing (complex, 10+ routes) | `express` or `fastify` |
| SQLite database | `better-sqlite3` |
| WebSocket | `ws` package |
| Templating | Built-in template literals or `ejs` |

**Rule of thumb:** Start with zero dependencies. Add packages only when the built-in solution becomes unwieldy.

---

## SOP 6: Environment Variables and Secrets

### Setting Variables

```bash
# Set variables — these persist across restarts
become my-tool toolforge env set API_KEY "sk-abc123"
become my-tool toolforge env set NODE_ENV "production"
become my-tool toolforge env set LOG_LEVEL "info"

# List all variables
become my-tool toolforge env list

# Remove a variable
become my-tool toolforge env unset API_KEY
```

### Reading Variables in Code

```javascript
const apiKey = process.env.API_KEY;
if (!apiKey) {
    console.error('API_KEY not set — some features will be unavailable');
}
```

### Caveats

- **Variables are set per-tool**, not per-webservice-instance. All pods for the same tool share the same environment.
- **Restart the webservice after changing env vars** — they're loaded at process start, not dynamically:
  ```bash
  become my-tool webservice --backend=kubernetes node22 restart
  ```
- **Never hardcode secrets** in source files committed to version control. Always use `toolforge env set`.

---

## SOP 7: Logging and Debugging

### Kubernetes Logs

```bash
# Tail logs from the current pod
become my-tool kubectl logs -f deployment/my-tool

# Last N lines
become my-tool kubectl logs --tail=100 deployment/my-tool

# Follow a specific pod (useful with multiple replicas)
become my-tool kubectl logs -f pod/my-tool-7d8f9e2a4-x3y7z

# Search for errors
become my-tool kubectl logs deployment/my-tool | grep -i error
```

### Structured Logging (Zero-Dependency)

```javascript
function log(level, message, data = {}) {
    const entry = {
        timestamp: new Date().toISOString(),
        level,
        message,
        ...data,
    };
    // Write to stdout — Kubernetes collects this
    process.stdout.write(JSON.stringify(entry) + '\n');
}

// Usage
log('info', 'Server starting', { port: PORT });
log('error', 'Failed to resolve file', { file: filename, error: e.message });
```

### Common Issues

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Connection refused` | Server not listening on `PORT` | Check `process.env.PORT` in code |
| `CrashLoopBackOff` in status | Server crashes on startup | Run `kubectl logs` to see the error |
| `ImagePullBackOff` | Runtime image not found | Check runtime name (`node22` not `nodejs22`) |
| Slow first request | Cold start + NFS metadata | Use a keepalive or health check endpoint |
| `ERR_FAILED 200 (OK)` | Streamed response to Pannellum | Use `readFile()` instead of streaming |
| 404 for existing files | Path resolution wrong | Log `filePath` and check directory traversal |

### Health Check Endpoint

Toolforge's Kubernetes expects the server to be responsive. Add a lightweight health check:

```javascript
server.on('listening', () => {
    // Signal to Kubernetes that the server is ready
    console.log('READY');
});
```

---

## SOP 8: Cron Jobs

For batch processing, periodic syncs, or scheduled maintenance:

```bash
# Run a script every hour
become my-tool job schedule node22 \
    --command 'node /data/project/my-tool/cron/cleanup.mjs' \
    --no-filelog \
    "0 * * * *"

# Run once
become my-tool job submit node22 \
    --command 'node /data/project/my-tool/cron/backfill.mjs'
```

### Cron Job Script Template

```javascript
// cron/cleanup.mjs — Scheduled script (no HTTP server needed)
import { readdir, unlink, stat } from 'node:fs/promises';
import { join } from 'node:path';

const CACHE_DIR = '/data/project/my-tool/images';
const MAX_AGE_DAYS = 7;

async function cleanup() {
    const files = await readdir(CACHE_DIR);
    const now = Date.now();
    let removed = 0;

    for (const file of files) {
        const filePath = join(CACHE_DIR, file);
        const stats = await stat(filePath);
        const ageDays = (now - stats.atimeMs) / (1000 * 60 * 60 * 24);
        if (ageDays > MAX_AGE_DAYS) {
            await unlink(filePath);
            removed++;
        }
    }

    console.log(`Cleanup: removed ${removed} files (threshold: ${MAX_AGE_DAYS} days)`);
}

cleanup().catch(err => {
    console.error('Cleanup failed:', err);
    process.exit(1);
});
```

---

## SOP 9: Restarting and Updating

### Restart (zero-downtime)

```bash
become my-tool webservice --backend=kubernetes node22 restart
```

The Kubernetes deployment performs a rolling restart — no downtime as long as your server starts quickly.

### Update Code

```bash
# Upload new version
scp server.mjs <user>@login.toolforge.org:/data/project/my-tool/

# Restart to pick up changes
ssh <user>@login.toolforge.org "become my-tool webservice --backend=kubernetes node22 restart"
```

### Stop

```bash
become my-tool webservice --backend=kubernetes node22 stop
```

---

## Reference: Quick Command Cheat Sheet

```bash
# === Lifecycle ===
become my-tool webservice --backend=kubernetes node22 start
become my-tool webservice --backend=kubernetes node22 stop
become my-tool webservice --backend=kubernetes node22 restart
become my-tool webservice --backend=kubernetes node22 status

# === Logs ===
become my-tool kubectl logs -f deployment/my-tool
become my-tool kubectl logs --tail=100 deployment/my-tool

# === File Transfer (from local machine) ===
scp server.mjs <user>@login.toolforge.org:/data/project/my-tool/
scp -r public/ <user>@login.toolforge.org:/data/project/my-tool/

# === Environment ===
become my-tool toolforge env set KEY value
become my-tool toolforge env list
become my-tool toolforge env unset KEY

# === Scheduled Jobs ===
become my-tool job schedule node22 --command 'node script.mjs' "0 * * * *"
become my-tool job submit node22 --command 'node script.mjs'

# === Direct Shell ===
become my-tool
```

---

## Reference: Common Pitfalls

| Pitfall | Why It Happens | Prevention |
|---------|---------------|------------|
| **Missing PORT** | Hardcoded port in code | Always use `process.env.PORT || 8765` |
| **Streaming to Pannellum** | `createReadStream().pipe(res)` causes `ERR_FAILED` | Always use `readFile()` + `res.end()` for images |
| **No Cache-Control** | Missing headers = re-download on every page load | Always set cache headers for static assets |
| **Cached 404 pages** | 404 served with `Cache-Control: public` | Use `no-store` for error responses |
| **Slow npm install** | NFS metadata operations are slow | Minimize dependencies; use `.npmrc` to skip audit |
| **Missing MIME type** | `Content-Type` not set, browser refuses to load | Explicit MIME map for all file extensions |
| **Traversal vulnerability** | `join(dir, pathname)` can escape the root | Always `path.resolve()` and check `startsWith(dir + path.sep)` |
| **Crash on startup** | Unhandled promise rejection in `createServer` | Wrap async handlers in try/catch |
| **Stale image cache** | Commons file overwritten, old URL still cached | Append `?v={timestamp}` to cached image URLs |
| **CORS errors** | `upload.wikimedia.org` has no CORS headers | Proxy images through your own server |

---

## See Also

- **[wikimedia-toolforge](../wikimedia-toolforge/SKILL.md)** — Account setup, tool creation, SSH, Kubernetes pods, cron jobs, database access
  - **SOP 9: Frontend Assets (Privacy-Preserving CDN)** — Must-load JS/CSS from `tools-static.wmflabs.org/cdnjs/` instead of external CDNs
- **[commons-file-resolution](../commons-file-resolution/SKILL.md)** — Resolving `File:` references to HTTP URLs, caching images for same-origin serving
- **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** — User-Agent, rate limiting, error handling
- **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** — Thumbnail URL generation and format conversion
- **[wikimedia-security-and-privacy](../wikimedia-security-and-privacy/SKILL.md)** — CDN privacy risks, data minimization, and third-party script policies
