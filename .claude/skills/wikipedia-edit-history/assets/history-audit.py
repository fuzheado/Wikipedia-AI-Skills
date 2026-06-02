#!/usr/bin/env python3
"""
History Auditor — fetch page revision history, compute per-revision diffs,
and flag suspicious edits.

Flags: page blanking, large content additions from new users, edit warring,
revert patterns, and missing edit summaries.

Uses only Python standard library (urllib).
For detailed diff HTML parsing, see the wikimedia-diffs skill.

Usage:
    python3 history-audit.py "Albert Einstein"
    python3 history-audit.py "Python (programming language)" --limit 100
    python3 history-audit.py "Berlin" --json
"""

import sys
import json
import re
import urllib.request
import urllib.parse
import argparse

USER_AGENT = "HistoryAuditor/1.0 (https://en.wikipedia.org; demo@example.com) WikiSkills"
API = "https://en.wikipedia.org/w/api.php"


def api_request(params):
    """Make an API request and return parsed JSON."""
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_history(title, limit=50):
    """Fetch revision history for a page."""
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvlimit": min(limit, 500),
        "rvprop": "ids|timestamp|user|userid|size|comment|tags|flags",
        "format": "json",
    }
    data = api_request(params)
    pages = data.get("query", {}).get("pages", {})
    for pid, page in pages.items():
        if "missing" in page:
            return None, f"Page '{title}' does not exist"
        return page.get("revisions", []), page.get("title", title)
    return [], title


def check_user_block_status(username):
    """Check if a user is currently blocked."""
    if not username or re.match(r"^\d+\.\d+\.\d+\.\d+$", username):
        return None  # IP addresses checked differently
    params = {
        "action": "query",
        "list": "users",
        "ususers": username,
        "usprop": "blockinfo|groups",
        "format": "json",
    }
    data = api_request(params)
    users = data.get("query", {}).get("users", [])
    if users:
        return users[0]
    return None


def compute_deltas(revs):
    """Compute byte deltas between consecutive revisions and add metadata."""
    enriched = []
    for i, rev in enumerate(revs):
        prev_size = revs[i + 1].get("size", 0) if i + 1 < len(revs) else None
        cur_size = rev.get("size", 0)
        delta = (cur_size - prev_size) if prev_size is not None else None

        enriched.append({
            "revid": rev.get("revid"),
            "parentid": rev.get("parentid", 0),
            "timestamp": rev.get("timestamp", ""),
            "user": rev.get("user", "(unknown)"),
            "userid": rev.get("userid", 0),
            "is_anon": rev.get("userid", 0) == 0,
            "size": cur_size,
            "delta": delta,
            "comment": rev.get("comment", ""),
            "is_minor": rev.get("minor", False),
            "tags": rev.get("tags", []),
        })
    return enriched


def detect_flags(revs_enriched, title):
    """Analyze revision history for suspicious patterns."""
    flags = []

    for i, rev in enumerate(revs_enriched):
        # Flag 1: Page blanking
        if rev["delta"] is not None and rev["delta"] < -10000 and rev["size"] < 500:
            flags.append({
                "type": "page_blanking",
                "severity": "high",
                "revid": rev["revid"],
                "user": rev["user"],
                "timestamp": rev["timestamp"],
                "detail": (f"Page size dropped from "
                           f"{rev['size'] - rev['delta']}B to {rev['size']}B "
                           f"by {rev['user']}"),
            })

        # Flag 2: Large addition by new/anonymous user
        if rev["delta"] is not None and rev["delta"] > 20000 and rev["is_anon"]:
            flags.append({
                "type": "large_addition_anon",
                "severity": "medium",
                "revid": rev["revid"],
                "user": rev["user"],
                "timestamp": rev["timestamp"],
                "detail": (f"+{rev['delta']}B added by anonymous user "
                           f"{rev['user']} — possible copyright violation"),
            })

        # Flag 3: Missing edit summary on large change
        if rev["delta"] is not None and abs(rev["delta"]) > 5000 and not rev["comment"].strip():
            flags.append({
                "type": "missing_summary",
                "severity": "low",
                "revid": rev["revid"],
                "user": rev["user"],
                "timestamp": rev["timestamp"],
                "detail": (f"{'Added' if rev['delta'] > 0 else 'Removed'} "
                           f"{abs(rev['delta'])}B with no edit summary"),
            })

        # Flag 4: Revert pattern
        if rev["comment"] and re.search(r"\brv\b|revert|undid|Reverted", rev["comment"], re.I):
            flags.append({
                "type": "revert",
                "severity": "info",
                "revid": rev["revid"],
                "user": rev["user"],
                "timestamp": rev["timestamp"],
                "detail": f"Revert by {rev['user']}: \"{rev['comment'][:80]}\"",
            })

    # Flag 5: Edit warring (3+ reverts by same user in this batch)
    revert_counts = {}
    for f in flags:
        if f["type"] == "revert":
            revert_counts[f["user"]] = revert_counts.get(f["user"], 0) + 1

    for user, count in revert_counts.items():
        if count >= 3:
            flags.append({
                "type": "potential_edit_war",
                "severity": "high",
                "revid": None,
                "user": user,
                "timestamp": None,
                "detail": (f"{user} made {count} reverts in the recent "
                           f"history — possible 3RR violation"),
            })

    return flags


def main():
    parser = argparse.ArgumentParser(
        description="Audit Wikipedia page history for suspicious edits")
    parser.add_argument("title", help="Article title to audit")
    parser.add_argument("--limit", type=int, default=50,
                        help="Number of revisions to check (default: 50)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    revs, resolved_title = fetch_history(args.title, args.limit)
    if revs is None:
        print(f"Error: {resolved_title}")
        sys.exit(1)

    enriched = compute_deltas(revs)
    flags = detect_flags(enriched, resolved_title)

    if args.json:
        print(json.dumps({
            "title": resolved_title,
            "revisions_checked": len(enriched),
            "flag_count": len(flags),
            "flags": flags,
            "revisions": enriched,
        }, indent=2))
    else:
        print(f"=== History Audit: {resolved_title} ===")
        print(f"Revisions checked: {len(enriched)}")
        print()

        if not flags:
            print("No suspicious patterns detected.")
        else:
            # Sort by severity
            severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
            flags.sort(key=lambda f: severity_order.get(f["severity"], 99))

            print(f"Flags ({len(flags)}):")
            for f in flags:
                severity_tag = {
                    "high": "🔴 HIGH",
                    "medium": "🟡 MEDIUM",
                    "low": "🟢 LOW",
                    "info": "ℹ️ INFO",
                }.get(f["severity"], f["severity"])

                print(f"\n  [{severity_tag}] {f['type']}")
                print(f"  {f['detail']}")

        print()
        print("Recent edits (last 5):")
        for rev in enriched[:5]:
            ts = rev["timestamp"].replace("T", " ")[:19] if rev["timestamp"] else "?"
            delta = rev["delta"]
            delta_str = f"+{delta}B" if delta and delta > 0 else (f"{delta}B" if delta else "0B")
            user = rev["user"]
            comment = rev["comment"][:60] if rev["comment"] else "(no summary)"
            print(f"  r{rev['revid']} [{ts}] {delta_str} by {user}: {comment}")


if __name__ == "__main__":
    main()
