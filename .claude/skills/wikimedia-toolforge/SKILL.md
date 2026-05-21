---
name: wikimedia-toolforge
description: Manage Toolforge accounts, web services, Kubernetes pods, cron jobs, and file deployment for Wikimedia tools
license: MIT
compatibility: opencode
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

## Guardrails & Common Pitfalls

1. **Always use `become`** before running tool-specific commands. Running `webservice` or `crontab -e` without `become` will execute under your user account, not the tool's service account, resulting in permission errors.
2. **SSH key expiry** — Toolforge SSH keys expire after a period. If you get permission denied, regenerate your key in the admin console and re-add it to `ssh-agent`.
3. **NFS latency** — `/data/project/` is on NFS. File operations can be slow. Avoid frequent small writes. Use local `/tmp/` for temporary files and move results to NFS only when needed.
4. **Resource limits** — Kubernetes pods have 1 CPU and 1Gi RAM by default. Use toolforge jobs with `--mem` and `--cpu` flags for larger tasks. Do not run resource-intensive tasks on bastion or login nodes.
5. **Do not run long processes on login** — The login shell is for administration only. Long-running processes should be jobs or web services. Processes running for more than 30 minutes on login may be killed without warning.
6. **Database connections** — For replica database access, see the `wikimedia-database` skill. For tool-owned databases (MariaDB), use `become my-tool-name` and run `sql my-tool-name` to access the tool's database.
7. **Static file caching** — Static web services (`--backend=kubernetes static`) serve from `/data/project/my-tool-name/`. Files are cached; wait a few minutes after deployment or use a versioned URL pattern (`style.v2.css`).
8. **Test locally first** — Deploying broken code to Toolforge wastes time. Test scripts locally with representative data before deploying.
9. **Clean up old jobs** — Kubernetes job history accumulates. Delete completed jobs that are no longer needed using `toolforge jobs delete`.

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
