#!/usr/bin/env python3
"""MinT translation CLI — translate text or files via the Wikimedia MinT service.

Usage:
  python3 translate.py "Jazz is a music genre." en es
  python3 translate.py --file article.md --format markdown en fr
  python3 translate.py --list-languages en
  python3 translate.py "Hello world" en hi --provider indictrans2-indic-en

Stdlib only — no pip dependencies.
"""
import argparse
import json
import sys
import urllib.parse
import urllib.request

API = "https://translate.wmcloud.org"
UA = "mint-skill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; research) translate.py"


def request(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data,
                                 headers={"User-Agent": UA,
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.load(resp)


def translate(content, source, target, provider=None, fmt="text"):
    body = {"content": content, "source_language": source,
            "target_language": target, "format": fmt}
    if provider:
        body["provider"] = provider
    return request("/api/translate", body)


def list_languages(source=None):
    langmap = request("/api/languages")
    if source is None:
        return langmap
    # map: target -> source -> [models]; show targets that accept `source`
    targets = {tgt: models for tgt, srcs in langmap.items()
               if source in srcs for models in [srcs[source]]}
    return targets


def main():
    ap = argparse.ArgumentParser(description="Translate via Wikimedia MinT")
    ap.add_argument("text", nargs="*", help="Text to translate; or with --file, the source and target codes")
    ap.add_argument("--file", help="Read content from a file instead of the text argument")
    ap.add_argument("--format", default="text", choices=["html", "json", "markdown", "text", "svg", "webpage"],
                    help="Input format (default: text)")
    ap.add_argument("--provider", help="Model provider (see /api/languages); defaults to the pair's first model")
    ap.add_argument("--list-languages", metavar="SOURCE", nargs="?", const="", help="List target languages (optionally for a source language)")
    args = ap.parse_args()

    if args.list_languages is not None:
        src = args.list_languages or None
        langmap = list_languages(src)
        for tgt in sorted(langmap):
            models = langmap[tgt]
            print(f"{tgt:8s} {', '.join(models)}")
        return

    pos = args.text
    if args.file:
        if len(pos) != 2:
            ap.error("with --file, provide source and target as positional arguments")
        content = open(args.file, encoding="utf-8").read()
        source, target = pos
    else:
        if len(pos) != 3:
            ap.error("text, source, and target are required (or use --file SOURCE TARGET)")
        content, source, target = pos

    result = translate(content, source, target, args.provider, args.format)
    print(result["translation"])
    if result.get("translationtime") is not None:
        print(f"# model={result.get('model')} time={result.get('translationtime'):.2f}s",
              file=sys.stderr)


if __name__ == "__main__":
    main()
