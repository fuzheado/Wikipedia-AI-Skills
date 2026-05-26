---
name: wikipedia-edit-history
description: Read and analyze Wikipedia's page revision history — diffs, edit summaries, user contributions, byte changes, rollback, and understanding the evolution of a page over time
license: MIT
compatibility: opencode
---

## SOP: Accessing Page History

Every Wikipedia page has a complete edit history. Access it via:

**URL:** `https://en.wikipedia.org/w/index.php?title=PageName&action=history`

**API:**
```
action=query&prop=revisions&titles=Albert_Einstein&rvlimit=50&format=json
```

**Key parameters:**

| Parameter | Purpose |
|-----------|---------|
| `rvlimit` | Max revisions (1–500, default 10) |
| `rvprop` | What data per revision (see §2) |
| `rvdir` | `older` (newest first) or `newer` (oldest first) |
| `rvstart` / `rvend` | Timestamp-based date range |
| `rvuser` | Filter to a specific user |

**Pagination:** API responses include a `continue` object. Merge it into the next request to fetch the next page of results.

**Date range example:**
```
action=query&prop=revisions&titles=Albert_Einstein&rvstart=2026-01-01T00:00:00Z&rvend=2025-06-01T00:00:00Z&rvdir=newer&rvlimit=500
```

**`prop=revisions` vs. `list=recentchanges`:** Use `prop=revisions` for history of a single page. Use `list=recentchanges` to see what's happening wiki-wide.

---

## SOP: Reading Revision Records

Each revision, when requested with `rvprop=ids|timestamp|user|userid|size|comment|tags|flags`, returns:

```json
{
  "revid": 123456789,
  "parentid": 123456788,
  "timestamp": "2026-05-23T14:30:00Z",
  "user": "Example",
  "userid": 12345,
  "size": 24500,
  "comment": "/* Early life */ added citation",
  "tags": ["mobile edit"],
  "minor": true
}
```

| Field | Description |
|-------|-------------|
| `revid` | Unique revision ID (sequential, per wiki) |
| `parentid` | Previous revision (0 for page creation) |
| `timestamp` | ISO 8601 timestamp |
| `user` | Username or IP address (empty if oversighted) |
| `userid` | User ID (0 for anonymous editors) |
| `size` | Page length in bytes after this revision |
| `comment` | Edit summary |
| `tags` | Machine-applied labels |
| `minor` | True if marked as minor edit |

**`rvprop` cost:** `ids`, `flags`, `timestamp`, `user`, `size`, `sha1`, `comment`, `tags` are low cost. `content` (full wikitext) is high cost — use sparingly.

Link to a specific revision: `https://en.wikipedia.org/w/index.php?title=PageName&oldid=123456789`

---

## SOP: Interpreting Diffs (Overview)

For detailed diff fetching and interpretation, see the **[wikimedia-diffs](../wikimedia-diffs/SKILL.md)** skill. This section covers the basics needed for history navigation.

**Diff URL:** `https://en.wikipedia.org/w/index.php?title=PageName&diff=NEW_REV_ID&oldid=OLD_REV_ID`

**Visual reading:**
- **Red/pink** background: deleted content (in oldid, removed in newid)
- **Green/light green** background: added content (new in newid)
- White: unchanged context lines

**Key metrics from `action=compare`:**
- `diffsize` — total bytes changed (additions + removals churn)
- `fromsize` / `tosize` — page sizes before and after
- Net change: `tosize - fromsize`

**Detecting reverts:** A revert shows a large block of content removed and identical content restored. Edit summary often contains "rv", "Reverted", "Undid", or "restore". The user reverting is typically different from the user being reverted.

> 💡 For programmatic diff fetching, HTML comparison, statistics, and BeautifulSoup parsing, load **`wikimedia-diffs`**.

---

## SOP: Reading Edit Summaries

Edit summaries (the `comment` field) explain why a change was made.

**Common patterns:**

