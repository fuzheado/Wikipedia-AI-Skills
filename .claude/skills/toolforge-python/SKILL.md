---
name: toolforge-python
description: Deploy Python web services on Wikimedia Toolforge — Flask (WSGI) and FastAPI (ASGI), gunicorn/uvicorn, Build Service and traditional Kubernetes backends, virtual environments, pip caching, PORT configuration, static files, logging, and common pitfalls
license: MIT
compatibility: opencode
depends_on: [wikimedia-toolforge, wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["Toolforge Python", "Flask", "gunicorn", "Python webservice", "python3.11", "WSGI"]
  - keywords: ["Toolforge FastAPI", "ASGI", "uvicorn", "Python ASGI", "FastAPI toolforge"]
  - keywords: ["Toolforge build service", "Procfile", "buildpack", "toolforge build start"]
  - keywords: ["Toolforge venv", "virtual environment", "pip install", "Toolforge pip", "requirements.txt", "runtime.txt"]
  - keywords: ["Toolforge PORT", "gunicorn bind", "Toolforge static", "Python http server"]
  - keywords: ["Toolforge flask", "flask app", "Toolforge deploy python", "toolforge python"]
  - keywords: ["Toolforge cron python", "python job", "scheduled python", "Toolforge batch"]
last_verified: 2026-06-22
---

> ⚠️ **Prerequisites:** This skill assumes you have a Toolforge account and can SSH in. See **[wikimedia-toolforge](../wikimedia-toolforge/SKILL.md)** for account setup, tool creation, and basic SSH configuration.

> 💡 **Python is the dominant language on Toolforge.** Most existing tools use Python, and the platform has first-class support for Python runtimes. This skill covers the standard Flask + gunicorn stack, which powers the vast majority of Toolforge Python web services.

---

## Quick Reference

| Goal | Command / Pattern |
|------|-------------------|
| Deploy a new Python service | See SOP 1 |
| Choose a runtime | `python3.11` (default), `python3.9` (legacy) — see SOP 1.1 |
| Start/restart a webservice | `become <tool> webservice --backend=kubernetes python3.11 start` |
| See logs | `become <tool> kubectl logs -f deployment/<tool>` |
| Set environment variables | `become <tool> toolforge env set NAME value` |
| Serve static files | Use Flask's `send_from_directory()` or `static_url_path` — see SOP 3 |
| Install dependencies | Use a virtual environment and `requirements.txt` — see SOP 4 |
| Run a cron job | `become <tool> job schedule python3.11 --command 'python3 script.py' "0 * * * *"` |

---

## SOP 1: Bootstrap a Python Web Service

The standard Toolforge Python stack: **Flask + gunicorn**, deployed in a virtual environment.

### 1.1 Choose a Runtime

Toolforge offers these Python runtime versions:

| Runtime | Kubernetes Image | Status |
|---------|-----------------|--------|
| `python3.11` | `docker-registry.tools.wmflabs.org/toolforge-python311-sssd-web:latest` | ✅ Current default (Python 3.11) |
| `python3.9` | `docker-registry.tools.wmflabs.org/toolforge-python39-sssd-web:latest` | ⚠️ Legacy (Python 3.9, available but not recommended for new tools) |

The runtime image includes Python, pip, and system libraries. Your code and
dependencies live on NFS at `/data/project/<tool>/`.

### 1.2 Create the Tool and Virtual Environment

```bash
# From your local machine
ssh <user>@login.toolforge.org

# Create the tool (one time)
toolforge tools create my-python-tool

# Enter the tool's home
become my-python-tool

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Flask and gunicorn
pip install flask gunicorn
```

### 1.3 Write Your App

Create `app.py` — a minimal Flask application:

```python
# app.py — Flask web service for Toolforge
import os
from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)

# Toolforge sets the PORT environment variable — your server must bind to it
PORT = int(os.environ.get('PORT', 8765))


@app.route('/')
def home():
    return '<h1>Hello from Toolforge!</h1>'


@app.route('/api/hello')
def hello():
    return jsonify(message='Hello from Toolforge!', status='ok')


@app.route('/api/status')
def status():
    return jsonify(status='running', port=PORT)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
```

**Key points:**
- Bind to `0.0.0.0:PORT` (not `127.0.0.1`) — Kubernetes needs the external interface
- Always read `PORT` from the environment; the fallback (`8765`) is for local dev only
- The `if __name__ == '__main__'` guard lets you test locally with `python3 app.py`

### 1.4 Deploy with gunicorn

gunicorn is the production WSGI server. Toolforge expects gunicorn to be
installed in your virtual environment.

```bash
# From your local machine — upload files
scp app.py <user>@login.toolforge.org:/data/project/my-python-tool/
scp requirements.txt <user>@login.toolforge.org:/data/project/my-python-tool/

# SSH in and set up
ssh <user>@login.toolforge.org
become my-python-tool

# Create venv and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the webservice
webservice --backend=kubernetes python3.11 start
```

### 1.5 Verify

```bash
# Check status
become my-python-tool webservice --backend=kubernetes python3.11 status

# View logs
become my-python-tool kubectl logs -f deployment/my-python-tool

# Test
curl https://my-python-tool.toolforge.org/
curl https://my-python-tool.toolforge.org/api/hello
```

---

## SOP 1-B: FastAPI / ASGI (Alternative Framework)

[FastAPI](https://fastapi.tiangolo.com/) is a modern ASGI framework with automatic
OpenAPI docs, async support, and built-in data validation. It runs on uvicorn —
an ASGI server — rather than gunicorn directly.

### Key Differences from Flask

| | Flask (WSGI) | FastAPI (ASGI) |
|---|-------------|----------------|
| Server | gunicorn directly | gunicorn **with uvicorn workers** |
| Async | Limited | Native `async/await` |
| Docs | Manual | Auto-generated at `/docs` |
| Validation | Manual or extensions | Built-in via Pydantic |

### Minimal FastAPI App

```python
# app.py — FastAPI ASGI application for Toolforge
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def home():
    return {"Hello": "World"}


@app.get("/api/hello")
async def hello():
    return {"message": "Hello from Toolforge!", "status": "ok"}
```

### Installing Dependencies

```bash
pip install fastapi httpx "uvicorn[standard]" gunicorn
```

### Procfile (Required for Build Service)

```
web: gunicorn app:app -k uvicorn.workers.UvicornWorker --workers=4 \
     --timeout 60 --bind 0.0.0.0 --forwarded-allow-ips=*
```

**How this works:** Gunicorn manages multiple uvicorn worker processes.
Each worker runs an instance of the uvicorn ASGI server. Gunicorn handles
process management and scaling; uvicorn handles async request processing.

### Local Testing

```bash
# FastAPI dev server (auto-reload, great for development)
uvicorn app:app --reload

# Open http://127.0.0.1:8000 to see the JSON response
# Open http://127.0.0.1:8000/docs for auto-generated API docs
```

### Production Deploy (With Build Service)

FastAPI apps typically use the Build Service deployment path (see SOP 1-C).
The key differences from Flask:
- Prodfile uses `-k uvicorn.workers.UvicornWorker`
- gunicorn wraps uvicorn, not the app directly
- The app must be ASGI-compatible (FastAPI, Starlette, Quart, etc.)

---

## SOP 1-C: Build Service Deployment (Container-Based)

The **Build Service** is the recommended path for new tools. Instead of
`scp`-ing files and running `webservice start`, you push code to a Git
repository and Toolforge builds a container image from it.

### Benefits Over Traditional Deployment

| Traditional (Kubernetes) | Build Service (Container) |
|--------------------------|---------------------------|
| Manual `scp` uploads | `git push` triggers deploy |
| Venv lives on NFS | Dependencies baked into image |
| Runtime tied to Toolforge images | Any Python version via `runtime.txt` |
| ASGI/WSGI both work but manual | Native support for both |

### Step-by-Step

**1. Create a Git repo for your tool**

Go to [toolsadmin.wikimedia.org](https://toolsadmin.wikimedia.org/tools/) →
select your tool → `Git repositories` → `create repository`. Clone the
resulting URL (use the public HTTPS URL for Build Service):

```bash
git clone https://gitlab.wikimedia.org/toolforge-repos/my-python-tool.git
cd my-python-tool
```

**2. Set up your project**

```bash
# Create a virtual environment for local dev
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi httpx "uvicorn[standard]" gunicorn
# Or for Flask:
pip install flask gunicorn

# Freeze dependencies
pip freeze > requirements.txt
```

> ⚠️ **License requirement:** All code on Toolforge must be under an
> [OSI-approved open-source license](https://opensource.org/licenses).
> Include a license header in your source files and a `LICENSE` file in your
> repository. See the [Right to fork policy](https://wikitech.wikimedia.org/wiki/Help:Toolforge/Right_to_fork_policy).

**3. Specify Python version (optional)**

Create `runtime.txt` to pin a specific Python version:

```bash
echo "python-3.12.1" > runtime.txt
```

Format: `python-<major>.<minor>.<patch>` — case-sensitive, no spaces.
If omitted, the latest available Python is used.

**4. Create a Procfile**

The `Procfile` tells Toolforge how to start your server:

```
web: gunicorn app:app -k uvicorn.workers.UvicornWorker --workers=4 --timeout 60 --bind 0.0.0.0 --forwarded-allow-ips=*
```

For Flask (WSGI, no uvicorn worker):

```
web: gunicorn app:app --workers=4 --timeout 60 --bind 0.0.0.0 --forwarded-allow-ips=*
```

The PORT environment variable is handled automatically — gunicorn reads it.

**5. Commit and push**

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

**6. Build and start on Toolforge**

```bash
ssh <user>@login.toolforge.org
become my-python-tool

# Start the build (use the PUBLIC HTTPS URL)
toolforge build start https://gitlab.wikimedia.org/toolforge-repos/my-python-tool.git

# Check build status — wait for "ok (Succeeded)"
toolforge build show

# Start the webservice
toolforge webservice buildservice start --mount=none
```

**7. Verify**

```bash
curl https://my-python-tool.toolforge.org/
# FastAPI docs: https://my-python-tool.toolforge.org/docs
```

### Updating Your App

```bash
# Make changes locally, push, then rebuild
git add .
git commit -m "Update"
git push origin main

# SSH in and rebuild
ssh <user>@login.toolforge.org
become my-python-tool
toolforge build start https://gitlab.wikimedia.org/toolforge-repos/my-python-tool.git
```

### Which Path to Choose?

| Scenario | Use |
|----------|-----|
| New Python tool (2024+) | Build Service (SOP 1-C) |
| FastAPI / ASGI app | Build Service required |
| Existing Flask app already on NFS | Traditional (SOP 1) |
| Quick prototype, no Git setup | Traditional (SOP 1) |
| Need to pin exact Python version | Build Service with `runtime.txt` |

---

## SOP 2: The `PORT` Environment Variable

Toolforge's Kubernetes proxy routes incoming requests to your container. It
sets the `PORT` environment variable — your server **must** bind to this port.

### Do This

```python
import os
PORT = int(os.environ.get('PORT', 8765))

# Flask dev server (for testing only — use gunicorn in production)
app.run(host='0.0.0.0', port=PORT)
```

gunicorn automatically reads `PORT` from the environment, so no extra
configuration is needed:

```bash
# gunicorn binds to PORT automatically
venv/bin/gunicorn --bind=0.0.0.0 app:app
```

### Don't Do This

```python
app.run(port=5000)       # ❌ Toolforge proxy won't find it
app.run(port=80)         # ❌ Not running as root
app.run(port='8080')     # ❌ PORT may be different
```

### How It Works

```
Browser ─→ toolforge.org ─→ Kubernetes Ingress ─→ Pod:PORT
                                                      │
                                                process.env.PORT
                                               (e.g., "31245")
```

The `PORT` value is assigned per-pod and is **not predictable** — always read
it from the environment.

---

## SOP 3: Static File Serving

### Using Flask

Flask serves static files from the `static/` folder by default:

```python
from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# Option 1: Serve from Flask's built-in static route
# Place files in /data/project/my-tool/static/ — automatically served at /static/

# Option 2: Custom route for large files or specific directories
@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'images'),
        filename
    )
```

### Cache-Control Headers

Toolforge uses Varnish as an HTTP accelerator. Set proper cache headers for
performance:

| Asset Type | Recommendation | Effect |
|------------|---------------|--------|
| Images, thumbnails | `public, max-age=604800, immutable` | 1 week, never revalidates |
| CSS, JS | `public, max-age=3600` | 1 hour |
| API responses | `no-store` | Never cached |

```python
@app.after_request
def add_cache_headers(response):
    if response.mimetype.startswith('image/'):
        response.headers['Cache-Control'] = 'public, max-age=604800, immutable'
    elif request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=3600'
    return response
```

---

## SOP 4: Virtual Environments and Dependencies

### The NFS Problem

Toolforge's NFS filesystem has **slow metadata operations**. Creating a virtual
environment and running `pip install` can take minutes. Strategies to cope:

1. **Minimize dependencies** — stick to Flask + stdlib when possible
2. **Use a single venv** — create it once, reuse across deployments
3. **Pin exact versions** — prevents pip from resolving dependency trees on
   every install

### requirements.txt

```txt
flask==3.1.0
gunicorn==23.0.0
requests==2.32.3
```

### Full Setup

```bash
# SSH into Toolforge
ssh <user>@login.toolforge.org
become my-python-tool

# Create venv (one time)
python3 -m venv venv

# Activate and install
source venv/bin/activate
pip install -r requirements.txt

# Freeze for reproducibility
pip freeze > requirements-frozen.txt
```

### pip Cache Warning

pip's cache directory defaults to `~/.cache/pip`, which is on NFS. For tools
with many dependencies, this can slow things down. You can override it:

```bash
# Use /tmp for pip cache (in-memory tmpfs, faster but ephemeral)
export PIP_CACHE_DIR=/tmp/pip-cache
pip install -r requirements.txt
```

> ⚠️ **Do not run `pip install` in a cron job** — it will be slow and unreliable.
> Install dependencies once in your venv and reference that in cron commands.

---

## SOP 5: Environment Variables & Secrets

Store configuration and secrets via Toolforge's environment variable system:

```bash
# Set (from a become shell)
become my-python-tool
toolforge env set SECRET_KEY my-secret-value
toolforge env set OAUTH_CLIENT_ID abc123
toolforge env set FLASK_ENV production

# List
toolforge env list

# Remove
toolforge env unset OLD_VAR
```

### Accessing in Python

```python
import os

SECRET_KEY = os.environ.get('SECRET_KEY')
OAUTH_CLIENT_ID = os.environ.get('OAUTH_CLIENT_ID')
FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
```

> ⚠️ **Never hardcode secrets** in source files. Always use `toolforge env set`
> and read from the environment. Toolforge's env system stores values securely
> and they survive pod restarts.

---

## SOP 6: Logging & Debugging

### View Logs

```bash
# Live tail
become my-python-tool kubectl logs -f deployment/my-python-tool

# Last 100 lines
become my-python-tool kubectl logs --tail=100 deployment/my-python-tool
```

### Python Logging

Use the standard `logging` module with stdout (Toolforge captures it):

```python
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

logger.info(f"Server starting on port {PORT}")
```

### Debugging a Crash Loop

If your pod keeps restarting:
1. Check logs for tracebacks (`kubectl logs` shows the last crash)
2. Test locally with the same Python version
3. Verify `requirements.txt` is complete
4. Check PORT binding — the most common crash cause

---

## SOP 7: Cron Jobs

For batch processing, periodic syncs, or scheduled maintenance:

```bash
# Run a script every hour
become my-python-tool job schedule python3.11 \
    --command '/data/project/my-python-tool/venv/bin/python3 /data/project/my-python-tool/cron/cleanup.py' \
    "0 * * * *"

# Run once
become my-python-tool job submit python3.11 \
    --command '/data/project/my-python-tool/venv/bin/python3 /data/project/my-python-tool/cron/backfill.py'
```

### Cron Script Template

```python
#!/usr/bin/env python3
# cron/cleanup.py — Scheduled script (no HTTP server needed)
import os
import time
from pathlib import Path

CACHE_DIR = Path('/data/project/my-python-tool/cache')
MAX_AGE_DAYS = 7


def cleanup():
    now = time.time()
    removed = 0
    for file in CACHE_DIR.glob('*'):
        if file.is_file():
            age_days = (now - file.stat().st_atime) / (60 * 60 * 24)
            if age_days > MAX_AGE_DAYS:
                file.unlink()
                removed += 1
    print(f'Cleanup: removed {removed} files (threshold: {MAX_AGE_DAYS} days)')


if __name__ == '__main__':
    cleanup()
```

> ⚠️ **Always use full paths** for the Python interpreter and scripts in cron
> commands. Cron runs in a minimal environment — no shell profile, no `$PATH`
> setup, no activated venv.

---

## SOP 8: Restarting and Updating

### Restart (zero-downtime)

```bash
become my-python-tool webservice --backend=kubernetes python3.11 restart
```

The Kubernetes deployment performs a rolling restart — no downtime as long as
your server starts quickly.

### Update Code

```bash
# Upload new version
scp app.py <user>@login.toolforge.org:/data/project/my-python-tool/

# If dependencies changed, reinstall
ssh <user>@login.toolforge.org "become my-python-tool bash -c 'source venv/bin/activate && pip install -r /data/project/my-python-tool/requirements.txt'"

# Restart
ssh <user>@login.toolforge.org "become my-python-tool webservice --backend=kubernetes python3.11 restart"
```

### Stop

```bash
become my-python-tool webservice --backend=kubernetes python3.11 stop
```

---

## Reference: Quick Command Cheat Sheet

```bash
# === Lifecycle ===
become my-python-tool webservice --backend=kubernetes python3.11 start
become my-python-tool webservice --backend=kubernetes python3.11 stop
become my-python-tool webservice --backend=kubernetes python3.11 restart
become my-python-tool webservice --backend=kubernetes python3.11 status

# === Logs ===
become my-python-tool kubectl logs -f deployment/my-python-tool
become my-python-tool kubectl logs --tail=100 deployment/my-python-tool

# === File Transfer (from local machine) ===
scp app.py <user>@login.toolforge.org:/data/project/my-python-tool/
scp -r static/ <user>@login.toolforge.org:/data/project/my-python-tool/

# === Virtual Environment ===
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# === Environment ===
become my-python-tool toolforge env set KEY value
become my-python-tool toolforge env list
become my-python-tool toolforge env unset KEY

# === Scheduled Jobs ===
become my-python-tool job schedule python3.11 \
    --command '/data/project/my-python-tool/venv/bin/python3 /data/project/my-python-tool/cron/script.py' \
    "0 * * * *"
```

---

## Reference: Common Pitfalls

| Pitfall | Why It Happens | Prevention |
|---------|---------------|------------|
| **Missing PORT** | Hardcoded port in code | Always use `int(os.environ.get('PORT', 8765))` |
| **Wrong bind address** | `app.run()` defaults to `127.0.0.1` | Always bind `0.0.0.0` |
| **Forgot venv** | pip installs globally, gunicorn not found | Always `source venv/bin/activate` before pip install |
| **Slow pip install** | NFS metadata operations | Minimize dependencies, pin versions, use `PIP_CACHE_DIR=/tmp` |
| **No Cache-Control** | Missing headers = re-download on every page load | Always set cache headers for static assets |
| **Cached 404 pages** | 404 served with `Cache-Control: public` | Use `no-store` for error responses |
| **Crash on startup** | Import error or missing dependency | Test locally with `python3 app.py` before deploying |
| **Cron uses wrong Python** | No venv activation in cron | Always use full path to venv Python: `/data/project/<tool>/venv/bin/python3` |
| **Stale venv** | Dependencies outdated after code change | Re-run `pip install -r requirements.txt` after code updates |
| **TLS/SSL errors from API calls** | Missing CA certificates in container | Install `certifi` and use `requests` (handles this automatically) |

---

## Cross-References

| Related Skill | Why |
|--------------|-----|
| **[wikimedia-toolforge](../wikimedia-toolforge/SKILL.md)** | Account setup, tool creation, SSH, Kubernetes pods, cron jobs, database access |
| **[toolforge-nodejs](../toolforge-nodejs/SKILL.md)** | Node.js equivalent — same platform, different language |
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent, rate limiting, error handling |
| **[wikimedia-database](../wikimedia-database/SKILL.md)** | SQL replicas — database access from Python tools |
| **[pywikibot](../pywikibot/SKILL.md)** | Bot framework — often deployed on Toolforge with Python |
| **[wikimedia-cdn-assets](SKILL.md)** | CDN assets for frontend — privacy-preserving, same Toolforge infrastructure |

---

## Tooling

### 🔧 Deploy Script (`scripts/deploy-python.sh`)

One-command deployment for Python tools:

```bash
./scripts/deploy-python.sh my-python-tool
```

Uploads `app.py`, `requirements.txt`, and static files, reinstalls dependencies,
and restarts the webservice.

### 🐍 Flask App Template (`assets/flask-app-template.py`)

Ready-to-deploy Flask app with:
- Home page with status
- Health check endpoint (`/api/status`)
- Wikipedia API proxy (`/api/summary/<title>`, `/api/search?q=...`)
- Static file serving with cache headers
- Proper User-Agent for Wikimedia API requests
- gunicorn compatibility

```bash
cp assets/flask-app-template.py app.py
# Edit, test locally with `python3 app.py`, then deploy
```

### 🐍 Cron Script Template (`assets/cron-template.py`)

Template for scheduled Python scripts with:
- Standard logging setup
- Error handling and exit codes
- NFS-safe file operations
- Example: cache cleanup, data sync, batch processing

### 📚 requirements.txt Template (`assets/requirements-template.txt`)

Pre-configured dependency file with commonly used packages:
```
flask==3.1.0
gunicorn==23.0.0
requests==2.32.3
```
