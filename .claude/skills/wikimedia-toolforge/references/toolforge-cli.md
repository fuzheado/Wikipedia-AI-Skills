# Toolforge CLI Command Reference

Quick reference for the `toolforge` CLI and related commands.

---

## Account & Tools

| Command | Description |
|---|---|
| `toolforge tools list` | List all tools you maintain |
| `toolforge tools create <name>` | Create a new tool |
| `toolforge tools delete <name>` | Delete a tool (irreversible!) |
| `toolforge tools maintainers add <tool> <user>` | Add a maintainer to a tool |
| `toolforge tools maintainers remove <tool> <user>` | Remove a maintainer |

## Web Services

| Command | Description |
|---|---|
| `webservice --backend=kubernetes <type> start` | Start a web service |
| `webservice --backend=kubernetes <type> stop` | Stop a web service |
| `webservice --backend=kubernetes <type> restart` | Restart a web service |
| `webservice --backend=kubernetes <type> status` | Check service status |
| `webservice --backend=kubernetes <type> logs` | View service logs |
| `webservice --backend=kubernetes <type> logs --tail=50` | Last 50 log lines |

### Web Service Types

| Type | Language/Runtime |
|---|---|
| `python3.11` | Python 3.11 (Flask, Django, FastAPI) |
| `node` | Node.js (Express) |
| `php8.2` | PHP 8.2 |
| `static` | Static file serving (HTML/JS/CSS) |

## Kubernetes Jobs

| Command | Description |
|---|---|
| `toolforge jobs run <name> --command "<cmd>" --image <image>` | Run a job |
| `toolforge jobs list` | List all jobs |
| `toolforge jobs logs <name>` | Show job logs |
| `toolforge jobs delete <name>` | Delete a job |

### Job Options

| Option | Description |
|---|---|
| `--image python3.11` | Container image |
| `--wait` | Wait for completion and show logs |
| `--mem 2Gi` | Memory limit (default 1Gi, max 4Gi) |
| `--cpu 1` | CPU cores (default 1, max 2) |
| `--filelog` | Stream logs to NFS file |
| `--timestamps` | Add timestamps to output |

## Environment Variables

| Command | Description |
|---|---|
| `toolforge env set <key> <value>` | Set an environment variable |
| `toolforge env list` | List all environment variables |
| `toolforge env unset <key>` | Remove an environment variable |

## Cron Jobs

| Command | Description |
|---|---|
| `crontab -l` | List cron jobs |
| `crontab -e` | Edit cron jobs |
| `crontab -r` | Remove all cron jobs |

## File Operations

| Command | Description |
|---|---|
| `ssh <user>@login.toolforge.org` | SSH into bastion |
| `become <tool-name>` | Switch to tool's service account |
| `scp <local> <user>@login.toolforge.org:<remote>` | Copy single file |
| `rsync -avz <local>/ <user>@login.toolforge.org:<remote>/` | Sync directory |

## Database

| Command | Description |
|---|---|
| `sql <tool-name>` | Access tool's MariaDB database |
| `toolforge db list` | List available databases |

## Useful Paths

| Path | Purpose |
|---|---|
| `/data/project/<tool-name>/` | Tool home directory |
| `/data/project/<tool-name>/www/static/` | Static file serving root |
| `/tmp/` | Local temp (fast, not shared) |

## Useful Aliases to Add to `~/.ssh/config`

```
Host toolforge
    HostName login.toolforge.org
    User your-username
    ForwardAgent yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

Then just `ssh toolforge` instead of `ssh user@login.toolforge.org`.