| Summary | Meaning |
|---------|---------|
| `copyedit` | Minor grammar, spelling, formatting |
| `fix typo` | Spelling correction |
| `add ref` | Added a citation |
| `/* Section name */ added citation` | Section-specific edit |
| `rv vandalism` | Reverted vandalism |
| `Reverted [[WP:AGF|good faith]] edits` | Reverted well-intentioned but incorrect edit |

**Automatic summaries:** Rollback and undo generate automatic summaries. Bot accounts often have identifiers like "BOT" or "Bot" in their summaries or usernames.

**Missing summaries:** Edits with an empty `comment` field provide no context — you'll need to inspect the diff to understand the change.

---

## SOP: Distinguishing Minor and Major Edits

The `minor` flag indicates the editor considered the change trivial:

**What IS minor:** Spelling, grammar, formatting, fixing wikilinks, simple copyediting that doesn't change meaning.

**What is NOT minor** (per WP:MINOR): Adding/removing content or citations, changing meaning, any change that could be disputed.

The `bot` flag indicates an automated bot account. API filtering:

```
# Filter to minor edits
action=query&prop=revisions&titles=Page&rvminor=1&format=json
```

> 💡 For edit magnitude (byte churn, lines added/removed), see **[wikimedia-diffs](../wikimedia-diffs/SKILL.md)**.

---

## SOP: Identifying Editors and Their Contributions

Each revision records who made it:
- **Registered user:** `user` = username, `userid` = positive integer
- **Anonymous editor:** `user` = IP address, `userid` = 0
- **Oversighted:** `user` = empty string

**User contributions URL:** `https://en.wikipedia.org/wiki/Special:Contributions/Username`

**Contributions API:**
```
action=query&list=usercontribs&ucuser=Username&uclimit=50&format=json
```

**Bot detection:** Check user groups via:
```
action=query&list=users&ususers=Username&usprop=groups&format=json
```
If `groups` contains `"bot"`, the account is a bot.

**User groups and edit permissions:** Autoconfirmed (4 days, 500 edits) → extended confirmed (30 days, 500 edits) → administrator (full delete/block/protect rights). Bot accounts' edits are hidden from recent changes by default.

---

## SOP: Analyzing Byte Size Changes

Each revision stores the page's byte length (`size`). Calculate the delta:

```python
delta = current_revision["size"] - parent_revision["size"]
```

**Typical sizes:**

| Delta | Classification | Typical Edit |
|-------|---------------|-------------|
| 1–200 B | Small | Copyedit, fix typo, add wikilink |
| 200–2,000 B | Medium | Add a paragraph, add citation |
| 2,000–20,000 B | Large | Add a section, rewrite |
| 20,000+ B | Very large | Major rewrite, new article |

**Red flags:**
- Size drops to <100 bytes → page blanking (possible vandalism)
- Size jumps 50,000+ bytes from a new user → possible copyright violation
- Size oscillates rapidly → edit warring or revert cycle

> 💡 For precise byte churn (total added + removed), use `action=compare` diff data in **[wikimedia-diffs](../wikimedia-diffs/SKILL.md)**.

---

## SOP: Reverting Edits (Undo vs. Rollback)

**Undo** (`action=edit&undoafter=REVID&undo=REVID`) — reverts a single edit while preserving non-conflicting later edits. Any user can undo. It's selective — it undoes one revision at a time.

**Rollback** (`action=rollback`) — reverts all consecutive edits by the last editor of a page. Requires the `rollback` permission (autoconfirmed users). It's all-or-nothing — reverts everything the last editor did, in one click.

**Detecting reverts in history:** Look for edit summaries containing "rv", "Reverted", "Undid", or "restore". The byte change is typically similar in magnitude to earlier edits but negative.

**Three-Revert Rule (3RR):** No user may make more than 3 reverts on a single page within 24 hours. On BLPs and certain contentious topics, a 1-revert rule (1RR) applies. Violations can lead to a block.

