---
name: wikipedia-talk-page
description: Navigate and participate in Wikipedia talk pages — discussion conventions, signing, archiving, WikiProject banners, assessment ratings, and page collaboration norms
license: MIT
compatibility: opencode
---

## SOP: Understanding the Talk Namespace

Every Wikipedia page has an associated **talk page** where editors discuss improvements. The naming pattern is: prepend `Talk:` for mainspace, or replace the namespace prefix with `X talk:` for others.

| Subject Page | Talk Page |
|-------------|-----------|
| `Albert Einstein` | `Talk:Albert Einstein` |
| `User:Example` | `User talk:Example` |
| `Wikipedia:Manual of Style` | `Wikipedia talk:Manual of Style` |

- A **red-linked** talk page means no discussion has ever been started. This is normal.
- Talk pages have **separate edit histories, watchlists, and protection levels** from their subject pages.
- Access via the "Talk" tab in the web UI, or directly via URL/API as any other page.

---

## SOP: Reading Threaded Discussions

Discussions are organized into topics, each under a `== Heading ==`:

```wikitext
== Date of birth discrepancy ==

I noticed the article lists two different dates. ~~~~

: The 1950 source says March 14. ~~~~
:: But the 1960 biography says March 13. ~~~~
::: I've added both as citations for discussion. ~~~~
```

**Indentation rules:** Each reply is indented with one more colon than the message it replies to. Use `{{outdent}}` to reset after deep nesting (4+ levels).

**Reading order:** Start at the section heading (the topic), then read chronologically top to bottom. Indentation shows who is replying to whom.

---

## SOP: Signing and Attributing Comments

**Always sign your comments on talk pages** using one of these:

| Wikitext | Renders As | Use |
|----------|-----------|-----|
| `~~~~` | `Username 23 May 2026 14:30 (UTC)` | Standard — use for every comment |
| `~~~` | `Username` | Rare — username only |
| `~~~~~` | `23 May 2026 14:30 (UTC)` | Rare — timestamp only |

**Detecting unsigned comments:** An unsigned comment lacks `~~~~`. Retroactively tag with `{{unsigned|Username}}`.

**Custom signatures:** Users can configure a custom signature in preferences. The display text may differ from the username. When attributing, rely on the **username from the revision history**, not just the display text.

---

## SOP: Reading WikiProject Banners

WikiProject banners are boxes at the **top of talk pages** that tag the article's scope and indicate its quality and importance:

```wikitext
{{WikiProject Biography|class=B|importance=High}}
{{WikiProject Physics|class=B|importance=Top}}
```

**Assessment ratings** (ascending quality):

| Rating | Meaning |
|--------|---------|
| Stub | Very brief — just enough to define the topic |
| Start | Basic coverage, but incomplete |
| C | Substantial content, significant gaps remain |
| B | Mostly complete, some gaps or issues |
| GA | Good Article (passed formal review) |
| FA | Featured Article (comprehensive, passed peer review) |

**Importance ratings:** Top (core topic) → High → Mid → Low → NA

**How to read assessment data:**
- **Manual (single article):** Parse talk page wikitext for `{{WikiProject...|class=...|importance=...}}`
- **Bulk (many articles):** Use the **[wikimedia-page-assessment](../wikimedia-page-assessment/SKILL.md)** skill, which queries the `page_assessments` database table directly

> 💡 For bulk analysis (e.g., "find all FA-class articles in WikiProject Physics"), use the database-backed approach.

---

## SOP: Finding and Using Archives

Talk pages archive old discussions to stay manageable. Archives are subpages of the talk page (e.g., `Talk:Article/Archive 1`).

**Automated archiving** is configured via `{{User:MiszaBot/config}}`:

```wikitext
{{User:MiszaBot/config
| algo = old(30d)            → Archive threads older than 30 days
| archive = Talk:Article/Archive %(counter)d
| counter = 3
| maxarchivesize = 150K
| minthreadsleft = 5
}}
```

**Finding archives via API:**
```
action=query&list=prefixsearch&pssearch=Talk:Albert_Einstein/Archive&format=json
```

**Searching across archives:** Query each archive subpage individually via `action=query&prop=revisions&titles=Talk:Albert_Einstein/Archive_1&rvprop=content`. The main talk page search only covers the active page, not archives.

The `{{Archives}}` template displays an archive box in the talk page header with links to all archives and a search field.

---

## SOP: Participating in Discussions

**Starting a new topic:** Add a `== Subject ==` heading followed by your comment at the **bottom** of the talk page. Use the "Add topic" (+) tab in the UI for a guided form.

**Replying to an existing thread:** Add one more colon than the message you're replying to, then write your comment and sign with `~~~~`.

**Notifying other editors:** Use `{{ping|Username}}` inside your signed comment to trigger a notification. Multiple users: `{{ping|UserA|UserB|UserC}}`. Pings only work when combined with a signature.

**Section editing:** Append `&section=N` to the edit URL, or click the `[edit]` link next to a section heading, to edit a single discussion topic without loading the full page.

---

## SOP: Following Talk Page Etiquette

| Rule | What It Means |
|------|--------------|
| **Assume good faith** (WP:AGF) | Assume other editors are trying to help, even if you disagree |
| **No personal attacks** (WP:NPA) | Comment on content, not on the contributor |
| **Stay on topic** (WP:TALK) | Discuss how to improve the article, not the subject itself |
| **Sign your comments** | Always use `~~~~` |
| **Strike, don't delete** | Use `<s>old text</s>` to retract, rather than removing |

**Striking vs. deleting:**
```
✅ Correct: <s>I think this is wrong.</s> On second thought, you're right. ~~~~
❌ Wrong: (comment removed entirely) — makes threads unreadable.
```

**Closing discussions:**
| Template | Meaning |
|----------|---------|
| `{{resolved}}` | Issue addressed or agreed |
| `{{done}}` | Requested action completed |
| `{{not done}}` | Proposal rejected |
| `{{withdrawn}}` | Proposer withdrawing |

**Article talk vs. user talk:** `Talk:Article` is for discussing the article with anyone interested. `User talk:Username` is for personal messages to a specific editor. Do not discuss article content on a user's talk page.

---

## SOP: Accessing Talk Pages via API

| Task | API Method |
|------|-----------|
| Get talk page wikitext | `action=raw&title=Talk:Title` |
| Get parsed talk page | `action=parse&page=Talk:Title&prop=text` |
| Search talk pages | `list=search` with namespace (`srnamespace=1`) |
| Find archive subpages | `list=prefixsearch&pssearch=Talk:Title/Archive` |
| Check if talk page exists | `prop=info` on the talk page title |

---

## Relationship to Other Skills

- **wikipedia-page-anatomy** — Understanding talk pages complements understanding article anatomy; they share the same underlying MediaWiki structure.
- **wikipedia-edit-history** — Talk pages have their own edit history; the same diff/rollback concepts apply.
- **wikimedia-page-assessment** — For bulk assessment queries, use the database-backed skill instead of parsing talk pages one by one.
- **wikimedia-api-access** — Talk page operations use the same Action API; defer to this skill for User-Agent and rate limiting.

---

## Tooling (to be built)

- `scripts/get-assessment.sh` — Fetch WikiProject assessment class and importance for a given article from its talk page
- `scripts/list-archives.sh` — List all archived discussion subpages for a given talk page
- `references/assessment-ratings.md` — Reference guide for FA/GA/B/C/Start/Stub criteria
- `assets/talk-archive-search.py` — Python tool that searches across a talk page and all its archives
