#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find archived image URLs for Flickr photo IDs via CDX wildcard queries.

Use this when the archived photo page is an SPA shell (no modelExport, no
'sizes' in metadata.json) but the image bytes may still be in the Wayback.
The Wayback crawler follows <img>/og:image URLs to the Flickr image host even
when the page itself is a shell, so image discovery has to query CDX directly.

Key CDX lesson (from the 184802432@N05 rescue): a glob pattern like
`live.staticflickr.com/65535/<id>_*` finds all size captures only when the
`*` is a plain trailing wildcard with NO matchType. Do NOT add
`matchType=prefix` (the `*` is then treated as a literal character and you
get zero rows), and do NOT prefix the domain with `*` (e.g.
`*.staticflickr.com/*<id>_*` returns only generic staticflickr.com root
captures). For each ID first try the exact image host+server path that the
page model would produce, then a host-level wildcard fallback.

State: writes rescue_out/image_scan.json:
  { "<id>": [ [timestamp, original, statuscode, mimetype], ... ] }  (unique
  originals, ordered by CDX response). Resumable per --id / --ids-file.

Usage:
  python3 scan-cdx-images.py wayback_photo_ids.txt
  python3 scan-cdx-images.py wayback_photo_ids.txt --id 52157420557
  python3 scan-cdx-images.py --ids-file gone_ids.txt --host live.staticflickr.com/65535
"""
import argparse
import json
import os
import re
import time
import urllib.parse
import urllib.request

UA = "flickr-wayback-recovery/1.0 (contact@example.org)"
CDX = "https://web.archive.org/cdx/search/cdx"

# Default host patterns tried per ID. First pattern with rows wins.
#   {host}  - "live.staticflickr.com/65535"   (modern Flickr image host+server)
#   {id}    - the photo ID
DEFAULT_HOSTS = [
    "live.staticflickr.com/65535",
    "live.staticflickr.com",
    "farm66.staticflickr.com/65535",
    "farm8.staticflickr.com/65535",
]

# Flickr size letters by URL suffix, largest first. 'b' and 'l' both map to
# _b.jpg; the model's 's' size is served as _m.jpg; 'm' has no suffix.
SUFFIX_RANK = {"_o": 13, "_k": 12, "_h": 11, "_b": 10, "_c": 9, "_z": 8,
               "_w": 7, "_m": 6, "_n": 5, "_s": 4, "_t": 3, "_q": 2, "_sq": 1}
SUFFIX_RE = re.compile(r"_([a-z]{1,2})\.(?:jpg|jpeg|png|gif)$")


def rank(url):
    m = SUFFIX_RE.search(url)
    return SUFFIX_RANK.get("_" + m.group(1), 5) if m else 5


def cdx(params, timeout=120, tries=5):
    """CDX query. `url` is a glob; never pass matchType with a '*' pattern."""
    qs = urllib.parse.urlencode({**params, "output": "json"})
    req = urllib.request.Request(f"{CDX}?{qs}", headers={"User-Agent": UA})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                rows = json.load(r)
            return rows[1:] if rows else []
        except urllib.error.HTTPError as e:
            if e.code in (503, 504) and attempt < tries - 1:
                time.sleep(12 * (attempt + 1))
                continue
            return f"ERR {e.code}"
        except Exception as e:
            if attempt < tries - 1:
                time.sleep(8 * (attempt + 1))
                continue
            return f"ERR {e}"


def image_captures(pid, hosts):
    """All image captures for one ID across the given host+server paths.

    Pattern is always `<host>/<id>_*` (a trailing wildcard, NO matchType). The
    host strings in `hosts` already include the server path to guess (modern
    photos live under `live.staticflickr.com/65535/`). First host with hits
    wins; later hosts are only consulted if earlier ones return nothing.
    """
    out = {}
    for host in hosts:
        host = host.rstrip("/")
        rows = cdx({"url": f"{host}/{pid}_*", "fl": "timestamp,original,statuscode,mimetype",
                    "limit": "60"})
        if not isinstance(rows, str):
            for row in rows:
                if len(row) < 4:
                    continue
                ts, orig, status, mime = row[:4]
                orig = orig.split("&quot;")[0].split('"')[0]
                out.setdefault(orig, [ts, orig, status, mime])
            if rows:
                break
        time.sleep(1.0)
    return sorted(out.values())


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ids_file", nargs="?", help="file with one photo ID per line")
    ap.add_argument("--id", type=int)
    ap.add_argument("--host", action="append", dest="hosts",
                    help="image host+server to scan (repeatable); default: live.staticflickr.com/65535 …")
    ap.add_argument("--out", default="rescue_out/image_scan.json")
    ap.add_argument("--sleep", type=float, default=1.0)
    args = ap.parse_args()

    if args.id:
        pids = [args.id]
    elif args.ids_file:
        with open(args.ids_file, encoding="utf-8") as f:
            pids = [int(x) for x in f if x.strip()]
    else:
        ap.error("need --id or an ids file")

    hosts = args.hosts or DEFAULT_HOSTS
    out = {}
    if os.path.exists(args.out):
        with open(args.out, encoding="utf-8") as f:
            out = json.load(f)
    for pid in pids:
        if str(pid) in out:
            continue
        caps = image_captures(pid, hosts)
        if caps:
            out[str(pid)] = caps
            ok = sum(1 for c in caps if c[2] == "200")
            print(f"{pid}: {len(caps)} captures, {ok} with 200; best={max((rank(c[1]) for c in caps if c[2]=='200'), default=0)}")
            for c in caps[:3]:
                print(f"     {c}")
        else:
            print(f"{pid}: no image captures")
        time.sleep(args.sleep)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\nsaved {args.out} with {len(out)} IDs")


if __name__ == "__main__":
    main()
