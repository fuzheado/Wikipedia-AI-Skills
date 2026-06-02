#!/usr/bin/env python3
"""
Page Auditor — fetch a Wikipedia article and report on all its structural components.

Reports: infobox type and parameters, visible and hidden categories,
templates used (infobox, navbox, maintenance), protection level,
redirect/disambiguation status, WikiProject banners from the talk page,
reference/citation count, and section outline.

Usage:
    python3 page-audit.py "Albert Einstein"
    python3 page-audit.py "Python (programming language)" --json
    python3 page-audit.py "Page that doesn't exist"
    python3 page-audit.py "Einstein" --project fr.wikipedia
"""

import json
import sys
import re
import requests
import argparse

USER_AGENT = "PageAuditor/1.0 (https://en.wikipedia.org; demo@example.com) WikiSkills"
API_URL = "https://en.wikipedia.org/w/api.php"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


def api_request(params):
    """Make an API request and return the JSON response."""
    resp = SESSION.get(API_URL, params=params)
    resp.raise_for_status()
    return resp.json()


def fetch_page_info(title):
    """Fetch basic page info, categories, templates, and protection."""
    params = {
        "action": "query",
        "prop": "info|categories|templates|pageprops|revisions",
        "titles": title,
        "redirects": 1,
        "inprop": "protection",
        "cllimit": 100,
        "tllimit": 100,
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
    }
    return api_request(params)


def fetch_talk_page(title):
    """Fetch the talk page content for WikiProject banners."""
    talk_title = f"Talk:{title}"
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": talk_title,
        "rvprop": "content",
        "rvslots": "main",
        "format": "json",
    }
    data = api_request(params)
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if "missing" not in page:
            revs = page.get("revisions", [])
            if revs:
                return revs[0].get("slots", {}).get("main", {}).get("content", "")
    return ""


def extract_infobox(wikitext):
    """Extract the first infobox template from wikitext."""
    match = re.search(r"\{\{(Infobox[\s\S]*?\n\}\})", wikitext)
    if not match:
        return None, []
    infobox_text = match.group(1)

    # Determine infobox type
    type_match = re.match(r"\{\{Infobox\s+(\w+)", infobox_text)
    infobox_type = type_match.group(1) if type_match else "Unknown"

    # Extract parameters
    params = []
    for line in infobox_text.split("\n"):
        param_match = re.match(r"^\|([^=]+?)\s*=\s*(.*)", line.strip())
        if param_match:
            name = param_match.group(1).strip()
            value = param_match.group(2).strip()
            params.append((name, value))

    return infobox_type, params


def extract_sections(wikitext):
    """Extract the section outline from wikitext."""
    sections = re.findall(r"^(==+)\s*(.*?)\s*\1", wikitext, re.MULTILINE)
    return [(len(m[0]) - 1, m[1].strip()) for m in sections]


def count_references(wikitext):
    """Count number of <ref> tags."""
    refs = re.findall(r"<ref[^>]*>", wikitext)
    named_refs = re.findall(r'<ref\s+name\s*=\s*["\']([^"\']+)["\']\s*/>', wikitext)
    full_refs = [r for r in refs if "name" not in r or "/>" not in r]
    return len(full_refs), len(named_refs)


def extract_banners(talk_content):
    """Extract WikiProject banners from talk page content."""
    if not talk_content:
        return []
    banners = re.findall(r"\{\{WikiProject\s+(\w+)[\s\S]*?(?=\n\}\})", talk_content)
    results = []
    for banner in banners:
        cls = re.search(r"class\s*=\s*(\w+)", banner)
        imp = re.search(r"importance\s*=\s*(\w+)", banner)
        results.append({
            "project": re.match(r"(\w+)", banner).group(1) if re.match(r"(\w+)", banner) else banner,
            "class": cls.group(1) if cls else None,
            "importance": imp.group(1) if imp else None,
        })
    return results


def categorize_templates(templates):
    """Categorize templates into infobox, navbox, maintenance, and other."""
    cats = {"infobox": [], "navbox": [], "maintenance": [], "other": []}
    maint_keywords = ["cn", "citation needed", "better source", "dead link",
                      "POV", "expand section", "stub", "clarify", "when", "who",
                      "dubious", "failed verification", "weasel inline"]
    for t in templates:
        name = t.get("title", "")
        if "Infobox" in name:
            cats["infobox"].append(name)
        elif "navbox" in name.lower() or "Navbox" in name:
            cats["navbox"].append(name)
        elif name.lower() in maint_keywords:
            cats["maintenance"].append(name)
        else:
            cats["other"].append(name)
    return cats


