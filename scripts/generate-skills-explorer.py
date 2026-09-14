#!/usr/bin/env python3
"""Generate docs/skills-explorer.html from .claude/skills/*/SKILL.md.

The explorer is a static, no-build, no-CDN skill directory intended to replace
using the full force-directed network as the primary README discovery UI.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / ".claude" / "skills"
OUT = ROOT / "docs" / "skills-explorer.html"

DOMAIN_RULES = [
    ("Commons & media", ("commons", "flickr", "pattypan")),
    ("APIs, data & infrastructure", ("wikimedia-api", "wikimedia-auth", "wikimedia-database", "wikimedia-eventstreams", "wikimedia-toolforge", "toolforge", "wikimedia-i18n", "wikimedia-ml", "wikimedia-codex", "wikimedia-phabricator", "wikimedia-url-shortener", "wikipedia-error-handling")),
    ("Wikidata, search & reconciliation", ("wikidata", "quickstatements", "wikimedia-search", "wikimedia-petscan")),
    ("Wikipedia content & editing", ("wikipedia-", "wikimedia-wikitext", "wikimedia-diffs", "wikiwho", "xtools")),
    ("Sister projects", ("wikisource", "wiktionary", "wikivoyage")),
    ("MediaWiki structure & pages", ("mediawiki-", "pywikibot")),
]

TASK_RULES = [
    ("Editing & article quality", ("wikipedia-", "wikiwho", "wikimedia-diffs", "wikimedia-wikitext")),
    ("Commons/media work", ("commons", "flickr", "pattypan", "media-usage", "thumbnails", "audio-video", "pdf", "svg")),
    ("APIs, data & search", ("api", "database", "eventstreams", "search", "petscan", "pageviews", "page-assessment", "ml-services", "xtools")),
    ("Tool building", ("toolforge", "codex", "auth", "i18n", "security", "pywikibot", "error-handling")),
    ("Sister projects", ("wikisource", "wiktionary", "wikivoyage")),
    ("Wikidata", ("wikidata", "quickstatements", "reconciliation", "vector-search")),
]

ROLE_RULES = {
    "Editor": ("wikipedia-", "wikimedia-wikitext", "wikimedia-diffs", "wikiwho", "wikisource", "wiktionary", "wikivoyage"),
    "Commons contributor": ("commons", "flickr", "pattypan"),
    "Tool developer": ("api", "toolforge", "codex", "auth", "database", "eventstreams", "i18n", "security", "pywikibot"),
    "Researcher": ("pageviews", "xtools", "wikiwho", "wikidata", "search", "media-usage", "ml-services", "page-assessment"),
}

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
DEPENDS_RE = re.compile(r"depends_on:\s*\[([^\]]*)\]")
RELATED_RE = re.compile(r"related_skills:\s*\[([^\]]*)\]")
LINK_RE = re.compile(r"\.\./([a-z0-9-]+)/SKILL\.md")


def parse_list(raw: str) -> list[str]:
    if not raw:
        return []
    return sorted(set(re.findall(r"[a-z][a-z0-9-]*", raw)))


def frontmatter(text: str) -> dict[str, str | list[str]]:
    m = FRONTMATTER_RE.match(text)
    block = m.group(1) if m else ""
    data: dict[str, str | list[str]] = {}
    for key in ("name", "description", "last_verified"):
        km = re.search(rf"^{key}:\s*(.*)$", block, re.M)
        if km:
            data[key] = km.group(1).strip().strip('"')
    for key, rx in (("depends_on", DEPENDS_RE), ("related_skills", RELATED_RE)):
        km = rx.search(block)
        data[key] = parse_list(km.group(1) if km else "")
    return data


def classify(name: str, desc: str, rules: list[tuple[str, tuple[str, ...]]], default: str) -> str:
    hay = f"{name} {desc}".lower()
    for label, needles in rules:
        if any(n in hay for n in needles):
            return label
    return default


def roles_for(name: str, desc: str) -> list[str]:
    hay = f"{name} {desc}".lower()
    roles = [role for role, needles in ROLE_RULES.items() if any(n in hay for n in needles)]
    return roles or ["General"]


def skill_records() -> list[dict]:
    rows = []
    for skill_file in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        fm = frontmatter(text)
        name = str(fm.get("name") or skill_file.parent.name)
        desc = str(fm.get("description") or "")
        depends = set(fm.get("depends_on", []))
        related = set(fm.get("related_skills", []))
        links = set(LINK_RE.findall(text))
        cross = sorted((depends | related | links) - {name})
        rows.append({
            "name": name,
            "description": desc,
            "path": f"../.claude/skills/{skill_file.parent.name}/SKILL.md",
            "domain": classify(name, desc, DOMAIN_RULES, "Other / cross-cutting"),
            "task": classify(name, desc, TASK_RULES, "General reference"),
            "roles": roles_for(name, desc),
            "depends_on": sorted(depends),
            "related": sorted(related),
            "cross_links": cross,
            "degree": len(cross),
        })
    return rows


def write_html(rows: list[dict], out: Path | None = None) -> None:
    domains = sorted({r["domain"] for r in rows})
    tasks = sorted({r["task"] for r in rows})
    roles = sorted({role for r in rows for role in r["roles"]})
    data = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wikipedia AI Skills Explorer</title>
<style>
:root {{ color-scheme: light dark; --bg:#f8fafc; --panel:#fff; --ink:#172033; --muted:#607084; --line:#d8e0ea; --accent:#36c; --chip:#eef4ff; --chip2:#f4f6f8; --shadow:0 10px 30px rgba(20,35,55,.08); }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#0f1724; --panel:#162033; --ink:#f2f6fb; --muted:#aab7c7; --line:#2c3b51; --accent:#8ab4ff; --chip:#1d3154; --chip2:#202b3b; --shadow:0 10px 30px rgba(0,0,0,.25); }} }}
* {{ box-sizing:border-box; }} body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; background:var(--bg); color:var(--ink); }}
header {{ padding:32px 24px 20px; max-width:1200px; margin:0 auto; }}
h1 {{ margin:0 0 8px; font-size:clamp(2rem,4vw,3.5rem); letter-spacing:-.04em; }}
.lede {{ max-width:850px; color:var(--muted); font-size:1.08rem; line-height:1.55; }}
.toolbar {{ position:sticky; top:0; z-index:5; background:color-mix(in srgb, var(--bg) 86%, transparent); backdrop-filter: blur(12px); border-block:1px solid var(--line); }}
.toolbar-inner {{ max-width:1200px; margin:0 auto; padding:14px 24px; display:grid; grid-template-columns:minmax(220px,1fr) repeat(3, minmax(150px,220px)); gap:10px; }}
input, select {{ width:100%; border:1px solid var(--line); border-radius:12px; padding:10px 12px; background:var(--panel); color:var(--ink); font:inherit; }}
main {{ max-width:1200px; margin:0 auto; padding:22px 24px 56px; }}
.stats {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:18px; color:var(--muted); }}
.stat {{ background:var(--panel); border:1px solid var(--line); border-radius:999px; padding:6px 10px; }}
.paths {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; margin:0 0 22px; }}
.path {{ border:1px solid var(--line); background:var(--panel); border-radius:16px; padding:14px; box-shadow:var(--shadow); cursor:pointer; }}
.path strong {{ display:block; margin-bottom:4px; }} .path span {{ color:var(--muted); font-size:.92rem; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(310px,1fr)); gap:14px; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:16px; box-shadow:var(--shadow); display:flex; flex-direction:column; gap:10px; }}
.card h2 {{ margin:0; font-size:1.05rem; }} .card h2 a {{ color:var(--accent); text-decoration:none; }} .card h2 a:hover {{ text-decoration:underline; }}
.desc {{ margin:0; color:var(--muted); line-height:1.45; }}
.badges {{ display:flex; flex-wrap:wrap; gap:6px; }} .badge {{ border-radius:999px; padding:4px 8px; font-size:.78rem; background:var(--chip); color:var(--ink); }} .badge.soft {{ background:var(--chip2); color:var(--muted); }}
.links {{ margin-top:auto; border-top:1px solid var(--line); padding-top:10px; font-size:.85rem; color:var(--muted); }}
.links a {{ color:var(--accent); text-decoration:none; margin-right:6px; }} .links a:hover {{ text-decoration:underline; }}
.empty {{ padding:30px; text-align:center; color:var(--muted); border:1px dashed var(--line); border-radius:18px; background:var(--panel); }}
footer {{ max-width:1200px; margin:0 auto; padding:0 24px 36px; color:var(--muted); font-size:.9rem; }}
@media (max-width:850px) {{ .toolbar-inner {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<header>
<h1>Wikipedia AI Skills Explorer</h1>
<p class="lede">Find the right skill by task, domain, or role. This page is a browsable directory first; relationship data is still shown on each card, without forcing you through the full network hairball.</p>
</header>
<section class="toolbar"><div class="toolbar-inner">
<input id="q" type="search" placeholder="Search skills, descriptions, dependencies…" aria-label="Search skills">
<select id="domain" aria-label="Filter by domain"><option value="">All domains</option>{''.join(f'<option>{html.escape(d)}</option>' for d in domains)}</select>
<select id="task" aria-label="Filter by task"><option value="">All tasks</option>{''.join(f'<option>{html.escape(t)}</option>' for t in tasks)}</select>
<select id="role" aria-label="Filter by role"><option value="">All roles</option>{''.join(f'<option>{html.escape(r)}</option>' for r in roles)}</select>
</div></section>
<main>
<div class="stats"><span class="stat"><strong id="shown">{len(rows)}</strong> shown</span><span class="stat"><strong>{len(rows)}</strong> total skills</span><span class="stat">Click a learning path to filter</span><span class="stat"><a href="skills-network.html">Advanced network view</a></span></div>
<div class="paths" id="paths"></div>
<div class="grid" id="grid"></div>
<div class="empty" id="empty" hidden>No skills match these filters.</div>
</main>
<footer>Generated from <code>.claude/skills/*/SKILL.md</code>. The Graphviz/D3 network is still available for advanced relationship exploration.</footer>
<script>
const SKILLS = {data};
const PATHS = [
  {{title:'Editing Wikipedia', filter:{{role:'Editor'}}, note:'Policies, wikitext, diffs, edit history, article quality'}},
  {{title:'Commons/media work', filter:{{task:'Commons/media work'}}, note:'Files, thumbnails, SDC, PDFs, audio/video, upload workflows'}},
  {{title:'APIs and data', filter:{{task:'APIs, data & search'}}, note:'Action API, search, pageviews, databases, ML services'}},
  {{title:'Building tools', filter:{{role:'Tool developer'}}, note:'Toolforge, auth, Codex, security, i18n, bots'}},
  {{title:'Sister projects', filter:{{task:'Sister projects'}}, note:'Wikisource, Wiktionary, Wikivoyage'}},
  {{title:'Wikidata workflows', filter:{{task:'Wikidata'}}, note:'QIDs, reconciliation, vectors, QuickStatements'}}
];
const el = id => document.getElementById(id);
function text(skill) {{ return [skill.name, skill.description, skill.domain, skill.task, ...skill.roles, ...skill.depends_on, ...skill.related, ...skill.cross_links].join(' ').toLowerCase(); }}
function badge(t, cls='') {{ return `<span class="badge ${{cls}}">${{escapeHtml(t)}}</span>`; }}
function escapeHtml(s) {{ return String(s).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
function card(s) {{
  const deps = s.depends_on.slice(0,5).map(x => badge(x,'soft')).join('');
  const rel = s.cross_links.slice(0,6).map(x => `<a href="#" data-skill="${{escapeHtml(x)}}">${{escapeHtml(x)}}</a>`).join(' ');
  return `<article class="card"><h2><a href="${{escapeHtml(s.path)}}">${{escapeHtml(s.name)}}</a></h2><p class="desc">${{escapeHtml(s.description)}}</p><div class="badges">${{badge(s.domain)}}${{badge(s.task,'soft')}}${{s.roles.map(r=>badge(r,'soft')).join('')}}</div>${{deps ? `<div class="badges"><span class="badge soft">depends on</span>${{deps}}</div>` : ''}}<div class="links">${{rel ? `Related: ${{rel}}` : 'No direct cross-links found'}}</div></article>`;
}}
function currentFilters() {{ return {{q:el('q').value.trim().toLowerCase(), domain:el('domain').value, task:el('task').value, role:el('role').value}}; }}
function render() {{
  const f = currentFilters();
  const tokens = f.q.split(/\\s+/).filter(Boolean);
  const rows = SKILLS.filter(s => (!f.domain || s.domain===f.domain) && (!f.task || s.task===f.task) && (!f.role || s.roles.includes(f.role)) && tokens.every(t => text(s).includes(t)));
  el('shown').textContent = rows.length;
  el('grid').innerHTML = rows.map(card).join('');
  el('empty').hidden = rows.length !== 0;
}}
function setFilter(filter) {{ if ('domain' in filter) el('domain').value = filter.domain; if ('task' in filter) el('task').value = filter.task; if ('role' in filter) el('role').value = filter.role; el('q').value = ''; render(); }}
el('paths').innerHTML = PATHS.map(p => `<button class="path" data-filter='${{JSON.stringify(p.filter)}}'><strong>${{escapeHtml(p.title)}}</strong><span>${{escapeHtml(p.note)}}</span></button>`).join('');
document.addEventListener('input', e => {{ if (['q','domain','task','role'].includes(e.target.id)) render(); }});
document.addEventListener('click', e => {{ const p=e.target.closest('.path'); if (p) setFilter(JSON.parse(p.dataset.filter)); const a=e.target.closest('[data-skill]'); if (a) {{ e.preventDefault(); el('q').value=a.dataset.skill; el('domain').value=el('task').value=el('role').value=''; render(); window.scrollTo({{top:0, behavior:'smooth'}}); }} }});
render();
</script>
</body>
</html>
"""
    target = out or OUT
    target.write_text(html_doc, encoding="utf-8")
    try:
        shown: Path | str = target.relative_to(ROOT)
    except ValueError:  # caller passed a path outside the repo (e.g. tests)
        shown = target
    print(f"Generated {shown} — {len(rows)} skills")


def main() -> None:
    rows = skill_records()
    write_html(rows)


if __name__ == "__main__":
    main()