---

## SOP: Using Revision Tags and Flags

Tags are machine-applied labels describing the editing context:

| Tag | Meaning |
|-----|---------|
| `mobile edit` | Made from a mobile device |
| `mobile web edit` | Made from mobile web interface |
| `visual editor` | Used VisualEditor |
| `possible vandalism` | Flagged by abuse filter |
| `mw-reverted` | This revision was later reverted |
| `self-revert` | Editor reverted their own edit |

**Fetch tags on revisions:**
```
action=query&prop=revisions&titles=Page&rvprop=ids|tags&format=json
```

**List all available tags on a wiki:**
```
action=query&list=tags&format=json
```

**Flag meanings:** `new` (page creation), `minor` (minor edit), `bot` (bot account).

---

## SOP: Detecting Vandalism and Problematic Edits

**Common vandalism signals:**

| Signal | What to Check |
|--------|---------------|
| Large byte increase from new/unregistered user | Possible copyright violation |
| Page blanking (size < 100 bytes) | Likely malicious |
| Offensive edit summaries | Profanity or nonsense |
| `possible vandalism` tag | Flagged by abuse filters |
| Quick reverts by multiple editors | Content likely vandalism |
| Repeating characters / gibberish in diff | Nonsense text added |

**Detecting edit warring:** Look for the same content being added and removed repeatedly by the same pair of editors. Check for `mw-reverted` tags. More than 3 reverts by one user in 24 hours may violate 3RR.

**Checking user block status:**
```
action=query&list=users&ususers=Username&usprop=blockinfo|groups&format=json
```
Returns `blockid`, `blockedby`, `blockreason`, `blockexpiry` if the user is currently blocked.

**When to act:**

| Severity | Action |
|----------|--------|
| Clear vandalism | Revert. Notify at WP:AIV if repeated. |
| Suspicious but unclear | Check contributions. Leave talk page note. |
| Content dispute | Do NOT treat as vandalism. Discuss on talk page. |
| Edit warring | Do NOT revert. Report at WP:AN3. |

---

## SOP: Accessing History Data via API

| Task | API Method |
|------|-----------|
| Get latest revision ID | `prop=info&inprop=revisions` |
| Get revision list | `prop=revisions` with `rvprop=ids|timestamp|user|size|comment` |
| Compare two revisions | `action=compare` (see `wikimedia-diffs`) |
| Get a specific revision's content | `action=query&revids=REVID&prop=revisions&rvprop=content` |
| Get user contributions | `list=usercontribs` with `ucprop=ids|title|timestamp|comment|size|sizediff` |
| Undo an edit | `action=edit&undoafter=REVID&undo=REVID&token=TOKEN` |
| Rollback | `action=rollback&title=Page&from=User&token=TOKEN` |
| Check user block status | `list=users&usprop=blockinfo|groups` |

---

## Relationship to Other Skills

- **wikimedia-diffs** — The companion skill for deep diff fetching, parsing, and statistics. This skill provides the broader history context (user contributions, rollback, vandalism detection); `wikimedia-diffs` handles the precise diff mechanics.
- **wikipedia-page-anatomy** — The article page is what gets edited; history tracks its evolution over time.
- **wikipedia-talk-page** — Talk pages have their own history; same revision concepts apply.
- **wikimedia-api-access** — History operations use the same Action API; defer to this skill for User-Agent and rate limiting.

---

## Tooling (to be built)

- `scripts/recent-edits.sh` — Show recent edits to a page with diff size, user, and summary
- `scripts/compare-revisions.sh` — Compare two revisions and show a summary of changes (byte delta, user, key changes)
- `scripts/user-contribs.sh` — Fetch recent contributions for a user with page titles and edit summaries
- `references/diff-patterns.md` — Common diff patterns and what they mean (content addition, blanking, revert, copyedit)
- `assets/history-audit.py` — Python tool that fetches page history, computes per-revision diffs, and flags suspicious edits
