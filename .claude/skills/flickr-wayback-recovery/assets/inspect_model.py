#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract and resolve the `modelExport` JSON blob from an archived Flickr page.

Flickr embeds a serialized JSON blob inside a `<script class="modelExport">`
tag. The blob uses a "cyclical JSON" format: ``data["main"]`` holds the page
objects (``photo-models``, ``person-models``, ``photo-stats-models``,
``photo-head-meta-models``) and strings like ``"~3"`` reference
``data["legend"]`` entries. ``resolve_model`` replaces those references so the
caller can read plain nested dicts.

Usage:
    python inspect_model.py <archived-photo-page.html>
"""
import json
import re
import sys


def extract_model(html):
    """Return the parsed modelExport dict, or None if the page has no blob.

    The real blob is the *first* `modelExport: {` occurrence after the
    `<script class="modelExport"` tag; the token also appears in JS
    comments/code before it.
    """
    idx = html.find('<script class="modelExport"')
    if idx == -1:
        idx = html.find("<script class='modelExport'")
    if idx == -1:
        return None
    seg = html[idx:]
    m = re.search(r"modelExport:\s*(\{)", seg)
    if not m:
        return None
    start = m.start(1)
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(seg)):
        c = seg[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(seg[start:i + 1])
    return None


REF_RE = re.compile(r"^~(\d+)$")


def _resolve_path(main, path):
    """Navigate main by a legend path like ['photo-models','0','engagement']."""
    cur = main
    for part in path:
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def resolve_model(data):
    """Resolve cyclical-json string references (~N) in data['main'].

    Returns a deep copy of main where every `~N` string has been replaced by
    the object found at legend[N] inside main.
    """
    main = data.get("main", {})
    legend = data.get("legend", [])
    cache = {}
    for idx, path in enumerate(legend):
        try:
            cache["~%d" % idx] = _resolve_path(main, path)
        except Exception:
            cache["~%d" % idx] = None

    def clone(node):
        if isinstance(node, dict):
            return {k: clone(v) for k, v in node.items()}
        if isinstance(node, list):
            return [clone(v) for v in node]
        if isinstance(node, str):
            m = REF_RE.match(node)
            if m:
                target = cache.get(node)
                return clone(target) if target is not None else node
        return node

    return {k: clone(v) for k, v in main.items()}


def photo_metadata(data):
    """Extract the metadata fields a Commons manifest needs from a page.

    Returns a dict with title/description/license/dateTaken/datePosted/tags/
    owner/sizes, or None if the page has no usable photo model.
    """
    main = resolve_model(data)
    photos = main.get("photo-models") or []
    if not photos or not isinstance(photos[0], dict):
        return None
    p = photos[0]
    stats = (main.get("photo-stats-models") or [{}])[0]
    if not isinstance(stats, dict):
        stats = {}
    meta = (main.get("photo-head-meta-models") or [{}])[0]
    if not isinstance(meta, dict):
        meta = {}
    owner = None
    people = main.get("person-models") or []
    if people and isinstance(people[0], dict):
        o = people[0]
        owner = {
            "nsid": o.get("id"),
            "path_alias": o.get("pathAlias"),
            "username": o.get("username"),
            "realname": o.get("realname"),
        }
    elif isinstance(p.get("owner"), dict):
        o = p["owner"]
        owner = {
            "nsid": o.get("id"),
            "path_alias": o.get("pathAlias"),
            "username": o.get("username"),
            "realname": o.get("realname"),
        }
    keywords = meta.get("keywords") or ""
    tags = [t.strip() for t in url_decode(keywords).split(",") if t.strip()]
    sizes = p.get("sizes") or {}
    # Normalize older-page shape (displayUrl) to the {url: ...} shape the
    # downloader expects.
    if isinstance(sizes, dict):
        sizes = {
            k: dict(v, url=v.get("url") or v.get("displayUrl"))
            for k, v in sizes.items() if isinstance(v, dict)
        }
    return {
        "id": p.get("id") or stats.get("id"),
        "title": url_decode(p.get("title") or ""),
        "description": url_decode(p.get("description") or ""),
        "license": p.get("license"),
        "dateTaken": url_decode(stats.get("dateTaken") or ""),
        "datePosted": stats.get("datePosted"),
        "tags": tags,
        "owner": owner,
        "secret": p.get("secret"),
        "oWidth": p.get("oWidth"),
        "oHeight": p.get("oHeight"),
        "sizes": sizes,
    }


def url_decode(s):
    """Flickr percent-encodes metadata with latin-1 (ISO-8859-1) bytes."""
    if not s:
        return ""
    import urllib.parse
    try:
        return urllib.parse.unquote_to_bytes(s).decode("latin-1")
    except Exception:
        return s


if __name__ == "__main__":
    path = sys.argv[1]
    html = open(path, encoding="utf-8", errors="replace").read()
    data = extract_model(html)
    if not data:
        print("modelExport: NOT FOUND")
        sys.exit(1)
    print("modelExport: FOUND")
    meta = photo_metadata(data)
    if meta:
        print(json.dumps(meta, ensure_ascii=False, indent=2))
    else:
        print("no photo model in this page")
