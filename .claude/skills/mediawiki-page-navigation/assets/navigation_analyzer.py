#!/usr/bin/env python3
"""
Navigation Analyzer — Trace navigation template hierarchy, subpage structure,
and link tree for a wiki page.

Given a page title, this script:
  - Identifies navigation templates used
  - Traces subpage hierarchy
  - Checks for /Sub template availability
  - Maps the link tree
  - Detects temporal navigation (CURRENTYEAR + #ifexist)

Usage:
    python3 navigation-analyzer.py "AvoinGLAM/Past activities" --wiki meta
    python3 navigation-analyzer.py "Project" --tree
    python3 navigation-analyzer.py "Project/Subpage" --conditionals
    python3 navigation-analyzer.py "Page" --json
"""

import argparse
import json
import os
import re
import sys
from urllib.parse import urlencode
from urllib.request import urlopen, Request


# --- Configuration ---------------------------------------------------------

DEFAULT_WIKI = "https://meta.wikimedia.org"
USER_AGENT = os.environ.get(
    "WIKIMEDIA_USER_AGENT",
    "MediaWikiNavigationSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch",
)

# Templates commonly used for navigation
NAVIGATION_KEYWORDS = [
    "navigation", "nav", "menu", "header", "Nav", "Navigation",
]


# --- API Helpers -----------------------------------------------------------

def api_call(wiki, params):
    """Make a MediaWiki API call."""
    url = f"{wiki}/w/api.php"
    params["format"] = "json"
    data = urlencode(params).encode("utf-8")
    req = Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def page_exists(wiki, title):
    """Check if a page exists on the wiki."""
    data = api_call(wiki, {
        "action": "query",
        "prop": "info",
        "titles": title,
    })
    for pid, pdata in data.get("query", {}).get("pages", {}).items():
        return pid != "-1"
    return False


# --- Navigation Analysis ---------------------------------------------------

def parse_hierarchy(title):
    """Parse a page title into its hierarchy segments."""
    parts = title.split("/")
    return {
        "full": title,
        "root": parts[0],
        "segments": parts,
        "depth": len(parts) - 1,
        "parent": "/".join(parts[:-1]) if len(parts) > 1 else None,
        "leaf": parts[-1],
    }


def get_templates(wiki, title):
    """Get all templates used on a page."""
    data = api_call(wiki, {
        "action": "query",
        "prop": "templates",
        "titles": title,
        "tllimit": 500,
    })
    templates = []
    for pid, pdata in data.get("query", {}).get("pages", {}).items():
        templates = pdata.get("templates", [])
    return templates


def find_navigation_templates(templates):
    """Filter templates that are likely navigation-related."""
    nav_templates = []
    other_templates = []
    
    for t in templates:
        title = t.get("title", "")
        is_nav = any(kw.lower() in title.lower() for kw in NAVIGATION_KEYWORDS)
        
        # Also check if it's a CSS template or a box template
        if title.endswith(".css"):
            other_templates.append({"type": "stylesheet", "title": title})
        elif is_nav:
            nav_templates.append({"type": "navigation", "title": title})
        else:
            other_templates.append({"type": "other", "title": title})
    
    return nav_templates, other_templates


def check_sub_templates(wiki, title):
    """Check for /Sub templates at each level of the hierarchy."""
    parts = title.split("/")
    candidates = []
    
    # Check at each level
    for i in range(len(parts), 0, -1):
        prefix = "/".join(parts[:i])
        cand = f"Template:{prefix}/Sub"
        exists = page_exists(wiki, cand)
        candidates.append({
            "template": cand,
            "exists": exists,
            "level": i,
        })
    
    # Also check root
    root_cand = f"Template:{parts[0]}/Sub"
    if root_cand not in [c["template"] for c in candidates]:
        exists = page_exists(wiki, root_cand)
        candidates.append({
            "template": root_cand,
            "exists": exists,
            "level": 0,
        })
    
    return candidates


def detect_temporal_navigation(templates):
    """Detect temporal navigation patterns like {{CURRENTYEAR}}."""
    temporal_patterns = []
    for t in templates:
        title = t.get("title", "")
        if "currentyear" in title.lower() or re.search(r'\b\d{4}\b', title):
            temporal_patterns.append(title)
    return temporal_patterns


