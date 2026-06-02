#!/usr/bin/env bash
# Find article quality gaps in a WikiProject
# Usage: ./quality-gaps.sh "WikiProject Name" [limit]
#   Returns high-importance articles with low quality (Stub/Start/C-class)
#   — the highest-ROI improvement targets.
#
#   Uses pymysql (pure Python) by default to avoid MySQL 9.x auth plugin
#   issues. Falls back to mysql CLI if pymysql is unavailable.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PROJECT="${1:-}"
LIMIT="${2:-30}"
LOCAL_PORT="${TOOLFORGE_DB_PORT:-3307}"

if [ -z "$PROJECT" ]; then
    echo -e "${RED}❌ No WikiProject specified${NC}"
    echo "   Usage: ./quality-gaps.sh \"Physics\" [limit]"
    echo "   Usage: ./quality-gaps.sh \"Biology\" 50"
    echo ""
    echo "   Finds high-importance articles stuck at Stub/Start/C-class."
    exit 1
fi

# Check tunnel
if ! command -v nc &>/dev/null || ! nc -z 127.0.0.1 "$LOCAL_PORT" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  No tunnel detected on 127.0.0.1:${LOCAL_PORT}${NC}"
    echo "   Run ./scripts/setup-tunnel.sh first (from wikimedia-database skill)"
    exit 1
fi

echo -e "${CYAN}🔍 Quality Gaps for: ${PROJECT}${NC}"
echo -e "   High-importance articles at Stub/Start/C-class"
echo -e "   Limit: ${LIMIT}"
echo ""

# Try pymysql first (pure Python, works with MySQL 9.x+)
if python3 -c "import pymysql" 2>/dev/null; then
    python3 -c "
import os, sys, pymysql
from dotenv import load_dotenv

load_dotenv()

try:
    conn = pymysql.connect(
        host='127.0.0.1',
        port=int(os.getenv('TOOLFORGE_DB_PORT', '${LOCAL_PORT}')),
        user=os.getenv('TOOLFORGE_SQL_USER'),
        password=os.getenv('TOOLFORGE_SQL_PASSWORD'),
        database='enwiki_p',
        cursorclass=pymysql.cursors.DictCursor,
        charset='utf8mb4'
    )
    with conn.cursor() as cursor:
        project = '${PROJECT}'
        limit = ${LIMIT}
        cursor.execute('''
            SELECT p.page_title, pa.pa_class, pa.pa_importance,
                   p.page_len AS bytes,
                   rev.rev_timestamp AS last_assessed
            FROM page_assessments pa
            JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
            JOIN page p ON pa.pa_page_id = p.page_id
            LEFT JOIN revision rev ON pa.pa_page_revision = rev.rev_id
            WHERE pap.pap_project_title = %s
              AND p.page_namespace = 0
              AND p.page_is_redirect = 0
              AND pa.pa_class IN ('Stub', 'Start', 'C')
              AND pa.pa_importance IN ('Top', 'High')
              AND p.page_len > 0
            ORDER BY FIELD(pa.pa_importance, 'Top', 'High') ASC,
                     FIELD(pa.pa_class, 'Stub', 'Start', 'C') ASC,
                     last_assessed ASC
            LIMIT %s
        ''', (project, limit))
        rows = cursor.fetchall()
        if not rows:
            print('No quality gaps found for this project.')
            sys.exit(0)
        print(f'{\"Article\":<55} {\"Class\":<8} {\"Import\":<8} {\"Bytes\":>8}  {\"Last assessed\"}')
        print('-' * 95)
        for r in rows:
            title = r['page_title'].decode('utf-8') if isinstance(r['page_title'], bytes) else r['page_title']
            assessed = r['last_assessed'].decode('utf-8')[:8] if r['last_assessed'] and isinstance(r['last_assessed'], bytes) else (str(r['last_assessed'] or '')[:8] if r['last_assessed'] else 'N/A')
            cls = r['pa_class'].decode('utf-8') if isinstance(r['pa_class'], bytes) else str(r['pa_class'] or '')
            imp = r['pa_importance'].decode('utf-8') if isinstance(r['pa_importance'], bytes) else str(r['pa_importance'] or '')
            byte_val = int(r['bytes']) if r['bytes'] is not None else 0
            print(f'{title:<55} {cls:<8} {imp:<8} {byte_val:>8,}  {assessed}')
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()
"
else
    # Fallback: mysql CLI (may fail on MySQL 9.x+)
    if ! command -v mysql &>/dev/null; then
        echo -e "${RED}❌ Neither pymysql nor mysql CLI available${NC}"
        echo "   Install pymysql: pip install pymysql python-dotenv"
        exit 1
    fi

    echo -e "${YELLOW}⚠️  pymysql not available, trying mysql CLI (may fail on MySQL 9.x)${NC}"

    SQL="SELECT p.page_title, pa.pa_class, pa.pa_importance,
           p.page_len AS bytes,
           rev.rev_timestamp AS last_assessed
    FROM page_assessments pa
    JOIN page_assessments_projects pap ON pa.pa_project_id = pap.pap_project_id
    JOIN page p ON pa.pa_page_id = p.page_id
    LEFT JOIN revision rev ON pa.pa_page_revision = rev.rev_id
    WHERE pap.pap_project_title = '${PROJECT}'
      AND p.page_namespace = 0
      AND p.page_is_redirect = 0
      AND pa.pa_class IN ('Stub', 'Start', 'C')
      AND pa.pa_importance IN ('Top', 'High')
      AND p.page_len > 0
    ORDER BY
      FIELD(pa.pa_importance, 'Top', 'High') ASC,
      FIELD(pa.pa_class, 'Stub', 'Start', 'C') ASC,
      rev.rev_timestamp ASC
    LIMIT ${LIMIT};"

    mysql -h 127.0.0.1 \
        -P "$LOCAL_PORT" \
        -u "${TOOLFORGE_SQL_USER}" \
        -p"${TOOLFORGE_SQL_PASSWORD}" \
        -D enwiki_p \
        -e "$SQL" \
        --table 2>&1 || {
            echo -e "${RED}❌ mysql CLI failed - authentication issue on MySQL 9.x${NC}"
            echo "   Install pymysql for compatibility:"
            echo "     pip install pymysql python-dotenv"
            exit 1
        }
fi
