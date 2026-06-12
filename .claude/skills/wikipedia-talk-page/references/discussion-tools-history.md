# Discussion Tools History: Talk Pages Evolution

This reference provides historical context for understanding why Wikipedia talk pages work the way they do — the failed replacement attempts, the community consultation, and the philosophical debates that shaped the current approach.

---

## 1. The Origins: DocumentMode vs. ThreadMode

Before Wikipedia existed, the earliest wikis (starting with Ward Cunningham's WikiWikiWeb in 1995) had **no separation between discussion and content**. Editors would place threaded comments directly underneath article content on the same page. This was called **ThreadMode** — a series of signed, first-person comments in chronological order.

Wiki inventor **Ward Cunningham actively discouraged ThreadMode** in favor of **DocumentMode** — unsigned, third-person text that represents community consensus and can be freely edited by anyone:

> "I have done my best to discourage dialog in favor of dissertation, which offers a better fit to this medium. I've been overruled." — Ward Cunningham

The tension between these two modes has never been resolved. Talk pages are ThreadMode spaces, but they sit in a DocumentMode platform.

### Key Milestones

| Date | Event |
|------|-------|
| 1995 | First wiki (WikiWikiWeb) — no talk pages, discussion mixed with content |
| 2001 | Wikipedia launches — still no talk namespace, discussions on subpages like `Article/Talk` |
| 2002-01-25 | Talk: namespace introduced with Phase II MediaWiki software |
| 2002-03 | `~~~~` auto-signature feature added (before this, comments were unsigned or signed manually with just a username) |
| 2002 | English Wikipedia's Village Pump created |
| 2006 | LiquidThreads development begins |

---

## 2. First Attempt: LiquidThreads (2006–2015)

LiquidThreads (LQT) was the first WMF attempt at a structured discussion system:

- **Origin:** WikiProject Aircraft at English Wikipedia voted to start an off-wiki BBS (bulletin board system) for threaded discussions. A volunteer proposed creating an "on-wiki" equivalent and named it LiquidThreads.
- **Version 1:** Deployed on non-WMF wikis, ~2007
- **Version 2:** WMF hired the original developer to rebuild it. Deployed on strategy wiki (strategy.wikimedia.org) and Wikinews.
- **Outcome:** Never gained wide adoption on major Wikipedias. Most wikis stopped using it by 2015.
- **Status:** Unmaintained. Still present on a few wikis (Wikinews still uses it).

### Why LiquidThreads Failed

- Poor technical implementation
- Poor community reception
- Disrupted existing workflows that had evolved on wikitext

---

## 3. Second Attempt: Flow / Structured Discussions (2013–2024)

Flow was the WMF's major attempt to fully replace talk pages. It was developed by the Global Collaboration team starting in 2013.

### What Flow Did

- Structured topics with automatic threading
- Visual editor for comments (no wikitext required)
- Auto-signing and auto-indentation
- Infinite scrolling through topics
- Planned (but never fully built) "workflows" for voting, RFC closing, etc.

### Community Response

Flow was met with **overwhelming hostility** from the English Wikipedia community. From *The Signpost* (2015): *"Flow placed on ice."*

| Arguments for Flow | Arguments against Flow |
|---|---|
| Easy for newcomers | Infinite scrolling (universally hated) |
| Auto-signing and indentation | No proper wikitext support |
| Clear reply affordances | No diff support for individual comments |
| Good for small discussions | No way to manually restructure discussions |
| | Poor search and history |
| | Notification spam |
| | Not compatible with existing workflows (voting, drafting, templates, RFCs) |

A small number of wikis (Catalan Wikipedia, some help desks) adopted Flow successfully, especially for newcomer-facing spaces where simplicity mattered more than flexibility.

### Post-Mortem (Danny Horn, WMF Director of Product):

> "It was a real problem with the tool, and the way that we were thinking about it. We assumed that it was okay to build a tool that couldn't handle a lot of important senior editor use cases, because it would be easier for junior editors, and that was worth it. If we had gone ahead the way that we were planning to, we would have broken a lot of things without really understanding or respecting how important those broken things were. We had the wrong philosophy, and that led to bad product decisions."

### Deprecation (2024–2025)

The temporary accounts project revealed that maintaining Flow was technically unsustainable. The WMF officially deprecated Flow and is asking communities to migrate back to wikitext. From Phabricator T346108:

> "Flow is a complex piece of software that was never quite finished, fits poorly into the MediaWiki architecture due to its many (eventually un-utilized) layers of abstraction, lacks key features (such as search and solid moderation) and has many disruptive bugs, and is rejected by most Wikimedia communities."

---

## 4. The 2019 Talk Pages Consultation

After the failure of Flow, the WMF took a different approach: **consult the community first, then build.**

### Phase 1 (March–May 2019)

- 20 wikis and usergroup spaces participated (15 language Wikipedias, Commons, Wikidata, 2 Wiktionaries)
- ~450 contributors shared feedback
- WMF also conducted usability tests with 10 people who read Wikipedia regularly but had never contributed

**Key findings (from the Phase 1 report):**

> "A wikitext talk page isn't made out of software; it's a collection of cultural conventions that are baffling to newcomers and annoying for experienced editors."

**Most complained-about issues (ranked by frequency):**

| Issue | Frequency |
|-------|-----------|
| Colon indentation system | ✎✎✎✎✎✎✎ (maximum) |
| Figuring out how/where to reply | ✎✎✎✎✎✎✎ |
| Learning to sign with `~~~~` | ✎✎✎✎✎✎✎ |
| Desire for stability/wikitext continuity | ✎✎✎✎✎✎ |
| Archiving (inconsistent, breaks links) | ✎✎✎✎✎ |
| Notifications (too many or too few) | ✎✎✎✎✎ |
| Newcomer barriers | ✎✎✎✎ |
| Difficulty searching/poor archives | ✎✎✎✎ |
| Watchlist (no section-level watchlisting) | ✎✎✎✎ |

**Usability test findings:**
- **All users** struggled to find the talk page
- **None** found the "Discussion" tab at the top of the page
- Most thought clicking "edit source" on an article section would lead to a forum about that section
- One tester: "If I got to this point, I'd give up. Regardless of what I was doing because it's overwhelming."

### Phase 2 (June–August 2019)

The proposed product direction: **"Wikitext talk pages should be improved, and not replaced."**

Phase 2 tested this direction with 12 wikis. Key concerns raised:

1. **Forum or workspace?** — Talk pages are for improving articles, not general discussion. Making them too easy/findable risks attracting off-topic soapboxing.
2. **"A wiki page is a wiki page"** — Some experienced editors argued that the blank-wikitext simplicity *is* the virtue. Any change breaks that consistency.
3. **Mastery and fine-grained control** — Power users value being able to restructure discussions manually.
4. **Moderation and oversight** — Admins need to delete/revision-delete/suppress at individual edit level.
5. **Loss of existing workflows** — Voting, drafting, template-based processes that evolved on wikitext.

**The result:** Broad community support for the incremental approach. **95% of English Wikipedia respondents** supported incremental change. **Almost nobody** wanted Flow back.

---

## 5. The Incremental Approach: DiscussionTools (2020–Present)

The WMF Editing Team began building **DiscussionTools** — features that sit on top of wikitext without replacing it:

| Feature | Deployed | Impact |
|---------|----------|--------|
| Reply Tool | 2020–2021 (phased) | 160% increase in junior contributor comment completion; 79.5% fewer reverts |
| New Topic Tool | 2021 | Simplified topic creation |
| Topic Subscriptions | 2021–2022 | Section-level watchlisting |
| Permalinks | January 2024 | Stable links to individual comments |
| Usability Improvements | 2024–2026 (phased) | 11% decrease in revert rate; 16.7% more edit attempts by newcomers |
| Thank from talk pages | 2025–2026 | Inline thanks without navigating to history |

As of March 2023, **over 3 million comments** had been posted through DiscussionTools — one out of every four signed comments on-wiki.

---

## 6. Usability Improvements A/B Test Results (2024)

The WMF ran a controlled experiment at 15 wikis (50% got the Usability Improvements, 50% didn't):

| Metric | Result |
|--------|--------|
| Revert rate decrease (all users) | 11% |
| Revert rate decrease (users with <100 edits) | 12.5% |
| Increase in message completion | 3.3% |
| Increase in edit attempts (users with <100 edits) | 16.7% |
| Increase in saved edits per view (users with <100 edits) | 19% |
| Opt-out rate | 48 users out of 2,122 who commented (2.3%) |

---

## 7. Emerging Communities Moving Off-Wiki

The 2019 consultation identified a concerning trend: some non-Western language communities **have moved their coordination entirely off-wiki** to WhatsApp, Telegram, Facebook, or Discord because talk pages were unusable. Community Specialist Sherry Snyder:

> "Different communities have different approaches, and some of them find it easier to communicate off wiki, using third-party services."

This off-wiki migration represents a failure of the talk page system to serve the global Wikimedia community equitably.

---

## 8. The Road Not Taken: What Wasn't Built

Even in the incremental approach, some features from the 2019 consultation remain unimplemented:

- **Move discussion between pages** with full history — still done manually via cut-and-paste
- **View section-level history** — can only see full-page history
- **Automatic archiving with per-thread granularity** — still bot-dependent
- **Cross-wiki discussions** — conversations spanning multiple language Wikipedias still require manual coordination
- **Voting/decision-making tools** — still done with wikitext templates and human counting
- **RFC automation** — close timers, category sorting, notification — still template-based
- **Mobile parity** — DiscussionTools features are still catching up on mobile web

---

## References

- [Talk Pages Consultation Phase 1 Report](https://www.mediawiki.org/wiki/Talk_pages_consultation_2019/Phase_1_report)
- [Talk Pages Consultation Phase 2 Report](https://www.mediawiki.org/wiki/Talk_pages_consultation_2019/Phase_2_report/en)
- [People Are Talking (WMF Design Blog, 2021)](https://design.wikimedia.org/blog/2021/03/10/people-are-talking.html)
- [Making Talk Pages Better for Everyone (WMF Diff, 2024)](https://diff.wikimedia.org/2024/05/02/making-talk-pages-better-for-everyone/)
- [Structured Discussions Deprecation Report](https://www.mediawiki.org/wiki/Structured_Discussions/Deprecation/Report)
- [Discussion Tools in the Past](https://www.mediawiki.org/wiki/Talk_pages_consultation_2019/Discussion_tools_in_the_past)
- [The Signpost: English Wikipedia Talk Page Conclusions (2019)](https://signpost.news/2019-04-30/Discussion_report)
- [Flow placed on ice — The Signpost (2015)](https://signpost.news/2015-09-02/News_and_notes)
- [Ward Cunningham on Wiki Design Principles (2009)](https://williamhertling.com/2009/04/notes-from-ward-cunningham-on-the-design-principles-of-wiki-april-2009-chifoo-talk/)
