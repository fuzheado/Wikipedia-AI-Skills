#!/usr/bin/env python3
"""
Wikimedia Commons File Inspector

Fetches and displays metadata for a Commons file:
license, author, categories, usage across wikis, and EXIF data.

Usage:
    python3 commons-file-inspector.py "File:Penguins_Logo.svg"
    python3 commons-file-inspector.py "Eiffel Tower" --search
"""

import json
import sys
import requests
import argparse

USER_AGENT = "CommonsFileInspector/1.0 (https://commons.wikimedia.org; demo@example.com) WMSkills"
API_URL = "https://commons.wikimedia.org/w/api.php"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


def search_files(query, limit=10):
    """Search for files on Commons by query string."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": 6,
        "srlimit": limit,
        "format": "json",
    }
    resp = SESSION.get(API_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    return [r["title"] for r in data.get("query", {}).get("search", [])]


def get_file_metadata(title):
    """Fetch extended metadata for a single file."""
    params = {
        "action": "query",
        "prop": "imageinfo|categories|globalusage",
        "iiprop": "url|user|extmetadata|size|mime|timestamp",
        "titles": title,
        "format": "json",
    }
    resp = SESSION.get(API_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", {})
    for page_id, page_data in pages.items():
        return page_data
    return None


def format_size(bytes_val):
    """Human-readable file size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def display_file_info(data):
    """Print beautifully formatted file metadata."""
    title = data.get("title", "Unknown")
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

    imageinfo = data.get("imageinfo", [])
    if imageinfo:
        info = imageinfo[0]
        print(f"\n  📄 Basic Info")
        print(f"     MIME type:  {info.get('mime', 'N/A')}")
        print(f"     Size:       {format_size(info.get('size', 0))}")
        print(f"     Width:      {info.get('width', 'N/A')} px")
        print(f"     Height:     {info.get('height', 'N/A')} px")
        print(f"     Uploader:   {info.get('user', 'N/A')}")
        print(f"     Uploaded:   {info.get('timestamp', 'N/A')}")
        print(f"     URL:        {info.get('descriptionurl', 'N/A')}")

        extmeta = info.get("extmetadata", {})
        if extmeta:
            print(f"\n  📋 License & Attribution")
            for field in ["LicenseShortName", "LicenseUrl", "Artist", "Credit", "Copyrighted"]:
                val = extmeta.get(field, {})
                if isinstance(val, dict):
                    val = val.get("value", "")
                if val:
                    label = field.replace("LicenseShortName", "License")
                    label = label.replace("LicenseUrl", "License URL")
                    label = label.replace("Copyrighted", "Copyrighted?")
                    print(f"     {label}: {val}")
    else:
        print("\n  ⚠️  No imageinfo found. Is this a valid file title?")

    categories = data.get("categories", [])
    if categories:
        print(f"\n  🏷️  Categories ({len(categories)})")
        for cat in categories[:15]:
            print(f"     • {cat.get('title', 'N/A')}")
        if len(categories) > 15:
            print(f"     ... and {len(categories) - 15} more")

    usage = data.get("globalusage", [])
    if usage:
        print(f"\n  🌐 Used on {len(usage)} wiki(s)")
        for use in usage[:10]:
            print(f"     • {use.get('wiki', 'N/A')}: {use.get('title', 'N/A')}")
        if len(usage) > 10:
            print(f"     ... and {len(usage) - 10} more")

    print()


def main():
    parser = argparse.ArgumentParser(description="Inspect metadata for a Wikimedia Commons file")
    parser.add_argument("query", help="File title (e.g., 'File:Penguins_Logo.svg') or search query")
    parser.add_argument("--search", "-s", action="store_true", help="Treat query as a search term")
    args = parser.parse_args()

    if args.search:
        print(f"🔍 Searching Commons for '{args.query}'...")
        results = search_files(args.query)
        if not results:
            print("No files found.")
            return
        print(f"Found {len(results)} file(s). Inspecting each...\n")
        for title in results:
            data = get_file_metadata(title)
            if data:
                display_file_info(data)
    else:
        data = get_file_metadata(args.query)
        if data:
            display_file_info(data)
        else:
            print(f"File '{args.query}' not found.")
            sys.exit(1)


if __name__ == "__main__":
    main()
