---
name: wikipedia-talk-page
description: Navigate, participate in, and understand Wikipedia talk pages — includes modern DiscussionTools (Reply Tool, Topic Subscriptions, Permalinks), Usability Improvements, community gadgets, wikitext conventions, WikiProject banners, archives, and talk page etiquette
license: MIT
compatibility: opencode
depends_on: [wikimedia-api-access]
skill_discovery_hints:
  - keywords: ["talk page", "DiscussionTools", "Reply Tool", "topic subscription", "WikiProject banner"]
  - keywords: ["talk page archive", "discussion", "indentation", "ping", "@-mention"]
last_verified: 2026-06-12
---

> ⚠️ **User-Agent required:** The API examples below use the Action API. All requests must include a descriptive `User-Agent` header or they will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format.

> 💡 **This skill covers both legacy wikitext conventions and modern tools.** Most talk pages now have DiscussionTools enabled (Reply buttons, auto-signing, topic subscriptions). Use the modern path unless the user is on a wiki or page where wikitext is the only option.

---

## SOP: Understanding the Talk Namespace

Every Wikipedia page has an associated **talk page**. Pattern: prepend `Talk:` for mainspace, replace namespace prefix with `X talk:` for others.

| Subject Page | Talk Page |
|-------------|-----------|
| `Albert Einstein` | `Talk:Albert Einstein` |
| `User:Example` | `User talk:Example` |
| `Wikipedia:Manual of Style` | `Wikipedia talk:Manual of Style` |

- A **red-linked** talk page means no discussion has ever been started. This is normal.
- Talk pages have **separate edit histories, watchlists, and protection levels** from their subject pages.
- Access via the "Talk" tab in the web UI, or directly via URL/API.
- **Usability note:** New contributors often don't find the "Discussion" tab and assume clicking "edit" on an article will open a forum. If someone can't find a talk page, point them to the top-of-page tabs or the URL directly.

---

## SOP: Modern Talk Page Tools (DiscussionTools)

Since 2020, the WMF Editing Team has deployed **DiscussionTools** — a suite adding modern UI on top of existing wikitext. These are now the default on most wikis.

### Reply Tool

Each signed comment has a **[ reply ]** button opening an inline editor that:

- **Auto-indents** at the correct nesting level
- **Auto-signs** with `~~~~`
- Provides **visual mode** (no wikitext) or **source mode** (wikitext)
- **@-mention** with autocomplete
- **Opt-out**: Preferences → Editing → uncheck "Use the reply tool"

