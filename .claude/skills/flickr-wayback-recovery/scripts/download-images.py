#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download the best archived image for every photo in rescue_out/metadata.json.

Strategy, in order:
  1. the largest size listed in metadata['sizes'] (o > k > h > l > c > z > m ...),
     fetched through  https://web.archive.org/web/<page_ts>id_/<staticflickr-url>
  2. image URLs embedded in the cached archived page HTML
     (some pages carry their own //web.archive.org/web/<ts>/<img-url> copies).

State: images/<id>.<ext> + images.json ({ext, bytes, url, ts}). Resumable:
photos already present with the recorded byte count are skipped. Downloads are
validated by magic bytes (Wayback returns HTML error pages with HTTP 200).

Usage:
  python3 download-images.py --sleep 1 [--id 10964377675]
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request

UA = "flickr-wayback-recovery/1.0 (contact@example.org)"
SUFFIX_ORDER = ["o", "k", "h", "l", "c", "z", "m", "n", "s", "t", "q", "sq"]
MAGIC = [(b"\xff\xd8\xff", "jpg"), (b"\x89PNG\r\n\x1a\n", "png"),
         (b"GIF87a", "gif"), (b"GIF89a", "gif")]


def looks_like_image(blob):
    for magic, ext in MAGIC:
        if blob.startswith(magic):
            return ext
    return None


def suffix_of(url):
    # Flickr m-size URLs have no suffix (…_<secret>.jpg); everything else ends
    # in _<1-2 letters>.<ext> (s,q,t,n,w,m,z,c,b,h,k,o). Match only short
    # suffix letters so the secret is not mistaken for a size suffix.
    m = re.search(r"_([a-z]{1,2})\.(?:jpg|jpeg|png|gif)$", url)
    return m.group(1) if m else "m"


def http_get(url, retries=6, timeout=90):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def archived_image_urls(meta, page_dir="pages"):
    """Yield (url, label) candidates, best size first."""
    sizes = meta.get("sizes") or {}
    ts = meta.get("archive_ts") or ""
    ranked = sorted(
        ((k, s) for k, s in sizes.items() if isinstance(s, dict) and s.get("url")),
        key=lambda kv: (SUFFIX_ORDER.index(kv[0])
                        if kv[0] in SUFFIX_ORDER else len(SUFFIX_ORDER)),
    )
    for key, s in ranked:
        u = s["url"]
        if u.startswith("//"):
            u = "https:" + u
        if "web.archive.org" in u:
            yield u, key
        elif ts:
            yield f"https://web.archive.org/web/{ts}id_/{u}", key

    # Fallback: sizes embedded in the cached page HTML.
    page_file = meta.get("page_file")
    if page_file:
        path = os.path.join(page_dir, page_file)
        if os.path.exists(path):
            html = open(path, encoding="utf-8", errors="replace").read()
            for u in sorted(set(re.findall(r"//web\.archive\.org/web/(\d+)id_?/(https?://[^\s\"'<>]+\.(?:jpg|jpeg|png|gif))", html)),
                            key=lambda x: -SUFFIX_ORDER.index(suffix_of(x[1]))
                            if suffix_of(x[1]) in SUFFIX_ORDER else 0):
                yield f"https://web.archive.org/web/{u[0]}id_/{u[1]}", suffix_of(u[1])

    # Fallback: CDX-discovered image URLs (see scan-cdx-images.py) — the only
    # source when the archived page is an SPA shell with no modelExport.
    # Order best size first so the first successful download is the largest.
    if os.path.exists("rescue_out/image_scan.json"):
        with open("rescue_out/image_scan.json", encoding="utf-8") as f:
            scan = json.load(f)
        recs = [r for r in (scan.get(meta.get("id") or str(meta.get("flickr_id", "")), []) or [])
                if len(r) >= 2 and r[0] and r[1]]
        recs.sort(key=lambda r: SUFFIX_ORDER.index(suffix_of(r[1]))
                  if suffix_of(r[1]) in SUFFIX_ORDER else len(SUFFIX_ORDER))
        for ts, orig, *_ in recs:
            yield f"https://web.archive.org/web/{ts}id_/{orig}", suffix_of(orig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--meta", default="rescue_out/metadata.json")
    ap.add_argument("--images", default="images")
    ap.add_argument("--pages", default="pages")
    ap.add_argument("--state", default="images.json")
    ap.add_argument("--sleep", type=float, default=1.0)
    ap.add_argument("--id", type=int)
    args = ap.parse_args()

    os.makedirs(args.images, exist_ok=True)
    with open(args.meta, encoding="utf-8") as f:
        meta = json.load(f)
    state = {}
    if os.path.exists(args.state):
        with open(args.state, encoding="utf-8") as f:
            state = json.load(f)

    ok = failed = skipped = 0
    for pid_s, rec in sorted(meta.items(), key=lambda kv: int(kv[0])):
        if args.id and int(pid_s) != args.id:
            continue
        if rec.get("error"):
            continue
        # Skip when a complete local file is already recorded.
        cur = state.get(pid_s) or {}
        if cur.get("ext") and cur.get("bytes"):
            path = os.path.join(args.images, f"{pid_s}.{cur['ext']}")
            if os.path.exists(path) and os.path.getsize(path) == cur["bytes"]:
                skipped += 1
                continue
        saved = False
        for url, label in archived_image_urls(rec, args.pages):
            try:
                blob = http_get(url)
            except Exception as e:
                print(f"[{pid_s}] fetch {label} failed: {e}", flush=True)
                continue
            ext = looks_like_image(blob)
            if not ext:
                print(f"[{pid_s}] {label} not an image (HTML error page?)", flush=True)
                continue
            out = os.path.join(args.images, f"{pid_s}.{ext}")
            with open(out, "wb") as f:
                f.write(blob)
            state[pid_s] = {"ext": ext, "bytes": len(blob),
                            "url": url, "ts": rec.get("archive_ts")}
            ok += 1
            print(f"[{pid_s}] saved {ext} {len(blob)} bytes from {label}", flush=True)
            saved = True
            break
        if not saved:
            failed += 1
            print(f"[{pid_s}] NO IMAGE", flush=True)
        time.sleep(args.sleep)

    with open(args.state, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1)
    print(f"\ndownloaded {ok}, skipped {skipped}, failed {failed}")


if __name__ == "__main__":
    main()
