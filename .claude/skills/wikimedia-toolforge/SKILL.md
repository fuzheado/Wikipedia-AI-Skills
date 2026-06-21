---
name: wikimedia-toolforge
description: Manage Toolforge accounts, web services, Kubernetes pods, cron jobs, and file deployment for Wikimedia tools
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["Toolforge", "tool hosting", "Kubernetes", "web service", "cron job", "deploy"]
  - keywords: ["toolforge tools create", "become", "webservice", "toolforge jobs"]
last_verified: 2026-06-10
---

Toolforge (formerly Wikimedia Tool Labs) is a cloud hosting platform for community-developed tools that interact with Wikimedia wikis and data. This skill covers account setup, service management, deployment, and debugging.

## Prerequisites

- A [Toolforge account](https://toolforge.org/) approved via Wikimedia Foundation onboarding
- SSH public key added to your Toolforge account via the [admin console](https://admin.toolforge.org/)
- `ssh-agent` running locally with your private key loaded (`ssh-add ~/.ssh/id_ed25519`)
- The following environment variable set (optional but recommended):
  - `TOOLFORGE_USER` — Your Toolforge shell/LDAP username

## SOP 1: Account & Project Setup

### 1.1 Verify Account

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org hostname
```

If successful, you will see a hostname like `tools-sgebastion-XX`. If the connection hangs or fails, check that your SSH key is added to the admin console.

### 1.2 Create a New Tool

Each tool is a sub-account with its own directory, database access, and web service.

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org toolforge tools create my-tool-name
```

**Naming rules:**
- Lowercase letters, digits, and hyphens only
- Must be unique across all Toolforge
- Should be descriptive (e.g., `pageview-analyzer`, `category-watchdog`)

After creation, the tool's home directory is at `/data/project/my-tool-name/`.

### 1.3 Configure Tool Permissions

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org toolforge tools maintainers add my-tool-name ${TOOLFORGE_USER:-your-username}
```

This adds you as a maintainer so you can deploy files and manage services.

## SOP 2: File Deployment

### 2.1 Deploy Files via SSH

```bash
# Deploy a single file
scp my-script.py ${TOOLFORGE_USER:-your-username}@login.toolforge.org:/data/project/my-tool-name/

# Deploy an entire directory
rsync -avz --exclude '.*' ./my-tool/ ${TOOLFORGE_USER:-your-username}@login.toolforge.org:/data/project/my-tool-name/
```

**Always use `rsync` for repeated deployments** — it only transfers changed files and preserves permissions.

### 2.2 Deploy via Git (Recommended for Maintained Tools)

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
cd /data/project/my-tool-name/
git clone https://github.com/your-org/my-tool.git .
```

Then update with `git pull` on subsequent deployments. This provides version history and rollback.

### 2.3 Set Executable Permissions

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org chmod +x /data/project/my-tool-name/my-script.py
```

## SOP 3: Web Services

Toolforge supports several web service backends. Choose based on your needs:

| Backend | Use Case | Start Command |
|---------|----------|---------------|
| `webservice --backend=kubernetes python3.11` | Python web apps (Flask, Django, FastAPI) | `webservice --backend=kubernetes python3.11 start` |
| `webservice --backend=kubernetes node` | Node.js web apps (Express) | `webservice --backend=kubernetes node start` |
| `webservice --backend=kubernetes php8.2` | PHP web apps | `webservice --backend=kubernetes php8.2 start` |
| `webservice --backend=kubernetes static` | Static file serving (HTML/JS) | `webservice --backend=kubernetes static start` |
| `webservice --backend=buildservice` | Build Service container (any language) | `webservice --backend=buildservice start` |

### 3.1 Start a Web Service

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
become my-tool-name
cd /data/project/my-tool-name
webservice --backend=kubernetes python3.11 start
```

The `become` command switches to the tool's service account, which has the correct permissions and environment variables.

### 3.2 Check Service Status

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
become my-tool-name
webservice --backend=kubernetes python3.11 status
```

### 3.3 Stop a Web Service

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
become my-tool-name
webservice --backend=kubernetes python3.11 stop
```

### 3.4 Restart a Web Service

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
become my-tool-name
webservice --backend=kubernetes python3.11 restart
```

### 3.5 Web Service Entry Point

The web service looks for a `server.py` (Python), `app.js` (Node), or `index.php` (PHP) in the tool's home directory by default. To use a custom entry point, set the `WEB_CONCURRENCY` or create a `launch.sh` script:

```bash
#!/bin/bash
# launch.sh — custom web service entry point
cd /data/project/my-tool-name
gunicorn -w 4 -b 0.0.0.0:8000 my_app:app
```

Mark it executable: `chmod +x launch.sh`, then start with:
```bash
webservice --backend=kubernetes python3.11 start --launch launch.sh
```

## SOP 4: Kubernetes Jobs (One-Off Tasks)

For one-off or batch processing tasks that don't need a persistent web service:

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
become my-tool-name
toolforge jobs run my-job-name --command "python3 /data/project/my-tool-name/my_script.py" --image python3.11 --wait
```

### Common Job Options

| Option | Description |
|--------|-------------|
| `--command "..."` | Command to run inside the container |
| `--image python3.11` | Container image (choose based on language/runtime) |
| `--wait` | Wait for the job to finish before returning logs |
| `--mem 2Gi` | Memory limit (default: 1Gi, max: 4Gi) |
| `--cpu 1` | CPU cores (default: 1, max: 2) |
| `--filelog` | Stream logs to a file on NFS (for later inspection) |
| `--timestamps` | Add timestamps to log output |

### Check Job Status

```bash
become my-tool-name
toolforge jobs list
toolforge jobs logs my-job-name
```

### Delete a Job

```bash
become my-tool-name
toolforge jobs delete my-job-name
```

## SOP 5: Cron Jobs

For scheduled, recurring tasks:

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
become my-tool-name
crontab -e
```

Add a line in standard cron format:

```
# Run daily at 2:00 AM UTC
0 2 * * * /usr/bin/python3 /data/project/my-tool-name/daily_report.py >> /data/project/my-tool-name/logs/cron.log 2>&1
```

**Cron job guardrails:**
- Always redirect output to a log file (otherwise cron emails it to you and can fill your mailbox)
- Use absolute paths for all commands and file references
- Test the script manually before scheduling it via cron
- Set a reasonable schedule — do not run on sub-minute intervals
- For long-running jobs (over 10 minutes), use `toolforge jobs` (SOP 4) triggered by cron instead of running directly

### List Cron Jobs

```bash
become my-tool-name
crontab -l
```

## SOP 6: Environment Variables & Secrets

### 6.1 Set Environment Variables

Toolforge provides a `set-webservice-env` command for web services:

```bash
become my-tool-name
toolforge env set MY_VARIABLE my_value
```

### 6.2 View Environment Variables

```bash
become my-tool-name
toolforge env list
```

### 6.3 Remove an Environment Variable

```bash
become my-tool-name
toolforge env unset MY_VARIABLE
```

### 6.4 Secrets (Database Passwords, API Keys)

Store sensitive values as environment variables via `toolforge env set`. These are stored securely and not shown in `env list` output. Do not hardcode secrets in source files.

### 6.5 MediaWiki API Authentication (Bot Passwords)

If your Toolforge tool authenticates against the MediaWiki API to make edits
(e.g., via bot passwords or Pywikibot), be aware that the API's `lgname`
parameter requires **underscores** where usernames have spaces:

```python
# ✗ Fails silently with "Unknown error"
lgname = "AL Wiki MIT@mybot"

# ✓ Works
lgname = "AL_Wiki_MIT@mybot"
```

See the **[pywikibot](../pywikibot/SKILL.md)** skill ("Login fails" troubleshooting
section) and the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill
("Login Username Quirk" section) for full details.

## SOP 7: Logs & Debugging

### 7.1 Web Service Logs

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
become my-tool-name
webservice --backend=kubernetes python3.11 logs
```

Add `--tail` to see only the last N lines:
```bash
webservice --backend=kubernetes python3.11 logs --tail=50
```

### 7.2 Job Logs

```bash
become my-tool-name
toolforge jobs logs my-job-name
```

### 7.3 Check Disk Usage

```bash
become my-tool-name
du -sh /data/project/my-tool-name/
```

### 7.4 Interactive Debugging via Shell

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
become my-tool-name
# Now run commands interactively from the tool's home directory
python3 -c "import requests; print(requests.get('https://en.wikipedia.org/api/rest_v1/page/summary/Python_(programming_language)').json())"
```

## SOP 8: Build Service (Container Images)

The Toolforge Build Service allows you to build custom container images from a public Git
repository using Cloud Native Buildpacks. This is the modern, recommended way to deploy
tools — it frees you from per-language base images and gives you control over the runtime.

### 8.1 How It Works

Instead of deploying files to NFS and using a language-specific webservice backend, you:

1. Host your code in a **public Git repository** (GitLab, GitHub, Gerrit)
2. Add a **`Procfile`** at the root of your repo defining how to start your app
3. Run `toolforge build start` to build a container image from your repository
4. Run the built image as a **web service** or a **job**

The Build Service supports: Python, Node.js, PHP, Ruby, Go, Java/JVM, .NET, and Rust.
It can also install OS-level Apt packages and compile frontend assets with Node.js at build time.

### 8.2 Prerequisites

- A **public Git repository** containing your tool's code
- A **Procfile** at the repository root
- `become` access to your tool account

### 8.3 Procfile Format

The Procfile is a plain text file named `Procfile` (no extension) at the root of your repo:

```
web: gunicorn --bind=0.0.0.0 --workers=4 --forwarded-allow-ips=* app:app
migrate: python -m app.django migrate
```

- The `web:` entry defines what runs when you start a **web service**
- Other entries (e.g., `migrate:`) define what runs as **jobs**
- Every process type in the Procfile becomes an executable command in the container

**Important:** Do not name a process type after a real command (e.g., do not use `celery:`
as a process type — use `run-celery:` instead).

### 8.4 Building an Image

```bash
ssh ${TOOLFORGE_USER:-your-username}@login.toolforge.org
become my-tool-name

# Build from the default branch (HEAD)
toolforge build start https://gitlab.wikimedia.org/toolforge-repos/my-tool

# Build from a specific branch, tag, or commit
toolforge build start --ref v1.2.0 https://gitlab.wikimedia.org/toolforge-repos/my-tool

# Use the latest buildpacks (newer language versions)
toolforge build start -L https://gitlab.wikimedia.org/toolforge-repos/my-tool

# Pass build-time environment variables
toolforge build start --envvar NODE_ENV=production https://gitlab.wikimedia.org/toolforge-repos/my-tool
```

### 8.5 Starting a Web Service

```bash
become my-tool-name

# Start the web service from the built image
toolforge webservice buildservice start --mount=none

# Alternatively, create a service.template so 'webservice start' works directly:
echo -e 'type: buildservice\nmount: none' > service.template

# Check status
toolforge webservice buildservice status

# View logs
toolforge webservice buildservice logs -f

# Restart after a new build
toolforge webservice buildservice restart

# Stop
toolforge webservice buildservice stop

# Get an interactive shell inside the running container
toolforge webservice buildservice shell
```

**Note on NFS mounts:** By default, `--mount=none` is recommended. If your tool needs
to read/write files in `/data/project/`, use `--mount=all` and reference the path via
the `$TOOL_DATA_DIR` environment variable instead of relying on `$HOME`.

### 8.6 Running a Job

```bash
become my-tool-name

# Run the 'migrate' process from your Procfile
toolforge jobs run --wait --image my-tool/my-tool:latest --command "migrate" some-job

# Run with arguments
toolforge jobs run --wait --image my-tool/my-tool:latest --command "migrate --production" migrate-job

# Pass composite commands via shell wrapper
toolforge jobs run --wait --image my-tool/my-tool:latest --command "sh -c 'env; nodejs --version'" debug-job
```

### 8.7 Checking Build Logs

```bash
become my-tool-name

# View the most recent build log
toolforge build logs

# Check build quota
toolforge build quota
```

### 8.8 Updating Code

To deploy a new version:

```bash
become my-tool-name

# 1. Push new code to your Git repo
# 2. Trigger a new build
toolforge build start https://gitlab.wikimedia.org/toolforge-repos/my-tool
# 3. Restart the web service to use the new image
toolforge webservice buildservice restart
```

### 8.9 Installing Apt Packages

Create a `project.toml` at the root of your repository:

```toml
[_]
schema-version = "0.2"

[com.heroku.buildpacks.deb-packages]
install = [
    "imagemagick",
    "php",
]
```

Packages from Ubuntu 24.04 (Noble) can be looked up at
https://packages.ubuntu.com/noble/.

### 8.10 Known Limitations

- Limited to a single primary language runtime per image (Node.js can be a secondary runtime for asset compilation)
- No LDAP connection inside containers — commands like `id <user>` will not work
- `$HOME` does not point to `/data/project/<tool>/` — use `$TOOL_DATA_DIR` instead
- NFS is not mounted by default — use `--mount=all` explicitly when needed
- Build images have a storage quota — check with `toolforge build quota` and request increases via Phabricator if needed

## Guardrails & Common Pitfalls

1. **Always use `become`** before running tool-specific commands. Running `webservice` or `crontab -e` without `become` will execute under your user account, not the tool's service account, resulting in permission errors.
2. **SSH key expiry** — Toolforge SSH keys expire after a period. If you get permission denied, regenerate your key in the admin console and re-add it to `ssh-agent`.
3. **NFS latency** — `/data/project/` is on NFS. File operations can be slow. Avoid frequent small writes. Use local `/tmp/` for temporary files and move results to NFS only when needed.
4. **Resource limits** — Kubernetes pods have 1 CPU and 1Gi RAM by default. Use toolforge jobs with `--mem` and `--cpu` flags for larger tasks. Do not run resource-intensive tasks on bastion or login nodes.
5. **Do not run long processes on login** — The login shell is for administration only. Long-running processes should be jobs or web services. Processes running for more than 30 minutes on login may be killed without warning.
6. **Database connections** — For replica database access, see the `wikimedia-database` skill. For tool-owned databases (MariaDB), use `become my-tool-name` and run `sql my-tool-name` to access the tool's database. If you need the actual MySQL username and password (e.g., for an external client or connection string), find them in the tool's home directory after `become`:

   ```bash
   become my-tool-name
   cat replica.my.cnf
   ```

   This prints `[client]` with `user` and `password` fields. The `sql` command is still the recommended way to connect interactively, but `replica.my.cnf` is useful when configuring ORM connection strings or database drivers in application code.
7. **Static file caching** — Static web services (`--backend=kubernetes static`) serve from `/data/project/my-tool-name/`. Files are cached; wait a few minutes after deployment or use a versioned URL pattern (`style.v2.css`).
8. **Test locally first** — Deploying broken code to Toolforge wastes time. Test scripts locally with representative data before deploying.
9. **Clean up old jobs** — Kubernetes job history accumulates. Delete completed jobs that are no longer needed using `toolforge jobs delete`.
10. **Build Service: Git repo required** — The Build Service requires a **public** Git repository. Private repos are not supported. The `Procfile` must be at the repository root and named exactly `Procfile` (no extension). After a build, you must restart the web service to pick up the new image — `toolforge build start` alone does not restart running services.
11. **Build Service: NFS and $HOME** — Build Service containers do not have NFS mounted by default. Use `--mount=all` to mount it. Inside the container, `$HOME` does not point to `/data/project/<tool>/` — use the `$TOOL_DATA_DIR` environment variable instead for tool home directory paths.

## Example Workflows

### Full Web App Deployment

```bash
# 1. Create tool
ssh user@login.toolforge.org toolforge tools create my-web-tool

# 2. Deploy code
rsync -avz ./my-web-app/ user@login.toolforge.org:/data/project/my-web-tool/

# 3. Set environment variables
ssh user@login.toolforge.org "become my-web-tool; toolforge env set API_KEY my-secret-key"

# 4. Start web service
ssh user@login.toolforge.org "become my-web-tool; webservice --backend=kubernetes python3.11 start"

# 5. Verify it's running
ssh user@login.toolforge.org "become my-web-tool; webservice --backend=kubernetes python3.11 status"
```

### Daily Data Collection (Cron + Job)

```bash
# 1. Deploy the script
rsync -avz collect_data.py user@login.toolforge.org:/data/project/my-tool/

# 2. Set cron to trigger a Kubernetes job
ssh user@login.toolforge.org "become my-tool; crontab -l | { cat; echo '0 3 * * * toolforge jobs run daily-collect --command \"python3 /data/project/my-tool/collect_data.py\" --image python3.11 --wait --filelog >> /data/project/my-tool/logs/cron_trigger.log 2>&1'; } | crontab -"
```

### Build Service Web App (Modern Workflow)

```bash
# 1. Create tool
ssh user@login.toolforge.org toolforge tools create my-build-tool

# 2. Push code to a public Git repository (e.g., GitLab)
#    Ensure a Procfile exists at the root:
#      web: gunicorn --bind=0.0.0.0 --workers=4 app:app

# 3. Build the container image from the Git repo
ssh user@login.toolforge.org "become my-build-tool; toolforge build start https://gitlab.wikimedia.org/toolforge-repos/my-build-tool"

# 4. Start as a build service web service
ssh user@login.toolforge.org "become my-build-tool; toolforge webservice buildservice start --mount=none"

# 5. Verify it's running
ssh user@login.toolforge.org "become my-build-tool; toolforge webservice buildservice status"

# 6. To update: push new code to Git, rebuild, restart
#    ssh login.toolforge.org "become my-build-tool; toolforge build start <repo-url>"
#    ssh login.toolforge.org "become my-build-tool; toolforge webservice buildservice restart"
```

---

## Tooling

This skill includes helper scripts, reference docs, and templates:

### 🔧 Deploy Tool (`scripts/deploy.sh`)

Deploy files to a Toolforge tool via rsync with dry-run preview.

```bash
./scripts/deploy.sh ./my-web-app my-tool-name
```

Features dry-run confirmation, permission setting, and post-deploy steps.

**Note:** For the Build Service (SOP 8), you do not use rsync deployment. Instead,
push code to a public Git repository and use `toolforge build start`. See the
Build Service workflow example above.

### 🔧 Status Check (`scripts/status.sh`)

Check web service status, Kubernetes jobs, disk usage, and active processes.

```bash
./scripts/status.sh my-tool-name
```

### 🔧 Kubernetes Job Manager (`scripts/manage-k8s.sh`)

Manage Kubernetes jobs: run, list, logs, delete, and status.

```bash
./scripts/manage-k8s.sh my-tool-name run my-job "python3 /data/project/my-tool/script.py"
./scripts/manage-k8s.sh my-tool-name list
./scripts/manage-k8s.sh my-tool-name logs my-job
```

### 🔧 Cron Job Manager (`scripts/manage-cron.sh`)

Manage cron jobs: list, add, remove by pattern, or clear all.

```bash
./scripts/manage-cron.sh my-tool-name list
./scripts/manage-cron.sh my-tool-name add '0 2 * * *' 'python3 /data/project/my-tool/daily.py >> /data/project/my-tool/logs/cron.log 2>&1'
./scripts/manage-cron.sh my-tool-name remove daily.py
```

### 📚 CLI Reference (`references/toolforge-cli.md`)

Quick reference of all Toolforge CLI commands organized by category:
- Account & tools, web services (including buildservice), Kubernetes jobs, environment variables, cron, file operations, database

### 🧩 Deploy Config (`assets/deploy-config.sh`)

Environment variable template for deployment scripts:

```bash
cp assets/deploy-config.sh my-config.sh
# Edit my-config.sh with your Toolforge username and tool name
source my-config.sh
./scripts/deploy.sh ./my-app my-tool-name
```

### 🐍 Flask App Template (`assets/app-template.py`)

Ready-to-deploy Flask app with:
- Home page with status
- Health check endpoint (`/api/status`)
- Wikipedia API proxy (`/api/summary/<title>`, `/api/search?q=...`)
- Proper User-Agent for Wikimedia API requests
- WSGI entry point for gunicorn

```bash
cp assets/app-template.py server.py
# Edit, test locally with `python3 server.py`, then deploy
```

**For Build Service deployment:** Add a `Procfile` at your repo root containing:
```
web: gunicorn --bind=0.0.0.0 --workers=4 --forwarded-allow-ips=* app:app
```
Then push to a public Git repo and run `toolforge build start`.
