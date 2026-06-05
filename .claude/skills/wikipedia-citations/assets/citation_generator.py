#!/usr/bin/env python3
"""Interactive CLI to generate Wikipedia citation templates.

Prompts for source metadata and generates the appropriate CS1 template.

Usage:
    python3 citation_generator.py
    python3 citation_generator.py --type web
    python3 citation_generator.py --url https://example.com --title "My Title"
"""

import argparse
import sys


def generate_cite_web(**kwargs) -> str:
    parts = ["{{cite web"]
    for key in ["url", "title", "website", "last", "first", "date", "access-date",
                "publisher", "language", "archive-url", "archive-date", "url-status", "quote"]:
        if kwargs.get(key):
            parts.append(f" |{key}={kwargs[key]}")
    parts.append("}}")
    return "\n".join(parts)


def generate_cite_news(**kwargs) -> str:
    parts = ["{{cite news"]
    for key in ["url", "title", "last", "first", "date", "work", "newspaper",
                "publisher", "pages", "access-date", "archive-url", "archive-date"]:
        if kwargs.get(key):
            parts.append(f" |{key}={kwargs[key]}")
    parts.append("}}")
    return "\n".join(parts)


def generate_cite_book(**kwargs) -> str:
    parts = ["{{cite book"]
    for key in ["title", "last", "first", "author", "date", "year", "publisher",
                "location", "isbn", "oclc", "pages", "page", "edition", "volume",
                "url", "access-date", "language"]:
        if kwargs.get(key):
            parts.append(f" |{key}={kwargs[key]}")
    parts.append("}}")
    return "\n".join(parts)


def generate_cite_journal(**kwargs) -> str:
    parts = ["{{cite journal"]
    for key in ["title", "last", "first", "author", "date", "year", "journal",
                "volume", "issue", "pages", "doi", "pmid", "pmc", "url",
                "access-date", "language"]:
        if kwargs.get(key):
            parts.append(f" |{key}={kwargs[key]}")
    parts.append("}}")
    return "\n".join(parts)


GENERATORS = {
    "web": ("cite web", generate_cite_web),
    "news": ("cite news", generate_cite_news),
    "book": ("cite book", generate_cite_book),
    "journal": ("cite journal", generate_cite_journal),
}

FIELDS = {
    "web": ["url", "title", "website", "last", "first", "date", "access-date"],
    "news": ["url", "title", "last", "first", "date", "newspaper"],
    "book": ["title", "author", "year", "publisher", "isbn", "pages"],
    "journal": ["title", "author", "journal", "volume", "pages", "doi", "year"],
}


def interactive():
    """Interactive mode — ask the user what to generate."""
    print("📝 Citation Template Generator")
    print("═" * 40)
    print("Choose source type:")
    for key, (name, _) in GENERATORS.items():
        print(f"  {key}) {name}")
    print()

    while True:
        choice = input("Type (web/news/book/journal) [web]: ").strip().lower() or "web"
        if choice in GENERATORS:
            break
        print(f"Invalid choice. Choose from: {', '.join(GENERATORS.keys())}")

    tmpl_name, generator = GENERATORS[choice]
    print(f"\nEnter fields for {tmpl_name}. Press Enter to skip optional fields.\n")

    kwargs = {}
    for field in FIELDS[choice]:
        value = input(f"  {field}: ").strip()
        if value:
            kwargs[field] = value

    # Optional fields
    print("\nOptional fields (press Enter to skip):")
    archive_url = input("  archive-url: ").strip()
    if archive_url:
        kwargs["archive-url"] = archive_url
        kwargs["archive-date"] = input("  archive-date: ").strip()
        kwargs["url-status"] = input("  url-status (live/dead/unfit) [live]: ").strip() or "live"

    doi = input("  doi: ").strip()
    if doi:
        kwargs["doi"] = doi

    print("\n" + "═" * 40)
    print("Generated template:")
    print("═" * 40)
    print(generator(**kwargs))
    print("═" * 40)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Wikipedia citation templates",
    )
    parser.add_argument("--type", choices=list(GENERATORS.keys()), help="Citation type")
    parser.add_argument("--url")
    parser.add_argument("--title")
    parser.add_argument("--author")
    parser.add_argument("--last")
    parser.add_argument("--first")
    parser.add_argument("--date")
    parser.add_argument("--year")
    parser.add_argument("--publisher")
    parser.add_argument("--website")
    parser.add_argument("--journal")
    parser.add_argument("--newspaper")
    parser.add_argument("--volume")
    parser.add_argument("--issue")
    parser.add_argument("--pages")
    parser.add_argument("--isbn")
    parser.add_argument("--doi")
    parser.add_argument("--access-date")
    parser.add_argument("--archive-url")
    parser.add_argument("--archive-date")

    args = parser.parse_args()

    if args.type:
        kwargs = {k: v for k, v in vars(args).items() if v is not None and k != "type"}
        tmpl_name, generator = GENERATORS[args.type]
        print(generator(**kwargs))
    else:
        interactive()


if __name__ == "__main__":
    main()
