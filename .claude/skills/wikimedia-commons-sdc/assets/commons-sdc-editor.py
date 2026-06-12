#!/usr/bin/env python3
"""
Commons SDC Editor — Add, edit, and inspect Structured Data on Commons via the Wikibase API.

Commands:
  caption M12345 en "A caption text"     Set a file caption
  claim M12345 P180 Q42                  Add a Wikidata-item statement
  date M12345 P571 2023-01-15            Add a date statement
  coord M12345 P1259 48.8566 2.3522      Add coordinate statement
  copy M12345 M67890                     Copy all claims between files
  inspect M12345                         Show all SDC for a file
  batch-csv path/to/file.csv             Batch from CSV
  batch-category "Category Name" P180 Q42  Add statement to all files in category

Requires WCQS_AUTH_TOKEN env var with a bot password (User@botname:password)
or use --botpass user@botname:password

Usage:
  python3 commons-sdc-editor.py caption M12345 en "Sugar cubes"
  python3 commons-sdc-editor.py claim M12345 P180 Q42
  python3 commons-sdc-editor.py inspect M12345
  python3 commons-sdc-editor.py batch-category "Bridges in Paris" P180 Q12280
"""

import argparse
import csv
import json
import os
import sys
import time

import requests


UA = "CommonsSDCEditor/1.0 (https://example.com; user@example.com)"


def get_session(botpass: str | None = None) -> tuple[requests.Session, str]:
    """Authenticate and return (session, csrf_token)."""
    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    if botpass:
        username, password = botpass.split(":", 1)
        session.auth = (username, password)
    elif "WCQS_AUTH_TOKEN" in os.environ:
        # Supports bot password as env var
        token = os.environ["WCQS_AUTH_TOKEN"]
        if ":" in token:
            username, password = token.split(":", 1)
            session.auth = (username, password)
        else:
            print("Error: WCQS_AUTH_TOKEN should be in user@botname:password format", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: Set WCQS_AUTH_TOKEN or use --botpass", file=sys.stderr)
        sys.exit(1)

    # Get CSRF token
    resp = session.get(
        "https://commons.wikimedia.org/w/api.php",
        params={"action": "query", "meta": "tokens", "type": "csrf", "format": "json"},
    )
    csrf_token = resp.json()["query"]["tokens"]["csrftoken"]
    return session, csrf_token


def cmd_caption(session, csrf, args):
    """Set a file caption."""
    m_id, lang, text = args.m_id, args.lang, args.text
    resp = session.post(
        "https://commons.wikimedia.org/w/api.php",
        data={
            "action": "wbsetlabel",
            "id": m_id,
            "language": lang,
            "value": text,
            "token": csrf,
            "format": "json",
        },
    )
    data = resp.json()
    if "error" in data:
        print(f"Error: {data['error']['code']} — {data['error']['info']}")
    else:
        print(f"✓ Caption set for {m_id} [{lang}]")


def cmd_claim(session, csrf, args):
    """Add a Wikidata-item statement."""
    m_id, prop, qid = args.m_id, args.prop, args.qid
    resp = session.post(
        "https://commons.wikimedia.org/w/api.php",
        data={
            "action": "wbcreateclaim",
            "entity": m_id,
            "property": prop,
            "value": json.dumps({"id": qid}),
            "token": csrf,
            "format": "json",
        },
    )
    data = resp.json()
    if "error" in data:
        print(f"Error: {data['error']['code']} — {data['error']['info']}")
    else:
        cid = data["claim"]["id"]
        print(f"✓ Created claim {cid} ({prop} → {qid})")


def cmd_date(session, csrf, args):
    """Add a date statement."""
    m_id, prop, date_str = args.m_id, args.prop, args.date
    # Parse date — accept YYYY-MM-DD or YYYY-MM or YYYY
    parts = date_str.split("-")
    if len(parts) == 3:
        precision = 11  # day
    elif len(parts) == 2:
        precision = 10  # month
    else:
        precision = 9   # year

    time_value = f"+{date_str}T00:00:00Z"

    resp = session.post(
        "https://commons.wikimedia.org/w/api.php",
        data={
            "action": "wbcreateclaim",
            "entity": m_id,
            "property": prop,
            "value": json.dumps({
                "time": time_value,
                "timezone": 0,
                "before": 0,
                "after": 0,
                "precision": precision,
                "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
            }),
            "token": csrf,
            "format": "json",
        },
    )
    data = resp.json()
    if "error" in data:
        print(f"Error: {data['error']['code']} — {data['error']['info']}")
    else:
        print(f"✓ Claim created")


def cmd_coord(session, csrf, args):
    """Add a coordinate statement."""
    m_id, prop = args.m_id, args.prop
    lat, lon = float(args.lat), float(args.lon)
    resp = session.post(
        "https://commons.wikimedia.org/w/api.php",
        data={
            "action": "wbcreateclaim",
            "entity": m_id,
            "property": prop,
            "value": json.dumps({
                "latitude": lat,
                "longitude": lon,
                "precision": 0.0001,
                "globe": "http://www.wikidata.org/entity/Q2",
            }),
            "token": csrf,
            "format": "json",
        },
    )
    data = resp.json()
    if "error" in data:
        print(f"Error: {data['error']['code']} — {data['error']['info']}")
    else:
        print(f"✓ Coordinates added")


def cmd_inspect(session, csrf, args):
    """Show all SDC for a file."""
    m_id = args.m_id
    resp = session.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "wbgetentities",
            "ids": m_id,
            "props": "labels|claims",
            "format": "json",
        },
    )
    data = resp.json()
    entity = data.get("entities", {}).get(m_id, {})

    print(f"=== {m_id} ===")
    labels = entity.get("labels", {})
    for lang, label in labels.items():
        print(f"  Caption [{lang}]: {label['value']}")

    claims = entity.get("claims", {})
    for prop, claim_list in claims.items():
        for claim in claim_list:
            snak = claim.get("mainsnak", {})
            rank = claim.get("rank", "normal")
            if snak.get("snaktype") == "value":
                dv = snak.get("datavalue", {})
                val = dv.get("value", {})
                if isinstance(val, dict) and "id" in val:
                    print(f"  {prop} → {val['id']} (rank: {rank})")
                elif isinstance(val, dict) and "time" in val:
                    print(f"  {prop} → {val['time']} (rank: {rank})")
                elif isinstance(val, dict) and "latitude" in val:
                    print(f"  {prop} → {val['latitude']},{val['longitude']} (rank: {rank})")
                else:
                    print(f"  {prop} → {val} (rank: {rank})")
            else:
                print(f"  {prop} → {snak.get('snaktype', '?')} (rank: {rank})")

            # Show qualifiers
            for qprop, quals in claim.get("qualifiers", {}).items():
                for q in quals:
                    qv = q.get("datavalue", {}).get("value", {})
                    if isinstance(qv, dict) and "id" in qv:
                        print(f"    qualifier {qprop} → {qv['id']}")
                    else:
                        print(f"    qualifier {qprop} → {qv}")


