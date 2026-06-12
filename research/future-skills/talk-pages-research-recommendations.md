# Future Skills Recommendations: Talk Pages & Discussion Research

> **Origins:** This document was generated from research conducted in June 2026 into Wikipedia Talk page efficacy, shortcomings, and the history of Wikimedia's efforts to improve them. The research covered academic papers, WMF product documentation, community consultations (2019 TPC), Phabricator tickets, community gadgets, historical discussion systems (LiquidThreads, Flow), user testing results, and toxicity/retention studies.

---

## Summary of Recommendations

| Rank | Candidate | Type | Priority | Effort | Skills Overlap |
|------|-----------|------|----------|--------|----------------|
| **1** | Update `wikipedia-talk-page` | **DONE** — see updated skill | Critical | Medium | Replaces current |
| **2** | New: `wikimedia-community-health` | New skill | High | High | Low |
| **3** | Fold DiscussionTools into talk page skill | **DONE** — see updated skill | Medium | None (included in #1) | N/A |
| **4** | New: `wikimedia-structured-discussions-deprecation` | New skill | Medium | Low | Minimal |
| **5** | Historical references file | **DONE** — see `references/discussion-tools-history.md` | Low | None (included in #1) | N/A |
| **6** | Expand `wikimedia-eventstreams` for talk events | Expand existing | Low | Low | Minimal |
| **7** | New: `wikimedia-phabricator` | **DONE** — see `.claude/skills/wikimedia-phabricator/` | Medium-Low | Low | Low |

---

## Candidate 1: `wikipedia-talk-page` — Modernization (COMPLETE)

**Status: ✅ Done as part of this research.**

The skill has been updated to include:
- DiscussionTools overview (Reply Tool, New Topic Tool, Topic Subscriptions, Permalinks, Thank)
- Usability Improvements (topic containers, page frame, clear affordances)
- Community gadgets (Convenient Discussions, Reply Link)
- Modern vs. legacy workflow comparison
- Structured Discussions / Flow deprecation awareness
- Deep nesting problem and outdenting guidance
- Toxicity/community health awareness section
- Historical context references file

---

## Candidate 2: `wikimedia-community-health` (New Skill)

**Priority: High | Effort: High | Overlap: Low**

This would be the largest new skill, covering an entire domain with zero current coverage in the skill set.

### Problem Space

The Wikimedia community has a substantial body of research and tooling around community health, toxic behavior, and contributor retention. No existing skill helps agents understand or address these dynamics.

### Research Base

The following can be synthesized into SOPs:

1. **Detox / Toxicity Detection (2017–2023)**
   - WMF Research on harassment and user retention
   - The Detox project built ML models to classify toxic comments
   - Findings: registered users make 2/3 of attacks; half come from occasional contributors
   - The WAC Corpus (Wikipedia Conversations for Abuse Detection) — a labeled dataset

2. **PNAS Nexus Study (2023) — "Toxic Comments Reduce Activity"**
   - Analyzed 57 million comments across 6 language Wikipedias
   - A single toxic comment measurably reduces future contributions
   - Quantified effect: multiple fewer edits per week per toxic exposure

3. **2019 Talk Pages Consultation — Cultural Barriers**
   - "Newcomers face a hostile frontier of veterans"
   - "The real barrier is social issues rather than technical ones"
   - Multiple language communities (Dutch, Thai, Polish) raised civility as primary concern
   - Some communities moved off-wiki entirely (WhatsApp, Telegram) due to on-wiki social dynamics

4. **Emerging Communities Off-Wiki Migration**
   - Non-Western language communities disproportionately affected
   - WhatsApp, Facebook, Telegram as alternatives
   - WMF Community Specialists explicitly working to understand this

5. **Wikimedia Foundation Community Health Resources**
   - [Research:Community Health](https://research.wikimedia.org/community-health.html)
   - Anti-Harassment Tools team
   - Private Incident Reporting System (PIRS)
   - Universal Code of Conduct (UCoC)

### What This Skill Would Cover

| SOP | Description |
|-----|-------------|
| Understanding toxicity patterns | How to recognize toxic interaction patterns in talk page discussions |
| Newcomer retention factors | What drives newcomers away — both technical (usability) and social (hostility) |
| Detox/ML models | How to use the Detox models via Lift Wing to classify comments (see also `wikimedia-ml-services`) |
| Incident reporting | How to navigate the reporting system (UCoC, ArbCom, local noticeboards) |
| Community migration patterns | Understand why communities move off-wiki and how to analyze this |
| Universal Code of Conduct | The UCoC and its enforcement pathways |

### Key Design Considerations

- **This skill must be neutral and analytical** — it should help agents *understand* community dynamics, not make normative judgments or intervene directly
- **Strong data and research citations** — ground every claim in published WMF research or academic papers
- **Do not instruct agents to "diagnose" specific users as toxic** — focus on patterns and systems
- **Cross-reference** with `wikimedia-ml-services` (for toxicity scoring APIs), `wikipedia-security-and-privacy` (for harassment prevention), and `wikipedia-edit-history` (for behavioral analysis)

### Resources to Include

- Python script to fetch a talk page and generate a basic sentiment/toxicity analysis using Lift Wing
- Reference document summarizing the Detox research and PNAS Nexus paper
- Quick-reference table of reporting pathways (UCoC → ArbCom → local noticeboards)
- Decision tree: "Is this a technical barrier, a social barrier, or both?"

---

## Candidate 3: Fold DiscussionTools Into Talk Page Skill (COMPLETE)

**Status: ✅ Done as part of this research.**

The DiscussionTools features are now documented directly in `wikipedia-talk-page`, rather than as a separate skill. Rationale:

- They are part of the same user experience — separating them would force agents to cross-reference
- The project already has a preference for broader, fewer skills
- DiscussionTools features are not a separate "system" — they augment existing talk pages

---

## Candidate 4: `wikimedia-structured-discussions-deprecation` (New Skill)

**Priority: Medium | Effort: Low | Overlap: Minimal**

A small, time-limited skill about the deprecation of Structured Discussions (Flow).

### Problem Space

As of 2024–2026, communities still using Flow need to migrate back to wikitext talk pages. This is driven by the temporary accounts infrastructure work that made Flow maintenance unsustainable. However, the migration is not trivial — Flow boards have structured data, automatic threading, and visual editing that wikitext doesn't directly replicate.

### What This Skill Would Cover

| SOP | Description |
|-----|-------------|
| Identifying Flow pages | How to detect whether a given wiki/page uses Structured Discussions |
| Feature comparison | What Flow does that wikitext doesn't (and vice versa) |
| Migration tools | WMF-provided tools to export Flow content |
| Migration checklist | What to preserve (threading, history, notifications) and what can't be preserved |
| Community communication | How to announce migration, get buy-in, handle objections |
| Post-migration cleanup | Archiving old Flow boards, updating links, redirects |

### Why Not Just a Reference File?

- The migration process involves **executable steps** (running export scripts, converting topics, verifying history)
- The deprecation has **technical specifics** (extension config, database tables, API endpoints)
- Community migration requires **social process guidance** (how to announce, how long to keep old boards readable)
- These are too procedural for a reference file and too narrow to live in another skill

### Shelf Life

This skill has a limited shelf life — it becomes historical reference once all Flow pages are migrated. Estimate: useful for ~2 years from 2026. After that, it could be merged into `references/discussion-tools-history.md`.

### Resources to Include

- WMF's Structured Discussions deprecation page: https://www.mediawiki.org/wiki/Structured_Discussions/Deprecation
- Migration script examples
- Community announcement template
- Phabricator tickets for known migration issues

---

## Candidate 5: Historical References File (COMPLETE)

**Status: ✅ Done as part of this research.**

`references/discussion-tools-history.md` now covers:
- DocumentMode vs. ThreadMode debate
- LiquidThreads (2006–2015)
- Flow / Structured Discussions (2013–2024)
- 2019 Talk Pages Consultation (Phases 1 & 2)
- DiscussionTools deployment history
- Usability Improvements A/B test results
- Emerging communities moving off-wiki
- The "road not taken" — unimplemented features

---

## Candidate 6: `wikimedia-phabricator` (COMPLETE)

**Status: ✅ Created as part of this research.**

See `.claude/skills/wikimedia-phabricator/SKILL.md` — a 238-line lean skill covering:
- What Phabricator is and how it differs from MediaWiki
- Searching (basic, advanced, from URL references)
- Understanding task statuses (Needs Triage → Open → Stalled → Resolved → Closed)
- Understanding project tags and task hierarchies (parent/subtask, epics)
- Filing bug reports (what to include, conventions)
- Tracking what's in development (step-by-step workflow)
- Quick reference card

## Candidate 7: Expand `wikimedia-eventstreams` for Talk Page Events

**Priority: Low | Effort: Low | Overlap: Minimal**

### What Could Be Added

The eventstreams skill already has a one-line comment about detecting talk page namespace changes. This could be expanded to cover:

- The `page-links-change` event for talk page links
- Using event streams to monitor new talk page topics in real time
- Monitoring talk pages for specific keywords or patterns
- Alerting when a discussion starts on a watched article

### Why Low Priority

- This is only relevant for tool builders doing real-time monitoring
- The existing eventstreams documentation is already comprehensive
- Talk page monitoring is a specialized niche within a specialized niche

---

## Candidate: Not Recommended — `wikipedia-talk-page-gadgets`

**Decision: Do not create as a separate skill.**

The community gadgets (Convenient Discussions, Reply Link, etc.) are important but:

1. The landscape changes too frequently for a durable skill
2. Installation instructions vary by wiki
3. They are better documented as a section within `wikipedia-talk-page` (done)
4. The WMF may adopt their features into core DiscussionTools, making them obsolete

---

## Additional Knowledge from This Research That Could Enrich Existing Skills

These are smaller pieces of knowledge that don't warrant standalone skills but would improve existing ones:

| Knowledge | Where It Could Live |
|-----------|---------------------|
| Talk page namespace filtering for CirrusSearch (`talk:`, `user talk:` prefixes) | Already in `wikimedia-search-cirrussearch` (present) |
| Using page_assessments SQL table (replica) for talk page banner data | Already in `wikimedia-page-assessment` (present) |
| Lift Wing toxicity/revert-risk models for talk page comments | Add a section to `wikimedia-ml-services` — currently missing |
| The WAC Corpus as a training dataset | Add to `wikimedia-ml-services` references |
| Using DiscussionTools' database tables (`comment`, `comment_revision`) for analysis | Add to `wikimedia-database` references |
| Talk page edit patterns in edit history analysis (section edits, unsigned comment detection) | Add to `wikipedia-edit-history` |

---

## Research Sources Referenced for This Analysis

| Source | Type | Used For |
|--------|------|----------|
| TPC Phase 1 Report (2019) | WMF consultation | All UX issues, colon problem, newcomer barriers |
| TPC Phase 2 Report (2019) | WMF consultation | Product direction, feature list, concerns |
| New User Tests (2019) | Usability research | Discovery failure, task completion data |
| People Are Talking (WMF Design Blog, 2021) | Design retrospective | Flow post-mortem, gadget pipeline, designer journey |
| Making Talk Pages Better (WMF Diff, 2024) | Product announcement | Usability Improvements rollout, A/B test results |
| Structured Discussions Deprecation Report (2024) | Technical report | Flow deprecation rationale, migration |
| PNAS Nexus — Toxic Comments (2023) | Academic paper | Toxicity quantification, retention impact |
| Detox — Harassment & Retention (WMF Research) | WMF research | Toxicity patterns, attacker demographics |
| WAC Corpus (2020) | Academic paper | Abuse detection dataset |
| SAC 2011 — Schneider et al. | Academic paper | First in-depth talk page analysis |
| Discussion Tools in the Past (MediaWiki) | Historical document | LQT history, Talk namespace origin |
| The Signpost (2015, 2019) | Community journalism | Flow post-mortem, community sentiment |
| Phabricator T346108, T409297, T379264 | Engineering tickets | Flow deprecation, enwiki deployment |
| Convenient Discussions (jwbth) | Community tool | Gadget feature set, inspiration for DiscussionTools |
| Ward Cunningham on Wiki Design (2009) | Historical interview | DocumentMode vs ThreadMode philosophy |

---

## How to Use This Document

When deciding whether to create a new skill, refer to this document for:

1. **Problem validation** — Is this a real pain point with research backing?
2. **Existing coverage** — Does another skill already touch on this?
3. **Shelf life** — Is the knowledge durable enough for a skill?
4. **Actionability** — Can an agent *do* something useful with this skill?
5. **Scope** — Is it too narrow (gadget-specific) or too broad (entire domain)?

The candidates ranked #2 (`wikimedia-community-health`) and #4 (`wikimedia-structured-discussions-deprecation`) are the most actionable next steps after the talk page skill update.