def analyze_wikitext_for_nav_patterns(wiki, template_title):
    """Fetch a template's wikitext and analyze navigation patterns."""
    data = api_call(wiki, {
        "action": "parse",
        "page": template_title,
        "prop": "text",
    })
    wikitext = data.get("parse", {}).get("text", {}).get("*", "")
    
    patterns = {
        "has_titleparts": "{{#titleparts" in wikitext,
        "has_ifexist": "{{#ifexist" in wikitext,
        "has_mylanguage": "Special:MyLanguage" in wikitext,
        "has_currentyear": "{{CURRENTYEAR}}" in wikitext,
        "has_sub_nav": "/Sub" in wikitext,
        "has_translate": "<translate>" in wikitext,
        "has_templatestyles": "<templatestyles" in wikitext,
        "has_fullpagename": "{{FULLPAGENAME}}" in wikitext,
        "has_subpagename": "{{SUBPAGENAME}}" in wikitext,
    }
    
    return patterns


# --- Main ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze navigation structure of a wiki page",
    )
    parser.add_argument("title", help="Page title to analyze")
    parser.add_argument("--wiki", default=DEFAULT_WIKI, help="Wiki base URL")
    parser.add_argument("--tree", action="store_true", help="Show page hierarchy tree")
    parser.add_argument("--conditionals", action="store_true", help="Show conditional navigation")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Parse hierarchy
    hierarchy = parse_hierarchy(args.title)
    
    # Get templates
    all_templates = get_templates(args.wiki, args.title)
    nav_templates, other_templates = find_navigation_templates(all_templates)
    
    # Check sub templates
    sub_candidates = check_sub_templates(args.wiki, args.title)
    
    # Analyze navigation template patterns
    nav_patterns = {}
    for nt in nav_templates:
        nav_patterns[nt["title"]] = analyze_wikitext_for_nav_patterns(
            args.wiki, nt["title"]
        )
    
    # Build result
    result = {
        "page": args.title,
        "hierarchy": hierarchy,
        "templates": {
            "total": len(all_templates),
            "navigation": nav_templates,
            "other": other_templates,
        },
        "sub_templates": sub_candidates,
        "navigation_patterns": nav_patterns,
    }
    
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    # Human-readable output
    print(f"\n╔══ Navigation Analyzer ════════════════════════")
    print(f"║  Page: {args.title}")
    print(f"╚════════════════════════════════════════════════")
    
    # Hierarchy
    print(f"\n─── Page Hierarchy ───")
    print(f"  Root:     {hierarchy['root']}")
    print(f"  Leaf:     {hierarchy['leaf']}")
    print(f"  Depth:    {hierarchy['depth']}")
    if hierarchy['parent']:
        print(f"  Parent:   {hierarchy['parent']}")
        print(f"  Siblings: {hierarchy['parent']}/...")
    
    if args.tree:
        print(f"\n─── Hierarchy Tree ───")
        for i, segment in enumerate(hierarchy['segments']):
            indent = "  " + "  " * i
            prefix = "/".join(hierarchy['segments'][:i+1])
            marker = "└── " if i == len(hierarchy['segments']) - 1 else "├── "
            print(f"{indent}{marker}{segment}  ({prefix})")
    
    # Navigation templates
    if nav_templates:
        print(f"\n─── Navigation Templates ({len(nav_templates)}) ───")
        for nt in nav_templates:
            print(f"  🧭 {nt['title']}")
            if nt['title'] in nav_patterns:
                patterns = nav_patterns[nt['title']]
                features = []
                if patterns['has_titleparts']: features.append("titleparts")
                if patterns['has_ifexist']: features.append("ifexist")
                if patterns['has_sub_nav']: features.append("Sub-nav")
                if patterns['has_currentyear']: features.append("CURRENTYEAR")
                if patterns['has_mylanguage']: features.append("MyLanguage")
                if patterns['has_templatestyles']: features.append("TemplateStyles")
                if features:
                    print(f"      Patterns: {', '.join(features)}")
    
    # Sub templates
    existing_subs = [s for s in sub_candidates if s['exists']]
    if existing_subs:
        print(f"\n─── Active /Sub Templates ───")
        for s in existing_subs:
            level = "root" if s['level'] == 0 else f"level {s['level']}"
            print(f"  🔗 {s['template']}  ({level})")
    
    missing_subs = [s for s in sub_candidates if not s['exists']]
    if args.conditionals and missing_subs:
        print(f"\n─── Potential /Sub Templates (would trigger #ifexist) ───")
        for s in missing_subs:
            level = "root" if s['level'] == 0 else f"level {s['level']}"
            print(f"  ❌ {s['template']}  ({level})")
    
    # Other templates
    if not nav_templates and other_templates:
        print(f"\n─── All Templates ({len(other_templates)}) ───")
        for ot in other_templates:
            icon = "🎨" if ot['type'] == 'stylesheet' else "📄"
            print(f"  {icon} {ot['title']}")

    print("")


if __name__ == "__main__":
    main()