The Reply Tool has been shown to significantly improve newcomer comment success rates. See [this Diff post](https://diff.wikimedia.org/2024/05/02/making-talk-pages-better-for-everyone/) for A/B test results.

### New Topic Tool

"Add topic" (+) tab opens an inline form that auto-adds headings and posts at the bottom. **Opt-out**: Preferences → Editing → uncheck "Quick topic adding".

### Topic Subscriptions (Section-Level Watchlisting)

**Solves the "can't follow one thread without drowning in all of them" problem.** Subscribe to a single section (bell/star icon) to receive Echo notifications only for new comments in that thread. Subscriptions persist across archives. Check Preferences → Notifications for automatic subscription options.

### Permalinks (January 2024)

Each comment has a stable `#c-` anchor URL. Use for direct links that survive archiving:
`https://en.wikipedia.org/wiki/Talk:Article#c-Username-20260101120000-Topic`

### Thank from Talk Pages

A "Thank" button next to Reply lets you thank users for comments without visiting page history.

---

## SOP: Usability Improvements (Visual Changes)

Rolling out to all wikis in phases. Opt-out: Preferences → Appearance → "Use the talk page usability improvements".

| Change | What It Does |
|--------|-------------|
| **Topic containers** | Boxes each discussion with subtle background, separating topics visually |
| **Improved headings** | Shows participant count, comment count, last comment date per section |
| **Clear action buttons** | Reply/Add topic as bold buttons, not disguised links |
| **Page frame / breadcrumbs** | Top-of-page summary of latest activity; breadcrumb to subject page |
| **Table of contents** | Comment counts per topic for spotting active discussions |

---

## SOP: Reading Threaded Discussions

### Modern (with DiscussionTools)

The Reply Tool renders threading with clear visual hierarchy. No colon-counting needed — the tool handles it. Permalinks reference individual comments.

### Legacy (wikitext / no tools)

Discussions under `== Heading ==` sections, indented with colons:

```wikitext
== Date of birth discrepancy ==

I noticed the article lists two different dates. ~~~~

: The 1950 source says March 14. ~~~~
:: But the 1960 biography says March 13. ~~~~
```

**Indentation rules:** Each reply adds one more colon (`:` → `::` → `:::`). The colon creates a definition-list indent in wikitext HTML.

**Reading order:** Start at section heading, read chronologically top to bottom. Indentation shows who replies to whom.

**Deep nesting problem:** Beyond 4–5 levels, colon indentation becomes unusable — especially on mobile. Use `{{outdent}}` to reset:

```
{{outdent|::::}}
New comment at the left margin. ~~~~
```

Alternative strategies: start a new sub-section (`=== Side topic ===`) or move very long debates to a subpage.

**Accessibility:** Legacy colon indentation uses `<dl>` elements, which is semantically wrong for threading. Screen readers may announce indented comments as "definitions." DiscussionTools' rendering doesn't have this problem.

---

## SOP: Signing and Attributing Comments

### Modern (with DiscussionTools)

The Reply Tool **auto-signs** on publish. No need to type `~~~~` unless editing source mode.

### Legacy (wikitext only)

Always sign talk page comments:

| Wikitext | Renders As | Use |
|----------|-----------|-----|
| `~~~~` | `Username 23 May 2026 14:30 (UTC)` | Standard |
| `~~~` | `Username` | Rare |
| `~~~~~` | `23 May 2026 14:30 (UTC)` | Rare |

**Detecting unsigned comments:** Lacks `~~~~`. Tag with `{{unsigned|Username}}`.

**Custom signatures:** User-configurable in preferences. Display text may differ from username. For reliable attribution, use the **username from revision history**, not display text.

---

## SOP: Community Gadgets

Community-built, unofficial but widely used. Check Special:Preferences → Gadgets on any wiki.

### Convenient Discussions (by Jack who built the house)

Full shell over MediaWiki discussions: inline reply/edit, @-mentions, quoting, section watchlisting.
- **Available as gadget on Russian Wikipedia; userscript on any wiki.**
- **Compatibility:** Incompatible with DiscussionTools Reply Tool — enabling CD disables it.
- Install: add script to `common.js` — see [User:JWBTH/CD](https://commons.wikimedia.org/wiki/User:JWBTH/CD)

### Reply Link Gadget (by Enterprisey)

Lighter alternative: adds `[reply]` link per comment with auto-indent/sign. More compatible than CD.

---

## SOP: WikiProject Banners

Banners at the **top of talk pages** tagging article scope, quality, and importance:

```wikitext
{{WikiProject Biography|class=B|importance=High}}
```

**Assessment ratings:** Stub → Start → C → B → GA → FA (ascending). **Importance:** Top → High → Mid → Low → NA.

**Reading assessment data:**
- **Single article:** Parse talk page wikitext for `{{WikiProject...|class=...|importance=...}}`
- **Bulk:** Use **[wikimedia-page-assessment](../wikimedia-page-assessment/SKILL.md)** (queries `page_assessments` database table directly)

---

## SOP: Finding and Using Archives

Archives are subpages of the talk page (`Talk:Article/Archive 1`).

**Automated archiving** via `{{User:MiszaBot/config}}`:

```wikitext
{{User:MiszaBot/config
| algo = old(30d)
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

**Searching across archives:** Query each archive individually via `action=query&prop=revisions&titles=Talk:...&rvprop=content`. The `{{Archives}}` template links all archives and provides a search field.

**Permalinks:** Since 2024, comment permalinks remain stable across archiving — a significant improvement over the old system where archiving broke all comment links.

---

## SOP: Participating in Discussions

### Modern Workflow (Recommended)

1. **Find talk page** via "Talk" tab at article top
2. **Click [ reply ]** on an existing comment, or "Add topic" button for new thread
3. **Write** in visual or source mode; use @-mentions for pinging
4. **Click Publish** — auto-signs, auto-indents, posts at correct position
5. **Subscribe** (bell icon) to get notifications for new replies in that thread

### Legacy Workflow (wikitext fallback)

**New topic:** Add `== Subject ==` + comment at the **bottom** of the page. Use "Add topic" (+) tab or edit full page.

**Reply:** Add one more colon than the message you're replying to, write your comment, sign with `~~~~`.

| Topic |
|-------|
| `I think the article is missing context. ~~~~` |
| `: I agree, but let's find sources. ~~~~` |
| `:: Good point. Here's a source: [link]. ~~~~` |

**Notifying editors:** `{{ping|Username}}` inside a signed comment. Pings only work with a signature. In the Reply Tool, @-mentions accomplish the same thing.

**Section editing:** Click `[edit]` next to a heading, or append `&section=N` to the edit URL, to edit a single discussion without loading the full page.

---

## SOP: Following Talk Page Etiquette

| Rule | Meaning |
|------|---------|
| **Assume good faith** (WP:AGF) | Assume others are trying to help, even if you disagree |
| **No personal attacks** (WP:NPA) | Comment on content, not the contributor |
| **Stay on topic** (WP:TALK) | Discuss how to improve the article, not the subject itself |
| **Sign your comments** | Use `~~~~` or let the Reply Tool do it |
| **Strike, don't delete** | `<s>old text</s>` to retract; never remove comments entirely |
| **Don't edit others' comments** | Except vandalism, formatting fixes, or signatures |
| **Respond in context** | Article talk: reply below addressed comment. User talk: reply on own page unless asked otherwise |

**Closing discussions:**
| Template | Meaning |
|----------|---------|
| `{{resolved}}` | Issue addressed |
| `{{done}}` | Action completed |
| `{{not done}}` | Proposal rejected |
| `{{withdrawn}}` | Proposer withdrawing |

**Article talk vs. user talk:** `Talk:Article` is for improving the article with any interested editor. `User talk:Username` is for personal messages to a specific editor. Don't discuss article content on user talk pages.

---

## SOP: Structured Discussions / Flow — Deprecated

**Structured Discussions** (Flow) was a WMF project (2013–2024) to replace wikitext talk pages with a structured forum. It is **officially deprecated**; communities still using it (Catalan Wikipedia, some help desks) are being asked to migrate back to wikitext.

**If you encounter a Flow page:**
- Visual-editor-only comments; no wikitext shown
- Automatic threading, but limited search and no diff support
- Cannot be edited with normal wikitext tools
- The WMF provides [migration tooling](https://www.mediawiki.org/wiki/Structured_Discussions/Deprecation)

For historical context on why Flow was abandoned, see `references/discussion-tools-history.md`.

---

## SOP: Accessing Talk Pages via API

| Task | API Method |
|------|-----------|
| Get talk page wikitext | `action=raw&title=Talk:Title` |
| Get parsed talk page | `action=parse&page=Talk:Title&prop=text` |
| Search talk pages | `list=search` with namespace (`srnamespace=1`) |
| Find archive subpages | `list=prefixsearch&pssearch=Talk:Title/Archive` |
| Check if talk page exists | `prop=info` on the talk page title |
| Get DiscussionTools data | `action=discussiontoolsinfo&page=Talk:Title` |

---

## Relationship to Other Skills

- **wikipedia-page-anatomy** — Shares underlying MediaWiki structure with articles.
- **wikipedia-edit-history** — Talk pages have their own history; same diff/rollback apply.
- **wikimedia-page-assessment** — For bulk assessment queries instead of parsing banners individually.
- **wikimedia-api-access** — Same Action API; handles User-Agent and rate limiting.
- **wikimedia-eventstreams** — Can monitor talk page events (new topics, replies) in real time.
- **wikimedia-search-cirrussearch** — Can search talk namespaces with `talk:` prefix.
- **wikipedia-notability-assessment** — WikiProject banner assessment data and notability evaluation.
- **wikipedia-wikiprojects** — Finding projects, interpreting assessment tables, and navigating the WikiProject directory.

---

## Tooling

### 🔧 Get Assessment (`scripts/get-assessment.sh`)
```bash
./scripts/get-assessment.sh "Albert Einstein"
./scripts/get-assessment.sh "Python (programming language)" --json
```

### 🔧 List Archives (`scripts/list-archives.sh`)
```bash
./scripts/list-archives.sh "Albert Einstein"
./scripts/list-archives.sh "Talk:Albert Einstein" --json
```

### 📚 Assessment Ratings Reference (`references/assessment-ratings.md`)
FA/GA/B/C/Start/Stub ratings and Top/High/Mid/Low importance with descriptions and distribution stats.

### 📚 Discussion Tools History (`references/discussion-tools-history.md`)
Historical context: 2019 Talk Pages Consultation, LiquidThreads, Flow, DocumentMode vs. ThreadMode debate. Load on demand when historical understanding is needed.

### 🐍 Talk Archive Search (`assets/talk-archive-search.py`)
Search across a talk page and all its archives for a keyword or phrase. Uses only Python stdlib.
```bash
python3 assets/talk-archive-search.py "Albert Einstein" "Nobel"
python3 assets/talk-archive-search.py "Talk:Albert Einstein" "birth date" --json
```
