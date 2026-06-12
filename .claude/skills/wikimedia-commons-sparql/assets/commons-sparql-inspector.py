#!/usr/bin/env python3
"""
Commons SPARQL Inspector — Query Commons structured data via SPARQL.

Inspects Commons files by:
  - Looking up an M ID and returning its structured data
  - Finding files that depict a given Wikidata item
  - Showing copyright/license/camera metadata for a file
  - Listing files in a Commons category

Uses the QLever endpoint by default (no auth required).
Use --wcqs to use the official WCQS endpoint (requires env WCQS_AUTH_TOKEN).

Usage:
  python3 commons-sparql-inspector.py m:M37200540
  python3 commons-sparql-inspector.py depicts:Q42
  python3 commons-sparql-inspector.py category:"Bridges in Paris"
  python3 commons-sparql-inspector.py file:"Eiffel Tower from below.jpg"
  python3 commons-sparql-inspector.py --wcqs m:M37200540
"""

import argparse
import json
import os
import sys
from http.cookiejar import Cookie
from urllib.parse import urlparse

import requests


# --- Configuration ---

QL_URL = "https://qlever.dev/api/wikimedia-commons"
WCQS_URL = "https://commons-query.wikimedia.org/sparql"
UA = "CommonsSPARQLInspector/1.0 (https://example.com; user@example.com)"


def build_session(endpoint: str, wcqs_token: str | None = None) -> requests.Session:
    """Build a requests.Session for the given endpoint."""
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "application/sparql-results+json"})

    if endpoint == WCQS_URL and wcqs_token:
        domain = urlparse(endpoint).netloc
        session.cookies.set_cookie(
            Cookie(0, "wcqsOauth", wcqs_token, None, False,
                   domain, False, False, "/", True,
                   False, None, True, None, None, {})
        )

    return session


def run_query(session: requests.Session, endpoint: str, query: str) -> dict:
    """Execute a SPARQL query and return parsed JSON results."""
    if endpoint == QL_URL:
        resp = session.get(
            endpoint,
            params={"query": query},
            timeout=60,
        )
    else:
        resp = session.post(
            endpoint,
            data={"query": query},
            timeout=60,
            allow_redirects=True,
        )
    resp.raise_for_status()
    return resp.json()


def lookup_mid(session, endpoint, m_id: str):
    """Retrieve all structured data statements for an M ID."""
    query = f"""
    SELECT ?property ?value WHERE {{
      <http://commons.wikimedia.org/entity/{m_id}> ?property ?value .
      FILTER(
        STRSTARTS(STR(?property), "http://www.wikidata.org/prop/direct/") ||
        STRSTARTS(STR(?property), "http://schema.org/")
      )
    }}
    """
    data = run_query(session, endpoint, query)
    results = {}
    for binding in data["results"]["bindings"]:
        prop = binding["property"]["value"]
        val = binding["value"]["value"]
        label = prop.rsplit("/", 1)[-1]
        if label not in results:
            results[label] = []
        results[label].append(val)
    return results


def find_depicts(session, endpoint, q_id: str, limit: int = 20):
    """Find files that depict a given Wikidata item."""
    query = f"""
    #defaultView:ImageGrid
    SELECT ?file ?image WHERE {{
      ?file wdt:P180 wd:{q_id} ;
             schema:url ?image .
    }}
    LIMIT {limit}
    """
    data = run_query(session, endpoint, query)
    return data["results"]["bindings"]


def find_files_in_category(session, endpoint, category: str, limit: int = 50):
    """Find all files in a Commons category."""
    query = f"""
    SELECT ?title ?pageid WHERE {{
      SERVICE wikibase:mwapi {{
        bd:serviceParam wikibase:endpoint "commons.wikimedia.org";
                        wikibase:api "Generator";
                        mwapi:generator "categorymembers";
                        mwapi:gcmtype "file";
                        mwapi:gcmtitle "Category:{category}";
                        mwapi:gcmprop "title|pageid";
                        mwapi:gcmlimit "max".
        ?title wikibase:apiOutput mwapi:title .
        ?pageid wikibase:apiOutput "@pageid" .
      }}
    }}
    LIMIT {limit}
    """
    data = run_query(session, endpoint, query)
    results = []
    for binding in data["results"]["bindings"]:
        results.append({
            "title": binding["title"]["value"],
            "m_id": f"M{binding['pageid']['value']}",
        })
    return results


