#!/usr/bin/env python3
"""Build a ground-truth surface for the Wikimedia REST + AQS metrics APIs.

Two things are recorded, both from live sources:

  1. PATH TEMPLATES — from the AQS OpenAPI specs (pageviews, mediarequests, edits)
     and the REST API core spec (en.wikipedia /w/rest_v1/). Used to catch
     documented endpoints that do not exist (e.g. `/pageviews/top-by-ec/...`).

  2. PARAMETER VALUES — by probing one representative URL per value and
     recording the HTTP status. The specs do not carry these enums, so the only
     ground truth is the live service: `agent_type=automated` returns 400, and
     that fact belongs in a machine-checkable file, not in prose.

Polite by construction: one request per probe at >=1.1s pacing, descriptive UA,
429/503 retried with backoff.

Usage: python3 scripts/refresh-rest-surface.py
Writes: scripts/rest-surface.json
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = ("Wikipedia-AI-Skills/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills) "
      "refresh-rest-surface")

AQS_SPECS = {
    "pageviews": "https://wikimedia.org/api/rest_v1/metrics/pageviews/api-spec.json",
    "mediarequests": "https://wikimedia.org/api/rest_v1/metrics/mediarequests/api-spec.json",
    "edits": "https://wikimedia.org/api/rest_v1/metrics/edits/api-spec.json",
    "commons-analytics": "https://wikimedia.org/api/rest_v1/metrics/commons-analytics/api-spec.json",
}
CORE_SPEC = "https://en.wikipedia.org/api/rest_v1/?spec"

BASE_PV = "https://wikimedia.org/api/rest_v1/metrics/pageviews"
BASE_MR = "https://wikimedia.org/api/rest_v1/metrics/mediarequests"

# Representative URL per candidate value. Whatever the service answers is the
# ground truth; values that 400/404 are recorded as invalid, not omitted.
PROBES = {
    "pageviews:access": (f"{BASE_PV}/per-article/en.wikipedia/{{v}}/user/Albert_Einstein/monthly/20260101/20260131",
                         ["all-access", "desktop", "mobile-web", "mobile-app", "all-access-all", "desktop-site"]),
    "pageviews:agent": (f"{BASE_PV}/per-article/en.wikipedia/all-access/{{v}}/Albert_Einstein/monthly/20260101/20260131",
                        ["all-agents", "user", "spider", "automated", "bot"]),
    "mediarequests:agent_type": (f"{BASE_MR}/aggregate/all-referers/image/{{v}}/monthly/20260801/20260901",
                                 ["user", "spider", "all-agents", "automated"]),
    "mediarequests:referer": (f"{BASE_MR}/aggregate/{{v}}/image/user/monthly/20260801/20260901",
                              ["all-referers", "internal", "external", "unknown", "none", "search-engine"]),
    "mediarequests:media_type": (f"{BASE_MR}/aggregate/all-referers/{{v}}/user/monthly/20260801/20260901",
                                 ["image", "audio", "video", "all-media-types", "other", "document"]),
}


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                r.read(400)
                return r.status
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and i + 1 < tries:
                time.sleep(4 * (i + 1))
                continue
            return e.code
        except Exception:
            if i + 1 < tries:
                time.sleep(2)
                continue
            return None
    return None


def json_get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and i + 1 < tries:
                time.sleep(4 * (i + 1))
                continue
            raise
    raise RuntimeError(url)


def main():
    out = {
        "generated_by": "scripts/refresh-rest-surface.py",
        "note": ("Paths come from the live OpenAPI/REST specs; parameter values are probed "
                 "live. A value listed under 'invalid' returns 400/404 and must never be "
                 "presented in a skill as usable."),
        "paths": [],
        "modules": {},
        "params": {},
    }

    for mod, url in AQS_SPECS.items():
        try:
            spec = json_get(url)
        except Exception as e:
            print(f"  !! spec {mod}: {e}", file=sys.stderr)
            continue
        paths = sorted((spec.get("paths") or {}).keys())
        full = []
        for p in paths:
            p2 = p
            for pre in ("/metrics/", "/" + mod + "/"):   # specs are inconsistent about prefixes
                if p2.startswith(pre):
                    p2 = p2[len(pre):]
            full.append("/metrics/" + mod + "/" + p2.lstrip("/"))
        out["modules"][mod] = {"spec": url, "path_count": len(full), "paths": full}
        out["paths"].extend(full)
        print(f"  spec {mod}: {len(full)} paths")
        time.sleep(1.2)

    try:
        core = json_get(CORE_SPEC)
        cpaths = sorted((core.get("paths") or {}).keys())
        out["modules"]["core_rest"] = {"spec": CORE_SPEC, "path_count": len(cpaths), "paths": cpaths}
        out["paths"].extend(cpaths)
        print(f"  spec core_rest: {len(cpaths)} paths")
    except Exception as e:
        print(f"  !! spec core_rest: {e}", file=sys.stderr)

    print("  probing parameter values (>=1.1s pacing):")
    for key, (tmpl, values) in PROBES.items():
        valid, invalid = [], {}
        for v in values:
            url = tmpl.format(v=v)
            code = get(url)
            time.sleep(1.1)
            if code == 200:
                valid.append(v)
            else:
                invalid[v] = code
        out["params"][key] = {"template": tmpl, "valid": valid, "invalid": invalid}
        print(f"    {key:26s} valid={valid} invalid={invalid}")

    with open("scripts/rest-surface.json", "w") as f:
        json.dump(out, f, indent=1)
    print(f"wrote scripts/rest-surface.json — {len(out['paths'])} path templates, "
          f"{len(out['params'])} probed parameters")


if __name__ == "__main__":
    main()
