#!/usr/bin/env bash
# Convert a MediaWiki wikitable to rough HTML for visual preview.
# Reads wikitable from stdin or the clipboard.
#
# Usage:
#   echo '{| class="wikitable"|! A|! B|-|1|2|}' | ./wikitable-to-html.sh
#   ./wikitable-to-html.sh < my_table.wiki

set -euo pipefail

INPUT=$(cat)

python3 -c "
import sys, html

wt = '''${INPUT//\'/\'\\\'\'}'''

# Very rough conversion — for preview purposes only
# Proper parsing should use mwparserfromhell (see SKILL.md)

lines = wt.split('\n')
in_table = False
in_header = False
html_parts = []

for line in lines:
    stripped = line.strip()

    if stripped.startswith('{|'):
        in_table = True
        classes = 'wikitable'
        if 'class=\"' in stripped:
            m = __import__('re').search(r'class=\"([^\"]+)\"', stripped)
            if m:
                classes = m.group(1)
        style = ''
        if 'style=\"' in stripped:
            m = __import__('re').search(r'style=\"([^\"]+)\"', stripped)
            if m:
                style = f' style=\"{m.group(1)}\"'
        html_parts.append(f'<table class=\"{classes}\"{style}>')
        html_parts.append('  <thead>')

    elif stripped.startswith('|}'):
        if in_header:
            html_parts.append('  </thead>')
        html_parts.append('</table>')
        in_table = False

    elif stripped.startswith('|-'):
        if in_header:
            html_parts.append('  </thead>')
            html_parts.append('  <tbody>')
            in_header = False
        html_parts.append('    <tr>')

    elif stripped.startswith('|+'):
        html_parts.append(f'  <caption>{stripped[2:].strip()}</caption>')

    elif stripped.startswith('!'):
        in_header = True
        # Find all header cells (separated by !! or newlines)
        cells = [c.strip() for c in stripped[1:].split('!!') if c.strip()]
        for c in cells:
            scope = 'scope=\"col\"'
            c_clean = c
            if 'scope=\"' in c:
                m = __import__('re').search(r'scope=\"([^\"]+)\"', c)
                if m:
                    scope = f'scope=\"{m.group(1)}\"'
                c_clean = __import__('re').sub(r'scope=\"[^\"]*\"\s*\|\s*', '', c_clean)
            if 'style=\"' in c_clean:
                m = __import__('re').search(r'style=\"([^\"]+)\"', c_clean)
                style = f' style=\"{m.group(1)}\"' if m else ''
                c_clean = __import__('re').sub(r'style=\"[^\"]*\"\s*\|\s*', '', c_clean)
            else:
                style = ''
            html_parts.append(f'      <th {scope}{style}>{c_clean}</th>')

    elif stripped.startswith('|') and not stripped.startswith('||'):
        cell_text = stripped[1:].strip()
        # Strip style/class attributes
        cell_text = __import__('re').sub(r'^(style|class)=\"[^\"]*\"\s*\|\s*', '', cell_text)
        html_parts.append(f'      <td>{cell_text}</td>')

if in_header:
    html_parts.append('  </thead>')
    html_parts.append('  </tbody>')

print('''<!DOCTYPE html>
<html><head><meta charset=\"utf-8\">
<style>
  table { border-collapse: collapse; font-family: sans-serif; }
  td, th { border: 1px solid #a2a9b1; padding: 4px 8px; }
  th { background: #eaecf0; }
  .sortable th { cursor: pointer; }
</style></head><body>''')
print('\\n'.join(html_parts))
print('</body></html>')
" > /tmp/wikitable_preview.html

echo "Preview saved to file:///tmp/wikitable_preview.html"
open /tmp/wikitable_preview.html 2>/dev/null || true