def cmd_copy(session, csrf, args):
    """Copy all claims from source to target."""
    src, tgt = args.src, args.tgt
    resp = session.get(
        "https://commons.wikimedia.org/w/api.php",
        params={"action": "wbgetclaims", "entity": src, "format": "json"},
    )
    claims = resp.json().get("claims", {})
    copied = 0
    for prop, claim_list in claims.items():
        for claim in claim_list:
            snak = claim.get("mainsnak", {})
            if snak.get("snaktype") == "value" and "datavalue" in snak:
                r = session.post(
                    "https://commons.wikimedia.org/w/api.php",
                    data={
                        "action": "wbcreateclaim",
                        "entity": tgt,
                        "property": prop,
                        "value": json.dumps(snak["datavalue"]["value"]),
                        "token": csrf,
                        "format": "json",
                    },
                )
                if "error" not in r.json():
                    copied += 1
                time.sleep(0.3)
    print(f"Copied {copied} claims from {src} to {tgt}")


def cmd_batch_csv(session, csrf, args):
    """Batch from CSV file."""
    with open(args.csv_path) as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            m_id = row.get("m_id", "")
            if not m_id:
                # Try to resolve from filename
                filename = row.get("filename", "")
                if filename:
                    resp = session.get(
                        "https://commons.wikimedia.org/w/api.php",
                        params={
                            "action": "query",
                            "prop": "info",
                            "titles": f"File:{filename}",
                            "format": "json",
                        },
                    )
                    for pid in resp.json()["query"]["pages"]:
                        m_id = f"M{pid}"

            if not m_id:
                print(f"Row {i}: no m_id or filename, skipping")
                continue

            # Add captions
            for key, val in row.items():
                if key.startswith("caption_") and val.strip():
                    lang = key.replace("caption_", "")
                    r = session.post(
                        "https://commons.wikimedia.org/w/api.php",
                        data={
                            "action": "wbsetlabel",
                            "id": m_id,
                            "language": lang,
                            "value": val.strip(),
                            "token": csrf,
                            "format": "json",
                        },
                    )
                    if "error" in r.json():
                        print(f"Row {i}: caption error: {r.json()['error']['info']}")

            # Add claims (columns named P180, P170, etc.)
            for key, val in row.items():
                if key.startswith("P") and val.strip():
                    r = session.post(
                        "https://commons.wikimedia.org/w/api.php",
                        data={
                            "action": "wbcreateclaim",
                            "entity": m_id,
                            "property": key,
                            "value": json.dumps({"id": val.strip()}),
                            "token": csrf,
                            "format": "json",
                        },
                    )
                    if "error" in r.json():
                        print(f"Row {i}: {key} error: {r.json()['error']['info']}")

            print(f"Row {i}: {m_id} done")
            time.sleep(0.5)


