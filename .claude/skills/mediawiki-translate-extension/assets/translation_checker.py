#!/usr/bin/env python3
"""
Translation Checker — Comprehensive translation analysis for a wiki page.

Analyzes the translation status of a page: available languages, completion
stats, fuzzy (outdated) units, and common issues.

Usage:
    python3 translation-checker.py "AvoinGLAM/Past activities" --wiki meta
    python3 translation-checker.py "Project/Page" --fuzzy
    python3 translation-checker.py "Project/Page" --json
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
    except Exception:
        return ""


# --- Translation Analysis --------------------------------------------------

def extract_translate_units(wikitext):
    """Extract translation units from <translate> sections.

    Translation units have the pattern:
        Content text. <!--T:N-->

    The <!--T:N--> marker comes AFTER its content.
    """
    units = []
    
    # Find all <translate>...</translate> sections
    sections = re.findall(
        r'<translate>(.*?)</translate>', wikitext, re.DOTALL
    )
    
    for section in sections:
        # Match each content + marker pair: content comes before <!--T:N-->
        for match in re.finditer(r'(.*?)<!--T:(\d+)-->', section, re.DOTALL):
            content = match.group(1).strip()
            unit_id = int(match.group(2))
            units.append({
                "id": unit_id,
                "content": content,
                "has_tvar": "<tvar" in content,
            })
    
    return units


def extract_tvar_variables(wikitext):
    """Extract all <tvar> variable names used."""
    tvars = set()
    for match in re.finditer(r'<tvar\s+name="([^"]+)"\s*>', wikitext):
        tvars.add(match.group(1))
    return sorted(tvars)


def check_translation_api(wiki, title):
    """Check translation-related API data."""
    result = {}
    
    # Langlinks
    data = api_call(wiki, {
        "action": "query",
        "prop": "langlinks",
        "titles": title,
        "lllimit": 500,
    })
    for pid, pdata in data.get("query", {}).get("pages", {}).items():
        langlinks = pdata.get("langlinks", [])
        result["languages"] = [ll["lang"] for ll in langlinks]
        result["language_count"] = len(langlinks)
    
    # Page properties
    data = api_call(wiki, {
        "action": "query",
        "prop": "pageprops",
        "titles": title,
    })
    for pid, pdata in data.get("query", {}).get("pages", {}).items():
        props = pdata.get("pageprops", {})
        result["pageprops"] = props
        result["is_translatable"] = "translatable" in props
    
    return result


def check_templatestyles_references(wiki, title):
    """Check if the page uses templatestyles (for CSS compatibility)."""
    data = api_call(wiki, {
        "action": "query",
        "prop": "templates",
        "titles": title,
        "tllimit": 500,
    })
    for pid, pdata in data.get("query", {}).get("pages", {}).items():
        templates = pdata.get("templates", [])
        css_templates = [t["title"] for t in templates if t["title"].endswith(".css")]
        return css_templates
    return []


def check_special_mylanguage_usage(wikitext):
    """Check for Special:MyLanguage usage."""
    count = len(re.findall(r'Special:MyLanguage', wikitext))
    return count


def check_timef_usage(wikitext):
    """Check for #timef usage."""
    count = len(re.findall(r'\{\{#timef:', wikitext))
    return count


# --- Main ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze translation status of a wiki page",
    )
    parser.add_argument("title", help="Page title to analyze")
    parser.add_argument("--wiki", default=DEFAULT_WIKI, help="Wiki base URL")
    parser.add_argument("--fuzzy", action="store_true", help="Show fuzzy/outdated info")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Fetch wikitext
    wikitext = fetch_wikitext(args.wiki, args.title)
    
    # Analyze
    units = extract_translate_units(wikitext)
    tvars = extract_tvar_variables(wikitext)
    api_info = check_translation_api(args.wiki, args.title)
    css_templates = check_templatestyles_references(args.wiki, args.title)
    mylang_count = check_special_mylanguage_usage(wikitext)
    timef_count = check_timef_usage(wikitext)
    
    result = {
        "page": args.title,
        "wiki": args.wiki,
        "wikitext_size": len(wikitext),
        "has_translate_tags": "<translate>" in wikitext,
        "has_languages_bar": "<languages />" in wikitext or "<languages/>" in wikitext,
        "translation_units": {
            "count": len(units),
            "with_tvar": sum(1 for u in units if u["has_tvar"]),
            "ids": [u["id"] for u in sorted(units, key=lambda x: x["id"])],
        },
        "tvar_variables": tvars,
        "special_mylanguage_count": mylang_count,
        "timef_count": timef_count,
        "api_info": api_info,
        "css_templates": css_templates,
    }
    
    if args.json:
        print(json.dumps(result, indent=2))
        return
    
    # Human-readable
    print(f"\n╔══ Translation Checker ════════════════════════")
    print(f"║  Page: {args.title}")
    print(f"╚═════════════════════════════════════════════════")
    
    print(f"\n─── Translation Markup ───")
    print(f"  <translate> tags:     {'✅' if result['has_translate_tags'] else '❌'} Found")
    print(f"  <languages /> bar:    {'✅' if result['has_languages_bar'] else '❌'} {'Found' if result['has_languages_bar'] else 'Missing'}")
    print(f"  Special:MyLanguage:   {mylang_count} occurrences")
    print(f"  #timef usage:         {timef_count} occurrences")
    
    print(f"\n─── Translation Units ───")
    print(f"  Total units:          {result['translation_units']['count']}")
    print(f"  Units with <tvar>:    {result['translation_units']['with_tvar']}")
    if tvars:
        print(f"  tvar variables:      {', '.join(tvars)}")
    
    print(f"\n─── API Translation Info ───")
    print(f"  Translatable:         {'✅ Yes' if api_info.get('is_translatable') else '❌ No'}")
    print(f"  Language variants:     {api_info.get('language_count', 0)}")
    if api_info.get("languages"):
        print(f"  Languages:            {', '.join(api_info['languages'][:10])}")
        if len(api_info["languages"]) > 10:
            print(f"                        ... and {len(api_info['languages']) - 10} more")
    
    if css_templates:
        print(f"\n─── CSS Templates (for translation styling) ───")
        for ct in css_templates:
            print(f"  🎨 {ct}")
    
    print(f"\n─── Unit Listing ───")
    for unit in sorted(units, key=lambda x: x["id"]):
        preview = unit["content"][:80].replace("\n", " ")
        tvar_indicator = " 📦" if unit["has_tvar"] else ""
        print(f"  [{unit['id']:3d}]{tvar_indicator} {preview}")
    
    print("")


if __name__ == "__main__":
    main()
