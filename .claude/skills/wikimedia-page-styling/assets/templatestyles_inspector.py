#!/usr/bin/env python3
"""
TemplateStyles Inspector — Analyze a wiki page for all TemplateStyles usage.

Fetches a page via the MediaWiki API, identifies all loaded TemplateStyles
stylesheets, and reports on their CSS properties, selectors, and any
potential issues with the sanitizer.

Usage:
    python3 templatestyles-inspector.py "AvoinGLAM/Past activities" --wiki meta
    python3 templatestyles-inspector.py "Page" --rules
    python3 templatestyles-inspector.py "Page" --lint
    python3 templatestyles-inspector.py "Page" --json
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from urllib.parse import urlencode
from urllib.request import urlopen, Request


# --- Configuration ---------------------------------------------------------

DEFAULT_WIKI = "https://meta.wikimedia.org"
USER_AGENT = os.environ.get(
    "WIKIMEDIA_USER_AGENT",
    "WikimediaPageStylingSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch",
)


# --- API Helpers -----------------------------------------------------------

def api_call(wiki, params):
    """Make a MediaWiki API call."""
    url = f"{wiki}/w/api.php"
    params["format"] = "json"
    data = urlencode(params).encode("utf-8")
    req = Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_page_html(wiki, title):
    """Fetch parsed HTML of a page."""
    data = api_call(wiki, {
        "action": "parse",
        "page": title,
        "prop": "text|modules|jsconfigvars",
        "format": "json",
    })
    return data.get("parse", {})


# --- TemplateStyles Detection ----------------------------------------------

ALLOWED_CSS_PROPERTIES = {
    # Box model
    "width", "height", "min-width", "max-width", "min-height", "max-height",
    "padding", "padding-top", "padding-right", "padding-bottom", "padding-left",
    "margin", "margin-top", "margin-right", "margin-bottom", "margin-left",
    "box-sizing",
    # Display & layout
    "display", "flex", "flex-direction", "flex-wrap", "flex-flow",
    "flex-grow", "flex-shrink", "flex-basis",
    "grid", "grid-template", "grid-template-columns", "grid-template-rows",
    "grid-template-areas", "grid-column", "grid-column-start", "grid-column-end",
    "grid-row", "grid-row-start", "grid-row-end",
    "grid-area", "gap", "grid-gap", "column-gap", "row-gap",
    "order", "align-items", "align-content", "align-self",
    "justify-items", "justify-content", "justify-self",
    "place-items", "place-content", "place-self",
    # Positioning
    "position", "top", "right", "bottom", "left",
    "overflow", "overflow-x", "overflow-y", "z-index",
    "float", "clear",
    # Typography
    "font", "font-family", "font-size", "font-weight", "font-style", "font-variant",
    "line-height", "text-align", "text-decoration", "text-transform",
    "text-overflow", "text-shadow",
    "letter-spacing", "word-spacing", "white-space",
    "word-break", "overflow-wrap", "hyphens",
    "direction", "unicode-bidi",
    "column-count", "column-gap", "column-width", "columns",
    # Color & background
    "color", "background", "background-color",
    "background-image", "background-repeat", "background-size",
    "background-position", "background-attachment",
    "background-clip", "background-origin",
    "opacity",
    # Border & outline
    "border", "border-collapse",
    "border-color", "border-style", "border-width",
    "border-top", "border-right", "border-bottom", "border-left",
    "border-top-color", "border-top-style", "border-top-width",
    "border-right-color", "border-right-style", "border-right-width",
    "border-bottom-color", "border-bottom-style", "border-bottom-width",
    "border-left-color", "border-left-style", "border-left-width",
    "border-radius", "border-top-left-radius", "border-top-right-radius",
    "border-bottom-left-radius", "border-bottom-right-radius",
    "outline", "outline-color", "outline-style", "outline-width",
    # Visual effects
    "box-shadow", "filter", "backdrop-filter",
    "transform", "transition", "transition-property",
    "transition-duration", "transition-timing-function", "transition-delay",
    "animation", "animation-name", "animation-duration",
    "animation-timing-function", "animation-delay",
    "animation-iteration-count", "animation-direction",
    "animation-fill-mode", "animation-play-state",
    # Lists
    "list-style", "list-style-type", "list-style-image", "list-style-position",
    # Tables
    "table-layout", "empty-cells", "caption-side", "vertical-align",
    # Content
    "content", "counter-increment", "counter-reset", "quotes",
    # UI
    "cursor", "visibility", "clip", "clip-path", "pointer-events",
    "resize", "user-select", "caret-color",
}


def extract_templatestyles_from_html(html):
    """Extract TemplateStyles module info from parsed HTML metadata."""
    # TemplateStyles doesn't appear in the HTML directly.
    # We detect them from the page's module list.
    modules = set()
    
    # Look for templatestyles in the page HTML link tags
    import re
    # Pattern: load.php?modules=ext.templatestyles;target=Template:Name
    for match in re.finditer(
        r'load\.php\?modules=ext\.templatestyles(?:;target=([^&"\']+))?',
        html
    ):
        target = match.group(1)
        if target:
            # Convert dots back to slashes for the template name
            template = target.replace(".", "/")
            modules.add(f"Template:{template}")
    
    return modules


def get_templates_from_api(wiki, title):
    """Get all templates used on a page."""
    data = api_call(wiki, {
        "action": "query",
        "prop": "templates",
        "titles": title,
        "tllimit": 500,
        "format": "json",
    })
    pages = data.get("query", {}).get("pages", {})
    templates = []
    for page_id, page_data in pages.items():
        for t in page_data.get("templates", []):
            templates.append(t["title"])
    return templates


def get_page_info(wiki, title):
    """Get page metadata."""
    data = api_call(wiki, {
        "action": "query",
        "prop": "info|pageprops",
        "titles": title,
        "format": "json",
    })
    pages = data.get("query", {}).get("pages", {})
    for page_id, page_data in pages.items():
        if page_id != "-1":
            return page_data
    return {}


def fetch_template_source(wiki, template_title):
    """Fetch the raw wikitext of a template."""
    data = api_call(wiki, {
        "action": "parse",
        "page": template_title,
        "prop": "text",
        "format": "json",
    })
    text = data.get("parse", {}).get("text", {}).get("*", "")
    return text


def extract_css_properties(css_text):
    """Extract CSS property: value pairs from CSS text."""
    properties = []
    # Remove comments
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)
    
    for match in re.finditer(
        r'([a-zA-Z@-]+)\s*:\s*([^;{}]+)',
        css_text
    ):
        prop = match.group(1).strip().lower()
        value = match.group(2).strip()
        properties.append((prop, value))
    
    return properties


def extract_selectors(css_text):
    """Extract CSS selectors from CSS text."""
    selectors = []
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)
    
    for match in re.finditer(
        r'([.#a-zA-Z0-9_:\[\]\(\)\*>+\s~-]+)\s*\{',
        css_text
    ):
        sel = match.group(1).strip()
        if sel and not sel.startswith('@'):
            selectors.append(sel)
    
    return selectors


def lint_css_properties(properties):
    """Check CSS properties for potential TemplateStyles issues."""
    issues = []
    
    for prop, value in properties:
        if prop not in ALLOWED_CSS_PROPERTIES:
            issues.append({
                "type": "disallowed",
                "property": prop,
                "value": value,
                "message": f"'{prop}' is not in the TemplateStyles allowlist",
            })
        elif prop == "background-image" and "url(" in value:
            issues.append({
                "type": "restricted",
                "property": prop,
                "value": value,
                "message": "background-image: url() is not allowed — use gradients instead",
            })
        elif prop == "font-family" and not any(
            f in value for f in ["sans-serif", "serif", "monospace", "cursive", "fantasy", "system-ui"]
        ):
            issues.append({
                "type": "restricted",
                "property": prop,
                "value": value,
                "message": "Custom font may not be available unless hosted on WMF servers",
            })
        elif prop == "cursor" and "url(" in value:
            issues.append({
                "type": "restricted",
                "property": prop,
                "value": value,
                "message": "Custom URL cursors are not allowed",
            })
    
    return issues


# --- Main ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze a wiki page for TemplateStyles usage",
    )
    parser.add_argument("title", help="Page title to inspect")
    parser.add_argument("--wiki", default=DEFAULT_WIKI, help="Wiki base URL")
    parser.add_argument("--rules", action="store_true", help="Show CSS rules grouped by selector")
    parser.add_argument("--lint", action="store_true", help="Check for unsupported CSS properties")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Get page info
    page_info = get_page_info(args.wiki, args.title)
    if not page_info:
        print(f"Error: Page '{args.title}' not found on {args.wiki}")
        sys.exit(1)
    
    # Get templates
    templates = get_templates_from_api(args.wiki, args.title)
    
    # Find TemplateStyles CSS templates (those ending in .css)
    css_templates = [t for t in templates if t.endswith(".css")]
    
    # Get parsed HTML to find actual loaded modules
    parse_data = fetch_page_html(args.wiki, args.title)
    html = parse_data.get("text", {}).get("*", "")
    modules = parse_data.get("modules", [])
    js_config = parse_data.get("jsconfigvars", {})
    
    # Also check the module list for templatestyles
    ts_modules = [m for m in modules if "templatestyles" in m]
    
    # Prepare output
    result = {
        "page": {
            "title": args.title,
            "pageid": page_info.get("pageid"),
            "length": page_info.get("length"),
        },
        "templatestyles": {
            "css_templates": css_templates,
            "ts_modules": ts_modules,
            "count": len(css_templates),
        },
        "all_templates_count": len(templates),
    }
    
    # Analyze each CSS template
    css_analysis = []
    for css_tpl in css_templates:
        source = fetch_template_source(args.wiki, css_tpl)
        # Try to extract just CSS from the HTML-wrapped response
        # The API wraps CSS in <pre> tags or raw text depending on how it's stored
        
        # Look for .css extension in the page content
        analysis = {
            "template": css_tpl,
        }
        
        if source:
            # Extract CSS properties
            properties = extract_css_properties(source)
            selectors = extract_selectors(source)
            
            analysis["selectors"] = selectors
            analysis["selector_count"] = len(selectors)
            analysis["properties"] = properties
            analysis["property_count"] = len(properties)
            
            # Lint
            issues = lint_css_properties(properties)
            if args.lint:
                analysis["issues"] = issues
                analysis["issue_count"] = len(issues)
        
        css_analysis.append(analysis)
    
    result["css_analysis"] = css_analysis
    
    # --- Output ------------------------------------------------------------
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    # Human-readable output
    print(f"\n╔══ TemplateStyles Inspector ════════════════════════")
    print(f"║  Page: {args.title}")
    print(f"║  Wiki: {args.wiki}")
    print(f"╚═══════════════════════════════════════════════════════")
    print(f"\n  Total templates on page: {len(templates)}")
    print(f"  TemplateStyles CSS templates: {len(css_templates)}")
    print(f"  TemplateStyles modules loaded: {len(ts_modules)}")
    
    if css_templates:
        print(f"\n─── TemplateStyles Templates ───")
        for t in css_templates:
            print(f"  📄 {t}")
    
    if ts_modules:
        print(f"\n─── Loaded Modules ───")
        for m in ts_modules:
            print(f"  🔧 {m}")
    
    if args.rules and css_analysis:
        print(f"\n─── CSS Rules ───")
        for analysis in css_analysis:
            print(f"\n  📄 {analysis['template']}")
            for sel in analysis.get("selectors", []):
                print(f"    {sel}")
            for prop, value in analysis.get("properties", []):
                print(f"      {prop}: {value}")
    
    if args.lint and css_analysis:
        print(f"\n─── Lint Results ───")
        total_issues = 0
        for analysis in css_analysis:
            issues = analysis.get("issues", [])
            if issues:
                print(f"\n  📄 {analysis['template']}")
                for issue in issues:
                    icon = "❌" if issue["type"] == "disallowed" else "⚠️"
                    print(f"    {icon} [{issue['type']}] {issue['message']}")
                    total_issues += 1
        if total_issues == 0:
            print(f"  ✅ No issues found.")
    
    print("")


if __name__ == "__main__":
    main()