def cmd_batch_category(session, csrf, args):
    """Add a statement to all files in a category."""
    category, prop, qid = args.category, args.prop, args.qid
    print(f"Fetching files in Category:{category}...")
    files = []
    cmcontinue = None
    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmtype": "file",
            "cmlimit": "max",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
        resp = session.get("https://commons.wikimedia.org/w/api.php", params=params)
        data = resp.json()
        for m in data["query"]["categorymembers"]:
            files.append({"title": m["title"], "m_id": f"M{m['pageid']}"})
        if "continue" in data and "cmcontinue" in data["continue"]:
            cmcontinue = data["continue"]["cmcontinue"]
        else:
            break

    print(f"Adding {prop} → {qid} to {len(files)} files...")
    success = 0
    for f in files:
        r = session.post(
            "https://commons.wikimedia.org/w/api.php",
            data={
                "action": "wbcreateclaim",
                "entity": f["m_id"],
                "property": prop,
                "value": json.dumps({"id": qid}),
                "token": csrf,
                "format": "json",
            },
        )
        if "error" not in r.json():
            success += 1
        else:
            print(f"  Error on {f['title']}: {r.json()['error'].get('info', '?')}")
        time.sleep(0.5)

    print(f"Done: {success}/{len(files)} succeeded")


def main():
    parser = argparse.ArgumentParser(description="Commons SDC Editor")
    parser.add_argument("--botpass", help="Bot password in user@botname:password format")
    sub = parser.add_subparsers(dest="command", required=True)

    p_caption = sub.add_parser("caption", help="Set a file caption")
    p_caption.add_argument("m_id")
    p_caption.add_argument("lang")
    p_caption.add_argument("text")

    p_claim = sub.add_parser("claim", help="Add a Wikidata-item statement")
    p_claim.add_argument("m_id")
    p_claim.add_argument("prop")
    p_claim.add_argument("qid")

    p_date = sub.add_parser("date", help="Add a date statement")
    p_date.add_argument("m_id")
    p_date.add_argument("prop")
    p_date.add_argument("date")

    p_coord = sub.add_parser("coord", help="Add coordinate statement")
    p_coord.add_argument("m_id")
    p_coord.add_argument("prop")
    p_coord.add_argument("lat")
    p_coord.add_argument("lon")

    p_inspect = sub.add_parser("inspect", help="Show all SDC for a file")
    p_inspect.add_argument("m_id")

    p_copy = sub.add_parser("copy", help="Copy claims between files")
    p_copy.add_argument("src")
    p_copy.add_argument("tgt")

    p_batch_csv = sub.add_parser("batch-csv", help="Batch from CSV")
    p_batch_csv.add_argument("csv_path")

    p_batch_cat = sub.add_parser("batch-category", help="Add statement to all files in category")
    p_batch_cat.add_argument("category")
    p_batch_cat.add_argument("prop")
    p_batch_cat.add_argument("qid")

    args = parser.parse_args()
    session, csrf = get_session(args.botpass)

    commands = {
        "caption": cmd_caption,
        "claim": cmd_claim,
        "date": cmd_date,
        "coord": cmd_coord,
        "inspect": cmd_inspect,
        "copy": cmd_copy,
        "batch-csv": cmd_batch_csv,
        "batch-category": cmd_batch_category,
    }
    commands[args.command](session, csrf, args)


if __name__ == "__main__":
    main()
