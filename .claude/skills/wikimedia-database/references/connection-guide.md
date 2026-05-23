# Connection Guide: Toolforge SSH Tunnel

## Prerequisites

### Required

| Requirement | How to get it |
|---|---|
| Toolforge account | Apply at [toolforge.org](https://toolforge.org/) |
| SSH public key added | Upload via [admin.toolforge.org](https://admin.toolforge.org/) |
| SSH private key loaded | `ssh-add ~/.ssh/id_ed25519` |
| Replica database credentials | See "Getting Credentials" below |

### Environment variables

Set these in your `.env` file (see `assets/.env.example`):

```bash
TOOLFORGE_USER="your-shell-username"     # Your Toolforge LDAP username
TOOLFORGE_SQL_USER="u12345"              # Your replica DB username (starts with 'u')
TOOLFORGE_SQL_PASSWORD="your-password"   # Your replica DB password
TOOLFORGE_DB_PORT="3307"                 # Local port for tunnel (optional, default 3307)
```

---

## Getting Credentials

### Option A: Replica Database Credentials (from dashboard)

These give you access to Wikimedia production replicas (enwiki, wikidata, etc.).

1. Log into [admin.toolforge.org](https://admin.toolforge.org/) and go to **MySQL Databases**
2. You'll find:
   - **Username** (starts with `u`, e.g., `u12345`) → set as `TOOLFORGE_SQL_USER`
   - **Password** → set as `TOOLFORGE_SQL_PASSWORD`
   - **Hostname** (e.g., `enwiki.analytics.db.svc.wikimedia.cloud`)
3. Copy these into your `.env` file

**Important:** These are NOT per-tool credentials. They're linked to your Toolforge user account and work for all replica databases.

### Option B: Tool-Owned Database Credentials (from replica.my.cnf)

If you need credentials for a *specific tool's own MariaDB database* (not replicas), they're stored in the tool's home directory. After SSHing in and running `become`:

```bash
become my-tool-name
cat replica.my.cnf
```

This prints:
```ini
[client]
user = u12345
password = your-tool-db-password
```

Use these if you need to connect to the tool's database from an external MySQL client or application code.

See the `wikimedia-toolforge` skill for more on tool-owned databases.

---

## Connection Methods

### Method 1: `setup-tunnel.sh` (recommended)

```bash
./scripts/setup-tunnel.sh [db_host] [local_port]
```

- Auto-detects whether tunnel is already running
- Uses `autossh` if available (auto-reconnecting, recommended for long sessions)
- Falls back to plain `ssh`
- Verifies the tunnel is active before returning

### Method 2: Direct SSH

```bash
# Plain SSH
ssh -L 3307:enwiki.analytics.db.svc.wikimedia.cloud:3306 \
    youruser@login.toolforge.org -N

# With autossh (auto-reconnect on drop)
autossh -M 0 \
    -o "ServerAliveInterval 30" \
    -o "ServerAliveCountMax 3" \
    -o "ExitOnForwardFailure yes" \
    -L 3307:enwiki.analytics.db.svc.wikimedia.cloud:3306 \
    youruser@login.toolforge.org -N -v
```

### Method 3: SSH config (most convenient)

Add to `~/.ssh/config`:

```
Host toolforge
    HostName login.toolforge.org
    User youruser
    ForwardAgent yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
    ExitOnForwardFailure yes
    LocalForward 3307 enwiki.analytics.db.svc.wikimedia.cloud:3306
```

Then connect with just:

```bash
ssh toolforge -N
```

---

## Testing the Connection

```bash
# Check if tunnel is listening
nc -z 127.0.0.1 3307 && echo "Tunnel active" || echo "No tunnel"

# MySQL quick test (requires mysql CLI)
mysql -h 127.0.0.1 -P 3307 -u u12345 -p -e "SELECT 1"

# Or use the query script
./scripts/query.sh "SELECT COUNT(*) as total_pages FROM page WHERE page_namespace = 0"
```

---

## Troubleshooting

### "Permission denied (publickey)"
- Your SSH key isn't loaded: `ssh-add -l`
- Your key isn't added to Toolforge: check admin panel

### "Connection refused" on local port
- Tunnel isn't running: run `./scripts/setup-tunnel.sh`
- Wrong port: check `TOOLFORGE_DB_PORT`

### "Access denied for user"
- Wrong replica username/password: check `.env`
- Remember username starts with `u` (e.g., `u12345`)

### Tunnel keeps dropping
- Install autossh: `brew install autossh` (macOS) or `apt install autossh` (Linux)
- Use the SSH config method above with `ServerAliveInterval`

### "Too many connections"
- Close unused tunnels: `./scripts/close-tunnel.sh`
- Check for zombie ssh processes: `ps aux | grep 'ssh -L'`

### Can't connect to a specific database
- Database names must end in `_p` (e.g., `enwiki_p`, not `enwiki`)
- The database must be in the list of available replicas

---

## Security Notes

- The tunnel encrypts all traffic between your machine and Toolforge
- Replica databases are **read-only** — use only SELECT queries
- Never commit `.env` files with credentials to version control
- Rotate your replica password if you suspect it's been exposed
