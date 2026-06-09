#!/usr/bin/env bash
# Generate a MediaWiki wikitable from CSV data on stdin.
#
# Usage:
#   cat data.csv | ./generate-table.sh
#   echo "Name,Score\nAlice,95\nBob,87" | ./generate-table.sh --caption "Scores"
#   ./generate-table.sh < data.csv --classes "wikitable sortable mw-collapsible"

set -euo pipefail

CAPTION=""
CLASSES="wikitable sortable"

while [ $# -gt 0 ]; do
    case "$1" in
        --caption) CAPTION="$2"; shift 2 ;;
        --classes) CLASSES="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

INPUT=$(cat)

python3 -c "
import sys
sys.path.insert(0, 'assets')
from wikitable_tools import csv_to_wikitable

result = csv_to_wikitable(
    '''${INPUT//\'/\'\\\'\'}''',
    classes='${CLASSES}',
    caption='''${CAPTION//\'/\'\\\'\'}''',
)
print(result)
" 2>&1
