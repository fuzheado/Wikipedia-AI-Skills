#!/usr/bin/env python3
"""
Template Inspector — Fetch and analyze a MediaWiki template's structure.

Fetches a template's source, parameters, protection level, Lua module
dependencies, and tracking categories from the Action API.

Usage:
    python3 template-inspector.py "Infobox person"
    python3 template-inspector.py "Infobox person" --parameters
    python3 template-inspector.py "Infobox settlement" --modules
    python3 template-inspector.py "Cite web" --format json
    python3 template-inspector.py "Infobox settlement" --format json --modules
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import urlencode
from urllib.request import urlopen, Request


# --- Configuration ---------------------------------------------------------

DEFAULT_WIKI = "https://en.wikipedia.org"
USER_AGENT = os.environ.get(
    "WIKIMEDIA_USER_AGENT",
    "WikipediaTemplatesSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch",
)


# --- API Helpers -----------------------------------------------------------

def api_call(params, wiki=DEFAULT_WIKI):
    """Make an Action API call and return the parsed JSON response."""
    params["format"] = "json"
    url = f"{wiki}/w/api.php?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_title(title):
    """Ensure the title is prefixed with Template: if not already namespaced."""
    if title.startswith("Template:") or title.startswith("Module:"):
        return title
    return f"Template:{title}"


# --- Analysis Functions ----------------------------------------------------

def fetch_basic_info(title, wiki=DEFAULT_WIKI):
    """Fetch page info: protection, pageprops, existence."""
    data = api_call({
        "action": "query",
        "prop": "info|pageprops",
        "inprop": "protection",
        "titles": title,
    }, wiki)
    pages = data.get("query", {}).get("pages", {})
    for pid, pdata in pages.items():
        if pid == "-1":
            return {"exists": False, "title": title}
        return {
            "exists": True,
            "title": pdata.get("title", title),
            "pageid": int(pid),
            "protection": pdata.get("protection", []),
            "pageprops": pdata.get("pageprops", {}),
        }
    return {"exists": False, "title": title}


def fetch_source(title, wiki=DEFAULT_WIKI):
    """Fetch the raw wikitext source of the template."""
    data = api_call({
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvlimit": 1,
        "titles": title,
    }, wiki)
    pages = data.get("query", {}).get("pages", {})
    for pid, pdata in pages.items():
        if pid == "-1":
            return None
        revs = pdata.get("revisions", [])
        if revs:
            return revs[0].get("content", "")
    return None


def fetch_templates(title, wiki=DEFAULT_WIKI):
    """Fetch all templates (including Lua modules) used by the page."""
    data = api_call({
        "action": "query",
        "prop": "templates",
        "titles": title,
    }, wiki)
    pages = data.get("query", {}).get("pages", {})
    for pid, pdata in pages.items():
        if pid == "-1":
            return []
        return pdata.get("templates", [])
    return []


def extract_parameters(source):
    """Extract parameter names from template source code using regex.

    This is a best-effort approach — for complete AST-based parsing,
    use mwparserfromhell (see the wikimedia-wikitext skill).
    """
    params = {"named": [], "positional": [], "with_defaults": {}}

    # Match {{{param_name}}} and {{{param_name|default}}}
    pattern = re.compile(r'\{\{\{(\w[\w ]*)\|?([^}]*)\}\}\}')
    for match in pattern.finditer(source):
        name = match.group(1).strip()
        default = match.group(2).strip() if match.group(2) else None

        if name.isdigit():
            ptype = "positional"
        else:
            ptype = "named"

        if default:
            params["with_defaults"][name] = default

        if name.isdigit() and ptype == "positional":
            if name not in [p["name"] for p in params["positional"]]:
                params["positional"].append({"name": name, "default": default})
        elif ptype == "named":
            if name not in [p["name"] for p in params["named"]]:
                params["named"].append({"name": name, "default": default})

    # Sort positional by number
    params["positional"].sort(key=lambda p: int(p["name"]))
    return params


def extract_lua_calls(source):
    """Extract all {{#invoke:Module|function}} calls from source."""
    if not source:
        return []
    pattern = re.compile(r'\{\{#invoke:(\w[\w ]*)\|(\w[\w ]*)\|?([^}]*)\}\}')
    calls = []
    for match in pattern.finditer(source):
        calls.append({
            "module": match.group(1).strip(),
            "function": match.group(2).strip(),
            "args": match.group(3).strip() if match.group(3) else "",
        })
    return calls


def extract_include_tags(source):
    """Count <noinclude>, <includeonly>, <onlyinclude> tags."""
    if not source:
        return {}
    return {
        "noinclude": len(re.findall(r'<noinclude>', source)),
        "includeonly": len(re.findall(r'<includeonly>', source)),
        "onlyinclude": len(re.findall(r'<onlyinclude>', source)),
    }


def classify_template(source, title):
    """Classify the template by type based on its source."""
    if not source:
        return "unknown"

    lc_source = source.lower()
    lc_title = title.lower()

    if "navbox" in lc_source or "navbox" in lc_title:
        return "navigation"
    if "infobox" in lc_source or "infobox" in lc_title:
        return "infobox"
    if "cite " in lc_source or "citation" in lc_source or "cite" in lc_title:
        return "citation"
    if "stub" in lc_title or "stub" in lc_source:
        return "stub"
    if "wikiproject" in lc_source or lc_source.startswith("{{wikiproject"):
        return "banner"
    if lc_source.startswith("#redirect"):
        return "redirect"
    # Check for maintenance categories it adds
    if "citation needed" in lc_source or "clarify" in lc_source:
        return "maintenance"

    return "other"


# --- Output Formatters -----------------------------------------------------

def format_plain(result):
    """Format the analysis as human-readable plain text."""
    lines = []

    if not result.get("exists", False):
        lines.append(f"❌ Template '{result.get('title', '?')}' does not exist.")
        return "\n".join(lines)

    info = result.get("info", {})
    if not info:
        lines.append(f"❌ Template '{result.get('title', '?')}' does not exist.")
        return "\n".join(lines)

    source = result.get("source")
    params = result.get("parameters", {})
    templates_list = result.get("templates", [])
    include_tags = result.get("include_tags", {})
    lua_calls = result.get("lua_calls", [])
    classification = result.get("classification", "unknown")

    lines.append(f"📋 Template: {info.get('title', result['title'])}")
    lines.append(f"   Page ID: {info['pageid']}")
    lines.append(f"   Classification: {classification}")
    lines.append("")

    # Protection
    lines.append("🔒 Protection:")
    if info["protection"]:
        for p in info["protection"]:
            lines.append(f"   {p['type']}: {p['level']} (expires: {p.get('expiry', 'unknown')})")
    else:
        lines.append("   Unprotected")
    lines.append("")

    # Include tags
    lines.append("📦 Include Control Tags:")
    for tag, count in include_tags.items():
        lines.append(f"   <{tag}>: {count}")
    lines.append("")

    # Parameters
    pos = params.get("positional", [])
    named = params.get("named", [])
    with_defaults = params.get("with_defaults", {})
    lines.append(f"📝 Parameters: {len(pos)} positional, {len(named)} named")
    if pos:
        lines.append("   Positional:")
        for p in pos:
            dflt = p.get("default")
            if dflt:
                lines.append(f"     {p['name']} (default: {dflt})")
            else:
                lines.append(f"     {p['name']} (required)")
    if named:
        lines.append("   Named:")
        for p in named[:20]:  # Limit output
            dflt = p.get("default")
            if dflt:
                lines.append(f"     {p['name']} (default: {dflt})")
            else:
                lines.append(f"     {p['name']}")
        if len(named) > 20:
            lines.append(f"     ... and {len(named) - 20} more")
    lines.append("")

    # Lua calls
    if lua_calls:
        lines.append(f"🖥️  Lua {{#invoke}} calls: {len(lua_calls)}")
        for call in lua_calls:
            lines.append(f"   {call['module']}.{call['function']}()")
        lines.append("")

    # Module dependencies
    modules = [t for t in templates if t.get("ns") == 828]
    if modules:
        lines.append(f"📚 Lua Module Dependencies: {len(modules)}")
        for m in modules:
            lines.append(f"   • {m['title']}")

    return "\n".join(lines)


def format_json(result):
    """Format the analysis as JSON."""
    return json.dumps(result, indent=2, ensure_ascii=False)


# --- Main ------------------------------------------------------------------

def analyze_template(title, wiki=DEFAULT_WIKI):
    """Perform full analysis of a template."""
    api_title = normalize_title(title)

    info = fetch_basic_info(api_title, wiki)
    if not info["exists"]:
        return {"title": title, "exists": False}

    source = fetch_source(api_title, wiki)
    templates = fetch_templates(api_title, wiki)
    params = extract_parameters(source) if source else {}
    include_tags = extract_include_tags(source) if source else {}
    lua_calls = extract_lua_calls(source) if source else []
    classification = classify_template(source, api_title)

    return {
        "title": title,
        "api_title": api_title,
        "exists": True,
        "info": info,
        "source": source,
        "parameters": params,
        "templates": templates,
        "include_tags": include_tags,
        "lua_calls": lua_calls,
        "classification": classification,
        "wiki": wiki,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Inspect a MediaWiki template and report its structure."
    )
    parser.add_argument("title", help="Template name (e.g., 'Infobox person')")
    parser.add_argument("--parameters", action="store_true",
                        help="Show only parameter information")
    parser.add_argument("--modules", action="store_true",
                        help="Show only Lua module dependencies")
    parser.add_argument("--format", choices=["plain", "json"], default="plain",
                        help="Output format (default: plain)")
    parser.add_argument("--wiki", default=DEFAULT_WIKI,
                        help=f"Wiki URL (default: {DEFAULT_WIKI})")
    args = parser.parse_args()

    result = analyze_template(args.title, args.wiki)

    if args.format == "json":
        output = format_json(result)
        print(output)
    else:
        if args.parameters and result.get("exists"):
            params = result.get("parameters", {})
            print(f"Parameters for {args.title}:")
            for p in params.get("positional", []):
                dflt = p.get("default")
                print(f"  Positional #{p['name']}: default={dflt}")
            for p in params.get("named", []):
                dflt = p.get("default")
                print(f"  Named '{p['name']}': default={dflt}")
        elif args.modules and result.get("exists"):
            modules = [t for t in result.get("templates", []) if t.get("ns") == 828]
            if modules:
                print(f"Lua modules used by {args.title}:")
                for m in modules:
                    print(f"  • {m['title']}")
            else:
                print(f"No Lua module dependencies found for {args.title}.")
        else:
            print(format_plain(result))


if __name__ == "__main__":
    main()