def audit(title, project="en.wikipedia.org", output_json=False):
    """Full page audit."""
    global API_URL
    API_URL = f"https://{project}/w/api.php"

    data = fetch_page_info(title)
    pages = data.get("query", {}).get("pages", {})
    redirects = data.get("query", {}).get("redirects", [])

    if not pages:
        return {"error": "Page not found"}

    page_id, page = next(iter(pages.items()))

    # Handle missing page
    if "missing" in page:
        return {"error": f"Page '{title}' does not exist"}

    # Handle redirect
    resolved_title = page.get("title", title)
    if redirects:
        resolved_title = redirects[0].get("to", resolved_title)

    # Get wikitext
    revs = page.get("revisions", [])
    wikitext = revs[0].get("slots", {}).get("main", {}).get("content", "") if revs else ""

    # Talk page
    talk_content = fetch_talk_page(resolved_title)

    # Infobox
    infobox_type, infobox_params = extract_infobox(wikitext)

    # Sections
    sections = extract_sections(wikitext)

    # References
    full_refs, named_refs = count_references(wikitext)

    # Categories
    cats = page.get("categories", [])
    visible_cats = [c["title"] for c in cats if "hidden" not in c]
    hidden_cats = [c["title"] for c in cats if "hidden" in c]

    # Templates
    templates = page.get("templates", [])
    template_cats = categorize_templates(templates)

    # Protection
    protections = page.get("protection", [])

    # Page props
    pageprops = page.get("pageprops", {})
    is_disambig = "disambiguation" in str(pageprops)
    wikibase_id = pageprops.get("wikibase_item", "")

    # WikiProject banners
    banners = extract_banners(talk_content)

    result = {
        "title": resolved_title,
        "page_id": page.get("pageid"),
        "length_bytes": page.get("length", 0),
        "is_redirect": bool(redirects),
        "is_disambiguation": is_disambig,
        "wikibase_qid": wikibase_id,
        "infobox": {
            "type": infobox_type,
            "params": len(infobox_params) if infobox_params else 0,
        },
        "section_count": len(sections),
        "sections": [{"level": lvl, "title": sec} for lvl, sec in sections],
        "references": {
            "inline_refs": full_refs,
            "named_usages": named_refs,
            "total": full_refs + named_refs,
        },
        "categories": {
            "visible": [c.replace("Category:", "") for c in visible_cats],
            "hidden": [c.replace("Category:", "") for c in hidden_cats],
        },
        "templates": {
            "total": len(templates),
            "infobox": template_cats["infobox"],
            "navbox": template_cats["navbox"],
            "maintenance": template_cats["maintenance"],
        },
        "protection": {p["type"]: p["level"] for p in protections},
        "assessment_banners": banners,
    }

    if output_json:
        print(json.dumps(result, indent=2))
    else:
        _print_report(result)

    return result


def _print_report(r):
    """Print a formatted human-readable audit report."""
    print(f"=== Page Audit: {r['title']} ===")
    print(f"  Page ID:       {r['page_id']}")
    print(f"  Length:        {r['length_bytes']} bytes")
    if r['is_redirect']:
        print("  ⚠️  Redirect page")
    if r['is_disambiguation']:
        print("  ℹ️  Disambiguation page")
    if r['wikibase_qid']:
        print(f"  Wikidata:      {r['wikibase_qid']}")

    print(f"\n  📋 Infobox")
    print(f"     Type: {r['infobox']['type'] or 'None'}")
    print(f"     Parameters: {r['infobox']['params']}")

    print(f"\n  📝 Sections ({r['section_count']})")
    for s in r['sections'][:15]:
        indent = "  " * s['level']
        print(f"     {indent}{s['title']}")
    if r['section_count'] > 15:
        print(f"     ... and {r['section_count'] - 15} more")

    print(f"\n  📚 References: {r['references']['total']}")
    print(f"     Inline refs: {r['references']['inline_refs']}")
    print(f"     Named usages: {r['references']['named_usages']}")

    print(f"\n  🏷️  Categories")
    print(f"     Visible: {len(r['categories']['visible'])}")
    if r['categories']['visible']:
        for c in r['categories']['visible'][:8]:
            print(f"       • {c}")
        if len(r['categories']['visible']) > 8:
            print(f"       ... and {len(r['categories']['visible']) - 8} more")
    print(f"     Hidden: {len(r['categories']['hidden'])}")

    print(f"\n  🧩 Templates: {r['templates']['total']}")
    print(f"     Infobox: {len(r['templates']['infobox'])}")
    print(f"     Navbox: {len(r['templates']['navbox'])}")
    print(f"     Maintenance: {len(r['templates']['maintenance'])}")

    print(f"\n  🔒 Protection")
    if r['protection']:
        for ptype, plevel in r['protection'].items():
            print(f"     {ptype}: {plevel}")
    else:
        print("     None (open)")

    if r['assessment_banners']:
        print(f"\n  🏅 WikiProject Assessments ({len(r['assessment_banners'])})")
        for b in r['assessment_banners'][:5]:
            cls = f"class={b['class']}" if b['class'] else "no class"
            imp = f"importance={b['importance']}" if b['importance'] else "no importance"
            print(f"     {b['project']}: {cls}, {imp}")
        if len(r['assessment_banners']) > 5:
            print(f"     ... and {len(r['assessment_banners']) - 5} more")

    print()


def main():
    parser = argparse.ArgumentParser(description="Audit the structure of a Wikipedia article")
    parser.add_argument("title", help="Article title to audit")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--project", default="en.wikipedia.org",
                        help="Wiki project domain (default: en.wikipedia.org)")
    args = parser.parse_args()

    result = audit(args.title, project=args.project, output_json=args.json)
    if "error" in result:
        print(f"Error: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
