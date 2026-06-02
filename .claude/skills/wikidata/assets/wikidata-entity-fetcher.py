#!/usr/bin/env python3
"""
Wikidata Entity Fetcher

Fetches and displays Wikidata item data — labels, descriptions,
claims (with qualifiers), sitelinks, and more — using the Action
API and/or SPARQL.

Usage:
    python3 wikidata-entity-fetcher.py Q937
    python3 wikidata-entity-fetcher.py Q937 --verbose
    python3 wikidata-entity-fetcher.py --search Einstein
    python3 wikidata-entity-fetcher.py P31
    python3 wikidata-entity-fetcher.py --sparql "SELECT ?item ?itemLabel WHERE { wd:Q937 wdt:P106 ?item. SERVICE wikibase:label { bd:serviceParam wikibase:language 'en'. } }"
"""

import json
import sys
import requests
import argparse

USER_AGENT = "WikidataEntityFetcher/1.0 (https://www.wikidata.org; demo@example.com) WikiSkills"
API_URL = "https://www.wikidata.org/w/api.php"
SPARQL_URL = "https://query.wikidata.org/sparql"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


def fetch_entity(entity_id, props="labels|descriptions|aliases|claims|sitelinks", langs="en"):
    """Fetch entity data from the Wikibase Action API."""
    params = {
        "action": "wbgetentities",
        "ids": entity_id,
        "props": props,
        "languages": langs,
        "format": "json",
    }
    resp = SESSION.get(API_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    entities = data.get("entities", {})
    if not entities:
        print(f"Entity '{entity_id}' not found.")
        return None
    eid, entity = next(iter(entities.items()))
    return entity


def fetch_property_label(prop_id):
    """Fetch the label for a property (for display)."""
    entity = fetch_entity(prop_id, props="labels", langs="en")
    if entity:
        labels = entity.get("labels", {})
        label_data = labels.get("en", {})
        return label_data.get("value", prop_id)
    return prop_id


def run_sparql(query):
    """Run a SPARQL query and return results."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json"}
    resp = SESSION.get(SPARQL_URL, params={"format": "json", "query": query}, headers=headers)
    resp.raise_for_status()
    return resp.json()


def search_entities(query, limit=10):
    """Search for entities by label."""
    params = {
        "action": "wbsearchentities",
        "search": query,
        "language": "en",
        "limit": limit,
        "format": "json",
    }
    resp = SESSION.get(API_URL, params=params)
    resp.raise_for_status()
    return resp.json().get("search", [])


def display_entity(entity, verbose=False):
    """Pretty-print entity data."""
    labels = entity.get("labels", {})
    descriptions = entity.get("descriptions", {})
    aliases = entity.get("aliases", {})
    claims = entity.get("claims", {})
    sitelinks = entity.get("sitelinks", {})

    en_label = labels.get("en", {}).get("value", "(no English label)")
    en_desc = descriptions.get("en", {}).get("value", "")

    print(f"\n{'='*60}")
    print(f"  {en_label}")
    if en_desc:
        print(f"  {en_desc}")
    print(f"{'='*60}")

    # Aliases
    alias_list = aliases.get("en", [])
    if alias_list:
        alias_str = ", ".join(a.get("value", "") for a in alias_list)
        print(f"\n  Aliases: {alias_str}")

    # Claims
    if claims:
        print(f"\n  📋 Statements ({len(claims)} properties)")
        for prop_id, claim_list in sorted(claims.items()):
            prop_label = fetch_property_label(prop_id)
            vals = []
            for claim in claim_list[:3]:  # show up to 3 values per property
                mainsnak = claim.get("mainsnak", {})
                dv = mainsnak.get("datavalue", {})
                val = dv.get("value", {})
                datatype = mainsnak.get("datatype", "")
                formatted = format_value(val, datatype)
                vals.append(formatted)

                # Qualifiers (in verbose mode)
                if verbose:
                    qualifiers = claim.get("qualifiers", {})
                    if qualifiers:
                        q_parts = []
                        for qprop, qlist in qualifiers.items():
                            qlabel = fetch_property_label(qprop)
                            for q in qlist[:2]:
                                qdv = q.get("datavalue", {})
                                qval = qdv.get("value", {})
                                qdt = q.get("datatype", "")
                                qparts.append(f"{qlabel}: {format_value(qval, qdt)}")
                        if q_parts:
                            vals[-1] += f" [{', '.join(q_parts)}]"

            val_str = "; ".join(vals)
            if len(claim_list) > 3:
                val_str += f" ... (+{len(claim_list) - 3} more)"
            print(f"     {prop_label} ({prop_id}): {val_str}")

    # Sitelinks
    if sitelinks:
        print(f"\n  🌐 Wikipedia links: {len(sitelinks)} languages")
        sites = list(sitelinks.items())
        for site, link_data in sites[:8]:
            print(f"     {site}: {link_data.get('title', '?')}")
        if len(sites) > 8:
            print(f"     ... and {len(sites) - 8} more")
    print()


def format_value(val, datatype):
    """Format a data value based on its type."""
    if datatype == "wikibase-item":
        return val.get("id", "?")
    elif datatype == "time":
        return val.get("time", "?").replace("T00:00:00Z", "")
    elif datatype == "string":
        return val
    elif datatype == "commonsMedia":
        return f"File:{val}"
    elif datatype == "globe-coordinate":
        return f"({val.get('latitude', '?')}, {val.get('longitude', '?')})"
    elif datatype == "quantity":
        amount = val.get("amount", "?")
        unit = val.get("unit", "").split("/")[-1] if val.get("unit") else ""
        return f"{amount} {unit}".strip()
    elif datatype == "url":
        return val
    elif datatype == "external-id":
        return val
    else:
        return str(val)


def display_sparql_results(data):
    """Pretty-print SPARQL JSON results."""
    head = data.get("head", {}).get("vars", [])
    results = data.get("results", {}).get("bindings", [])
    if not results:
        print("No results.")
        return

    print(f"\n  Results: {len(results)}")
    print(f"  Columns: {' | '.join(head)}")
    print(f"  {'─' * 50}")
    for row in results[:15]:
        parts = []
        for var in head:
            val = row.get(var, {})
            label = val.get("value", "")
            parts.append(label)
        print(f"  {' | '.join(parts)}")
    if len(results) > 15:
        print(f"  ... and {len(results) - 15} more")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch and display Wikidata entity data"
    )
    parser.add_argument("query", nargs="?", help="Q/P ID (e.g., Q937) or search term (with --search)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show qualifiers and details")
    parser.add_argument("--search", "-s", action="store_true", help="Search by label instead of Q ID")
    parser.add_argument("--sparql", "-S", metavar="QUERY", help="Run a SPARQL query")
    args = parser.parse_args()

    if args.sparql:
        print(f"🔍 Running SPARQL query...")
        data = run_sparql(args.sparql)
        display_sparql_results(data)
        return

    if not args.query:
        parser.print_help()
        return

    if args.search:
        print(f"🔍 Searching for '{args.query}'...")
        results = search_entities(args.query)
        if not results:
            print("No results found.")
            return
        print(f"Found {len(results)} result(s):\n")
        for r in results:
            eid = r.get("id", "?")
            label = r.get("label", "(no label)")
            desc = r.get("description", "")
            desc_str = f" — {desc}" if desc else ""
            print(f"  {eid}: {label}{desc_str}")
        print()
    else:
        # Treat query as a Q/P ID
        qid = args.query.strip().upper()
        if not (qid.startswith("Q") or qid.startswith("P")):
            print("Error: Expected a Q or P number (e.g., Q937) or use --search for label search.")
            sys.exit(1)

        entity = fetch_entity(qid)
        if entity:
            display_entity(entity, verbose=args.verbose)


if __name__ == "__main__":
    main()
