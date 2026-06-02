#!/usr/bin/env python3
"""
Wikitext Parser — extract templates, links, and plain text from MediaWiki wikitext.

Usage:
    python3 parse-wikitext.py page.wikitext --templates
    python3 parse-wikitext.py page.wikitext --links
    python3 parse-wikitext.py page.wikitext --plaintext
    python3 parse-wikitext.py page.wikitext --infobox
    python3 parse-wikitext.py page.wikitext --sections
    python3 parse-wikitext.py page.wikitext --citations
    python3 parse-wikitext.py page.wikitext --all

Dependencies: pip install mwparserfromhell
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import mwparserfromhell
except ImportError:
    print("❌ mwparserfromhell not installed.")
    print("   Install: pip install mwparserfromhell")
    sys.exit(1)


def load_wikitext(path: str) -> str:
    """Read wikitext from a file or stdin."""
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def extract_templates(code):
    """Extract all template calls with their parameters."""
    results = []
    for template in code.filter_templates():
        entry = {
            "name": str(template.name).strip(),
            "params": [],
        }
        for param in template.params:
            entry["params"].append({
                "name": str(param.name).strip(),
                "value": str(param.value).strip(),
            })
        results.append(entry)
    return results


def extract_links(code):
    """Extract all internal wikilinks ([[...]])."""
    links = []
    for link in code.filter_wikilinks():
        title = str(link.title).strip()
        text = str(link.text).strip() if link.text else None
        # Skip categories, files, interlanguage links
        if not title.startswith(("Category:", "File:", "Image:", ":")):
            links.append({"title": title, "display": text})
    return links


def extract_infobox(code):
    """Extract data from the first Infobox template found."""
    for template in code.filter_templates():
        name = str(template.name).strip()
        if name.startswith("Infobox"):
            data = {}
            for param in template.params:
                key = str(param.name).strip()
                value = str(param.value).strip()
                data[key] = value
            return {"type": name, "data": data}
    return None


def extract_sections(code):
    """Split wikitext into sections by heading."""
    sections = {}
    current_heading = "lead"
    current_content = []

    for node in code.nodes:
        if isinstance(node, mwparserfromhell.nodes.Heading):
            # Save previous section
            sections[current_heading] = "\n".join(current_content).strip()
            current_heading = str(node.title).strip()
            current_content = []
        else:
            current_content.append(str(node))

    # Save last section
    sections[current_heading] = "\n".join(current_content).strip()

    # Remove empty sections
    return {k: v for k, v in sections.items() if v}


def extract_citations(code):
    """Extract <ref> tag contents."""
    citations = []
    for tag in code.filter_tags():
        if hasattr(tag, "tag") and str(tag.tag).lower() == "ref":
            content = str(tag.contents).strip() if tag.contents else ""
            attribs = {}
            if tag.attributes:
                for attr in tag.attributes:
                    attribs[str(attr.name)] = str(attr.value)
            citations.append({"attributes": attribs, "content": content})
    return citations


def main():
    parser = argparse.ArgumentParser(description="Parse MediaWiki wikitext")
    parser.add_argument("file", help="Path to .wikitext file (or '-' for stdin)")
    parser.add_argument("--templates", action="store_true", help="Extract all templates")
    parser.add_argument("--links", action="store_true", help="Extract internal wikilinks")
    parser.add_argument("--plaintext", action="store_true", help="Convert to plain text")
    parser.add_argument("--infobox", action="store_true", help="Extract Infobox data")
    parser.add_argument("--sections", action="store_true", help="Split into sections")
    parser.add_argument("--citations", action="store_true", help="Extract citation refs")
    parser.add_argument("--all", action="store_true", help="Run all extractions")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")

    args = parser.parse_args()

    # Load wikitext
    try:
        wikitext = load_wikitext(args.file)
    except FileNotFoundError:
        print(f"❌ File not found: {args.file}")
        sys.exit(1)

    code = mwparserfromhell.parse(wikitext)
    results = {}

    if args.all or args.templates:
        results["templates"] = extract_templates(code)
    if args.all or args.links:
        results["links"] = extract_links(code)
    if args.all or args.plaintext:
        results["plaintext"] = code.strip_code()
    if args.all or args.infobox:
        results["infobox"] = extract_infobox(code)
    if args.all or args.sections:
        results["sections"] = extract_sections(code)
    if args.all or args.citations:
        results["citations"] = extract_citations(code)

    if args.format == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for key, value in results.items():
            print(f"\n{'=' * 60}")
            print(f"  {key.upper()}")
            print(f"{'=' * 60}")
            if isinstance(value, str):
                print(value[:2000])  # Truncate long output
                if len(value) > 2000:
                    print("  ... (truncated)")
            elif isinstance(value, list):
                print(f"  Count: {len(value)}")
                for item in value[:20]:  # Limit to 20 items
                    print(f"  - {json.dumps(item, ensure_ascii=False)}")
                if len(value) > 20:
                    print(f"  ... and {len(value) - 20} more")
            elif value is None:
                print("  (not found)")
            else:
                print(json.dumps(value, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
