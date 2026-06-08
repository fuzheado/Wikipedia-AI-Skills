#!/usr/bin/env python3
"""
Template Scanner — Scan a Wikipedia page for all template usage, classified by type.

Fetches a page's templates via the Action API, then classifies each one
by its purpose (infobox, citation, navbox, maintenance, stub, banner, etc.).

Usage:
    python3 template-scanner.py "Albert Einstein"
    python3 template-scanner.py "Berlin" --by-type
    python3 template-scanner.py "Python (programming language)" --format json
    python3 template-scanner.py "Berlin" --modules
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from urllib.parse import urlencode
from urllib.request import urlopen, Request


# --- Configuration ---------------------------------------------------------

DEFAULT_WIKI = "https://en.wikipedia.org"
USER_AGENT = os.environ.get(
    "WIKIMEDIA_USER_AGENT",
    "WikipediaTemplatesSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch",
)

# Template type classification by name patterns
TYPE_PATTERNS = {
    "infobox": [
        r"^Infobox\b", r"^Taxobox\b", r"^Infobox\s",
    ],
    "citation": [
        r"^Cite\b", r"^Citation\b", r"^Sfn\b", r"^Harv\w+\b",
        r"^Full citation needed\b", r"^Failed verification\b",
    ],
    "navbox": [
        r"^Navbox\b", r"^Sidebar\b", r"^Series\b", r"^Subject bar\b",
        r"^Portal bar\b", r"^Authority control\b", r"^Sister project\b",
    ],
    "maintenance": [
        r"^Cn\b", r"^Citation needed\b", r"^Clarify\b",
        r"^(When|Where|Who)\b", r"^According to whom\b",
        r"^Dubious\b", r"^POV\b", r"^Original research\b",
        r"^Better source\b", r"^Primary source\b",
        r"^Self-published source\b", r"^Third-party\b",
        r"^Dead link\b", r"^Expand section\b",
        r"^Empty section\b", r"^Refimprove\b",
        r"^More citations needed\b", r"^One source\b",
        r"^Cleanup\b", r"^Update\b", r"^In use\b",
        r"^Under construction\b", r"^Unreferenced\b",
    ],
    "hatnote": [
        r"^About\b", r"^For\b", r"^Distinguish\b", r"^Redirect\b",
        r"^Other uses\b", r"^See also\b", r"^Main\b", r"^Further\b",
    ],
    "stub": [
        r".*stub$",
    ],
    "banner": [
        r"^WikiProject\b", r"^ArticleHistory\b", r"^GA nominee\b",
        r"^Peer review\b", r"^DYK\b", r"^Annual report\b",
    ],
    "date_and_format": [
        r"^(Start|End) date\b", r"^(Birth|Death) date\b",
        r"^Age\b", r"^Years or months ago\b",
        r"^Convert\b", r"^Format price\b", r"^Ordinal\b",
        r"^Lang\b", r"^Lang-\w+$", r"^Abbr\b",
    ],
    "structural": [
        r"^TOC\b", r"^Clear\b", r"^-$", r"^Stack\b",
        r"^Column", r"^Div col\b", r"^Ordered list\b",
    ],
    "media": [
        r"^Listen\b", r"^Multiple image\b", r"^Superimpose\b",
        r"^Image label\b", r"^External media\b", r"^Commons\b",
        r"^Wikiquote\b", r"^Wiktionary\b", r"^Wikisource\b",
    ],
    "user_talk": [
        r"^Welcome\b", r"^Uw-\w+", r"^Reply to\b",
        r"^Ping\b", r"^Outdent\b", r"^Unsigned\b",
    ],
    "template_doc": [
        r"^Documentation\b", r"^TemplateData\b", r"^Sandbox other\b",
        r"^Para\b", r"^Template shortcut\b",
    ],
    "module": [
        r"^#invoke\b",  # This won't match template names, used for ns=828 items
    ],
}

# Some templates are known to be Lua-backed
LUA_BACKED = {
    "Infobox settlement", "Infobox royalty", "Infobox sportsperson",
    "Infobox ship", "Infobox video game", "Infobox television",
    "Navbox", "Navbox with collapsible groups", "Navbox musical artist",
    "Cite web", "Cite news", "Cite book", "Cite journal",
    "Authority control", "Sfn", "Harvnb", "Sfnp",
}


# --- API Helpers -----------------------------------------------------------

def api_call(params, wiki=DEFAULT_WIKI):
    """Make an Action API call and return the parsed JSON response."""
    params["format"] = "json"
    url = f"{wiki}/w/api.php?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def classify_template_name(template_name):
    """Classify a template by name pattern."""
    # Strip namespace prefix
    name = template_name
    if ":" in name:
        name = name.split(":", 1)[1]

    for type_name, patterns in TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return type_name

    return "other"


def is_lua_backed(template_name):
    """Check if a template name is known to be Lua-backed."""
    name = template_name
    if ":" in name:
        name = name.split(":", 1)[1]
    return name in LUA_BACKED


# --- Scanning Functions ----------------------------------------------------

def scan_page_templates(page_title, wiki=DEFAULT_WIKI):
    """Fetch all templates used on a page and classify them."""
    data = api_call({
        "action": "query",
        "prop": "templates",
        "titles": page_title,
    }, wiki)

    pages = data.get("query", {}).get("pages", {})
    for pid, pdata in pages.items():
        if pid == "-1":
            return {"exists": False, "title": page_title}
        templates = pdata.get("templates", [])
        return {
            "exists": True,
            "title": pdata.get("title", page_title),
            "pageid": int(pid),
            "templates": templates,
        }
    return {"exists": False, "title": page_title}


def classify_all(templates):
    """Classify a list of templates and organize by type."""
    by_type = defaultdict(list)
    module_templates = []
    other_templates = []

    for t in templates:
        tid = t.get("title", "Unknown")
        ttype = classify_template_name(tid)
        is_lua = is_lua_backed(tid)

        entry = {
            "title": tid,
            "ns": t.get("ns"),
            "type": ttype,
            "lua_backed": is_lua,
        }

        by_type[ttype].append(entry)

        if t.get("ns") == 828:
            module_templates.append(entry)
        elif ttype == "other":
            other_templates.append(entry)

    return by_type, module_templates, other_templates


# --- Output Formatters -----------------------------------------------------

def format_by_type(by_type, modules, others, page_info):
    """Format results grouped by template type."""
    lines = []
    lines.append(f"📄 Page: {page_info['title']}")
    lines.append(f"   Total templates: {sum(len(v) for v in by_type.values())}")
    if modules:
        lines.append(f"   Lua modules: {len(modules)}")
    lines.append("")

    TYPE_ICONS = {
        "infobox": "🪪",
        "citation": "📝",
        "navbox": "🧭",
        "maintenance": "⚠️",
        "hatnote": "🔗",
        "stub": "📌",
        "banner": "🏴",
        "date_and_format": "📅",
        "structural": "📐",
        "media": "🖼️",
        "user_talk": "💬",
        "template_doc": "📖",
        "module": "🖥️",
        "other": "❓",
    }

    # Sort by type in a sensible order
    type_order = ["infobox", "citation", "navbox", "maintenance", "hatnote",
                  "stub", "banner", "date_and_format", "structural", "media",
                  "user_talk", "template_doc", "other"]

    for ttype in type_order:
        items = by_type.get(ttype, [])
        if not items:
            continue
        icon = TYPE_ICONS.get(ttype, "📄")
        lines.append(f"{icon} {ttype.title()} ({len(items)}):")
        for item in items:
            lua_mark = " [Lua]" if item["lua_backed"] else ""
            lines.append(f"   • {item['title']}{lua_mark}")
        lines.append("")

    if modules:
        lines.append(f"🖥️  Lua Module Dependencies ({len(modules)}):")
        for m in modules:
            lines.append(f"   • {m['title']}")

    return "\n".join(lines)


def format_flat(by_type, modules, others, page_info):
    """Format results as a flat list."""
    lines = []
    lines.append(f"Page: {page_info['title']}")
    lines.append(f"Total: {sum(len(v) for v in by_type.values())} templates")
    lines.append("")

    for ttype, items in sorted(by_type.items()):
        for item in items:
            lua_mark = " [Lua]" if item["lua_backed"] else ""
            lines.append(f"  [{ttype}] {item['title']}{lua_mark}")

    if modules:
        lines.append("")
        lines.append("Lua Modules:")
        for m in modules:
            lines.append(f"  {m['title']}")

    return "\n".join(lines)


def format_json_result(page_info, by_type, modules, others):
    """Format results as JSON."""
    return json.dumps({
        "page": page_info["title"],
        "page_id": page_info.get("pageid"),
        "total_templates": sum(len(v) for v in by_type.values()),
        "by_type": {t: items for t, items in by_type.items()},
        "lua_modules": modules,
    }, indent=2, ensure_ascii=False)


# --- Main ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scan a page for all template usage, classified by type."
    )
    parser.add_argument("title", help="Page title to scan (e.g., 'Albert Einstein')")
    parser.add_argument("--by-type", action="store_true",
                        help="Group results by template type (default)")
    parser.add_argument("--flat", action="store_true",
                        help="Show flat list without type grouping")
    parser.add_argument("--format", choices=["plain", "json"], default="plain",
                        help="Output format (default: plain)")
    parser.add_argument("--modules", action="store_true",
                        help="Show only Lua module dependencies")
    parser.add_argument("--wiki", default=DEFAULT_WIKI,
                        help=f"Wiki URL (default: {DEFAULT_WIKI})")
    args = parser.parse_args()

    page_info = scan_page_templates(args.title, args.wiki)
    if not page_info["exists"]:
        print(f"Error: Page '{args.title}' not found on {args.wiki}.", file=sys.stderr)
        sys.exit(1)

    templates = page_info.get("templates", [])
    by_type, modules, others = classify_all(templates)

    if args.modules:
        # Show only module dependencies
        modules_only = [t for t in templates if t.get("ns") == 828]
        if not modules_only:
            print(f"No Lua module dependencies found on {args.title}.")
            return
        if args.format == "json":
            print(json.dumps(modules_only, indent=2, ensure_ascii=False))
        else:
            print(f"Lua module dependencies on {args.title}:")
            for m in modules_only:
                print(f"  • {m['title']}")
        return

    if args.format == "json":
        print(format_json_result(page_info, by_type, modules, others))
    elif args.flat:
        print(format_flat(by_type, modules, others, page_info))
    else:
        print(format_by_type(by_type, modules, others, page_info))


if __name__ == "__main__":
    main()
