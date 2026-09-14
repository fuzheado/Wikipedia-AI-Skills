#!/usr/bin/env python3
"""refresh-api-surface.py — Capture the live Wikimedia Action API module
surface into scripts/api-surface.json (ground truth for verify-api.py).

Sources (all live, all authoritative):
  1. paraminfo main-module `action` parameter — the full top-level action list,
     merged across en.wikipedia.org, www.wikidata.org, commons.wikimedia.org and
     en.wikisource.org (the last for Wikisource-only extension modules such as
     ProofreadPage's prop=proofread)
     (so Wikibase modules like wbgetentities are included)
  2. paraminfo query+NAME — verifies every candidate query submodule
     (prop=/list=/meta=); names that don't exist come back in warnings, so the
     registry only records what the live API actually reports
  3. per-action paraminfo — the `prop` parameter's allowed values for
     non-query actions used with prop= in the skills (e.g. parse: wikitext,
     text, links, ...)

The candidate seed for query submodules = everything the skills use + a
curated core list (stable across MediaWiki versions). Any token a skill uses
that is NOT in the registry is a violation until the registry is refreshed,
mirroring the command-registry model.

Usage:
    python3 scripts/refresh-api-surface.py

Writes: scripts/api-surface.json
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"
OUT = SCRIPT_DIR / "api-surface.json"
APIS = (
    "https://en.wikipedia.org/w/api.php",
    "https://www.wikidata.org/w/api.php",
    "https://commons.wikimedia.org/w/api.php",
    "https://en.wikisource.org/w/api.php",
)
USER_AGENT = os.environ.get(
    "WIKIMEDIA_USER_AGENT",
    "wikipedia-ai-skills-api-surface/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills)",
)

# Curated core query submodules (stable across MediaWiki versions). Unioned
# with everything the skills actually use; every name is then verified live.
CORE_PROPS = """info revisions categories categoryinfo images imageinfo duplicatefiles
extlinks extracts fileusage globalusage iwlinks langlinks links linkshere pageimages
pageprops pageviews redirects revisions stubimageinfo templates transcludedin
deletedrevisions description coordinates contributors preloadcontent module wikibase""".split()
CORE_LISTS = """allcategories alldeletedrevisions allfileusages allimages alllinks
allmessages allpages allredirects alltransclusions allusers backlinks blocks
categorymembers deletedrevs embeddedin exturlusage filearchive globalallusers
imageusage iwbacklinks langbacklinks logevents pagepropnames pageswithprop
prefixsearch protectedtitles querypage random recentchanges search tags
usercontribs users watchlist watchlistraw""".split()
CORE_METAS = """siteinfo userinfo tokens globaluserinfo filerepoinfo""".split()

API_URL_RE = re.compile("https?://[^\\s\\)\\]>'\x22\x60]*api\\.php[^\\s\\)\\]>'\x22\x60]*")


def fetch_json(api: str, params: dict) -> dict:
    q = urlencode(params)
    req = Request(f"{api}?{q}", headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8", "replace"))


def paraminfo_module_list(api: str) -> set[str]:
    """The top-level action list from the main module's action parameter."""
    d = fetch_json(api, {"action": "paraminfo", "modules": "main",
                         "format": "json", "formatversion": "2"})
    for m in d.get("paraminfo", {}).get("modules", []):
        for p in m.get("parameters", []):
            if p.get("name") == "action":
                return set(p.get("type", []))
    return set()


def paraminfo_batch(api: str, names: list[str], prefix: str = "") -> set[str]:
    """Verify names via paraminfo (chunked); return the set that exists."""
    confirmed: set[str] = set()
    names = sorted(set(names))
    for i in range(0, len(names), 40):
        chunk = names[i:i + 40]
        mods = "|".join(f"{prefix}+{n}" if prefix else n for n in chunk)
        try:
            d = fetch_json(api, {"action": "paraminfo", "modules": mods,
                                 "format": "json", "formatversion": "2"})
        except Exception as e:
            print(f"paraminfo call failed for chunk {i} on {api}: {e}", file=sys.stderr)
            continue
        confirmed.update(m["name"] for m in d.get("paraminfo", {}).get("modules", []))
    return confirmed


