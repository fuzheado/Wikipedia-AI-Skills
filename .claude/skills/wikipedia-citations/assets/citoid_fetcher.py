#!/usr/bin/env python3
"""Fetch citation metadata via Citoid API and convert to wiki templates.

Accepts URLs, DOIs, ISBNs, PMIDs. Outputs CS1 citation templates,
raw Citoid data (Zotero JSON), or structured metadata.

Usage:
    python3 citoid_fetcher.py https://example.com/article
    python3 citoid_fetcher.py 10.7554/eLife.32259
    python3 citoid_fetcher.py 978-0-262-52316-5 --raw
    python3 citoid_fetcher.py urls.txt --batch          # one URL per line
    python3 citoid_fetcher.py https://example.com --wiki  # output as <ref>...</ref>
"""

import argparse
import json
import sys
import time
import urllib.parse

import requests


USER_AGENT = "CitoidFetcher/1.0 (user@example.com) ContentGapResearch"
CITOID_API = "https://en.wikipedia.org/api/rest_v1/data/citation/zotero/{input}"

# Map Citoid item types to CS1 template names
TYPE_MAP = {
    "journalArticle": "cite journal",
    "book": "cite book",
    "bookSection": "cite book",
    "newspaperArticle": "cite news",
    "magazineArticle": "cite magazine",
    "webpage": "cite web",
    "report": "cite report",
    "thesis": "cite thesis",
    "conferencePaper": "cite conference",
    "patent": "cite patent",
    "film": "cite AV media",
    "podcast": "cite podcast",
    "interview": "cite interview",
    "map": "cite map",
    "manuscript": "cite thesis",
    "audioRecording": "cite AV media",
    "videoRecording": "cite AV media",
    "tvBroadcast": "cite episode",
    "radioBroadcast": "cite episode",
    "presentation": "cite conference",
    "email": "cite web",
    "letter": "cite web",
    "statute": "cite legislation",
    "bill": "cite legislation",
    "case": "cite court",
    "hearing": "cite court",
    "patent": "cite patent",
    "statute": "cite web",
    "encyclopediaArticle": "cite encyclopedia",
    "dictionaryEntry": "cite encyclopedia",
    "document": "cite web",
}


def guess_input_type(raw: str) -> str:
    """Guess whether input is a URL, DOI, ISBN, or plain text."""
    raw = raw.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return "url"
    if raw.startswith("10.") or "/" in raw[:10]:
        return "doi"
    cleaned = raw.replace("-", "")
    if cleaned.isdigit() and len(cleaned) in (10, 13):
        return "isbn"
    return "url"


def fetch_citoid(input_str: str) -> list[dict] | None:
    """Fetch citation data from Citoid."""
    input_type = guess_input_type(input_str)

    if input_type == "url":
        encoded = urllib.parse.quote(input_str, safe="")
    else:
        encoded = urllib.parse.quote(input_str, safe="")

    url = CITOID_API.format(input=encoded)
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"⚠  Error: {e}", file=sys.stderr)
        return None


def citoid_to_template(citation: dict, as_ref: bool = False) -> str:
    """Convert a Citoid citation to a CS1 template string."""
    item_type = citation.get("itemType", "webpage")
    url = citation.get("url", "")
    title = citation.get("title", "")
    date = citation.get("date", "")
    access_date = citation.get("accessDate", "")

    template = TYPE_MAP.get(item_type, "cite web")

    parts = [f"{{{{{template}}}"]
    if url:
        parts.append(f" |url={url}")
    if title:
        parts.append(f" |title={title}")
    if date:
        parts.append(f" |date={date}")
    if access_date:
        parts.append(f" |access-date={access_date}")

    # Authors
    authors = citation.get("author", [])
    for i, (last, first) in enumerate(authors, 1):
        if i == 1:
            parts.append(f" |last={last} |first={first}")
        else:
            parts.append(f" |last{i}={last} |first{i}={first}")

    # Type-specific fields
    if template == "cite journal":
        journal = citation.get("publicationTitle") or citation.get("journalTitle", "")
        if journal:
            parts.append(f" |journal={journal}")
        volume = citation.get("volume", "")
        if volume:
            parts.append(f" |volume={volume}")
        issue = citation.get("issue", "")
        if issue:
            parts.append(f" |issue={issue}")
        pages = citation.get("pages", "")
        if pages:
            parts.append(f" |pages={pages}")
        doi = citation.get("DOI", "")
        if doi:
            parts.append(f" |doi={doi}")
        pmid = citation.get("PMID", "")
        if pmid:
            parts.append(f" |pmid={pmid}")

    if template == "cite news":
        newspaper = citation.get("publicationTitle", "")
        if newspaper:
            parts.append(f" |newspaper={newspaper}")

    if template == "cite web":
        website = citation.get("websiteTitle", "") or citation.get("publisher", "")
        if website:
            parts.append(f" |website={website}")

    if template in ("cite book",):
        publisher = citation.get("publisher", "")
        if publisher:
            parts.append(f" |publisher={publisher}")
        isbn_list = citation.get("ISBN", [])
        if isbn_list and isbn_list[0]:
            parts.append(f" |isbn={isbn_list[0]}")
        edition = citation.get("edition", "")
        if edition:
            parts.append(f" |edition={edition}")

    parts.append("}}")

    result = "\n".join(parts)
    if as_ref:
        result = f"<ref>{result}</ref>"
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Fetch citation metadata via Citoid API",
    )
    parser.add_argument("input", help="URL, DOI, ISBN, PMID, or file path with --batch")
    parser.add_argument("--raw", action="store_true", help="Output raw Citoid JSON")
    parser.add_argument("--wiki", action="store_true", help="Wrap in <ref>...</ref> tags")
    parser.add_argument("--batch", action="store_true", help="Input is a file with one identifier per line")
    parser.add_argument("--delay", type=float, default=0.5, help="Seconds between batch requests")

    args = parser.parse_args()

    if args.batch:
        with open(args.input) as f:
            inputs = [line.strip() for line in f if line.strip()]
    else:
        inputs = [args.input]

    for i, input_str in enumerate(inputs):
        if args.batch:
            print(f"[{i+1}/{len(inputs)}] {input_str}", file=sys.stderr)

        data = fetch_citoid(input_str)
        if data is None:
            print(f"❌ {input_str}: No data\n")
            continue

        if args.raw:
            print(json.dumps(data, indent=2, default=str))
        elif args.wiki:
            if not data:
                print(f"<!-- {input_str}: no results -->")
            else:
                print(citoid_to_template(data[0], as_ref=True))
        else:
            if not data:
                print(f"<!-- {input_str}: no results -->")
            else:
                print(citoid_to_template(data[0]))
            print()

        if i < len(inputs) - 1:
            time.sleep(args.delay)


if __name__ == "__main__":
    main()
