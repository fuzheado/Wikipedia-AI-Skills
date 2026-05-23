#!/usr/bin/env bash
# Run a SQL query against a Wikimedia production replica
# Usage: ./query.sh "SELECT ..." [database]
#   Pass SQL as a single argument (quote it!)
#   database: which replica to query (default: enwiki_p)

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

# ──────────────────────────────────
# 2. Execute query
# ──────────────────────────────────

echo -e "${CYAN}📊 Querying ${DB}${NC}"
echo -e "   SQL: ${SQL}"
echo ""

# Try using mysql CLI first (fastest path)
if command -v mysql &>/dev/null; then
    mysql -h 127.0.0.1 \
        -P "$LOCAL_PORT" \
        -u "${TOOLFORGE_SQL_USER}" \
        -p"${TOOLFORGE_SQL_PASSWORD}" \
        -D "$DB" \
        -e "$SQL" \
        --table 2>&1
else
    echo -e "${YELLOW}⚠️  mysql CLI not found. Try the Python path:${NC}"
    echo ""
    echo "   pip install pymysql python-dotenv"
    echo ""
    echo "   Then use the Python pattern from SKILL.md:"
    echo ""
    cat <<'PYTHON'
import os, pymysql
from dotenv import load_dotenv
load_dotenv()

conn = pymysql.connect(
    host='127.0.0.1',
    port=int(os.getenv('TOOLFORGE_DB_PORT', '3307')),
    user=os.getenv('TOOLFORGE_SQL_USER'),
    password=os.getenv('TOOLFORGE_SQL_PASSWORD'),
    database=os.environ.get('DB_NAME', 'enwiki_p'),
    cursorclass=pymysql.cursors.DictCursor,
    charset='utf8mb4'
)
try:
    with conn.cursor() as cursor:
        cursor.execute("""SQL""")
        for row in cursor.fetchall():
            print(row)
finally:
    conn.close()
PYTHON
    exit 1
fi
