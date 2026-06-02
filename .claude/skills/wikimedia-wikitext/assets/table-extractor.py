#!/usr/bin/env python3
"""
Table Extractor — convert Wikipedia tables to pandas DataFrames via the
Parsoid HTML pipeline, with CSV/JSON export.

The key principle: never parse wikitext table syntax ({| ... |}) manually.
Always use the Parsoid HTML endpoint and let pandas.read_html() do the work.

Usage:
    python3 table-extractor.py "List of countries by GDP (nominal)"
    python3 table-extractor.py "List of countries by GDP (nominal)" --csv
    python3 table-extractor.py "List of countries by GDP (nominal)" --json
    python3 table-extractor.py "List of capitals" --table 2 --csv output.csv

Dependencies: pip install requests beautifulsoup4 lxml pandas
"""

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

try:
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"❌ Missing dependency: {e.name}")
    print("   Install: pip install requests beautifulsoup4 lxml pandas")
    sys.exit(1)


USER_AGENT = "WikitextSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)"
BASE_URL = "https://en.wikipedia.org/w/rest.php/v1/page"


def fetch_page_html(title: str) -> str:
    """Fetch Parsoid HTML for a Wikipedia page."""
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    url = f"{BASE_URL}/{encoded}/html"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": 'text/html; charset=utf-8; profile="https://www.mediawiki.org/wiki/Specs/HTML/2.1.0"',
    }

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"❌ HTTP {resp.status_code}: {resp.reason}")
        sys.exit(1)
    return resp.text


def extract_tables(html: str, table_index: int = None):
    """Extract tables from Parsoid HTML using pandas.read_html()."""
    soup = BeautifulSoup(html, "html.parser")

    # pandas.read_html works on <table> elements
    tables = pd.read_html(str(soup))

    if not tables:
        print("❌ No tables found on this page.")
        sys.exit(1)

    if table_index is not None:
        if table_index < 0 or table_index >= len(tables):
            print(f"❌ Table index {table_index} out of range (0-{len(tables) - 1})")
            sys.exit(1)
        tables = [tables[table_index]]

    return tables


def main():
    parser = argparse.ArgumentParser(
        description="Extract Wikipedia tables as DataFrames via Parsoid HTML"
    )
    parser.add_argument("title", help="Wikipedia page title")
    parser.add_argument("--table", type=int, default=None,
                        help="Table index to extract (default: all)")
    parser.add_argument("--csv", action="store_true",
                        help="Export as CSV files")
    parser.add_argument("--json", action="store_true",
                        help="Export as JSON files")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output file path (for single-table export)")
    parser.add_argument("--project", default="en.wikipedia.org",
                        help="Wikimedia project (default: en.wikipedia.org)")

    args = parser.parse_args()

    # Override BASE_URL if a different project is specified
    global BASE_URL
    BASE_URL = f"https://{args.project}/w/rest.php/v1/page"

    # Fetch
    print(f"📄 Fetching: {args.title}", file=sys.stderr)
    html = fetch_page_html(args.title)

    # Extract
    tables = extract_tables(html, args.table)

    # Display
    for i, df in enumerate(tables):
        table_num = args.table if args.table is not None else i
        print(f"\n{'=' * 60}")
        print(f"  Table {table_num}: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"{'=' * 60}")

        # Clean column names for display
        df_clean = df.copy()
        df_clean.columns = [str(c).replace("\n", " ") for c in df_clean.columns]

        # Show first 10 rows
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 120)
        pd.set_option("display.max_colwidth", 40)
        print(df_clean.head(10).to_string(index=False))

        if len(df) > 10:
            print(f"\n  ... ({len(df) - 10} more rows)")

        # Export
        base_name = args.output or f"table_{table_num}"

        if args.csv:
            csv_path = f"{base_name}.csv" if args.table is not None else f"table_{table_num}.csv"
            df.to_csv(csv_path, index=False)
            print(f"💾 Saved: {csv_path}", file=sys.stderr)

        if args.json:
            json_path = f"{base_name}.json" if args.table is not None else f"table_{table_num}.json"
            df.to_json(json_path, orient="records", indent=2, force_ascii=False)
            print(f"💾 Saved: {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
