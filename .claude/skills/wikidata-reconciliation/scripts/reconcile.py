#!/usr/bin/env python3
"""
reconcile.py — resolve unstructured labels to verified Wikidata QIDs.

Primary path: action=wbsearchentities (reliable; the reconciliation service's
batch POST endpoint is currently broken — see SKILL.md).

Usage:
    python3 reconcile.py "Eiffel Tower"
    python3 reconcile.py --file labels.txt --lang en
    python3 reconcile.py --verify "Eiffel Tower"          # also check P31/label via wbgetentities
    python3 reconcile.py --verify --file labels.csv       # verify a CSV of labels

Output: JSON lines to stdout (label, qid, desc, confidence), summary to stderr.

Stdlib only (urllib). Requires a descriptive User-Agent (WMF policy).
"""
import argparse
import json
import sys
import time
import urllib.parse
import urllib.request

UA = ("HermesAgent/1.0 (https://en.wikipedia.org/wiki/User:WikiButler-bot) "
      "WikidataReconciliation/1.0")
API = "https://www.wikidata.org/w/api.php"
DELAY = 0.5  # seconds between API calls (floor; 1.0 recommended for big batches)


def api(params, delay=DELAY):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    time.sleep(delay)
    return data


def resolve(label, lang="en", limit=3):
    """Return the best candidate for a label: {label, qid, desc, confidence}."""
    label = label.strip()
    if not label:
        return {"label": label, "qid": None, "desc": "", "confidence": "none"}
    d = api({"action": "wbsearchentities", "format": "json", "formatversion": "2",
             "search": label, "language": lang, "limit": limit})
    for hit in d.get("search", []):
        desc = hit.get("description", "")
        if hit.get("match", {}).get("type") == "label":
            return {"label": label, "qid": hit["id"], "desc": desc,
                    "confidence": "high"}
        if desc:  # first described candidate: medium confidence
            return {"label": label, "qid": hit["id"], "desc": desc,
                    "confidence": "medium"}
    return {"label": label, "qid": None, "desc": "", "confidence": "none"}


def verify(qid, expected_label=None, lang="en"):
    """Check a QID exists, has a label, and report its P31 types."""
    d = api({"action": "wbgetentities", "format": "json", "formatversion": "2",
             "ids": qid, "props": "labels|descriptions|claims", "languages": lang})
    ent = d.get("entities", {}).get(qid)
    if ent is None:
        return {"qid": qid, "exists": False, "label": None, "p31": [],
                "label_matches": False}
    label = ent.get("labels", {}).get(lang, {}).get("value")
    p31 = [c["mainsnak"]["datavalue"]["value"]["id"]
           for c in ent.get("claims", {}).get("P31", [])
           if c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")]
    label_matches = bool(expected_label) and bool(label) and \
        expected_label.strip().lower() == label.lower()
    return {"qid": qid, "exists": True, "label": label, "p31": p31,
            "label_matches": label_matches}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("labels", nargs="*", help="label(s) to resolve")
    ap.add_argument("--file", help="file with one label per line")
    ap.add_argument("--lang", default="en", help="label language (default: en)")
    ap.add_argument("--verify", action="store_true",
                    help="also verify each resolved QID via wbgetentities")
    args = ap.parse_args()

    labels = list(args.labels)
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            labels.extend(line.strip() for line in f if line.strip())
    if not labels:
        ap.error("provide labels as arguments or via --file")

    results = []
    for label in labels:
        r = resolve(label, args.lang)
        if r["qid"] and args.verify:
            v = verify(r["qid"], expected_label=label, lang=args.lang)
            r["verified"] = v
        results.append(r)
        print(json.dumps(r, ensure_ascii=False))
        sys.stdout.flush()

    n_high = sum(1 for r in results if r["confidence"] == "high")
    n_med = sum(1 for r in results if r["confidence"] == "medium")
    n_none = sum(1 for r in results if r["confidence"] == "none")
    sys.stderr.write(
        f"[reconcile] {len(results)} labels: {n_high} high, {n_med} medium, "
        f"{n_none} unresolved\n")


if __name__ == "__main__":
    main()
