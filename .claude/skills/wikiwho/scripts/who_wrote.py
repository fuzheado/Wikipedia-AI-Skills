#!/usr/bin/env python3
"""Who wrote this? — authorship breakdown of a Wikipedia article via the WikiWho API.

Fetches token-level attribution for an article (current or historical revision),
counts tokens per editor, and resolves user IDs to usernames via the Action API.

Usage:
  ./who_wrote.py "Albert Einstein"              # current revision, enwiki
  ./who_wrote.py "Albert Einstein" 123456789    # specific revision
  ./who_wrote.py "Albert Einstein" --lang de    # German Wikipedia
  ./who_wrote.py "Albert Einstein" --top 10 --csv out.csv

Stdlib only — no pip dependencies.
"""
import argparse
import collections
import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://wikiwho-api.wmcloud.org/{lang}/api/v1.0.0-beta"
UA = "wikiwho-skill/1.0 (https://github.com/fuzheado/Wikipedia-AI-Skills; research) who_wrote.py"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        # 400 = bad title/lang, 408 = server timeout (retry), 503 = down (back off)
        sys.exit(f"error: WikiWho API returned {e.code} {e.reason} for {url}\n"
                 f"       Check the article title and language code "
                 f"(the article may not exist in that wiki).")


def resolve_users(user_ids, wiki_domain):
    """Resolve WikiWho editor IDs (integers) to usernames. Anonymous (0 / '0|<ip>') are passed through."""
    names = {}
    ids = [u for u in user_ids if str(u).isdigit() and int(u) > 0]
    for i in range(0, len(ids), 50):
        q = urllib.parse.urlencode({
            "action": "query", "list": "users",
            "ususerids": "|".join(map(str, ids[i:i + 50])), "format": "json",
        })
        data = get(f"https://{wiki_domain}/w/api.php?{q}")
        for u in data.get("query", {}).get("users", []):
            names[str(u["userid"])] = u.get("name", "(deleted)")
    return names


def fetch_tokens(article, rev_id, lang):
    base = API.format(lang=lang)
    if rev_id:
        data = get(f"{base}/rev_content/{article}/{rev_id}/?editor=true")
        key = str(rev_id)
    else:
        data = get(f"{base}/latest_rev_content/{article}/?editor=true")
        key = list(data["revisions"][0].keys())[0]
    return data, data["revisions"][0][key]["tokens"]


def main():
    ap = argparse.ArgumentParser(description="Authorship breakdown via WikiWho")
    ap.add_argument("article", help="Wikipedia article title (spaces ok)")
    ap.add_argument("rev_id", nargs="?", default=None, help="Optional revision ID")
    ap.add_argument("--lang", default="en", help="Wikipedia language code (default: en)")
    ap.add_argument("--domain", default=None, help="API domain for username resolution (default: <lang>.wikipedia.org)")
    ap.add_argument("--top", type=int, default=None, help="Show only the top N editors")
    ap.add_argument("--csv", default=None, help="Also write results to a CSV file")
    args = ap.parse_args()

    wiki_domain = args.domain or f"{args.lang}.wikipedia.org"
    data, tokens = fetch_tokens(args.article, args.rev_id, args.lang)
    counts = collections.Counter(t.get("editor", "?") for t in tokens)
    names = resolve_users(list(counts), wiki_domain)
    total = len(tokens)

    rows = []
    for editor, n in counts.most_common():
        display = names.get(editor, editor)
        pct = 100.0 * n / total
        rows.append((display, n, round(pct, 1)))

    if args.top:
        rows = rows[:args.top]
    for display, n, pct in rows:
        print(f"{display:26s} {n:6d} tokens  {pct:5.1f}%")

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["editor", "tokens", "pct"])
            w.writerows(rows)
    print(f"\narticle: {data.get('article_title')} | page_id: {data.get('page_id')} | tokens: {total}")


if __name__ == "__main__":
    main()