def lookup_file_by_title(session, endpoint, title: str):
    """Find the M ID for a file by its Commons page title."""
    # URL-decode if needed and construct the Special:FilePath URL
    from urllib.parse import quote
    file_url = f"http://commons.wikimedia.org/wiki/Special:FilePath/{quote(title)}"

    query = f"""
    SELECT ?file ?pageid ?width ?height ?encoding WHERE {{
      ?file schema:url <{file_url}> ;
            schema:contentUrl ?content .
      OPTIONAL {{ ?file schema:width ?width . }}
      OPTIONAL {{ ?file schema:height ?height . }}
      OPTIONAL {{ ?file schema:encodingFormat ?encoding . }}
    }}
    """
    data = run_query(session, endpoint, query)
    return data["results"]["bindings"]


def main():
    parser = argparse.ArgumentParser(
        description="Inspect Commons structured data via SPARQL"
    )
    parser.add_argument(
        "query",
        help=(
            "Query to run. Formats: "
            "m:M12345 (lookup M ID), "
            "depicts:Q42 (find files depicting Q42), "
            "category:\"Bridges in Paris\" (files in category), "
            "file:\"File.jpg\" (find by file title)"
        ),
    )
    parser.add_argument(
        "--wcqs", action="store_true",
        help="Use the official WCQS endpoint (requires WCQS_AUTH_TOKEN env var)"
    )
    parser.add_argument("--limit", type=int, default=20, help="Max results")
    args = parser.parse_args()

    if args.wcqs:
        token = os.environ.get("WCQS_AUTH_TOKEN")
        if not token:
            print("Error: --wcqs requires WCQS_AUTH_TOKEN environment variable", file=sys.stderr)
            sys.exit(1)
        endpoint = WCQS_URL
    else:
        token = None
        endpoint = QL_URL

    session = build_session(endpoint, token)
    q = args.query

    if q.startswith("m:"):
        m_id = q[2:]
        print(f"🔍 Looking up M ID: {m_id}")
        results = lookup_mid(session, endpoint, m_id)
        print(json.dumps(results, indent=2))

    elif q.startswith("depicts:"):
        q_id = q[8:]
        print(f"🔍 Files depicting {q_id}:")
        results = find_depicts(session, endpoint, q_id, args.limit)
        for r in results:
            file_uri = r["file"]["value"]
            m_id = file_uri.rsplit("/", 1)[-1]
            img_url = r.get("image", {}).get("value", "?")
            print(f"  {m_id} → {img_url}")

    elif q.startswith("category:"):
        cat = q[9:]
        print(f"🔍 Files in Category:{cat}:")
        results = find_files_in_category(session, endpoint, cat, args.limit)
        for r in results:
            print(f"  {r['m_id']}: {r['title']}")

    elif q.startswith("file:"):
        title = q[5:]
        print(f"🔍 Looking up file: {title}")
        results = lookup_file_by_title(session, endpoint, title)
        if not results:
            print("  No results found")
        for r in results:
            file_uri = r["file"]["value"]
            m_id = file_uri.rsplit("/", 1)[-1]
            w = r.get("width", {}).get("value", "?")
            h = r.get("height", {}).get("value", "?")
            enc = r.get("encoding", {}).get("value", "?")
            print(f"  {m_id}")
            print(f"  Dimensions: {w}×{h}")
            print(f"  Format: {enc}")

    else:
        print(f"Running raw SPARQL query...")
        data = run_query(session, endpoint, q)
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