def action_prop_values(api: str, action: str) -> set[str]:
    """Allowed values of a module's 'prop' parameter (e.g. parse: wikitext...)."""
    try:
        d = fetch_json(api, {"action": "paraminfo", "modules": action,
                             "format": "json", "formatversion": "2"})
    except Exception as e:
        print(f"paraminfo failed for {action}: {e}", file=sys.stderr)
        return set()
    for m in d.get("paraminfo", {}).get("modules", []):
        for p in m.get("parameters", []):
            if p.get("name") == "prop" and "type" in p:
                return set(p["type"])
    return set()


def skill_api_tokens(skills_dir: Path) -> dict:
    """Which (action, prop/list/meta) tokens do the skills actually use?"""
    used = {"action": set(), "prop": set(), "list": set(), "meta": set()}
    nonquery_props = {}  # action -> set(prop tokens)
    for f in skills_dir.rglob("*.md"):
        text = f.read_text()
        for m in API_URL_RE.finditer(text):
            qs = m.group(0).split("?", 1)[1] if "?" in m.group(0) else ""
            params = {}
            for kv in qs.split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    params[k] = v
            action = params.get("action", "query")
            for kind in ("prop", "list", "meta"):
                if kind not in params:
                    continue
                tokens = {x for x in params[kind].split("|")
                          if re.fullmatch(r"[a-z][a-z0-9_-]*", x)}
                used[kind].update(tokens)
                if kind == "prop" and action != "query":
                    nonquery_props.setdefault(action, set()).update(tokens)
            used["action"].add(action)
    used["nonquery_props"] = nonquery_props
    return used


def main() -> int:
    print("Capturing API surface from live Wikimedia APIs ...", file=sys.stderr)

    # 1. top-level actions, merged across wikis
    actions: set[str] = set()
    for api in APIS:
        actions |= paraminfo_module_list(api)
    actions.discard("query")

    used = skill_api_tokens(DEFAULT_SKILLS_DIR)
    enwiki = APIS[0]

    # 2. query submodules — enwiki is the baseline, but some modules are
    #    extension-provided and exist only on other wikis (ProofreadPage's
    #    `prop=proofread`/`proofreadinfo`/`list=proofreadpages` are Wikisource-only).
    #    Union the skill-used tokens across every host so those validate too.
    seed_props = used["prop"] | set(CORE_PROPS)
    seed_lists = used["list"] | set(CORE_LISTS)
    seed_metas = used["meta"] | set(CORE_METAS)
    props = paraminfo_batch(enwiki, sorted(seed_props), prefix="query")
    lists = paraminfo_batch(enwiki, sorted(seed_lists), prefix="query")
    metas = paraminfo_batch(enwiki, sorted(seed_metas), prefix="query")
    for api in APIS[1:]:
        props |= paraminfo_batch(api, sorted(used["prop"]), prefix="query")
        lists |= paraminfo_batch(api, sorted(used["list"]), prefix="query")
        metas |= paraminfo_batch(api, sorted(used["meta"]), prefix="query")

    # 3. per-action prop= values for non-query actions used with prop= in skills
    action_props = {}
    for action in sorted(used["nonquery_props"]):
        vals = action_prop_values(enwiki, action)
        if vals:
            action_props[action] = sorted(vals)

    surface = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/refresh-api-surface.py",
        "source": "live paraminfo from " + ", ".join(APIS),
        "note": ("Ground-truth Wikimedia Action API surface. Do not edit by hand; "
                 "regenerate with scripts/refresh-api-surface.py."),
        "action": sorted(actions),
        "query": {"prop": sorted(props), "list": sorted(lists), "meta": sorted(metas)},
        "action_props": action_props,
    }
    OUT.write_text(json.dumps(surface, indent=1, sort_keys=True) + "\n")

    print(f"Surface written to {OUT}", file=sys.stderr)
    print(f"  {len(actions)} top-level action modules (3 wikis)", file=sys.stderr)
    print(f"  query: {len(props)} prop=, {len(lists)} list=, {len(metas)} meta=", file=sys.stderr)
    print(f"  action_props for: {sorted(action_props)}", file=sys.stderr)
    missing = used["action"] - actions - {"query"}
    if missing:
        print(f"  WARNING: skill-used actions not in registry: {sorted(missing)}", file=sys.stderr)
    for kind, used_set in (("prop", used["prop"]), ("list", used["list"]), ("meta", used["meta"])):
        reg = {"prop": props, "list": lists, "meta": metas}[kind]
        miss = used_set - reg
        if miss:
            print(f"  WARNING: skill-used {kind}= tokens not in registry: {sorted(miss)}",
                  file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
