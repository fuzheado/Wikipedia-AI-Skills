#!/usr/bin/env python3
"""Build per-file person labels for a Commons category tree (evaluation ground truth).

    python3 person_ground_truth.py "Category:Erasmus Prize 2015" [--out gt.json] [--max-depth 3]

Why this exists: event categories on Commons are usually already person-categorised
(`Category:Jane Doe in 2015`, `Category:Jane Doe`), which is free ground truth for any
people-recognition experiment. The hard part is not the API, it is resolving a category
name to the right human: Commons category items are P31=Q4167836 whose P301 points at the
person, so checking P31=Q5 alone silently matches nothing.

Prints files / labelled files / people / pairs, plus every category it could NOT map.
Read that list: a name that reads like a person means a qualifier shape is missing; one
that reads like a work or a building means the blacklist needs widening.

All data is public Wikimedia content; no credentials are used.
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "HermesAgent/1.0 (https://en.wikipedia.org/wiki/User:Fuzheado) PersonGroundTruth/1.0"
API_DELAY = 0.2  # seconds between requests; Commons 429s a fast anonymous walk

BLACK = re.compile(
    r'(portrait paintings|paintings by|collections?|trust|ceremonial|guards?|'
    r'births|deaths|alumni|staff|board members|users in|wikimedians|wikipedians|'
    r'photographs by|interiors?|facades?|squares|stations?)',
    re.I)

# qualifier shapes seen on real event categories, longest first
QUALIFIERS = [
    r'^(.*?) in \d{4}$',
    r'^(.*?) in the \d{4}s$',
    r'^(.*?) in the Netherlands$',
    r'^(.*?) (?:smiling|gesturing with hands|shaking hands|facing forward)$',
    r'^(.*?) (?:with people|with objects|with microphones)$',
    r'^(.*?) wearing .*$',
    r'^(.*?) by year$',
]

_cache = {}
_last = [0.0]


def api(params, host="commons.wikimedia.org"):
    """One API call with rate limiting and Retry-After handling (429 is normal, not fatal)."""
    key = (host, tuple(sorted(params.items())))
    if key in _cache:
        return _cache[key]
    p = dict(params)
    p['format'] = 'json'
    url = "https://%s/w/api.php?%s" % (host, urllib.parse.urlencode(p))
    wait = 2
    for attempt in range(6):
        gap = time.time() - _last[0]
        if gap < API_DELAY:
            time.sleep(API_DELAY - gap)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            out = json.load(urllib.request.urlopen(req, timeout=60))
            _cache[key] = out
            return out
        except urllib.error.HTTPError as e:
            retry = e.headers.get('Retry-After') if hasattr(e, 'headers') else None
            if attempt == 5:
                raise
            time.sleep(min(60, int(retry) if retry and retry.isdigit() else wait))
            wait = min(wait * 2, 30)
        except Exception:  # noqa: BLE001  network blips are retried, then raised
            if attempt == 5:
                raise
            time.sleep(wait)
            wait = min(wait * 2, 30)
    raise RuntimeError(url)


def batches(titles, maxlen=3500, maxcount=50):
    """Yield batches of titles whose URL-encoded size stays under maxlen.

    Commons file titles are long ("File:2015 Erasmus Prize - 25 November 2015 - Stiftung
    Praemium Erasmianum (101).JPG"), so the usual "50 titles per call" rule overflows the
    URL: a 282-file walk answered HTTP 414 URI Too Long at the first 50-title batch. Batch
    by encoded length, not by count — but keep the count cap too, because the Action API
    rejects more than 50 titles per request even when the URL would fit.
    """
    cur, used = [], 0
    for t in titles:
        size = len(urllib.parse.quote(t)) + 3
        if cur and (used + size > maxlen or len(cur) >= maxcount):
            yield cur
            cur, used = [], 0
        cur.append(t)
        used += size
    if cur:
        yield cur


def pageitems(titles):
    out = {}
    for batch in batches(list(titles)):
        r = api({'action': 'query', 'prop': 'pageprops', 'ppprop': 'wikibase_item',
                 'titles': '|'.join(batch)})
        if 'query' not in r:
            raise RuntimeError('API refused a titles batch: %s' % json.dumps(r)[:300])
        for p in r['query']['pages'].values():
            q = p.get('pageprops', {}).get('wikibase_item')
            if q:
                out[p['title']] = q
    return out


def claims(qids):
    out = {}
    qids = sorted({q for q in qids if q})
    for batch in batches(qids, 3000):
        r = api({'action': 'wbgetentities', 'ids': '|'.join(batch),
                 'props': 'claims|labels', 'languages': 'en|mul|nl|de'},
                host='www.wikidata.org')
        for q, ent in r.get('entities', {}).items():
            cl = ent.get('claims', {})
            get = lambda pid: [c['mainsnak'].get('datavalue', {}).get('value', {}).get('id')
                               for c in cl.get(pid, []) if c['mainsnak'].get('datavalue')]
            labs = ent.get('labels', {})
            label = next((labs[k]['value'] for k in ('en', 'mul', 'nl', 'de') if k in labs), None)
            out[q] = {'P31': get('P31'), 'P301': get('P301'), 'label': label}
    return out


def tree(root, max_depth):
    """BFS the category tree with a visited set AND a depth cap.

    Both are load-bearing: event categories contain members that point sideways or upward
    (a parent category, a themed collection), and without a visited set the same subtree is
    re-walked until the API 429s you. A live run on one 88-member category recursed into an
    unrelated archive's parchment collection before this was added.
    """
    files, seen, queue, skipped = [], set(), [(root, 0)], []
    while queue:
        cat, depth = queue.pop(0)
        if cat in seen:
            continue
        seen.add(cat)
        r = api({'action': 'query', 'list': 'categorymembers', 'cmtitle': cat,
                 'cmlimit': '500', 'maxlag': '5'})
        for m in r.get('query', {}).get('categorymembers', []):
            if m['ns'] == 6:
                files.append(m['title'])
            elif m['ns'] == 14:
                if depth + 1 > max_depth:
                    skipped.append(m['title'])
                else:
                    queue.append((m['title'], depth + 1))
    if skipped:
        print("depth cap %d skipped %d subcategories, e.g. %s"
              % (max_depth, len(skipped), ", ".join(skipped[:3])), file=sys.stderr)
    return list(dict.fromkeys(files)), len(seen)


def resolve(cat, M, catitem):
    qi = catitem.get(cat)
    if qi:
        m = M.get(qi, {})
        for t in m.get('P301', []):
            if 'Q5' in M.get(t, {}).get('P31', []):
                return t
        if 'Q5' in m.get('P31', []):
            return qi
    for pat in QUALIFIERS:
        hit = re.match(pat, cat[9:], re.I)
        if not hit:
            continue
        base = 'Category:' + hit.group(1)
        qi = pageitems([base]).get(base)
        if not qi:
            continue
        M.update(claims([qi]))
        for t in M[qi].get('P301', []) + [qi]:
            M.update(claims([t]))
            if 'Q5' in M.get(t, {}).get('P31', []):
                return t
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Person ground truth for a Commons category tree.")
    ap.add_argument('category', help='e.g. "Category:Erasmus Prize 2015"')
    ap.add_argument('--out', default='file_persons.json')
    ap.add_argument('--max-depth', type=int, default=3,
                    help='subcategory depth to walk (default 3)')
    args = ap.parse_args(argv)
    if not args.category.startswith('Category:'):
        print('error: pass a full category title, e.g. "Category:Some event 2015"',
              file=sys.stderr)
        return 2
    root = args.category

    files, ncats = tree(root, args.max_depth)
    if not files:
        print('error: no files under %s (wrong title? empty category tree?)' % root,
              file=sys.stderr)
        return 2

    filecats = {}
    for batch in batches(files):
        r = api({'action': 'query', 'prop': 'categories', 'titles': '|'.join(batch),
                 'cllimit': 'max', 'clshow': '!hidden'})
        if 'query' not in r:
            raise RuntimeError('API refused a titles batch: %s' % json.dumps(r)[:300])
        for p in r['query']['pages'].values():
            filecats[p['title']] = [c['title'] for c in p.get('categories', [])]
    cats = sorted({c for v in filecats.values() for c in v if not BLACK.search(c[9:])})
    catitem = pageitems(cats)
    M = claims(catitem.values())

    person_cat, unmapped = {}, []
    for c in cats:
        q = resolve(c, M, catitem)
        if q:
            M.update(claims([q]))
            person_cat[c] = {'qid': q, 'label': M.get(q, {}).get('label') or c[9:]}
        else:
            unmapped.append(c[9:])

    file_persons = {}
    for f, cs in filecats.items():
        for c in cs:
            if c in person_cat:
                pc = person_cat[c]
                file_persons.setdefault(f, {})[pc['qid']] = pc['label']

    people = {q for v in file_persons.values() for q in v}
    out = {'category': root, 'file_persons': file_persons, 'person_cat': person_cat,
           'unmapped': unmapped, 'files': len(files), 'categories_walked': ncats}
    json.dump(out, open(args.out, 'w'), indent=1, ensure_ascii=False)

    print("files %d | labelled %d | people %d | pairs %d"
          % (len(files), len(file_persons), len(people),
             sum(len(v) for v in file_persons.values())))
    print("unmapped categories (%d) — eyeball these:" % len(unmapped))
    for c in unmapped:
        print("  ", c)
    return 0


if __name__ == '__main__':
    sys.exit(main())
