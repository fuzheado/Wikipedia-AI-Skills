#!/usr/bin/env python3
"""
Parsoid HTML Extractor — fetch and extract data from Wikipedia pages via the
MediaWiki REST API HTML endpoint.

Usage:
    python3 parsoid-extractor.py "Python (programming language)" --tables
    python3 parsoid-extractor.py "Albert Einstein" --sections
    python3 parsoid-extractor.py "Berlin" --infobox
    python3 parsoid-extractor.py "Machine learning" --links
    python3 parsoid-extractor.py "France" --all --format json

Dependencies: pip install requests beautifulsoup4 lxml pandas
"""

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ requests not installed. Install: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ beautifulsoup4 not installed. Install: pip install beautifulsoup4 lxml")
    sys.exit(1)


USER_AGENT = "WikitextSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)"
BASE_URL = "https://en.wikipedia.org/w/rest.php/v1/page"


def fetch_page_html(title: str) -> str:
    """Fetch the Parsoid-rendered HTML for a Wikipedia page."""
    encoded = urllib.parse.quote(title.replace(" ", "_"))
    url = f"{BASE_URL}/{encoded}/html"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": 'text/html; charset=utf-8; profile="https://www.mediawiki.org/wiki/Specs/HTML/2.1.0"',
    }

    resp = requests.get(url, headers=headers, timeout=30)

    if resp.status_code == 200:
        return resp.text
    elif resp.status_code == 404:
        print(f"❌ Page not found: {title}")
        sys.exit(1)
    elif resp.status_code == 429:
        retry = resp.headers.get("Retry-After", "unknown")
        print(f"❌ Rate limited. Retry after {retry} seconds.")
        sys.exit(1)
    else:
        print(f"❌ HTTP {resp.status_code}: {resp.reason}")
        sys.exit(1)


def extract_tables(soup):
    """Extract all HTML tables as list-of-dicts."""
    import pandas as pd

    try:
        tables = pd.read_html(str(soup))
    except ValueError:
        return []

    result = []
    for i, df in enumerate(tables):
        result.append({
            "index": i,
            "shape": list(df.shape),
            "columns": list(df.columns),
            "data": df.head(50).to_dict(orient="records"),
        })
    return result


def extract_sections(soup):
    """Extract sections with their headings and text content."""
    sections = {}
    current_heading = "lead"
    current_parts = []

    # Find all mw-heading divs
    for heading_div in soup.find_all("div", class_=lambda c: c and "mw-heading" in c):
        # Save previous section
        sections[current_heading] = "".join(current_parts).strip()

        h_tag = heading_div.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        current_heading = h_tag.get_text(strip=True) if h_tag else "unknown"
        current_parts = []

        # Collect siblings until next heading
        for sibling in heading_div.find_next_siblings():
            if sibling.get("class") and any(
                "mw-heading" in (c or "") for c in sibling.get("class", [])
            ):
                break
            current_parts.append(str(sibling))

    # Save last section
    sections[current_heading] = "".join(current_parts).strip()

    # Filter empty sections and convert to plain text
    result = {}
    for heading, html in sections.items():
        if html:
            text = BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)
            result[heading] = text[:2000]  # Truncate
    return result


def extract_infobox(soup):
    """Extract data from the infobox table."""
    infobox = soup.find("table", class_="infobox")
    if not infobox:
        return None

    rows = infobox.find_all("tr")
    data = {}
    for row in rows:
        header = row.find("th")
        cell = row.find("td")
        if header and cell:
            key = header.get_text(strip=True)
            # Remove footnote links
            for sup in cell.find_all("sup"):
                sup.decompose()
            value = cell.get_text(separator=" ", strip=True)
            data[key] = value
        elif header and not cell:
            # Caption-only row (e.g., image row)
            pass
    return data


def extract_links(soup):
    """Extract internal and external links."""
    return {
        "internal": [
            {"href": a.get("href"), "text": a.get_text(strip=True)}
            for a in soup.select('a[rel="mw:WikiLink"]')
        ],
        "external": [
            {"href": a.get("href"), "text": a.get_text(strip=True)}
            for a in soup.select('a[rel="mw:ExtLink"]')
        ],
    }


def main():
    parser = argparse.ArgumentParser(description="Extract data from Wikipedia via Parsoid HTML")
    parser.add_argument("title", help="Wikipedia page title")
    parser.add_argument("--tables", action="store_true", help="Extract tables")
    parser.add_argument("--sections", action="store_true", help="Extract sections")
    parser.add_argument("--infobox", action="store_true", help="Extract infobox data")
    parser.add_argument("--links", action="store_true", help="Extract links")
    parser.add_argument("--all", action="store_true", help="Run all extractions")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--project", default="en.wikipedia.org",
                        help="Wikimedia project (default: en.wikipedia.org)")
    parser.add_argument("--save", help="Save raw HTML to file")

    args = parser.parse_args()

    # Override BASE_URL if a different project is specified
    global BASE_URL
    BASE_URL = f"https://{args.project}/w/rest.php/v1/page"

    # Fetch HTML
    print(f"📄 Fetching: {args.title} on {args.project}...", file=sys.stderr)
    html = fetch_page_html(args.title)

    if args.save:
        Path(args.save).write_text(html, encoding="utf-8")
        print(f"💾 HTML saved to: {args.save}", file=sys.stderr)

    soup = BeautifulSoup(html, "html.parser")
    results = {"title": args.title, "url": f"https://{args.project}/wiki/{args.title.replace(' ', '_')}"}

    if args.all or args.tables:
        results["tables"] = extract_tables(soup)
    if args.all or args.sections:
        results["sections"] = extract_sections(soup)
    if args.all or args.infobox:
        results["infobox"] = extract_infobox(soup)
    if args.all or args.links:
        results["links"] = extract_links(soup)

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for key, value in results.items():
            if key == "title" or key == "url":
                continue
            print(f"\n{'=' * 60}")
            print(f"  {key.upper()}")
            print(f"{'=' * 60}")
            if isinstance(value, list):
                print(f"  Count: {len(value)}")
                for item in value[:5]:
                    print(f"  - {json.dumps(item, ensure_ascii=False)[:200]}")
                if len(value) > 5:
                    print(f"  ... and {len(value) - 5} more")
            elif isinstance(value, dict):
                for k, v in value.items():
                    print(f"  {k}: {str(v)[:100]}")
            elif value is None:
                print("  (not found)")


if __name__ == "__main__":
    main()
