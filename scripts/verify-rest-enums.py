#!/usr/bin/env python3
"""verify-rest-enums.py — Check AQS REST endpoint paths and parameter values in the
skills against the ground truth in scripts/rest-surface.json.

Complements verify-api.py, which only covers Action API module/property names
(URLs containing api.php). This covers the metrics half of the surface:

  1. ENDPOINT PATHS — a `…/api/rest_v1/metrics/<module>/…` URL or a bare
     `GET /metrics/<module>/…` path must either match a path template from the
     live AQS OpenAPI specs, or be a segment-prefix of one (so base URLs such as
     `/metrics/pageviews/` stay legal). Catches endpoints that were never
     implemented or have been retired: `/metrics/pageviews/top-by-ec/…`,
     `/metrics/pageviews/top-by-country/{country}/{date}`.

  2. PARAMETER VALUES — a value the live service answers with HTTP 400 must not
     appear in an enumeration of accepted values. The enums are probed live by
     refresh-rest-surface.py, so the check itself is offline. This is the
     cross-API trap that prose invites: `agent=automated` is valid for
     pageviews, `agent_type=automated` is a 400 for mediarequests.

SCOPE / LIMITS — read before extending:

  * Only the AQS `/metrics/` family is path-checked. The core REST endpoints
    (`/page/…`, `/transform/…`) are NOT checked here: `/w/rest_v1/` and the
    api.wikimedia.org gateway expose different sets, so checking core paths
    against one spec produces mostly false positives. Giving the gateway its own
    surface file is the right next step, not widening this one.
  * Paths that exist as HTTP 200 are never flagged, only paths absent from the
    surface — a *shorter* path than a template (a partial URL a script completes
    at runtime) is treated as a legal prefix.
  * Known non-findings, deliberately skipped: `.json` spec/doc links, elided
    paths containing `…`, and lines that merely warn about a bad value
    ("no automated", "HTTP 400", "invalid", "never", "only", …).
  * One known false-positive class: a bare `POST /v2/…`-style path for a
    *non-Wikimedia* API quoted in a cross-API comparison table is resolved
    against the AQS module the file also mentions. Filtering it needs a host
    allow-list for other APIs, which is a separate piece of work.
  * A violation means "not in the surface", never "the skill is wrong" — a new
    legitimate endpoint fails until `refresh-rest-surface.py` is re-run. That is
    the intended direction: surface files are refreshed, skills are edited.

Offline: no network in CI. Refresh the surface with
`python3 scripts/refresh-rest-surface.py`.

Usage:
    python3 scripts/verify-rest-enums.py
    python3 scripts/verify-rest-enums.py --json

Exit codes: 0 = clean, 1 = violations found.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DEFAULT_SURFACE = SCRIPT_DIR / "rest-surface.json"
DEFAULT_SKILLS_DIR = REPO_ROOT / ".claude" / "skills"

URL_RE = re.compile(r"https?://[^\s)\]`\"'<>]*api/rest_v1/metrics/[^\s)\]`\"'<>]*")
BARE_RE = re.compile(r"`?(?:GET|POST)\s+(/[^\s`\)\]\"']*)")
PLACEHOLDER_RE = re.compile(r"\{[^/{}]+\}")
CUE_RE = re.compile(r"\b400\b|invalid|not a valid|reject|does not exist|no such|retired|deprecated"
                    r"|no\s+`?\s*automated|never|only|unlike|heuristic", re.I)
EXT = (".md", ".sh", ".py", ".json", ".txt")
# First path segments that belong to a different API (core REST, Action API) and are
# therefore never candidates for an AQS /metrics/ module path.
CORE_FIRST = {"page", "transform", "data", "feed", "w", "wiki", "api", "rest_v1", "core"}


def template_regex(tmpl: str) -> str:
    parts = [r"[^/]+" if (s.startswith("{") and s.endswith("}")) else re.escape(s)
             for s in tmpl.strip("/").split("/")]
    return "^/" + "/".join(parts) + "/?$"


def normalise(path: str) -> str:
    path = path.split("?", 1)[0].split("#", 1)[0]
    path = re.sub(r"\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*|<[^>]*>", "X", path)  # $VAR, ${VAR}, <x>
    return "/" + PLACEHOLDER_RE.sub("X", re.sub(r"/{2,}", "/", path)).strip("/")


def seg_ok(seg: str, tseg: str) -> bool:
    """A template segment that is a placeholder matches anything."""
    return (tseg.startswith("{") and tseg.endswith("}")) or seg == tseg


def is_prefix_of_template(segs, template_segs) -> bool:
    return len(segs) <= len(template_segs) and all(seg_ok(s, t)
                                                   for s, t in zip(segs, template_segs))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", default=str(DEFAULT_SURFACE))
    ap.add_argument("--skills-dir", default=str(DEFAULT_SKILLS_DIR))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    surface = json.loads(Path(args.surface).read_text())
    metrics_templates = [t for t in surface.get("paths", []) if t.startswith("/metrics/")]
    compiled = [(t, re.compile(template_regex(t)), t.strip("/").split("/")) for t in metrics_templates]
    modules = {t.strip("/").split("/")[1] for t in metrics_templates}
    # The segment after /metrics/<module>/ — e.g. 'top', 'per-article', 'aggregate'.
    # Used to decide whether a bare `GET /x/…` path is even a candidate for an AQS module.
    SUBPATHS = {t.strip("/").split("/")[2] for t in metrics_templates if len(t.strip("/").split("/")) > 2}

    violations, checked = [], 0
    root = Path(args.skills_dir)
    files = [f for f in sorted(root.rglob("*"))
             if f.is_file() and f.suffix.lower() in EXT
             and not any(part.startswith(".") for part in f.relative_to(root).parts[:-1])]

    for f in files:
        rel = str(f.relative_to(REPO_ROOT)) if str(f).startswith(str(REPO_ROOT)) else str(f)
        for lineno, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
            cands = []
            for m in URL_RE.finditer(line):
                cands.append(m.group(0).split("/api/rest_v1/", 1)[1])
            for m in BARE_RE.finditer(line):
                cands.append(m.group(1))
            for raw in cands:
                if raw.rstrip("/").endswith(".json"):
                    continue  # a spec/doc link, not an endpoint
                if "..." in raw or "…" in raw:
                    continue  # an elided path ("…/metrics/pageviews/…"), not a concrete endpoint
                cand = normalise(raw)
                segs = cand.strip("/").split("/")
                if segs[0] == "metrics":
                    if len(segs) < 2 or segs[1] not in modules:
                        continue  # a metrics module with no spec in the surface — out of scope
                    checked += 1
                    if any(rx.match(cand) or is_prefix_of_template(segs, tsegs)
                           for _, rx, tsegs in compiled):
                        continue
                    violations.append({"file": rel, "line": lineno, "kind": "unknown-path",
                                       "value": cand, "text": line.strip()[:170]})
                    continue
                # A relative endpoint path (`GET /top-by-ec/{project}/…`) names the module
                # implicitly: resolve it against the modules the file itself mentions.
                first = segs[0]
                if first in CORE_FIRST or not first:
                    continue  # a core REST (/page/…) or Action API (/w/…) path — not this check
                mods = re.findall(r"/metrics/([a-z-]+)", f.read_text(errors="replace")) or \
                    [m for m in modules if m in f.parts[-3] or m in rel]
                mods = [m for m in dict.fromkeys(mods) if m in modules]
                if not mods:
                    continue
                hit = False
                for mod in mods:
                    trial = normalise(f"/metrics/{mod}/{cand.strip('/')}")
                    tsegs = trial.strip("/").split("/")
                    checked += 1
                    if any(rx.match(trial) or is_prefix_of_template(tsegs, ts)
                           for _, rx, ts in compiled):
                        hit = True
                        break
                if not hit:
                    violations.append({"file": rel, "line": lineno, "kind": "unknown-path",
                                       "value": cand, "text": line.strip()[:170]})

    for key, info in (surface.get("params") or {}).items():
        pname = key.split(":", 1)[1]
        names = {pname, pname.replace("_", "-")}
        invalid = info.get("invalid") or {}
        valid = info.get("valid") or []
        if not invalid:
            continue
        for f in files:
            if f.suffix.lower() not in (".md", ".sh", ".py"):
                continue
            rel = str(f.relative_to(REPO_ROOT)) if str(f).startswith(str(REPO_ROOT)) else str(f)
            for lineno, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
                low = line.lower()
                name_rx = re.compile(r"(?<![a-z0-9_-])(" + "|".join(map(re.escape, sorted(names))) + r")(?![a-z0-9_-])`?\s*[=∈:(|/]")
                m = name_rx.search(low)
                if not m or CUE_RE.search(line):
                    continue
                window = low[m.start():m.start() + 90]
                # only an enumeration context counts: a valid value must sit beside the
                # parameter name, otherwise this is prose about traffic in general
                if not any(re.search(r"(?<![a-z0-9_-])" + re.escape(v) + r"(?![a-z0-9_-])", window) for v in valid):
                    continue
                for bad, code in invalid.items():
                    if re.search(r"(?<![a-z0-9_-])" + re.escape(bad) + r"(?![a-z0-9_-])", window):
                        violations.append({"file": rel, "line": lineno, "kind": "invalid-value",
                                           "param": pname, "value": bad, "http_status": code,
                                           "text": line.strip()[:170]})

    if args.json:
        print(json.dumps({"violations": violations, "count": len(violations),
                          "paths_checked": checked, "templates": len(metrics_templates)}, indent=1))
    elif not violations:
        print(f"verify-rest-enums: clean — {checked} AQS path references checked against "
              f"{len(metrics_templates)} live templates; "
              f"{len(surface.get('params', {}))} probed parameter sets")
    else:
        print(f"verify-rest-enums: {len(violations)} violation(s) "
              f"({checked} AQS path references checked)\n")
        for v in violations:
            if v["kind"] == "unknown-path":
                print(f"  {v['file']}:{v['line']}  unknown endpoint: {v['value']}")
            else:
                print(f"  {v['file']}:{v['line']}  {v['param']}={v['value']} -> HTTP {v['http_status']}")
            print(f"      | {v['text']}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
