#!/usr/bin/env python3
"""
Wikitext utilities — fetch Wikipedia wikitext and extract infobox data.
Uses only Python standard library (urllib) so no pip install needed.

Usage:
    python3 wikitext_utils.py infobox "Albert Einstein"
    python3 wikitext_utils.py infobox "Python (programming language)" --project fr.wikipedia
    python3 wikitext_utils.py infobox "Berlin" --json
"""

import sys
import re
import json
import urllib.request
import urllib.parse
import argparse

USER_AGENT = "PageAnatomy/1.0 (https://en.wikipedia.org; demo@example.com) WikiSkills"


def fetch_wikitext(title, project="en.wikipedia.org"):
    """Fetch raw wikitext for a page using stdlib urllib."""
    url = f"https://{project}/w/index.php"
    params = urllib.parse.urlencode({"title": title, "action": "raw"})
    req = urllib.request.Request(f"{url}?{params}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def extract_infobox(wikitext):
    """Extract the first {{Infobox...}} template block with proper brace nesting."""
    lines = wikitext.split('\n')
    infobox_lines = []
    in_infobox = False
    brace_depth = 0
    infobox_type = None

    for line in lines:
        if not in_infobox:
            match = re.match(r'\{\{Infobox\s+(\w+)', line)
            if match:
                in_infobox = True
                infobox_type = match.group(1)
                brace_depth = line.count('{{') - line.count('}}')
                infobox_lines.append(line)
        else:
            infobox_lines.append(line)
            brace_depth += line.count('{{') - line.count('}}')
            if brace_depth <= 0:
                break

    if not infobox_lines:
        return None, []

    # Extract parameters
    params = []
    for line in infobox_lines:
        param_match = re.match(r'^\|([^=]+?)\s*=\s*(.*)', line)
        if param_match:
            name = param_match.group(1).strip()
            value = param_match.group(2).strip()
            params.append((name, value))

    return infobox_type, params


def main():
    parser = argparse.ArgumentParser(description="Extract infobox from a Wikipedia article")
    parser.add_argument("command", choices=["infobox"], help="Operation")
    parser.add_argument("title", help="Article title")
    parser.add_argument("--project", default="en.wikipedia.org",
                        help="Wiki project domain")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    wikitext = fetch_wikitext(args.title, args.project)
    infobox_type, params = extract_infobox(wikitext)

    if not infobox_type:
        print("No infobox found on this page.")
        sys.exit(0)

    if args.json:
        print(json.dumps({
            "type": infobox_type,
            "params": [{"name": n, "value": v} for n, v in params]
        }, indent=2))
    else:
        print(f"Infobox type: {infobox_type}")
        print(f"Total parameters: {len(params)}")
        print()
        print("Parameters:")
        for name, value in params:
            if len(value) > 120:
                value = value[:120] + "..."
            print(f"  {name}: {value}")


if __name__ == "__main__":
    main()
