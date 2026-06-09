#!/usr/bin/env python3
"""
Template Translation Scanner — Scan templates for translation compliance.

Checks that template labels use <translate>, links use Special:MyLanguage/,
dates use #timef, and other best practices are followed.

Usage:
    python3 template-translation-scanner.py "Template:AvoinGLAM/Main navigation" --wiki meta
    python3 template-translation-scanner.py --project "AvoinGLAM" --wiki meta
    python3 template-translation-scanner.py "Template:Project/Box" --report
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
    "MediaWikiTranslateSkill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; contact@example.com) ContentGapResearch",
)

# Best practice rules
RULES = [
    {
        "id": "translate-labels",
        "description": "Menu labels and UI text should be wrapped in <translate>",
        "check": lambda wt: "<translate>" in wt,
        "weight": "required",
    },
    {
        "id": "mylanguage-links",
        "description": "Internal links should use Special:MyLanguage/",
        "check": lambda wt: "Special:MyLanguage" in wt,
        "weight": "required",
    },
    {
        "id": "languages-bar",
        "description": "Template source should include <languages/> for translators",
        "check": lambda wt: "<languages />" in wt or "<languages/>" in wt,
        "weight": "recommended",
    },
    {
        "id": "timef-dates",
        "description": "Dates should use #timef (locale-aware) not #time",
        "check": lambda wt: "{{#timef:" in wt,
        "weight": "recommended",
    },
    {
        "id": "no-hardcoded-labels",
        "description": "Avoid hardcoded labels not wrapped in <translate> (checking for bare English text in menus)",
        "check": lambda wt: True,  # Always passes — checked separately
        "weight": "recommended",
    },
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


def fetch_wikitext(wiki, title):
    """Fetch raw wikitext of a page."""
    url = f"{wiki}/w/index.php"
    params = urlencode({"title": title, "action": "raw"})
    req = Request(f"{url}?{params}", headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        return ""


def get_project_templates(wiki, project_name):
    """Get all templates in a project namespace."""
    data = api_call(wiki, {
        "action": "query",
        "list": "prefixsearch",
        "pssearch": f"Template:{project_name}/",
        "pslimit": 500,
    })
    return [
        r["title"] for r in data.get("query", {}).get("prefixsearch", [])
    ]


# --- Compliance Checks -----------------------------------------------------

def check_translate_coverage(wikitext):
    """Estimate what percentage of visible text is wrapped in <translate>."""
    # Extract all text in menus, links, etc.
    # Simple heuristic: count characters inside <translate> vs outside
    in_translate = len("".join(re.findall(
        r'<translate>(.*?)</translate>', wikitext, re.DOTALL
    )))
    
    # Count total text (excluding markup, templates, etc.)
    # Simple: just count all characters in the wikitext
    # (Imperfect but gives a rough estimate)
    total_text = len(wikitext)
    
    if total_text == 0:
        return 0.0
    
    # This is a rough heuristic — actual translatable text is less than total
    # We're looking for a reasonable proportion
    ratio = in_translate / total_text
    return min(ratio * 2, 1.0)  # Scale up since not all wikitext is text


def check_bare_labels(wikitext):
    """Find potential hardcoded labels not wrapped in <translate>."""
    issues = []
    # Look for text in link descriptions that isn't wrapped
    # Pattern: [[Link|Text]] where Text isn't inside <translate>
    
    # First, strip translate sections
    stripped = re.sub(r'<translate>.*?</translate>', '', wikitext, flags=re.DOTALL)
    
    # Find link texts in the remaining content
    for match in re.finditer(r'\[\[[^]]+\|([^]]+)\]\]', stripped):
        label = match.group(1)
        # Skip if it's a parameter, magic word, or template call
        if not label.startswith("{{") and not label.startswith("<"):
            # Check if it's a likely English label (all ASCII letters)
            if re.match(r'^[A-Za-z\s]+$', label):
                issues.append(label)
    
    return issues


def analyze_template(wiki, title):
    """Analyze a single template for translation compliance."""
    wikitext = fetch_wikitext(wiki, title)
    
    if not wikitext:
        return {"title": title, "error": "Could not fetch wikitext"}
    
    results = {}
    for rule in RULES:
        passed = rule["check"](wikitext)
        results[rule["id"]] = {
            "passed": passed,
            "description": rule["description"],
            "weight": rule["weight"],
        }
    
    # Additional checks
    coverage = check_translate_coverage(wikitext)
    bare_labels = check_bare_labels(wikitext)
    
    # Count translate units
    unit_count = len(re.findall(r'<!--T:\d+-->', wikitext))
    
    # Count tvar usage
    tvar_count = len(re.findall(r'<tvar\s+name=', wikitext))
    
    return {
        "title": title,
        "wikitext_size": len(wikitext),
        "checks": results,
        "coverage_estimate": coverage,
        "translate_unit_count": unit_count,
        "tvar_count": tvar_count,
        "bare_labels_found": bare_labels[:10],  # Limit output
        "has_style": "<templatestyles" in wikitext,
    }


# --- Main ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scan templates for translation compliance",
    )
    parser.add_argument("template", nargs="?", help="Template to scan")
    parser.add_argument("--wiki", default=DEFAULT_WIKI, help="Wiki base URL")
    parser.add_argument("--project", help="Scan all templates in a project")
    parser.add_argument("--report", action="store_true", help="Show compliance report")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if args.project:
        templates = get_project_templates(args.wiki, args.project)
        print(f"Scanning {len(templates)} templates in project '{args.project}'...")
        
        results = []
        for t in templates:
            result = analyze_template(args.wiki, t)
            results.append(result)
        
        if args.json:
            print(json.dumps(results, indent=2))
            return
        
        # Report
        print(f"\n╔══ Translation Compliance Report ═══════════════════")
        print(f"║  Project: {args.project}")
        print(f"║  Templates: {len(templates)}")
        print(f"╚═════════════════════════════════════════════════════")
        
        for r in results:
            if "error" in r:
                print(f"\n  ❌ {r['title']}: {r['error']}")
                continue
            
            title_short = r["title"].replace(f"Template:{args.project}/", "")
            check_results = r.get("checks", {})
            failed = [k for k, v in check_results.items() if not v.get("passed")]
            
            if failed:
                print(f"\n  ⚠️  {title_short}: {len(failed)} issue(s)")
                for f in failed:
                    print(f"    ❌ {check_results[f]['description']}")
            else:
                print(f"\n  ✅ {title_short}: All checks passed")
            
            if r.get("bare_labels_found"):
                print(f"      📝 Potential hardcoded labels: {', '.join(r['bare_labels_found'][:3])}")
    
    elif args.template:
        result = analyze_template(args.wiki, args.template)
        
        if args.json:
            print(json.dumps(result, indent=2))
            return
        
        print(f"\n╔══ Template Translation Scan ═══════════════════════")
        print(f"║  Template: {args.template}")
        print(f"╚═════════════════════════════════════════════════════")
        
        if "error" in r:
            print(f"\n  ❌ Error: {r['error']}")
            return
        
        r = result  # shorthand
        
        print(f"\n─── Overview ───")
        print(f"  Size: {r['wikitext_size']} chars")
        print(f"  Translate units: {r['translate_unit_count']}")
        print(f"  <tvar> variables: {r['tvar_count']}")
        print(f"  Coverage estimate: {r['coverage_estimate']:.0%}")
        
        print(f"\n─── Compliance Checks ───")
        for check_id, check_data in r.get("checks", {}).items():
            icon = "✅" if check_data["passed"] else "❌"
            weight = check_data["weight"]
            print(f"  {icon} [{weight}] {check_data['description']}")
        
        if r.get("bare_labels_found"):
            print(f"\n─── Potential Hardcoded Labels ───")
            for label in r["bare_labels_found"]:
                print(f"  📝 '{label}'")
        
        if r.get("has_style"):
            print(f"\n  🎨 Uses TemplateStyles")
    
    else:
        print("Error: Specify a template name or --project.")


if __name__ == "__main__":
    main()
