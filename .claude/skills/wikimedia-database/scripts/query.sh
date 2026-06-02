#!/usr/bin/env bash
# Run a SQL query against a Wikimedia production replica
# Usage: ./query.sh "SELECT ..." [database]
#   Pass SQL as a single argument (quote it!)
#   database: which replica to query (default: enwiki_p)
#
#   Uses pymysql (pure Python) by default to avoid MySQL 9.x auth plugin
#   issues. Falls back to mysql CLI if pymysql is unavailable.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SQL="${1:-}"
DB="${2:-enwiki_p}"
LOCAL_PORT="${TOOLFORGE_DB_PORT:-3307}"

# ──────────────────────────────────
# 1. Validate
# ──────────────────────────────────

if [ -z "$SQL" ]; then
    echo -e "${RED}❌ No SQL provided${NC}"
    echo "   Usage: ./query.sh \"SELECT page_title, page_id FROM page LIMIT 5\" [database]"
    echo ""
    echo "   Examples:"
    echo "     ./query.sh \"SELECT 1\""
    echo "     ./query.sh \"SELECT page_title FROM page WHERE page_id = 736\""
    echo "     ./query.sh \"SELECT * FROM page_props WHERE pp_propname = 'wikibase_item' LIMIT 10\"" "enwiki_p"
    exit 1
fi

# Check that it's a SELECT (safety guardrail)
SQL_UPPER=$(echo "$SQL" | tr '[:lower:]' '[:upper:]')
if [[ "$SQL_UPPER" != SELECT* ]]; then
    echo -e "${RED}❌ Only SELECT queries are allowed (read-only replica)${NC}"
    exit 1
fi

# Check tunnel
if ! command -v nc &>/dev/null || ! nc -z 127.0.0.1 "$LOCAL_PORT" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  No tunnel detected on 127.0.0.1:${LOCAL_PORT}${NC}"
    echo "   Run ./scripts/setup-tunnel.sh first"
    exit 1
fi

# Check env vars
MISSING=""
[ -z "${TOOLFORGE_SQL_USER:-}" ] && MISSING="$MISSING TOOLFORGE_SQL_USER"
[ -z "${TOOLFORGE_SQL_PASSWORD:-}" ] && MISSING="$MISSING TOOLFORGE_SQL_PASSWORD"
if [ -n "$MISSING" ]; then
    echo -e "${RED}❌ Missing environment variables:${MISSING}${NC}"
    echo "   Set them in your .env file or export them."
    exit 1
fi

echo -e "${CYAN}📊 Querying ${DB}${NC}"
echo -e "   SQL: ${SQL}"
echo ""

# ──────────────────────────────────
# 2. Try pymysql first (MySQL 9.x compatible)
# ──────────────────────────────────

if python3 -c "import pymysql" 2>/dev/null; then
    # Pass SQL to Python via environment variable to avoid quoting issues
    export QUERY_SQL="$SQL"
    export QUERY_DB="$DB"
    export QUERY_PORT="$LOCAL_PORT"
    python3 << 'PYEOF'
import os, sys, pymysql
from dotenv import load_dotenv

# Silent load: find_dotenv() can fail in embedded heredoc contexts
try:
    load_dotenv()
except Exception:
    pass

sql = os.environ['QUERY_SQL']
db = os.environ['QUERY_DB']
port = int(os.environ['QUERY_PORT'])

try:
    conn = pymysql.connect(
        host='127.0.0.1',
        port=port,
        user=os.getenv('TOOLFORGE_SQL_USER'),
        password=os.getenv('TOOLFORGE_SQL_PASSWORD'),
        database=db,
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )
    with conn.cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            print("(no results)")
            sys.exit(0)
        # Print header from column names
        if rows:
            headers = list(rows[0].keys())
            col_widths = {}
            for h in headers:
                max_val = len(str(h))
                for r in rows:
                    val = r[h]
                    if isinstance(val, bytes):
                        val = val.decode('utf-8')
                    max_val = max(max_val, len(str(val)))
                col_widths[h] = min(max_val + 2, 60)
            # Header row
            header_line = "  ".join(h.ljust(col_widths[h]) for h in headers)
            print(header_line)
            print("-" * len(header_line))
            # Data rows
            for r in rows:
                vals = []
                for h in headers:
                    val = r[h]
                    if val is None:
                        val = "NULL"
                    elif isinstance(val, bytes):
                        val = val.decode('utf-8')
                    elif isinstance(val, float):
                        val = f"{val:.2f}"
                    vals.append(str(val).ljust(col_widths[h]))
                print("  ".join(vals))
        print(f"\n({len(rows)} rows)")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()
PYEOF
    exit 0
fi

# ──────────────────────────────────
# 3. Fallback: mysql CLI
# ──────────────────────────────────

if command -v mysql &>/dev/null; then
    echo -e "${YELLOW}⚠️  pymysql not available, trying mysql CLI (may fail on MySQL 9.x)${NC}"
    echo ""
    mysql -h 127.0.0.1 \
        -P "$LOCAL_PORT" \
        -u "${TOOLFORGE_SQL_USER}" \
        -p"${TOOLFORGE_SQL_PASSWORD}" \
        -D "$DB" \
        -e "$SQL" \
        --table 2>&1 || {
            echo ""
            echo -e "${RED}❌ mysql CLI failed${NC}"
            echo "   Install pymysql for MySQL 9.x compatibility:"
            echo "     pip install pymysql python-dotenv"
            exit 1
        }
else
    echo -e "${RED}❌ Neither pymysql nor mysql CLI available${NC}"
    echo "   Install pymysql: pip install pymysql python-dotenv"
    exit 1
fi
