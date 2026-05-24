---
name: wikimedia-database
description: Execute SQL queries against Wikimedia production replicas via an SSH tunnel to Toolforge, with connection management and data handling guardrails
license: MIT
compatibility: opencode
---

Enables the agent to execute dynamic SQL queries against Wikimedia production replicas (e.g., `enwiki`, `enwiki_p`, `wikidata`, `commonswiki`) by leveraging a local SSH tunnel and specific environment variables for multi-layer authentication.

## **Prerequisites**

* **Authentication:** The following variables must be set in the `.env` file:
* `TOOLFORGE_USER`: The shell/LDAP username for SSH (e.g., `janesmith`).
* `TOOLFORGE_SQL_USER`: The replica database username (e.g., `u1234`).
* `TOOLFORGE_SQL_PASSWORD`: The replica database password.
* `TOOLFORGE_DB_PORT`: The local port for the SSH tunnel (default: `3307`). Set if you need a different port to avoid conflicts with a local MySQL/MariaDB instance.

* **SSH Config:** The user must have their SSH keys added to the `ssh-agent` to allow non-interactive connections.

## **Standard Operating Procedure (SOP)**

### **1. Connection Management**

Before executing any SQL, the agent must ensure the tunnel is active.

* **Check:** Attempt a connection to `127.0.0.1:${TOOLFORGE_DB_PORT:-3307}`.
* **Auto-Establish:** If the port is closed, the agent should attempt to spawn a background SSH process:
`ssh -L ${TOOLFORGE_DB_PORT:-3307}:enwiki.analytics.db.svc.wikimedia.cloud:3306 ${TOOLFORGE_USER}@login.toolforge.org -N`
* **Persistence (Recommended):** For long-running data generation, use `autossh` instead of plain
  `ssh`. Autossh monitors the connection and re-establishes it if the tunnel drops, which happens
  frequently during multi-hour sessions. Install with `brew install autossh` (macOS) or
  `apt install autossh` (Linux), then use:
  `autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -L ${TOOLFORGE_DB_PORT:-3307}:enwiki.analytics.db.svc.wikimedia.cloud:3306 ${TOOLFORGE_USER}@login.toolforge.org -N -v`
* **Escalation:** If the tunnel fails to open, provide the user with the command above to run manually.

### **2. Implementation Pattern (Python)**

The agent should use `pymysql` to interact with the replicas.

```python
import os
import socket
import subprocess
import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_db_connection(db_name='enwiki_p'):
    host = '127.0.0.1'
    port = int(os.getenv('TOOLFORGE_DB_PORT', '3307'))
    
    # Check if tunnel is open
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        if s.connect_ex((host, port)) != 0:
            user = os.getenv("TOOLFORGE_USER")
            # Spawn persistent background tunnel
            cmd = ["ssh", "-L", f"{port}:enwiki.analytics.db.svc.wikimedia.cloud:3306", f"{user}@login.toolforge.org", "-N"]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
    return pymysql.connect(
        host=host,
        port=port,
        user=os.getenv("TOOLFORGE_SQL_USER"),
        password=os.getenv("TOOLFORGE_SQL_PASSWORD"),
        database=db_name,
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )

def query_wiki(sql, db='enwiki_p'):
    conn = get_db_connection(db)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()

```

### **3. Data Handling Guardrails**

* **Read-Only:** Only generate `SELECT` statements.
* **Namespace Filtering:** Always consider `page_namespace` (e.g., `0` for Main/Article space).
* **Binary Decoding:** Many strings (titles, user names) are stored as `Varbinary`. If the output looks like `b'Title'`, the agent must apply `.decode('utf-8')`.
* **Safety Limits:** Every exploratory query **must** include a `LIMIT` (suggested default: 10-50).
* **Database Naming:** Project names must end in `_p` (e.g., `wikidatawiki_p`, `commonswiki_p`).

### **MySQL 9+ compatibility**

If you get `ERROR 2059: Authentication plugin 'mysql_native_password' cannot be loaded`
when using the `mysql` CLI, this is because **MySQL 9.x removed the
`mysql_native_password` plugin entirely** from the client — both as a loadable
`.so` and as a compiled-in implementation. Neither `--default-auth` nor any
other flag can work around this.

**The fix is to use `pymysql`** (pure Python). It implements the MySQL protocol
natively and handles `mysql_native_password` authentication without any
external plugins:

```bash
pip install pymysql python-dotenv
```

The `query.sh` script will automatically use `pymysql` if available, falling
back to the `mysql` CLI only if Python dependencies are missing.

## **Example Use Cases**

* **Prompt:** "What are the 5 oldest pages in the 'Draft' namespace?"
* **Action:** Execute `SELECT page_title, page_touched FROM page WHERE page_namespace = 118 ORDER BY page_id ASC LIMIT 5;`


* **Prompt:** "Count revisions by 'ExampleUser' on enwiki."
* **Action:** Execute `SELECT COUNT(*) FROM revision_userindex JOIN actor ON rev_actor = actor_id WHERE actor_name = 'ExampleUser';`

---

## **Tooling**

This skill includes helper scripts, reference docs, and templates:

### 🔧 Tunnel Management (`scripts/setup-tunnel.sh`)

Establishes an SSH tunnel to Toolforge. Auto-detects if tunnel is already
active, prefers `autossh` for auto-reconnecting, and verifies the connection.

```bash
./scripts/setup-tunnel.sh [db_host] [local_port]
```

**Requires:** `TOOLFORGE_USER` environment variable and SSH key loaded in agent.

### 🔧 Query Runner (`scripts/query.sh`)

Run a SQL query against a replica and see results in the terminal.

```bash
./scripts/query.sh "SELECT page_title, page_len FROM page LIMIT 10" [database]
```

Includes safety guardrails: only SELECT allowed, missing env vars detected.

### 🔧 Tunnel Closer (`scripts/close-tunnel.sh`)

Cleanly tear down the SSH tunnel.

```bash
./scripts/close-tunnel.sh [local_port]
```

### 📚 Schema Reference (`references/schema-replicas.md`)

Full reference of Wikimedia replica database tables (page, revision, actor,
page_props, categorylinks, pagelinks) with column descriptions and common
queries.

### 📚 Connection Guide (`references/connection-guide.md`)

Step-by-step guide for setting up Toolforge access, getting credentials,
and troubleshooting common issues.

### 🧩 Environment Template (`assets/.env.example`)

```bash
cp assets/.env.example .env
# Edit .env with your credentials
```

### 🧩 Sample SQL Queries (`assets/sample-queries.sql`)

50+ pre-built SQL queries organized by category (page info, stats, categories,
pageviews, Wikidata, revisions, links, cross-refs, user activity).
